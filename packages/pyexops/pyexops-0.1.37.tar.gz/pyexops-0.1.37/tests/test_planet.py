# pyexops/tests/test_planet.py

import numpy as np
import pytest
from pyexops import Planet, Atmosphere # Import Atmosphere for type hinting
from pyexops.orbital_solver import OrbitalSolver # Needed for internal calculation logic

# Helper function for a simple Planet object
@pytest.fixture
def basic_planet():
    return Planet(radius=0.1, period=10.0, semimajor_axis=10.0,
                  inclination=90.0, epoch_transit=0.0, planet_mass=1.0)

# Helper for an atmosphere object
@pytest.fixture
def test_atmosphere(basic_planet):
    return Atmosphere(basic_planet.radius, [(400, basic_planet.radius), (500, basic_planet.radius * 1.02)])

# Test Planet initialization (existing tests should ensure this works)
def test_planet_init(basic_planet):
    assert basic_planet.radius == 0.1
    assert basic_planet.period == 10.0
    assert basic_planet.semimajor_axis == 10.0
    assert basic_planet.inclination_rad == np.deg2rad(90.0)
    assert basic_planet.epoch_transit == 0.0
    assert basic_planet.planet_mass == 1.0
    assert basic_planet.eccentricity == 0.0
    assert basic_planet.argument_of_periastron_rad == np.deg2rad(90.0)
    assert basic_planet.albedo == 0.5
    assert basic_planet.atmosphere is None
    assert basic_planet.host_star_index == 0 # NEW: Default value

def test_planet_init_with_atmosphere(basic_planet, test_atmosphere):
    planet = Planet(radius=0.1, period=10.0, semimajor_axis=10.0,
                    inclination=90.0, epoch_transit=0.0, planet_mass=1.0,
                    atmosphere=test_atmosphere)
    assert planet.atmosphere is test_atmosphere

def test_planet_init_atmosphere_radius_mismatch():
    with pytest.raises(ValueError, match="Atmosphere's solid radius must match Planet's radius."):
        Planet(radius=0.1, period=10.0, semimajor_axis=10.0,
               inclination=90.0, epoch_transit=0.0, planet_mass=1.0,
               atmosphere=Atmosphere(0.2, [])) # Mismatched radius

# Test get_position_at_time
def test_get_position_at_time_circular(basic_planet):
    time_transit = basic_planet.epoch_transit
    time_quarter_phase = time_transit + basic_planet.period / 4
    time_half_phase = time_transit + basic_planet.period / 2

    # At transit (t=0): Planet should be at (0, -a*cos(i)) in sky plane, z=0 if i=90
    # Our get_position_at_time logic: x = a * sin(phase), y = z_orbital * cos(i) = a * cos(phase) * cos(i)
    # At t=0, phase=0. So x_planet=0, y_planet = a*cos(i). For i=90, y_planet=0.
    # z_planet_bary = -a * cos(phase) * sin(i). For i=90, z_planet_bary = -a.
    # This means at t=0, the planet is at (0,0) in the sky plane and towards the observer.
    x, y, z = basic_planet.get_position_at_time(time_transit)
    assert np.isclose(x, 0.0)
    assert np.isclose(y, 0.0)
    assert np.isclose(z, -basic_planet.semimajor_axis)

    # At quarter phase (t=P/4): Planet should be at (a, 0) if i=90, z=0
    x, y, z = basic_planet.get_position_at_time(time_quarter_phase)
    assert np.isclose(x, basic_planet.semimajor_axis)
    assert np.isclose(y, 0.0)
    assert np.isclose(z, 0.0)

    # At half phase (t=P/2): Planet should be at (0,0) in sky plane and behind the observer
    x, y, z = basic_planet.get_position_at_time(time_half_phase)
    assert np.isclose(x, 0.0)
    assert np.isclose(y, 0.0)
    assert np.isclose(z, basic_planet.semimajor_axis)

def test_get_position_at_time_elliptical():
    planet = Planet(radius=0.1, period=10.0, semimajor_axis=10.0,
                    inclination=85.0, epoch_transit=0.0, planet_mass=1.0,
                    eccentricity=0.5, argument_of_periastron=0.0) # Periastron at f=0

    # At t=0 (epoch_transit, M=0, E=0, f=0):
    # This means planet is at periastron and true anomaly is 0.
    # argument_of_periastron=0 means periastron is along the observer's line of sight
    # so planet is at its closest point to star in 3D orbit.
    # x_rel_host = r * sin(0) = 0
    # y_rel_host = -r * cos(0) * cos(inc) = -r * cos(inc)
    # z_rel_host = -r * cos(0) * sin(inc) = -r * sin(inc)
    # r = a * (1-e)
    r_at_peri = planet.semimajor_axis * (1 - planet.eccentricity)
    
    x, y, z = planet.get_position_at_time(0.0)
    assert np.isclose(x, 0.0)
    assert np.isclose(y, -r_at_peri * np.cos(np.deg2rad(planet.inclination_rad)))
    assert np.isclose(z, -r_at_peri * np.sin(np.deg2rad(planet.inclination_rad)))

    # Check that positions are different at different times for elliptical
    x_t0, y_t0, z_t0 = planet.get_position_at_time(0.0)
    x_t1, y_t1, z_t1 = planet.get_position_at_time(1.0)
    assert not np.isclose(x_t0, x_t1) or not np.isclose(y_t0, y_t1) or not np.isclose(z_t0, z_t1)

# NEW: Test get_position_at_time with host_star_current_x/y_bary
def test_get_position_at_time_with_barycentric_offset():
    planet = Planet(radius=0.1, period=10.0, semimajor_axis=10.0,
                  inclination=90.0, epoch_transit=0.0, planet_mass=1.0)
    
    # Simulate host star at (5, -3) relative to system barycenter
    host_star_x_offset = 5.0
    host_star_y_offset = -3.0

    # Planet at transit (t=0), expected to be at (0,0) relative to host
    x_rel_host, y_rel_host, z_rel_host = planet.get_position_at_time(0.0, 0.0, 0.0) # Get relative position

    x_planet_bary, y_planet_bary, z_planet_bary = planet.get_position_at_time(
        0.0, host_star_x_offset, host_star_y_offset
    )
    
    assert np.isclose(x_planet_bary, x_rel_host + host_star_x_offset)
    assert np.isclose(y_planet_bary, y_rel_host + host_star_y_offset)
    assert np.isclose(z_planet_bary, z_rel_host) # Z is still relative to host, as host star's Z isn't passed here for planet's depth

# NEW: Test host_star_index in Planet init
def test_planet_init_host_star_index():
    planet_star1 = Planet(radius=0.1, period=10.0, semimajor_axis=10.0, inclination=90.0, epoch_transit=0.0, planet_mass=1.0, host_star_index=0)
    planet_star2 = Planet(radius=0.1, period=10.0, semimajor_axis=10.0, inclination=90.0, epoch_transit=0.0, planet_mass=1.0, host_star_index=1)
    
    assert planet_star1.host_star_index == 0
    assert planet_star2.host_star_index == 1