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
    def _solve_kepler_equation(mean_anomaly: np.ndarray, eccentricity: float,
                               tolerance: float = 1e-8, max_iterations: int = 100) -> np.ndarray:
        """
        Solves Kepler's equation (M = E - e * sin(E)) for the eccentric anomaly (E)
        using the Newton-Raphson method.

        :param mean_anomaly: Mean anomaly (M) in radians.
        :param eccentricity: Orbital eccentricity (e).
        :param tolerance: Desired precision for E.
        :param max_iterations: Maximum number of iterations for Newton-Raphson.
        :return: Eccentric anomaly (E) in radians.
        :raises ValueError: If eccentricity is out of valid range [0, 1).
        """
        if not (0 <= eccentricity < 1):
            raise ValueError("Eccentricity must be between 0 (inclusive) and 1 (exclusive).")

        # Initial guess for E using M
        E = mean_anomaly + eccentricity * np.sin(mean_anomaly) * (1.0 + eccentricity)

        for _ in range(max_iterations):
            f = E - eccentricity * np.sin(E) - mean_anomaly
            f_prime = 1 - eccentricity * np.cos(E)
            delta_E = f / f_prime

            E -= delta_E

            if np.all(np.abs(delta_E) < tolerance):
                break
        
        return E

    @staticmethod
    def calculate_stellar_radial_velocity(
        star_mass: float,
        planet_mass: float,
        period: float,  # days
        semimajor_axis: float, # stellar radii
        inclination: float,  # degrees
        epoch_transit: float, # days
        times: np.ndarray, # days
        eccentricity: float = 0.0,
        argument_of_periastron: float = 90.0 # degrees
    ) -> np.ndarray:
        """
        Computes the stellar radial velocity induced by a single planet for
        both circular and elliptical orbits.

        :param star_mass: Mass of the star in solar masses (M_sun).
        :param planet_mass: Mass of the planet in Jupiter masses (M_Jup).
        :param period: Orbital period in days.
        :param semimajor_axis: Semi-major axis in stellar radii.
        :param inclination: Orbital inclination in degrees.
        :param epoch_transit: Time of mid-transit in days.
        :param times: Array of time points in days.
        :param eccentricity: Orbital eccentricity (0.0 for circular).
        :param argument_of_periastron: Argument of periastron in degrees.
                                       For circular transiting orbits, typically 90 degrees.
        :return: Array of stellar radial velocities in m/s.
        """

        # Convert input units to SI for calculation
        M_star_kg = star_mass * OrbitalSolver.M_SUN
        # Assuming planet_mass is in Jupiter masses, convert to kg.
        m_planet_kg = planet_mass * OrbitalSolver.M_JUP 

        # Convert period from days to seconds
        P_sec = period * OrbitalSolver.DAY_TO_SEC

        # Convert semimajor_axis from stellar radii to meters
        # This 'a_meters' is the star's radius in meters from the previous formula,
        # but in actual RV calculation, we need the semi-major axis in meters,
        # which depends on the star's semi-major axis relative to the center of mass.
        # The true semi-major axis 'a_planet' for the planet's orbit around the star
        # (approximately the center of mass) is needed for K.
        # The semi-major axis in stellar radii needs to be converted to meters.
        # This requires the stellar radius in meters for conversion.
        # Let's ensure 'semimajor_axis' is interpreted as the planet's orbit 'a' around the star.
        # So 'a' is already in stellar radii, which is not what 'a_meters' used to be.
        # Let's call it 'planet_semimajor_axis_m'
        planet_semimajor_axis_m = semimajor_axis * OrbitalSolver.R_SUN # Planet's 'a' in meters

        # Convert inclination and argument of periastron to radians
        inclination_rad = np.deg2rad(inclination)
        argument_of_periastron_rad = np.deg2rad(argument_of_periastron)

        # Calculate Mean Anomaly (M)
        # For an eccentric orbit, the time of mid-transit (T0) is generally the time of inferior conjunction.
        # This T0 usually corresponds to True Anomaly (f) = pi - omega (where omega is argument of periastron).
        # However, for simplicity and consistency with circular transit,
        # we'll define M = 0 (and thus E = 0, f = -omega) at T0.
        # Then the RV formula will correctly account for the phase shift.
        mean_anomaly = 2 * np.pi * (times - epoch_transit) / period

        # Solve Kepler's equation for Eccentric Anomaly (E)
        eccentric_anomaly = OrbitalSolver._solve_kepler_equation(mean_anomaly, eccentricity)

        # Calculate True Anomaly (f) from Eccentric Anomaly (E)
        # Using atan2 is more robust as it preserves quadrant information
        true_anomaly = 2 * np.arctan2(np.sqrt(1 + eccentricity) * np.sin(eccentric_anomaly / 2),
                                     np.sqrt(1 - eccentricity) * np.cos(eccentric_anomaly / 2))

        # Calculate the semi-amplitude (K) of the radial velocity in m/s
        # K = (m_p * sin(i)) / ((M_star + m_p)^(2/3)) * ((2 * G * pi) / P)^(1/3) / sqrt(1 - e^2)
        # This formula is more robust for elliptical orbits.
        
        # Check for near-zero eccentricity to avoid division by very small numbers,
        # although sqrt(1 - e^2) is typically handled well by numpy.
        # If eccentricity is exactly 1, this formula would break. But e<1 is enforced in _solve_kepler_equation.
        
        # If P_sec or (M_star_kg + m_planet_kg) is zero, K should be zero
        if P_sec == 0 or (M_star_kg + m_planet_kg) == 0:
            K = 0.0
        else:
            K_factor_mass = (m_planet_kg * np.sin(inclination_rad)) / ((M_star_kg + m_planet_kg)**(2/3))
            K_factor_period_G = ((2 * OrbitalSolver.G * np.pi) / P_sec)**(1/3)
            K_factor_ecc = 1 / np.sqrt(1 - eccentricity**2)
            K = K_factor_mass * K_factor_period_G * K_factor_ecc

        # Calculate stellar radial velocity
        # RV = K * [cos(f + omega) + e * cos(omega)]
        radial_velocities = K * (np.cos(true_anomaly + argument_of_periastron_rad) + eccentricity * np.cos(argument_of_periastron_rad))
        
        # Ensure the output array is explicitly float64
        return radial_velocities.astype(np.float64)