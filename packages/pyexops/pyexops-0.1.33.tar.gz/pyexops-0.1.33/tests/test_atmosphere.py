# pyexops/tests/test_atmosphere.py

import pytest
import numpy as np
from pyexops import Atmosphere

def test_atmosphere_initialization_empty_data():
    """Test Atmosphere initialization with empty transmission_model_data."""
    solid_radius = 0.1
    atm = Atmosphere(solid_radius, [])
    assert atm.planet_solid_radius_stellar_radii == solid_radius
    assert atm.wavelengths_nm.size == 0
    assert atm.effective_radii_at_wavelengths.size == 0

def test_atmosphere_initialization_single_data_point():
    """Test Atmosphere initialization with a single data point."""
    solid_radius = 0.1
    transmission_data = [(500.0, 0.11)]
    atm = Atmosphere(solid_radius, transmission_data)
    assert atm.planet_solid_radius_stellar_radii == solid_radius
    assert np.array_equal(atm.wavelengths_nm, np.array([500.0]))
    assert np.array_equal(atm.effective_radii_at_wavelengths, np.array([0.11]))

def test_atmosphere_initialization_multiple_data_points():
    """Test Atmosphere initialization with multiple data points."""
    solid_radius = 0.1
    transmission_data = [(500.0, 0.11), (600.0, 0.12), (700.0, 0.11)]
    atm = Atmosphere(solid_radius, transmission_data)
    assert atm.planet_solid_radius_stellar_radii == solid_radius
    assert np.array_equal(atm.wavelengths_nm, np.array([500.0, 600.0, 700.0]))
    assert np.array_equal(atm.effective_radii_at_wavelengths, np.array([0.11, 0.12, 0.11]))

def test_atmosphere_initialization_unsorted_data_raises_error():
    """Test that unsorted transmission_model_data raises a ValueError."""
    solid_radius = 0.1
    transmission_data = [(600.0, 0.12), (500.0, 0.11)] # Unsorted
    with pytest.raises(ValueError, match="transmission_model_data must be sorted by wavelength."):
        Atmosphere(solid_radius, transmission_data)

def test_atmosphere_initialization_invalid_data_type_raises_error():
    """Test that invalid data type in transmission_model_data raises a ValueError."""
    solid_radius = 0.1
    transmission_data = [(500.0, 'invalid'), (600.0, 0.12)] # Invalid value type
    with pytest.raises(ValueError, match="transmission_model_data must be a list of \(float, float\) tuples."):
        Atmosphere(solid_radius, transmission_data)

def test_get_effective_radius_direct_match():
    """Test get_effective_radius when wavelength directly matches a data point."""
    solid_radius = 0.1
    transmission_data = [(500.0, 0.11), (600.0, 0.12), (700.0, 0.11)]
    atm = Atmosphere(solid_radius, transmission_data)
    assert np.isclose(atm.get_effective_radius(600.0), 0.12)

def test_get_effective_radius_interpolation():
    """Test get_effective_radius with linear interpolation."""
    solid_radius = 0.1
    transmission_data = [(500.0, 0.11), (600.0, 0.12), (700.0, 0.11)]
    atm = Atmosphere(solid_radius, transmission_data)
    # Wavelength 550.0 nm is halfway between 500.0 and 600.0, so radius should be halfway
    assert np.isclose(atm.get_effective_radius(550.0), 0.115)
    # Wavelength 650.0 nm is halfway between 600.0 and 700.0
    assert np.isclose(atm.get_effective_radius(650.0), 0.115)

def test_get_effective_radius_extrapolation_left():
    """Test get_effective_radius with extrapolation below the minimum wavelength."""
    solid_radius = 0.1
    transmission_data = [(500.0, 0.11), (600.0, 0.12)]
    atm = Atmosphere(solid_radius, transmission_data)
    # Should extrapolate to the value at the minimum wavelength (0.11)
    assert np.isclose(atm.get_effective_radius(450.0), 0.11)

def test_get_effective_radius_extrapolation_right():
    """Test get_effective_radius with extrapolation above the maximum wavelength."""
    solid_radius = 0.1
    transmission_data = [(500.0, 0.11), (600.0, 0.12)]
    atm = Atmosphere(solid_radius, transmission_data)
    # Should extrapolate to the value at the maximum wavelength (0.12)
    assert np.isclose(atm.get_effective_radius(650.0), 0.12)

def test_get_effective_radius_no_data_returns_solid_radius():
    """Test get_effective_radius when no transmission_model_data is provided."""
    solid_radius = 0.1
    atm = Atmosphere(solid_radius, [])
    assert np.isclose(atm.get_effective_radius(550.0), solid_radius)