# pyexops/tests/test_scene.py

import numpy as np
import pytest
from pyexops import Star, Planet, Scene # Import necessary classes
from pyexops.binary_star_system import BinaryStarSystem # NEW: Import BinaryStarSystem

# Fixture for a basic Star object
@pytest.fixture
def basic_star():
    return Star(radius=5.0, base_flux=1000.0, limb_darkening_coeffs=(0.2, 0.1), star_mass=1.0)

# Fixture for a basic Planet object
@pytest.fixture
def basic_planet():
    return Planet(radius=0.1, period=10.0, semimajor_axis=10.0,
                  inclination=90.0, epoch_transit=0.0, planet_mass=1.0, host_star_index=0) # host_star_index added

# NEW: Fixture for a binary star system
@pytest.fixture
def test_binary_system():
    star_A = Star(radius=5.0, base_flux=10000.0, limb_darkening_coeffs=(0.3, 0.2), star_mass=1.0)
    star_B = Star(radius=2.0, base_flux=2000.0, limb_darkening_coeffs=(0.4, 0.1), star_mass=0.5)
    
    return BinaryStarSystem(
        star_A, star_B,
        period_days=10.0,
        semimajor_axis_stellar_radii=10.0, # Relative to starA's radius
        inclination_deg=90.0,
        eccentricity=0.0,
        argument_of_periastron_deg=0.0,
        epoch_periastron_days=0.0
    )

# Test Scene initialization with new parameters
def test_scene_init_with_jitter_and_prnu(basic_star, basic_planet):
    image_resolution = (50, 50)
    barycenter_pixel_on_image = (25, 25)
    pointing_jitter_std_pixels = 0.5
    prnu_map = np.ones(image_resolution) * 1.05

    scene = Scene(
        stars=basic_star, # Now accepts 'stars' as parameter name
        planets=[basic_planet],
        image_resolution=image_resolution,
        barycenter_pixel_on_image=barycenter_pixel_on_image,
        background_flux_per_pixel=10.0,
        read_noise_std=2.0,
        psf_type='gaussian',
        psf_params={'sigma_pixels': 1.0},
        pointing_jitter_std_pixels=pointing_jitter_std_pixels,
        pixel_response_non_uniformity_map=prnu_map
    )

    assert scene.pointing_jitter_std_pixels == pointing_jitter_std_pixels
    assert np.array_equal(scene.pixel_response_non_uniformity_map, prnu_map)
    assert scene.barycenter_pixel_on_image == barycenter_pixel_on_image
    assert scene.is_binary is False
    assert scene.star_list[0] is basic_star

    # Test invalid PRNU map shape
    with pytest.raises(ValueError, match="pixel_response_non_uniformity_map must have shape matching image_resolution."):
        Scene(
            stars=basic_star,
            planets=[basic_planet],
            image_resolution=image_resolution,
            barycenter_pixel_on_image=barycenter_pixel_on_image,
            pixel_response_non_uniformity_map=np.ones((10, 10))
        )
    
    # Test invalid stars type
    with pytest.raises(TypeError, match="`stars` must be a Star object for single systems or a BinaryStarSystem object."):
        Scene(
            stars="Not a star object",
            planets=[basic_planet],
            image_resolution=image_resolution,
            barycenter_pixel_on_image=barycenter_pixel_on_image
        )


# Test generate_image with pointing jitter
def test_generate_image_with_jitter(basic_star, basic_planet):
    image_resolution = (50, 50)
    barycenter_pixel_on_image = (25, 25)
    pointing_jitter_std_pixels = 1.0 # Significant jitter for testing

    scene_no_jitter = Scene(
        stars=basic_star,
        planets=[basic_planet],
        image_resolution=image_resolution,
        barycenter_pixel_on_image=barycenter_pixel_on_image,
        psf_type='gaussian', psf_params={'sigma_pixels': 1.0},
        read_noise_std=0.0, background_flux_per_pixel=0.0
    )
    
    scene_with_jitter = Scene(
        stars=basic_star,
        planets=[basic_planet],
        image_resolution=image_resolution,
        barycenter_pixel_on_image=barycenter_pixel_on_image,
        psf_type='gaussian', psf_params={'sigma_pixels': 1.0},
        pointing_jitter_std_pixels=pointing_jitter_std_pixels,
        read_noise_std=0.0, background_flux_per_pixel=0.0
    )

    num_frames = 100
    centroids_x = []
    centroids_y = []

    for _ in range(num_frames):
        img = scene_with_jitter.generate_image(time=0.0, add_noise=False, inject_systematics=False)
        y_coords, x_coords = np.indices(img.shape)
        total_flux = np.sum(img)
        if total_flux > 0:
            centroid_x = np.sum(img * x_coords) / total_flux
            centroid_y = np.sum(img * y_coords) / total_flux
            centroids_x.append(centroid_x)
            centroids_y.append(centroid_y)
        else:
            centroids_x.append(barycenter_pixel_on_image[0])
            centroids_y.append(barycenter_pixel_on_image[1])

    assert not np.allclose(centroids_x, barycenter_pixel_on_image[0], atol=0.01)
    assert not np.allclose(centroids_y, barycenter_pixel_on_image[1], atol=0.01)

    assert np.std(centroids_x) > pointing_jitter_std_pixels * 0.5 
    assert np.std(centroids_y) > pointing_jitter_std_pixels * 0.5

    img_no_jitter = scene_no_jitter.generate_image(time=0.0, add_noise=False, inject_systematics=False)
    total_flux_nj = np.sum(img_no_jitter)
    centroid_x_nj = np.sum(img_no_jitter * x_coords) / total_flux_nj
    centroid_y_nj = np.sum(img_no_jitter * y_coords) / total_flux_nj
    
    assert np.isclose(centroid_x_nj, barycenter_pixel_on_image[0], atol=0.1) 
    assert np.isclose(centroid_y_nj, barycenter_pixel_on_image[1], atol=0.1)


