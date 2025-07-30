# pyexops/tests/test_photometer.py

import numpy as np
import pytest
from scipy.ndimage import convolve # Only needed for PSF matching logic check
from pyexops.photometer import Photometer
from pyexops.astrometry import Astrometry # Import Astrometry

# Helper to create a simple star image (Gaussian)
def create_gaussian_image(shape=(100, 100), center=(50, 50), sigma=2.0, amplitude=1000.0):
    """Creates a 2D Gaussian image."""
    y, x = np.mgrid[0:shape[0], 0:shape[1]]
    gaussian_2d = amplitude * np.exp(-((x - center[0])**2 + (y - center[1])**2) / (2 * sigma**2))
    return gaussian_2d

# Fixture for a basic image
@pytest.fixture
def image_data():
    return create_gaussian_image() + 50 # Add background

# Fixture for a basic PSF kernel (normalized Gaussian)
@pytest.fixture
def psf_kernel():
    sigma = 1.5
    size = int(np.ceil(sigma * 5))
    if size % 2 == 0: size += 1
    center = size // 2
    y, x = np.indices((size, size)) - center
    r_sq = x**2 + y**2
    kernel = np.exp(-r_sq / (2 * sigma**2))
    return kernel / np.sum(kernel)

# Fixture for a basic Photometer instance
@pytest.fixture
def photometer_instance(psf_kernel):
    target_ap_rad = 3.0 * 1.5 # 3 sigma for Gaussian PSF
    bg_inner_rad = target_ap_rad + 5.0
    bg_outer_rad = bg_inner_rad + 10.0
    system_center = (50, 50) # NEW: Changed to system_center_pixel
    return Photometer(target_ap_rad, bg_inner_rad, bg_outer_rad, psf_kernel, system_center_pixel=system_center)

def test_photometer_init_system_center_pixel(photometer_instance): # NEW: Test new parameter name
    """Test if system_center_pixel is stored correctly."""
    assert photometer_instance.system_center_pixel == (50, 50)

def test_define_apertures(photometer_instance): # Changed fixture usage
    """Test aperture mask generation."""
    # Now uses photometer_instance (which has system_center_pixel = (50,50))
    target_mask, bg_mask = photometer_instance.define_apertures(50, 50, (100, 100)) # Pass explicit center
    
    assert target_mask.shape == (100, 100)
    assert bg_mask.shape == (100, 100)
    
    # Check some pixel values
    assert target_mask[50, 50] == True # Center pixel
    assert target_mask[50, 55] == False # Outside target radius
    assert bg_mask[50, 12] == True # Inside background annulus
    assert bg_mask[50, 8] == False # Inside inner bg radius
    assert bg_mask[50, 20] == False # Outside outer bg radius

def test_extract_sap_flux(image_data, photometer_instance):
    """Test SAP flux extraction."""
    target_mask, background_mask = photometer_instance.define_apertures(50, 50, image_data.shape)
    flux, bg_per_pixel = photometer_instance.extract_sap_flux(image_data, target_mask, background_mask)
    
    assert flux > 0 
    assert bg_per_pixel > 0 
    assert np.isclose(bg_per_pixel, 50.0, atol=1.0) 

def test_extract_optimal_flux(image_data, photometer_instance):
    """Test Optimal flux extraction."""
    target_mask, background_mask = photometer_instance.define_apertures(50, 50, image_data.shape)
    flux, bg_per_pixel = photometer_instance.extract_optimal_flux(image_data, target_mask, background_mask, (50, 50)) # Pass centroid_guess
    
    assert flux > 0 
    assert bg_per_pixel > 0 
    assert np.isclose(bg_per_pixel, 50.0, atol=1.0)

def test_extract_psf_fitting_flux(image_data, photometer_instance):
    """Test PSF fitting flux extraction."""
    target_mask, background_mask = photometer_instance.define_apertures(50, 50, image_data.shape)
    flux, bg_per_pixel, fitted_x, fitted_y = photometer_instance.extract_psf_fitting_flux(image_data, (50, 50), background_mask) # Pass centroid_guess
    
    assert flux > 0 
    assert bg_per_pixel > 0 
    assert np.isclose(bg_per_pixel, 50.0, atol=1.0)
    assert np.isclose(fitted_x, 50.0, atol=0.1) 
    assert np.isclose(fitted_y, 50.0, atol=0.1)

