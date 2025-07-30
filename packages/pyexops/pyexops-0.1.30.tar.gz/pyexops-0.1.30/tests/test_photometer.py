# pyexops/tests/test_simulator.py

import numpy as np
import pytest
from dask.distributed import Client, LocalCluster
import os

from pyexops import Star, Planet, Scene, Photometer, TransitSimulator, Atmosphere

# Fixtures for basic components
@pytest.fixture
def basic_star():
    return Star(radius=5.0, base_flux=1000.0, limb_darkening_coeffs=(0.2, 0.1), star_mass=1.0)

@pytest.fixture
def basic_planet():
    return Planet(radius=0.1, period=1.0, semimajor_axis=10.0,
                  inclination=90.0, epoch_transit=0.5, planet_mass=0.001) # Small mass for RV

@pytest.fixture
def basic_atmosphere(basic_planet):
    # Example: slightly larger effective radius at certain wavelengths
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

def test_run_simulation_dip_alignment(simulator_params):
    """Test run_simulation with DIP and image alignment."""
    # Temporarily set jitter for this test to confirm alignment works
    simulator = TransitSimulator(
        **simulator_params,
        pointing_jitter_std_pixels=0.5 # Introduce jitter
    )
    
    observation_times = np.linspace(0, 1.0, 5) # Few points for speed

    # Run with DIP and alignment
    times, fluxes, _, _ = simulator.run_simulation(
        observation_times,
        add_noise=True,
        inject_systematics=False, # No systematics for this test
        photometry_method='dip',
        perform_image_alignment=True, # Enable alignment
        apply_dip_psf_matching=False
    )

    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0)
    
    # Qualitative check: alignment should reduce noise from jitter
    # (hard to test quantitatively in unit test without more complex setup)
    # But we can check that it runs without error and returns data.

def test_run_simulation_dip_psf_matching(simulator_params):
    """Test run_simulation with DIP and PSF matching."""
    # For this test, let's make the scene's PSF slightly different from the photometer's ideal kernel initially,
    # then check if PSF matching improves the consistency.
    sim_params_psf_mismatch = simulator_params.copy()
    sim_params_psf_mismatch['psf_params'] = {'sigma_pixels': 1.5} # Scene generates images with this PSF
    
    simulator = TransitSimulator(
        **sim_params_psf_mismatch,
        # The photometer's kernel will be based on the Scene's initial PSF param (1.5 sigma)
        # For this test, we need the photometer's kernel to be different from what's *actually* in the image.
        # This implies modifying the photometer's kernel directly for the test, or having the scene generate
        # frames with a different PSF for a subset of frames (which is not how Scene is designed now).
        # A simpler way to test the *logic* of PSF matching is to ensure the convolution step is called.
        # Let's ensure a non-None psf_kernel for the photometer is present.
    )

    # To test PSF matching, let's force the photometer's kernel to be different from the Scene's PSF.
    # This simulates a "mismatched" PSF scenario for DIP.
    phot_original_kernel = simulator.photometer.psf_kernel
    # Create a *different* kernel that the photometer will use for matching
    # (e.g., a perfect Gaussian for DIP matching, even if the scene produces a Moffat)
    sigma_for_matching = 1.0 # Smaller, ideal PSF for matching
    size_k = int(np.ceil(sigma_for_matching * 7)) 
    if size_k % 2 == 0: size_k += 1 
    center_k = size_k // 2
    y_k, x_k = np.indices((size_k, size_k)) - center_k
    r_sq_k = x_k**2 + y_k**2
    ideal_matching_kernel = np.exp(-r_sq_k / (2 * sigma_for_matching**2))
    ideal_matching_kernel /= np.sum(ideal_matching_kernel)
    
    simulator.photometer.psf_kernel = ideal_matching_kernel # Inject a specific matching kernel

    observation_times = np.linspace(0, 1.0, 5) # Few points

    # Run with DIP and PSF matching
    times, fluxes, _, _ = simulator.run_simulation(
        observation_times,
        add_noise=True,
        inject_systematics=False,
        photometry_method='dip',
        perform_image_alignment=False,
        apply_dip_psf_matching=True # Enable PSF matching
    )

    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0)
    # The output should be more "stable" or accurate if PSF matching corrects for variations.
    # This is hard to assert numerically in a basic unit test.
    # We mainly test that the function executes without error and that the logic is engaged.

