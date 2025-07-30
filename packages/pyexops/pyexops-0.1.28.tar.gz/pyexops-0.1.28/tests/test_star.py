# pyexops/tests/test_star.py

import pytest
import numpy as np
from pyexops import Star, Spot

# Common parameters for tests
STAR_RADIUS = 10.0
BASE_FLUX = 100.0
LIMB_DARKENING = (0.5, 0.2)

def test_star_initialization():
    """Test Star initialization with default parameters."""
    star = Star(STAR_RADIUS, BASE_FLUX)
    assert star.radius == STAR_RADIUS
    assert star.base_flux == BASE_FLUX
    assert star.u1 == LIMB_DARKENING[0]
    assert star.u2 == LIMB_DARKENING[1]
    assert star.star_mass == 1.0 # Default
    assert star.rotational_period_equator_days == 25.0 # Default
    assert star.differential_rotation_coeff == 0.0 # Default
    assert star.spots == []
    assert star.flares == [] # Check for empty flares list

def test_star_initialization_custom_params():
    """Test Star initialization with custom parameters."""
    star = Star(20.0, 200.0, (0.1, 0.3), star_mass=0.5,
                rotational_period_equator_days=10.0, differential_rotation_coeff=0.1)
    assert star.radius == 20.0
    assert star.base_flux == 200.0
    assert star.u1 == 0.1
    assert star.u2 == 0.3
    assert star.star_mass == 0.5
    assert star.rotational_period_equator_days == 10.0
    assert star.differential_rotation_coeff == 0.1

def test_add_spot():
    """Test adding a spot to the star."""
    star = Star(STAR_RADIUS, BASE_FLUX)
    spot = Spot(latitude_deg=0.0, longitude_at_epoch_deg=0.0, 
                radius_umbra=0.1, radius_penumbra=0.2, 
                contrast_umbra=0.1, contrast_penumbra=0.5)
    star.add_spot(spot)
    assert len(star.spots) == 1
    assert star.spots[0] == spot

def test_add_flare():
    """Test adding a flare to the star."""
    star = Star(STAR_RADIUS, BASE_FLUX)
    flare = star.Flare(flare_time_peak=5.0, flare_duration_days=0.1, flare_amplitude_relative=0.01)
    star.add_flare(flare)
    assert len(star.flares) == 1
    assert star.flares[0] == flare

def test_spot_initialization():
    """Test Spot initialization."""
    spot = Spot(latitude_deg=30.0, longitude_at_epoch_deg=45.0, 
                radius_umbra=0.1, radius_penumbra=0.2, 
                contrast_umbra=0.1, contrast_penumbra=0.5)
    assert spot.latitude_deg == 30.0
    assert spot.longitude_at_epoch_deg == 45.0
    assert spot.radius_umbra == 0.1
    assert spot.radius_penumbra == 0.2
    assert spot.contrast_umbra == 0.1
    assert spot.contrast_penumbra == 0.5

def test_flare_initialization():
    """Test Flare initialization."""
    star = Star(STAR_RADIUS, BASE_FLUX) # Need a Star instance to create Flare object
    flare = star.Flare(flare_time_peak=10.0, flare_duration_days=0.5, flare_amplitude_relative=0.02, flare_shape='exponential_decay')
    assert flare.flare_time_peak == 10.0
    assert flare.flare_duration_days == 0.5
    assert flare.flare_amplitude_relative == 0.02
    assert flare.flare_shape == 'exponential_decay'
    with pytest.raises(ValueError, match="Flare shape 'invalid_shape' not supported."):
        star.Flare(0.0, 0.1, 0.01, flare_shape='invalid_shape')

