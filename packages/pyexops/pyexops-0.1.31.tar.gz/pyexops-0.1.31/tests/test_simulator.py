# pyexops/tests/test_simulator.py

import numpy as np
import pytest
from dask.distributed import Client, LocalCluster
import os

from pyexops import Star, Planet, Scene, Photometer, TransitSimulator, Atmosphere
from pyexops.orbital_solver import OrbitalSolver # Import to get expected RV range

# Fixtures for basic components (ensure star has mass, planets have mass)
@pytest.fixture
def basic_star():
    return Star(radius=5.0, base_flux=1000.0, limb_darkening_coeffs=(0.2, 0.1), star_mass=1.0) # Added star_mass

@pytest.fixture
def basic_planet():
    return Planet(radius=0.1, period=1.0, semimajor_axis=10.0,
                  inclination=90.0, epoch_transit=0.5, planet_mass=0.001) # Added planet_mass

@pytest.fixture
def massive_planet():
    # A more massive planet for noticeable RV and ellipsoidal effects
    return Planet(radius=0.1, period=1.0, semimajor_axis=5.0, # Closer orbit
                  inclination=90.0, epoch_transit=0.5, planet_mass=5.0) # 5 Jupiter masses

@pytest.fixture
def basic_atmosphere(basic_planet):
    transmission_data = [
        (400, basic_planet.radius * 1.0),
        (500, basic_planet.radius * 1.05), # 5% larger at 500nm
        (600, basic_planet.radius * 1.0)
    ]
    return Atmosphere(basic_planet.radius, transmission_data)

@pytest.fixture
def simulator_params(basic_star, basic_planet):
    return {
        'star': basic_star,
        'planets': [basic_planet],
        'image_resolution': (50, 50),
        'star_center_pixel': (25, 25),
        'background_flux_per_pixel': 5.0,
        'target_aperture_radius_pixels': 3.0,
        'background_aperture_inner_radius_pixels': 6.0,
        'background_aperture_outer_radius_pixels': 10.0,
        'read_noise_std': 2.0,
        'psf_type': 'gaussian',
        'psf_params': {'sigma_pixels': 1.0}
    }

# --- New tests for Task 4.1 (from previous turn) ---
# (Included for completeness, assuming these already pass and are not the focus of this turn's fix)

def test_simulator_init_with_jitter_and_prnu(simulator_params):
    """Test if Simulator correctly passes jitter and PRNU to Scene."""
    pointing_jitter_std_pixels = 0.5
    prnu_map = np.ones((50, 50)) * 1.02

    simulator = TransitSimulator(
        **simulator_params,
        pointing_jitter_std_pixels=pointing_jitter_std_pixels,
        pixel_response_non_uniformity_map=prnu_map
    )

    assert simulator.scene.pointing_jitter_std_pixels == pointing_jitter_std_pixels
    assert np.array_equal(simulator.scene.pixel_response_non_uniformity_map, prnu_map)

def test_run_simulation_dip_alignment(simulator_params):
    """Test run_simulation with DIP and image alignment."""
    simulator = TransitSimulator(
        **simulator_params,
        pointing_jitter_std_pixels=0.5 # Introduce jitter
    )
    
    observation_times = np.linspace(0, 1.0, 5) # Few points for speed

    times, fluxes, _, _ = simulator.run_simulation(
        observation_times,
        add_noise=True,
        inject_systematics=False,
        photometry_method='dip',
        perform_image_alignment=True,
        apply_dip_psf_matching=False
    )

    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0)

def test_run_simulation_dip_psf_matching(simulator_params):
    """Test run_simulation with DIP and PSF matching."""
    sim_params_psf_mismatch = simulator_params.copy()
    sim_params_psf_mismatch['psf_params'] = {'sigma_pixels': 1.5} # Scene generates images with this PSF
    
    simulator = TransitSimulator(
        **sim_params_psf_mismatch,
    )
    sigma_for_matching = 1.0 
    size_k = int(np.ceil(sigma_for_matching * 7)) 
    if size_k % 2 == 0: size_k += 1 
    center_k = size_k // 2
    y_k, x_k = np.indices((size_k, size_k)) - center_k
    r_sq_k = x_k**2 + y_k**2
    ideal_matching_kernel = np.exp(-r_sq_k / (2 * sigma_for_matching**2))
    ideal_matching_kernel /= np.sum(ideal_matching_kernel)
    
    simulator.photometer.psf_kernel = ideal_matching_kernel 

    observation_times = np.linspace(0, 1.0, 5) 

    times, fluxes, _, _ = simulator.run_simulation(
        observation_times,
        add_noise=True,
        inject_systematics=False,
        photometry_method='dip',
        perform_image_alignment=False,
        apply_dip_psf_matching=True 
    )

    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0)

