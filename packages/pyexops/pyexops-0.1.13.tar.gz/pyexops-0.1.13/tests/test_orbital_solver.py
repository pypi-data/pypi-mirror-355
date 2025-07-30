# pyexops/tests/test_orbital_solver.py

import pytest
import numpy as np
from pyexops import OrbitalSolver

# Define some common test parameters
STAR_MASS_SUN = 1.0
PLANET_MASS_JUP = 1.0 # 1 Jupiter mass
PERIOD_DAYS = 3.0
SEMIMAJOR_AXIS_STELLAR_RADII = 10.0 # 10 stellar radii
INCLINATION_DEG = 90.0 # Transiting
EPOCH_TRANSIT_DAYS = 0.0 # Transit at t=0
TIMES = np.linspace(-0.5 * PERIOD_DAYS, 0.5 * PERIOD_DAYS, 100) # One complete orbit centered at transit

def test_rv_circular_basic_amplitude():
    """
    Tests the basic amplitude of a circular RV curve.
    For the system: M_star=1 M_Sol, M_planet=1 M_Jup, P=3 days, a=10 R_star.
    A calculated estimate (using OrbitalSolver's constants)
    for this specific system is K = ~170.16 m/s.
    """
    rvs = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES
    )
    # The amplitude is K (from the K * sin(phi) formula)
    max_rv = np.max(rvs)
    min_rv = np.min(rvs)
    amplitude = (max_rv - min_rv) / 2

    expected_amplitude = 170.16 # m/s (calculated value)
    assert np.isclose(amplitude, expected_amplitude, rtol=1e-2), f"Expected RV amplitude {expected_amplitude}, got {amplitude}"
    assert np.isclose(rvs[np.argmin(np.abs(TIMES - EPOCH_TRANSIT_DAYS))], 0.0, atol=1e-5), "RV at mid-transit should be 0"

def test_rv_zero_inclination():
    """Tests RV for zero inclination (face-on view, no signal)."""
    rvs = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=0.0, # Zero inclination
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES
    )
    assert np.allclose(rvs, 0.0, atol=1e-9), "RV should be zero for 0 inclination"

def test_rv_180_inclination():
    """Tests RV for 180 degrees inclination (also should be zero, or very close)."""
    rvs = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=180.0, # 180 degrees inclination
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES
    )
    assert np.allclose(rvs, 0.0, atol=1e-9), "RV should be zero for 180 degree inclination"

def test_rv_planet_mass_effect():
    """Tests how planet mass affects RV amplitude."""
    rvs_low_mass = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=0.1, # 0.1 Jupiter mass
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES
    )
    rvs_high_mass = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=10.0, # 10 Jupiter masses
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES
    )
    amplitude_low = (np.max(rvs_low_mass) - np.min(rvs_low_mass)) / 2
    amplitude_high = (np.max(rvs_high_mass) - np.min(rvs_high_mass)) / 2
    assert amplitude_high > amplitude_low, "Higher planet mass should result in higher RV amplitude"
    assert np.isclose(amplitude_high, amplitude_low * 10, rtol=1e-2), "Amplitude should scale linearly with planet mass"

def test_rv_period_effect():
    """Tests how period affects RV amplitude."""
    rvs_short_period = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=1.0, # 1 day
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES
    )
    rvs_long_period = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=10.0, # 10 days
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES
    )
    amplitude_short = (np.max(rvs_short_period) - np.min(rvs_short_period)) / 2
    amplitude_long = (np.max(rvs_long_period) - np.min(rvs_long_period)) / 2
    assert amplitude_short > amplitude_long, "Shorter period should result in higher RV amplitude"
    # If semi-major axis is kept constant, K is inversely proportional to P.
    assert np.isclose(amplitude_short, amplitude_long * (10.0 / 1.0), rtol=0.05), "Amplitude should scale inversely with period (keeping 'a' constant)"


def test_rv_phase_circular():
    """Tests the phase of a circular RV curve."""
    # With epoch_transit = 0.0, RV should be 0 at t=0, then positive.
    rvs = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=np.array([-0.01, 0.0, 0.01]) # Times around transit epoch
    )
    assert np.isclose(rvs[1], 0.0, atol=1e-5), "RV at epoch_transit (circular) should be 0."
    assert rvs[2] > rvs[1], "RV should increase after epoch_transit (circular)."
    assert rvs[0] < rvs[1], "RV should decrease before epoch_transit (circular)."

def test_rv_small_star_mass():
    """Tests with a very small star mass (e.g., brown dwarf or very low-mass star)."""
    rvs_small_star = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=0.1, # 0.1 Solar Mass
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES
    )
    rvs_normal_star = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN, # 1 Solar Mass
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES
    )
    amplitude_small_star = (np.max(rvs_small_star) - np.min(rvs_small_star)) / 2
    amplitude_normal_star = (np.max(rvs_normal_star) - np.min(rvs_normal_star)) / 2
    assert amplitude_small_star > amplitude_normal_star, "Smaller stellar mass should result in higher RV amplitude"
    # The scaling is approximately (M_star_normal / M_star_small)
    assert np.isclose(amplitude_small_star, amplitude_normal_star * (STAR_MASS_SUN / 0.1), rtol=0.2), "Amplitude should scale approximately inversely with stellar mass"

def test_rv_eccentricity_no_effect_in_current_impl():
    """
    Tests that eccentricity currently has no effect on RV in the circular-only implementation.
    This test will need to be updated when full elliptical RV is implemented.
    """
    rvs_e0 = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        eccentricity=0.0,
        argument_of_periastron=90.0,
        times=TIMES
    )
    rvs_e0_5 = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        eccentricity=0.5, # Non-zero eccentricity
        argument_of_periastron=90.0,
        times=TIMES
    )
    # They should be identical, as eccentricity is not yet used in the calculation.
    assert np.allclose(rvs_e0, rvs_e0_5, atol=1e-9), "Eccentricity should not affect RV in the circular-only implementation."

def test_rv_argument_of_periastron_no_effect_in_current_impl():
    """
    Tests that argument_of_periastron currently has no effect on RV in the circular-only implementation.
    This test will need to be updated when full elliptical RV is implemented.
    """
    rvs_omega90 = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        eccentricity=0.0,
        argument_of_periastron=90.0,
        times=TIMES
    )
    rvs_omega0 = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        eccentricity=0.0,
        argument_of_periastron=0.0, # Different argument of periastron
        times=TIMES
    )
    # They should be identical, as argument_of_periastron is not yet used in the circular-only calculation.
    assert np.allclose(rvs_omega90, rvs_omega0, atol=1e-9), "Argument of periastron should not affect RV in the circular-only implementation."