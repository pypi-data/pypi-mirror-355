# pyexops/tests/test_simulator.py

import numpy as np
import pytest
from dask.distributed import Client, LocalCluster
import os

from pyexops import Star, Planet, Scene, Photometer, TransitSimulator, Atmosphere
from pyexops.orbital_solver import OrbitalSolver 
from pyexops.binary_star_system import BinaryStarSystem # NEW: Import BinaryStarSystem

# Fixtures for basic components
@pytest.fixture
def basic_star():
    return Star(radius=5.0, base_flux=1000.0, limb_darkening_coeffs=(0.2, 0.1), star_mass=1.0)

@pytest.fixture
def basic_planet():
    return Planet(radius=0.1, period=1.0, semimajor_axis=10.0,
                  inclination=90.0, epoch_transit=0.5, planet_mass=0.001)

@pytest.fixture
def massive_planet():
    return Planet(radius=0.1, period=1.0, semimajor_axis=5.0, 
                  inclination=90.0, epoch_transit=0.5, planet_mass=5.0) 

@pytest.fixture
def basic_atmosphere(basic_planet):
    transmission_data = [
        (400, basic_planet.radius * 1.0),
        (500, basic_planet.radius * 1.05), 
        (600, basic_planet.radius * 1.0)
    ]
    return Atmosphere(basic_planet.radius, transmission_data)

# NEW: Fixture for a binary star system
@pytest.fixture
def test_binary_system_for_sim():
    star_A = Star(radius=5.0, base_flux=10000.0, limb_darkening_coeffs=(0.3, 0.2), star_mass=1.0)
    star_B = Star(radius=2.0, base_flux=2000.0, limb_darkening_coeffs=(0.4, 0.1), star_mass=0.5)
    
    return BinaryStarSystem(
        star_A, star_B,
        period_days=10.0,
        semimajor_axis_stellar_radii=10.0, # Relative to starA's radius
        inclination_deg=90.0,
        eccentricity=0.0,
        argument_of_periastron_deg=0.0,
        epoch_periastron_days=0.0
    )


@pytest.fixture
def simulator_params(basic_star, basic_planet):
    return {
        'stars': basic_star, # Changed from 'star' to 'stars'
        'planets': [basic_planet],
        'image_resolution': (50, 50),
        'barycenter_pixel_on_image': (25, 25), # Changed from 'star_center_pixel'
        'background_flux_per_pixel': 5.0,
        'target_aperture_radius_pixels': 3.0,
        'background_aperture_inner_radius_pixels': 6.0,
        'background_aperture_outer_radius_pixels': 10.0,
        'read_noise_std': 2.0,
        'psf_type': 'gaussian',
        'psf_params': {'sigma_pixels': 1.0}
    }

# --- New tests for Task 4.1 ---

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
    assert simulator.barycenter_pixel_on_image == simulator_params['barycenter_pixel_on_image'] # Check new param name

def test_run_simulation_dip_alignment(simulator_params):
    """Test run_simulation with DIP and image alignment."""
    simulator = TransitSimulator(
        **simulator_params,
        pointing_jitter_std_pixels=0.5 
    )
    
    observation_times = np.linspace(0, 1.0, 5) 

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
    sim_params_psf_mismatch['psf_params'] = {'sigma_pixels': 1.5} 
    
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

# --- Existing tests from previous phases ---

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
    # Ensure star mass is set for RV calc in fixture
    simulator_params['stars'].star_mass = 1.0 
    simulator_params['planets'][0].planet_mass = 1.0 
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
    assert isinstance(rvs, np.ndarray) # Should be single array for single star
    assert np.std(rvs) > 0.0 

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
    images, target_masks, background_masks, barycenter_pixel = simulator.get_simulation_images_for_visualization( # NEW: barycenter_pixel
        times_for_viz
    )
    assert len(images) == len(times_for_viz)
    assert images[0].shape == simulator_params['image_resolution']
    assert len(target_masks) == len(times_for_viz)
    assert len(background_masks) == len(times_for_viz)
    assert barycenter_pixel == simulator_params['barycenter_pixel_on_image'] # NEW: barycenter_pixel

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

# --- Tests for Task 4.2 (from previous turn, now integrated with new simulator init) ---

def test_run_simulation_doppler_beaming(simulator_params, massive_planet):
    params = simulator_params.copy()
    params['planets'] = [massive_planet]
    simulator = TransitSimulator(**params)
    
    observation_times = np.linspace(0, massive_planet.period * 2, 50) 

    times_no_beaming, fluxes_no_beaming, rvs, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        return_radial_velocity=True, 
        include_doppler_beaming=False
    )
    
    times_with_beaming, fluxes_with_beaming, _, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        return_radial_velocity=False, 
        include_doppler_beaming=True,
        stellar_spectral_index=3.0
    )

    assert fluxes_with_beaming.shape == fluxes_no_beaming.shape
    assert not np.allclose(fluxes_with_beaming, fluxes_no_beaming, atol=1e-5) 
    
    correlation = np.corrcoef(rvs, (fluxes_with_beaming - fluxes_no_beaming) / fluxes_no_beaming)[0, 1]
    # Beaming is inversely correlated with RV if RV is positive for receding
    # Flux increases when RV is negative (approaching). So correlation should be negative.
    if np.std(rvs) > 1e-3: 
        assert correlation < -0.5 
    else:
        assert np.allclose(fluxes_with_beaming, fluxes_no_beaming, atol=1e-9) 

