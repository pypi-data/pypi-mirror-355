# pyexops/src/pyexops/simulator.py

import numpy as np
import matplotlib.pyplot as plt
from dask.distributed import Client, progress 
from dask import delayed 

# Import classes from within the package
from .star import Star, Spot
from .planet import Planet
from .scene import Scene
from .photometer import Photometer
from .orbital_solver import OrbitalSolver 

class TransitSimulator:
    """
    Main simulator class to run the transit simulation and generate a light curve.
    """
    def __init__(self, star: Star, planets: list[Planet], 
                 image_resolution: tuple, star_center_pixel: tuple, 
                 background_flux_per_pixel: float,
                 # Non-default arguments must come before default arguments
                 target_aperture_radius_pixels: float,
                 background_aperture_inner_radius_pixels: float,
                 background_aperture_outer_radius_pixels: float,
                 # Default arguments
                 read_noise_std: float = 5.0, 
                 psf_type: str = 'gaussian', 
                 psf_params: dict = None):
        
        self.star = star
        self.planets = planets
        
        # Store both components and the original tuple for flexibility
        self.star_center_pixel_x, self.star_center_pixel_y = star_center_pixel 
        self.star_center_pixel = star_center_pixel 

        # Initialize Scene (image generator)
        self.scene = Scene(star=star, planets=planets,
                           image_resolution=image_resolution,
                           star_center_pixel=star_center_pixel, 
                           background_flux_per_pixel=background_flux_per_pixel,
                           read_noise_std=read_noise_std, 
                           psf_type=psf_type, 
                           psf_params=psf_params) 
        
        # Initialize Photometer (flux extractor)
        self.photometer = Photometer(target_aperture_radius_pixels=target_aperture_radius_pixels,
                                     background_aperture_inner_radius_pixels=background_aperture_inner_radius_pixels,
                                     background_aperture_outer_radius_pixels=background_aperture_outer_radius_pixels,
                                     psf_kernel=self.scene.psf_kernel_for_photometry, 
                                     read_noise_std=read_noise_std)  
        
        self.image_resolution = image_resolution
        self.read_noise_std = read_noise_std 

    def get_simulation_images_for_visualization(self, times_for_viz: np.ndarray, add_noise: bool = True, inject_systematics: bool = False) -> tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray], tuple]:
        """
        Generates and collects image frames for visualization.
        :param times_for_viz: Array of specific time points for which to generate images.
        :param add_noise: Whether to add Poisson and Gaussian noise to each image.
        :param inject_systematics: Whether to inject a synthetic systematic trend.
        :return: (list_of_images, list_of_target_masks, list_of_background_masks, star_center_pixel)
        """
        images = []
        target_masks = []
        background_masks = []

        # Aperture masks are static in this simulator (star_center_pixel is fixed)
        # So, we define them once.
        target_mask, background_mask = self.photometer.define_apertures(
            self.star_center_pixel_x, self.star_center_pixel_y, self.image_resolution
        )
        
        print(f"Generating {len(times_for_viz)} images for interactive visualization.")
        for i, t in enumerate(times_for_viz):
            if i % (len(times_for_viz) // 10 + 1) == 0:
                print(f"  Visualization progress: {i / len(times_for_viz) * 100:.0f}% (Time: {t:.2f})")
            
            # For visualization, typically don't inject systematics into the image itself
            # Pass 'time' to generate_image for dynamic spots
            image = self.scene.generate_image(t, add_noise=add_noise, inject_systematics=inject_systematics)
            images.append(image)
            target_masks.append(target_mask) 
            background_masks.append(background_mask) 
        
        print("Image generation for visualization complete.")
        return images, target_masks, background_masks, self.star_center_pixel 

    def _process_single_frame(self, time: float, add_noise: bool, inject_systematics: bool,
                               photometry_method: str, target_mask: np.ndarray, background_mask: np.ndarray,
                               template_image: np.ndarray = None) -> float:
        """
        Helper function to generate an image and extract flux for a single time point.
        Designed to be easily parallelized with Dask.
        This method will be 'bound' to the simulator instance when called via dask.delayed.
        """
        # Pass 'time' to generate_image for dynamic spots
        image = self.scene.generate_image(time, add_noise=add_noise, inject_systematics=inject_systematics)
        
        extracted_flux = 0.0 

        if photometry_method == 'sap':
            extracted_flux, _ = self.photometer.extract_sap_flux(image, target_mask, background_mask)
        elif photometry_method == 'optimal':
            extracted_flux, _ = self.photometer.extract_optimal_flux(image, target_mask, background_mask, 
                                                                    self.star_center_pixel) 
        elif photometry_method == 'psf_fitting':
            # psf_fitting returns (flux, background, fitted_x, fitted_y). We only need flux here.
            extracted_flux, _, _, _ = self.photometer.extract_psf_fitting_flux(image, 
                                                                               self.star_center_pixel, 
                                                                               background_mask)
        elif photometry_method == 'dip':
            if template_image is None:
                raise ValueError("Template image must be provided for 'dip' photometry method.")
            extracted_flux, _ = self.photometer.extract_difference_imaging_flux(image, template_image, 
                                                                                 self.star_center_pixel,
                                                                                 background_mask)
        else:
            raise ValueError(f"Unknown photometry method: {photometry_method}")
        
        return extracted_flux

    def run_simulation(self, observation_times: np.ndarray, add_noise: bool = True, 
                       inject_systematics: bool = True, photometry_method: str = 'sap', 
                       dask_client: Client = None,
                       return_radial_velocity: bool = False, 
                       rv_instrumental_noise_std: float = 0.0, 
                       stellar_jitter_std: float = 0.0,
                       include_reflected_light: bool = False # NEW: Include planetary phase curve
                       ) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, np.ndarray | None]: # Return type updated
        """
        Runs the simulation over a specified array of observation times.
        :param observation_times: A numpy array of specific times (timestamps) at which to generate images.
                                  These times should ideally be sorted.
        :param add_noise: Whether to add Poisson and Gaussian noise to each image.
        :param inject_systematics: Whether to inject a synthetic systematic trend.
        :param photometry_method: Type of photometry to use ('sap', 'optimal', 'psf_fitting', 'dip').
        :param dask_client: Optional Dask client for parallel execution. If None, runs sequentially.
        :param return_radial_velocity: If True, calculates and returns the stellar radial velocity curve.
        :param rv_instrumental_noise_std: Standard deviation of Gaussian instrumental noise to add to RVs (m/s).
        :param stellar_jitter_std: Standard deviation of Gaussian stellar jitter noise to add to RVs (m/s).
        :param include_reflected_light: If True, calculates and adds the planetary reflected light (phase curve) to the total flux.
        :return: (times, fluxes, radial_velocities, reflected_fluxes) numpy arrays. fluxes are normalized.
                 radial_velocities is None if return_radial_velocity is False.
                 reflected_fluxes is None if include_reflected_light is False.
        """
        times = np.sort(np.unique(observation_times))

        # Define aperture masks once as star position is fixed relative to detector
        target_mask, background_mask = self.photometer.define_apertures(
            self.star_center_pixel_x, self.star_center_pixel_y, self.image_resolution
        )

        template_image = None
        if photometry_method == 'dip':
            print("Generating template image for Difference Imaging Photometry...")
            # Pass 'time' to generate_image for dynamic spots in template creation
            template_image = self.scene.generate_template_image(times, add_noise=False, inject_systematics=False) 

        print(f"Running simulation for {len(times)} observation points using {photometry_method.upper()} photometry...")
        print(f"Using PSF type: {self.scene.psf_type.capitalize()}")

        # Bind the process_single_frame method to the simulator instance for Dask serialization.
        process_func = self._process_single_frame

        if dask_client:
            print(f"Parallelizing with Dask client: {dask_client.dashboard_link}")
            delayed_results = []
            for t in times:
                delayed_result = delayed(process_func)(
                    time=t, 
                    add_noise=add_noise, 
                    inject_systematics=inject_systematics,
                    photometry_method=photometry_method, 
                    target_mask=target_mask, 
                    background_mask=background_mask,
                    template_image=template_image 
                )
                delayed_results.append(delayed_result)
            
            # Compute results and show progress
            futures = dask_client.compute(delayed_results)
            progress(futures)
            computed_fluxes = dask_client.gather(futures)
            fluxes = np.array(computed_fluxes)

        else: # Sequential execution
            print("Running sequentially (no Dask client provided).")
            fluxes = []
            for i, t in enumerate(times):
                if i % (len(times) // 10 + 1) == 0: 
                    print(f"  Progress: {i / len(times) * 100:.0f}% (Time: {t:.2f})")

                extracted_flux = process_func(
                    time=t, 
                    add_noise=add_noise, 
                    inject_systematics=inject_systematics,
                    photometry_method=photometry_method, 
                    target_mask=target_mask, 
                    background_mask=background_mask,
                    template_image=template_image
                )
                fluxes.append(extracted_flux)
            fluxes = np.array(fluxes)
        
        # Calculate Out-of-Transit (OOT) flux before adding phase curve or normalizing for flux-related noise
        # This is a rough estimate of the star's "normal" brightness for scaling purposes.
        # It's typically the max flux found if no deep transits are present, or median OOT.
        oot_flux_estimate = np.max(fluxes) 
        if oot_flux_estimate == 0:
            oot_flux_estimate = self.star.base_flux # Fallback if initial extraction yields zero
            if oot_flux_estimate == 0: oot_flux_estimate = 1.0 # Avoid division by zero

        # --- Reflected Light (Phase Curve) Calculation ---
        reflected_fluxes = None
        if include_reflected_light:
            print("Calculating planetary reflected light (phase curve)...")
            total_reflected_fluxes = np.zeros_like(times, dtype=np.float64)
            for planet in self.planets:
                if planet.albedo > 0: # Only calculate if planet has reflectivity
                    planet_reflected_fluxes = OrbitalSolver.calculate_reflected_flux(
                        star_flux_oot=oot_flux_estimate, # Use the estimated OOT flux for scaling
                        planet_radius_stellar_radii=planet.radius,
                        planet_semimajor_axis_stellar_radii=planet.semimajor_axis,
                        planet_period_days=planet.period,
                        planet_epoch_transit_days=planet.epoch_transit,
                        planet_albedo=planet.albedo,
                        times=times,
                        eccentricity=planet.eccentricity,
                        argument_of_periastron=np.rad2deg(planet.argument_of_periastron_rad)
                    )
                    total_reflected_fluxes += planet_reflected_fluxes
            
            fluxes += total_reflected_fluxes # Add reflected light to the extracted fluxes
            reflected_fluxes = total_reflected_fluxes # Store for return

            print("Planetary reflected light calculation complete.")


        # Normalize fluxes
        if oot_flux_estimate == 0: # Re-check after possible addition of reflected light
            normalized_fluxes = np.zeros_like(fluxes)
        else:
            normalized_fluxes = fluxes / oot_flux_estimate # Normalize by the original OOT estimate

        # --- Radial Velocity Calculation ---
        radial_velocities = None
        if return_radial_velocity:
            print("Calculating radial velocities...")
            # Sum RV contributions from all planets
            total_rvs = np.zeros_like(times, dtype=np.float64) 
            if self.star.star_mass <= 0:
                print("Warning: Star mass must be positive for RV calculation. Returning zeros.")
            else:
                for planet in self.planets:
                    # Pass all required parameters from star and planet objects
                    planet_rvs = OrbitalSolver.calculate_stellar_radial_velocity(
                        star_mass=self.star.star_mass,
                        planet_mass=planet.planet_mass,
                        period=planet.period,
                        semimajor_axis=planet.semimajor_axis,
                        inclination=np.rad2deg(planet.inclination_rad), 
                        epoch_transit=planet.epoch_transit,
                        eccentricity=planet.eccentricity,
                        argument_of_periastron=np.rad2deg(planet.argument_of_periastron_rad), 
                        times=times
                    )
                    total_rvs += planet_rvs 

            # Add noise to RVs
            if rv_instrumental_noise_std > 0:
                total_rvs += np.random.normal(0, rv_instrumental_noise_std, size=total_rvs.shape)
                print(f"  Added {rv_instrumental_noise_std:.2f} m/s instrumental noise to RVs.")
            if stellar_jitter_std > 0:
                total_rvs += np.random.normal(0, stellar_jitter_std, size=total_rvs.shape)
                print(f"  Added {stellar_jitter_std:.2f} m/s stellar jitter to RVs.")
            
            radial_velocities = total_rvs
            print("Radial velocity calculation complete.")

        return times, normalized_fluxes, radial_velocities, reflected_fluxes # Return reflected_fluxes

    def apply_pdcsap_detrending(self, times: np.ndarray, raw_fluxes: np.ndarray) -> np.ndarray:
        """
        Simulates the effect of PDCSAP detrending on a raw light curve.
        It attempts to remove systematic trends while protecting known transit signals.
        :param times: Array of time points.
        :param raw_fluxes: The raw, noisy, and systematic-laden flux measurements.
        :return: Detrended (PDCSAP-like) normalized fluxes.
        """
        detrended_fluxes = np.copy(raw_fluxes)
        
        transit_mask = np.ones_like(times, dtype=bool)
        
        if len(self.planets) > 0:
            masking_half_duration = 0.2 

            first_transit_idx = int(np.floor((times[0] - self.planets[0].epoch_transit) / self.planets[0].period))
            last_transit_idx = int(np.ceil((times[-1] - self.planets[0].epoch_transit) / self.planets[0].period))
            
            for n in range(first_transit_idx, last_transit_idx + 1):
                current_mid_transit_time = self.planets[0].epoch_transit + n * self.planets[0].period
                transit_mask[(times > (current_mid_transit_time - masking_half_duration)) & 
                             (times < (current_mid_transit_time + masking_half_duration))] = False

        if np.sum(transit_mask) < (len(times) * 0.1): 
            print("Warning: Insufficient out-of-transit data for robust detrending. Detrending might be unreliable.")
            oot_raw_flux = np.max(raw_fluxes) if np.max(raw_fluxes) != 0 else 1.0 
            return raw_fluxes / oot_raw_flux

        poly_degree = 2 
        
        if np.sum(transit_mask) <= poly_degree:
             print(f"Warning: Not enough OOT points ({np.sum(transit_mask)}) for polynomial degree {poly_degree}. Skipping detrending.")
             oot_raw_flux = np.max(raw_fluxes[transit_mask]) if np.sum(transit_mask) > 0 else (np.max(raw_fluxes) if np.max(raw_fluxes) != 0 else 1.0)
             return raw_fluxes / oot_raw_flux

        coeffs = np.polyfit(times[transit_mask], raw_fluxes[transit_mask], poly_degree)
        systematic_model = np.polyval(coeffs, times)

        detrended_fluxes = raw_fluxes - systematic_model + np.median(raw_fluxes[transit_mask]) 
        
        oot_detrended_flux = np.max(detrended_fluxes[transit_mask]) 
        if oot_detrended_flux == 0:
            detrended_fluxes = np.zeros_like(detrended_fluxes)
        else:
            detrended_fluxes = detrended_fluxes / oot_detrended_flux

        return detrended_fluxes