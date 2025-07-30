# pyexops/tests/test_star.py

import pytest
import numpy as np
from pyexops import Star, Spot

# Fixtures for common test objects
@pytest.fixture
def basic_star():
    return Star(radius=10.0, base_flux=100.0, limb_darkening_coeffs=(0.5, 0.2))

@pytest.fixture
def basic_spot():
    return Spot(center_x=0.0, center_y=0.0, radius_umbra=0.1, radius_penumbra=0.2, contrast_umbra=0.1, contrast_penumbra=0.5)

# Test cases for Spot class
def test_spot_flux_factor_umbra(basic_spot):
    # Point inside umbra
    assert basic_spot.get_flux_factor(0.0, 0.0) == 0.1
    assert basic_spot.get_flux_factor(0.05, 0.0) == 0.1

def test_spot_flux_factor_penumbra(basic_spot):
    # Point inside penumbra (linear interpolation)
    # Mid-penumbra: radius_umbra=0.1, radius_penumbra=0.2, contrast_umbra=0.1, contrast_penumbra=0.5
    # For r = (0.1+0.2)/2 = 0.15, factor should be (0.1+0.5)/2 = 0.3
    r_mid_penumbra = 0.15
    expected_factor = basic_spot.contrast_umbra + \
                      (1.0 - basic_spot.contrast_umbra) * \
                      (r_mid_penumbra - basic_spot.radius_umbra) / \
                      (basic_spot.radius_penumbra - basic_spot.radius_umbra)
    assert basic_spot.get_flux_factor(r_mid_penumbra, 0.0) == pytest.approx(expected_factor)

def test_spot_flux_factor_outside(basic_spot):
    # Point outside penumbra
    assert basic_spot.get_flux_factor(0.3, 0.0) == 1.0

def test_spot_flux_factor_umbra_eq_penumbra_radius():
    spot = Spot(0.0, 0.0, 0.1, 0.1, 0.1, 0.5)
    assert spot.get_flux_factor(0.05, 0.0) == 0.1 # Should be umbra contrast

# Test cases for Star class
def test_star_initialization(basic_star):
    assert basic_star.radius == 10.0
    assert basic_star.base_flux == 100.0
    assert basic_star.u1 == 0.5
    assert basic_star.u2 == 0.2
    assert basic_star.spots == []

def test_star_add_spot(basic_star, basic_spot):
    basic_star.add_spot(basic_spot)
    assert len(basic_star.spots) == 1
    assert basic_star.spots[0] == basic_spot

def test_star_get_pixel_flux_outside_disk(basic_star):
    # Pixel outside star disk (r_prime > 1.0)
    assert basic_star.get_pixel_flux(1.1, 0.0) == 0.0

def test_star_get_pixel_flux_center(basic_star):
    # Pixel at star center (r_prime = 0)
    # Limb darkening: 1 - u1*(1-1) - u2*(1-1)^2 = 1.0
    assert basic_star.get_pixel_flux(0.0, 0.0) == basic_star.base_flux

def test_star_get_pixel_flux_edge(basic_star):
    # Pixel at star edge (r_prime = 1.0)
    # mu = sqrt(1 - 1^2) = 0
    # Limb darkening: 1 - u1*(1-0) - u2*(1-0)^2 = 1 - u1 - u2
    expected_flux_factor = 1.0 - basic_star.u1 - basic_star.u2
    expected_flux = basic_star.base_flux * expected_flux_factor
    assert basic_star.get_pixel_flux(1.0, 0.0) == pytest.approx(expected_flux)

def test_star_get_pixel_flux_with_spot_occultation(basic_star):
    # Star with a central spot, test pixel at center
    central_spot = Spot(center_x=0.0, center_y=0.0, radius_umbra=0.1, radius_penumbra=0.2, contrast_umbra=0.1, contrast_penumbra=0.5)
    basic_star.add_spot(central_spot)
    
    # Pixel at center (0,0) is in umbra
    expected_flux = basic_star.base_flux * central_spot.contrast_umbra
    assert basic_star.get_pixel_flux(0.0, 0.0) == pytest.approx(expected_flux)

    # Pixel just outside penumbra (0.3, 0.0) should have normal limb-darkened flux
    # r_prime = 0.3, mu = sqrt(1 - 0.3^2) = sqrt(0.91)
    mu = np.sqrt(1.0 - 0.3**2)
    expected_flux_no_spot = basic_star.base_flux * (1.0 - basic_star.u1 * (1.0 - mu) - basic_star.u2 * (1.0 - mu)**2)
    assert basic_star.get_pixel_flux(0.3, 0.0) == pytest.approx(expected_flux_no_spot)