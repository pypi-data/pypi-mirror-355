# pyexops/tests/test_scene.py

import pytest
import numpy as np
from pyexops import Star, Planet, Scene, Atmosphere

# Common parameters for tests
STAR_RADIUS = 10.0
BASE_FLUX = 5000.0
LIMB_DARKENING = (0.5, 0.2)
IMAGE_RESOLUTION = (50, 50)
STAR_CENTER_PIXEL = (25, 25)
BACKGROUND_FLUX = 1.0
READ_NOISE_STD = 1.0
PSF_TYPE = 'gaussian'
PSF_PARAMS = {'sigma_pixels': 1.0}

def create_default_star_and_planet(planet_radius=0.1):
    star = Star(STAR_RADIUS, BASE_FLUX, LIMB_DARKENING)
    # Period 1.0, SMA 10.0, Inc 90.0, Epoch 0.0
    planet = Planet(planet_radius, 1.0, 10.0, 90.0, 0.0, planet_mass=0.01) # Low mass, no RV effect
    return star, [planet]

def test_scene_initialization():
    star, planets = create_default_star_and_planet()
    scene = Scene(star, planets, IMAGE_RESOLUTION, STAR_CENTER_PIXEL, BACKGROUND_FLUX, READ_NOISE_STD, PSF_TYPE, PSF_PARAMS)
    
    assert scene.star == star
    assert scene.planets == planets
    assert scene.width == IMAGE_RESOLUTION[0]
    assert scene.height == IMAGE_RESOLUTION[1]
    assert scene.star_center_pixel_x == STAR_CENTER_PIXEL[0]
    assert scene.star_center_pixel_y == STAR_CENTER_PIXEL[1]
    assert scene.background_flux_per_pixel == BACKGROUND_FLUX
    assert scene.read_noise_std == READ_NOISE_STD
    assert scene.psf_type == PSF_TYPE
    assert scene.psf_params == PSF_PARAMS
    assert scene.pixels_per_star_radius == STAR_RADIUS
    assert scene.psf_kernel_for_photometry is not None

def test_generate_image_no_planet_no_noise():
    star, _ = create_default_star_and_planet() # No planets
    scene = Scene(star, [], IMAGE_RESOLUTION, STAR_CENTER_PIXEL, BACKGROUND_FLUX, READ_NOISE_STD, PSF_TYPE, PSF_PARAMS)
    
    image = scene.generate_image(time=0.0, add_noise=False, inject_systematics=False)
    
    assert image.shape == IMAGE_RESOLUTION
    assert np.all(image >= BACKGROUND_FLUX) # Should at least have background flux
    # Center pixel should have star flux + background
    center_flux_expected = star.get_pixel_flux(0.0, 0.0, time=0.0) # Star center flux at t=0
    assert image[STAR_CENTER_PIXEL[1], STAR_CENTER_PIXEL[0]] > BACKGROUND_FLUX # PSF spreads it, but center should be bright

def test_generate_image_with_noise():
    star, _ = create_default_star_and_planet()
    scene = Scene(star, [], IMAGE_RESOLUTION, STAR_CENTER_PIXEL, BACKGROUND_FLUX, READ_NOISE_STD, PSF_TYPE, PSF_PARAMS)
    
    image_noisy = scene.generate_image(time=0.0, add_noise=True, inject_systematics=False)
    image_clean = scene.generate_image(time=0.0, add_noise=False, inject_systematics=False)
    
    # Noise should make them different
    assert not np.array_equal(image_noisy, image_clean)
    # Assert noise values are plausible (e.g. standard deviation is non-zero)
    assert np.std(image_noisy - image_clean) > 0.1 # Should be some variation

def test_generate_image_with_planet_transit():
    star, planets = create_default_star_and_planet(planet_radius=0.3) # Large planet
    scene = Scene(star, planets, IMAGE_RESOLUTION, STAR_CENTER_PIXEL, BACKGROUND_FLUX, READ_NOISE_STD, PSF_TYPE, PSF_PARAMS)
    
    # At mid-transit (t=0), planet should occult star
    image_transit = scene.generate_image(time=0.0, add_noise=False, inject_systematics=False)
    # Out of transit (t=0.5 * period), planet should not occult
    image_oot = scene.generate_image(time=0.5, add_noise=False, inject_systematics=False)
    
    # Sum of flux in image_transit should be less than image_oot
    assert np.sum(image_transit) < np.sum(image_oot)

def test_generate_image_with_transmission_spectroscopy():
    """
    Test generate_image uses effective radius for occultation when atmosphere and wavelength are provided.
    Simulate a planet that is larger at 800nm than at 600nm.
    """
    solid_radius = 0.15
    # Atmosphere makes planet effectively 0.16 at 800nm, 0.17 at 850nm, 0.15 at 900nm
    transmission_data = [(600.0, solid_radius), (800.0, 0.16), (850.0, 0.17), (900.0, solid_radius)]
    atmosphere = Atmosphere(solid_radius, transmission_data)

    star = Star(STAR_RADIUS, BASE_FLUX)
    # Set planet to be slightly grazing to highlight radius difference
    planet_inclination = 89.8 # Adjust inclination for sensitivity
    planet = Planet(radius=solid_radius, period=1.0, semimajor_axis=10.0, 
                    inclination=planet_inclination, epoch_transit=0.0,
                    planet_mass=0.01, atmosphere=atmosphere)
    planets = [planet]
    
    scene = Scene(star, planets, IMAGE_RESOLUTION, STAR_CENTER_PIXEL, BACKGROUND_FLUX, READ_NOISE_STD, PSF_TYPE, PSF_PARAMS)

    # Generate image at mid-transit (time=0) for two different wavelengths
    # Wavelength 1: 850nm (where effective radius is 0.17) - should have deeper transit
    image_850nm = scene.generate_image(time=0.0, add_noise=False, inject_systematics=False, wavelength_nm=850.0)
    # Wavelength 2: 600nm (where effective radius is solid_radius=0.15) - shallower transit
    image_600nm = scene.generate_image(time=0.0, add_noise=False, inject_systematics=False, wavelength_nm=600.0)

    # Get out-of-transit image for comparison
    image_oot = scene.generate_image(time=0.5, add_noise=False, inject_systematics=False)
    
    # Calculate total flux for each image
    total_flux_850nm = np.sum(image_850nm)
    total_flux_600nm = np.sum(image_600nm)
    total_flux_oot = np.sum(image_oot)

    # Check if 850nm transit is deeper (lower flux) than 600nm transit
    assert total_flux_850nm < total_flux_600nm, "Transit at 850nm (larger effective radius) should be deeper."
    assert total_flux_850nm < total_flux_oot # Both should be deeper than OOT
    assert total_flux_600nm < total_flux_oot

def test_generate_template_image_basic():
    star, planets = create_default_star_and_planet()
    scene = Scene(star, planets, IMAGE_RESOLUTION, STAR_CENTER_PIXEL, BACKGROUND_FLUX)
    
    times = np.linspace(0, 10, 100) # Some times
    template = scene.generate_template_image(times, num_frames=10, add_noise=False)
    
    assert template.shape == IMAGE_RESOLUTION
    assert np.all(template >= BACKGROUND_FLUX)
    # Template should resemble a star image without significant transit features
    center_flux = star.get_pixel_flux(0.0, 0.0, time=0.0)
    assert template[STAR_CENTER_PIXEL[1], STAR_CENTER_PIXEL[0]] > BACKGROUND_FLUX