def test_flare_flux_contribution_exponential_decay():
    """
    Test get_flux_contribution for 'exponential_decay' flare shape.
    Verifies rise, peak, and decay phases.
    """
    star = Star(STAR_RADIUS, BASE_FLUX)
    peak_time = 5.0
    duration = 0.1 # Days
    amplitude = 0.1 # 10% increase
    flare = star.Flare(flare_time_peak=peak_time, flare_duration_days=duration, flare_amplitude_relative=amplitude)

    rise_time_expected = duration * 0.1
    decay_time_expected = duration * 0.9

    # Before flare starts
    assert np.isclose(flare.get_flux_contribution(peak_time - rise_time_expected - 0.01), 0.0)

    # At flare start (should be 0)
    assert np.isclose(flare.get_flux_contribution(peak_time - rise_time_expected), 0.0)

    # Halfway through rise
    half_rise_time = peak_time - rise_time_expected / 2
    assert np.isclose(flare.get_flux_contribution(half_rise_time), amplitude / 2)

    # At peak time
    assert np.isclose(flare.get_flux_contribution(peak_time), amplitude)

    # During decay (e.g., half decay time from peak)
    decay_point_time = peak_time + decay_time_expected / 2
    # The exponential decay tau is decay_time_expected / 3.0
    expected_decay_flux = amplitude * np.exp(-(decay_point_time - peak_time) / (decay_time_expected / 3.0))
    assert np.isclose(flare.get_flux_contribution(decay_point_time), expected_decay_flux)

    # Long after flare end (should be 0 due to cutoff)
    assert np.isclose(flare.get_flux_contribution(peak_time + decay_time_expected * 2 + 0.1), 0.0)
    assert np.isclose(flare.get_flux_contribution(peak_time + decay_time_expected * 3), 0.0)


def test_get_pixel_flux_outside_star():
    """Test get_pixel_flux for a pixel outside the star."""
    star = Star(STAR_RADIUS, BASE_FLUX)
    # x_rel=1.1 means 1.1 stellar radii from center
    flux = star.get_pixel_flux(x_rel=1.1, y_rel=0.0, time=0.0)
    assert flux == 0.0

def test_get_pixel_flux_center_no_spots_no_flares():
    """Test get_pixel_flux at star center with no spots or flares (should be base_flux)."""
    star = Star(STAR_RADIUS, BASE_FLUX)
    # At center (r_prime=0), mu=1, limb darkening factor is (1 - u1*0 - u2*0) = 1.0
    flux = star.get_pixel_flux(x_rel=0.0, y_rel=0.0, time=0.0)
    assert flux == star.base_flux

def test_get_pixel_flux_limb_darkening_only():
    """Test get_pixel_flux with limb darkening only."""
    star = Star(STAR_RADIUS, BASE_FLUX, limb_darkening_coeffs=(0.5, 0.2))
    
    # At center (r_prime=0, mu=1)
    flux_center = star.get_pixel_flux(x_rel=0.0, y_rel=0.0, time=0.0)
    assert np.isclose(flux_center, star.base_flux * (1 - 0.5*0 - 0.2*0), rtol=1e-5) # Should be base_flux

    # Near limb (e.g., r_prime=0.9, mu=sqrt(1-0.9^2) approx 0.43589)
    # I(mu) = I(1) * [1 - u1*(1-mu) - u2*(1-mu)^2]
    # At r_prime=0.9, x_rel=0.9, y_rel=0.0
    mu = np.sqrt(1.0 - 0.9**2)
    expected_flux_limb = star.base_flux * (1.0 - star.u1 * (1.0 - mu) - star.u2 * (1.0 - mu)**2)
    flux_limb = star.get_pixel_flux(x_rel=0.9, y_rel=0.0, time=0.0)
    assert np.isclose(flux_limb, expected_flux_limb, rtol=1e-5)
    assert flux_limb < flux_center # Should be dimmer at limb

