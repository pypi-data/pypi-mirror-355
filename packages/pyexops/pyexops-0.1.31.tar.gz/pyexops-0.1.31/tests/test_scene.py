# pyexops/tests/test_scene.py

import numpy as np
import pytest
from pyexops import Star, Planet, Scene # Import necessary classes

# Helper function for a simple Star object
@pytest.fixture
def basic_star():
    return Star(radius=5.0, base_flux=1000.0, limb_darkening_coeffs=(0.2, 0.1))

# Helper function for a simple Planet object
@pytest.fixture
def basic_planet():
    return Planet(radius=0.1, period=10.0, semimajor_axis=10.0,
                  inclination=90.0, epoch_transit=0.0, planet_mass=1.0)

# Test Scene initialization with new parameters
def test_scene_init_with_jitter_and_prnu(basic_star, basic_planet):
    image_resolution = (50, 50)
    star_center_pixel = (25, 25)
    pointing_jitter_std_pixels = 0.5
    prnu_map = np.ones(image_resolution) * 1.05 # 5% non-uniformity

    scene = Scene(
        star=basic_star,
        planets=[basic_planet],
        image_resolution=image_resolution,
        star_center_pixel=star_center_pixel,
        background_flux_per_pixel=10.0,
        read_noise_std=2.0,
        psf_type='gaussian',
        psf_params={'sigma_pixels': 1.0},
        pointing_jitter_std_pixels=pointing_jitter_std_pixels,
        pixel_response_non_uniformity_map=prnu_map
    )

    assert scene.pointing_jitter_std_pixels == pointing_jitter_std_pixels
    assert np.array_equal(scene.pixel_response_non_uniformity_map, prnu_map)

    # Test invalid PRNU map shape
    with pytest.raises(ValueError, match="pixel_response_non_uniformity_map must have shape matching image_resolution."):
        Scene(
            star=basic_star,
            planets=[basic_planet],
            image_resolution=image_resolution,
            star_center_pixel=star_center_pixel,
            pixel_response_non_uniformity_map=np.ones((10, 10))
        )

# Test generate_image with pointing jitter
def test_generate_image_with_jitter(basic_star, basic_planet):
    image_resolution = (50, 50)
    star_center_pixel = (25, 25)
    pointing_jitter_std_pixels = 1.0 # Significant jitter for testing

    scene_no_jitter = Scene(
        star=basic_star,
        planets=[basic_planet],
        image_resolution=image_resolution,
        star_center_pixel=star_center_pixel,
        psf_type='gaussian', psf_params={'sigma_pixels': 1.0},
        add_noise=False # Disable noise to isolate jitter effect
    )
    
    scene_with_jitter = Scene(
        star=basic_star,
        planets=[basic_planet],
        image_resolution=image_resolution,
        star_center_pixel=star_center_pixel,
        psf_type='gaussian', psf_params={'sigma_pixels': 1.0},
        pointing_jitter_std_pixels=pointing_jitter_std_pixels,
        add_noise=False
    )

    # Generate multiple images with jitter and check if their centroids vary
    # We can't predict the exact jitter, but we can check its effect statistically
    num_frames = 100
    centroids_x = []
    centroids_y = []

    for _ in range(num_frames):
        img = scene_with_jitter.generate_image(time=0.0, add_noise=False, inject_systematics=False)
        # Crude centroid estimation
        y_coords, x_coords = np.indices(img.shape)
        total_flux = np.sum(img)
        if total_flux > 0:
            centroid_x = np.sum(img * x_coords) / total_flux
            centroid_y = np.sum(img * y_coords) / total_flux
            centroids_x.append(centroid_x)
            centroids_y.append(centroid_y)
        else:
            centroids_x.append(star_center_pixel[0])
            centroids_y.append(star_center_pixel[1])


    # Check that centroids with jitter are not all at the nominal center
    assert not np.allclose(centroids_x, star_center_pixel[0], atol=0.01)
    assert not np.allclose(centroids_y, star_center_pixel[1], atol=0.01)

    # Check that the standard deviation of centroids is non-zero and roughly matches expected jitter
    # This is a statistical test, so it might fail occasionally if random numbers are extreme
    assert np.std(centroids_x) > pointing_jitter_std_pixels * 0.5 # Should be at least half the input stddev
    assert np.std(centroids_y) > pointing_jitter_std_pixels * 0.5

    # Check that a scene without jitter produces images with centroids consistently at the center
    img_no_jitter = scene_no_jitter.generate_image(time=0.0, add_noise=False, inject_systematics=False)
    total_flux_nj = np.sum(img_no_jitter)
    centroid_x_nj = np.sum(img_no_jitter * x_coords) / total_flux_nj
    centroid_y_nj = np.sum(img_no_jitter * y_coords) / total_flux_nj
    
    assert np.isclose(centroid_x_nj, star_center_pixel[0], atol=0.1) # PSF smoothing can cause minor sub-pixel variations
    assert np.isclose(centroid_y_nj, star_center_pixel[1], atol=0.1)


