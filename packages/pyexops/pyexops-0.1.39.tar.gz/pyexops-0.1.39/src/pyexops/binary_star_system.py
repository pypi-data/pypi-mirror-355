# pyexops/src/pyexops/binary_star_system.py

import numpy as np
from typing import Tuple, TYPE_CHECKING

# TYPE_CHECKING is used to avoid circular imports during runtime while allowing type hints
if TYPE_CHECKING:
    from .star import Star
    from .orbital_solver import OrbitalSolver 

class BinaryStarSystem:
    """
    Represents a binary star system, managing the properties and orbital dynamics
    of two stars orbiting their common barycenter.
    """
    def __init__(self, star1: 'Star', star2: 'Star',
                 period_days: float, semimajor_axis_stellar_radii: float,
                 inclination_deg: float, eccentricity: float = 0.0,
                 argument_of_periastron_deg: float = 90.0, epoch_periastron_days: float = 0.0):
        """
        Initializes the binary star system.

        :param star1: The primary Star object.
        :param star2: The secondary Star object.
        :param period_days: Orbital period of the binary system in days.
        :param semimajor_axis_stellar_radii: Semi-major axis of the binary system in stellar radii (relative to star1.radius).
                                             This defines the total separation 'a'.
        :param inclination_deg: Orbital inclination of the binary system in degrees relative to the observer's line of sight.
                                90 degrees for edge-on (eclipsing) binary.
        :param eccentricity: Orbital eccentricity of the binary system (0.0 for circular).
        :param argument_of_periastron_deg: Argument of periastron in degrees for the binary orbit.
                                           Typically 90 degrees for primary transit/eclipse in an eccentric transiting system.
        :param epoch_periastron_days: Time (in days) of periastron passage for the binary orbit.
                                      If eccentricity is 0, this can be considered epoch of conjunction.
        :raises ValueError: If masses are invalid or semimajor_axis is non-positive.
        """
        if star1.star_mass <= 0 or star2.star_mass <= 0:
            raise ValueError("Both stars in a binary system must have positive masses.")
        if period_days <= 0:
            raise ValueError("Binary period must be positive.")
        if semimajor_axis_stellar_radii <= 0:
            raise ValueError("Binary semi-major axis must be positive.")

        self.star1 = star1
        self.star2 = star2
        
        self.period_days = period_days
        self.semimajor_axis_stellar_radii = semimajor_axis_stellar_radii
        self.inclination_deg = inclination_deg
        self.eccentricity = eccentricity
        self.argument_of_periastron_deg = argument_of_periastron_deg
        self.epoch_periastron_days = epoch_periastron_days

        # Calculate total mass and mass ratio for barycentric calculations
        self.total_mass_solar = self.star1.star_mass + self.star2.star_mass
        self.mass_ratio = self.star2.star_mass / self.star1.star_mass # m2/m1

        # Calculate individual semi-major axes relative to the barycenter
        # a1 = a * m2 / (m1 + m2)
        # a2 = a * m1 / (m1 + m2)
        self.semimajor_axis_star1_bary = self.semimajor_axis_stellar_radii * self.star2.star_mass / self.total_mass_solar
        self.semimajor_axis_star2_bary = self.semimajor_axis_stellar_radii * self.star1.star_mass / self.total_mass_solar


    def get_star_barycentric_positions_at_time(self, times_days: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculates the 2D projected (x, y) positions and the line-of-sight (z) distance
        of Star1 and Star2 relative to the system's barycenter at given times.

        This method encapsulates the orbital solution for the binary system.

        :param times_days: An array of time points in days.
        :return: A tuple (x1_bary_proj, y1_bary_proj, z1_bary_los,
                          x2_bary_proj, y2_bary_proj, z2_bary_los)
                 where coordinates are numpy arrays in stellar radii (consistent with semimajor_axis_stellar_radii).
                 (x_proj, y_proj) are in the plane of the sky, z_los is along the line of sight.
        """
        from .orbital_solver import OrbitalSolver # Import locally to avoid circular dependency

        # Ensure times_days is an array for vectorized operations
        times_days = np.atleast_1d(times_days)

        # Calculate Mean Anomaly relative to periastron
        mean_anomaly = 2 * np.pi * (times_days - self.epoch_periastron_days) / self.period_days

        # Solve Kepler's equation for Eccentric Anomaly (E)
        eccentric_anomaly = OrbitalSolver._solve_kepler_equation(mean_anomaly, self.eccentricity)

        # Calculate True Anomaly (f) from Eccentric Anomaly (E)
        true_anomaly = 2 * np.arctan2(np.sqrt(1 + self.eccentricity) * np.sin(eccentric_anomaly / 2),
                                      np.sqrt(1 - self.eccentricity) * np.cos(eccentric_anomaly / 2))

        # Calculate the instantaneous orbital radius from barycenter for each star
        r1_bary = self.semimajor_axis_star1_bary * (1 - self.eccentricity**2) / (1 + self.eccentricity * np.cos(true_anomaly))
        r2_bary = self.semimajor_axis_star2_bary * (1 - self.eccentricity**2) / (1 + self.eccentricity * np.cos(true_anomaly))
        
        # Convert inclination and argument of periastron to radians
        inclination_rad = np.deg2rad(self.inclination_deg)
        argument_of_periastron_rad = np.deg2rad(self.argument_of_periastron_deg)

        # Angle in orbital plane (f + omega)
        angle_in_orbital_plane = true_anomaly + argument_of_periastron_rad

        # Projected X, Y positions on sky plane and Z along line of sight for each star
        # Convention: X-axis along ascending node, Y in sky plane, Z along line of sight (positive away from observer)

        # Star1's positions
        x1_bary_proj = r1_bary * np.sin(angle_in_orbital_plane)
        y1_bary_proj = r1_bary * np.cos(angle_in_orbital_plane) * np.cos(inclination_rad)
        z1_bary_los  = r1_bary * np.cos(angle_in_orbital_plane) * np.sin(inclination_rad)

        # Star2's positions (opposite direction from barycenter)
        x2_bary_proj = -r2_bary * np.sin(angle_in_orbital_plane)
        y2_bary_proj = -r2_bary * np.cos(angle_in_orbital_plane) * np.cos(inclination_rad)
        z2_bary_los  = -r2_bary * np.cos(angle_in_orbital_plane) * np.sin(inclination_rad)

        return (x1_bary_proj.astype(np.float64), y1_bary_proj.astype(np.float64), z1_bary_los.astype(np.float64),
                x2_bary_proj.astype(np.float64), y2_bary_proj.astype(np.float64), z2_bary_los.astype(np.float64))