def test_get_pixel_flux_with_flare():
    """
    Test get_pixel_flux correctly applies flare effect.
    """
    star = Star(STAR_RADIUS, BASE_FLUX)
    flare_peak_time = 5.0
    flare_amplitude = 0.1 # 10% relative increase
    flare = star.Flare(flare_time_peak=flare_peak_time, flare_duration_days=0.1, flare_amplitude_relative=flare_amplitude)
    star.add_flare(flare)

    pixel_x_rel, pixel_y_rel = 0.0, 0.0 # Pixel at star center

    # At time without flare
    flux_no_flare = star.get_pixel_flux(pixel_x_rel, pixel_y_rel, time=0.0)
    assert np.isclose(flux_no_flare, star.base_flux)

    # At flare peak time
    flux_at_peak = star.get_pixel_flux(pixel_x_rel, pixel_y_rel, time=flare_peak_time)
    assert np.isclose(flux_at_peak, star.base_flux * (1.0 + flare_amplitude))

    # During flare decay (should be between base_flux and peak flux)
    flux_during_decay = star.get_pixel_flux(pixel_x_rel, pixel_y_rel, time=flare_peak_time + 0.05)
    assert flux_during_decay > star.base_flux
    assert flux_during_decay < flux_at_peak

def test_calculate_rotational_period_at_latitude_rigid_rotation():
    """Test rotation period calculation for rigid rotation (k=0)."""
    star = Star(STAR_RADIUS, BASE_FLUX, rotational_period_equator_days=25.0, differential_rotation_coeff=0.0)
    
    # Should be constant regardless of latitude
    period_equator = star._calculate_rotational_period_at_latitude(np.deg2rad(0))
    period_mid_lat = star._calculate_rotational_period_at_latitude(np.deg2rad(45))
    period_pole = star._calculate_rotational_period_at_latitude(np.deg2rad(90))

    assert np.isclose(period_equator, 25.0)
    assert np.isclose(period_mid_lat, 25.0)
    assert np.isclose(period_pole, 25.0)

def test_calculate_rotational_period_at_latitude_differential_rotation():
    """Test rotation period calculation for differential rotation (k>0)."""
    star = Star(STAR_RADIUS, BASE_FLUX, rotational_period_equator_days=25.0, differential_rotation_coeff=0.1)
    
    period_equator = star._calculate_rotational_period_at_latitude(np.deg2rad(0))
    period_mid_lat = star._calculate_rotational_period_at_latitude(np.deg2rad(30))
    period_high_lat = star._calculate_rotational_period_at_latitude(np.deg2rad(60))

    # Equator should have P_equator
    assert np.isclose(period_equator, 25.0)
    
    # Higher latitudes should have longer periods (slower rotation)
    assert period_mid_lat > period_equator
    assert period_high_lat > period_mid_lat

    # Specific values: P_lat = P_equator / (1 - k * sin^2(lat))
    expected_mid_lat_period = 25.0 / (1 - 0.1 * np.sin(np.deg2rad(30))**2)
    expected_high_lat_period = 25.0 / (1 - 0.1 * np.sin(np.deg2rad(60))**2)
    assert np.isclose(period_mid_lat, expected_mid_lat_period)
    assert np.isclose(period_high_lat, expected_high_lat_period)

