# pyexops/simulator.py

import numpy as np
import matplotlib.pyplot as plt
from dask.distributed import Client, progress, LocalCluster # Import Dask components

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
                 # Moved these 3 parameters here, before any default arguments
                 target_aperture_radius_pixels: float,
                 background_aperture_inner_radius_pixels: float,
                 background_aperture_outer_radius_pixels: float,
                 # Optional parameters with default values
                 read_noise_std: float = 5.0, 
                 psf_type: str = 'gaussian', 
                 psf_params: dict = None):
        
        self.star = star
        self.planets = planets
        
        # Initialize Scene (image generator) with new PSF parameters and read_noise_std
        self.scene = Scene(star=star, planets=planets,
                           image_resolution=image_resolution,
                           star_center_pixel=star_center_pixel,
                           background_flux_per_pixel=background_flux_per_pixel,
                           read_noise_std=read_noise_std, 
                           psf_type=psf_type, 
                           psf_params=psf_params) 
        
        # Initialize Photometer (flux extractor) with PSF kernel and read_noise_std
        self.photometer = Photometer(target_aperture_radius_pixels=target_aperture_radius_pixels,
                                     background_aperture_inner_radius_pixels=background_aperture_inner_radius_pixels,
                                     background_aperture_outer_radius_pixels=background_aperture_outer_radius_pixels,
                                     psf_kernel=self.scene.psf_kernel_for_photometry, 
                                     read_noise_std=read_noise_std)  
        
        self.star_center_pixel_x, self.star_center_pixel_y = star_center_pixel
        self.image_resolution = image_resolution
        self.read_noise_std = read_noise_std 

    def _process_single_frame(self, time: float, add_noise: bool, inject_systematics: bool,
                               photometry_method: str, target_mask: np.ndarray, background_mask: np.ndarray,
                               template_image: np.ndarray = None) -> float:
        """
        Helper function to generate an image and extract flux for a single time point.
        Designed to be easily parallelized with Dask.
        """
        image = self.scene.generate_image(time, add_noise=add_noise, inject_systematics=inject_systematics)
        
        if photometry_method == 'sap':
            extracted_flux, _ = self.photometer.extract_sap_flux(image, target_mask, background_mask)
        elif photometry_method == 'optimal':
            extracted_flux, _ = self.photometer.extract_optimal_flux(image, target_mask, background_mask, 
                                                                    (self.star_center_pixel_x, self.star_center_pixel_y))
        elif photometry_method == 'psf_fitting':
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

        target_mask, background_mask = self.photometer.define_apertures(
            self.star_center_pixel_x, self.star_center_pixel_y, self.image_resolution
        )

        template_image = None
        if photometry_method == 'dip':
            print("Generating template image for Difference Imaging Photometry...")
            template_image = self.scene.generate_template_image(times, add_noise=False) 

        print(f"Running simulation for {len(times)} observation points using {photometry_method.upper()} photometry...")
        print(f"Using PSF type: {self.scene.psf_type.capitalize()}")

        process_func = self._process_single_frame

        if dask_client:
            print(f"Parallelizing with Dask client: {dask_client.dashboard_link}")
            delayed_results = []
            for t in times:
                delayed_result = dask_client.delayed(process_func)(
                    time=t, 
                    add_noise=add_noise, 
                    inject_systematics=inject_systematics,
                    photometry_method=photometry_method, 
                    target_mask=target_mask, 
                    background_mask=background_mask,
                    template_image=template_image
                )
                delayed_results.append(delayed_result)
            
            computed_fluxes = dask_client.compute(delayed_results)
            progress(computed_fluxes)
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
        
        oot_flux = np.max(fluxes) 
        if oot_flux == 0: 
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
            return raw_fluxes / np.max(raw_fluxes) 

        poly_degree = 2 
        
        if np.sum(transit_mask) <= poly_degree:
             print(f"Warning: Not enough OOT points ({np.sum(transit_mask)}) for polynomial degree {poly_degree}. Skipping detrending.")
             return raw_fluxes / np.max(raw_fluxes) 

        coeffs = np.polyfit(times[transit_mask], raw_fluxes[transit_mask], poly_degree)
        systematic_model = np.polyval(coeffs, times)

        detrended_fluxes = raw_fluxes - systematic_model + np.median(raw_fluxes[transit_mask]) 
        
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