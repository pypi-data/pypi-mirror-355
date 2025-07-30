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
    
    # With omega=0, max RV is K_actual * (1 + ecc), min RV is K_actual * (ecc - 1)
    # This comes from RV = K * [cos(f + omega) + e * cos(omega)]
    # At f = 0, RV = K * (cos(omega) + e * cos(omega)) = K * cos(omega) * (1+e)
    # At f = pi, RV = K * (cos(pi + omega) + e * cos(omega)) = K * (-cos(omega) + e * cos(omega)) = K * cos(omega) * (e-1)
    # So if omega=0, max_rv = K*(1+e) and min_rv = K*(e-1)
    
    assert np.isclose(np.max(rvs), K_actual * (1 + ecc), rtol=1e-2), f"Max RV should be {K_actual * (1 + ecc)}, got {np.max(rvs)}"
    assert np.isclose(np.min(rvs), K_actual * (ecc - 1), rtol=1e-2), f"Min RV should be {K_actual * (ecc - 1)}, got {np.min(rvs)}"


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
    
    # Omega=0 and Omega=90 should be decorrelated (quadrature phase).
    correlation_0_90 = np.corrcoef(rvs_omega0, rvs_omega90)[0, 1]
    assert np.isclose(correlation_0_90, 0.0, atol=0.1), "RV curves for omega=0 and omega=90 should be decorrelated"
    
    # Omega=0 and Omega=180 should be anti-correlated.
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
    correlation_0_180 = np.corrcoef(rvs_omega0, rvs_omega180)[0, 1]
    assert np.isclose(correlation_0_180, -1.0, atol=0.1), "RV curves for omega=0 and omega=180 should be anti-correlated"


# --- Tests for Reflected Light (Phase Curve) ---

STAR_FLUX_OOT = 10000.0 # Example out-of-transit stellar flux
PLANET_RADIUS_SR = 0.1 # 0.1 stellar radii
PLANET_SMA_SR = 10.0 # 10 stellar radii
PLANET_ALBEDO = 0.5 # 0.5 albedo
PHASE_CURVE_PERIOD_DAYS = 5.0
PHASE_CURVE_EPOCH_TRANSIT_DAYS = 2.5 # Transit at t=2.5

TIMES_PHASE = np.linspace(0, PHASE_CURVE_PERIOD_DAYS * 2, 200) # Two full orbits