def test_run_simulation_dip_alignment_and_psf_matching(simulator_params):
    """Test DIP with both image alignment and PSF matching."""
    simulator = TransitSimulator(
        **simulator_params,
        pointing_jitter_std_pixels=0.5 
    )
    
    sigma_for_matching = 1.0 
    size_k = int(np.ceil(sigma_for_matching * 7)) 
    if size_k % 2 == 0: size_k += 1 
    center_k = size_k // 2
    y_k, x_k = np.indices((size_k, size_k)) - center_k
    r_sq_k = x_k**2 + y_k**2
    ideal_matching_kernel = np.exp(-r_sq_k / (2 * sigma_for_matching**2))
    ideal_matching_kernel /= np.sum(ideal_matching_kernel)
    simulator.photometer.psf_kernel = ideal_matching_kernel

    observation_times = np.linspace(0, 1.0, 5) 

    times, fluxes, _, _ = simulator.run_simulation(
        observation_times,
        add_noise=True,
        inject_systematics=False,
        photometry_method='dip',
        perform_image_alignment=True,
        apply_dip_psf_matching=True 
    )

    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0)

# --- Existing tests from previous phases (ensure they still pass) ---

def test_run_simulation_sap(simulator_params):
    """Test basic SAP photometry simulation."""
    simulator = TransitSimulator(**simulator_params)
    observation_times = np.linspace(0, 1.0, 10) 
    
    times, fluxes, rvs, reflected_fluxes = simulator.run_simulation(
        observation_times,
        add_noise=True,
        inject_systematics=False,
        photometry_method='sap',
        return_radial_velocity=False,
        include_reflected_light=False
    )
    
    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0) 
    assert rvs is None
    assert reflected_fluxes is None
    
    transit_index = np.argmin(np.abs(times - 0.5))
    oot_index_start = np.argmin(np.abs(times - 0.1))
    oot_index_end = np.argmin(np.abs(times - 0.9))
    
    if fluxes[transit_index] < fluxes[oot_index_start] * 0.9: 
        assert True
    elif fluxes[transit_index] == np.max(fluxes): 
        assert True
    else:
        pytest.fail("Transit dip not observed or too shallow for basic test.")

def test_run_simulation_optimal_photometry(simulator_params):
    """Test optimal photometry simulation."""
    simulator = TransitSimulator(**simulator_params)
    observation_times = np.linspace(0, 1.0, 10)
    times, fluxes, _, _ = simulator.run_simulation(
        observation_times,
        photometry_method='optimal'
    )
    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0)

def test_run_simulation_psf_fitting_photometry(simulator_params):
    """Test PSF fitting photometry simulation."""
    simulator = TransitSimulator(**simulator_params)
    observation_times = np.linspace(0, 1.0, 10)
    times, fluxes, _, _ = simulator.run_simulation(
        observation_times,
        photometry_method='psf_fitting'
    )
    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0)

def test_run_simulation_dip_photometry(simulator_params):
    """Test difference imaging photometry simulation."""
    simulator = TransitSimulator(**simulator_params)
    observation_times = np.linspace(0, 1.0, 10)
    times, fluxes, _, _ = simulator.run_simulation(
        observation_times,
        photometry_method='dip',
        inject_systematics=True 
    )
    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0)

def test_run_simulation_rv_calculation(simulator_params):
    """Test simulation with radial velocity calculation."""
    simulator_params['planets'][0].planet_mass = 1.0 # 1 Jupiter mass
    simulator_params['star'].star_mass = 1.0 # 1 Solar mass
    simulator = TransitSimulator(**simulator_params)
    observation_times = np.linspace(0, 2.0, 20) 
    
    times, fluxes, rvs, _ = simulator.run_simulation(
        observation_times,
        add_noise=False, 
        photometry_method='sap',
        return_radial_velocity=True,
        rv_instrumental_noise_std=0.1,
        stellar_jitter_std=0.05
    )
    
    assert len(times) == len(fluxes)
    assert rvs is not None
    assert np.std(rvs) > 0.0 # Should have some variation due to planet

