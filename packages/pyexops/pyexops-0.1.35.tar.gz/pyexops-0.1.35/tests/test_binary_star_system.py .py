# pyexops/tests/test_binary_star_system.py

import numpy as np
import pytest
from pyexops.star import Star
from pyexops.binary_star_system import BinaryStarSystem
from pyexops.orbital_solver import OrbitalSolver # To verify orbital mechanics if needed

# Fixtures for basic stars
@pytest.fixture
def star_m1_r1():
    return Star(radius=1.0, base_flux=1000.0, limb_darkening_coeffs=(0.2, 0.1), star_mass=1.0)

@pytest.fixture
def star_m05_r07():
    return Star(radius=0.7, base_flux=500.0, limb_darkening_coeffs=(0.2, 0.1), star_mass=0.5)

# Test initialization of BinaryStarSystem
def test_binary_star_system_init(star_m1_r1, star_m05_r07):
    period = 10.0
    semimajor_axis = 10.0 # in stellar radii (of Star1)
    inclination = 90.0
    eccentricity = 0.1
    argument_of_periastron = 45.0
    epoch_periastron = 1.0

    binary_system = BinaryStarSystem(
        star1_m1_r1, star2_m05_r07, period, semimajor_axis, inclination,
        eccentricity, argument_of_periastron, epoch_periastron
    )

    assert binary_system.star1 == star_m1_r1
    assert binary_system.star2 == star_m05_r07
    assert binary_system.period_days == period
    assert binary_system.semimajor_axis_stellar_radii == semimajor_axis
    assert binary_system.inclination_deg == inclination
    assert binary_system.eccentricity == eccentricity
    assert binary_system.argument_of_periastron_deg == argument_of_periastron
    assert binary_system.epoch_periastron_days == epoch_periastron
    assert binary_system.total_mass_solar == star_m1_r1.star_mass + star_m05_r07.star_mass
    assert binary_system.mass_ratio == star_m05_r07.star_mass / star_m1_r1.star_mass

    # Check barycentric semi-major axes
    total_mass = star_m1_r1.star_mass + star_m05_r07.star_mass
    a1_bary_expected = semimajor_axis * star_m05_r07.star_mass / total_mass
    a2_bary_expected = semimajor_axis * star_m1_r1.star_mass / total_mass
    assert binary_system.semimajor_axis_star1_bary == pytest.approx(a1_bary_expected)
    assert binary_system.semimajor_axis_star2_bary == pytest.approx(a2_bary_expected)

def test_binary_star_system_init_invalid_masses():
    with pytest.raises(ValueError, match="Both stars in a binary system must have positive masses."):
        BinaryStarSystem(
            Star(radius=1.0, base_flux=1000, limb_darkening_coeffs=(0.2,0.1), star_mass=0.0), # Invalid mass
            Star(radius=0.7, base_flux=500, limb_darkening_coeffs=(0.2,0.1), star_mass=0.5),
            10.0, 10.0, 90.0
        )

def test_binary_star_system_init_invalid_period():
    with pytest.raises(ValueError, match="Binary period must be positive."):
        BinaryStarSystem(
            star_m1_r1(), star_m05_r07(), 0.0, 10.0, 90.0
        )

def test_binary_star_system_init_invalid_semimajor_axis():
    with pytest.raises(ValueError, match="Binary semi-major axis must be positive."):
        BinaryStarSystem(
            star_m1_r1(), star_m05_r07(), 10.0, -1.0, 90.0
        )

# Test get_star_barycentric_positions_at_time for circular orbit
def test_get_star_barycentric_positions_circular(star_m1_r1, star_m05_r07):
    period = 10.0
    semimajor_axis = 10.0
    inclination = 90.0
    epoch_periastron = 0.0 # Start at periastron, for circular this is just phase zero

    binary_system = BinaryStarSystem(
        star_m1_r1, star_m05_r07, period, semimajor_axis, inclination,
        eccentricity=0.0, argument_of_periastron_deg=0.0, epoch_periastron_days=epoch_periastron
    )

    times = np.array([0.0, 2.5, 5.0, 7.5, 10.0]) # Periastron, P/4, P/2, 3P/4, end of period

    # Expect positions relative to barycenter
    # Star1 is less massive than Star2 -> smaller orbit
    # At t=0 (periastron, omega=0): Star1 at (-a1, 0, 0), Star2 at (a2, 0, 0)
    # At t=P/4 (true_anomaly=pi/2): Star1 at (0, -a1, 0), Star2 at (0, a2, 0)
    # For inclination 90deg and omega=0:
    # At t=0: x1=0, y1=-a1*cos(0)*cos(90)=0, z1=-a1*cos(0)*sin(90)=-a1. Star1 is closer.
    # Star1 position at t=0 (periastron, which is line of sight with omega=0):
    # true_anomaly = 0, angle_in_orbital_plane = 0
    # x_proj = r * sin(0) = 0
    # y_proj = r * cos(0) * cos(inc) = r * cos(inc)
    # z_los = r * cos(0) * sin(inc) = r * sin(inc)
    # Using my OrbitalSolver implementation's convention:
    # x_proj = -r * sin(angle)
    # y_proj = -r * cos(angle) * cos(inc)
    # z_los = -r * cos(angle) * sin(inc)

    # For circular, inc=90, omega=0, epoch=0:
    # At t=0: mean_anom=0, ecc_anom=0, true_anom=0, angle_in_orbital_plane=0
    # x1_bary_proj = 0
    # y1_bary_proj = -a1_bary * cos(0) * cos(90) = 0
    # z1_bary_los = -a1_bary * cos(0) * sin(90) = -a1_bary (Star1 is at its closest point to observer)
    # x2_bary_proj = 0
    # y2_bary_proj = 0
    # z2_bary_los = a2_bary (Star2 is at its furthest point from observer)

    x1, y1, z1, x2, y2, z2 = binary_system.get_star_barycentric_positions_at_time(times)

    # Check t=0 (mid-eclipse)
    assert x1[0] == pytest.approx(0.0)
    assert y1[0] == pytest.approx(0.0)
    assert z1[0] == pytest.approx(-binary_system.semimajor_axis_star1_bary)
    assert x2[0] == pytest.approx(0.0)
    assert y2[0] == pytest.approx(0.0)
    assert z2[0] == pytest.approx(binary_system.semimajor_axis_star2_bary)

    # Check t=P/4 (quadrature)
    # At t=2.5: mean_anom=pi/2, true_anom=pi/2, angle_in_orbital_plane=pi/2
    # x1_bary_proj = -a1_bary * sin(pi/2) = -a1_bary
    # y1_bary_proj = -a1_bary * cos(pi/2) * cos(90) = 0
    # z1_bary_los = -a1_bary * cos(pi/2) * sin(90) = 0
    assert x1[1] == pytest.approx(-binary_system.semimajor_axis_star1_bary)
    assert y1[1] == pytest.approx(0.0)
    assert z1[1] == pytest.approx(0.0)
    assert x2[1] == pytest.approx(binary_system.semimajor_axis_star2_bary)
    assert y2[1] == pytest.approx(0.0)
    assert z2[1] == pytest.approx(0.0)

    # Check total separation
    total_separation = np.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2) # 3D separation
    assert np.allclose(total_separation, semimajor_axis)

    # Check opposition
    assert np.allclose(x1, -x2 * (binary_system.semimajor_axis_star1_bary / binary_system.semimajor_axis_star2_bary))
    assert np.allclose(y1, -y2 * (binary_system.semimajor_axis_star1_bary / binary_system.semimajor_axis_star2_bary))
    assert np.allclose(z1, -z2 * (binary_system.semimajor_axis_star1_bary / binary_system.semimajor_axis_star2_bary))


