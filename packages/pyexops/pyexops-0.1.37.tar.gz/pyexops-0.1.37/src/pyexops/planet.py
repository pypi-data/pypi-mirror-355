# pyexops/src/pyexops/planet.py

import numpy as np
from typing import Optional, Tuple

# TYPE_CHECKING is used to avoid circular imports during runtime while allowing type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .atmosphere import Atmosphere 

class Planet:
    """Represents an orbiting planet."""
    def __init__(self, radius: float, period: float, semimajor_axis: float, 
                 inclination: float, epoch_transit: float,
                 planet_mass: float, 
                 eccentricity: float = 0.0, 
                 argument_of_periastron: float = 90.0,
                 albedo: float = 0.5,
                 atmosphere: Optional['Atmosphere'] = None,
                 host_star_index: int = 0): # NEW: host_star_index
        """
        Initializes the planet.

        :param radius: Radius of the planet, in units of stellar radii (of its host star). This is the solid radius.
        :param period: Orbital period in consistent time units (e.g., days).
        :param semimajor_axis: Semi-major axis, in units of stellar radii (of its host star).
        :param inclination: Orbital inclination in degrees (90 deg for edge-on transit).
        :param epoch_transit: Time of mid-transit (in consistent time units).
        :param planet_mass: Mass of the planet, in units of Jupiter masses (M_Jup) or Earth masses (M_Earth).
        :param eccentricity: Orbital eccentricity (0.0 for circular).
        :param argument_of_periastron: Argument of periastron in degrees. For circular orbits, usually 90 degrees for a transit.
        :param albedo: Albedo (reflectivity) of the planet's atmosphere/surface (0.0 for completely dark, 1.0 for perfect reflection).
        :param atmosphere: An optional Atmosphere object defining the planet's atmospheric transmission.
                           If None, the planet has no atmospheric effects on transit depth.
        :param host_star_index: Index (0 or 1 for binary systems) indicating which star this planet orbits.
                                Defaults to 0 (primary star).
        :raises ValueError: If atmosphere's solid radius does not match planet's radius.
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
        self.atmosphere = atmosphere 
        self.host_star_index = host_star_index # Store host star index

        if self.atmosphere is not None and self.atmosphere.planet_solid_radius_stellar_radii != self.radius:
            raise ValueError("Atmosphere's solid radius must match Planet's radius.")

    def get_position_at_time(self, time: float, 
                             host_star_current_x_bary: float = 0.0, # NEW: Host star's X relative to system barycenter
                             host_star_current_y_bary: float = 0.0  # NEW: Host star's Y relative to system barycenter
                            ) -> Tuple[float, float, float]: # NEW: Return x, y, and z_los
        """
        Calculates the x, y, z position of the planet relative to the system's barycenter.

        The planet's position is calculated relative to its host star's center,
        and then offset by the host star's barycentric position.

        :param time: Current time in the same units as period and epoch_transit.
        :param host_star_current_x_bary: The x-position of the host star relative to the system barycenter.
        :param host_star_current_y_bary: The y-position of the host star relative to the system barycenter.
        :return: (x_planet_bary, y_planet_bary, z_planet_bary) in units of stellar radii (of the planet's host).
                 (x_planet_bary, y_planet_bary) are in the plane of the sky. z_planet_bary is along the line of sight.
        """
        # Phase relative to transit epoch
        mean_anomaly = 2 * np.pi * ((time - self.epoch_transit) / self.period)

        # Solve Kepler's equation for Eccentric Anomaly (E)
        from .orbital_solver import OrbitalSolver # Import locally
        eccentric_anomaly = OrbitalSolver._solve_kepler_equation(mean_anomaly, self.eccentricity)

        # Calculate True Anomaly (f) from Eccentric Anomaly (E)
        true_anomaly = 2 * np.arctan2(np.sqrt(1 + self.eccentricity) * np.sin(eccentric_anomaly / 2),
                                     np.sqrt(1 - self.eccentricity) * np.cos(eccentric_anomaly / 2))

        # Instantaneous distance from host star (r)
        r = self.semimajor_axis * (1 - self.eccentricity**2) / (1 + self.eccentricity * np.cos(true_anomaly))

        # Calculate position of planet relative to its host star in the sky plane (x_rel_host, y_rel_host)
        # and along the line of sight (z_rel_host).
        # Assuming periastron at argument_of_periastron_rad.
        # x_orbital: coordinate along the line of nodes (projected along sky x-axis)
        # y_orbital: coordinate in the orbital plane, perpendicular to x_orbital
        # z_orbital: coordinate along the line of sight
        
        # Position in orbital plane relative to host star
        # (r * cos(f), r * sin(f)) adjusted for argument of periastron (omega)
        angle_in_orbital_plane = true_anomaly + self.argument_of_periastron_rad

        x_rel_host = r * np.sin(angle_in_orbital_plane)
        y_rel_host = -r * np.cos(angle_in_orbital_plane) * np.cos(self.inclination_rad)
        z_rel_host = -r * np.cos(angle_in_orbital_plane) * np.sin(self.inclination_rad)

        # Add host star's barycentric position to get planet's position relative to system barycenter
        x_planet_bary = host_star_current_x_bary + x_rel_host
        y_planet_bary = host_star_current_y_bary + y_rel_host
        z_planet_bary = z_rel_host # For a planet orbiting a star, its Z is relative to that star. The star's Z is also needed.

        return float(x_planet_bary), float(y_planet_bary), float(z_planet_bary)