# pyexops/src/pyexops/orbital_solver.py

import numpy as np

class OrbitalSolver:
    """
    A class containing static methods for solving orbital mechanics problems,
    such as calculating stellar radial velocities (RV).
    """

    # Define physical constants in SI units
    # G: Gravitational constant (m^3 kg^-1 s^-2)
    # M_SUN: Solar mass (kg)
    # R_SUN: Solar radius (m)
    # M_JUP: Jupiter mass (kg)
    # M_EARTH: Earth mass (kg)
    # AU: Astronomical Unit (m)
    # DAY_TO_SEC: Days to seconds conversion factor
    G = 6.67430e-11
    M_SUN = 1.98847e30
    R_SUN = 6.957e8
    M_JUP = 1.898e27
    M_EARTH = 5.972e24
    AU = 1.495978707e11
    DAY_TO_SEC = 86400

    @staticmethod
    def calculate_stellar_radial_velocity(
        star_mass: float,
        planet_mass: float,
        period: float,  # days
        semimajor_axis: float, # stellar radii
        inclination: float,  # degrees
        epoch_transit: float, # days
        eccentricity: float = 0.0,
        argument_of_periastron: float = 90.0, # degrees
        times: np.ndarray # days
    ) -> np.ndarray:
        """
        Computes the stellar radial velocity induced by a single planet.
        Currently implements for circular orbits (eccentricity=0).
        For eccentric orbits, it simplifies to circular.
        Future: Expand to handle elliptical orbits correctly using solution of Kepler's equation.

        :param star_mass: Mass of the star in solar masses (M_sun).
        :param planet_mass: Mass of the planet in Jupiter masses (M_Jup).
        :param period: Orbital period in days.
        :param semimajor_axis: Semi-major axis in stellar radii.
        :param inclination: Orbital inclination in degrees.
        :param epoch_transit: Time of mid-transit in days.
        :param eccentricity: Orbital eccentricity (0.0 for circular).
        :param argument_of_periastron: Argument of periastron in degrees.
                                       For circular transiting orbits, typically 90 degrees.
        :param times: Array of time points in days.
        :return: Array of stellar radial velocities in m/s.
        """

        # Convert input units to SI for calculation
        M_star_kg = star_mass * OrbitalSolver.M_SUN
        # Assuming planet_mass is in Jupiter masses, convert to kg.
        # If more flexibility is needed (e.g., Earth masses), a parameter for units can be added.
        m_planet_kg = planet_mass * OrbitalSolver.M_JUP 

        # Convert period from days to seconds
        P_sec = period * OrbitalSolver.DAY_TO_SEC

        # Convert semimajor_axis from stellar radii to meters
        a_meters = semimajor_axis * OrbitalSolver.R_SUN

        # Convert inclination and argument of periastron to radians
        i_rad = np.deg2rad(inclination)
        # omega_rad = np.deg2rad(argument_of_periastron) # Not used in circular version yet

        # --- Simplification for initial implementation: Circular Orbit (e=0) ---
        # The semi-amplitude K for a circular orbit:
        # K = (2 * pi * a_p * sin(i)) / P * (m_p / (M_star + m_p))
        # Where a_p is the semi-major axis, P is the period, i is the inclination, m_p and M_star are the masses.

        K = (2 * np.pi * a_meters * np.sin(i_rad)) / P_sec * (m_planet_kg / (M_star_kg + m_planet_kg)) # K in m/s

        # Calculate orbital phase.
        # For circular transiting orbits, epoch_transit (T0) is the transit time.
        # The usual convention is that RV is zero at transit and becomes positive (redshift) shortly after.
        # This is achieved with a simple sine function of the phase: K * sin(phase).
        
        # Phase `phi` ranging from 0 to 2pi (for one period)
        phi = 2 * np.pi * (times - epoch_transit) / period
        
        radial_velocities = K * np.sin(phi)

        return radial_velocities