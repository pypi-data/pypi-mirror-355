# pyexops/src/pyexops/star.py

import numpy as np
from typing import List, Tuple, Optional

class Star:
    """Represents the host star with limb darkening, dynamic spots, and flare activity."""
    def __init__(self, radius: float, base_flux: float, limb_darkening_coeffs: Tuple[float, float] = (0.5, 0.2),
                 star_mass: float = 1.0,
                 rotational_period_equator_days: float = 25.0, # Equatorial rotation period in days
                 differential_rotation_coeff: float = 0.0): # Differential rotation coefficient (k)
        """
        Initializes the star.
        :param radius: Radius of the star. In this simulator, this will implicitly be in "pixels"
                       or a consistent unit that determines its apparent size on the image.
        :param base_flux: Maximum flux of the star at its center (arbitrary units).
        :param limb_darkening_coeffs: (u1, u2) for quadratic limb darkening model:
                                      I(mu) = I(1) * [1 - u1*(1-mu) - u2*(1-mu)^2]
        :param star_mass: Mass of the star, in solar masses (M_sun). Defaults to 1.0.
        :param rotational_period_equator_days: Sidereal rotation period at the equator in days.
        :param differential_rotation_coeff: Coefficient 'k' for differential rotation (e.g., for Sun, k~0.15).
                                            P_lat = P_equator / (1 - k * sin^2(latitude_rad)).
        """
        self.radius = radius
        self.base_flux = base_flux
        self.u1, self.u2 = limb_darkening_coeffs
        self.star_mass = star_mass 
        self.rotational_period_equator_days = rotational_period_equator_days
        self.differential_rotation_coeff = differential_rotation_coeff
        self.spots: List[Spot] = [] # List of Spot objects
        self.flares: List[self.Flare] = [] # List of Flare objects (using inner class)

    def add_spot(self, spot: 'Spot'):
        """Adds a spot to the star's surface."""
        self.spots.append(spot)

    def add_flare(self, flare: 'Star.Flare'): # Type hint using 'Star.Flare' or 'self.Flare'
        """Adds a flare event to the star."""
        self.flares.append(flare)

    def _calculate_rotational_period_at_latitude(self, latitude_rad: float) -> float:
        """
        Calculates the rotation period at a given latitude, considering differential rotation.
        :param latitude_rad: Latitude in radians.
        :return: Rotation period at that latitude in days.
        """
        if self.rotational_period_equator_days <= 0:
            return np.inf # Effectively no rotation if period is zero or negative

        # Standard differential rotation law: P_lat = P_equator / (1 - k * sin^2(latitude_rad))
        sin_sq_lat = np.sin(latitude_rad)**2
        denominator = (1 - self.differential_rotation_coeff * sin_sq_lat)
        
        if denominator <= 1e-6: # Avoid division by zero or very small numbers
            return np.inf # Effectively no rotation or extremely long period
            
        return self.rotational_period_equator_days / denominator

    def _get_projected_spot_properties(self, spot: 'Spot', current_time_days: float) -> Tuple[float, float, float, float, float, float, bool]:
        """
        Calculates the current projected 2D coordinates and visibility of a spot,
        considering stellar rotation and differential rotation.
        Assumes the observer is looking at the stellar equator, and the rotation axis is aligned with the image Y-axis.

        :param spot: The Spot object.
        :param current_time_days: The current time in days.
        :return: (projected_x_rel, projected_y_rel, umbra_radius, penumbra_radius, umbra_contrast, penumbra_contrast, is_visible)
                 Coordinates are relative to the star's center in stellar radii.
        """
        latitude_rad = np.deg2rad(spot.latitude_deg)

        # Calculate rotation period at spot's latitude
        P_lat = self._calculate_rotational_period_at_latitude(latitude_rad)

        # Calculate current longitude based on time and rotation period
        current_longitude_deg = spot.longitude_at_epoch_deg + (current_time_days / P_lat) * 360.0
        current_longitude_deg %= 360.0 # Normalize to [0, 360)

        current_longitude_rad = np.deg2rad(current_longitude_deg)

        # Project spherical coordinates onto a 2D disk
        # Assuming star's rotation axis is aligned with Y-axis in image.
        projected_center_x_rel = np.cos(latitude_rad) * np.sin(current_longitude_rad)
        projected_center_y_rel = np.sin(latitude_rad)

        # Determine visibility: A spot is visible if its cosine of longitude is positive
        # (i.e., it's on the hemisphere facing the observer).
        is_visible = np.cos(current_longitude_rad) > 0

        # For simplicity, ignoring foreshortening of spot radii for now.
        return (float(projected_center_x_rel), float(projected_center_y_rel),
                spot.radius_umbra, spot.radius_penumbra, 
                spot.contrast_umbra, spot.contrast_penumbra, is_visible)

    def get_pixel_flux(self, x_rel: float, y_rel: float, time: float) -> float:
        """
        Calculates the flux of a single point (pixel) on the star's surface,
        relative to the star's center. Accounts for limb darkening, dynamic spots, and flares.
        :param x_rel, y_rel: Coordinates relative to the star's center, in units of stellar radii.
        :param time: Current time in days, used to determine spot positions and flare contributions.
        :return: Flux value at that point.
        """
        r_prime = np.sqrt(x_rel**2 + y_rel**2) 

        if r_prime > 1.0: 
            return 0.0

        # Calculate limb darkening
        mu = np.sqrt(1.0 - r_prime**2) 
        limb_darkened_flux = self.base_flux * (1.0 - self.u1 * (1.0 - mu) - self.u2 * (1.0 - mu)**2)

        # Apply spot effects
        spot_flux_factor = 1.0
        for spot in self.spots:
            proj_x, proj_y, r_umbra, r_penumbra, c_umbra, c_penumbra, is_visible = \
                self._get_projected_spot_properties(spot, time)
            
            if is_visible:
                dist_from_spot_center = np.sqrt((x_rel - proj_x)**2 + (y_rel - proj_y)**2)

                if dist_from_spot_center <= r_umbra:
                    current_spot_factor = c_umbra
                elif dist_from_spot_center <= r_penumbra:
                    if r_penumbra == r_umbra: 
                        current_spot_factor = c_umbra 
                    else:
                        # Linear interpolation in penumbra
                        current_spot_factor = c_umbra + (1.0 - c_umbra) * \
                                              (dist_from_spot_center - r_umbra) / \
                                              (r_penumbra - r_umbra)
                else:
                    current_spot_factor = 1.0 # Outside this spot

                spot_flux_factor *= current_spot_factor
        
        # Calculate total flux after spots
        total_flux = limb_darkened_flux * spot_flux_factor

        # Apply flare effects
        flare_contribution_relative = 0.0
        for flare in self.flares:
            flare_contribution_relative += flare.get_flux_contribution(time)
        
        # Flares add flux multiplicatively to the star's current brightness (including limb-darkening/spots)
        total_flux *= (1.0 + flare_contribution_relative)

        return float(total_flux)

    class Flare:
        """
        Represents a single stellar flare event.
        Models a rapid rise and exponential decay.
        """
        def __init__(self, flare_time_peak: float, flare_duration_days: float, 
                     flare_amplitude_relative: float, flare_shape: str = 'exponential_decay'):
            """
            Initializes a stellar flare.
            :param flare_time_peak: Time (in days) when the flare reaches its peak brightness.
            :param flare_duration_days: The characteristic duration of the flare in days (primarily decay time).
            :param flare_amplitude_relative: The amplitude of the flare at its peak, relative to the star's
                                             base flux (e.g., 0.1 for 10% increase).
            :param flare_shape: The shape model for the flare ('exponential_decay').
                                 Currently, only 'exponential_decay' is implemented.
            """
            self.flare_time_peak = flare_time_peak
            self.flare_duration_days = flare_duration_days
            self.flare_amplitude_relative = flare_amplitude_relative
            self.flare_shape = flare_shape

            if self.flare_shape not in ['exponential_decay']:
                raise ValueError(f"Flare shape '{flare_shape}' not supported. Choose from 'exponential_decay'.")

        def get_flux_contribution(self, current_time: float) -> float:
            """
            Calculates the relative increase in stellar flux due to this flare at a given time.
            :param current_time: The current time in days.
            :return: Relative flux increase (e.g., 0.05 for 5% increase). Returns 0.0 if flare is not active.
            """
            if self.flare_shape == 'exponential_decay':
                # Simplified flare model: rapid rise, exponential decay.
                # Rise phase: 10% of duration
                # Decay phase: 90% of duration
                
                # Characteristic time scales
                rise_time = self.flare_duration_days * 0.1
                decay_time = self.flare_duration_days * 0.9

                flare_start_time = self.flare_time_peak - rise_time

                if current_time < flare_start_time:
                    return 0.0
                elif current_time < self.flare_time_peak:
                    # Linear rise from 0 to peak amplitude
                    time_into_rise = current_time - flare_start_time
                    return self.flare_amplitude_relative * (time_into_rise / rise_time)
                else: # current_time >= self.flare_time_peak (decay phase)
                    # Exponential decay
                    time_after_peak = current_time - self.flare_time_peak
                    # Decay constant (tau) such that flux is near zero after decay_time
                    # e^(-time_after_peak / tau)
                    # Let's say it decays to ~1% of peak after decay_time. exp(-decay_time / tau) = 0.01
                    # -decay_time / tau = ln(0.01) approx -4.6
                    # tau = decay_time / 4.6
                    tau = decay_time / 3.0 # Adjusted for a visually pleasing decay

                    flux_increase = self.flare_amplitude_relative * np.exp(-time_after_peak / tau)
                    
                    # Ensure flare effectively ends
                    if time_after_peak > (decay_time * 2): # Cutoff after substantial decay
                        return 0.0
                    return float(flux_increase)
            else:
                return 0.0 # Should not happen due to ValueError check in __init__


class Spot:
    """
    Represents a single stellar spot (umbra + penumbra).
    Position is defined by spherical coordinates (latitude, longitude_at_epoch).
    """
    def __init__(self, latitude_deg: float, longitude_at_epoch_deg: float, 
                 radius_umbra: float, radius_penumbra: float, 
                 contrast_umbra: float, contrast_penumbra: float):
        """
        Initializes a stellar spot.
        :param latitude_deg: Latitude of the spot in degrees relative to the stellar equator.
        :param longitude_at_epoch_deg: Longitude of the spot in degrees at a reference epoch (e.g., time=0).
        :param radius_umbra: Radius of the umbra (darkest part) in stellar radii.
        :param radius_penumbra: Radius of the penumbra (fainter outer part) in stellar radii.
        :param contrast_umbra: Flux reduction factor in the umbra (0.0 for completely dark, 1.0 for normal flux).
        :param contrast_penumbra: Flux reduction factor in the penumbra.
        """
        self.latitude_deg = latitude_deg
        self.longitude_at_epoch_deg = longitude_at_epoch_deg
        self.radius_umbra = radius_umbra
        self.radius_penumbra = radius_penumbra
        self.contrast_umbra = contrast_umbra
        self.contrast_penumbra = contrast_penumbra