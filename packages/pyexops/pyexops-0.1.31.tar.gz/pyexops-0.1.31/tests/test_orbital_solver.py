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
    """Test Kepler's equation solver for circular orbits."""
    M = np.array([0.0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi])
    e = 0.0
    E = OrbitalSolver._solve_kepler_equation(M, e)
    assert np.allclose(E, M)

def test__solve_kepler_equation_elliptical():
    """Test Kepler's equation solver for elliptical orbits."""
    M = np.array([0.0, np.pi/2, np.pi])
    e = 0.5
    # Expected values for M=0, pi, 2pi are E=0, pi, 2pi
    # For M=pi/2, E should be approx. 1.93 radians
    E = OrbitalSolver._solve_kepler_equation(M, e)
    assert np.allclose(E[0], 0.0)
    assert np.allclose(E[2], np.pi)
    assert np.isclose(E[1], 1.930847, atol=1e-6)

def test__solve_kepler_equation_invalid_eccentricity():
    """Test Kepler's equation solver with invalid eccentricity."""
    M = np.array([0.0])
    with pytest.raises(ValueError, match="Eccentricity must be between 0 \(inclusive\) and 1 \(exclusive\)."):
        OrbitalSolver._solve_kepler_equation(M, 1.0)
    with pytest.raises(ValueError, match="Eccentricity must be between 0 \(inclusive\) and 1 \(exclusive\)."):
        OrbitalSolver._solve_kepler_equation(M, -0.1)

def test_calculate_stellar_radial_velocity_circular_orbit():
    """Test RV calculation for a circular orbit."""
    star_mass = 1.0 # M_sun
    planet_mass = 0.001 # M_Jup (small planet)
    period = 3.0 # days
    semimajor_axis = 0.04 # AU
    inclination = 90.0 # degrees
    epoch_transit = 1.5 # days
    times = np.array([0.0, 0.75, 1.5, 2.25, 3.0]) # Times spanning one period

    # Expected RV amplitude for a typical hot Jupiter around a Sun-like star is ~100 m/s
    # K = (m_p * sin(i)) / ((M_star + m_p)^(2/3)) * ((2 * G * pi) / P)^(1/3) / sqrt(1 - e^2)
    # Using small planet mass to get small RV for testing precision.
    # For 0.001 M_Jup, K will be very small. Let's use 1 M_Jup to get a more typical K.
    planet_mass_large = 1.0 # M_Jup
    
    # Calculate K (semi-amplitude)
    M_star_kg = star_mass * M_SUN
    m_planet_kg = planet_mass_large * M_JUP
    P_sec = period * OrbitalSolver.DAY_TO_SEC
    inclination_rad = np.deg2rad(inclination)
    
    K_expected = (m_planet_kg * np.sin(inclination_rad)) / ((M_star_kg + m_planet_kg)**(2/3)) * \
                 ((2 * G * np.pi) / P_sec)**(1/3) / np.sqrt(1 - 0.0**2)
    
    # RV should be max at epoch_transit + P/4 and min at epoch_transit - P/4 (approx)
    # If omega=90deg, RV = K * (cos(f + 90) + e*cos(90)) = K * (-sin(f)).
    # At transit (f=pi-omega), f=0 if omega=pi. If omega=pi/2, f=pi/2.
    # For omega=90, RV = -K*sin(f). At transit, f approx pi/2, so RV approx -K.
    # At transit (t=1.5), planet is in front, star moving away (positive RV) if using default omega=90.
    # The RV formula is K * [cos(f + omega) + e * cos(omega)].
    # For transit (t=epoch_transit), true anomaly f = pi - omega.
    # So f + omega = pi. cos(pi) = -1.
    # RV at transit = K * (-1 + e * cos(omega)).
    # If e=0, RV at transit is -K. This means star is approaching observer.
    # Our `calculate_stellar_radial_velocity` uses a convention consistent with `radvel` for K, which is positive for approach.
    # So we expect RV at transit (t=1.5) to be -K, which is star moving towards observer.

    rvs = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=star_mass, planet_mass=planet_mass_large, period=period,
        semimajor_axis=semimajor_axis / (OrbitalSolver.R_SUN / OrbitalSolver.AU), # Convert AU to stellar radii
        inclination=inclination, epoch_transit=epoch_transit, times=times
    )
    
    assert np.isclose(rvs[2], -K_expected, atol=0.01) # Mid-transit (t=1.5)
    assert np.isclose(rvs[0], rvs[4], atol=1e-6) # Full period apart
    assert np.isclose(rvs[1], K_expected, atol=0.01) # RV should be positive max at P/4 before transit
    assert np.isclose(rvs[3], K_expected, atol=0.01) # RV should be positive max at P/4 after transit


