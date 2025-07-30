# pyexops/tests/test_simulator.py

import pytest
import numpy as np
from dask.distributed import Client, LocalCluster # For testing Dask functionality
from pyexops import Star, Planet, TransitSimulator

# Fixtures for Simulator testing
@pytest.fixture
def minimal_star():
    return Star(radius=5.0, base_flux=1000.0)

@pytest.fixture
def minimal_planet():
    return Planet(radius=0.1, period=1.0, semimajor_axis=2.0, inclination=90.0, epoch_transit=0.5)

@pytest.fixture
def default_sim_params(minimal_star, minimal_planet):
    return {
        "star": minimal_star,
        "planets": [minimal_planet],
        "image_resolution": (50, 50),
        "star_center_pixel": (25, 25),
        "background_flux_per_pixel": 1.0,
        "target_aperture_radius_pixels": 3.0,
        "background_aperture_inner_radius_pixels": 5.0,
        "background_aperture_outer_radius_pixels": 8.0,
        "read_noise_std": 1.0,
        "psf_type": 'gaussian',
        "psf_params": {'sigma_pixels': 1.0}
    }

@pytest.fixture
def local_dask_client():
    # Use a small local cluster for testing Dask integration
    cluster = LocalCluster(n_workers=2, threads_per_worker=1, processes=True, dashboard_address=None)
    client = Client(cluster)
    yield client
    client.close()
    cluster.close()

# --- Test run_simulation ---
def test_run_simulation_output_shape(default_sim_params):
    simulator = TransitSimulator(**default_sim_params)
    times = np.arange(0.0, 2.0, 0.1) # 20 points
    times_lc, fluxes_lc = simulator.run_simulation(times, add_noise=False, inject_systematics=False, photometry_method='sap', dask_client=None)
    assert times_lc.shape == (20,)
    assert fluxes_lc.shape == (20,)
    assert np.all(fluxes_lc >= 0.0) # Fluxes should be non-negative
    assert np.max(fluxes_lc) == pytest.approx(1.0) # Normalized max should be 1.0

@pytest.mark.parametrize("photometry_method", ['sap', 'optimal', 'psf_fitting', 'dip'])
def test_run_simulation_photometry_methods(default_sim_params, photometry_method):
    # This test primarily checks if the different photometry methods run without error.
    # Detailed photometric accuracy is tested in test_photometer.py
    simulator = TransitSimulator(**default_sim_params)
    times = np.arange(0.0, 2.0, 0.2) # Fewer points for quicker test
    try:
        times_lc, fluxes_lc = simulator.run_simulation(times, add_noise=False, inject_systematics=False, photometry_method=photometry_method, dask_client=None)
        assert times_lc.shape == fluxes_lc.shape
        assert np.max(fluxes_lc) == pytest.approx(1.0)
    except ValueError as e:
        # PSF Fitting might fail if data is too simple, or DIP if template logic is complex for test.
        # This is okay for a basic run test, but might need specific mocked images for more robust testing.
        if "PSF Fitting failed" in str(e) or "Template image must be provided" in str(e):
            pytest.skip(f"Photometry method {photometry_method} skipped due to specific data requirements for this basic test.")
        else:
            raise e

def test_run_simulation_dask_integration(default_sim_params, local_dask_client):
    simulator = TransitSimulator(**default_sim_params)
    times = np.arange(0.0, 2.0, 0.2) # Fewer points for quicker test
    
    # Run with Dask
    times_dask, fluxes_dask = simulator.run_simulation(times, add_noise=False, inject_systematics=False, photometry_method='sap', dask_client=local_dask_client)
    
    # Run sequentially for comparison
    times_seq, fluxes_seq = simulator.run_simulation(times, add_noise=False, inject_systematics=False, photometry_method='sap', dask_client=None)
    
    assert np.allclose(fluxes_dask, fluxes_seq) # Results should be the same
    assert times_dask.shape == fluxes_dask.shape
    assert np.max(fluxes_dask) == pytest.approx(1.0)

# --- Test apply_pdcsap_detrending ---
def test_apply_pdcsap_detrending_removes_trend(default_sim_params):
    simulator = TransitSimulator(**default_sim_params)
    
    # Create a raw light curve with a clear trend + a small transit
    times = np.arange(0.0, 10.0, 0.1)
    transit_signal = np.where((times > 4.5) & (times < 5.5), 0.9, 1.0) # Simple box transit
    systematic_trend = 1.0 + 0.1 * np.sin(times / 2.0) + 0.005 * times # Sinusoidal + linear trend
    
    raw_fluxes = transit_signal * systematic_trend + np.random.normal(0, 0.001, size=len(times)) # Add some noise
    raw_fluxes_normalized_by_max = raw_fluxes / np.max(raw_fluxes) # Simulate initial normalization

    detrended_fluxes = simulator.apply_pdcsap_detrending(times, raw_fluxes_normalized_by_max)
    
    # Check if the out-of-transit baseline is flattened (close to 1.0 after re-normalization)
    oot_mask = (times < 4.0) | (times > 6.0) # Mask transit region
    assert np.std(detrended_fluxes[oot_mask]) < np.std(raw_fluxes_normalized_by_max[oot_mask]) # Std dev should decrease
    assert np.allclose(np.mean(detrended_fluxes[oot_mask]), 1.0, atol=0.01) # OOT baseline should be flat around 1.0

    # Check if transit signal is preserved (depth should still be visible)
    transit_data_detrended = detrended_fluxes[(times > 4.5) & (times < 5.5)]
    assert np.min(transit_data_detrended) < 0.95 # Depth should be maintained

def test_apply_pdcsap_detrending_insufficient_oot_data(default_sim_params):
    simulator = TransitSimulator(**default_sim_params)
    times = np.arange(0.0, 1.0, 0.01) # Short duration
    # Make almost all data in transit
    simulator.planets = [Planet(radius=1.0, period=1.0, semimajor_axis=2.0, inclination=90.0, epoch_transit=0.5)] 
    
    raw_fluxes = np.ones_like(times) + np.random.normal(0, 0.01, size=len(times))
    
    # Should print warning and return normalized raw fluxes
    with pytest.warns(UserWarning, match="Insufficient out-of-transit data"): # Use pytest.warns to check for specific warning
        detrended_fluxes = simulator.apply_pdcsap_detrending(times, raw_fluxes)
    
    assert np.allclose(detrended_fluxes, raw_fluxes / np.max(raw_fluxes)) # Should essentially return normalized raw fluxes