# Test generate_image with Pixel Response Non-Uniformity (PRNU)
def test_generate_image_with_prnu(basic_star, basic_planet):
    image_resolution = (50, 50)
    barycenter_pixel_on_image = (25, 25)
    
    prnu_map = np.ones(image_resolution)
    prnu_map[0:25, :] *= 0.9 
    prnu_map[25:50, :] *= 1.1 

    scene = Scene(
        stars=basic_star,
        planets=[basic_planet],
        image_resolution=image_resolution,
        barycenter_pixel_on_image=barycenter_pixel_on_image,
        background_flux_per_pixel=0.0, 
        read_noise_std=0.0, 
        psf_type='gaussian',
        psf_params={'sigma_pixels': 1.0},
        pixel_response_non_uniformity_map=prnu_map
    )
    
    img_with_prnu = scene.generate_image(time=0.0, add_noise=False, inject_systematics=False)

    scene_no_prnu = Scene(
        stars=basic_star,
        planets=[basic_planet],
        image_resolution=image_resolution,
        barycenter_pixel_on_image=barycenter_pixel_on_image,
        background_flux_per_pixel=0.0,
        read_noise_std=0.0,
        psf_type='gaussian',
        psf_params={'sigma_pixels': 1.0},
        pixel_response_non_uniformity_map=None
    )
    img_no_prnu = scene_no_prnu.generate_image(time=0.0, add_noise=False, inject_systematics=False)

    assert np.allclose(img_with_prnu, img_no_prnu * prnu_map, atol=1e-6)

    assert img_with_prnu[40, 25] > img_no_prnu[40, 25] 
    assert img_with_prnu[10, 25] < img_no_prnu[10, 25] 

def test_generate_image_with_jitter_and_prnu(basic_star, basic_planet):
    image_resolution = (50, 50)
    barycenter_pixel_on_image = (25, 25)
    pointing_jitter_std_pixels = 0.5
    prnu_map = np.ones(image_resolution) * 1.05 

    scene = Scene(
        stars=basic_star,
        planets=[basic_planet],
        image_resolution=image_resolution,
        barycenter_pixel_on_image=barycenter_pixel_on_image,
        background_flux_per_pixel=10.0,
        read_noise_std=2.0,
        psf_type='gaussian',
        psf_params={'sigma_pixels': 1.0},
        pointing_jitter_std_pixels=pointing_jitter_std_pixels,
        pixel_response_non_uniformity_map=prnu_map
    )

    img = scene.generate_image(time=0.0, add_noise=False, inject_systematics=False)

    assert np.sum(img) > 0 
    assert img.shape == image_resolution

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

    assert np.std(centroids_x) > 0.01 
    assert np.std(centroids_y) > 0.01
    
    scene_no_prnu_with_jitter = Scene(
        stars=basic_star,
        planets=[basic_planet],
        image_resolution=image_resolution,
        barycenter_pixel_on_image=barycenter_pixel_on_image,
        background_flux_per_pixel=10.0,
        read_noise_std=2.0,
        psf_type='gaussian',
        psf_params={'sigma_pixels': 1.0},
        pointing_jitter_std_pixels=pointing_jitter_std_pixels,
        pixel_response_non_uniformity_map=None
    )
    img_no_prnu = scene_no_prnu_with_jitter.generate_image(time=0.0, add_noise=False, inject_systematics=False)
    
    assert not np.allclose(np.sum(img), np.sum(img_no_prnu), atol=10.0) 

# NEW: Test Scene initialization with a BinaryStarSystem
def test_scene_init_with_binary_system(test_binary_system, basic_planet):
    image_resolution = (100, 100)
    barycenter_pixel_on_image = (50, 50)
    
    # Adjust basic_planet to orbit star_A (index 0)
    basic_planet.host_star_index = 0

    scene = Scene(
        stars=test_binary_system, # Pass BinaryStarSystem object
        planets=[basic_planet],
        image_resolution=image_resolution,
        barycenter_pixel_on_image=barycenter_pixel_on_image,
        background_flux_per_pixel=0.0,
        read_noise_std=0.0,
        psf_type='gaussian',
        psf_params={'sigma_pixels': 1.0}
    )

    assert scene.is_binary is True
    assert len(scene.star_list) == 2
    assert scene.star_list[0] is test_binary_system.star1
    assert scene.star_list[1] is test_binary_system.star2
    assert scene.barycenter_pixel_on_image == barycenter_pixel_on_image
    assert scene.pixels_per_reference_radius == test_binary_system.star1.radius # Reference radius from star1