def test_calculate_stellar_radial_velocity_elliptical_orbit():
    """Test RV calculation for an elliptical orbit."""
    star_mass = 1.0 # M_sun
    planet_mass = 1.0 # M_Jup
    period = 10.0 # days
    semimajor_axis = 0.1 # AU
    inclination = 89.0 # degrees
    epoch_transit = 5.0 # days
    eccentricity = 0.3
    argument_of_periastron = 0.0 # degrees (periastron is at the line of sight)
    times = np.array([0.0, 2.5, 5.0, 7.5, 10.0]) # Spanning one period

    rvs = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=star_mass, planet_mass=planet_mass, period=period,
        semimajor_axis=semimajor_axis / (OrbitalSolver.R_SUN / OrbitalSolver.AU), # Convert AU to stellar radii
        inclination=inclination, epoch_transit=epoch_transit, times=times,
        eccentricity=eccentricity, argument_of_periastron=argument_of_periastron
    )
    
    # For e=0.3, omega=0, transit is no longer at periastron or apastron.
    # RV curve will be asymmetric.
    assert rvs.shape == times.shape
    assert np.max(rvs) > 0 and np.min(rvs) < 0 # Should have variation
    assert not np.isclose(rvs[0], rvs[1], atol=0.1) # Should not be perfectly symmetric like circular

def test_calculate_reflected_flux():
    """Test reflected flux calculation."""
    star_flux_oot = 1000.0
    planet_radius_stellar_radii = 0.1
    planet_semimajor_axis_stellar_radii = 10.0
    planet_period_days = 10.0
    planet_epoch_transit_days = 5.0
    planet_albedo = 0.5
    times = np.array([0.0, 2.5, 5.0, 7.5, 10.0]) # Spanning one period

    fluxes = OrbitalSolver.calculate_reflected_flux(
        star_flux_oot, planet_radius_stellar_radii, planet_semimajor_axis_stellar_radii,
        planet_period_days, planet_epoch_transit_days, planet_albedo, times
    )

    assert fluxes.shape == times.shape
    assert np.all(fluxes >= 0) # Flux should be non-negative

    # At primary transit (epoch_transit = 5.0), planet is 'new moon' to observer, reflected light is 0
    assert np.isclose(fluxes[2], 0.0, atol=1e-9) # t=5.0
    
    # At secondary eclipse (t=0.0 or 10.0, epoch_transit + P/2), planet is 'full moon' to observer, reflected light is max
    # Max reflected flux = star_flux_oot * albedo * (Rp/a)^2
    max_reflected_flux_expected = star_flux_oot * planet_albedo * (planet_radius_stellar_radii / planet_semimajor_axis_stellar_radii)**2
    assert np.isclose(fluxes[0], max_reflected_flux_expected, atol=1e-9) # t=0.0
    assert np.isclose(fluxes[4], max_reflected_flux_expected, atol=1e-9) # t=10.0

    # At quadratures (t=2.5, 7.5), reflected light should be half of max (for Lambertian (1-cos)/2)
    assert np.isclose(fluxes[1], max_reflected_flux_expected / 2, atol=1e-9)
    assert np.isclose(fluxes[3], max_reflected_flux_expected / 2, atol=1e-9)

    # Test edge cases for albedo
    assert np.allclose(OrbitalSolver.calculate_reflected_flux(star_flux_oot, 0.1, 10, 10, 5, 0.0, times), 0.0) # Albedo 0
    # Albedo 1 should give factor of 1 * (Rp/a)^2
    fluxes_albedo_1 = OrbitalSolver.calculate_reflected_flux(star_flux_oot, 0.1, 10, 10, 5, 1.0, times)
    assert np.isclose(fluxes_albedo_1[0], star_flux_oot * (0.1/10)**2, atol=1e-9)

    with pytest.raises(ValueError, match="Albedo must be between 0.0 and 1.0."):
        OrbitalSolver.calculate_reflected_flux(star_flux_oot, 0.1, 10, 10, 5, 1.1, times)


# --- NEW TESTS FOR TASK 4.2 ---

def test_calculate_doppler_beaming_factor():
    """Test Doppler beaming factor calculation."""
    rvs_ms = np.array([-1000.0, 0.0, 1000.0]) # -1 km/s, 0 km/s, +1 km/s
    stellar_spectral_index = 3.0 # Gamma

    # F/F0 = 1 + (gamma + 2) * (v/c)
    # Beaming factor = 1 + (3 + 2) * (v/c) = 1 + 5 * (v/c)
    expected_factors = np.array([
        1.0 + 5 * (-1000.0 / C), # Approaching (brighter)
        1.0,                       # No motion (no change)
        1.0 + 5 * (1000.0 / C)     # Receding (dimmer)
    ])
    
    beaming_factors = OrbitalSolver.calculate_doppler_beaming_factor(rvs_ms, stellar_spectral_index)
    
    assert beaming_factors.shape == rvs_ms.shape
    assert np.allclose(beaming_factors, expected_factors, atol=1e-9)
    
    # Check for RV = 0, factor is 1
    assert np.isclose(OrbitalSolver.calculate_doppler_beaming_factor(np.array([0.0]))[0], 1.0)
    
    # Check for very high RV (still within float limits)
    rv_extreme = np.array([0.1 * C]) # 10% speed of light
    factor_extreme = OrbitalSolver.calculate_doppler_beaming_factor(rv_extreme, stellar_spectral_index)
    assert np.isclose(factor_extreme[0], 1.0 + 5 * 0.1)

    # Test with default spectral index
    beaming_factors_default = OrbitalSolver.calculate_doppler_beaming_factor(rvs_ms)
    assert np.allclose(beaming_factors_default, expected_factors, atol=1e-9)

