# pyexops/src/pyexops/scene.py

import numpy as np
from scipy.ndimage import gaussian_filter, convolve, shift 
from scipy.special import j1 
from scipy.optimize import curve_fit 
from typing import List, Tuple, Union, TYPE_CHECKING, Optional 

# TYPE_CHECKING is used to avoid circular imports during runtime while allowing type hints
if TYPE_CHECKING:
    from .star import Star
    from .planet import Planet
    from .binary_star_system import BinaryStarSystem # NEW: Import BinaryStarSystem

class Scene:
    """
    Generates an image frame at a given time.

    This class is responsible for rendering the star(s) and planets onto a 2D image
    grid, applying limb darkening, stellar activity, point spread function (PSF)
    convolution, and instrumental effects like pointing jitter and pixel response
    non-uniformity (PRNU). It now supports binary star systems.
    """
    def __init__(self, stars: Union['Star', 'BinaryStarSystem'], planets: List['Planet'], 
                 image_resolution: Tuple[int, int], barycenter_pixel_on_image: Tuple[int, int], # Changed star_center_pixel to barycenter_pixel_on_image
                 background_flux_per_pixel: float = 0.0,
                 read_noise_std: float = 5.0, 
                 psf_type: str = 'gaussian', 
                 psf_params: Optional[dict] = None,
                 pointing_jitter_std_pixels: float = 0.0, 
                 pixel_response_non_uniformity_map: Optional[np.ndarray] = None): 
        """
        Initializes the scene generator.

        :param stars: The host Star object (for single star systems) OR a BinaryStarSystem object.
        :param planets: List of Planet objects.
        :param image_resolution: (width_pixels, height_pixels) of the image.
        :param barycenter_pixel_on_image: (x_pixel, y_pixel) coordinates of the system's barycenter in the image.
        :param background_flux_per_pixel: Constant background flux per pixel.
        :param read_noise_std: Standard deviation of Gaussian read noise per pixel.
        :param psf_type: Type of PSF to use ('gaussian', 'moffat', 'airy', 'elliptical_gaussian', 'combined').
        :param psf_params: Dictionary of parameters specific to the chosen PSF type.
                           - 'gaussian': {'sigma_pixels': float}\n
                           - 'moffat': {'fwhm_pixels': float, 'beta': float}\n
                           - 'airy': {'first_null_radius_pixels': float}\n
                           - 'elliptical_gaussian': {'sigma_x_pixels': float, 'sigma_y_pixels': float, 'angle_degrees': float}\n
                           - 'combined': {'components': list of dicts, each specifying a PSF type and its params}\n
        :param pointing_jitter_std_pixels: Standard deviation of Gaussian noise applied to star's center
                                           pixel for simulating pointing jitter.
        :param pixel_response_non_uniformity_map: A 2D numpy array (same shape as image_resolution)
                                                    representing multiplicative pixel response non-uniformity.
                                                    Values > 1 means higher sensitivity, < 1 lower.
        :raises ValueError: If an unsupported PSF type is provided or PRNU map shape is incorrect.
        :raises TypeError: If 'stars' is not a Star or BinaryStarSystem object.
        """
        self.stars_object = stars # Store the Star or BinaryStarSystem object
        
        if isinstance(self.stars_object, BinaryStarSystem): # NEW: Handle binary system
            self.is_binary = True
            self.star_list = [self.stars_object.star1, self.stars_object.star2]
            # pixels_per_star_radius needs to be based on a reference star for scaling
            # Let's use star1's radius as the reference for converting relative coords to pixels
            self.pixels_per_reference_radius = self.stars_object.star1.radius 
        elif isinstance(self.stars_object, Star):
            self.is_binary = False
            self.star_list = [self.stars_object]
            self.pixels_per_reference_radius = self.stars_object.radius 
        else:
            raise TypeError("`stars` must be a Star object for single systems or a BinaryStarSystem object.")

        self.planets = planets
        self.width, self.height = image_resolution
        self.barycenter_pixel_on_image_x, self.barycenter_pixel_on_image_y = barycenter_pixel_on_image
        self.background_flux_per_pixel = background_flux_per_pixel
        self.read_noise_std = read_noise_std 

        self.psf_type = psf_type.lower()
        self.psf_params = psf_params if psf_params is not None else {}

        # Extract specific PSF parameters for convenience
        if self.psf_type == 'gaussian':
            self.psf_sigma_pixels = self.psf_params.get('sigma_pixels', 1.0)
        elif self.psf_type == 'moffat':
            self.moffat_fwhm_pixels = self.psf_params.get('fwhm_pixels', 3.0)
            self.moffat_beta = self.psf_params.get('beta', 3.0)
        elif self.psf_type == 'airy':
            self.airy_first_null_radius_pixels = self.psf_params.get('first_null_radius_pixels', 2.0)
        elif self.psf_type == 'elliptical_gaussian':
            self.elliptical_sigma_x_pixels = self.psf_params.get('sigma_x_pixels', 1.0)
            self.elliptical_sigma_y_pixels = self.psf_params.get('sigma_y_pixels', 1.0)
            self.elliptical_angle_degrees = self.psf_params.get('angle_degrees', 0.0)
        elif self.psf_type == 'combined':
            self.combined_psf_components = self.psf_params.get('components', [])
        else:
            raise ValueError(f"Unsupported PSF type: {psf_type}. Choose from 'gaussian', 'moffat', 'airy', 'elliptical_gaussian', 'combined'.")

        self.pointing_jitter_std_pixels = pointing_jitter_std_pixels 
        
        # Validate PRNU map
        if pixel_response_non_uniformity_map is not None:
            if pixel_response_non_uniformity_map.shape != image_resolution:
                raise ValueError("pixel_response_non_uniformity_map must have shape matching image_resolution.")
            self.pixel_response_non_uniformity_map = pixel_response_non_uniformity_map.astype(np.float64)
        else:
            self.pixel_response_non_uniformity_map = None 

        # Pre-generate representative PSF kernel for optimal photometry and PSF fitting
        self.psf_kernel_for_photometry = self._get_representative_psf_kernel()

    def _get_representative_psf_kernel(self, kernel_size_factor: int = 7) -> np.ndarray:
        """
        Generates a representative PSF kernel for use in photometric methods (Optimal, PSF Fitting).
        This kernel represents the 'ideal' shape of the PSF that photometer expects.

        :param kernel_size_factor: Factor to determine kernel size based on PSF parameters (e.g., sigma).
        :return: A 2D numpy array representing the normalized PSF kernel.
        """
        if self.psf_type == 'combined':
            combined_kernel = None
            for component_params in self.combined_psf_components:
                comp_type = component_params.get('type')
                comp_kernel = None
                if comp_type == 'gaussian':
                    sigma = component_params.get('sigma_pixels', 1.0)
                    if sigma > 0: comp_kernel = self._generate_gaussian_kernel_internal(sigma, kernel_size_factor)
                elif comp_type == 'moffat':
                    fwhm = component_params.get('fwhm_pixels', 3.0)
                    beta = component_params.get('beta', 3.0)
                    if fwhm > 0 and beta > 0: comp_kernel = self._generate_moffat_kernel(fwhm, beta, kernel_size_factor)
                elif comp_type == 'airy':
                    first_null_radius = component_params.get('first_null_radius_pixels', 2.0)
                    if first_null_radius > 0: comp_kernel = self._generate_airy_kernel(first_null_radius, kernel_size_factor)
                elif comp_type == 'elliptical_gaussian':
                    sigma_x = component_params.get('sigma_x_pixels', 1.0)
                    sigma_y = component_params.get('sigma_y_pixels', 1.0)
                    angle = component_params.get('angle_degrees', 0.0)
                    if sigma_x > 0 or sigma_y > 0: comp_kernel = self._generate_elliptical_gaussian_kernel(sigma_x, sigma_y, angle, kernel_size_factor)
                
                if comp_kernel is not None:
                    if combined_kernel is None:
                        combined_kernel = comp_kernel
                    else:
                        s1 = combined_kernel.shape
                        s2 = comp_kernel.shape
                        new_size = max(s1[0], s2[0])
                        
                        padded_k1 = np.pad(combined_kernel, (((new_size - s1[0])//2, (new_size - s1[0]) - (new_size - s1[0])//2),
                                                            ((new_size - s1[1])//2, (new_size - s1[1]) - (new_size - s1[1])//2)), 'constant')
                        padded_k2 = np.pad(comp_kernel, (((new_size - s2[0])//2, (new_size - s2[0]) - (new_size - s2[0])//2),
                                                          ((new_size - s2[1])//2, (new_size - s2[1]) - (new_size - s2[1])//2)), 'constant')
                        
                        combined_kernel = convolve(padded_k1, padded_k2, mode='constant', cval=0.0)
                        combined_kernel /= np.sum(combined_kernel) # Re-normalize after convolution

            return combined_kernel if combined_kernel is not None else np.array([[1.0]])
        
        # For single PSF types, generate the kernel directly
        if self.psf_type == 'gaussian':
            return self._generate_gaussian_kernel_internal(self.psf_sigma_pixels, kernel_size_factor)
        elif self.psf_type == 'moffat':
            return self._generate_moffat_kernel(self.moffat_fwhm_pixels, self.moffat_beta, kernel_size_factor)
        elif self.psf_type == 'airy':
            return self._generate_airy_kernel(self.airy_first_null_radius_pixels, kernel_size_factor)
        elif self.psf_type == 'elliptical_gaussian':
            return self._generate_elliptical_gaussian_kernel(self.elliptical_sigma_x_pixels, self.elliptical_sigma_y_pixels, self.elliptical_angle_degrees, kernel_size_factor)
        else:
            return np.array([[1.0]]) # Fallback identity kernel

    def _generate_gaussian_kernel_internal(self, sigma_pixels: float, kernel_size_factor: int = 5) -> np.ndarray:
        """
        Internal helper to generate a 2D Gaussian kernel.

        :param sigma_pixels: Standard deviation of the Gaussian in pixels.
        :param kernel_size_factor: Multiplier for sigma to determine kernel array size.
        :return: A 2D numpy array representing the normalized Gaussian kernel.
        """
        if sigma_pixels <= 0: return np.array([[1.0]])

        size = int(np.ceil(sigma_pixels * kernel_size_factor)) 
        if size % 2 == 0: size += 1 
        if size < 3: size = 3 
        
        center = size // 2
        y, x = np.indices((size, size)) - center
        r_sq = x**2 + y**2
        
        kernel = np.exp(-r_sq / (2 * sigma_pixels**2))
        kernel /= np.sum(kernel) # Normalize
        return kernel

    def _generate_moffat_kernel(self, fwhm_pixels: float, beta: float, kernel_size_factor: int = 5) -> np.ndarray:
        """
        Generates a 2D Moffat PSF kernel.

        :param fwhm_pixels: Full Width at Half Maximum in pixels.
        :param beta: Shape parameter of the Moffat profile.
        :param kernel_size_factor: Multiplier for FWHM to determine kernel array size.
        :return: A 2D numpy array representing the normalized Moffat kernel.
        """
        if fwhm_pixels <= 0 or beta <= 0:
            return np.array([[1.0]]) 

        alpha = fwhm_pixels / (2 * np.sqrt(2**(1/beta) - 1))

        size = int(np.ceil(fwhm_pixels * kernel_size_factor)) 
        if size % 2 == 0: size += 1 
        if size < 3: size = 3 
        
        center = size // 2
        y, x = np.indices((size, size)) - center
        r = np.sqrt(x**2 + y**2)

        kernel = (1 + (r/alpha)**2)**(-beta)
        if np.sum(kernel) > 0:
            kernel /= np.sum(kernel) 
        else:
            kernel[center, center] = 1.0 
        return kernel

    def _generate_airy_kernel(self, first_null_radius_pixels: float, kernel_size_factor: int = 5) -> np.ndarray:
        """
        Generates a 2D Airy disk PSF kernel.

        :param first_null_radius_pixels: Radius of the first null (zero intensity) in pixels.
        :param kernel_size_factor: Multiplier for first null radius to determine kernel array size.
        :return: A 2D numpy array representing the normalized Airy kernel.
        """
        if first_null_radius_pixels <= 0:
            return np.array([[1.0]]) 

        size = int(np.ceil(first_null_radius_pixels * kernel_size_factor)) 
        if size % 2 == 0: size += 1
        if size < 3: size = 3 
        
        center = size // 2
        y, x = np.indices((size, size)) - center
        r = np.sqrt(x**2 + y**2)

        scale_factor = 3.831705970207512 / first_null_radius_pixels
        
        kernel = np.zeros((size, size), dtype=float)
        kernel[center, center] = 1.0 
        non_zero_r_mask = (r != 0)
        non_zero_r = r[non_zero_r_mask]
        kernel[non_zero_r_mask] = (2 * j1(non_zero_r * scale_factor) / (non_zero_r * scale_factor))**2

        if np.sum(kernel) > 0:
            kernel /= np.sum(kernel) 
        else: 
            kernel[center, center] = 1.0
        return kernel

    def _generate_elliptical_gaussian_kernel(self, sigma_x: float, sigma_y: float, angle_degrees: float, kernel_size_factor: int = 5) -> np.ndarray:
        """
        Generates a 2D elliptical Gaussian PSF kernel.

        :param sigma_x: Standard deviation along the major axis in pixels.
        :param sigma_y: Standard deviation along the minor axis in pixels.
        :param angle_degrees: Rotation angle of the major axis from the x-axis in degrees.
        :param kernel_size_factor: Multiplier for the maximum sigma to determine kernel array size.
        :return: A 2D numpy array representing the normalized elliptical Gaussian kernel.
        """
        if sigma_x <= 0 and sigma_y <= 0:
            return np.array([[1.0]]) 

        max_sigma = max(sigma_x, sigma_y)
        if max_sigma <= 0: 
            return np.array([[1.0]])
            
        size = int(np.ceil(max_sigma * kernel_size_factor)) 
        if size % 2 == 0: size += 1
        if size < 3: size = 3 
        
        center = size // 2
        y, x = np.indices((size, size)) - center

        theta = np.deg2rad(angle_degrees)
        
        x_rot = x * np.cos(theta) + y * np.sin(theta)
        y_rot = -x * np.sin(theta) + y * np.cos(theta)

        exponent_x = (x_rot**2 / sigma_x**2) if sigma_x > 0 else np.inf * (x_rot != 0)
        exponent_y = (y_rot**2 / sigma_y**2) if sigma_y > 0 else np.inf * (y_rot != 0)

        kernel = np.exp(-0.5 * (exponent_x + exponent_y))
        
        if np.sum(kernel) > 0:
            kernel /= np.sum(kernel) 
        else: 
            kernel[center, center] = 1.0 

        return kernel

    def generate_image(self, time: float, add_noise: bool = True, inject_systematics: bool = True,
                       wavelength_nm: Optional[float] = None) -> np.ndarray: 
        """
        Generates a 2D numpy array representing the image at a given time.

        This method calculates the stellar flux at each pixel, accounts for
        planetary transits, applies PSF convolution, and adds instrumental noise
        and non-uniformity. It now supports binary star systems and their eclipses.

        :param time: Current time.
        :param add_noise: Whether to add Poisson (photon) and Gaussian (read) noise.
        :param inject_systematics: Whether to inject a synthetic systematic trend (e.g., background drift).
        :param wavelength_nm: Optional wavelength in nanometers. If provided and planet has atmosphere,
                              effective planet radius will be used for occultation.
        :return: 2D numpy array (float) of image pixel values.
        """
        # Inject a simple systematic trend into the background flux for PDCSAP demo
        current_background_flux = self.background_flux_per_pixel
        if inject_systematics:
            current_background_flux *= (1 + 0.05 * np.sin(time / 5.0) + 0.001 * time)
            
        image = np.full((self.height, self.width), current_background_flux, dtype=float)
        
        # Apply pointing jitter to the system barycenter's effective center for this frame
        current_barycenter_x = self.barycenter_pixel_on_image_x
        current_barycenter_y = self.barycenter_pixel_on_image_y
        if self.pointing_jitter_std_pixels > 0: 
            dx_jitter, dy_jitter = np.random.normal(0, self.pointing_jitter_std_pixels, 2)
            current_barycenter_x += dx_jitter
            current_barycenter_y += dy_jitter

        # Get positions of stars relative to the barycenter for this time
        star_positions_bary = {}
        if self.is_binary:
            x1_b, y1_b, z1_b, x2_b, y2_b, z2_b = self.stars_object.get_star_barycentric_positions_at_time(time)
            star_positions_bary[0] = (x1_b, y1_b, z1_b)
            star_positions_bary[1] = (x2_b, y2_b, z2_b)
        else: # Single star system, star is at barycenter
            star_positions_bary[0] = (0.0, 0.0, 0.0) # Star 0 at barycenter's origin (relative)

        # Get positions of planets relative to the barycenter for this time
        # Need to pass host star's barycentric position
        planet_positions_bary = {}
        for planet in self.planets:
            host_star_pos = star_positions_bary.get(planet.host_star_index, (0.0, 0.0, 0.0))
            planet_positions_bary[planet] = planet.get_position_at_time(time, host_star_pos[0], host_star_pos[1])

        # Render stars and apply occultations
        for py in range(self.height):
            for px in range(self.width):
                total_stellar_flux_at_pixel = 0.0
                
                # Iterate through each star in the system
                for s_idx, star_obj in enumerate(self.star_list):
                    star_x_bary, star_y_bary, star_z_bary = star_positions_bary[s_idx]
                    
                    # Calculate pixel position relative to current star's center (in stellar radii of star_obj)
                    # Convert absolute image pixel to relative to star's center using its own radius for scaling
                    x_pixel_from_star_center = (px - (current_barycenter_x + star_x_bary * self.pixels_per_reference_radius))
                    y_pixel_from_star_center = (py - (current_barycenter_y + star_y_bary * self.pixels_per_reference_radius))
                    
                    # Scale to star_obj's radii
                    x_rel_to_star = x_pixel_from_star_center / star_obj.radius
                    y_rel_to_star = y_pixel_from_star_center / star_obj.radius

                    # Get stellar flux at this pixel location from this star
                    current_star_pixel_flux = star_obj.get_pixel_flux(x_rel_to_star, y_rel_to_star, time)
                    
                    # --- Apply mutual stellar eclipses (if binary) ---
                    if self.is_binary:
                        # Check if this star (star_obj) is being occulted by the other star
                        other_star_idx = 1 - s_idx # The index of the other star
                        other_star_obj = self.star_list[other_star_idx]
                        other_star_x_bary, other_star_y_bary, other_star_z_bary = star_positions_bary[other_star_idx]

                        # Project relative positions and radii onto the plane of the sky
                        # Distance between star_obj and other_star_obj in sky plane
                        dist_stars_proj = np.sqrt((star_x_bary - other_star_x_bary)**2 + (star_y_bary - other_star_y_bary)**2)
                        
                        # Relative line-of-sight distance (z_other - z_this_star). Positive means other_star is further.
                        rel_z_stars = other_star_z_bary - star_z_bary

                        # Assume occultation only happens if other_star is closer (smaller z_bary, if z points away)
                        # More precisely, if star_obj is behind other_star_obj in line of sight.
                        # Let's say smaller z_bary is "closer to observer".
                        
                        # Simplistic eclipse check: Is star_obj behind other_star_obj?
                        # This assumes z_bary is depth, so larger z is further away.
                        if star_z_bary > other_star_z_bary: # star_obj is behind other_star_obj
                            # Check if the pixel being drawn for star_obj is covered by other_star_obj
                            dist_to_other_star_center = np.sqrt(
                                (px - (current_barycenter_x + other_star_x_bary * self.pixels_per_reference_radius))**2 +
                                (py - (current_barycenter_y + other_star_y_bary * self.pixels_per_reference_radius))**2
                            )
                            # Convert other_star_obj's radius to image pixels based on reference radius
                            other_star_radius_pixels_on_image = other_star_obj.radius * self.pixels_per_reference_radius / self.stars_object.star1.radius
                            
                            if dist_to_other_star_center < other_star_radius_pixels_on_image:
                                # This pixel for star_obj is being occulted by other_star_obj
                                # For precise partial eclipses, this requires integrating overlapping areas.
                                # For now, a simple approximation: if the pixel for star_obj is *also* inside the other star, reduce its flux.
                                # A more robust method would be to calculate the flux of star_obj *behind* other_star_obj.
                                # For full generality, this is very hard per pixel. Summing it up is easier.
                                # For now, we simplify: if this star is 'behind' the other, and the pixel is inside the other, this pixel's flux is 0.
                                # This is a temporary simplification for scene rendering, as true eclipse logic is often applied to total flux.
                                # The more precise mutual stellar eclipse will be handled by a separate method calculating system flux.
                                pass # This simplified per-pixel occlusion is removed for now, as it's handled by total flux later.

                    # --- Apply planetary transits on this star ---
                    for planet in self.planets:
                        if planet.host_star_index == s_idx: # This planet orbits the current star_obj
                            planet_x_bary, planet_y_bary, planet_z_bary = planet_positions_bary[planet]
                            
                            # Calculate planet's position relative to the *current star_obj*'s center (in its own stellar radii)
                            # This is the same logic as Planet.get_position_at_time, but for rendering
                            
                            # Convert planetary barycentric position to position relative to star_obj's center (for this specific star)
                            x_rel_planet_to_star_obj_center = x_pixel_from_star_center / star_obj.radius
                            y_rel_planet_to_star_obj_center = y_pixel_from_star_center / star_obj.radius
                            
                            # Distance of current pixel to the planet's center (relative to star_obj's size)
                            # Need planet's coordinates relative to its host star in stellar radii of host_star
                            # From Planet.get_position_at_time, x_rel_host, y_rel_host
                            
                            # This gets complicated very fast for pixel-by-pixel rendering.
                            # The planet.get_position_at_time gives planet's barycentric position.
                            # We need planet's position relative to *this star's* current position on the image.

                            # Let's re-calculate planet's position relative to *its host star*
                            # in stellar radii of that host star.
                            phase = 2 * np.pi * ((time - planet.epoch_transit) / planet.period)
                            from .orbital_solver import OrbitalSolver # Local import
                            eccentric_anomaly = OrbitalSolver._solve_kepler_equation(phase, planet.eccentricity)
                            true_anomaly = 2 * np.arctan2(np.sqrt(1 + planet.eccentricity) * np.sin(eccentric_anomaly / 2),
                                                          np.sqrt(1 - planet.eccentricity) * np.cos(np.deg2rad(planet.argument_of_periastron_rad) / 2)) # Error in previous, should be E/2
                            
                            r_from_host = planet.semimajor_axis * (1 - planet.eccentricity**2) / (1 + planet.eccentricity * np.cos(true_anomaly))
                            
                            angle_in_orbital_plane_from_host = true_anomaly + planet.argument_of_periastron_rad

                            planet_x_rel_host = r_from_host * np.sin(angle_in_orbital_plane_from_host)
                            planet_y_rel_host = -r_from_host * np.cos(angle_in_orbital_plane_from_host) * np.cos(planet.inclination_rad)
                            
                            # Convert pixel coordinates from "relative to star_obj" to "relative to planet_center"
                            dist_pixel_from_planet_center = np.sqrt(
                                (x_rel_to_star - planet_x_rel_host * star_obj.radius / star_obj.radius)**2 + # Already in stellar radii of this star_obj
                                (y_rel_to_star - planet_y_rel_host * star_obj.radius / star_obj.radius)**2
                            )
                            
                            effective_planet_radius = planet.radius 
                            if planet.atmosphere is not None and wavelength_nm is not None:
                                effective_planet_radius = planet.atmosphere.get_effective_radius(wavelength_nm)

                            if dist_pixel_from_planet_center < effective_planet_radius: 
                                current_star_pixel_flux = 0.0 # Pixel is occulted by this planet
                                break # A pixel can only be occulted by one planet for this star.

                    total_stellar_flux_at_pixel += current_star_pixel_flux

                image[py, px] += total_stellar_flux_at_pixel
        
        # Apply Point Spread Function (PSF) based on selected type
        if self.psf_type == 'gaussian':
            if self.psf_sigma_pixels > 0: 
                image = gaussian_filter(image, sigma=self.psf_sigma_pixels)
        elif self.psf_type == 'moffat':
            moffat_kernel = self._generate_moffat_kernel(self.moffat_fwhm_pixels, self.moffat_beta)
            image = convolve(image, moffat_kernel, mode='constant', cval=0.0)
        elif self.psf_type == 'airy':
            airy_kernel = self._generate_airy_kernel(self.airy_first_null_radius_pixels)
            image = convolve(image, airy_kernel, mode='constant', cval=0.0)
        elif self.psf_type == 'elliptical_gaussian':
            elliptical_kernel = self._generate_elliptical_gaussian_kernel(
                self.elliptical_sigma_x_pixels, self.elliptical_sigma_y_pixels, self.elliptical_angle_degrees
            )
            image = convolve(image, elliptical_kernel, mode='constant', cval=0.0)
        elif self.psf_type == 'combined':
            for component_params in self.combined_psf_components:
                comp_type = component_params.get('type')
                if comp_type == 'gaussian':
                    sigma = component_params.get('sigma_pixels', 1.0)
                    if sigma > 0: image = gaussian_filter(image, sigma=sigma)
                elif comp_type == 'moffat':
                    fwhm = component_params.get('fwhm_pixels', 3.0)
                    beta = component_params.get('beta', 3.0)
                    if fwhm > 0 and beta > 0:
                        moffat_kernel = self._generate_moffat_kernel(fwhm, beta)
                        image = convolve(image, moffat_kernel, mode='constant', cval=0.0)
                elif comp_type == 'airy':
                    first_null_radius = component_params.get('first_null_radius_pixels', 2.0)
                    if first_null_radius > 0:
                        airy_kernel = self._generate_airy_kernel(first_null_radius)
                        image = convolve(image, airy_kernel, mode='constant', cval=0.0)
                elif comp_type == 'elliptical_gaussian':
                    sigma_x = component_params.get('sigma_x_pixels', 1.0)
                    sigma_y = component_params.get('sigma_y_pixels', 1.0)
                    angle = component_params.get('angle_degrees', 0.0)
                    if sigma_x > 0 or sigma_y > 0:
                        elliptical_kernel = self._generate_elliptical_gaussian_kernel(sigma_x, sigma_y, angle)
                        image = convolve(image, elliptical_kernel, mode='constant', cval=0.0)
                else:
                    print(f"Warning: Unknown component PSF type '{comp_type}' in combined PSF. Skipping.")

        # Apply Pixel Response Non-Uniformity (PRNU)
        if self.pixel_response_non_uniformity_map is not None: 
            image *= self.pixel_response_non_uniformity_map
            
        # Add noise
        if add_noise:
            image = np.random.poisson(image).astype(float) 
            image += np.random.normal(0, self.read_noise_std, size=image.shape)
            image[image < 0] = 0

        return image

    def generate_template_image(self, times: np.ndarray, num_frames: int = 10, 
                                wavelength_nm: Optional[float] = None) -> np.ndarray: 
        """
        Generates a template image by averaging multiple out-of-transit/eclipse frames.
        Used for Difference Imaging Photometry.

        This method ensures the template is clean by disabling noise and systematics.

        :param times: Full array of observation times.
        :param num_frames: Number of frames to average for the template.
        :param wavelength_nm: Optional wavelength in nanometers. Passed to generate_image for consistency.
        :return: Averaged template image.
        :raises ValueError: If not enough observation times are available or no template frames can be generated.
        """
        if len(times) < num_frames:
            raise ValueError(f"Cannot generate template: Not enough observation times ({len(times)}) for {num_frames} frames.")
        
        indices_for_template = np.linspace(0, len(times) - 1, num_frames, dtype=int)
        template_frames = []
        for idx in indices_for_template:
            t = times[idx]
            
            # For a binary system, it's more complex to guarantee 'out-of-eclipse'.
            # A rough check for primary transits and major stellar eclipses:
            is_in_any_eclipse = False
            
            # Check for stellar eclipses in binary
            if self.is_binary:
                x1, y1, z1, x2, y2, z2 = self.stars_object.get_star_barycentric_positions_at_time(t)
                dist_stars_proj = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                sum_radii = self.stars_object.star1.radius + self.stars_object.star2.radius
                if dist_stars_proj < sum_radii * 1.5: # Buffer for partial eclipses
                    is_in_any_eclipse = True
            
            # Check for planetary transits
            if not is_in_any_eclipse:
                for planet in self.planets:
                    # Planet position relative to its host star. For template generation, host_star_current_x/y_bary can be 0.
                    # It's a rough check for *any* occultation by planet.
                    # The more precise logic is to just take out-of-transit/eclipse parts of the full system.
                    # For a template, we just need times far from *any* major dips.
                    # Simplification: just check if any planet is close to *its* host star.
                    # This is imperfect for binary systems where a planet could transit the other star.
                    # For template, we ideally want a flat, high-flux baseline.
                    
                    # For now, approximate out-of-transit check based on primary transit phase.
                    # This simplified check doesn't handle secondary star transits by planet
                    # or occultations of planets by the secondary star.
                    # A more robust template generation would require a model fit.
                    
                    # Simplified check: if planet is within few stellar radii of its host
                    # This check is more relevant for the primary transit of its host.
                    x_p, y_p, _ = planet.get_position_at_time(t, 0.0, 0.0) # Assuming host is at (0,0) for this check
                    dist_from_host_center = np.sqrt(x_p**2 + y_p**2)
                    if dist_from_host_center < (1.0 + planet.radius + 0.1) * planet.semimajor_axis / (self.pixels_per_reference_radius / planet.radius): 
                         is_in_any_eclipse = True
                         # The scaling here is tricky if star.radius is not 1.0. Re-evaluate.
                         # Better: just check phase if period is known
                         orbital_phase_from_transit = (t - planet.epoch_transit) % planet.period
                         if orbital_phase_from_transit < 0: orbital_phase_from_transit += planet.period
                         # If within 0.1 period of transit or secondary eclipse
                         if (orbital_phase_from_transit < 0.1 * planet.period or 
                             orbital_phase_from_transit > 0.9 * planet.period or
                             (orbital_phase_from_transit > 0.4 * planet.period and orbital_phase_from_transit < 0.6 * planet.period)):
                             is_in_any_eclipse = True

            if not is_in_any_eclipse:
                template_frames.append(self.generate_image(t, add_noise=False, inject_systematics=False, wavelength_nm=wavelength_nm)) 

        if not template_frames:
            print("Warning: No sufficiently out-of-eclipse/transit frames found for template. Using first available frames. Template quality might be compromised.")
            template_frames = [self.generate_image(times[i], add_noise=False, inject_systematics=False, wavelength_nm=wavelength_nm) for i in range(min(num_frames, len(times)))]

        if not template_frames:
            raise ValueError("Could not generate any template frames.")

        template = np.mean(template_frames, axis=0)
        return template