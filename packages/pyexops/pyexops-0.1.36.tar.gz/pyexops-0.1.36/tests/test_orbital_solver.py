# pyexops/tests/test_orbital_solver.py

import numpy as np
import pytest
from pyexops.orbital_solver import OrbitalSolver

# Constants for test readability
M_SUN = OrbitalSolver.M_SUN
M_JUP = OrbitalSolver.M_JUP
R_SUN = OrbitalSolver.R_SUN
AU = OrbitalSolver.AU
G = OrbitalSolver.G
C = OrbitalSolver.G_SPEED_OF_LIGHT # Speed of light

def test__solve_kepler_equation_circular():
    M = np.array([0.0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi])
    e = 0.0
    E = OrbitalSolver._solve_kepler_equation(M, e)
    assert np.allclose(E, M)

def test__solve_kepler_equation_elliptical():
    M = np.array([0.0, np.pi/2, np.pi])
    e = 0.5
    E = OrbitalSolver._solve_kepler_equation(M, e)
    assert np.allclose(E[0], 0.0)
    assert np.allclose(E[2], np.pi)
    assert np.isclose(E[1], 1.930847, atol=1e-6)

def test__solve_kepler_equation_invalid_eccentricity():
    M = np.array([0.0])
    with pytest.raises(ValueError, match="Eccentricity must be between 0 \(inclusive\) and 1 \(exclusive\)."):
        OrbitalSolver._solve_kepler_equation(M, 1.0)
    with pytest.raises(ValueError, match="Eccentricity must be between 0 \(inclusive\) and 1 \(exclusive\)."):
        OrbitalSolver._solve_kepler_equation(M, -0.1)

def test_calculate_stellar_radial_velocity_circular_orbit():
    star_mass = 1.0 
    planet_mass_large = 1.0 # M_Jup
    period = 3.0 
    semimajor_axis = 0.04 
    inclination = 90.0 
    epoch_transit = 1.5 
    times = np.array([0.0, 0.75, 1.5, 2.25, 3.0]) 

    M_star_kg = star_mass * M_SUN
    m_planet_kg = planet_mass_large * M_JUP
    P_sec = period * OrbitalSolver.DAY_TO_SEC
    inclination_rad = np.deg2rad(inclination)
    
    K_expected = (m_planet_kg * np.sin(inclination_rad)) / ((M_star_kg + m_planet_kg)**(2/3)) * \
                 ((2 * G * np.pi) / P_sec)**(1/3) / np.sqrt(1 - 0.0**2)
    
    rvs = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=star_mass, planet_mass=planet_mass_large, period=period,
        semimajor_axis=semimajor_axis / (R_SUN / AU), 
        inclination=inclination, epoch_transit=epoch_transit, times=times
    )
    
    assert np.isclose(rvs[2], -K_expected, atol=0.01) 
    assert np.isclose(rvs[0], rvs[4], atol=1e-6) 
    assert np.isclose(rvs[1], K_expected, atol=0.01) 
    assert np.isclose(rvs[3], K_expected, atol=0.01) 


def test_calculate_stellar_radial_velocity_elliptical_orbit():
    star_mass = 1.0 
    planet_mass = 1.0 
    period = 10.0 
    semimajor_axis = 0.1 
    inclination = 89.0 
    epoch_transit = 5.0 
    eccentricity = 0.3
    argument_of_periastron = 0.0 
    times = np.array([0.0, 2.5, 5.0, 7.5, 10.0]) 

    rvs = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=star_mass, planet_mass=planet_mass, period=period,
        semimajor_axis=semimajor_axis / (R_SUN / AU), 
        inclination=inclination, epoch_transit=epoch_transit, times=times,
        eccentricity=eccentricity, argument_of_periastron=argument_of_periastron
    )
    
    assert rvs.shape == times.shape
    assert np.max(rvs) > 0 and np.min(rvs) < 0 
    assert not np.isclose(rvs[0], rvs[1], atol=0.1) 