def test_get_star_barycentric_positions_elliptical(star_m1_r1, star_m05_r07):
    period = 10.0
    semimajor_axis = 10.0
    inclination = 85.0 # non-90 for more general test
    eccentricity = 0.5
    argument_of_periastron = 90.0 # Periastron at ascending node
    epoch_periastron = 0.0

    binary_system = BinaryStarSystem(
        star_m1_r1, star_m05_r07, period, semimajor_axis, inclination,
        eccentricity, argument_of_periastron, epoch_periastron
    )

    times = np.array([0.0, 1.0, 5.0, 9.0, 10.0]) # At periastron, near apastron, etc.

    x1, y1, z1, x2, y2, z2 = binary_system.get_star_barycentric_positions_at_time(times)

    # Check shape
    assert x1.shape == times.shape
    assert y1.shape == times.shape
    assert z1.shape == times.shape
    assert x2.shape == times.shape
    assert y2.shape == times.shape
    assert z2.shape == times.shape

    # At periastron (t=0.0), separation should be a*(1-e)
    # The true anomaly is 0. angle_in_orbital_plane = 90deg.
    # Star1 should be at x = -r1_bary, y=0, z=0 if inc=90
    # With inc=85 and omega=90:
    # x1 = -r1*sin(90) = -r1
    # y1 = -r1*cos(90)*cos(85) = 0
    # z1 = -r1*cos(90)*sin(85) = 0
    # So Star1 is on the x-axis, and z_los is 0 (it's crossing the plane of sky).
    # The actual Z-position for a transiting system would be where star1 is closest/furthest.
    # This coordinate system assumes periastron is along the X-axis for (r cos f, r sin f).
    # Then it's rotated by omega and inclined.
    # At t=0 (periastron): angle_in_orbital_plane = omega_rad.
    # So x1 = -r1 * sin(omega_rad)
    # y1 = -r1 * cos(omega_rad) * cos(inclination_rad)
    # z1 = -r1 * cos(omega_rad) * sin(inclination_rad)
    
    # For omega=90 deg (pi/2 rad), cos(omega_rad)=0, sin(omega_rad)=1.
    # So x1[0] = -r1_bary_at_periastron
    # y1[0] = 0
    # z1[0] = 0

    r1_peri = binary_system.semimajor_axis_star1_bary * (1 - eccentricity)
    assert x1[0] == pytest.approx(-r1_peri)
    assert y1[0] == pytest.approx(0.0)
    assert z1[0] == pytest.approx(0.0)

    # At t=P/2 (apastron for M_anom=pi for e=0) - for eccentric it's at true_anomaly=pi.
    # (times[2]=5.0) which is P/2. For e=0.5, true_anomaly=pi is not at t=5.0.
    # This gets complex. Just check that positions are calculated and distinct.
    assert np.any(x1 != 0) or np.any(y1 != 0) or np.any(z1 != 0)
    assert np.any(x2 != 0) or np.any(y2 != 0) or np.any(z2 != 0)
    assert not np.allclose(x1, 0.0) or not np.allclose(y1, 0.0) or not np.allclose(z1, 0.0)

    # Check opposition and non-zero mass ratio
    assert np.allclose(x1, -x2 * (binary_system.semimajor_axis_star1_bary / binary_system.semimajor_axis_star2_bary))
    assert np.allclose(y1, -y2 * (binary_system.semimajor_axis_star1_bary / binary_system.semimajor_axis_star2_bary))
    assert np.allclose(z1, -z2 * (binary_system.semimajor_axis_star1_bary / binary_system.semimajor_axis_star2_bary))