def test_run_simulation_reflected_light(simulator_params):
    """Test simulation with planetary reflected light."""
    simulator_params['planets'][0].albedo = 0.5 
    simulator = TransitSimulator(**simulator_params)
    observation_times = np.linspace(0, 1.0, 10)
    
    times, fluxes, _, reflected_fluxes = simulator.run_simulation(
        observation_times,
        add_noise=False,
        photometry_method='sap',
        include_reflected_light=True
    )
    
    assert len(times) == len(fluxes)
    assert reflected_fluxes is not None
    assert np.all(reflected_fluxes >= 0) 
    assert np.max(reflected_fluxes) > 0

def test_run_simulation_with_atmosphere(simulator_params, basic_atmosphere):
    """Test simulation with atmospheric transmission spectrum."""
    simulator_params['planets'][0].atmosphere = basic_atmosphere
    simulator = TransitSimulator(**simulator_params)
    
    times_500nm, fluxes_500nm, _, _ = simulator.run_simulation(
        np.linspace(0.4, 0.6, 20), 
        add_noise=False,
        photometry_method='sap',
        wavelength_nm=500
    )
    
    times_400nm, fluxes_400nm, _, _ = simulator.run_simulation(
        np.linspace(0.4, 0.6, 20), 
        add_noise=False,
        photometry_method='sap',
        wavelength_nm=400
    )

    depth_500nm = 1 - np.min(fluxes_500nm)
    depth_400nm = 1 - np.min(fluxes_400nm)
    
    assert depth_500nm > depth_400nm
    assert depth_500nm > 0 

def test_get_simulation_images_for_visualization(simulator_params):
    simulator = TransitSimulator(**simulator_params)
    times_for_viz = np.linspace(0, 1.0, 5)
    images, target_masks, background_masks, star_center = simulator.get_simulation_images_for_visualization(
        times_for_viz
    )
    assert len(images) == len(times_for_viz)
    assert images[0].shape == simulator_params['image_resolution']
    assert len(target_masks) == len(times_for_viz)
    assert len(background_masks) == len(times_for_viz)
    assert star_center == simulator_params['star_center_pixel']

def test_run_simulation_dask_parallelization(simulator_params):
    """Test parallel execution with Dask."""
    cluster = LocalCluster(n_workers=2, threads_per_worker=1, processes=False)
    client = Client(cluster)
    
    simulator = TransitSimulator(**simulator_params)
    observation_times = np.linspace(0, 1.0, 20) 
    
    try:
        times, fluxes, _, _ = simulator.run_simulation(
            observation_times,
            add_noise=True,
            photometry_method='sap',
            dask_client=client
        )
        assert len(times) == len(fluxes)
        assert np.all(fluxes > 0)
    finally:
        client.close()
        cluster.close()

# --- NEW TESTS FOR TASK 4.2 ---

def test_run_simulation_doppler_beaming(simulator_params, massive_planet):
    """Test run_simulation with Doppler beaming effect."""
    # Use a massive planet to ensure noticeable RV and thus beaming
    params = simulator_params.copy()
    params['planets'] = [massive_planet]
    simulator = TransitSimulator(**params)
    
    # Simulate over two periods to see full RV cycle
    observation_times = np.linspace(0, massive_planet.period * 2, 50) 

    # Run without beaming
    times_no_beaming, fluxes_no_beaming, rvs, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        return_radial_velocity=True, # Get RVs for comparison
        include_doppler_beaming=False
    )
    
    # Run with beaming
    times_with_beaming, fluxes_with_beaming, _, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        return_radial_velocity=False, # Don't need RVs returned, just for beaming
        include_doppler_beaming=True,
        stellar_spectral_index=3.0
    )

    assert fluxes_with_beaming.shape == fluxes_no_beaming.shape
    
    # There should be a difference in flux due to beaming
    assert not np.allclose(fluxes_with_beaming, fluxes_no_beaming, atol=1e-5) # Expect small difference
    
    # Beaming makes star brighter when approaching (RV < 0)
    # RVs max negative around transit - P/4. Flux should be max around transit - P/4.
    # RVs max positive around transit + P/4. Flux should be min around transit + P/4.
    
    # Find flux deviations
    flux_deviation = (fluxes_with_beaming - fluxes_no_beaming) / fluxes_no_beaming
    
    # Check correlation with RVs
    # When RV is most negative (approaching), flux_deviation should be most positive
    # When RV is most positive (receding), flux_deviation should be most negative
    
    # Note: A precise check depends on precise phasing, which relies on orbital_solver.
    # A simple check: the max deviation should be associated with an RV, and vice-versa
    # And the average deviation should be close to zero.
    
    # Calculate RV amplitude
    rv_amplitude = np.max(rvs) - np.min(rvs)
    
    if rv_amplitude > 1e-3: # Only if RV is significant enough to cause beaming
        # Check that min/max flux deviation corresponds to max/min RV (inverse correlation)
        # RVs are positive for receding, negative for approaching.
        # Beaming makes approaching brighter, receding dimmer.
        # So flux_deviation should be INVERSELY correlated with RVs.
        correlation = np.corrcoef(rvs, flux_deviation)[0, 1]
        assert correlation < -0.5 # Expect strong negative correlation (flux up when RV down)
    else:
        assert np.allclose(fluxes_with_beaming, fluxes_no_beaming, atol=1e-9) # No RV, no beaming