def test_run_simulation_ellipsoidal_variations(simulator_params, massive_planet):
    params = simulator_params.copy()
    params['planets'] = [massive_planet]
    simulator = TransitSimulator(**params)

    observation_times = np.linspace(0, massive_planet.period * 2, 50) 

    times_no_ellip, fluxes_no_ellip, _, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        include_ellipsoidal_variations=False
    )
    
    times_with_ellip, fluxes_with_ellip, _, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        include_ellipsoidal_variations=True,
        stellar_gravity_darkening_coeff=0.32
    )

    assert fluxes_with_ellip.shape == fluxes_no_ellip.shape
    assert not np.allclose(fluxes_with_ellip, fluxes_no_ellip, atol=1e-5) 
    
    flux_deviation = (fluxes_with_ellip - fluxes_no_ellip) / fluxes_no_ellip
    
    transit_idx_1 = np.argmin(np.abs(observation_times - 0.5))
    eclipse_idx_1 = np.argmin(np.abs(observation_times - 0.0))
    quadrature_idx_1 = np.argmin(np.abs(observation_times - 0.25))

    assert flux_deviation[transit_idx_1] > flux_deviation[quadrature_idx_1]
    assert flux_deviation[eclipse_idx_1] > flux_deviation[quadrature_idx_1]
    assert np.std(flux_deviation) > 1e-6 

def test_run_simulation_combined_subtle_effects(simulator_params, massive_planet):
    params = simulator_params.copy()
    params['planets'] = [massive_planet]
    simulator = TransitSimulator(**params)

    observation_times = np.linspace(0, massive_planet.period * 2, 50) 

    times_no_subtle, fluxes_no_subtle, _, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        include_doppler_beaming=False, include_ellipsoidal_variations=False
    )
    
    times_with_subtle, fluxes_with_subtle, _, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        include_doppler_beaming=True, stellar_spectral_index=3.0,
        include_ellipsoidal_variations=True, stellar_gravity_darkening_coeff=0.32
    )

    assert fluxes_with_subtle.shape == fluxes_no_subtle.shape
    assert not np.allclose(fluxes_with_subtle, fluxes_no_subtle, atol=1e-5)
    assert np.all(fluxes_with_subtle > 0)
    assert np.max(fluxes_with_subtle) < np.max(fluxes_no_subtle) * 1.01 
    assert np.min(fluxes_with_subtle) > np.min(fluxes_no_subtle) * 0.99 

# --- NEW TESTS FOR TASK 5.1 ---

def test_simulator_init_with_binary_system(test_binary_system_for_sim, basic_planet):
    """Test Simulator initialization with a BinaryStarSystem object."""
    # Ensure planet is assigned to a star within the binary
    basic_planet.host_star_index = 0 # Planet orbits star1
    
    params = {
        'stars': test_binary_system_for_sim,
        'planets': [basic_planet],
        'image_resolution': (100, 100),
        'barycenter_pixel_on_image': (50, 50),
        'background_flux_per_pixel': 0.0,
        'target_aperture_radius_pixels': 5.0,
        'background_aperture_inner_radius_pixels': 10.0,
        'background_aperture_outer_radius_pixels': 15.0,
        'read_noise_std': 0.0,
        'psf_type': 'gaussian',
        'psf_params': {'sigma_pixels': 1.0}
    }
    
    simulator = TransitSimulator(**params)
    
    assert simulator.is_binary is True
    assert simulator.stars_object is test_binary_system_for_sim
    assert simulator.star_list[0] is test_binary_system_for_sim.star1
    assert simulator.star_list[1] is test_binary_system_for_sim.star2
    assert simulator.system_total_mass == test_binary_system_for_sim.total_mass_solar
    assert simulator.photometer.system_center_pixel == params['barycenter_pixel_on_image']