# NEW: Test generate_image for a binary star system (no planets, just stars eclipsing)
def test_generate_image_binary_star_eclipse(test_binary_system):
    image_resolution = (100, 100)
    barycenter_pixel_on_image = (50, 50)

    scene = Scene(
        stars=test_binary_system,
        planets=[], # No planets for this test
        image_resolution=image_resolution,
        barycenter_pixel_on_image=barycenter_pixel_on_image,
        background_flux_per_pixel=0.0,
        read_noise_std=0.0,
        psf_type='gaussian',
        psf_params={'sigma_pixels': 1.0}
    )
    
    # Times around eclipse (epoch_periastron=0.0, inclination=90, so eclipse at t=0 and t=P/2)
    # Binary period = 10 days
    time_mid_eclipse = 0.0 # Conjunction
    time_oot = 2.5 # Quadrature

    img_eclipse = scene.generate_image(time_mid_eclipse, add_noise=False, inject_systematics=False)
    img_oot = scene.generate_image(time_oot, add_noise=False, inject_systematics=False)

    # In eclipse, flux should be less than OOT (sum of two stars)
    total_flux_eclipse = np.sum(img_eclipse)
    total_flux_oot = np.sum(img_oot)

    # OOT flux should be sum of fluxes of two stars (roughly)
    expected_oot_flux_approx = test_binary_system.star1.base_flux + test_binary_system.star2.base_flux
    assert total_flux_oot == pytest.approx(expected_oot_flux_approx, rel=0.05) # Allow some PSF/pixel effects

    # Eclipse flux should be significantly lower than OOT
    assert total_flux_eclipse < total_flux_oot * 0.9 # Expect at least 10% dip from main star being eclipsed


# NEW: Test generate_image for binary star system with planet transit
def test_generate_image_binary_star_with_planet_transit(test_binary_system):
    image_resolution = (100, 100)
    barycenter_pixel_on_image = (50, 50)

    # Planet orbiting Star A (index 0)
    planet_on_star_A = Planet(radius=0.1, period=test_binary_system.period_days / 5, # Faster orbit
                              semimajor_axis=test_binary_system.star1.radius * 3, # Close to star A
                              inclination=90.0, epoch_transit=test_binary_system.epoch_periastron_days,
                              planet_mass=0.001, host_star_index=0) # Orbits star A

    scene = Scene(
        stars=test_binary_system,
        planets=[planet_on_star_A],
        image_resolution=image_resolution,
        barycenter_pixel_on_image=barycenter_pixel_on_image,
        background_flux_per_pixel=0.0,
        read_noise_std=0.0,
        psf_type='gaussian',
        psf_params={'sigma_pixels': 1.0}
    )

    # Times:
    # 1. Primary transit of planet on star A (planet's epoch_transit = 0.0)
    # 2. Out-of-transit for planet, out-of-eclipse for binary
    # 3. Mid-binary eclipse (t=0.0 for binary)
    
    # Adjust planet's epoch_transit to fall outside binary eclipse for easier testing separation
    # Let planet transit at time = 1.0
    planet_on_star_A.epoch_transit = 1.0
    binary_eclipse_time = 0.0

    # Simulate images
    img_oot = scene.generate_image(time=5.0, add_noise=False, inject_systematics=False) # Out of both
    img_binary_eclipse = scene.generate_image(time=binary_eclipse_time, add_noise=False, inject_systematics=False)
    img_planet_transit = scene.generate_image(time=planet_on_star_A.epoch_transit, add_noise=False, inject_systematics=False)

    total_flux_oot = np.sum(img_oot)
    total_flux_binary_eclipse = np.sum(img_binary_eclipse)
    total_flux_planet_transit = np.sum(img_planet_transit)

    # Flux should drop during planet transit and binary eclipse
    assert total_flux_planet_transit < total_flux_oot * 0.95 # Expect planet dip
    assert total_flux_binary_eclipse < total_flux_oot * 0.95 # Expect binary dip

    # Ensure that planet transit doesn't affect the 'other' star if it's not transiting it.
    # This is implicitly handled by the per-star pixel flux calculation and planet.host_star_index.
    # However, for a planet orbiting S1, it *could* transit S2 from our perspective.
    # The current logic only applies occultation if planet.host_star_index matches the star being rendered.
    # This is a known simplification for phase 5.1.
    
    # Test a case where the planet could transit the other star from our perspective (more complex)
    # This requires specific orbital alignment. For this test, assume current simple model.