def test_calculate_ellipsoidal_variation_factor():
    """Test ellipsoidal variation factor calculation."""
    star_mass_solar = 1.0
    planet_mass_jupiter = 5.0 # Very massive planet to see effect
    star_radius_stellar_radii = 1.0 # 1 stellar radius
    planet_semimajor_axis_stellar_radii = 5.0 # Close-in orbit (5 stellar radii)
    inclination_deg = 90.0 # Edge-on orbit
    period_days = 1.0
    epoch_transit_days = 0.5
    times_days = np.array([0.0, 0.25, 0.5, 0.75, 1.0]) # Covering two conjunctions (0.0, 0.5, 1.0) and two quadratures (0.25, 0.75)
    stellar_gravity_darkening_coeff = 0.32
    stellar_limb_darkening_coeffs = (0.5, 0.2) # u1, u2

    # Expect two peaks (brighter) at conjunctions (transit, secondary eclipse)
    # and two troughs (dimmer) at quadratures.
    # At t=0.5 (transit), flux should be maximum (1 - amp * cos(2*0)) = 1 - amp (if orbital phase is 0 at transit)
    # Our orbital_phase is 0 at transit (epoch_transit)
    # So `np.cos(2 * orbital_phase)` will be 1 at transit (t=0.5), and -1 at quadratures (t=0.25, 0.75).
    # Therefore, flux_factor = 1.0 - base_amplitude_relative * np.cos(2 * orbital_phase)
    # Max at transit (t=0.5) and secondary eclipse (t=0.0, 1.0)
    # Min at quadratures (t=0.25, 0.75)

    factors = OrbitalSolver.calculate_ellipsoidal_variation_factor(
        star_mass_solar, planet_mass_jupiter, star_radius_stellar_radii,
        planet_semimajor_axis_stellar_radii, inclination_deg, period_days,
        epoch_transit_days, times_days, stellar_gravity_darkening_coeff,
        stellar_limb_darkening_coeffs
    )

    assert factors.shape == times_days.shape
    assert np.all(factors > 0) # Factors should be positive

    # Expected pattern: Max at 0.0, 0.5, 1.0 (conjunctions) and Min at 0.25, 0.75 (quadratures)
    assert factors[0] > factors[1] # Conjunction > Quadrature
    assert factors[2] > factors[1] # Conjunction > Quadrature
    assert factors[0] == pytest.approx(factors[2], abs=1e-9) # Both conjunctions should be similar magnitude
    assert factors[1] == pytest.approx(factors[3], abs=1e-9) # Both quadratures should be similar magnitude

    # Test inclination effects: if inclination is 0 (face-on), sin^2(i) is 0, so no variation
    factors_inc_0 = OrbitalSolver.calculate_ellipsoidal_variation_factor(
        star_mass_solar, planet_mass_jupiter, star_radius_stellar_radii,
        planet_semimajor_axis_stellar_radii, 0.0, period_days,
        epoch_transit_days, times_days, stellar_gravity_darkening_coeff,
        stellar_limb_darkening_coeffs
    )
    assert np.allclose(factors_inc_0, 1.0, atol=1e-9) # Should be flat line at 1.0

    # Test with zero masses or semi-major axis, should return 1.0
    assert np.allclose(OrbitalSolver.calculate_ellipsoidal_variation_factor(
        0.0, planet_mass_jupiter, star_radius_stellar_radii,
        planet_semimajor_axis_stellar_radii, inclination_deg, period_days, epoch_transit_days, times_days), 1.0)
    assert np.allclose(OrbitalSolver.calculate_ellipsoidal_variation_factor(
        star_mass_solar, 0.0, star_radius_stellar_radii,
        planet_semimajor_axis_stellar_radii, inclination_deg, period_days, epoch_transit_days, times_days), 1.0)
    assert np.allclose(OrbitalSolver.calculate_ellipsoidal_variation_factor(
        star_mass_solar, planet_mass_jupiter, star_radius_stellar_radii,
        0.0, inclination_deg, period_days, epoch_transit_days, times_days), 1.0)