# pyexops/scene.py

import numpy as np
from scipy.ndimage import gaussian_filter, convolve
from scipy.special import j1 # For Airy Disk PSF
from scipy.optimize import curve_fit # For more robust centroid if needed

# Forward declaration for type hinting to avoid circular imports if needed
# from .star import Star
# from .planet import Planet

class Scene:
    """Generates an image frame at a given time."""
    def __init__(self, star: 'Star', planets: list['Planet'], 
                 image_resolution: tuple, star_center_pixel: tuple, 
                 background_flux_per_pixel: float = 0.0,
                 read_noise_std: float = 5.0, # Added read_noise_std to Scene
                 psf_type: str = 'gaussian', 
                 psf_params: dict = None):
        """
        Initializes the scene generator.
        :param star: The host Star object.
        :param planets: List of Planet objects.
        :param image_resolution: (width_pixels, height_pixels) of the image.
        :param star_center_pixel: (x_pixel, y_pixel) coordinates of the star's center in the image.
        :param background_flux_per_pixel: Constant background flux per pixel.
        :param read_noise_std: Standard deviation of Gaussian read noise per pixel.
        :param psf_type: Type of PSF to use ('gaussian', 'moffat', 'airy', 'elliptical_gaussian', 'combined').
        :param psf_params: Dictionary of parameters specific to the chosen PSF type.
                           - 'gaussian': {'sigma_pixels': float}\n
                           - 'moffat': {'fwhm_pixels': float, 'beta': float}\n
                           - 'airy': {'first_null_radius_pixels': float}\n
                           - 'elliptical_gaussian': {'sigma_x_pixels': float, 'sigma_y_pixels': float, 'angle_degrees': float}\n
                           - 'combined': {'components': list of dicts, each specifying a PSF type and its params}\n
        """
        self.star = star
        self.planets = planets
        self.width, self.height = image_resolution
        self.star_center_pixel_x, self.star_center_pixel_y = star_center_pixel
        self.background_flux_per_pixel = background_flux_per_pixel
        self.read_noise_std = read_noise_std # Stored for noise injection

        self.psf_type = psf_type.lower()
        self.psf_params = psf_params if psf_params is not None else {}

        # Store PSF parameters based on type
        if self.psf_type == 'gaussian':
            self.psf_sigma_pixels = self.psf_params.get('sigma_pixels', 1.5)
            if self.psf_sigma_pixels <= 0: self.psf_sigma_pixels = 0.001 
        elif self.psf_type == 'moffat':
            self.moffat_fwhm_pixels = self.psf_params.get('fwhm_pixels', 3.0)
            self.moffat_beta = self.psf_params.get('beta', 3.0) 
            if self.moffat_fwhm_pixels <= 0 or self.moffat_beta <= 0: raise ValueError("Moffat 'fwhm_pixels' and 'beta' must be positive.")
        elif self.psf_type == 'airy':
            self.airy_first_null_radius_pixels = self.psf_params.get('first_null_radius_pixels', 2.0)
            if self.airy_first_null_radius_pixels <= 0: raise ValueError("Airy 'first_null_radius_pixels' must be positive.")
        elif self.psf_type == 'elliptical_gaussian':
            self.elliptical_sigma_x_pixels = self.psf_params.get('sigma_x_pixels', 1.0)
            self.elliptical_sigma_y_pixels = self.psf_params.get('sigma_y_pixels', 1.5)
            self.elliptical_angle_degrees = self.psf_params.get('angle_degrees', 0.0)
            if self.elliptical_sigma_x_pixels <= 0 and self.elliptical_sigma_y_pixels <= 0: raise ValueError("Elliptical Gaussian at least one sigma must be positive.")
        elif self.psf_type == 'combined':
            self.combined_psf_components = self.psf_params.get('components', [])
            if not isinstance(self.combined_psf_components, list) or not self.combined_psf_components:
                raise ValueError("For 'combined' PSF, 'components' must be a non-empty list of dicts.")
        else:
            raise ValueError(f"Unknown PSF type: {psf_type}. Choose from 'gaussian', 'moffat', 'airy', 'elliptical_gaussian', 'combined'.")

        self.pixels_per_star_radius = self.star.radius 

        # Pre-generate representative PSF kernel for optimal photometry and PSF fitting
        self.psf_kernel_for_photometry = self._get_representative_psf_kernel()

    def _get_representative_psf_kernel(self, kernel_size_factor: int = 7) -> np.ndarray:
        """
        Generates a representative PSF kernel for use in photometric methods (Optimal, PSF Fitting).
        This kernel represents the 'ideal' shape of the PSF that photometer expects.
        """
        # For combined PSFs, we'll combine their kernels
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
                        # Convolve current kernel with existing combined kernel
                        # Pad smaller kernel if sizes differ
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
        """Internal helper to generate a Gaussian kernel for convolution or optimal phot."""
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
        """Generates a 2D Moffat PSF kernel."""
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
        """Generates a 2D Airy disk PSF kernel."""
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
        # Handle the r=0 case explicitly where j1(x)/x approaches 0.5
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
        """Generates a 2D elliptical Gaussian PSF kernel."""
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

    def generate_image(self, time: float, add_noise: bool = True, inject_systematics: bool = True) -> np.ndarray:
        """
        Generates a 2D numpy array representing the image at a given time.
        :param time: Current time.
        :param add_noise: Whether to add Poisson and Gaussian noise.
        :param inject_systematics: Whether to inject a synthetic systematic trend (for PDCSAP demo).
        :return: 2D numpy array (float) of image pixel values.
        """
        # Inject a simple systematic trend into the background flux for PDCSAP demo
        current_background_flux = self.background_flux_per_pixel
        if inject_systematics:
            # Example: a slow sinusoidal variation + a linear drift
            current_background_flux *= (1 + 0.05 * np.sin(time / 5.0) + 0.001 * time) # 5% variation, and 0.1% per day drift
            
        image = np.full((self.height, self.width), current_background_flux, dtype=float)
        
        planet_positions_stellar_radii = [p.get_position_at_time(time) for p in self.planets]

        for py in range(self.height):
            for px in range(self.width):
                x_pixel_from_center = (px - self.star_center_pixel_x)
                y_pixel_from_center = (py - self.star_center_pixel_y)

                x_rel_stellar_radii = x_pixel_from_center / self.pixels_per_star_radius
                y_rel_stellar_radii = y_pixel_from_center / self.pixels_per_star_radius

                star_flux_at_pixel = self.star.get_pixel_flux(x_rel_stellar_radii, y_rel_stellar_radii)
                
                for i, planet in enumerate(self.planets):
                    planet_x, planet_y = planet_positions_stellar_radii[i]
                    
                    dist_from_planet_center = np.sqrt((x_rel_stellar_radii - planet_x)**2 + (y_rel_stellar_radii - planet_y)**2)
                    if dist_from_planet_center < planet.radius: 
                        star_flux_at_pixel = 0.0 
                        break 

                image[py, px] += star_flux_at_pixel
        
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

        # Add noise
        if add_noise:
            # Poisson noise (photon noise)
            image = np.random.poisson(image).astype(float) 
            
            # Read noise (Gaussian)
            image += np.random.normal(0, self.read_noise_std, size=image.shape)
            
            # Ensure no negative flux after noise addition
            image[image < 0] = 0

        return image

    def generate_template_image(self, times: np.ndarray, num_frames: int = 10, add_noise: bool = True) -> np.ndarray:
        """
        Generates a template image by averaging multiple out-of-transit frames.
        Used for Difference Imaging Photometry.
        :param times: Full array of observation times.
        :param num_frames: Number of frames to average for the template.
        :param add_noise: Whether the individual frames should have noise (yes, for realism).
        :return: Averaged template image.
        """
        if len(times) < num_frames:
            raise ValueError(f"Cannot generate template: Not enough observation times ({len(times)}) for {num_frames} frames.")
        
        # Select num_frames evenly spaced frames that are preferably out-of-transit
        # For simplicity, let's just pick from start and end.
        indices_for_template = np.linspace(0, len(times) - 1, num_frames, dtype=int)
        template_frames = []
        for idx in indices_for_template:
            t = times[idx]
            # Ensure these frames are taken without a planet in transit for a clean template
            # (This is a simplification; real DIP uses OOT frames explicitly)
            is_in_transit = False
            for planet in self.planets:
                # Roughly check if planet is near transit
                # Needs more robust check than simple time window.
                # A full transit model could check for overlaps.
                # For now, let's just rely on visual inspection in simple examples or assume OOT selection.
                
                # A very rough estimate of when the planet is 'near' transit
                # This could be a refined check in future phases.
                planet_x_rel, planet_y_rel = planet.get_position_at_time(t)
                dist_from_center = np.sqrt(planet_x_rel**2 + planet_y_rel**2)
                if dist_from_center < (1.0 + planet.radius + 0.1): # Star radius + planet radius + buffer
                    is_in_transit = True
                    break
            
            if not is_in_transit:
                template_frames.append(self.generate_image(t, add_noise=add_noise, inject_systematics=False)) # Template should be clean of systematics if possible

        if not template_frames:
            print("Warning: No out-of-transit frames found for template. Using first available frames.")
            # Fallback if no clean OOT frames found based on rough check
            template_frames = [self.generate_image(times[i], add_noise=add_noise, inject_systematics=False) for i in range(min(num_frames, len(times)))]

        if not template_frames:
            raise ValueError("Could not generate any template frames.")

        template = np.mean(template_frames, axis=0)
        return template