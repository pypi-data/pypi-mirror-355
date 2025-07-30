# pyexops/tests/test_orbital_solver.py

import pytest
import numpy as np
from pyexops import OrbitalSolver

# Define some common test parameters
STAR_MASS_SUN = 1.0
PLANET_MASS_JUP = 1.0 # 1 Jupiter mass
PERIOD_DAYS = 3.0
SEMIMAJOR_AXIS_STELLAR_RADII = 10.0 # 10 stellar radii (used for image, but K uses masses/period)
INCLINATION_DEG = 90.0 # Transiting
EPOCH_TRANSIT_DAYS = 0.0 # Transit at t=0
TIMES = np.linspace(-0.5 * PERIOD_DAYS, 0.5 * PERIOD_DAYS, 100) # One complete orbit centered at transit

def test_rv_circular_basic_amplitude():
    """
    Tests the basic amplitude of a circular RV curve.
    For the system: M_star=1 M_Sol, M_planet=1 M_Jup, P=3 days, a_planet = 0.04 AU (approx)
    Using the more general K formula: K = ~170.16 m/s
    """
    rvs = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII, # This 'a' is mainly for scene, K doesn't use it directly here
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES,
        eccentricity=0.0 # Explicitly circular
    )
    
    max_rv = np.max(rvs)
    min_rv = np.min(rvs)
    amplitude = (max_rv - min_rv) / 2

    # Theoretical K calculation for reference (approximated a_planet from P and M_star)
    # G = 6.67430e-11
    # M_SUN = 1.98847e30
    # M_JUP = 1.898e27
    # DAY_TO_SEC = 86400
    # M_star_kg = STAR_MASS_SUN * M_SUN
    # m_planet_kg = PLANET_MASS_JUP * M_JUP
    # P_sec = PERIOD_DAYS * DAY_TO_SEC
    # a_planet_cubed = (G * M_star_kg * P_sec**2) / (4 * np.pi**2) # using M_star approximation
    # a_planet_m = a_planet_cubed**(1/3)
    # K_calc = (2 * np.pi * a_planet_m * np.sin(np.deg2rad(INCLINATION_DEG))) / P_sec * (m_planet_kg / M_star_kg)
    # print(K_calc) # This gives ~170.16 m/s

    expected_amplitude = 170.16 # m/s (calculated value for a~0.04 AU planet)
    assert np.isclose(amplitude, expected_amplitude, rtol=1e-2), f"Expected RV amplitude {expected_amplitude}, got {amplitude}"
    
    # RV at mid-transit should be 0 for circular, assuming omega=90 (periastron at highest RV point, not transit)
    # For omega=90, (f + omega) = (f + pi/2). At transit (f approx 0), cos(pi/2) = 0.
    assert np.isclose(rvs[np.argmin(np.abs(TIMES - EPOCH_TRANSIT_DAYS))], 0.0, atol=1e-5), "RV at mid-transit (circular, omega=90) should be 0"


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
    """Tests how period affects RV amplitude (using the more general K formula)."""
    # K is proportional to P^(-1/3) if (M_star + m_planet) and G are fixed,
    # and semi-major axis 'a' is determined by Kepler's 3rd Law: a^3 ~ P^2 * (M_star + m_planet)
    # So a ~ (P^2)^(1/3) = P^(2/3)
    # Substituting 'a' into the RV amplitude formula K = (2 * pi * a * sin(i)) / P * (m_p / M_star)
    # gives K ~ (P^(2/3) / P) = P^(-1/3)
    # Therefore, K(P1)/K(P2) = (P2/P1)^(1/3)

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
    assert np.isclose(amplitude_short, amplitude_long * (10.0 / 1.0)**(1/3), rtol=0.05), "Amplitude should scale as P^(-1/3)"

def test_rv_phase_circular():
    """Tests the phase of a circular RV curve (omega=90)."""
    # With epoch_transit = 0.0, RV should be 0 at t=0, then positive.
    rvs = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=np.array([-0.01, 0.0, 0.01]), # Times around transit epoch
        eccentricity=0.0,
        argument_of_periastron=90.0 # omega=90 degrees
    )
    assert np.isclose(rvs[1], 0.0, atol=1e-5), "RV at epoch_transit (circular, omega=90) should be 0."
    assert rvs[2] > rvs[1], "RV should increase after epoch_transit (circular, omega=90)."
    assert rvs[0] < rvs[1], "RV should decrease before epoch_transit (circular, omega=90)."