def test_extract_dip_flux_no_alignment_no_psf_matching(image_data, photometer_instance):
    """Test DIP with no alignment and no PSF matching."""
    template_image = image_data * 0.9 + 5 
    
    target_mask, background_mask = photometer_instance.define_apertures(50, 50, image_data.shape)
    
    extracted_flux, diff_bg = photometer_instance.extract_difference_imaging_flux(
        image_data, template_image, (50, 50), background_mask, # Pass system_center_pixel
        perform_alignment=False, apply_psf_matching_kernel=False
    )
    
    original_star_flux, _ = photometer_instance.extract_sap_flux(image_data, target_mask, background_mask)
    
    assert np.isclose(extracted_flux, original_star_flux, rtol=0.05) 
    assert np.isclose(diff_bg, 0.0, atol=1.0) 

def test_extract_dip_flux_with_alignment(image_data, photometer_instance):
    """Test DIP with image alignment."""
    true_dy, true_dx = 0.5, -0.7
    image_shifted = Astrometry.apply_shift(image_data, true_dy, true_dx, order=3)
    
    template_image = image_data * 0.9 + 5 
    
    target_mask, background_mask = photometer_instance.define_apertures(50, 50, image_data.shape)
    
    extracted_flux, diff_bg = photometer_instance.extract_difference_imaging_flux(
        image_shifted, template_image, (50, 50), background_mask,
        perform_alignment=True, apply_psf_matching_kernel=False
    )
    
    original_star_flux, _ = photometer_instance.extract_sap_flux(image_data, target_mask, background_mask)
    
    assert np.isclose(extracted_flux, original_star_flux, rtol=0.05)
    assert np.isclose(diff_bg, 0.0, atol=1.0)


def test_extract_dip_flux_with_psf_matching(image_data, photometer_instance, psf_kernel):
    """Test DIP with PSF matching kernel."""
    broad_psf_kernel_temp = psf_kernel * 1.5 
    broad_psf_kernel_temp = broad_psf_kernel_temp / np.sum(broad_psf_kernel_temp)
    
    template_raw = np.zeros_like(image_data)
    template_raw[50, 50] = 1000 
    template_image_mismatched_psf = convolve(template_raw, broad_psf_kernel_temp, mode='constant', cval=0.0) + 50
    template_image_mismatched_psf *= 0.9 
    
    target_mask, background_mask = photometer_instance.define_apertures(50, 50, image_data.shape)

    extracted_flux_with_match, _ = photometer_instance.extract_difference_imaging_flux(
        image_data, template_image_mismatched_psf, (50, 50), background_mask,
        perform_alignment=False, apply_psf_matching_kernel=True
    )
    
    original_star_flux, _ = photometer_instance.extract_sap_flux(image_data, target_mask, background_mask)
    
    assert extracted_flux_with_match > 0
    assert np.isclose(extracted_flux_with_match, original_star_flux, rtol=0.1) 

    phot_no_kernel = Photometer(3, 8, 18, psf_kernel=None, system_center_pixel=(50,50))
    with pytest.raises(ValueError, match="PSF matching for DIP requires a PSF kernel"):
        phot_no_kernel.extract_difference_imaging_flux(
            image_data, template_image_mismatched_psf, (50, 50), background_mask,
            perform_alignment=False, apply_psf_matching_kernel=True
        )

def test_extract_dip_flux_with_alignment_and_psf_matching(image_data, photometer_instance, psf_kernel):
    """Test DIP with both image alignment and PSF matching."""
    true_dy, true_dx = 0.5, -0.7
    image_shifted = Astrometry.apply_shift(image_data, true_dy, true_dx, order=3)
    
    broad_psf_kernel_temp = psf_kernel * 1.5 
    broad_psf_kernel_temp = broad_psf_kernel_temp / np.sum(broad_psf_kernel_temp)
    template_raw = np.zeros_like(image_data)
    template_raw[50, 50] = 1000 
    template_image_mismatched_psf = convolve(template_raw, broad_psf_kernel_temp, mode='constant', cval=0.0) + 50
    template_image_mismatched_psf *= 0.9 
    
    target_mask, background_mask = photometer_instance.define_apertures(50, 50, image_data.shape)
    
    extracted_flux, diff_bg = photometer_instance.extract_difference_imaging_flux(
        image_shifted, template_image_mismatched_psf, (50, 50), background_mask,
        perform_alignment=True, apply_psf_matching_kernel=True
    )
    
    original_star_flux, _ = photometer_instance.extract_sap_flux(image_data, target_mask, background_mask)
    
    assert extracted_flux > 0
    assert np.isclose(extracted_flux, original_star_flux, rtol=0.1) 
    assert np.isclose(diff_bg, 0.0, atol=1.0)