# pyexops/tests/test_photometer.py

import pytest
import numpy as np
from pyexops import Photometer, Star, Scene

# Fixtures for Photometer testing
@pytest.fixture
def basic_photometer():
    return Photometer(target_aperture_radius_pixels=5.0,
                      background_aperture_inner_radius_pixels=7.0,
                      background_aperture_outer_radius_pixels=10.0)

@pytest.fixture
def photometer_with_psf():
    # Create a simple Gaussian PSF kernel for testing
    sigma = 1.5
    size = int(np.ceil(sigma * 7)) # Larger kernel to avoid edge effects
    if size % 2 == 0: size += 1
    center = size // 2
    y, x = np.indices((size, size)) - center
    r_sq = x**2 + y**2
    kernel = np.exp(-r_sq / (2 * sigma**2))
    kernel /= np.sum(kernel) # Normalize
    
    return Photometer(target_aperture_radius_pixels=5.0,
                      background_aperture_inner_radius_pixels=7.0,
                      background_aperture_outer_radius_pixels=10.0,
                      psf_kernel=kernel,
                      read_noise_std=1.0) # Provide read noise for optimal weights

@pytest.fixture
def sample_image_data():
    # A 20x20 image with a bright spot (star) and uniform background
    img = np.full((20, 20), 10.0) # Background flux
    # Add a bright spot (simplified star, not PSF-convolved)
    img[8:12, 8:12] += 100.0 # Bright 4x4 square at center
    return img

@pytest.fixture
def sample_target_mask():
    # A circular mask around (9.5, 9.5) with radius 2.5 (covering the 4x4 spot)
    mask = np.zeros((20, 20), dtype=bool)
    Y, X = np.indices((20, 20))
    distances = np.sqrt((X - 9.5)**2 + (Y - 9.5)**2) # Star at (9.5, 9.5)
    mask[distances <= 2.5] = True
    return mask

@pytest.fixture
def sample_background_mask():
    # An annulus mask around (9.5, 9.5)
    mask = np.zeros((20, 20), dtype=bool)
    Y, X = np.indices((20, 20))
    distances = np.sqrt((X - 9.5)**2 + (Y - 9.5)**2)
    mask[(distances >= 4.0) & (distances <= 6.0)] = True
    return mask

# --- Test define_apertures ---
def test_define_apertures_masks_are_boolean(basic_photometer):
    target_mask, background_mask = basic_photometer.define_apertures(10, 10, (20, 20))
    assert target_mask.dtype == bool
    assert background_mask.dtype == bool

def test_define_apertures_correct_sizes(basic_photometer):
    target_mask, background_mask = basic_photometer.define_apertures(10, 10, (20, 20))
    # Roughly check expected pixel counts for radius 5.0 (target) and annulus 7.0-10.0 (background)
    assert np.sum(target_mask) == pytest.approx(np.pi * 5.0**2, rel=0.1) # Approx area
    assert np.sum(background_mask) == pytest.approx(np.pi * (10.0**2 - 7.0**2), rel=0.1) # Approx area

def test_define_apertures_no_overlap(basic_photometer):
    target_mask, background_mask = basic_photometer.define_apertures(10, 10, (20, 20))
    assert not np.any(target_mask & background_mask) # No common pixels

def test_define_apertures_invalid_radii():
    with pytest.raises(ValueError, match="Background inner radius must be strictly greater than target aperture radius."):
        Photometer(5.0, 5.0, 10.0)
    with pytest.raises(ValueError, match="Background outer radius must be strictly greater than inner radius."):
        Photometer(1.0, 7.0, 7.0)

# --- Test _estimate_background ---
def test_estimate_background(basic_photometer):
    img = np.full((10,10), 50.0)
    bg_mask = np.ones((10,10), dtype=bool)
    avg_bg, count_bg = basic_photometer._estimate_background(img, bg_mask)
    assert avg_bg == 50.0
    assert count_bg == 100

def test_estimate_background_no_pixels(basic_photometer):
    img = np.full((10,10), 50.0)
    bg_mask = np.zeros((10,10), dtype=bool)
    avg_bg, count_bg = basic_photometer._estimate_background(img, bg_mask)
    assert avg_bg == 0.0
    assert count_bg == 0

# --- Test extract_sap_flux ---
def test_extract_sap_flux(basic_photometer, sample_image_data, sample_target_mask, sample_background_mask):
    flux, bg = basic_photometer.extract_sap_flux(sample_image_data, sample_target_mask, sample_background_mask)
    # Expected: 4x4 spot at 100 flux = 1600 total. Background 10.0. Target area is ~20 pixels.
    # So (1600 + 20*10) - (10 * 20) = 1600.
    assert flux == pytest.approx(1600.0) 
    assert bg == pytest.approx(10.0)

# --- Test _find_centroid ---
def test_find_centroid_center(basic_photometer):
    img = np.zeros((20,20))
    img[9:11, 9:11] = 100 # Perfect 2x2 square at center
    cx, cy = basic_photometer._find_centroid(img, (9.5, 9.5))
    assert cx == pytest.approx(9.5)
    assert cy == pytest.approx(9.5)