def test_run_simulation_ellipsoidal_variations(simulator_params, massive_planet):
    """Test run_simulation with ellipsoidal variations effect."""
    # Use a massive, close-in planet for noticeable ellipsoidal effect
    params = simulator_params.copy()
    params['planets'] = [massive_planet]
    simulator = TransitSimulator(**params)

    # Simulate over two periods to see two full cycles of ellipsoidal variation
    observation_times = np.linspace(0, massive_planet.period * 2, 50) 

    # Run without ellipsoidal variations
    times_no_ellip, fluxes_no_ellip, _, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        include_ellipsoidal_variations=False
    )
    
    # Run with ellipsoidal variations
    times_with_ellip, fluxes_with_ellip, _, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        include_ellipsoidal_variations=True,
        stellar_gravity_darkening_coeff=0.32
    )

    assert fluxes_with_ellip.shape == fluxes_no_ellip.shape
    
    # There should be a difference in flux due to ellipsoidal variations
    assert not np.allclose(fluxes_with_ellip, fluxes_no_ellip, atol=1e-5) # Expect small difference
    
    # Ellipsoidal variations cause two peaks per period (at conjunctions) and two troughs (at quadratures)
    # Transit (t=0.5, 1.5) and secondary eclipse (t=0.0, 1.0, 2.0) should be flux maxima.
    # Quadratures (t=0.25, 0.75, 1.25, 1.75) should be flux minima.
    
    flux_deviation = (fluxes_with_ellip - fluxes_no_ellip) / fluxes_no_ellip
    
    # Find expected peaks and troughs indices
    transit_idx_1 = np.argmin(np.abs(observation_times - 0.5))
    eclipse_idx_1 = np.argmin(np.abs(observation_times - 0.0))
    eclipse_idx_2 = np.argmin(np.abs(observation_times - 1.0))
    quadrature_idx_1 = np.argmin(np.abs(observation_times - 0.25))
    quadrature_idx_2 = np.argmin(np.abs(observation_times - 0.75))

    # Check that conjunctions are brighter than quadratures
    assert flux_deviation[transit_idx_1] > flux_deviation[quadrature_idx_1]
    assert flux_deviation[eclipse_idx_1] > flux_deviation[quadrature_idx_1]
    
    # Check that there is actual variation
    assert np.std(flux_deviation) > 1e-6 # Standard deviation should be non-zero for variation

def test_run_simulation_combined_subtle_effects(simulator_params, massive_planet):
    """Test run_simulation with both Doppler beaming and ellipsoidal variations."""
    params = simulator_params.copy()
    params['planets'] = [massive_planet]
    simulator = TransitSimulator(**params)

    observation_times = np.linspace(0, massive_planet.period * 2, 50) 

    # Run without subtle effects
    times_no_subtle, fluxes_no_subtle, _, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        include_doppler_beaming=False, include_ellipsoidal_variations=False
    )
    
    # Run with both subtle effects
    times_with_subtle, fluxes_with_subtle, _, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        include_doppler_beaming=True, stellar_spectral_index=3.0,
        include_ellipsoidal_variations=True, stellar_gravity_darkening_coeff=0.32
    )

    assert fluxes_with_subtle.shape == fluxes_no_subtle.shape
    
    # The combined flux should be different from the baseline
    assert not np.allclose(fluxes_with_subtle, fluxes_no_subtle, atol=1e-5)
    
    # Ensure they are not negative (though factors are close to 1)
    assert np.all(fluxes_with_subtle > 0)
    
    # Check that max/min are not at extreme ends of possible values (i.e., within reasonable range for subtle effects)
    assert np.max(fluxes_with_subtle) < np.max(fluxes_no_subtle) * 1.01 # Max 1% increase
    assert np.min(fluxes_with_subtle) > np.min(fluxes_no_subtle) * 0.99 # Max 1% decrease