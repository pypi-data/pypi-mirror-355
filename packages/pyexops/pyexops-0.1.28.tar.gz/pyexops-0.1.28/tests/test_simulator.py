# pyexops/tests/test_simulator.py

import pytest
import numpy as np
from pyexops import Star, Planet, TransitSimulator, Atmosphere

# Common parameters for tests
STAR_RADIUS = 10.0
STAR_BASE_FLUX = 5000.0
LIMB_DARKENING = (0.3, 0.2)
STAR_MASS = 1.0 # Solar masses

IMAGE_RESOLUTION = (100, 100)
STAR_CENTER_PIXEL = (50, 50)
BACKGROUND_FLUX_PER_PIXEL = 5.0
READ_NOISE_STD = 5.0
PSF_TYPE = 'gaussian'
PSF_PARAMS = {'sigma_pixels': 1.5}

TARGET_APERTURE_RADIUS = 3.0 * PSF_PARAMS['sigma_pixels']
BG_INNER_RADIUS = TARGET_APERTURE_RADIUS + 5.0
BG_OUTER_RADIUS = BG_INNER_RADIUS + 10.0

def create_simple_simulator(planet_radius=0.1, planet_period=1.0, planet_mass=0.01,
                            planet_albedo=0.0, planet_atmosphere=None):
    star = Star(STAR_RADIUS, STAR_BASE_FLUX, LIMB_DARKENING, STAR_MASS)
    planet = Planet(
        radius=planet_radius,
        period=planet_period,
        semimajor_axis=10.0, # in stellar radii
        inclination=89.5, # slightly grazing
        epoch_transit=0.5, # mid-transit at 0.5 days
        planet_mass=planet_mass, # in Jupiter masses
        albedo=planet_albedo,
        atmosphere=planet_atmosphere
    )
    return TransitSimulator(
        star=star,
        planets=[planet],
        image_resolution=IMAGE_RESOLUTION,
        star_center_pixel=STAR_CENTER_PIXEL,
        background_flux_per_pixel=BACKGROUND_FLUX_PER_PIXEL,
        target_aperture_radius_pixels=TARGET_APERTURE_RADIUS,
        background_aperture_inner_radius_pixels=BG_INNER_RADIUS,
        background_aperture_outer_radius_pixels=BG_OUTER_RADIUS,
        read_noise_std=READ_NOISE_STD,
        psf_type=PSF_TYPE,
        psf_params=PSF_PARAMS
    )

def test_run_simulation_basic_light_curve():
    simulator = create_simple_simulator()
    times = np.linspace(0, 1.0, 50) # Covers one transit
    
    sim_times, fluxes, _, _ = simulator.run_simulation(times, add_noise=False, inject_systematics=False)
    
    assert len(sim_times) == len(times)
    assert np.min(fluxes) < 1.0 # Should have a transit dip
    assert np.isclose(np.max(fluxes), 1.0) # Should be normalized to 1.0 OOT

def test_run_simulation_with_noise():
    simulator = create_simple_simulator()
    times = np.linspace(0, 1.0, 50)
    
    _, noisy_fluxes, _, _ = simulator.run_simulation(times, add_noise=True, inject_systematics=False)
    _, clean_fluxes, _, _ = simulator.run_simulation(times, add_noise=False, inject_systematics=False)
    
    assert not np.array_equal(noisy_fluxes, clean_fluxes) # Noise should make them different

def test_run_simulation_with_systematics():
    simulator = create_simple_simulator()
    times = np.linspace(0, 10.0, 100) # Long enough to see systematics
    
    _, fluxes_with_sys, _, _ = simulator.run_simulation(times, add_noise=False, inject_systematics=True)
    _, fluxes_without_sys, _, _ = simulator.run_simulation(times, add_noise=False, inject_systematics=False)
    
    # Should have a trend
    assert np.std(fluxes_with_sys) > np.std(fluxes_without_sys) * 1.5 # Significant systematic trend

def test_apply_pdcsap_detrending():
    simulator = create_simple_simulator()
    times = np.linspace(0, 10.0, 100)
    # Generate raw fluxes with strong systematics
    _, raw_fluxes_with_sys, _, _ = simulator.run_simulation(times, add_noise=False, inject_systematics=True)
    
    detrended_fluxes = simulator.apply_pdcsap_detrending(times, raw_fluxes_with_sys)
    
    # Detrended fluxes should have lower std deviation (systematics removed)
    assert np.std(detrended_fluxes) < np.std(raw_fluxes_with_sys) * 0.5 # Should be significantly reduced

def test_run_simulation_with_rv():
    # Make a more massive planet for a clear RV signal
    simulator = create_simple_simulator(planet_mass=5.0) 
    times = np.linspace(0, 3.0, 100) # Covers one period
    
    _, _, rvs, _ = simulator.run_simulation(times, return_radial_velocity=True,
                                            rv_instrumental_noise_std=0.0, stellar_jitter_std=0.0)
    
    assert rvs is not None
    assert np.min(rvs) < 0.0 # Should have a sinusoidal RV curve
    assert np.max(rvs) > 0.0