def test_calculate_reflected_flux():
    star_flux_oot = 1000.0
    planet_radius_stellar_radii = 0.1
    planet_semimajor_axis_stellar_radii = 10.0
    planet_period_days = 10.0
    planet_epoch_transit_days = 5.0
    planet_albedo = 0.5
    times = np.array([0.0, 2.5, 5.0, 7.5, 10.0]) 

    fluxes = OrbitalSolver.calculate_reflected_flux(
        star_flux_oot, planet_radius_stellar_radii, planet_semimajor_axis_stellar_radii,
        planet_period_days, planet_epoch_transit_days, planet_albedo, times
    )

    assert fluxes.shape == times.shape
    assert np.all(fluxes >= 0) 

    assert np.isclose(fluxes[2], 0.0, atol=1e-9) 
    
    max_reflected_flux_expected = star_flux_oot * planet_albedo * (planet_radius_stellar_radii / planet_semimajor_axis_stellar_radii)**2
    assert np.isclose(fluxes[0], max_reflected_flux_expected, atol=1e-9) 
    assert np.isclose(fluxes[4], max_reflected_flux_expected, atol=1e-9) 

    assert np.isclose(fluxes[1], max_reflected_flux_expected / 2, atol=1e-9)
    assert np.isclose(fluxes[3], max_reflected_flux_expected / 2, atol=1e-9)

    assert np.allclose(OrbitalSolver.calculate_reflected_flux(star_flux_oot, 0.1, 10, 10, 5, 0.0, times), 0.0) 
    fluxes_albedo_1 = OrbitalSolver.calculate_reflected_flux(star_flux_oot, 0.1, 10, 10, 5, 1.0, times)
    assert np.isclose(fluxes_albedo_1[0], star_flux_oot * (0.1/10)**2, atol=1e-9)

    with pytest.raises(ValueError, match="Albedo must be between 0.0 and 1.0."):
        OrbitalSolver.calculate_reflected_flux(star_flux_oot, 0.1, 10, 10, 5, 1.1, times)


# --- NEW TESTS FOR TASK 4.2 ---

def test_calculate_doppler_beaming_factor():
    rvs_ms = np.array([-1000.0, 0.0, 1000.0]) 
    stellar_spectral_index = 3.0 

    expected_factors = np.array([
        1.0 + 5 * (-1000.0 / C), 
        1.0,                       
        1.0 + 5 * (1000.0 / C)     
    ])
    
    beaming_factors = OrbitalSolver.calculate_doppler_beaming_factor(rvs_ms, stellar_spectral_index)
    
    assert beaming_factors.shape == rvs_ms.shape
    assert np.allclose(beaming_factors, expected_factors, atol=1e-9)
    
    assert np.isclose(OrbitalSolver.calculate_doppler_beaming_factor(np.array([0.0]))[0], 1.0)
    
    rv_extreme = np.array([0.1 * C]) 
    factor_extreme = OrbitalSolver.calculate_doppler_beaming_factor(rv_extreme, stellar_spectral_index)
    assert np.isclose(factor_extreme[0], 1.0 + 5 * 0.1)

    beaming_factors_default = OrbitalSolver.calculate_doppler_beaming_factor(rvs_ms)
    assert np.allclose(beaming_factors_default, expected_factors, atol=1e-9)

def test_calculate_ellipsoidal_variation_factor():
    star_mass_solar = 1.0
    planet_mass_jupiter = 5.0 
    star_radius_stellar_radii = 1.0 
    planet_semimajor_axis_stellar_radii = 5.0 
    inclination_deg = 90.0 
    period_days = 1.0
    epoch_transit_days = 0.5
    times_days = np.array([0.0, 0.25, 0.5, 0.75, 1.0]) 
    stellar_gravity_darkening_coeff = 0.32
    stellar_limb_darkening_coeffs = (0.5, 0.2) 

    factors = OrbitalSolver.calculate_ellipsoidal_variation_factor(
        star_mass_solar, planet_mass_jupiter, star_radius_stellar_radii,
        planet_semimajor_axis_stellar_radii, inclination_deg, period_days,
        epoch_transit_days, times_days, stellar_gravity_darkening_coeff,
        stellar_limb_darkening_coeffs
    )

    assert factors.shape == times_days.shape
    assert np.all(factors > 0) 

    assert factors[0] > factors[1] 
    assert factors[2] > factors[1] 
    assert factors[0] == pytest.approx(factors[2], abs=1e-9) 
    assert factors[1] == pytest.approx(factors[3], abs=1e-9) 

    factors_inc_0 = OrbitalSolver.calculate_ellipsoidal_variation_factor(
        star_mass_solar, planet_mass_jupiter, star_radius_stellar_radii,
        planet_semimajor_axis_stellar_radii, 0.0, period_days,
        epoch_transit_days, times_days, stellar_gravity_darkening_coeff,
        stellar_limb_darkening_coeffs
    )
    assert np.allclose(factors_inc_0, 1.0, atol=1e-9) 

    assert np.allclose(OrbitalSolver.calculate_ellipsoidal_variation_factor(
        0.0, planet_mass_jupiter, star_radius_stellar_radii,
        planet_semimajor_axis_stellar_radii, inclination_deg, period_days, epoch_transit_days, times_days), 1.0)
    assert np.allclose(OrbitalSolver.calculate_ellipsoidal_variation_factor(
        star_mass_solar, 0.0, star_radius_stellar_radii,
        planet_semimajor_axis_stellar_radii, inclination_deg, period_days, epoch_transit_days, times_days), 1.0)
    assert np.allclose(OrbitalSolver.calculate_ellipsoidal_variation_factor(
        star_mass_solar, planet_mass_jupiter, star_radius_stellar_radii,
        0.0, inclination_deg, period_days, epoch_transit_days, times_days), 1.0)

