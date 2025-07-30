# pyexops/src/pyexops/binary_star_system.py

import numpy as np
from typing import Tuple, TYPE_CHECKING

# TYPE_CHECKING is used to avoid circular imports during runtime while allowing type hints
if TYPE_CHECKING:
    from .star import Star
    from .orbital_solver import OrbitalSolver # For using solve_kepler_equation if needed internally

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
        # a1 * m1 = a2 * m2  and a1 + a2 = a
        # a1 = a * m2 / (m1 + m2)
        # a2 = a * m1 / (m1 + m2)
        self.semimajor_axis_star1_bary = self.semimajor_axis_stellar_radii * self.star2.star_mass / self.total_mass_solar
        self.semimajor_axis_star2_bary = self.semimajor_axis_stellar_radii * self.star1.star_mass / self.total_mass_solar


    def get_star_barycentric_positions_at_time(self, time_days: float) -> Tuple[float, float, float, float, float, float]:
        """
        Calculates the 2D projected (x, y) positions and the line-of-sight (z) distance
        of Star1 and Star2 relative to the system's barycenter at a given time.

        This method encapsulates the orbital solution for the binary system.

        :param time_days: The current time in days.
        :return: A tuple (x1_bary_proj, y1_bary_proj, z1_bary_los,
                          x2_bary_proj, y2_bary_proj, z2_bary_los)
                 where coordinates are in stellar radii (consistent with semimajor_axis_stellar_radii).
                 (x_proj, y_proj) are in the plane of the sky, z_los is along the line of sight.
        """
        from .orbital_solver import OrbitalSolver # Import locally to avoid circular dependency in type hints

        # Calculate Mean Anomaly relative to periastron
        mean_anomaly = 2 * np.pi * (time_days - self.epoch_periastron_days) / self.period_days

        # Solve Kepler's equation for Eccentric Anomaly (E)
        eccentric_anomaly = OrbitalSolver._solve_kepler_equation(mean_anomaly, self.eccentricity)

        # Calculate True Anomaly (f) from Eccentric Anomaly (E)
        true_anomaly = 2 * np.arctan2(np.sqrt(1 + self.eccentricity) * np.sin(eccentric_anomaly / 2),
                                      np.sqrt(1 - self.eccentricity) * np.cos(eccentric_anomaly / 2))

        # Calculate the instantaneous orbital separation (r) from periastron
        # r = a * (1 - e^2) / (1 + e * cos(f))
        current_separation = self.semimajor_axis_stellar_radii * (1 - self.eccentricity**2) / (1 + self.eccentricity * np.cos(true_anomaly))

        # Convert inclination and argument of periastron to radians
        inclination_rad = np.deg2rad(self.inclination_deg)
        argument_of_periastron_rad = np.deg2rad(self.argument_of_periastron_deg)

        # Calculate the position of star1 relative to the barycenter in its own orbital plane (x_orb, y_orb)
        # and its z component (line of sight).
        # We assume the orbital plane is defined by X (along periastron) and Y (90 deg from periastron)
        # Position in orbital plane relative to barycenter
        # Star1 is on one side, Star2 on the other.
        # x_orbital = -a1 * cos(true_anomaly)   (relative to barycenter)
        # y_orbital = -a1 * sin(true_anomaly)
        # Let's use a standard orbital coordinate system: periastron at f=0.
        # r * cos(f) is distance along line to periastron. r * sin(f) is perpendicular.
        # x_plane = r * cos(f)
        # y_plane = r * sin(f)

        # Position of Star1 relative to Barycenter
        # In a standard setup, at true_anomaly=0 (periastron), star1 and star2 are furthest apart.
        # Let's align the X-axis of the binary's orbital plane with the argument of periastron.
        # Position of M1 relative to barycenter:
        r1 = self.semimajor_axis_star1_bary * (1 - self.eccentricity**2) / (1 + self.eccentricity * np.cos(true_anomaly))
        
        # Orbital coordinates relative to barycenter (X_orb, Y_orb) for star1
        # X_orb is along the line of nodes (where the orbital plane intersects the plane of sky)
        # Y_orb is perpendicular in the orbital plane
        # For simplicity, let's derive coordinates directly in observer's frame (x,y,z)
        
        # Position in orbit (from barycenter): (r * cos(f), r * sin(f)) in orbital plane relative to periastron.
        # Adjust for argument of periastron (omega): f' = f + omega
        angle_in_orbital_plane = true_anomaly + argument_of_periastron_rad

        # Projected X, Y positions on sky plane and Z along line of sight for separation (relative to barycenter)
        # For Star1, it's r1, for Star2, it's r2. r1 + r2 = current_separation
        r2 = current_separation - r1

        # Projected position of Star1 on sky plane (x, y) and along line of sight (z)
        x1_bary_proj = -r1 * np.sin(angle_in_orbital_plane)
        y1_bary_proj = -r1 * np.cos(angle_in_orbital_plane) * np.cos(inclination_rad)
        z1_bary_los  = -r1 * np.cos(angle_in_orbital_plane) * np.sin(inclination_rad)

        # Projected position of Star2 on sky plane (x, y) and along line of sight (z)
        # Star2 is 180 degrees (pi radians) opposite to Star1 relative to barycenter
        x2_bary_proj = -x1_bary_proj * (r2 / r1) if r1 > 0 else 0.0 # Maintain ratio for current separation
        y2_bary_proj = -y1_bary_proj * (r2 / r1) if r1 > 0 else 0.0
        z2_bary_los  = -z1_bary_los  * (r2 / r1) if r1 > 0 else 0.0
        
        # It's typical for the Z-axis to point towards the observer.
        # If z is positive, the object is further away. If negative, it's closer.
        # For transiting/eclipsing systems, the inclination is close to 90 degrees.
        # The star which is "behind" (larger Z value) is occulted.

        return (float(x1_bary_proj), float(y1_bary_proj), float(z1_bary_los),
                float(x2_bary_proj), float(y2_bary_proj), float(z2_bary_los))