def test_run_simulation_with_rv_noise():
    simulator = create_simple_simulator(planet_mass=5.0)
    times = np.linspace(0, 3.0, 100)
    
    _, _, rvs_noisy, _ = simulator.run_simulation(times, return_radial_velocity=True,
                                                 rv_instrumental_noise_std=10.0, stellar_jitter_std=5.0)
    _, _, rvs_clean, _ = simulator.run_simulation(times, return_radial_velocity=True,
                                                 rv_instrumental_noise_std=0.0, stellar_jitter_std=0.0)
    
    assert not np.array_equal(rvs_noisy, rvs_clean) # Noise should make them different
    assert np.std(rvs_noisy - rvs_clean) > 0.1 # Significant noise added

def test_run_simulation_with_reflected_light():
    # Planet needs to be close and have high albedo for noticeable phase curve
    simulator = create_simple_simulator(
        planet_radius=0.1, # Small transit, so phase curve is clearer
        planet_period=0.5, # Very short period for distinct phase curve
        planet_albedo=0.8
    )
    times = np.linspace(0, 1.0, 100) # Two periods
    
    _, fluxes_with_phase, _, reflected_fluxes_only = simulator.run_simulation(
        times, 
        add_noise=False, 
        inject_systematics=False,
        include_reflected_light=True
    )
    
    assert reflected_fluxes_only is not None
    # Reflected light should be positive values
    assert np.all(reflected_fluxes_only >= 0)
    # The flux should show a modulation due to reflected light
    # Fluxes_with_phase should show a very subtle hump at secondary eclipse (period/2 after transit)
    # The amplitude of the phase curve is (albedo * (Rp/ap)^2 * StarFlux)
    # Let's verify that the max flux is roughly at secondary eclipse (relative to transit)
    
    # Find flux at transit and secondary eclipse
    transit_time = 0.5 # As defined in create_simple_simulator
    secondary_eclipse_time = transit_time + (0.5 * 0.5) # Period 0.5, half period later
    
    idx_transit = np.argmin(np.abs(times - transit_time))
    idx_secondary_eclipse = np.argmin(np.abs(times - secondary_eclipse_time))

    flux_at_transit = fluxes_with_phase[idx_transit]
    flux_at_secondary_eclipse = fluxes_with_phase[idx_secondary_eclipse]

    # For a hump at secondary eclipse (as implemented in OrbitalSolver), flux_at_secondary_eclipse should be higher
    # than flux_at_transit (excluding the transit dip itself, which is already applied)
    # The normalization divides by OOT flux, so it's tricky.
    # Let's check reflected_fluxes_only instead.
    refl_at_transit = reflected_fluxes_only[idx_transit]
    refl_at_secondary_eclipse = reflected_fluxes_only[idx_secondary_eclipse]

    # Max reflected flux should be at secondary eclipse (as implemented)
    assert refl_at_secondary_eclipse > refl_at_transit
    assert np.isclose(refl_at_transit, 0.0, atol=1e-5 * np.max(reflected_fluxes_only)), "Reflected flux should be near zero at transit"
    assert np.isclose(refl_at_secondary_eclipse, np.max(reflected_fluxes_only), rtol=1e-5), "Reflected flux should be maximal at secondary eclipse"


def test_run_simulation_with_transmission_spectroscopy():
    """
    Test run_simulation accurately models transmission spectroscopy effects.
    Planet is effectively larger at 850nm than at 600nm.
    """
    solid_radius = 0.1
    # Atmosphere makes planet effectively 0.16 at 850nm, 0.12 at 600nm
    transmission_data = [(600.0, 0.12), (850.0, 0.16)]
    atmosphere = Atmosphere(solid_radius, transmission_data)

    # Use a planet with this atmosphere
    simulator = create_simple_simulator(planet_radius=solid_radius, planet_atmosphere=atmosphere)
    
    times = np.linspace(0, 1.0, 50) # Covers one transit

    # Run simulation at 850nm (larger effective radius)
    _, fluxes_850nm, _, _ = simulator.run_simulation(times, add_noise=False, inject_systematics=False, wavelength_nm=850.0)
    # Run simulation at 600nm (smaller effective radius)
    _, fluxes_600nm, _, _ = simulator.run_simulation(times, add_noise=False, inject_systematics=False, wavelength_nm=600.0)
    
    # Calculate transit depths
    depth_850nm = 1.0 - np.min(fluxes_850nm)
    depth_600nm = 1.0 - np.min(fluxes_600nm)

    # Transit at 850nm should be deeper than at 600nm
    assert depth_850nm > depth_600nm, "Transit depth at 850nm should be greater due to larger effective radius."
    assert depth_850nm > 0 # Ensure actual transit happened
    assert depth_600nm > 0