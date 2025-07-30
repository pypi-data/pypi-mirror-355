# pyexops/tests/test_planet.py

import pytest
import numpy as np
from pyexops import Planet

@pytest.fixture
def basic_planet():
    # Radius is 0.1 stellar radii, Period 5 days, a=10 stellar radii, inclination=90 (edge-on), epoch=0
    return Planet(radius=0.1, period=5.0, semimajor_axis=10.0, inclination=90.0, epoch_transit=0.0)

def test_planet_initialization(basic_planet):
    assert basic_planet.radius == 0.1
    assert basic_planet.period == 5.0
    assert basic_planet.semimajor_axis == 10.0
    assert basic_planet.inclination_rad == pytest.approx(np.pi / 2)
    assert basic_planet.epoch_transit == 0.0

@pytest.mark.parametrize("time, expected_x, expected_y", [
    (0.0, 0.0, 0.0), # Mid-transit for edge-on at epoch
    (1.25, 10.0, 0.0), # Quarter period, x-axis
    (2.5, 0.0, 0.0), # Half period, back at center (but on far side)
    (3.75, -10.0, 0.0) # Three-quarter period, -x-axis
])
def test_planet_get_position_at_time_edge_on(basic_planet, time, expected_x, expected_y):
    # For edge-on (inclination=90), y should always be 0 (in stellar radii)
    x, y = basic_planet.get_position_at_time(time)
    assert x == pytest.approx(expected_x, abs=1e-9)
    assert y == pytest.approx(expected_y, abs=1e-9)

def test_planet_get_position_at_time_inclination():
    # Planet with 89 degrees inclination
    planet = Planet(radius=0.1, period=5.0, semimajor_axis=10.0, inclination=89.0, epoch_transit=0.0)
    # At mid-transit (t=0), x=0.0, y will be slightly off-center
    x, y = planet.get_position_at_time(0.0)
    assert x == pytest.approx(0.0, abs=1e-9)
    # y = a * cos(inclination)
    expected_y_at_transit = 10.0 * np.cos(np.deg2rad(89.0))
    assert y == pytest.approx(expected_y_at_transit, abs=1e-9)

    # At quarter period (t=1.25), x=10.0, y should be 0 because cos(phase)=0
    x_quarter, y_quarter = planet.get_position_at_time(1.25)
    assert x_quarter == pytest.approx(10.0, abs=1e-9)
    assert y_quarter == pytest.approx(0.0, abs=1e-9) # Because cos(phase) becomes 0 here