# pyexops/planet.py

import numpy as np

class Planet:
    """Represents an orbiting planet."""
    def __init__(self, radius: float, period: float, semimajor_axis: float, 
                 inclination: float, epoch_transit: float):
        """
        Initializes the planet.
        :param radius: Radius of the planet, in units of stellar radii.
        :param period: Orbital period in consistent time units (e.g., days).
        :param semimajor_axis: Semi-major axis, in units of stellar radii.
        :param inclination: Orbital inclination in degrees (90 deg for edge-on transit).
        :param epoch_transit: Time of mid-transit (in consistent time units).
        """
        self.radius = radius
        self.period = period
        self.semimajor_axis = semimajor_axis
        self.inclination_rad = np.deg2rad(inclination)
        self.epoch_transit = epoch_transit

    def get_position_at_time(self, time: float) -> tuple:
        """
        Calculates the x, y position of the planet relative to the star's center
        in the plane of the sky.
        :param time: Current time in the same units as period and epoch_transit.
        :return: (x_planet, y_planet) in units of stellar radii.
        """
        phase = 2 * np.pi * ((time - self.epoch_transit) / self.period)

        x_orbital = self.semimajor_axis * np.sin(phase)
        z_orbital = self.semimajor_axis * np.cos(phase) 
        
        x_planet_stellar_radii = x_orbital
        y_planet_stellar_radii = z_orbital * np.cos(self.inclination_rad)
        
        return x_planet_stellar_radii, y_planet_stellar_radii