# Test generate_image with Pixel Response Non-Uniformity (PRNU)
def test_generate_image_with_prnu(basic_star, basic_planet):
    image_resolution = (50, 50)
    star_center_pixel = (25, 25)
    
    # Create a PRNU map with varying sensitivity
    prnu_map = np.ones(image_resolution)
    prnu_map[0:25, :] *= 0.9 # Top half 10% less sensitive
    prnu_map[25:50, :] *= 1.1 # Bottom half 10% more sensitive

    scene = Scene(
        star=basic_star,
        planets=[basic_planet],
        image_resolution=image_resolution,
        star_center_pixel=star_center_pixel,
        background_flux_per_pixel=0.0, # No background for clarity
        read_noise_std=0.0, # No noise
        psf_type='gaussian',
        psf_params={'sigma_pixels': 1.0},
        pixel_response_non_uniformity_map=prnu_map
    )
    
    # Generate an image with PRNU
    img_with_prnu = scene.generate_image(time=0.0, add_noise=False, inject_systematics=False)

    # Generate an image without PRNU for comparison (by making PRNU map None)
    scene_no_prnu = Scene(
        star=basic_star,
        planets=[basic_planet],
        image_resolution=image_resolution,
        star_center_pixel=star_center_pixel,
        background_flux_per_pixel=0.0,
        read_noise_std=0.0,
        psf_type='gaussian',
        psf_params={'sigma_pixels': 1.0},
        pixel_response_non_uniformity_map=None
    )
    img_no_prnu = scene_no_prnu.generate_image(time=0.0, add_noise=False, inject_systematics=False)

    # The image with PRNU should be element-wise multiplied by the PRNU map
    # A small tolerance for floating point operations after PSF convolution
    assert np.allclose(img_with_prnu, img_no_prnu * prnu_map, atol=1e-6)

    # Check if a specific pixel in the more sensitive region is higher than the corresponding one without PRNU
    # And a pixel in the less sensitive region is lower
    assert img_with_prnu[40, 25] > img_no_prnu[40, 25] # In 1.1 region
    assert img_with_prnu[10, 25] < img_no_prnu[10, 25] # In 0.9 region


# Test both jitter and PRNU applied simultaneously
def test_generate_image_with_jitter_and_prnu(basic_star, basic_planet):
    image_resolution = (50, 50)
    star_center_pixel = (25, 25)
    pointing_jitter_std_pixels = 0.5
    prnu_map = np.ones(image_resolution) * 1.05 # 5% non-uniformity

    scene = Scene(
        star=basic_star,
        planets=[basic_planet],
        image_resolution=image_resolution,
        star_center_pixel=star_center_pixel,
        background_flux_per_pixel=10.0,
        read_noise_std=2.0,
        psf_type='gaussian',
        psf_params={'sigma_pixels': 1.0},
        pointing_jitter_std_pixels=pointing_jitter_std_pixels,
        pixel_response_non_uniformity_map=prnu_map
    )

    img = scene.generate_image(time=0.0, add_noise=False, inject_systematics=False)

    # This test mainly ensures that the code runs without error and that the effects are present.
    # Verifying quantitative interaction between jitter and PRNU in a unit test is complex
    # due to the random nature of jitter. We'll rely on visual inspection in notebooks
    # and integration tests for more nuanced validation.
    assert np.sum(img) > 0 
    assert img.shape == image_resolution

    # Quick check for non-uniformity and jitter effect
    # The sum of flux should be affected by PRNU
    # The centroid should be shifted by jitter

    # To check jitter, we generate multiple images and verify centroids vary.
    num_frames = 50
    centroids_x = []
    centroids_y = []
    for _ in range(num_frames):
        img_temp = scene.generate_image(time=0.0, add_noise=False, inject_systematics=False)
        y_coords, x_coords = np.indices(img_temp.shape)
        total_flux = np.sum(img_temp)
        if total_flux > 0:
            centroids_x.append(np.sum(img_temp * x_coords) / total_flux)
            centroids_y.append(np.sum(img_temp * y_coords) / total_flux)

    assert np.std(centroids_x) > 0.01 # Expect some spread due to jitter
    assert np.std(centroids_y) > 0.01

    # To check PRNU, compare with a case that has jitter but no PRNU.
    # This is tricky because jitter randomizes exact flux values.
    # A more robust check might involve analyzing a large number of images or
    # using a very simple PRNU that affects sum (e.g., global factor).
    # For now, let's just assert that the total flux is not exactly the same as without PRNU,
    # assuming the star is not perfectly centered in a PRNU-neutral region.
    
    scene_no_prnu_with_jitter = Scene(
        star=basic_star,
        planets=[basic_planet],
        image_resolution=image_resolution,
        star_center_pixel=star_center_pixel,
        background_flux_per_pixel=10.0,
        read_noise_std=2.0,
        psf_type='gaussian',
        psf_params={'sigma_pixels': 1.0},
        pointing_jitter_std_pixels=pointing_jitter_std_pixels,
        pixel_response_non_uniformity_map=None
    )
    img_no_prnu = scene_no_prnu_with_jitter.generate_image(time=0.0, add_noise=False, inject_systematics=False)
    
    # We expect the mean flux to be different if PRNU is non-uniform and star is not perfectly centered or very broad
    # For a simple uniform PRNU factor (e.g., 1.05 everywhere), total flux would be * 1.05
    # For the split PRNU map, it's more complex. A simpler assertion is if the effect is noticeable.
    assert not np.allclose(np.sum(img), np.sum(img_no_prnu), atol=10.0) # Allow some difference