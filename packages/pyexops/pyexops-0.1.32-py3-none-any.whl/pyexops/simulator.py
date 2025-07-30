# pyexops/src/pyexops/simulator.py

import numpy as np
import matplotlib.pyplot as plt
from dask.distributed import Client, progress 
from dask import delayed 
from typing import Optional, Union, Dict, Tuple, List 

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
    def __init__(self, star: Star, planets: List[Planet], 
                 image_resolution: Tuple[int, int], star_center_pixel: Tuple[int, int], 
                 background_flux_per_pixel: float,
                 target_aperture_radius_pixels: float,
                 background_aperture_inner_radius_pixels: float,
                 background_aperture_outer_radius_pixels: float,
                 read_noise_std: float = 5.0, 
                 psf_type: str = 'gaussian', 
                 psf_params: Optional[dict] = None,
                 pointing_jitter_std_pixels: float = 0.0, 
                 pixel_response_non_uniformity_map: Optional[np.ndarray] = None): 
        
        self.star = star
        self.planets = planets
        
        self.star_center_pixel_x, self.star_center_pixel_y = star_center_pixel 
        self.star_center_pixel = star_center_pixel 

        self.scene = Scene(star=star, planets=planets,
                           image_resolution=image_resolution,
                           star_center_pixel=star_center_pixel, 
                           background_flux_per_pixel=background_flux_per_pixel,
                           read_noise_std=read_noise_std, 
                           psf_type=psf_type, 
                           psf_params=psf_params,
                           pointing_jitter_std_pixels=pointing_jitter_std_pixels, 
                           pixel_response_non_uniformity_map=pixel_response_non_uniformity_map) 
        
        self.photometer = Photometer(target_aperture_radius_pixels=target_aperture_radius_pixels,
                                     background_aperture_inner_radius_pixels=background_aperture_inner_radius_pixels,
                                     background_aperture_outer_radius_pixels=background_aperture_outer_radius_pixels,
                                     psf_kernel=self.scene.psf_kernel_for_photometry, 
                                     read_noise_std=read_noise_std,
                                     star_center_pixel=star_center_pixel) 
        
        self.image_resolution = image_resolution
        self.read_noise_std = read_noise_std 

    def get_simulation_images_for_visualization(self, times_for_viz: np.ndarray, add_noise: bool = True, inject_systematics: bool = False,
                                                wavelength_nm: Optional[float] = None) -> Tuple[List[np.ndarray], List[np.ndarray], List[np.ndarray], Tuple[int, int]]:
        """
        Generates and collects image frames for visualization.
        :param times_for_viz: Array of specific time points for which to generate images.
        :param add_noise: Whether to add Poisson and Gaussian noise to each image.
        :param inject_systematics: Whether to inject a synthetic systematic trend.
        :param wavelength_nm: Optional wavelength in nanometers. Passed to generate_image.
        :return: (list_of_images, list_of_target_masks, list_of_background_masks, star_center_pixel)
        """
        images = []
        target_masks = []
        background_masks = []

        target_mask, background_mask = self.photometer.define_apertures(
            self.star_center_pixel_x, self.star_center_pixel_y, self.image_resolution
        )
        
        print(f"Generating {len(times_for_viz)} images for interactive visualization.")
        for i, t in enumerate(times_for_viz):
            if i % (len(times_for_viz) // 10 + 1) == 0:
                print(f"  Visualization progress: {i / len(times_for_viz) * 100:.0f}% (Time: {t:.2f})")
            
            image = self.scene.generate_image(t, add_noise=add_noise, inject_systematics=inject_systematics, wavelength_nm=wavelength_nm)
            images.append(image)
            target_masks.append(target_mask) 
            background_masks.append(background_mask) 
        
        print("Image generation for visualization complete.")
        return images, target_masks, background_masks, self.star_center_pixel 

    def _process_single_frame(self, time: float, add_noise: bool, inject_systematics: bool,
                               photometry_method: str, target_mask: np.ndarray, background_mask: np.ndarray,
                               template_image: Optional[np.ndarray] = None,
                               wavelength_nm: Optional[float] = None,
                               perform_image_alignment: bool = False, 
                               apply_dip_psf_matching: bool = False 
                               ) -> float: 
        """
        Helper function to generate an image and extract flux for a single time point.
        Designed to be easily parallelized with Dask.
        :param time: Current time.
        :param add_noise: Whether to add Poisson and Gaussian noise.
        :param inject_systematics: Whether to inject a synthetic systematic trend.
        :param photometry_method: Type of photometry to use.
        :param target_mask: Boolean mask for target aperture.
        :param background_mask: Boolean mask for background aperture.
        :param template_image: Optional template image for DIP.
        :param wavelength_nm: Optional wavelength in nanometers. Passed to generate_image.
        :param perform_image_alignment: If True, performs image alignment in DIP.
        :param apply_dip_psf_matching: If True, applies PSF matching kernel in DIP.
        :return: Extracted flux for the single frame.
        """
        image = self.scene.generate_image(time, add_noise=add_noise, inject_systematics=inject_systematics, wavelength_nm=wavelength_nm)
        
        extracted_flux = 0.0 

        if photometry_method == 'sap':
            extracted_flux, _ = self.photometer.extract_sap_flux(image, target_mask, background_mask)
        elif photometry_method == 'optimal':
            extracted_flux, _ = self.photometer.extract_optimal_flux(image, target_mask, background_mask, 
                                                                    self.star_center_pixel) 
        elif photometry_method == 'psf_fitting':
            extracted_flux, _, _, _ = self.photometer.extract_psf_fitting_flux(image, 
                                                                               self.star_center_pixel, 
                                                                               background_mask)
        elif photometry_method == 'dip':
            if template_image is None:
                raise ValueError("Template image must be provided for 'dip' photometry method.")
            extracted_flux, _ = self.photometer.extract_difference_imaging_flux(
                image, template_image, self.star_center_pixel, background_mask,
                perform_alignment=perform_image_alignment, 
                apply_psf_matching_kernel=apply_dip_psf_matching 
            )
        else:
            raise ValueError(f"Unknown photometry method: {photometry_method}")
        
        return extracted_flux

    def run_simulation(self, observation_times: np.ndarray, add_noise: bool = True, 
                       inject_systematics: bool = True, photometry_method: str = 'sap', 
                       dask_client: Optional[Client] = None,
                       return_radial_velocity: bool = False, 
                       rv_instrumental_noise_std: float = 0.0, 
                       stellar_jitter_std: float = 0.0,
                       include_reflected_light: bool = False, 
                       wavelength_nm: Optional[float] = None,
                       perform_image_alignment: bool = False, 
                       apply_dip_psf_matching: bool = False,
                       include_doppler_beaming: bool = False, # NEW
                       stellar_spectral_index: float = 3.0, # NEW
                       include_ellipsoidal_variations: bool = False, # NEW
                       stellar_gravity_darkening_coeff: float = 0.32 # NEW
                       ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]: 
        """
        Runs the simulation over a specified array of observation times for a single wavelength band.
        :param observation_times: A numpy array of specific times (timestamps) at which to generate images.
                                  These times should ideally be sorted.
        :param add_noise: Whether to add Poisson and Gaussian noise.
        :param inject_systematics: Whether to inject a synthetic systematic trend.
        :param photometry_method: Type of photometry to use.
        :param dask_client: Optional Dask client for parallel execution. If None, runs sequentially.
        :param return_radial_velocity: If True, calculates and returns the stellar radial velocity curve.
        :param rv_instrumental_noise_std: Standard deviation of Gaussian instrumental noise to add to RVs (m/s).
        :param stellar_jitter_std: Standard deviation of Gaussian stellar jitter noise to add to RVs (m/s).
        :param include_reflected_light: If True, calculates and adds the planetary reflected light (phase curve) to the total flux.
        :param wavelength_nm: Optional wavelength in nanometers. If provided and planet has atmosphere,
                              effective planet radius will be used for occultation.
        :param perform_image_alignment: If True, uses Astrometry to align image_data to template_image during DIP.
        :param apply_dip_psf_matching: If True, convolves the template_image with the photometer's psf_kernel
                                       before subtraction during DIP, to attempt PSF matching.
        :param include_doppler_beaming: If True, includes flux variations due to stellar Doppler beaming.
        :param stellar_spectral_index: Spectral index of the star for Doppler beaming calculation.
        :param include_ellipsoidal_variations: If True, includes flux variations due to stellar ellipsoidal deformation.
        :param stellar_gravity_darkening_coeff: Gravity darkening exponent for ellipsoidal variations.
        :return: (times, fluxes, radial_velocities, reflected_fluxes) numpy arrays. fluxes are normalized.
                 radial_velocities is None if return_radial_velocity is False.
                 reflected_fluxes is None if include_reflected_light is False.
        """
        times = np.sort(np.unique(observation_times))

        target_mask, background_mask = self.photometer.define_apertures(
            self.star_center_pixel_x, self.star_center_pixel_y, self.image_resolution
        )

        template_image = None
        if photometry_method == 'dip':
            print("Generating template image for Difference Imaging Photometry...")
            template_image = self.scene.generate_template_image(times, wavelength_nm=wavelength_nm) 

        print(f"Running simulation for {len(times)} observation points using {photometry_method.upper()} photometry...")
        print(f"Using PSF type: {self.scene.psf_type.capitalize()}")
        if wavelength_nm is not None:
            print(f"  at Wavelength: {wavelength_nm:.1f} nm")
        if photometry_method == 'dip':
            print(f"  DIP alignment: {perform_image_alignment}, DIP PSF matching: {apply_dip_psf_matching}")

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
                    template_image=template_image,
                    wavelength_nm=wavelength_nm,
                    perform_image_alignment=perform_image_alignment, 
                    apply_dip_psf_matching=apply_dip_psf_matching 
                )
                delayed_results.append(delayed_result)
            
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
                    template_image=template_image,
                    wavelength_nm=wavelength_nm 
                )
                fluxes.append(extracted_flux)
            fluxes = np.array(fluxes)
        
        # --- Astrophyiscal Subtle Effects ---
        # Determine the out-of-transit flux AFTER instrumental effects but BEFORE adding other astrophysical effects
        # (like reflected light, beaming, ellipsoidal) so these are relative to a stable star.
        oot_flux_estimate = np.max(fluxes) 
        if oot_flux_estimate == 0:
            oot_flux_estimate = self.star.base_flux 
            if oot_flux_estimate == 0: oot_flux_estimate = 1.0 

        # Radial Velocity (re-calculate if needed for beaming, or if explicitly requested)
        radial_velocities_unnoised = None
        # RVs are needed for Beaming, and planet/star masses are needed for Ellipsoidal variation calculation
        # So we calculate RVs if either beaming or ellipsoidal variations are requested, or if return_radial_velocity is True.
        if return_radial_velocity or include_doppler_beaming or include_ellipsoidal_variations: 
            print("Calculating stellar radial velocities (for subtle effects context)...")
            total_rvs_unnoised = np.zeros_like(times, dtype=np.float64) 
            if self.star.star_mass <= 0:
                print("Warning: Star mass must be positive for RV/beaming/ellipsoidal calculation. Returning zeros for RVs.")
            else:
                for planet in self.planets:
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
                    total_rvs_unnoised += planet_rvs
            radial_velocities_unnoised = total_rvs_unnoised
        
        # Doppler Beaming
        if include_doppler_beaming and radial_velocities_unnoised is not None:
            print("Applying Doppler beaming effect...")
            beaming_factors = OrbitalSolver.calculate_doppler_beaming_factor(
                stellar_radial_velocity_ms=radial_velocities_unnoised,
                stellar_spectral_index=stellar_spectral_index
            )
            fluxes *= beaming_factors
            print("Doppler beaming effect applied.")

        # Ellipsoidal Variations
        if include_ellipsoidal_variations:
            print("Applying ellipsoidal variations effect...")
            total_ellipsoidal_factors = np.ones_like(times, dtype=np.float64) 
            for planet in self.planets:
                if self.star.star_mass > 0 and planet.planet_mass > 0: # Ensure valid masses
                    ellipsoidal_factors_planet = OrbitalSolver.calculate_ellipsoidal_variation_factor(
                        star_mass_solar=self.star.star_mass,
                        planet_mass_jupiter=planet.planet_mass,
                        star_radius_stellar_radii=self.star.radius, 
                        planet_semimajor_axis_stellar_radii=planet.semimajor_axis,
                        inclination_deg=np.rad2deg(planet.inclination_rad),
                        period_days=planet.period,
                        epoch_transit_days=planet.epoch_transit,
                        times_days=times,
                        stellar_gravity_darkening_coeff=stellar_gravity_darkening_coeff,
                        stellar_limb_darkening_coeffs=(self.star.u1, self.star.u2) # CORRECTED: Access u1, u2 directly
                    )
                    total_ellipsoidal_factors *= ellipsoidal_factors_planet 
                else:
                    print(f"Warning: Skipping ellipsoidal variations for a planet with invalid mass or star with invalid mass (Planet mass: {planet.planet_mass}, Star mass: {self.star.star_mass})")

            fluxes *= total_ellipsoidal_factors
            print("Ellipsoidal variations effect applied.")

        # Reflected Light (Phase Curve) - already existing logic
        reflected_fluxes = None
        if include_reflected_light:
            print("Calculating planetary reflected light (phase curve)...")
            total_reflected_fluxes = np.zeros_like(times, dtype=np.float64)
            for planet in self.planets:
                if planet.albedo > 0: 
                    planet_reflected_fluxes = OrbitalSolver.calculate_reflected_flux(
                        star_flux_oot=oot_flux_estimate, 
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
            
            fluxes += total_reflected_fluxes 
            reflected_fluxes = total_reflected_fluxes 

            print("Planetary reflected light calculation complete.")

        # Add RV noise if RVs were calculated and noise parameters are provided
        radial_velocities = None
        if return_radial_velocity and radial_velocities_unnoised is not None:
            radial_velocities = radial_velocities_unnoised.copy() # Make a copy to add noise
            if rv_instrumental_noise_std > 0:
                radial_velocities += np.random.normal(0, rv_instrumental_noise_std, size=radial_velocities.shape)
                print(f"  Added {rv_instrumental_noise_std:.2f} m/s instrumental noise to RVs.")
            if stellar_jitter_std > 0:
                radial_velocities += np.random.normal(0, stellar_jitter_std, size=radial_velocities.shape)
                print(f"  Added {stellar_jitter_std:.2f} m/s stellar jitter to RVs.")
            print("Radial velocity curve finalized.")


        return times, normalized_fluxes, radial_velocities, reflected_fluxes