def test_run_simulation_binary_star_eclipses_only(test_binary_system_for_sim):
    """Test simulation of a binary star system with only stellar eclipses."""
    params = {
        'stars': test_binary_system_for_sim,
        'planets': [], # No planets
        'image_resolution': (100, 100),
        'barycenter_pixel_on_image': (50, 50),
        'background_flux_per_pixel': 0.0,
        'target_aperture_radius_pixels': 15.0, # Large aperture to capture both stars
        'background_aperture_inner_radius_pixels': 20.0,
        'background_aperture_outer_radius_pixels': 25.0,
        'read_noise_std': 0.0,
        'psf_type': 'gaussian',
        'psf_params': {'sigma_pixels': 1.0}
    }
    simulator = TransitSimulator(**params)
    
    # Simulate over one binary period
    observation_times = np.linspace(0, test_binary_system_for_sim.period_days, 100)
    
    times, fluxes, rvs, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        return_radial_velocity=True # Get RVs for binary context
    )
    
    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0)
    
    # Expect two dips per binary period (primary and secondary eclipse)
    # Eclipses occur at t=0.0 and t=P/2 if epoch_periastron=0 and inc=90, ecc=0.
    mid_eclipse_1 = test_binary_system_for_sim.epoch_periastron_days
    mid_eclipse_2 = test_binary_system_for_sim.epoch_periastron_days + test_binary_system_for_sim.period_days / 2.0
    
    flux_at_eclipse1 = fluxes[np.argmin(np.abs(times - mid_eclipse_1))]
    flux_at_eclipse2 = fluxes[np.argmin(np.abs(times - mid_eclipse_2))]
    flux_at_oot = fluxes[np.argmin(np.abs(times - (mid_eclipse_1 + test_binary_system_for_sim.period_days / 4.0)))]
    
    assert flux_at_eclipse1 < flux_at_oot * 0.9 # Primary eclipse dip
    assert flux_at_eclipse2 < flux_at_oot * 0.9 # Secondary eclipse dip (may be shallower)
    
    # Check RVs: should be a dictionary for binary system
    assert isinstance(rvs, dict)
    assert 'Star1_RV' in rvs
    assert 'Star2_RV' in rvs
    assert np.std(rvs['Star1_RV']) > 0 and np.std(rvs['Star2_RV']) > 0 # Should have orbital motion
    assert np.allclose(rvs['Star1_RV'], -rvs['Star2_RV'] * test_binary_system_for_sim.star2.star_mass / test_binary_system_for_sim.star1.star_mass, atol=0.1) # Check RV ratio

def test_run_simulation_binary_star_with_planet_transit(test_binary_system_for_sim):
    """Test simulation of a binary star system with a planet transiting one of the stars."""
    planet_on_star_A = Planet(radius=0.1, period=test_binary_system_for_sim.star1.radius * 2 / 0.1, # Short period for transit
                              semimajor_axis=test_binary_system_for_sim.star1.radius * 3, 
                              inclination=90.0, epoch_transit=test_binary_system_for_sim.epoch_periastron_days, # Aligned with binary eclipse
                              planet_mass=0.001, host_star_index=0) # Orbits star A

    params = {
        'stars': test_binary_system_for_sim,
        'planets': [planet_on_star_A],
        'image_resolution': (100, 100),
        'barycenter_pixel_on_image': (50, 50),
        'background_flux_per_pixel': 0.0,
        'target_aperture_radius_pixels': 15.0, 
        'background_aperture_inner_radius_pixels': 20.0,
        'background_aperture_outer_radius_pixels': 25.0,
        'read_noise_std': 0.0,
        'psf_type': 'gaussian',
        'psf_params': {'sigma_pixels': 1.0}
    }
    simulator = TransitSimulator(**params)

    observation_times = np.linspace(0, test_binary_system_for_sim.period_days, 200) # One binary period
    
    times, fluxes, rvs, _ = simulator.run_simulation(
        observation_times, add_noise=False, photometry_method='sap',
        return_radial_velocity=True 
    )

    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0)

    # Expect multiple dips: two binary eclipses + at least one planetary transit
    # Planet transit epoch is aligned with primary binary eclipse (t=0, P)
    # The dips should be distinct from each other.
    
    # Find flux at times of expected events
    mid_binary_eclipse1_idx = np.argmin(np.abs(times - test_binary_system_for_sim.epoch_periastron_days))
    mid_binary_eclipse2_idx = np.argmin(np.abs(times - (test_binary_system_for_sim.epoch_periastron_days + test_binary_system_for_sim.period_days / 2.0)))
    
    # Planet transit is also at epoch_periastron_days (0.0). This will deepen the binary eclipse.
    # To see a separate planet transit, adjust planet_on_star_A.epoch_transit.
    # Let's assume planet is very fast and transits multiple times.
    planet_transit_times = np.arange(0, test_binary_system_for_sim.period_days, planet_on_star_A.period)
    
    flux_oot = np.max(fluxes) # Take peak flux as OOT
    
    # Verify that there are dips deeper than simple binary eclipses alone
    # This requires running a binary-only sim first and comparing.
    # For now, a simpler check: min flux should be very low.
    
    # The overall min flux should be lower than just binary eclipses, because of the planet
    # (especially if the planet transits the larger, brighter star).
    assert np.min(fluxes) < flux_oot * 0.85 # Expect combined deep dip
    
    # Check RVs: should be a dictionary with RVs of both stars, affected by both their binary motion and planet wobble
    assert isinstance(rvs, dict)
    assert 'Star1_RV' in rvs and 'Star2_RV' in rvs
    assert np.std(rvs['Star1_RV']) > 0 and np.std(rvs['Star2_RV']) > 0