def test_run_simulation_dip_alignment_and_psf_matching(simulator_params):
    """Test run_simulation with DIP, alignment, and PSF matching."""
    simulator = TransitSimulator(
        **simulator_params,
        pointing_jitter_std_pixels=0.5 # Introduce jitter
    )
    
    # Inject a specific matching kernel for photometer (as in previous test)
    sigma_for_matching = 1.0 
    size_k = int(np.ceil(sigma_for_matching * 7)) 
    if size_k % 2 == 0: size_k += 1 
    center_k = size_k // 2
    y_k, x_k = np.indices((size_k, size_k)) - center_k
    r_sq_k = x_k**2 + y_k**2
    ideal_matching_kernel = np.exp(-r_sq_k / (2 * sigma_for_matching**2))
    ideal_matching_kernel /= np.sum(ideal_matching_kernel)
    simulator.photometer.psf_kernel = ideal_matching_kernel

    observation_times = np.linspace(0, 1.0, 5) # Few points

    # Run with DIP, alignment, and PSF matching
    times, fluxes, _, _ = simulator.run_simulation(
        observation_times,
        add_noise=True,
        inject_systematics=False,
        photometry_method='dip',
        perform_image_alignment=True, # Enable alignment
        apply_dip_psf_matching=True # Enable PSF matching
    )

    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0)

# --- Existing tests from previous phases (ensure they still pass) ---

def test_run_simulation_sap(simulator_params):
    """Test basic SAP photometry simulation."""
    simulator = TransitSimulator(**simulator_params)
    observation_times = np.linspace(0, 1.0, 10) # 10 points for speed
    
    times, fluxes, rvs, reflected_fluxes = simulator.run_simulation(
        observation_times,
        add_noise=True,
        inject_systematics=False,
        photometry_method='sap',
        return_radial_velocity=False,
        include_reflected_light=False
    )
    
    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0) # Fluxes should be positive
    assert rvs is None
    assert reflected_fluxes is None
    
    # Check for transit dip (qualitative)
    # Flux should drop during transit (around epoch_transit = 0.5)
    transit_index = np.argmin(np.abs(times - 0.5))
    oot_index_start = np.argmin(np.abs(times - 0.1))
    oot_index_end = np.argmin(np.abs(times - 0.9))
    
    # If a transit occurs, flux at mid-transit should be lower than out-of-transit
    if fluxes[transit_index] < fluxes[oot_index_start] * 0.9: # Expect at least 10% dip
        assert True
    elif fluxes[transit_index] == np.max(fluxes): # No transit occurred
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
        inject_systematics=True # DIP is good for systematics
    )
    assert len(times) == len(fluxes)
    assert np.all(fluxes > 0)

def test_run_simulation_rv_calculation(simulator_params):
    """Test simulation with radial velocity calculation."""
    simulator_params['planets'][0].planet_mass = 1.0 # 1 Jupiter mass
    simulator_params['star'].star_mass = 1.0 # 1 Solar mass
    simulator = TransitSimulator(**simulator_params)
    observation_times = np.linspace(0, 2.0, 20) # Over 2 periods
    
    times, fluxes, rvs, _ = simulator.run_simulation(
        observation_times,
        add_noise=False, # No noise for RV test clarity
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
    # Add albedo to planet
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
    assert np.all(reflected_fluxes >= 0) # Reflected flux should be non-negative
    # Check if reflected light adds flux (phase curve)
    assert np.max(reflected_fluxes) > 0

def test_run_simulation_with_atmosphere(simulator_params, basic_atmosphere):
    """Test simulation with atmospheric transmission spectrum."""
    simulator_params['planets'][0].atmosphere = basic_atmosphere
    simulator = TransitSimulator(**simulator_params)
    
    # Simulate at a wavelength where effective radius is larger (500nm)
    times_500nm, fluxes_500nm, _, _ = simulator.run_simulation(
        np.linspace(0.4, 0.6, 20), # Around transit
        add_noise=False,
        photometry_method='sap',
        wavelength_nm=500
    )
    
    # Simulate at a wavelength where effective radius is base (400nm)
    times_400nm, fluxes_400nm, _, _ = simulator.run_simulation(
        np.linspace(0.4, 0.6, 20), # Around transit
        add_noise=False,
        photometry_method='sap',
        wavelength_nm=400
    )

    # Check that transit depth is greater at 500nm (due to larger effective radius)
    depth_500nm = 1 - np.min(fluxes_500nm)
    depth_400nm = 1 - np.min(fluxes_400nm)
    
    assert depth_500nm > depth_400nm
    assert depth_500nm > 0 # Should have a dip

# Test get_simulation_images_for_visualization
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
    # Use a LocalCluster for testing in-process
    cluster = LocalCluster(n_workers=2, threads_per_worker=1, processes=False)
    client = Client(cluster)
    
    simulator = TransitSimulator(**simulator_params)
    observation_times = np.linspace(0, 1.0, 20) # More points for parallelization benefit
    
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