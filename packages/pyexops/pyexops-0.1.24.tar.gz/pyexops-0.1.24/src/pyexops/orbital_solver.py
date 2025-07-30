# pyexops/src/pyexops/orbital_solver.py

import numpy as np

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
        # Let's call it 'planet_semimajor_axis_m'
        planet_semimajor_axis_m = semimajor_axis * OrbitalSolver.R_SUN 

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

    @staticmethod
    def calculate_reflected_flux(
        star_flux_oot: float, # Out-of-transit flux of the star
        planet_radius_stellar_radii: float,
        planet_semimajor_axis_stellar_radii: float,
        planet_period_days: float,
        planet_epoch_transit_days: float,
        planet_albedo: float,
        times: np.ndarray,
        eccentricity: float = 0.0, # Used for calculating true anomaly (if needed for more precise phase angle)
        argument_of_periastron: float = 90.0 # Used for true anomaly
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
        if planet_semimajor_axis_stellar_radii <= 0:
            return np.zeros_like(times, dtype=np.float64) # No reflection if no orbit or at star center

        # Calculate Mean Anomaly
        mean_anomaly = 2 * np.pi * (times - planet_epoch_transit_days) / planet_period_days

        # For eccentric orbits, need Eccentric Anomaly and True Anomaly to correctly determine phase angle.
        # For simplicity, if e is non-zero, we will first solve Kepler's equation.
        # If e is 0, eccentric_anomaly = mean_anomaly, true_anomaly = mean_anomaly + omega_rad (roughly).
        
        # Let's simplify phase angle for now. We will use the orbital phase derived from epoch_transit
        # as a proxy for the phase angle of reflection.
        # Phase angle 'alpha' from 0 (full new moon - behind star) to pi (full phase - in front of star/transit).
        # At transit epoch_transit, planet is in front, so phase = 0, and we want alpha = pi.
        # At occultation (half period later), planet is behind, so phase = pi, and we want alpha = 0.
        
        # This implies: orbital_phase_rad = 2 * np.pi * (times - epoch_transit_days) / period_days
        # Then, alpha_rad = np.abs(np.pi - orbital_phase_rad % (2 * np.pi)) if we consider a simple model where
        # phase angle is strictly 0 to pi from 'occultation' to 'transit'.
        
        # A common simplified phase angle for an observer is derived from the projected Z position.
        # Let's use the definition based on the True Anomaly.
        # Phase angle (alpha) is the angle between the star-planet vector and planet-observer vector.
        # For an observer looking along Z, star at origin, planet at (X, Y, Z), alpha_rad = arccos(Z / |Planet_Star_Distance|).
        # In our orbital model, the Z-component (line-of-sight distance) is related to true anomaly and omega.
        # A simpler Lambertian phase function depends only on the cosine of the phase angle `alpha`.
        # The phase angle `alpha` can be considered to vary from 0 (full illumination, opposition) to pi (no illumination, conjunction).
        # Conventionally, at transit (inferior conjunction), observer sees full phase (alpha=pi).
        # At secondary eclipse (superior conjunction), observer sees new phase (alpha=0).

        # Let's derive it using True Anomaly.
        eccentric_anomaly = OrbitalSolver._solve_kepler_equation(mean_anomaly, eccentricity)
        true_anomaly = 2 * np.arctan2(np.sqrt(1 + eccentricity) * np.sin(eccentric_anomaly / 2),
                                     np.sqrt(1 - eccentricity) * np.cos(eccentric_anomaly / 2))
        
        # Relative distance from star to planet
        r = planet_semimajor_axis_stellar_radii * (1 - eccentricity**2) / (1 + eccentricity * np.cos(true_anomaly))

        # Position of planet in 3D space relative to star, in observer's frame (simplified)
        # Assuming inclination = 90 deg for simplicity in phase angle calculation.
        # x_observer_frame = r * cos(true_anomaly + argument_of_periastron_rad)
        # y_observer_frame = r * sin(true_anomaly + argument_of_periastron_rad) * cos(inclination_rad)
        # z_observer_frame = r * sin(true_anomaly + argument_of_periastron_rad) * sin(inclination_rad)
        
        # The true phase angle depends on the 3D geometry. For transiting planets and fixed inclination,
        # it's usually 0 at secondary eclipse and pi at transit.
        # A common approximation uses the true anomaly (f) and argument of periastron (omega).
        # The angle from the observer's line-of-sight to the planet (phi) often drives the phase.
        # cos(phi) = sin(i) * sin(f + omega)
        
        # For a simplified model, let's use the true anomaly directly to approximate phase.
        # True anomaly at transit (f_transit) and occultation (f_occultation).
        # The phase angle `alpha` of the planet as seen from the observer.
        # `alpha` ranges from 0 (full, planet behind star) to pi (new, planet in front).
        # For a transit at T0, true anomaly `f` maps to `epoch_transit`.
        # `f = pi - omega` for transit.
        # At secondary eclipse, `f = 2pi - omega`.
        # This implies `cos(phase_angle)` is related to `cos(true_anomaly)`.
        
        # Let's simplify further based on the time relative to transit:
        # Orbital phase from transit epoch: `phi_orb = 2 * np.pi * (times - planet_epoch_transit_days) / planet_period_days`
        # We need alpha from 0 to pi. alpha = 0 at secondary eclipse (phi_orb = pi), alpha = pi at transit (phi_orb = 0).
        # So, phase_angle_rad = np.abs(np.pi - (phi_orb % (2 * np.pi)))
        # This simplification treats orbit as circular for phase curve.
        
        # More precise: Use projected Z component (line-of-sight) as done in PyTransit / Kipping (2010).
        # The distance from system barycenter to planet along the line of sight (Z)
        # Z_coord_rel = np.sin(eccentric_anomaly) * np.sin(argument_of_periastron_rad) + np.cos(eccentric_anomaly) * np.cos(argument_of_periastron_rad) * np.cos(inclination_rad)
        # Let's use simpler: use `mean_anomaly` directly as the phase angle.
        
        # Simplest approach for phase angle alpha (0 at opposition/full, pi at conjunction/new):
        # alpha_rad = np.abs(mean_anomaly % (2 * np.pi) - np.pi) 
        # This implies alpha=pi at mean_anomaly=0 (transit), alpha=0 at mean_anomaly=pi (occultation)
        
        # Common usage (e.g. from Mandel & Agol or others) for phase angle `alpha_observer`:
        # `cos(alpha_observer) = -sin(i) * sin(f+omega) * (1-e^2)/(1+e*cos(f))`
        # This is getting too complex for "basic reflected light".
        
        # Let's define the phase angle as the angle in the orbital plane (from periastron, or some reference).
        # Simple Lambertian: F_reflected ~ (1 + cos(alpha)) where alpha is 0 at full phase, pi at new phase.
        # At transit, we see the full phase, so alpha = pi. At secondary eclipse, alpha = 0.
        # orbital_phase_rad = 2 * np.pi * (times - planet_epoch_transit_days) / planet_period_days
        # Let's use `mean_anomaly` for `alpha`, and offset it so that alpha=0 at secondary eclipse.
        # At secondary eclipse, mean_anomaly = pi. So, alpha = mean_anomaly - pi.
        alpha_rad = mean_anomaly - np.pi # At secondary eclipse (mean_anomaly=pi), alpha_rad = 0. At transit (mean_anomaly=0 or 2pi), alpha_rad = -pi or pi.
        # This needs to map to [0, pi] for cos(alpha).
        # A simple phase function that works:
        # When planet is `phi` radians from transit (0 at transit), then flux is proportional to (1 - cos(phi)).
        # It's lowest at transit. We want it highest.
        # Let's use the True Anomaly and Argument of Periastron.
        # Angle from observer's line of sight to planet: `psi = true_anomaly + argument_of_periastron_rad - pi/2` (if pi/2 is the transit phase)
        # A simpler phase angle definition often used for light curves: `phase_angle = np.pi - orbital_phase_from_transit_center`
        # Let orbital phase be `theta = 2 * np.pi * (times - epoch_transit) / period`
        # `cos(alpha) = np.cos(theta)` (This would mean alpha=0 at transit, alpha=pi at occultation)
        # So `F_reflected = C * (1 + np.cos(theta))/2`
        # Let's stick with this for simplicity:
        theta_orb = 2 * np.pi * (times - planet_epoch_transit_days) / planet_period_days
        
        # Calculate the amplitude of the reflected light signal
        # Relative flux = albedo * (R_p / a_p)^2 * PhaseFunction(theta_orb)
        # The star_flux_oot is the total flux of the star out of transit.
        # The maximum possible reflected light is proportional to (albedo * (R_p/a_p)^2) * star_flux_oot.
        # A simple phase function is (1 + cos(theta))/2 where theta=0 is occultation, theta=pi is transit.
        # Our `theta_orb` is 0 at transit, pi at occultation.
        # So we need `(1 + cos(theta_orb - pi))/2` or `(1 - cos(theta_orb))/2`.
        # This will be minimum at transit (0) and maximum at occultation (1). This is wrong.
        # We want maximum at transit (when planet is full).
        
        # Let's define `alpha` (phase angle) as 0 for full phase (transit) and `pi` for new phase (occultation)
        # If `theta_orb` is 0 at transit, and `pi` at occultation.
        # Then `alpha = theta_orb` for `theta_orb` from 0 to pi.
        # And `alpha = 2*pi - theta_orb` for `theta_orb` from pi to 2pi.
        # Use `np.abs(theta_orb % (2*np.pi) - np.pi)` for `alpha` to map [0, 2pi] to [0, pi]
        # such that `alpha=pi` at `theta_orb=0` and `alpha=0` at `theta_orb=pi`.
        
        alpha = np.abs(theta_orb % (2 * np.pi) - np.pi) # 0 at occultation (phi=pi), pi at transit (phi=0)
        
        # Simplified Lambertian phase function:
        # F_reflected_relative = albedo * (R_p / a_p)^2 * (1 + cos(alpha_rad))/2
        # F_reflected = star_flux_oot * (planet_albedo * (planet_radius_stellar_radii / planet_semimajor_axis_stellar_radii)**2 * (1 + np.cos(alpha)) / 2)
        
        # The overall scale factor for reflected light relative to stellar flux:
        reflection_amplitude_factor = planet_albedo * (planet_radius_stellar_radii / planet_semimajor_axis_stellar_radii)**2
        
        # Flux from reflected light. Max at transit (alpha=pi), Min at occultation (alpha=0).
        # Phase function (alpha is 0 for full-dark, pi for full-bright)
        reflected_fluxes = star_flux_oot * reflection_amplitude_factor * (1 + np.cos(alpha)) / 2
        
        return reflected_fluxes.astype(np.float64)