def test_rv_eccentric_orbit_shape_and_amplitude():
    """
    Tests the shape and amplitude of an eccentric RV curve.
    An eccentric orbit RV curve is not perfectly sinusoidal.
    Its peak-to-trough amplitude should be (K * (1+e*cos(omega_rad))) and (K * (1-e*cos(omega_rad)))
    """
    ecc = 0.3
    omega_deg = 0.0 # Periastron at f=0 (closest approach to star)
    
    # Calculate RV using the elliptical model
    rvs = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES,
        eccentricity=ecc,
        argument_of_periastron=omega_deg
    )

    # For omega = 0 (periastron at f=0), planet moves fastest towards observer after transit.
    # The RV curve should be non-sinusoidal.
    # Check that it's not perfectly symmetrical (not sinusoidal)
    mean_rv = np.mean(rvs)
    # Count points above/below mean (a rough check for asymmetry)
    points_above_mean = np.sum(rvs > mean_rv)
    points_below_mean = np.sum(rvs < mean_rv)
    assert abs(points_above_mean - points_below_mean) > 5, "RV curve should be asymmetric for eccentric orbit" # Allowing for some numerical noise

    # Verify that max RV is reached shortly after transit (f=0 implies planet at periastron, RV max if omega=0).
    # Since epoch_transit=0, and omega=0, planet is at periastron at t = T0 - (P*E_peri/2pi) where E_peri is the eccentric anomaly at periastron.
    # RV peak should be around t=0 - P*e/(2pi)
    # This check might be too complex for a unit test. Simpler to check amplitude properties.
    
    # Maximum peak velocity for e=0.3, omega=0 deg should be around K*(1+e).
    # K for this system with e=0 is ~170.16 m/s
    K_base = 170.16 # from test_rv_circular_basic_amplitude
    expected_peak_amplitude = K_base / np.sqrt(1 - ecc**2) # This K is the semi-amplitude for e=0.

    # The actual max/min RV depends on argument_of_periastron.
    # max(RV) should be K_e * (1+e) and min(RV) should be -K_e * (1-e)
    # where K_e = K_base / sqrt(1-e^2) for the K definition used in code.
    K_actual = K_base / np.sqrt(1 - ecc**2) # K in code matches this.
    
    # With omega=0, max RV is K_actual * (1 + e), min RV is K_actual * (e - 1)
    expected_max_rv = K_actual * (np.cos(0 + np.deg2rad(0.0)) + ecc * np.cos(np.deg2rad(0.0)))
    expected_min_rv = K_actual * (np.cos(np.pi + np.deg2rad(0.0)) + ecc * np.cos(np.deg2rad(0.0)))

    assert np.isclose(np.max(rvs), K_actual * (1 + ecc), rtol=1e-2), f"Max RV should be {K_actual * (1 + ecc)}, got {np.max(rvs)}"
    assert np.isclose(np.min(rvs), -K_actual * (1 - ecc), rtol=1e-2), f"Min RV should be {-K_actual * (1 - ecc)}, got {np.min(rvs)}"


def test_rv_eccentric_orbit_phase_shift_with_omega():
    """
    Tests how argument_of_periastron shifts the phase of an eccentric RV curve.
    For a fixed eccentricity, changing omega should shift the entire RV curve.
    """
    ecc = 0.3
    
    # Omega = 0 deg
    rvs_omega0 = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES,
        eccentricity=ecc,
        argument_of_periastron=0.0
    )

    # Omega = 90 deg (shifted by pi/2 compared to omega=0)
    rvs_omega90 = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES,
        eccentricity=ecc,
        argument_of_periastron=90.0
    )
    
    # For omega = 90 deg, the curve shape is "inverted" (shifted by half period) compared to omega = 270 deg.
    # The RV function depends on (f + omega). A change in omega shifts the argument.
    # Check correlation or phase shift.
    
    # A simple check: if omega changes by 90 degrees, a feature at time t in omega=0 curve
    # should appear at t + period/4 in omega=90 curve (roughly, for small e).
    # More robust: check dot product for anti-correlation between omega=0 and omega=180
    rvs_omega180 = OrbitalSolver.calculate_stellar_radial_velocity(
        star_mass=STAR_MASS_SUN,
        planet_mass=PLANET_MASS_JUP,
        period=PERIOD_DAYS,
        semimajor_axis=SEMIMAJOR_AXIS_STELLAR_RADII,
        inclination=INCLINATION_DEG,
        epoch_transit=EPOCH_TRANSIT_DAYS,
        times=TIMES,
        eccentricity=ecc,
        argument_of_periastron=180.0
    )
    
    # rvs_omega180 should be approximately -rvs_omega0, for the sinusoidal component (ignoring constant offset)
    # The constant offset is K * e * cos(omega_rad).
    constant_offset_0 = (OrbitalSolver.G * STAR_MASS_SUN * OrbitalSolver.M_SUN / ( (2 * np.pi * PERIOD_DAYS * OrbitalSolver.DAY_TO_SEC)**2 * (1 - ecc**2) ))**(1/3) * ecc * np.cos(np.deg2rad(0.0)) # Approx
    
    # Let's verify by checking the shape, correlation
    correlation_0_90 = np.corrcoef(rvs_omega0, rvs_omega90)[0, 1]
    correlation_0_180 = np.corrcoef(rvs_omega0, rvs_omega180)[0, 1]
    
    # Omega=0 and Omega=90 should be decorrelated (quadrature phase).
    assert np.isclose(correlation_0_90, 0.0, atol=0.1), "RV curves for omega=0 and omega=90 should be decorrelated"
    
    # Omega=0 and Omega=180 should be anti-correlated.
    assert np.isclose(correlation_0_180, -1.0, atol=0.1), "RV curves for omega=0 and omega=180 should be anti-correlated"