def test_find_centroid_offset(basic_photometer):
    img = np.zeros((20,20))
    img[14:16, 14:16] = 100 # Offset square
    cx, cy = basic_photometer._find_centroid(img, (14.5, 14.5))
    assert cx == pytest.approx(14.5)
    assert cy == pytest.approx(14.5)

def test_find_centroid_empty_image(basic_photometer):
    img = np.zeros((20,20))
    cx, cy = basic_photometer._find_centroid(img, (9.5, 9.5))
    assert cx == pytest.approx(9.5) # Should fall back to guess

# --- Test extract_optimal_flux ---
def test_extract_optimal_flux_requires_psf(basic_photometer, sample_image_data, sample_target_mask, sample_background_mask):
    with pytest.raises(ValueError, match="Optimal Photometry requires a PSF kernel"):
        basic_photometer.extract_optimal_flux(sample_image_data, sample_target_mask, sample_background_mask, (9.5, 9.5))

def test_extract_optimal_flux_basic(photometer_with_psf):
    # Create a simple image where the optimal flux is known
    # Star at center (25,25) of 50x50 image, flux 1000, sigma=1.5
    star_base_flux = 1000.0
    scene = Scene(star=Star(10.0, star_base_flux, (0,0)), planets=[], image_resolution=(50,50), star_center_pixel=(25,25),
                  background_flux_per_pixel=10.0, read_noise_std=1.0, psf_type='gaussian', psf_params={'sigma_pixels': 1.5})
    image_data = scene.generate_image(time=0.0, add_noise=False, inject_systematics=False)

    target_mask, background_mask = photometer_with_psf.define_apertures(25, 25, (50, 50))
    
    # Run optimal photometry
    optimal_flux, avg_bg = photometer_with_psf.extract_optimal_flux(image_data, target_mask, background_mask, (25, 25))

    assert avg_bg == pytest.approx(10.0) # Background should be recovered
    # Optimal flux should be close to the actual star flux (1000)
    assert optimal_flux == pytest.approx(star_base_flux, rel=0.05) # Allow some relative tolerance due to PSF sampling


# --- Test extract_psf_fitting_flux ---
def test_extract_psf_fitting_flux_requires_psf(basic_photometer, sample_image_data, sample_background_mask):
    with pytest.raises(ValueError, match="PSF Fitting Photometry requires a PSF kernel"):
        basic_photometer.extract_psf_fitting_flux(sample_image_data, (9.5, 9.5), sample_background_mask)

def test_extract_psf_fitting_flux_basic(photometer_with_psf):
    # Create a simple image with a known PSF profile
    star_base_flux = 1000.0
    actual_star_center = (25.3, 25.7) # Slightly off-center for fitting test
    scene = Scene(star=Star(10.0, star_base_flux, (0,0)), planets=[], image_resolution=(50,50), star_center_pixel=actual_star_center, # Use actual_star_center
                  background_flux_per_pixel=10.0, read_noise_std=1.0, psf_type='gaussian', psf_params={'sigma_pixels': 1.5})
    image_data = scene.generate_image(time=0.0, add_noise=False, inject_systematics=False)
    
    # We pass the ideal star_center_pixel as the initial guess to the photometer.
    # The photometer will internally use this for its cutout and fitting.
    fitted_flux, avg_bg, fitted_x, fitted_y = photometer_with_psf.extract_psf_fitting_flux(image_data, (25,25), # Initial integer guess
                                                                                         photometer_with_psf.define_apertures(25,25,(50,50))[1]) # Pass background mask

    assert avg_bg == pytest.approx(10.0, abs=0.1) # Background should be recovered
    assert fitted_flux == pytest.approx(star_base_flux, rel=0.05) # Flux should be recovered
    assert fitted_x == pytest.approx(actual_star_center[0], abs=0.5) # Centroid should be close to actual
    assert fitted_y == pytest.approx(actual_star_center[1], abs=0.5) # Centroid should be close to actual

# --- Test extract_difference_imaging_flux ---
def test_extract_difference_imaging_flux_basic(basic_photometer, sample_image_data, sample_background_mask):
    # Template: star flux 1600.0, background 10.0
    template_image = np.full((20, 20), 10.0) 
    template_image[8:12, 8:12] += 1600.0 # Star at 1600 flux in template

    # Image data: star flux changes to 1500.0 (transit effect)
    image_transit = np.full((20, 20), 10.0)
    image_transit[8:12, 8:12] += 1500.0

    # Ensure masks cover the star region
    target_mask, _ = basic_photometer.define_apertures(9.5, 9.5, (20, 20))

    # DIP should ideally recover 1500.0 flux (relative to template's 1600.0)
    # The method returns total flux (template star flux + difference)
    extracted_flux, avg_bg_diff = basic_photometer.extract_difference_imaging_flux(
        image_transit, template_image, (9.5, 9.5), sample_background_mask
    )
    
    assert extracted_flux == pytest.approx(1500.0)
    assert avg_bg_diff == pytest.approx(0.0, abs=1e-6) # Background in difference image should be near zero