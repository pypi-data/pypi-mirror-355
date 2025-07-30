# pyexops/src/pyexops/planet.py

import numpy as np

class Planet:
    """Represents an orbiting planet."""
    def __init__(self, radius: float, period: float, semimajor_axis: float, 
                 inclination: float, epoch_transit: float,
                 planet_mass: float, 
                 eccentricity: float = 0.0, 
                 argument_of_periastron: float = 90.0):
        """
        Initializes the planet.
        :param radius: Radius of the planet, in units of stellar radii.
        :param period: Orbital period in consistent time units (e.g., days).
        :param semimajor_axis: Semi-major axis, in units of stellar radii.
        :param inclination: Orbital inclination in degrees (90 deg for edge-on transit).
        :param epoch_transit: Time of mid-transit (in consistent time units).
        :param planet_mass: Mass of the planet, in units of Jupiter masses (M_Jup) or Earth masses (M_Earth).
        :param eccentricity: Orbital eccentricity (0.0 for circular).
        :param argument_of_periastron: Argument of periastron in degrees. For circular orbits, usually 90 degrees for a transit.
        """
        self.radius = radius
        self.period = period
        self.semimajor_axis = semimajor_axis
        self.inclination_rad = np.deg2rad(inclination)
        self.epoch_transit = epoch_transit
        self.planet_mass = planet_mass 
        self.eccentricity = eccentricity 
        self.argument_of_periastron_rad = np.deg2rad(argument_of_periastron) 

    def get_position_at_time(self, time: float) -> tuple:
        """
        Calculates the x, y position of the planet relative to the star's center
        in the plane of the sky for a circular orbit.
        :param time: Current time in the same units as period and epoch_transit.
        :return: (x_planet, y_planet) in units of stellar radii.
        """
        # For now, this method remains circular. The RV calculation will handle eccentricity.
        # This is acceptable, as the 2D position for image rendering still uses a simplified circular projection.
        # A more advanced scene rendering could consider the elliptical projection, but it is more complex.
        # For RV, we will use the full orbital mechanics.
        phase = 2 * np.pi * ((time - self.epoch_transit) / self.period)

        x_orbital = self.semimajor_axis * np.sin(phase)
        z_orbital = self.semimajor_axis * np.cos(phase) 
        
        x_planet_stellar_radii = x_orbital
        y_planet_stellar_radii = z_orbital * np.cos(self.inclination_rad)
        
        return x_planet_stellar_radii, y_planet_stellar_radii