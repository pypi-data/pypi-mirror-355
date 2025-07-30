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
        times: np.ndarray, # <<< MOVED THIS LINE HERE
        eccentricity: float = 0.0,
        argument_of_periastron: float = 90.0 # degrees
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
        :param times: Array of time points in days. # <<< UPDATED DOCSTRING POSITION
        :param eccentricity: Orbital eccentricity (0.0 for circular).
        :param argument_of_periastron: Argument of periastron in degrees.
                                       For circular transiting orbits, typically 90 degrees.
        :return: Array of stellar radial velocities in m/s.
        """

        # ... (rest of the method code remains the same) ...
        # (Não vou reproduzir o corpo inteiro do método para não encher a resposta com código repetido)
        # Por favor, garanta que esta seja a única alteração necessária no método.