# --- NEW TESTS FOR SECONDARY ECLIPSE (FROM FASE 5.4 - INCLUDED HERE FOR CONSISTENCY) ---

def test_calculate_secondary_eclipse_factor_full_eclipse():
    """Test secondary eclipse factor for full occultation."""
    # Star is larger than planet, planet goes fully behind
    star_r = 1.0
    planet_r = 0.1
    semimajor_a = 10.0
    inc = 90.0
    epoch_transit = 0.0
    period = 1.0
    times = np.array([0.5]) # Mid-secondary eclipse

    # For these parameters and t=0.5, planet should be at z=a, b=0 (full occultation)
    factor = OrbitalSolver.calculate_secondary_eclipse_factor(
        star_r, planet_r, semimajor_a, inc, epoch_transit, times
    )
    assert np.isclose(factor[0], 0.0, atol=1e-6) # Fully occulted

def test_calculate_secondary_eclipse_factor_no_eclipse():
    """Test secondary eclipse factor when no occultation occurs."""
    star_r = 0.1 # Star smaller than planet's radius
    planet_r = 1.0
    semimajor_a = 10.0
    inc = 0.0 # Face-on orbit, no eclipse
    epoch_transit = 0.0
    period = 1.0
    times = np.array([0.0, 0.5]) # Transit and secondary eclipse times

    factor = OrbitalSolver.calculate_secondary_eclipse_factor(
        star_r, planet_r, semimajor_a, inc, epoch_transit, times
    )
    assert np.allclose(factor, 1.0, atol=1e-6) # Always fully visible

    # Also test for when planet is in front (primary transit region)
    factor = OrbitalSolver.calculate_secondary_eclipse_factor(
        1.0, 0.1, 10.0, 90.0, 0.5, np.array([0.0]) # Times for primary transit
    )
    assert np.allclose(factor, 1.0, atol=1e-6) # No secondary eclipse effect in primary transit

def test_calculate_secondary_eclipse_factor_partial_eclipse_linear_approx():
    """Test secondary eclipse factor with partial occultation (using linear approx)."""
    # Star and planet radii close enough for partial.
    star_r = 1.0
    planet_r = 0.8
    semimajor_a = 2.0 # Very close orbit for strong overlap
    inc = 90.0
    epoch_transit = 0.0
    period = 1.0
    
    # Times for ingress/egress of secondary eclipse (around t=0.5)
    # The 'd' parameter is b_proj / Rs.
    # d = 1 - p (start of egress from total eclipse) = 1 - 0.8 = 0.2
    # d = 1 + p (end of egress) = 1 + 0.8 = 1.8
    # Let's pick a 'd' value in between.
    
    # Simulate a time where projected_separation_b (b_val) is within partial eclipse
    # e.g., t=0.45 or t=0.55 relative to mid-eclipse t=0.5.
    # orbital phase for mid-eclipse is pi.
    # A time of 0.499 period from epoch_transit + period/2
    
    # We need to calculate `b_val` at a specific time.
    # At t=0.5 (mid-eclipse), b_val=0. Let's try t=0.5 + 0.005 days.
    test_time = np.array([0.5 + 0.005])
    
    # This test is highly dependent on the internal linear approximation in orbital_solver.py.
    # If the approximation changes, this test will need adjustment.
    # It ensures the factor is between 0 and 1 for a partial eclipse.
    factor = OrbitalSolver.calculate_secondary_eclipse_factor(
        star_r, planet_r, semimajor_a, inc, epoch_transit, test_time,
        eccentricity=0.0, argument_of_periastron_deg=90.0 # Circular orbit, omega=90 so transit at t=0, eclipse at t=0.5
    )
    assert factor[0] > 0.0 and factor[0] < 1.0

def test_calculate_secondary_eclipse_factor_invalid_inputs():
    """Test secondary eclipse factor with invalid inputs."""
    times = np.array([0.0])
    # Zero star radius
    assert np.allclose(OrbitalSolver.calculate_secondary_eclipse_factor(0.0, 0.1, 10.0, 90.0, 0.0, times), 1.0)
    # Zero planet radius
    assert np.allclose(OrbitalSolver.calculate_secondary_eclipse_factor(1.0, 0.0, 10.0, 90.0, 0.0, times), 1.0)
    # Zero semi-major axis
    assert np.allclose(OrbitalSolver.calculate_secondary_eclipse_factor(1.0, 0.1, 0.0, 90.0, 0.0, times), 1.0)