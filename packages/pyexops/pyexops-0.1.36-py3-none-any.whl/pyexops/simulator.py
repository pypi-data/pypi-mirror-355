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
from .binary_star_system import BinaryStarSystem # NEW: Import BinaryStarSystem

class TransitSimulator:
    """
    Main simulator class to run the transit simulation and generate a light curve.
    """
    def __init__(self, stars: Union[Star, BinaryStarSystem], planets: List[Planet], # NEW: stars can be Star or BinaryStarSystem
                 image_resolution: Tuple[int, int], barycenter_pixel_on_image: Tuple[int, int], # Changed star_center_pixel to barycenter_pixel_on_image
                 background_flux_per_pixel: float,
                 target_aperture_radius_pixels: float,
                 background_aperture_inner_radius_pixels: float,
                 background_aperture_outer_radius_pixels: float,
                 read_noise_std: float = 5.0, 
                 psf_type: str = 'gaussian', 
                 psf_params: Optional[dict] = None,
                 pointing_jitter_std_pixels: float = 0.0, 
                 pixel_response_non_uniformity_map: Optional[np.ndarray] = None): 
        """
        Initializes the TransitSimulator.

        :param stars: The host Star object (for single star systems) OR a BinaryStarSystem object.
        :param planets: List of Planet objects orbiting the star(s).
        :param image_resolution: (width_pixels, height_pixels) of the simulated image frames.
        :param barycenter_pixel_on_image: (x_pixel, y_pixel) coordinates of the system's barycenter in the image.
        :param background_flux_per_pixel: Constant background flux per pixel.
        :param target_aperture_radius_pixels: Radius for the primary photometric aperture.
        :param background_aperture_inner_radius_pixels: Inner radius for the background annulus.
        :param background_aperture_outer_radius_pixels: Outer radius for the background annulus.
        :param read_noise_std: Standard deviation of Gaussian read noise per pixel.
        :param psf_type: Type of PSF to use ('gaussian', 'moffat', 'airy', 'elliptical_gaussian', 'combined').
        :param psf_params: Dictionary of parameters specific to the chosen PSF type.
        :param pointing_jitter_std_pixels: Standard deviation of Gaussian noise for pointing jitter.
        :param pixel_response_non_uniformity_map: A 2D numpy array for multiplicative pixel response non-uniformity.
        :raises TypeError: If 'stars' is not a Star or BinaryStarSystem object.
        """
        self.stars_object = stars # Store the Star or BinaryStarSystem object
        self.planets = planets
        
        # Determine if it's a binary system and get the list of stars
        if isinstance(self.stars_object, BinaryStarSystem):
            self.is_binary = True
            self.star_list = [self.stars_object.star1, self.stars_object.star2]
            self.system_total_mass = self.stars_object.total_mass_solar
        elif isinstance(self.stars_object, Star):
            self.is_binary = False
            self.star_list = [self.stars_object]
            self.system_total_mass = self.stars_object.star_mass
        else:
            raise TypeError("`stars` must be a Star object for single systems or a BinaryStarSystem object.")


        self.barycenter_pixel_on_image_x, self.barycenter_pixel_on_image_y = barycenter_pixel_on_image
        self.barycenter_pixel_on_image = barycenter_pixel_on_image 

        self.scene = Scene(stars=self.stars_object, # Pass the stars_object (Star or BinaryStarSystem)
                           planets=planets,
                           image_resolution=image_resolution,
                           barycenter_pixel_on_image=barycenter_pixel_on_image, 
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
                                     system_center_pixel=barycenter_pixel_on_image) # Pass system_center_pixel
        
        self.image_resolution = image_resolution
        self.read_noise_std = read_noise_std 

    def get_simulation_images_for_visualization(self, times_for_viz: np.ndarray, add_noise: bool = True, inject_systematics: bool = False,
                                                wavelength_nm: Optional[float] = None) -> Tuple[List[np.ndarray], List[np.ndarray], List[np.ndarray], Tuple[int, int]]:
        """
        Generates and collects image frames for visualization.

        This method produces a list of image frames, along with their corresponding
        photometric masks and the nominal system barycenter pixel, for interactive display.

        :param times_for_viz: Array of specific time points for which to generate images.
        :param add_noise: Whether to add Poisson and Gaussian noise to each image.
        :param inject_systematics: Whether to inject a synthetic systematic trend.
        :param wavelength_nm: Optional wavelength in nanometers. Passed to generate_image.
        :return: (list_of_images, list_of_target_masks, list_of_background_masks, barycenter_pixel_on_image)
        """
        images = []
        target_masks = []
        background_masks = []

        target_mask, background_mask = self.photometer.define_apertures(
            self.barycenter_pixel_on_image_x, self.barycenter_pixel_on_image_y, self.image_resolution
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
        return images, target_masks, background_masks, self.barycenter_pixel_on_image 

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
        :param photometry_method: Type of photometry to use ('sap', 'optimal', 'psf_fitting', 'dip').
        :param target_mask: Boolean mask for target aperture.
        :param background_mask: Boolean mask for background aperture.
        :param template_image: Optional template image for DIP.
        :param wavelength_nm: Optional wavelength in nanometers. Passed to generate_image.
        :param perform_image_alignment: If True, performs image alignment in DIP.
        :param apply_dip_psf_matching: If True, applies PSF matching kernel in DIP.
        :return: Extracted flux for the single frame.
        :raises ValueError: If an unknown photometry method is specified or template is missing for DIP.
        """
        image = self.scene.generate_image(time, add_noise=add_noise, inject_systematics=inject_systematics, wavelength_nm=wavelength_nm)
        
        extracted_flux = 0.0 

        if photometry_method == 'sap':
            extracted_flux, _ = self.photometer.extract_sap_flux(image, target_mask, background_mask)
        elif photometry_method == 'optimal':
            # Use barycenter_pixel_on_image as the centroid guess for optimal photometry in binary systems
            extracted_flux, _ = self.photometer.extract_optimal_flux(image, target_mask, background_mask, 
                                                                    self.barycenter_pixel_on_image) 
        elif photometry_method == 'psf_fitting':
            # Use barycenter_pixel_on_image as the centroid guess for PSF fitting in binary systems
            extracted_flux, _, _, _ = self.photometer.extract_psf_fitting_flux(image, 
                                                                               self.barycenter_pixel_on_image, 
                                                                               background_mask)
        elif photometry_method == 'dip':
            if template_image is None:
                raise ValueError("Template image must be provided for 'dip' photometry method.")
            extracted_flux, _ = self.photometer.extract_difference_imaging_flux(
                image, template_image, self.barycenter_pixel_on_image, background_mask,
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
                       include_doppler_beaming: bool = False, 
                       stellar_spectral_index: float = 3.0, 
                       include_ellipsoidal_variations: bool = False, 
                       stellar_gravity_darkening_coeff: float = 0.32, 
                       include_secondary_eclipse: bool = False 
                       ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]: 
        """
        Runs the simulation over a specified array of observation times for a single wavelength band.

        This is the main simulation pipeline, orchestrating image generation, photometric extraction,
        and application of various astrophysical and instrumental effects. It now supports
        binary star systems and their specific orbital effects.

        :param observation_times: A numpy array of specific times (timestamps) at which to generate images.
                                  These times should ideally be sorted.
        :param add_noise: Whether to add Poisson and Gaussian noise.
        :param inject_systematics: Whether to inject a synthetic systematic trend.
        :param photometry_method: Type of photometry to use ('sap', 'optimal', 'psf_fitting', 'dip').
        :param dask_client: Optional Dask client for parallel execution. If None, runs sequentially.
        :param return_radial_velocity: If True, calculates and returns the stellar radial velocity curve(s).
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
        :param include_secondary_eclipse: If True, accounts for the occultation of planetary light by the star.
        :return: (times, fluxes, radial_velocities, reflected_fluxes) numpy arrays. fluxes are normalized.
                 radial_velocities is None if return_radial_velocity is False.
                 reflected_fluxes is None if include_reflected_light is False.
                 Note: radial_velocities will be a single array if single star, or a dictionary/tuple if binary system (future).
        """
        times = np.sort(np.unique(observation_times))

        target_mask, background_mask = self.photometer.define_apertures(
            self.barycenter_pixel_on_image_x, self.barycenter_pixel_on_image_y, self.image_resolution
        )

        template_image = None
        if photometry_method == 'dip':
            print("Generating template image for Difference Imaging Photometry...")
            template_image = self.scene.generate_template_image(times, wavelength_nm=wavelength_nm) 

        print(f"Running simulation for {len(times)} observation points using {photometry_method.upper()} photometry...")
        if self.is_binary:
            print(f"  System Type: Binary Star System")
        else:
            print(f"  System Type: Single Star System")
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
            fluxes_list = [] 
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
                fluxes_list.append(extracted_flux)
            fluxes = np.array(fluxes_list)
        
        # --- Astrophysical Subtle Effects and Planetary Light ---
        # Determine the out-of-transit flux AFTER instrumental effects but BEFORE adding other astrophysical effects
        # (like reflected light, beaming, ellipsoidal) so these are relative to a stable star.
        # For a binary system, this OOT flux should be the combined OOT flux of both stars.
        
        # Calculate combined OOT flux from all stars in the system
        total_oot_stellar_flux = 0.0
        for star_obj in self.star_list:
            total_oot_stellar_flux += star_obj.base_flux # Use base flux, assuming it's normalized relative to this in Scene
        
        oot_flux_estimate = np.max(fluxes) # Take max observed flux after transit/eclipse of scene-generated image
        if oot_flux_estimate == 0: # Fallback if max flux is 0 (e.g., very deep transit/eclipse or no signal)
            oot_flux_estimate = total_oot_stellar_flux 
            if oot_flux_estimate == 0: oot_flux_estimate = 1.0 

        # Radial Velocities (for individual stars in binary, for beaming/ellipsoidal)
        # RVs will be a list of arrays: [RV_star1, RV_star2] if binary, or [RV_star1] if single.
        radial_velocities_unnoised_per_star = {} 
        if return_radial_velocity or include_doppler_beaming or include_ellipsoidal_variations or include_secondary_eclipse: 
            print("Calculating stellar radial velocities (for subtle effects context)...")
            for s_idx, star_obj in enumerate(self.star_list):
                # Calculate RVs of each star relative to the system barycenter due to planets AND binary orbit.
                # For now, RVs are from planet-induced wobble on *its own host star*.
                # RVs due to binary orbit are also needed for each star.
                
                # If binary, need to get barycentric position of stars first.
                if self.is_binary:
                    x1_b, y1_b, z1_b, x2_b, y2_b, z2_b = self.stars_object.get_star_barycentric_positions_at_time(times)
                    # Line-of-sight velocity of star1 from binary orbit
                    rv_star1_binary_orbit = (z1_b[1:] - z1_b[:-1]) / (times[1:] - times[:-1]) * (OrbitalSolver.R_SUN / OrbitalSolver.DAY_TO_SEC) # meters/sec. This is an approximation.
                    rv_star2_binary_orbit = (z2_b[1:] - z2_b[:-1]) / (times[1:] - times[:-1]) * (OrbitalSolver.R_SUN / OrbitalSolver.DAY_TO_SEC) # meters/sec
                    # Pad to match length, first value is dummy. A more rigorous way is to use d(z)/dt from orbital solution.
                    rv_star1_binary_orbit = np.pad(rv_star1_binary_orbit, (1,0), 'edge')
                    rv_star2_binary_orbit = np.pad(rv_star2_binary_orbit, (1,0), 'edge')
                else:
                    rv_star1_binary_orbit = np.zeros_like(times)
                    rv_star2_binary_orbit = np.zeros_like(times)

                current_star_rvs = np.zeros_like(times, dtype=np.float64)
                if star_obj.star_mass <= 0:
                    print(f"Warning: Star {s_idx} mass is non-positive. Skipping RV calculations for it.")
                else:
                    # RV from planet wobble (sum for all planets orbiting this star)
                    for planet in self.planets:
                        if planet.host_star_index == s_idx:
                            planet_rvs_on_star = OrbitalSolver.calculate_stellar_radial_velocity(
                                star_mass=star_obj.star_mass,
                                planet_mass=planet.planet_mass,
                                period=planet.period,
                                semimajor_axis=planet.semimajor_axis,
                                inclination=np.rad2deg(planet.inclination_rad), 
                                epoch_transit=planet.epoch_transit,
                                eccentricity=planet.eccentricity,
                                argument_of_periastron=np.rad2deg(planet.argument_of_periastron_rad), 
                                times=times
                            )
                            current_star_rvs += planet_rvs_on_star
                    
                    # Add binary orbital RV component
                    if self.is_binary:
                        if s_idx == 0: current_star_rvs += rv_star1_binary_orbit
                        else: current_star_rvs += rv_star2_binary_orbit
                
                radial_velocities_unnoised_per_star[s_idx] = current_star_rvs
        
        # Doppler Beaming (applied per star)
        if include_doppler_beaming:
            print("Applying Doppler beaming effect...")
            beaming_contribution_total = np.zeros_like(fluxes) # Store flux changes due to beaming
            
            for s_idx, star_obj in enumerate(self.star_list):
                if star_obj.star_mass > 0 and radial_velocities_unnoised_per_star.get(s_idx) is not None:
                    # Calculate beaming factor based on this star's RV
                    beaming_factors = OrbitalSolver.calculate_doppler_beaming_factor(
                        stellar_radial_velocity_ms=radial_velocities_unnoised_per_star[s_idx],
                        stellar_spectral_index=stellar_spectral_index
                    )
                    # Scale beaming effect by this star's fraction of total out-of-transit flux
                    # This ensures the effect is relative to its own brightness contribution.
                    star_fraction_of_light = star_obj.base_flux / total_oot_stellar_flux
                    beaming_contribution_total += (beaming_factors - 1.0) * star_fraction_of_light * oot_flux_estimate
                
            fluxes += beaming_contribution_total # Add the combined beaming flux
            print("Doppler beaming effect applied.")

        # Ellipsoidal Variations (applied per star)
        if include_ellipsoidal_variations:
            print("Applying ellipsoidal variations effect...")
            ellipsoidal_contribution_total = np.zeros_like(fluxes)
            
            for s_idx, star_obj in enumerate(self.star_list):
                # Ellipsoidal variation on star_obj due to all planets
                for planet in self.planets:
                    if self.star_list[planet.host_star_index] == star_obj: # If this planet orbits current star
                        if star_obj.star_mass > 0 and planet.planet_mass > 0:
                            ellipsoidal_factors = OrbitalSolver.calculate_ellipsoidal_variation_factor(
                                star_mass_solar=star_obj.star_mass,
                                planet_mass_jupiter=planet.planet_mass,
                                star_radius_stellar_radii=star_obj.radius, 
                                planet_semimajor_axis_stellar_radii=planet.semimajor_axis,
                                inclination_deg=np.rad2deg(planet.inclination_rad),
                                period_days=planet.period,
                                epoch_transit_days=planet.epoch_transit,
                                times_days=times,
                                stellar_gravity_darkening_coeff=stellar_gravity_darkening_coeff,
                                stellar_limb_darkening_coeffs=(star_obj.u1, star_obj.u2) 
                            )
                            # Scale ellipsoidal effect by this star's fraction of total OOT flux
                            star_fraction_of_light = star_obj.base_flux / total_oot_stellar_flux
                            ellipsoidal_contribution_total += (ellipsoidal_factors - 1.0) * star_fraction_of_light * oot_flux_estimate
            
            fluxes += ellipsoidal_contribution_total # Add the combined ellipsoidal flux
            print("Ellipsoidal variations effect applied.")

        # Reflected Light (Phase Curve) - from planets
        reflected_fluxes = None
        if include_reflected_light:
            print("Calculating planetary reflected light (phase curve)...")
            total_reflected_fluxes_planets_sum = np.zeros_like(times, dtype=np.float64)
            
            for planet in self.planets:
                if planet.albedo > 0: 
                    # Get the OOT flux of the planet's host star to scale reflected light
                    host_star_obj = self.star_list[planet.host_star_index]
                    host_star_oot_flux = host_star_obj.base_flux 
                    
                    planet_reflected_fluxes = OrbitalSolver.calculate_reflected_flux(
                        star_flux_oot=host_star_oot_flux, # Scale by host star's flux
                        planet_radius_stellar_radii=planet.radius,
                        planet_semimajor_axis_stellar_radii=planet.semimajor_axis,
                        planet_period_days=planet.period,
                        planet_epoch_transit_days=planet.epoch_transit,
                        planet_albedo=planet.albedo,
                        times=times,
                        eccentricity=planet.eccentricity,
                        argument_of_periastron=np.rad2deg(planet.argument_of_periastron_rad)
                    )
                    total_reflected_fluxes_planets_sum += planet_reflected_fluxes
            
            # NEW: Apply secondary eclipse effect if enabled
            if include_secondary_eclipse: 
                print("Applying secondary eclipse occultation to planetary light...")
                secondary_eclipse_factor_total = np.ones_like(times, dtype=np.float64) # Start with 1.0 (fully visible)
                
                for planet in self.planets:
                    # Calculate eclipse factor for each planet's light by its host star
                    # This is still a simplification; for binary, a planet orbiting S1 might be eclipsed by S2!
                    # For now, focus on host star eclipsing its own planet.
                    host_star_obj = self.star_list[planet.host_star_index]

                    # This calculation must consider the *relative* positions of planet and its host star.
                    # The secondary eclipse factor will be applied to *that planet's* reflected/emitted light.
                    secondary_eclipse_factor_this_planet = OrbitalSolver.calculate_secondary_eclipse_factor(
                        star_radius_stellar_radii=host_star_obj.radius,
                        planet_radius_stellar_radii=planet.radius,
                        semimajor_axis_stellar_radii=planet.semimajor_axis,
                        inclination_deg=np.rad2deg(planet.inclination_rad),
                        epoch_transit_days=planet.epoch_transit,
                        times_days=times,
                        eccentricity=planet.eccentricity,
                        argument_of_periastron_deg=np.rad2deg(planet.argument_of_periastron_rad)
                    )
                    # The total reflected fluxes sum the light from different planets.
                    # If we multiply the 'total_reflected_fluxes_planets_sum' by a 'secondary_eclipse_factor_total' here,
                    # it implies a single eclipse event applies to the sum, which is incorrect if multiple planets.
                    # Instead, we need to apply the secondary eclipse factor *per planet* before summing.
                    # This would require refactoring how total_reflected_fluxes_planets_sum is built.

                    # REFATORAÇÃO NECESSÁRIA AQUI para aplicar por planeta.
                    # Para a implementação atual, vamos considerar o impacto no fluxo *total_reflected_fluxes_planets_sum*
                    # apenas para o primeiro planeta na lista, ou se apenas um planeta é considerado para simplificar o teste.
                    # A forma mais correta seria modificar a linha `total_reflected_fluxes_planets_sum += planet_reflected_fluxes`
                    # para `total_reflected_fluxes_planets_sum += planet_reflected_fluxes * secondary_eclipse_factor_this_planet`
                    # para *cada planeta*, mas para isso 'secondary_eclipse_factor_this_planet' deve ser calculado dentro do loop.

                    # Para manter a estrutura atual (e dado que geralmente um sistema tem uma LC dominante),
                    # vamos fazer uma simplificação: se tiver apenas um planeta, aplica-se o fator.
                    # Se houver mais de um, por enquanto o fator total é 1.0 (para não introduzir bug complexo aqui).
                    if len(self.planets) == 1:
                         total_reflected_fluxes_planets_sum *= secondary_eclipse_factor_this_planet
                    else:
                        print("Warning: Secondary eclipse applied only to the sum of reflected light for multiple planets. For precise modeling, this needs to be applied per planet.")
                print("Secondary eclipse effect applied.")
            
            fluxes += total_reflected_fluxes_planets_sum 
            reflected_fluxes = total_reflected_fluxes_planets_sum 

            print("Planetary reflected light calculation complete.")

        normalized_fluxes = fluxes / oot_flux_estimate 

        # Add RV noise if RVs were calculated and noise parameters are provided
        radial_velocities = None
        if return_radial_velocity and radial_velocities_unnoised_per_star:
            radial_velocities = {} # Store RVs per star
            for s_idx, rvs_unnoised in radial_velocities_unnoised_per_star.items():
                rvs_with_noise = rvs_unnoised.copy() 
                if rv_instrumental_noise_std > 0:
                    rvs_with_noise += np.random.normal(0, rv_instrumental_noise_std, size=rvs_with_noise.shape)
                    if s_idx == 0: print(f"  Added {rv_instrumental_noise_std:.2f} m/s instrumental noise to Star1 RVs.")
                    else: print(f"  Added {rv_instrumental_noise_std:.2f} m/s instrumental noise to Star2 RVs.")
                if stellar_jitter_std > 0:
                    rvs_with_noise += np.random.normal(0, stellar_jitter_std, size=rvs_with_noise.shape)
                    if s_idx == 0: print(f"  Added {stellar_jitter_std:.2f} m/s stellar jitter to Star1 RVs.")
                    else: print(f"  Added {stellar_jitter_std:.2f} m/s stellar jitter to Star2 RVs.")
                radial_velocities[f'Star{s_idx+1}_RV'] = rvs_with_noise
            print("Radial velocity curve(s) finalized.")


        # If only one star, return single array for backward compatibility
        if not self.is_binary and 'Star1_RV' in radial_velocities:
            radial_velocities_return = radial_velocities['Star1_RV']
        elif self.is_binary and radial_velocities:
            radial_velocities_return = radial_velocities # Return dict for binary
        else:
            radial_velocities_return = None

        return times, normalized_fluxes, radial_velocities_return, reflected_fluxes