def test_get_projected_spot_properties_no_rotation():
    """
    Test spot projection at time=0 (no rotation applied).
    Check x,y coordinates and visibility.
    """
    star = Star(STAR_RADIUS, BASE_FLUX, rotational_period_equator_days=25.0, differential_rotation_coeff=0.0)
    current_time = 0.0

    # Spot at equator, prime meridian (0,0)
    spot_0_0 = Spot(latitude_deg=0.0, longitude_at_epoch_deg=0.0, 
                    radius_umbra=0.1, radius_penumbra=0.2, contrast_umbra=0.1, contrast_penumbra=0.5)
    proj_x, proj_y, _, _, _, _, is_visible = star._get_projected_spot_properties(spot_0_0, current_time)
    assert np.isclose(proj_x, 0.0)
    assert np.isclose(proj_y, 0.0)
    assert is_visible # Should be visible

    # Spot at 45 lat, 90 long (visible, on disk)
    spot_45_90 = Spot(latitude_deg=45.0, longitude_at_epoch_deg=90.0, 
                      radius_umbra=0.1, radius_penumbra=0.2, contrast_umbra=0.1, contrast_penumbra=0.5)
    proj_x, proj_y, _, _, _, _, is_visible = star._get_projected_spot_properties(spot_45_90, current_time)
    # Expected: x = cos(45)sin(90) = 1/sqrt(2), y = sin(45) = 1/sqrt(2)
    assert np.isclose(proj_x, 1/np.sqrt(2))
    assert np.isclose(proj_y, 1/np.sqrt(2))
    assert np.isclose(is_visible, True) # cos(90) is 0, but anything slightly visible is True.

    spot_45_89_9 = Spot(latitude_deg=45.0, longitude_at_epoch_deg=89.9, 
                      radius_umbra=0.1, radius_penumbra=0.2, contrast_umbra=0.1, contrast_penumbra=0.5)
    proj_x, proj_y, _, _, _, _, is_visible = star._get_projected_spot_properties(spot_45_89_9, current_time)
    assert is_visible # Just before limb
    
    spot_45_90_1 = Spot(latitude_deg=45.0, longitude_at_epoch_deg=90.1, 
                      radius_umbra=0.1, radius_penumbra=0.2, contrast_umbra=0.1, contrast_penumbra=0.5)
    proj_x, proj_y, _, _, _, _, is_visible = star._get_projected_spot_properties(spot_45_90_1, current_time)
    assert not is_visible # Just past limb


def test_spot_visibility_over_rotation():
    """Test that spots become visible/invisible as they rotate."""
    star = Star(STAR_RADIUS, BASE_FLUX, rotational_period_equator_days=10.0, differential_rotation_coeff=0.0)
    
    # Spot starting on the far side, at equator
    spot = Spot(latitude_deg=0.0, longitude_at_epoch_deg=180.0, 
                radius_umbra=0.1, radius_penumbra=0.2, contrast_umbra=0.1, contrast_penumbra=0.5)
    
    # At t=0, spot is at longitude 180 (far side)
    _, _, _, _, _, _, is_visible_t0 = star._get_projected_spot_properties(spot, 0.0)
    assert not is_visible_t0 

    # At t=P/4 (2.5 days), spot is at longitude 180+90 = 270 (left limb)
    _, _, _, _, _, _, is_visible_t_P4 = star._get_projected_spot_properties(spot, 2.5)
    assert not is_visible_t_P4 # Still not fully visible (edge-on or just past)

    # At t=P/2 (5 days), spot is at longitude 180+180 = 360/0 (prime meridian, front side)
    _, _, _, _, _, _, is_visible_t_P2 = star._get_projected_spot_properties(spot, 5.0)
    assert is_visible_t_P2 # Should be fully visible

    # At t=3P/4 (7.5 days), spot is at longitude 180+270 = 450/90 (right limb)
    _, _, _, _, _, _, is_visible_t_3P4 = star._get_projected_spot_properties(spot, 7.5)
    assert not is_visible_t_3P4 # Just past right limb


def test_get_pixel_flux_with_rotating_spot():
    """
    Test get_pixel_flux correctly applies spot effect as it rotates into view.
    """
    star = Star(STAR_RADIUS, BASE_FLUX, rotational_period_equator_days=10.0, differential_rotation_coeff=0.0)
    
    # Spot at center, but initially on far side
    spot = Spot(latitude_deg=0.0, longitude_at_epoch_deg=180.0, 
                radius_umbra=0.1, radius_penumbra=0.2, contrast_umbra=0.0, contrast_penumbra=0.0) # Completely dark spot
    star.add_spot(spot)

    pixel_x_rel, pixel_y_rel = 0.0, 0.0 # Pixel at star center

    # At t=0, spot is on far side (longitude 180). Flux at center should be full.
    flux_t0 = star.get_pixel_flux(pixel_x_rel, pixel_y_rel, time=0.0)
    assert np.isclose(flux_t0, star.base_flux) # No spot effect

    # At t=P/2 (5 days), spot has rotated to longitude 0 (front center). Flux at center should be reduced.
    flux_t_P2 = star.get_pixel_flux(pixel_x_rel, pixel_y_rel, time=5.0)
    assert flux_t_P2 < star.base_flux # Spot should reduce flux
    assert np.isclose(flux_t_P2, star.base_flux * spot.contrast_umbra) # Should be umbra contrast

