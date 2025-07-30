# pyexops/tests/test_astrometry.py

import numpy as np
import pytest
from pyexops.astrometry import Astrometry

# Helper to create a simple star image (Gaussian)
def create_gaussian_image(shape=(50, 50), center=(25, 25), sigma=2.0, amplitude=1000.0):
    """Creates a 2D Gaussian image."""
    y, x = np.mgrid[0:shape[0], 0:shape[1]]
    gaussian_2d = amplitude * np.exp(-((x - center[0])**2 + (y - center[1])**2) / (2 * sigma**2))
    return gaussian_2d

def test_estimate_shift_no_shift():
    """Test estimate_shift when there is no shift."""
    image_ref = create_gaussian_image()
    image_target = image_ref.copy()
    
    dy, dx = Astrometry.estimate_shift(image_ref, image_target)
    
    assert np.isclose(dy, 0.0, atol=0.01) # Allow for minor sub-pixel variations due to CoM
    assert np.isclose(dx, 0.0, atol=0.01)

def test_estimate_shift_integer_shift():
    """Test estimate_shift with a simple integer shift."""
    image_ref = create_gaussian_image()
    # Shift image_target by +2 pixels in y, -3 pixels in x
    image_target = np.roll(image_ref, shift=(2, -3), axis=(0, 1))
    
    dy, dx = Astrometry.estimate_shift(image_ref, image_target)
    
    # The estimated shift should be target_peak - ref_peak.
    # If ref_peak is at (25,25) and target_peak is at (27,22), shift is (2, -3)
    assert np.isclose(dy, 2.0, atol=0.01)
    assert np.isclose(dx, -3.0, atol=0.01)

def test_estimate_shift_subpixel_shift():
    """Test estimate_shift with a sub-pixel shift."""
    image_ref = create_gaussian_image()
    # Apply a known sub-pixel shift using scipy.ndimage.shift
    true_dy, true_dx = 0.5, -0.75
    image_target = Astrometry.apply_shift(image_ref, true_dy, true_dx, order=3)
    
    dy, dx = Astrometry.estimate_shift(image_ref, image_target)
    
    assert np.isclose(dy, true_dy, atol=0.05) # Allow some tolerance for CoM precision
    assert np.isclose(dx, true_dx, atol=0.05)

def test_estimate_shift_different_amplitudes():
    """Test estimate_shift when target image has different overall brightness."""
    image_ref = create_gaussian_image()
    image_target = create_gaussian_image(amplitude=500.0) # Half brightness
    
    dy, dx = Astrometry.estimate_shift(image_ref, image_target)
    
    assert np.isclose(dy, 0.0, atol=0.01)
    assert np.isclose(dx, 0.0, atol=0.01)

def test_estimate_shift_with_noise():
    """Test estimate_shift with some added noise."""
    image_ref = create_gaussian_image()
    image_target = Astrometry.apply_shift(image_ref, 1.2, 0.8, order=3)
    
    # Add Gaussian noise
    image_ref_noisy = image_ref + np.random.normal(0, 10, image_ref.shape)
    image_target_noisy = image_target + np.random.normal(0, 10, image_target.shape)
    
    dy, dx = Astrometry.estimate_shift(image_ref_noisy, image_target_noisy)
    
    assert np.isclose(dy, 1.2, atol=0.2) # Higher tolerance for noise
    assert np.isclose(dx, 0.8, atol=0.2)

def test_estimate_shift_empty_cutouts():
    """Test when cutouts are empty (e.g., star is near edge and search_box is too big)."""
    image_ref = create_gaussian_image(center=(2, 2)) # Star near corner
    image_target = image_ref.copy()
    
    # A small search box that might result in empty cutouts if not handled
    dy, dx = Astrometry.estimate_shift(image_ref, image_target, search_box_half_size=1) 
    
    assert np.isclose(dy, 0.0, atol=0.01)
    assert np.isclose(dx, 0.0, atol=0.01)

def test_apply_shift_integer_shift():
    """Test apply_shift with integer shifts."""
    image = np.zeros((10, 10))
    image[4, 4] = 100
    
    shifted_image = Astrometry.apply_shift(image, 1, 1, order=0) # Nearest neighbor
    
    assert shifted_image[5, 5] == 100
    assert np.sum(shifted_image) == 100

def test_apply_shift_subpixel_shift():
    """Test apply_shift with sub-pixel shifts and higher order interpolation."""
    image = np.zeros((10, 10))
    image[4, 4] = 100
    
    shifted_image = Astrometry.apply_shift(image, 0.5, 0.5, order=1) # Linear
    
    # With linear interpolation, the flux will be spread
    assert shifted_image[4, 4] < 100
    assert shifted_image[5, 5] > 0
    assert np.isclose(np.sum(shifted_image), 100.0) # Flux conserved

    shifted_image_cubic = Astrometry.apply_shift(image, 0.5, 0.5, order=3) # Cubic
    assert np.isclose(np.sum(shifted_image_cubic), 100.0)

def test_apply_shift_zero_shift():
    """Test apply_shift with zero shift."""
    image = create_gaussian_image()
    shifted_image = Astrometry.apply_shift(image, 0.0, 0.0)
    assert np.allclose(image, shifted_image)

def test_apply_shift_edge_effects():
    """Test apply_shift near image edges (should use cval=0.0)."""
    image = np.zeros((10, 10))
    image[0, 0] = 100
    
    shifted_image = Astrometry.apply_shift(image, -1, -1, order=0) # Shift off-image
    assert np.sum(shifted_image) == 0

    image[9, 9] = 100 # Star at bottom-right
    shifted_image = Astrometry.apply_shift(image, 1, 1, order=0) # Shift off-image
    assert np.sum(shifted_image) == 0