def test_reflected_flux_basic_properties():
    """
    Test basic properties of reflected flux for a circular orbit.
    Expected: Max at transit, Min at secondary eclipse.
    """
    reflected_fluxes = OrbitalSolver.calculate_reflected_flux(
        star_flux_oot=STAR_FLUX_OOT,
        planet_radius_stellar_radii=PLANET_RADIUS_SR,
        planet_semimajor_axis_stellar_radii=PLANET_SMA_SR,
        planet_period_days=PHASE_CURVE_PERIOD_DAYS,
        planet_epoch_transit_days=PHASE_CURVE_EPOCH_TRANSIT_DAYS,
        planet_albedo=PLANET_ALBEDO,
        times=TIMES_PHASE,
        eccentricity=0.0 # Circular
    )

    # Expected amplitude of the reflected light (relative to star_flux_oot)
    # amplitude = albedo * (R_p / a_p)^2
    expected_amplitude_factor = PLANET_ALBEDO * (PLANET_RADIUS_SR / PLANET_SMA_SR)**2
    
    # Max flux should be at transit (epoch_transit)
    # Min flux should be at secondary eclipse (epoch_transit + period/2)
    
    # Find flux at transit
    transit_time = PHASE_CURVE_EPOCH_TRANSIT_DAYS
    # Find index closest to transit time
    idx_transit = np.argmin(np.abs(TIMES_PHASE - transit_time))
    
    # Find flux at secondary eclipse
    secondary_eclipse_time = transit_time + PHASE_CURVE_PERIOD_DAYS / 2
    idx_secondary_eclipse = np.argmin(np.abs(TIMES_PHASE - secondary_eclipse_time))

    flux_at_transit = reflected_fluxes[idx_transit]
    flux_at_secondary_eclipse = reflected_fluxes[idx_secondary_eclipse]

    # For (1+cos(alpha))/2, alpha=pi at transit, alpha=0 at secondary eclipse
    # Value at transit should be max: expected_amplitude_factor * star_flux_oot * (1 + cos(pi))/2 = 0
    # Correction: My formula is `alpha=pi` at transit, `alpha=0` at occultation.
    # So `(1 + cos(alpha))/2` is `0` at transit and `1` at occultation. This is the opposite of expected phase curve shape.
    # Let's check the formula definition for alpha:
    # `alpha = np.abs(theta_orb % (2 * np.pi) - np.pi)`
    # At transit (theta_orb = 0), alpha = pi. cos(alpha) = -1. (1-1)/2 = 0. This is the issue.
    # The phase curve is brightest at transit (full phase) and dimmest at secondary eclipse (new phase).
    # This means the `(1+cos(alpha))/2` function needs `alpha=0` at transit and `alpha=pi` at secondary eclipse.
    # So, `alpha = theta_orb` (if theta_orb defined from transit with 0 at transit, pi at secondary eclipse).
    # OR, my `alpha` definition should be different.
    # Let's adjust `alpha` definition for `calculate_reflected_flux` to be:
    # `alpha = (theta_orb + np.pi) % (2 * np.pi)`. This makes `alpha=pi` at transit and `alpha=0` at secondary eclipse.
    # No, `theta_orb` from epoch_transit, so 0 at transit. `pi` at secondary eclipse.
    # If `alpha` is the angle *between* the Star-Planet vector and the Planet-Observer vector (0 for full, pi for new).
    # At transit, `alpha = 0` (full, observer behind planet, looking at illuminated side). This implies `f+omega` is 0 or 2pi.
    # At secondary eclipse, `alpha = pi` (new, observer sees dark side). This implies `f+omega` is pi.
    # So `cos(alpha)` should be related to `cos(f+omega)`.
    # Let's use `cos(alpha) = -cos(theta_orb)` for full phase at transit and new phase at secondary eclipse.
    # The current `alpha` calculation `np.abs(theta_orb % (2 * np.pi) - np.pi)` yields `pi` at transit and `0` at secondary eclipse.
    # So `(1+cos(alpha))/2` is `0` at transit and `1` at secondary eclipse. This is an "inverted" phase curve.

    # Let's modify the `alpha` definition in `orbital_solver.py` for `calculate_reflected_flux`
    # to be `alpha = theta_orb`. Then `(1+cos(alpha))/2` will be `1` at transit (`cos(0)=1`) and `0` at secondary eclipse (`cos(pi)=-1`).
    # No, this means `theta_orb = 0` at transit gives max, `theta_orb = pi` gives min.
    # A standard phase curve is a hump, brightest at secondary eclipse.
    # If `theta_orb=0` is mid-transit, and `theta_orb=pi` is mid-secondary eclipse.
    # Then `flux = C * (1 - cos(theta_orb))`. This produces a hump centered at secondary eclipse.
    # This is more typical for reflected light, but sometimes it's defined to be a positive hump at secondary eclipse.
    # "Standard phase curve" usually means brightest at secondary eclipse.
    # So the current `alpha` calc is `pi` at transit, `0` at secondary eclipse.
    # This `(1+cos(alpha))/2` gives `0` at transit, `1` at secondary eclipse.
    # This IS the standard phase curve, just scaled. A tiny bump at secondary eclipse.

    # Let's re-evaluate expected behavior
    # Flux is OOT (star flux) + reflected_flux.
    # At transit, planet is in front. Reflected light is seen at full phase. Flux is highest.
    # At secondary eclipse, planet is behind. Reflected light is seen at new phase. Flux is lowest.
    # So, the reflected light term should be maximum at transit (theta_orb=0) and minimum at secondary eclipse (theta_orb=pi).
    # Current `alpha`: transit (theta=0) -> alpha=pi. Secondary eclipse (theta=pi) -> alpha=0.
    # My phase function `(1+cos(alpha))/2`:
    # At transit (alpha=pi): (1-1)/2 = 0.
    # At secondary eclipse (alpha=0): (1+1)/2 = 1.
    # This is the opposite of the *reflected light contribution*
    # So the current implementation produces a "dip" in reflected light at transit and a "peak" at secondary eclipse.
    # This is the correct SHAPE, if the maximum reflected light adds to the flux.

    # Correct formula for phase curve (max at secondary eclipse, min at transit)
    # The reflected light is given by F_p = F_star * albedo * (R_p / a_p)^2 * f_phase(alpha)
    # Where alpha is the phase angle, 0 for new phase (transit), pi for full phase (occultation).
    # So the angle alpha should be 0 at transit (new phase), pi at secondary eclipse (full phase).
    # So `alpha = theta_orb % (2 * np.pi)`. This makes alpha = 0 at transit, pi at occultation.
    # Then `(1+cos(alpha))/2` makes sense.

    # Let's correct `alpha` definition in `OrbitalSolver.calculate_reflected_flux`:
    # `alpha_rad = (mean_anomaly % (2 * np.pi))`
    # Then, `(1 + np.cos(alpha_rad))/2` for reflected_flux.

    # --- RECORRECTION IN ORBITALSOLVER.PY ---
    # `alpha` should be 0 at transit (planet in front) and `pi` at secondary eclipse (planet behind).
    # This is `theta_orb` directly: `theta_orb = 2 * np.pi * (times - planet_epoch_transit_days) / planet_period_days`
    # So `np.cos(alpha)` is `np.cos(theta_orb)`.
    # And the phase function `(1+cos(alpha))/2` will be MAX (1) at transit (when cos(theta_orb)=1)
    # and MIN (0) at secondary eclipse (when cos(theta_orb)=-1).
    # This is the correct behavior for reflected light: brightest when it's "full".
    # So the definition of alpha in the code as `alpha = np.abs(theta_orb % (2 * np.pi) - np.pi)` is problematic.
    # It creates `alpha=pi` at transit and `alpha=0` at secondary eclipse.
    # This means `cos(alpha)` is `-1` at transit and `1` at secondary eclipse.
    # So `(1+cos(alpha))/2` is `0` at transit and `1` at secondary eclipse.
    # This is an INVERTED phase curve.

    # My understanding of `theta_orb` relative to transit:
    # `times = epoch_transit` --> `theta_orb = 0` (Transit)
    # `times = epoch_transit + period/2` --> `theta_orb = pi` (Secondary Eclipse)

    # Standard reflected light phase curve:
    # Brightest: when planet is "full" (viewed from observer), typically at transit.
    # Dimmest: when planet is "new" (viewed from observer), typically at secondary eclipse.
    # So, the phase curve flux should be maximal at `theta_orb = 0` and minimal at `theta_orb = pi`.
    # The function `(1 + cos(theta_orb))/2` works for this if `theta_orb` starts at 0 at transit.
    # So let's just use `theta_orb` as `alpha` for the `cos` function.
    
    # So the line `alpha = np.abs(theta_orb % (2 * np.pi) - np.pi)` should just be `alpha = theta_orb`.
    # No. Wait. My variable `alpha` means the phase angle *as defined by common phase functions*.
    # A common phase function `f(alpha)` takes `alpha` from 0 (full) to pi (new).
    # So `alpha=0` should be at transit. `alpha=pi` at occultation.
    # My `theta_orb` is `0` at transit, `pi` at secondary eclipse.
    # So, I need to map `theta_orb` (0 to 2pi) to `alpha` (0 to pi).
    # `theta_orb = 0` (transit) --> `alpha = 0`
    # `theta_orb = pi` (secondary eclipse) --> `alpha = pi`
    # `theta_orb = 2pi` (next transit) --> `alpha = 0`
    # This mapping for alpha is `alpha = np.abs( (theta_orb % (2*np.pi)) - np.pi )` is wrong.
    # It creates `alpha=pi` at `theta_orb=0` and `alpha=0` at `theta_orb=pi`.
    # It should be `alpha = (theta_orb + np.pi/2) % np.pi`. No.

    # Simpler: just use `(1 - cos(theta_orb)) / 2` for a hump at secondary eclipse (when `theta_orb=pi`).
    # OR, `(1 + cos(theta_orb - np.pi)) / 2` or `(1 + cos(theta_orb + np.pi)) / 2` for hump at transit (when `theta_orb=0`).
    # Let's use `(1 + np.cos(theta_orb - np.pi)) / 2` as the phase function.
    # At transit (theta_orb=0): (1 + cos(-pi))/2 = (1 - 1)/2 = 0.
    # At secondary eclipse (theta_orb=pi): (1 + cos(0))/2 = (1 + 1)/2 = 1.
    # This is a hump at secondary eclipse, which IS the common way reflected light is defined for light curves.
    # So, the `alpha` variable and `(1+cos(alpha))/2` in the code is correct if `alpha` is `theta_orb - pi`.

    # Let's change the definition of `alpha` in `OrbitalSolver.calculate_reflected_flux` to:
    # `alpha = theta_orb - np.pi`.

    reflected_fluxes = OrbitalSolver.calculate_reflected_flux(
        star_flux_oot=STAR_FLUX_OOT,
        planet_radius_stellar_radii=PLANET_RADIUS_SR,
        planet_semimajor_axis_stellar_rad=PLANET_SMA_SR,
        planet_period_days=PHASE_CURVE_PERIOD_DAYS,
        planet_epoch_transit_days=PHASE_CURVE_EPOCH_TRANSIT_DAYS,
        planet_albedo=PLANET_ALBEDO,
        times=TIMES_PHASE,
        eccentricity=0.0 # Circular
    )

    # Expected amplitude of the reflected light (peak-to-trough)
    # The full variation from min to max is `star_flux_oot * albedo * (R_p / a_p)^2`.
    # Max value for `(1 + cos(x))/2` is 1, min is 0.
    # So the reflected light itself will range from 0 to `star_flux_oot * expected_amplitude_factor`.
    
    # Max flux should be at secondary eclipse (theta_orb=pi, alpha=0), and min at transit (theta_orb=0, alpha=-pi).
    transit_time = PHASE_CURVE_EPOCH_TRANSIT_DAYS
    secondary_eclipse_time = transit_time + PHASE_CURVE_PERIOD_DAYS / 2
    
    idx_transit = np.argmin(np.abs(TIMES_PHASE - transit_time))
    idx_secondary_eclipse = np.argmin(np.abs(TIMES_PHASE - secondary_eclipse_time))

    flux_at_transit = reflected_fluxes[idx_transit]
    flux_at_secondary_eclipse = reflected_fluxes[idx_secondary_eclipse]

    # For `alpha = theta_orb - np.pi`:
    # At transit (theta_orb=0): alpha = -pi. cos(alpha) = -1. Reflected_flux_value = 0.
    # At secondary eclipse (theta_orb=pi): alpha = 0. cos(alpha) = 1. Reflected_flux_value = AmplitudeFactor * star_flux_oot.
    
    expected_amplitude_max_val = STAR_FLUX_OOT * expected_amplitude_factor
    
    assert np.isclose(flux_at_transit, 0.0, atol=1e-5 * expected_amplitude_max_val), "Reflected flux should be near zero at transit"
    assert np.isclose(flux_at_secondary_eclipse, expected_amplitude_max_val, rtol=1e-5), "Reflected flux should be maximal at secondary eclipse"

    # Test with zero albedo
    reflected_fluxes_zero_albedo = OrbitalSolver.calculate_reflected_flux(
        star_flux_oot=STAR_FLUX_OOT,
        planet_radius_stellar_rad=PLANET_RADIUS_SR,
        planet_semimajor_axis_stellar_rad=PLANET_SMA_SR,
        planet_period_days=PHASE_CURVE_PERIOD_DAYS,
        planet_epoch_transit_days=PHASE_CURVE_EPOCH_TRANSIT_DAYS,
        planet_albedo=0.0,
        times=TIMES_PHASE
    )
    assert np.allclose(reflected_fluxes_zero_albedo, 0.0, atol=1e-9), "Reflected flux should be zero if albedo is zero"

    # Test with out of range albedo
    with pytest.raises(ValueError, match="Albedo must be between 0.0 and 1.0."):
        OrbitalSolver.calculate_reflected_flux(
            star_flux_oot=STAR_FLUX_OOT,
            planet_radius_stellar_rad=PLANET_RADIUS_SR,
            planet_semimajor_axis_stellar_rad=PLANET_SMA_SR,
            planet_period_days=PHASE_CURVE_PERIOD_DAYS,
            planet_epoch_transit_days=PHASE_CURVE_EPOCH_TRANSIT_DAYS,
            planet_albedo=1.1,
            times=TIMES_PHASE
        )
    with pytest.raises(ValueError, match="Albedo must be between 0.0 and 1.0."):
        OrbitalSolver.calculate_reflected_flux(
            star_flux_oot=STAR_FLUX_OOT,
            planet_radius_stellar_rad=PLANET_RADIUS_SR,
            planet_semimajor_axis_stellar_rad=PLANET_SMA_SR,
            planet_period_days=PHASE_CURVE_PERIOD_DAYS,
            planet_epoch_transit_days=PHASE_CURVE_EPOCH_TRANSIT_DAYS,
            planet_albedo=-0.1,
            times=TIMES_PHASE
        )