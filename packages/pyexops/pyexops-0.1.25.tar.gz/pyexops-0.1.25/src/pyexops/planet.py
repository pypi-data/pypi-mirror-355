# pyexops/src/pyexops/planet.py

import numpy as np
from typing import Optional
from .atmosphere import Atmosphere # Import Atmosphere for type hinting

class Planet:
    """Represents an orbiting planet."""
    def __init__(self, radius: float, period: float, semimajor_axis: float, 
                 inclination: float, epoch_transit: float,
                 planet_mass: float, 
                 eccentricity: float = 0.0, 
                 argument_of_periastron: float = 90.0,
                 albedo: float = 0.5,
                 atmosphere: Optional[Atmosphere] = None): # NEW: atmosphere object
        """
        Initializes the planet.
        :param radius: Radius of the planet, in units of stellar radii. This is the solid radius.
        :param period: Orbital period in consistent time units (e.g., days).
        :param semimajor_axis: Semi-major axis, in units of stellar radii.
        :param inclination: Orbital inclination in degrees (90 deg for edge-on transit).
        :param epoch_transit: Time of mid-transit (in consistent time units).
        :param planet_mass: Mass of the planet, in units of Jupiter masses (M_Jup) or Earth masses (M_Earth).
        :param eccentricity: Orbital eccentricity (0.0 for circular).
        :param argument_of_periastron: Argument of periastron in degrees. For circular orbits, usually 90 degrees for a transit.
        :param albedo: Albedo (reflectivity) of the planet's atmosphere/surface (0.0 for black, 1.0 for perfect reflection).
        :param atmosphere: An optional Atmosphere object defining the planet's atmospheric transmission.
                           If None, the planet has no atmospheric effects on transit depth.
        """
        self.radius = radius # This is the solid radius
        self.period = period
        self.semimajor_axis = semimajor_axis
        self.inclination_rad = np.deg2rad(inclination)
        self.epoch_transit = epoch_transit
        self.planet_mass = planet_mass 
        self.eccentricity = eccentricity 
        self.argument_of_periastron_rad = np.deg2rad(argument_of_periastron) 
        self.albedo = albedo 
        self.atmosphere = atmosphere # Store atmosphere object

        if self.atmosphere is not None and self.atmosphere.planet_solid_radius_stellar_radii != self.radius:
            raise ValueError("Atmosphere's solid radius must match Planet's radius.")

    def get_position_at_time(self, time: float) -> tuple:
        """
        Calculates the x, y position of the planet relative to the star's center
        in the plane of the sky for a circular orbit.
        :param time: Current time in the same units as period and epoch_transit.
        :return: (x_planet, y_planet) in units of stellar radii.
        """
        # Note: This method calculates the 2D projected position of the planet's *center*.
        # The effective radius for occultation (due to atmosphere) is handled in Scene.
        phase = 2 * np.pi * ((time - self.epoch_transit) / self.period)

        x_orbital = self.semimajor_axis * np.sin(phase)
        z_orbital = self.semimajor_axis * np.cos(phase) 
        
        x_planet_stellar_radii = x_orbital
        y_planet_stellar_radii = z_orbital * np.cos(self.inclination_rad)
        
        return x_planet_stellar_radii, y_planet_stellar_radii