def test_spot_differential_rotation_movement():
    """
    Test that spots at different latitudes move at different rates due to differential rotation.
    """
    # Sun-like differential rotation
    star = Star(STAR_RADIUS, BASE_FLUX, rotational_period_equator_days=25.0, differential_rotation_coeff=0.15) 
    
    # Spot at equator
    spot_equator = Spot(latitude_deg=0.0, longitude_at_epoch_deg=0.0, 
                        radius_umbra=0.1, radius_penumbra=0.2, contrast_umbra=0.1, contrast_penumbra=0.5)
    
    # Spot at 45 degrees latitude
    spot_mid_lat = Spot(latitude_deg=45.0, longitude_at_epoch_deg=0.0, 
                        radius_umbra=0.1, radius_penumbra=0.2, contrast_umbra=0.1, contrast_penumbra=0.5)
    
    # Advance time by one equatorial rotation period
    time_advance = star.rotational_period_equator_days
    
    # Get current longitudes (not projected x/y) for verification of rotation
    P_eq = star.rotational_period_equator_days # Period at equator
    P_mid = star._calculate_rotational_period_at_latitude(np.deg2rad(spot_mid_lat.latitude_deg)) # Period at mid-lat
    
    # Longitude after one equatorial period
    lon_equator_final_deg = spot_equator.longitude_at_epoch_deg + (time_advance / P_eq) * 360.0
    lon_mid_lat_final_deg = spot_mid_lat.longitude_at_epoch_deg + (time_advance / P_mid) * 360.0

    # The equatorial spot should have completed a full rotation (or multiple of 360)
    assert np.isclose(lon_equator_final_deg % 360.0, spot_equator.longitude_at_epoch_deg % 360.0, atol=1e-5), \
        "Equatorial spot should return to original longitude after one equatorial period."

    # The mid-latitude spot should NOT have returned to its original longitude relative to the prime meridian
    # if differential rotation is present. It should have fallen behind.
    relative_rotation_equator = (time_advance / P_eq) * 360.0
    relative_rotation_mid_lat = (time_advance / P_mid) * 360.0
    
    # The mid-latitude spot should have rotated LESS (smaller angle) than the equatorial spot
    # for positive differential rotation coefficient.
    assert relative_rotation_mid_lat < relative_rotation_equator, \
        "Mid-latitude spot should have rotated less than equatorial spot due to differential rotation."

    # Check that their projected positions on the disk are different (meaning they moved relative to each other)
    # This checks that the projection function uses the updated longitude.
    # It's an indirect check, but better than trying to invert projection accurately.
    proj_x_eq_t0, proj_y_eq_t0, _, _, _, _, _ = star._get_projected_spot_properties(spot_equator, 0.0)
    proj_x_mid_t0, proj_y_mid_t0, _, _, _, _, _ = star._get_projected_spot_properties(spot_mid_lat, 0.0)
    
    proj_x_eq_t_adv, proj_y_eq_t_adv, _, _, _, _, _ = star._get_projected_spot_properties(spot_equator, time_advance)
    proj_x_mid_t_adv, proj_y_mid_t_adv, _, _, _, _, _ = star._get_projected_spot_properties(spot_mid_lat, time_advance)

    # Equatorial spot should return to roughly its initial projected position
    assert np.isclose(proj_x_eq_t_adv, proj_x_eq_t0)
    assert np.isclose(proj_y_eq_t_adv, proj_y_eq_t0) # y-position depends only on latitude, which is constant

    # Mid-latitude spot should NOT return to its initial projected position, relative to central meridian
    # It will have a different projected_x because its longitude is different.
    assert not np.isclose(proj_x_mid_t_adv, proj_x_mid_t0) or \
           not np.isclose(proj_y_mid_t_adv, proj_y_mid_t0) # y-position depends only on latitude