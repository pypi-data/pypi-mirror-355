# pyexops/src/pyexops/orbital_solver.py

import numpy as np
from typing import Tuple

class OrbitalSolver:
    """
    A class containing static methods for solving orbital mechanics problems,
    such as calculating stellar radial velocities (RV) and planetary phase curves.
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
    G_SPEED_OF_LIGHT = 299792458.0 # Speed of light in m/s # NEW

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

        # Convert inclination and argument of periastron to radians
        inclination_rad = np.deg2rad(inclination)
        argument_of_periastron_rad = np.deg2rad(argument_of_periastron)

        # Calculate Mean Anomaly (M)
        mean_anomaly = 2 * np.pi * (times - epoch_transit) / period

        # Solve Kepler's equation for Eccentric Anomaly (E)
        eccentric_anomaly = OrbitalSolver._solve_kepler_equation(mean_anomaly, eccentricity)

        # Calculate True Anomaly (f) from Eccentric Anomaly (E)
        true_anomaly = 2 * np.arctan2(np.sqrt(1 + eccentricity) * np.sin(eccentric_anomaly / 2),
                                     np.sqrt(1 - eccentricity) * np.cos(eccentric_anomaly / 2))

        # Calculate the semi-amplitude (K) of the radial velocity in m/s
        # K = (m_p * sin(i)) / ((M_star + m_p)^(2/3)) * ((2 * G * pi) / P)^(1/3) / sqrt(1 - e^2)
        
        # Guard against zero/negative masses or periods
        if P_sec <= 0 or (M_star_kg + m_planet_kg) <= 0:
            return np.zeros_like(times, dtype=np.float64)

        K_factor_mass = (m_planet_kg * np.sin(inclination_rad)) / ((M_star_kg + m_planet_kg)**(2/3))
        K_factor_period_G = ((2 * OrbitalSolver.G * np.pi) / P_sec)**(1/3)
        
        # Handle eccentricity for K, avoiding division by zero if e is very close to 1
        if 1 - eccentricity**2 <= 1e-9:
             K_factor_ecc = 0.0 # Or raise an error for near-parabolic orbit
        else:
            K_factor_ecc = 1 / np.sqrt(1 - eccentricity**2)

        K = K_factor_mass * K_factor_period_G * K_factor_ecc

        # Calculate stellar radial velocity
        # RV = K * [cos(f + omega) + e * cos(omega)]
        radial_velocities = K * (np.cos(true_anomaly + argument_of_periastron_rad) + eccentricity * np.cos(argument_of_periastron_rad))
        
        # Ensure the output array is explicitly float64
        return radial_velocities.astype(np.float64)

    @staticmethod
    def calculate_reflected_flux(
        star_flux_oot: float, # Out-of-transit flux of the star
        planet_radius_stellar_radii: float,
        planet_semimajor_axis_stellar_radii: float,
        planet_period_days: float,
        planet_epoch_transit_days: float,
        planet_albedo: float,
        times: np.ndarray,
        eccentricity: float = 0.0, 
        argument_of_periastron: float = 90.0 
    ) -> np.ndarray:
        """
        Computes the flux from reflected light of a planet.
        Uses a simplified Lambertian phase function.
        The reflected light is added to the system's total flux.

        :param star_flux_oot: The out-of-transit flux of the star (e.g., `base_flux` or `max_flux_from_simulation`).
        :param planet_radius_stellar_radii: Radius of the planet in stellar radii.
        :param planet_semimajor_axis_stellar_radii: Semi-major axis of the planet's orbit in stellar radii.
        :param planet_period_days: Orbital period in days.
        :param planet_epoch_transit_days: Time of mid-transit in days.
        :param planet_albedo: Albedo (reflectivity) of the planet (0.0 to 1.0).
        :param times: Array of time points in days.
        :param eccentricity: Orbital eccentricity.
        :param argument_of_periastron: Argument of periastron in degrees.
        :return: Array of reflected flux values (in units consistent with star_flux_oot).
        """
        if planet_albedo < 0 or planet_albedo > 1:
            raise ValueError("Albedo must be between 0.0 and 1.0.")
        if planet_semimajor_axis_stellar_radii <= 0 or planet_period_days <= 0:
            return np.zeros_like(times, dtype=np.float64) 

        # Calculate Mean Anomaly
        mean_anomaly = 2 * np.pi * (times - planet_epoch_transit_days) / planet_period_days

        # Solve Kepler's equation for Eccentric Anomaly (E)
        eccentric_anomaly = OrbitalSolver._solve_kepler_equation(mean_anomaly, eccentricity)
        
        # Calculate True Anomaly (f) from Eccentric Anomaly (E)
        # This is needed for a more accurate phase calculation if eccentricity is high
        true_anomaly = 2 * np.arctan2(np.sqrt(1 + eccentricity) * np.sin(eccentric_anomaly / 2),
                                      np.sqrt(1 - eccentricity) * np.cos(eccentric_anomaly / 2))
        
        argument_of_periastron_rad = np.deg2rad(argument_of_periastron)

        # Orbital phase angle (theta) from transit, where transit is 0 radians.
        # This is essentially the "true anomaly plus argument of periastron" projected
        # onto the plane of the sky. For transiting planets, the phase angle for reflection
        # `alpha` varies from 0 (full, secondary eclipse) to pi (new, primary transit).
        # We need a phase function that is minimum at primary transit and maximum at secondary eclipse.
        # Let's use `theta_orb` as the angle from the point directly behind the star (occultation).
        # So, at transit (mean_anomaly = 0), the angle from occultation is pi.
        # Let's align `theta_orb` such that `theta_orb = 0` at secondary eclipse (full phase), and `theta_orb = pi` at primary transit (new phase).
        # Since mean_anomaly is 0 at transit, and pi at occultation:
        # `theta_orb = mean_anomaly` (this aligns `theta_orb` with secondary eclipse at `pi`, transit at `0` or `2pi`).
        # We want our phase function `f(alpha)` to be `1` at `alpha=0` (full illumination) and `0` at `alpha=pi` (no illumination).
        # A simple Lambertian phase function is `(1 + cos(alpha))/2`.
        # So if `alpha = mean_anomaly - pi` (so alpha=0 at secondary eclipse (mean_anomaly=pi), alpha=-pi at transit (mean_anomaly=0)),
        # then `(1 + cos(mean_anomaly - pi))/2 = (1 - cos(mean_anomaly))/2`.
        # This will be minimum at transit and maximum at secondary eclipse, which is what we want.
        
        phase_angle_for_reflection_rad = mean_anomaly 
        
        # The overall scale factor for reflected light relative to stellar flux:
        reflection_amplitude_factor = planet_albedo * (planet_radius_stellar_radii / planet_semimajor_axis_stellar_radii)**2
        
        # Reflected flux using a Lambertian phase function.
        # It's maximal at secondary eclipse (when the planet shows its full illuminated face to us)
        # and minimal (zero) at primary transit (when the illuminated face is away from us).
        # `(1 - cos(theta_orb))/2` works if `theta_orb` is 0 at transit and pi at occultation.
        # Our `mean_anomaly` is 0 at transit and pi at occultation.
        reflected_fluxes = star_flux_oot * reflection_amplitude_factor * (1 - np.cos(mean_anomaly)) / 2
        
        return reflected_fluxes.astype(np.float64)

    @staticmethod
    def calculate_doppler_beaming_factor(stellar_radial_velocity_ms: np.ndarray, stellar_spectral_index: float = 3.0) -> np.ndarray:
        """
        Calculates the multiplicative factor due to Doppler beaming (relativistic beaming) effect.
        The star appears brighter when approaching (negative RV) and dimmer when receding (positive RV).

        :param stellar_radial_velocity_ms: Stellar radial velocity in meters per second.
                                           Positive for recession, negative for approach.
        :param stellar_spectral_index: Spectral index of the star (gamma in some literature),
                                       typically ~3 for G/K stars in visible/IR.
        :return: Array of multiplicative brightness factors (close to 1.0).
        """
        # The relativistic beaming factor is given by F/F0 = 1 + (gamma + 2) * (v/c)
        # where v is the radial velocity, c is the speed of light.
        # gamma is the stellar spectral index, often ~3 for visible bands.
        
        # Check for zero or non-finite inputs to prevent division by zero or inf
        if not np.isfinite(stellar_radial_velocity_ms).all():
            return np.ones_like(stellar_radial_velocity_ms, dtype=np.float64)

        beaming_factor = 1.0 + (stellar_spectral_index + 2.0) * (stellar_radial_velocity_ms / OrbitalSolver.G_SPEED_OF_LIGHT)
        return beaming_factor.astype(np.float64)

    @staticmethod
    def calculate_ellipsoidal_variation_factor(
        star_mass_solar: float,
        planet_mass_jupiter: float,
        star_radius_stellar_radii: float,
        planet_semimajor_axis_stellar_radii: float,
        inclination_deg: float,
        period_days: float,
        epoch_transit_days: float,
        times_days: np.ndarray,
        stellar_gravity_darkening_coeff: float = 0.32, # 'g' or 'y' gravity darkening exponent
        stellar_limb_darkening_coeffs: Tuple[float, float] = (0.5, 0.2) # (u1, u2)
    ) -> np.ndarray:
        """
        Calculates the multiplicative factor due to ellipsoidal variations caused by tidal
        deformation of the star by a close-in massive planet.
        The star appears brighter at conjunctions (primary transit and secondary eclipse)
        and dimmer at quadratures.

        :param star_mass_solar: Mass of the star in solar masses (M_sun).
        :param planet_mass_jupiter: Mass of the planet in Jupiter masses (M_Jup).
        :param star_radius_stellar_radii: Radius of the star in stellar radii (self-consistent unit).
        :param planet_semimajor_axis_stellar_radii: Semi-major axis in stellar radii.
        :param inclination_deg: Orbital inclination in degrees.
        :param period_days: Orbital period in days.
        :param epoch_transit_days: Time of mid-transit in days.
        :param times_days: Array of time points in days.
        :param stellar_gravity_darkening_coeff: Gravity darkening exponent (g or y), e.g., 0.32 for convective envelopes.
        :param stellar_limb_darkening_coeffs: (u1, u2) for quadratic limb darkening model.
        :return: Array of multiplicative brightness factors (close to 1.0).
        """
        # Ensure necessary parameters are valid
        if star_mass_solar <= 0 or planet_mass_jupiter <= 0 or planet_semimajor_axis_stellar_radii <= 0 or period_days <= 0:
            return np.ones_like(times_days, dtype=np.float64)

        inclination_rad = np.deg2rad(inclination_deg)
        
        # Calculate orbital phase (phi or theta), where phi=0 at transit
        orbital_phase = 2 * np.pi * (times_days - epoch_transit_days) / period_days

        # Amplitude coefficient (C2) depends on limb darkening and gravity darkening
        # Using u1 for simplicity (linear limb darkening coefficient)
        u1 = stellar_limb_darkening_coeffs[0]
        
        # Formula for C_ellip from Kipping & Bakos 2011, ApJL, 730, L8
        # C_ellip = (15 + u1) / (15 * (1 - u1)) * (1 + stellar_gravity_darkening_coeff) / 2
        
        # Avoid division by zero for limb darkening
        if 1 - u1 <= 1e-9:
            C_ellip = 1.0 # Fallback for pathological limb darkening
        else:
            C_ellip = ((15 + u1) / (15 * (1 - u1))) * ((1 + stellar_gravity_darkening_coeff) / 2)

        # Mass ratio
        mass_ratio = (planet_mass_jupiter * OrbitalSolver.M_JUP) / (star_mass_solar * OrbitalSolver.M_SUN)

        # Radius to semi-major axis ratio (cubed)
        radius_semimajor_ratio_cubed = (star_radius_stellar_radii / planet_semimajor_axis_stellar_radii)**3

        # Sin squared of inclination
        sin_sq_i = np.sin(inclination_rad)**2

        # Base amplitude of ellipsoidal variation
        # This is the full amplitude from minimum to maximum.
        base_amplitude_relative = C_ellip * mass_ratio * radius_semimajor_ratio_cubed * sin_sq_i

        # The flux variation pattern is proportional to -cos(2*orbital_phase) for primary transit (phase=0).
        # This means maximum brightness at orbital_phase = 0, pi (conjunctions)
        # and minimum brightness at orbital_phase = pi/2, 3pi/2 (quadratures).
        # So, flux_factor = 1 - base_amplitude_relative * cos(2 * orbital_phase)
        ellipsoidal_factor = 1.0 - base_amplitude_relative * np.cos(2 * orbital_phase)
        
        return ellipsoidal_factor.astype(np.float64)