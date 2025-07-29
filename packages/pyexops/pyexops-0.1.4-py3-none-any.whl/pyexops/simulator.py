# pyexops/src/pyexops/simulator.py

import numpy as np
import matplotlib.pyplot as plt
from dask.distributed import Client, progress # Import Dask components

# Import classes from within the package
from .star import Star, Spot
from .planet import Planet
from .scene import Scene
from .photometer import Photometer

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
        
        # Initialize Scene (image generator)
        self.scene = Scene(star=star, planets=planets,
                           image_resolution=image_resolution,
                           star_center_pixel=star_center_pixel,
                           background_flux_per_pixel=background_flux_per_pixel,
                           read_noise_std=read_noise_std, # Passed to Scene
                           psf_type=psf_type, 
                           psf_params=psf_params) 
        
        # Initialize Photometer (flux extractor)
        self.photometer = Photometer(target_aperture_radius_pixels=target_aperture_radius_pixels,
                                     background_aperture_inner_radius_pixels=background_aperture_inner_radius_pixels,
                                     background_aperture_outer_radius_pixels=background_aperture_outer_radius_pixels,
                                     psf_kernel=self.scene.psf_kernel_for_photometry, # Pass the representative PSF kernel
                                     read_noise_std=read_noise_std)  # Passed to Photometer
        
        self.star_center_pixel_x, self.star_center_pixel_y = star_center_pixel
        self.image_resolution = image_resolution
        self.read_noise_std = read_noise_std # Stored in simulator for consistent noise level reference

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
        # So we define them once.
        target_mask, background_mask = self.photometer.define_apertures(
            self.star_center_pixel_x, self.star_center_pixel_y, self.image_resolution
        )
        
        print(f"Generating {len(times_for_viz)} images for interactive visualization...")
        for i, t in enumerate(times_for_viz):
            if i % (len(times_for_viz) // 10 + 1) == 0:
                print(f"  Visualization progress: {i / len(times_for_viz) * 100:.0f}% (Time: {t:.2f})")
            
            # For visualization, typically don't inject systematics into the image itself
            image = self.scene.generate_image(t, add_noise=add_noise, inject_systematics=inject_systematics)
            images.append(image)
            target_masks.append(target_mask) # Append the same mask for each frame
            background_masks.append(background_mask) # Append the same mask for each frame
        
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
        # Access scene and photometer from self
        image = self.scene.generate_image(time, add_noise=add_noise, inject_systematics=inject_systematics)
        
        extracted_flux = 0.0 # Initialize

        if photometry_method == 'sap':
            extracted_flux, _ = self.photometer.extract_sap_flux(image, target_mask, background_mask)
        elif photometry_method == 'optimal':
            extracted_flux, _ = self.photometer.extract_optimal_flux(image, target_mask, background_mask, 
                                                                    (self.star_center_pixel_x, self.star_center_pixel_y))
        elif photometry_method == 'psf_fitting':
            # psf_fitting returns (flux, background, fitted_x, fitted_y). We only need flux here.
            extracted_flux, _, _, _ = self.photometer.extract_psf_fitting_flux(image, 
                                                                               (self.star_center_pixel_x, self.star_center_pixel_y), 
                                                                               background_mask)
        elif photometry_method == 'dip':
            if template_image is None:
                raise ValueError("Template image must be provided for 'dip' photometry method.")
            extracted_flux, _ = self.photometer.extract_difference_imaging_flux(image, template_image, 
                                                                                 (self.star_center_pixel_x, self.star_center_pixel_y),
                                                                                 background_mask)
        else:
            raise ValueError(f"Unknown photometry method: {photometry_method}")
        
        return extracted_flux

    def run_simulation(self, observation_times: np.ndarray, add_noise: bool = True, 
                       inject_systematics: bool = True, photometry_method: str = 'sap', 
                       dask_client: Client = None) -> tuple[np.ndarray, np.ndarray]:
        """
        Runs the simulation over a specified array of observation times.
        :param observation_times: A numpy array of specific times (timestamps) at which to generate images.
                                  These times should ideally be sorted.
        :param add_noise: Whether to add Poisson and Gaussian noise to each image.
        :param inject_systematics: Whether to inject a synthetic systematic trend.
        :param photometry_method: Type of photometry to use ('sap', 'optimal', 'psf_fitting', 'dip').
        :param dask_client: Optional Dask client for parallel execution. If None, runs sequentially.
        :return: (times, fluxes) numpy arrays. fluxes are normalized.
        """
        times = np.sort(np.unique(observation_times))

        # Define aperture masks once as star position is fixed relative to detector
        target_mask, background_mask = self.photometer.define_apertures(
            self.star_center_pixel_x, self.star_center_pixel_y, self.image_resolution
        )

        template_image = None
        if photometry_method == 'dip':
            print("Generating template image for Difference Imaging Photometry...")
            # Template image should typically be generated without noise or systematics for best results
            template_image = self.scene.generate_template_image(times, add_noise=False, inject_systematics=False) 

        print(f"Running simulation for {len(times)} observation points using {photometry_method.upper()} photometry...")
        print(f"Using PSF type: {self.scene.psf_type.capitalize()}")

        # Bind the process_single_frame method to the simulator instance for Dask serialization.
        # This creates a callable that Dask can serialize, carrying 'self' with it.
        process_func = self._process_single_frame

        if dask_client:
            print(f"Parallelizing with Dask client: {dask_client.dashboard_link}")
            delayed_results = []
            for t in times:
                delayed_result = dask_client.delayed(process_func)( # Pass the bound method
                    time=t, 
                    add_noise=add_noise, 
                    inject_systematics=inject_systematics,
                    photometry_method=photometry_method, 
                    target_mask=target_mask, 
                    background_mask=background_mask,
                    template_image=template_image # Will be None if photometry_method is not 'dip'
                )
                delayed_results.append(delayed_result)
            
            # Compute results and show progress
            computed_fluxes = dask_client.compute(delayed_results)
            progress(computed_fluxes) # Show progress bar for Dask computation
            fluxes = np.array(computed_fluxes)

        else: # Sequential execution if no Dask client is provided
            print("Running sequentially (no Dask client provided).")
            fluxes = []
            for i, t in enumerate(times):
                if i % (len(times) // 10 + 1) == 0: 
                    print(f"  Progress: {i / len(times) * 100:.0f}% (Time: {t:.2f})")

                extracted_flux = process_func( # Call the bound method directly
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
        
        # Normalize the light curve to the out-of-transit (OOT) flux
        oot_flux = np.max(fluxes) 
        if oot_flux == 0: # Avoid division by zero if no flux was detected
            normalized_fluxes = np.zeros_like(fluxes)
        else:
            normalized_fluxes = fluxes / oot_flux
        
        return times, normalized_fluxes

    def apply_pdcsap_detrending(self, times: np.ndarray, raw_fluxes: np.ndarray) -> np.ndarray:
        """
        Simulates the effect of PDCSAP detrending on a raw light curve.
        It attempts to remove systematic trends while protecting known transit signals.
        :param times: Array of time points.
        :param raw_fluxes: The raw, noisy, and systematic-laden flux measurements.
        :return: Detrended (PDCSAP-like) normalized fluxes.
        """
        detrended_fluxes = np.copy(raw_fluxes)
        
        # 1. Mask Transits (Crucial for PDCSAP-like behavior)
        # Create a boolean mask where True indicates data OUTSIDE of a transit
        transit_mask = np.ones_like(times, dtype=bool)
        
        if len(self.planets) > 0:
            # For this demo, use a fixed buffer around mid-transit for masking.
            # In a real scenario, this would be computed from transit duration.
            masking_half_duration = 0.2 # days

            # Identify all transit epochs within the simulation time
            first_transit_idx = int(np.floor((times[0] - self.planets[0].epoch_transit) / self.planets[0].period))
            last_transit_idx = int(np.ceil((times[-1] - self.planets[0].epoch_transit) / self.planets[0].period))
            
            for n in range(first_transit_idx, last_transit_idx + 1):
                current_mid_transit_time = self.planets[0].epoch_transit + n * self.planets[0].period
                # Pixels within transit window are marked as False (to be excluded from detrending model)
                transit_mask[(times > (current_mid_transit_time - masking_half_duration)) & 
                             (times < (current_mid_transit_time + masking_half_duration))] = False

        if np.sum(transit_mask) < (len(times) * 0.1): # Ensure at least 10% OOT data for detrending
            print("Warning: Insufficient out-of-transit data for robust detrending. Detrending might be unreliable.")
            # If detrending cannot be applied, return the raw fluxes, normalized to their OOT max
            oot_raw_flux = np.max(raw_fluxes) if np.max(raw_fluxes) != 0 else 1.0 # Avoid div by zero
            return raw_fluxes / oot_raw_flux

        # 2. Build a Detrending Model (e.g., a simple polynomial for systematic drifts)
        # Only fit the model to the out-of-transit data
        poly_degree = 2 # Low-order polynomial for general trends
        
        # Check if there's enough data points for the polynomial fit
        if np.sum(transit_mask) <= poly_degree:
             print(f"Warning: Not enough OOT points ({np.sum(transit_mask)}) for polynomial degree {poly_degree}. Skipping detrending.")
             # If detrending cannot be applied, return the raw fluxes, normalized to their OOT max
             oot_raw_flux = np.max(raw_fluxes[transit_mask]) if np.sum(transit_mask) > 0 else (np.max(raw_fluxes) if np.max(raw_fluxes) != 0 else 1.0)
             return raw_fluxes / oot_raw_flux

        coeffs = np.polyfit(times[transit_mask], raw_fluxes[transit_mask], poly_degree)
        systematic_model = np.polyval(coeffs, times)

        # 3. Subtract the systematic model from the entire light curve
        # Re-center the detrended curve by adding the median of the OOT raw fluxes
        detrended_fluxes = raw_fluxes - systematic_model + np.median(raw_fluxes[transit_mask]) 
        
        # Re-normalize (PDCSAP often normalizes the final light curve again)
        # Normalize to the new OOT level based on the detrended OOT data
        oot_detrended_flux = np.max(detrended_fluxes[transit_mask]) 
        if oot_detrended_flux == 0:
            detrended_fluxes = np.zeros_like(detrended_fluxes)
        else:
            detrended_fluxes = detrended_fluxes / oot_detrended_flux

        return detrended_fluxes

    def plot_light_curve(self, times: np.ndarray, fluxes: np.ndarray, title: str = "Simulated Light Curve"):
        """Plots the generated light curve."""
        plt.figure(figsize=(12, 6))
        plt.plot(times, fluxes, marker='.', linestyle='-', markersize=2, linewidth=0.7)
        plt.xlabel("Time (arbitrary units, e.g., days)")
        plt.ylabel("Normalized Flux")
        plt.title(title)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()