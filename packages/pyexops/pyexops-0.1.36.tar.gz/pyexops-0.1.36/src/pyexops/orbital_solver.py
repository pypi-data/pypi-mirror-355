# pyexops/src/pyexops/orbital_solver.py

import numpy as np
from typing import Tuple

class OrbitalSolver:
    """
    A class containing static methods for solving orbital mechanics problems,
    such as calculating stellar radial velocities (RV), planetary phase curves,
    Doppler beaming, ellipsoidal variations, and eclipse factors.
    It also handles binary star orbital positions.
    """

    # Define physical constants in SI units
    # G: Gravitational constant (m^3 kg^-1 s^-2)
    # M_SUN: Solar mass (kg)
    # R_SUN: Solar radius (m)
    # M_JUP: Jupiter mass (kg)
    # M_EARTH: Earth mass (kg)
    # AU: Astronomical Unit (m)
    # DAY_TO_SEC: Days to seconds conversion factor
    # G_SPEED_OF_LIGHT: Speed of light (m/s)
    G = 6.67430e-11
    M_SUN = 1.98847e30
    R_SUN = 6.957e8
    M_JUP = 1.898e27
    M_EARTH = 5.972e24
    AU = 1.495978707e11
    DAY_TO_SEC = 86400
    G_SPEED_OF_LIGHT = 299792458.0 

    @staticmethod
    def _solve_kepler_equation(mean_anomaly: np.ndarray, eccentricity: float,
                               tolerance: float = 1e-8, max_iterations: int = 100) -> np.ndarray:
        """
        Solves Kepler's equation (M = E - e * sin(E)) for the eccentric anomaly (E)
        using the Newton-Raphson method.

        :param mean_anomaly: Mean anomaly (M) in radians. Can be a single float or a numpy array.
        :param eccentricity: Orbital eccentricity (e).
        :param tolerance: Desired precision for E.
        :param max_iterations: Maximum number of iterations for Newton-Raphson.
        :return: Eccentric anomaly (E) in radians. Returns a numpy array.
        :raises ValueError: If eccentricity is out of valid range [0, 1).
        """
        if not (0 <= eccentricity < 1):
            raise ValueError("Eccentricity must be between 0 (inclusive) and 1 (exclusive).")

        # Ensure mean_anomaly is a numpy array for vectorized operations
        mean_anomaly = np.atleast_1d(mean_anomaly)

        # Initial guess for E using M
        E = mean_anomaly + eccentricity * np.sin(mean_anomaly) * (1.0 + eccentricity)

        for _ in range(max_iterations):
            f = E - eccentricity * np.sin(E) - mean_anomaly
            f_prime = 1 - eccentricity * np.cos(E)
            
            # Prevent division by zero if f_prime is too small
            # This can happen if eccentricity is very large and E is close to pi/0.
            # In Kepler's equation for e<1, f_prime is always >0.
            # But in numerical calc, it might get close.
            f_prime[np.abs(f_prime) < tolerance] = tolerance # Guard against division by zero

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
        semimajor_axis: float, # stellar radii (of the host star)
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
        :param semimajor_axis: Semi-major axis in stellar radii (of the host star).
        :param inclination: Orbital inclination in degrees.
        :param epoch_transit: Time of mid-transit in days.
        :param times: Array of time points in days.
        :param eccentricity: Orbital eccentricity (0.0 for circular).
        :param argument_of_periastron: Argument of periastron in degrees.
                                       For circular transiting orbits, typically 90 degrees.
        :return: Array of stellar radial velocities in m/s. Returns zeros if input parameters are invalid.
        """

        # Convert input units to SI for calculation
        M_star_kg = star_mass * OrbitalSolver.M_SUN
        m_planet_kg = planet_mass * OrbitalSolver.M_JUP 

        # Convert period from days to seconds
        P_sec = period * OrbitalSolver.DAY_TO_SEC

        # Guard against zero/negative masses or periods
        if P_sec <= 0 or (M_star_kg + m_planet_kg) <= 0:
            return np.zeros_like(times, dtype=np.float64)

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
        
        # Handle eccentricity for K, avoiding division by zero if e is very close to 1
        if 1 - eccentricity**2 <= 1e-9:
             K_factor_ecc = 0.0 # Or raise an error for near-parabolic orbit
        else:
            K_factor_ecc = 1 / np.sqrt(1 - eccentricity**2)

        K_factor_mass = (m_planet_kg * np.sin(inclination_rad)) / ((M_star_kg + m_planet_kg)**(2/3))
        K_factor_period_G = ((2 * OrbitalSolver.G * np.pi) / P_sec)**(1/3)
        K = K_factor_mass * K_factor_period_G * K_factor_ecc

        # Calculate stellar radial velocity
        # RV = K * [cos(f + omega) + e * cos(omega)]
        radial_velocities = K * (np.cos(true_anomaly + argument_of_periastron_rad) + eccentricity * np.cos(argument_of_periastron_rad))
        
        return radial_velocities.astype(np.float64)

    @staticmethod
    def calculate_reflected_flux(
        star_flux_oot: float, # Out-of-transit flux of the star
        planet_radius_stellar_radii: float, # Planet radius relative to its host star
        planet_semimajor_axis_stellar_radii: float, # Planet semi-major axis relative to its host star
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

        The reflected light is calculated assuming the planet is always visible,
        and its occultation by the star (secondary eclipse) must be handled separately.

        :param star_flux_oot: The out-of-transit flux of the planet's host star.
        :param planet_radius_stellar_radii: Radius of the planet in stellar radii (of its host star).
        :param planet_semimajor_axis_stellar_radii: Semi-major axis of the planet's orbit in stellar radii (of its host star).
        :param planet_period_days: Orbital period in days.
        :param planet_epoch_transit_days: Time of mid-transit in days.
        :param planet_albedo: Albedo (reflectivity) of the planet (0.0 to 1.0).
        :param times: Array of time points in days.
        :param eccentricity: Orbital eccentricity.
        :param argument_of_periastron: Argument of periastron in degrees.
        :return: Array of reflected flux values (in units consistent with star_flux_oot).
        :raises ValueError: If albedo is out of range.
        """
        if planet_albedo < 0 or planet_albedo > 1:
            raise ValueError("Albedo must be between 0.0 and 1.0.")
        if planet_semimajor_axis_stellar_radii <= 0 or planet_period_days <= 0:
            return np.zeros_like(times, dtype=np.float64) 

        mean_anomaly = 2 * np.pi * (times - planet_epoch_transit_days) / planet_period_days

        eccentric_anomaly = OrbitalSolver._solve_kepler_equation(mean_anomaly, eccentricity)
        
        true_anomaly = 2 * np.arctan2(np.sqrt(1 + eccentricity) * np.sin(eccentric_anomaly / 2),
                                      np.sqrt(1 - eccentricity) * np.cos(eccentric_anomaly / 2))
        
        # Phase angle for reflection: `alpha` varies from 0 (full, secondary eclipse) to pi (new, primary transit).
        # Our `mean_anomaly` is 0 at primary transit (new phase), and pi at secondary eclipse (full phase).
        # So using `mean_anomaly` directly as `alpha` ensures this phasing.
        # Lambertian phase function: F_reflected ~ (1 - cos(alpha))/2. This is minimum at primary transit (alpha=0)
        # and maximum at secondary eclipse (alpha=pi).
        
        reflection_amplitude_factor = planet_albedo * (planet_radius_stellar_radii / planet_semimajor_axis_stellar_radii)**2
        
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
        :param star_radius_stellar_radii: Radius of the star in stellar radii.
        :param planet_semimajor_axis_stellar_radii: Semi-major axis of the planet's orbit in stellar radii.
        :param inclination_deg: Orbital inclination in degrees.
        :param period_days: Orbital period in days.
        :param epoch_transit_days: Time of mid-transit in days.
        :param times_days: Array of time points in days.
        :param stellar_gravity_darkening_coeff: Gravity darkening exponent (g or y), e.g., 0.32 for convective envelopes.
        :param stellar_limb_darkening_coeffs: (u1, u2) for quadratic limb darkening model.
        :return: Array of multiplicative brightness factors (close to 1.0).
        """
        if star_mass_solar <= 0 or planet_mass_jupiter <= 0 or planet_semimajor_axis_stellar_radii <= 0 or period_days <= 0:
            return np.ones_like(times_days, dtype=np.float64)

        inclination_rad = np.deg2rad(inclination_deg)
        
        orbital_phase = 2 * np.pi * (times_days - epoch_transit_days) / period_days

        u1 = stellar_limb_darkening_coeffs[0]
        
        # C_ellip formula from Kipping & Bakos 2011, ApJL, 730, L8
        # C_ellip = (15 + u1) / (15 * (1 - u1)) * (1 + stellar_gravity_darkening_coeff) / 2
        
        if 1 - u1 <= 1e-9:
            C_ellip = 1.0 # Fallback for pathological limb darkening
        else:
            C_ellip = ((15 + u1) / (15 * (1 - u1))) * ((1 + stellar_gravity_darkening_coeff) / 2)

        mass_ratio = (planet_mass_jupiter * OrbitalSolver.M_JUP) / (star_mass_solar * OrbitalSolver.M_SUN)

        radius_semimajor_ratio_cubed = (star_radius_stellar_radii / planet_semimajor_axis_stellar_radii)**3

        sin_sq_i = np.sin(inclination_rad)**2

        base_amplitude_relative = C_ellip * mass_ratio * radius_semimajor_ratio_cubed * sin_sq_i

        ellipsoidal_factor = 1.0 - base_amplitude_relative * np.cos(2 * orbital_phase)
        
        return ellipsoidal_factor.astype(np.float64)
    
    @staticmethod
    def calculate_secondary_eclipse_factor(
        star_radius_stellar_radii: float,
        planet_radius_stellar_radii: float,
        semimajor_axis_stellar_radii: float,
        inclination_deg: float,
        epoch_transit_days: float,
        times_days: np.ndarray,
        eccentricity: float = 0.0,
        argument_of_periastron_deg: float = 90.0
    ) -> np.ndarray:
        """
        Calculates the occultation factor for the planet's light by the star (secondary eclipse).
        This factor is 1.0 when the planet is fully visible and 0.0 when it is fully occulted.
        Partial occultation is approximated.

        :param star_radius_stellar_radii: Radius of the star in stellar radii.
        :param planet_radius_stellar_radii: Radius of the planet in stellar radii.
        :param semimajor_axis_stellar_radii: Semi-major axis of the orbit in stellar radii.
        :param inclination_deg: Orbital inclination in degrees.
        :param epoch_transit_days: Time of primary mid-transit in days.
        :param times_days: Array of time points in days.
        :param eccentricity: Orbital eccentricity.
        :param argument_of_periastron_deg: Argument of periastron in degrees.
        :return: Array of occultation factors (0.0 to 1.0).
        """
        if star_radius_stellar_radii <= 0 or planet_radius_stellar_radii <= 0 or semimajor_axis_stellar_radii <= 0:
            return np.ones_like(times_days, dtype=np.float64)

        inclination_rad = np.deg2rad(inclination_deg)
        argument_of_periastron_rad = np.deg2rad(argument_of_periastron_deg)

        mean_anomaly = 2 * np.pi * (times_days - epoch_transit_days) / period_days

        eccentric_anomaly = OrbitalSolver._solve_kepler_equation(mean_anomaly, eccentricity)
        true_anomaly = 2 * np.arctan2(np.sqrt(1 + eccentricity) * np.sin(eccentric_anomaly / 2),
                                      np.sqrt(1 - eccentricity) * np.cos(eccentric_anomaly / 2))
        
        r_current_separation = semimajor_axis_stellar_radii * (1 - eccentricity**2) / (1 + eccentricity * np.cos(true_anomaly))

        # Position of planet relative to its host star in orbital plane
        angle_in_orbital_plane = true_anomaly + argument_of_periastron_rad
        x_rel_host = r_current_separation * np.sin(angle_in_orbital_plane)
        y_rel_host = -r_current_separation * np.cos(angle_in_orbital_plane) * np.cos(inclination_rad)
        z_rel_host = -r_current_separation * np.cos(angle_in_orbital_plane) * np.sin(inclination_rad) # Z distance of planet relative to star, positive for behind star.

        projected_separation_b = np.sqrt(x_rel_host**2 + y_rel_host**2)

        occultation_factor = np.ones_like(times_days, dtype=np.float64)
        
        # Secondary eclipse occurs when the planet is behind the star (z_rel_host > 0)
        # and their projected disks overlap.
        # Simplified geometry for occultation fraction (Lambda function from Mandel & Agol (2002) is complex)
        # We will use a simplified step/linear function based on impact parameter.

        # p = Rp / Rs (ratio of radii)
        p = planet_radius_stellar_radii / star_radius_stellar_radii
        
        # d = projected_separation_b / Rs (normalized projected separation)
        d = projected_separation_b / star_radius_stellar_radii
        
        # Conditions for overlap and occultation (star blocking planet's light):
        # Full occultation if d < 1 - p (star fully covers planet) AND planet is behind star
        # Partial occultation if 1 - p <= d < 1 + p AND planet is behind star
        # No occultation if d >= 1 + p OR planet is in front of star

        for i in range(len(times_days)):
            # Check if planet is behind the star (simplified: z_rel_host > 0)
            # A more robust check might use orbital phase or specific geometry.
            if z_rel_host[i] > 0: # Planet is behind the star
                # Check for overlap based on normalized separation 'd'
                if d[i] <= (1 - p): # Full occultation (if star is larger or equal size than planet)
                    occultation_factor[i] = 0.0
                elif d[i] < (1 + p): # Partial occultation
                    # Linear approximation for partial phase (very simple, not precise)
                    # From 0 (full eclipse) to 1 (no eclipse).
                    # This is just a placeholder; a real implementation needs the full Lambda function.
                    # As a rough approximation: scale between 0 and 1.
                    # When d = 1-p, it's full. When d = 1+p, it's none.
                    # fractional_unocculted = (d[i] - (1 - p)) / (2 * p) # Fraction of distance
                    # occultation_factor[i] = np.clip(fractional_unocculted, 0.0, 1.0)
                    
                    # For a truly simplified step-function-like behavior, but allowing a brief partial phase:
                    # If it's within the 'eclipse window' of d, then assume some obscuration.
                    # This is still very basic and not a geometric integral.
                    # Let's keep it simple: 0 if fully occulted, 1 if fully visible.
                    # And use a smooth transition if it is partial, for numerical stability.
                    
                    # Using the transit duration-like calculation for primary transit,
                    # this eclipse factor would be `(1 - Lambda(d,p))`.
                    # For now, let's keep the core simple (step function based on closest approach)
                    # and allow for more complex Lambda functions to be integrated in future phases.
                    
                    # A basic model: if d < (1-p), factor is 0. If d > (1+p), factor is 1.
                    # Between them, linearly interpolate.
                    # This is for the *fraction of light hidden*. So output is 1 - hidden_fraction.
                    # hidden_fraction = (d[i] - (1-p)) / (2*p) if d[i] >= (1-p) else 0 # 0 when fully eclipsed
                    # hidden_fraction = np.clip(1 - (d[i] - (1-p)) / (2*p), 0.0, 1.0) # 1 at (1-p), 0 at (1+p)
                    # This gives 1 when fully eclipsed, 0 when fully visible. We want the opposite.
                    
                    # We want the *fraction of planetary light visible*:
                    # Visible = 0.0 if d <= (1-p)
                    # Visible = 1.0 if d >= (1+p)
                    # Visible = (d - (1-p)) / (2*p) if (1-p) < d < (1+p) (linear ramp from 0 to 1)
                    
                    occultation_factor[i] = np.clip((d[i] - (1 - p)) / (2 * p), 0.0, 1.0) # Linear interpolation for partial
                else: # d >= (1 + p) - No overlap (planet fully visible)
                    occultation_factor[i] = 1.0
            else: # Planet is in front of the star (z_rel_host <= 0) or far away, so no secondary eclipse
                occultation_factor[i] = 1.0 
        
        return occultation_factor.astype(np.float64)

    @staticmethod
    def calculate_binary_star_barycentric_positions(
        star1_mass_solar: float, star2_mass_solar: float,
        binary_period_days: float, binary_semimajor_axis_stellar_radii: float,
        binary_inclination_deg: float, binary_eccentricity: float,
        binary_argument_of_periastron_deg: float, binary_epoch_periastron_days: float,
        times_days: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculates the 2D projected (x, y) positions and the line-of-sight (z) distance
        of Star1 and Star2 relative to the system's barycenter at given times.

        :param star1_mass_solar: Mass of the primary star in solar masses.
        :param star2_mass_solar: Mass of the secondary star in solar masses.
        :param binary_period_days: Orbital period of the binary system in days.
        :param binary_semimajor_axis_stellar_radii: Semi-major axis of the binary system (a = a1 + a2) in stellar radii.
        :param binary_inclination_deg: Orbital inclination of the binary system in degrees.
        :param binary_eccentricity: Orbital eccentricity of the binary system.
        :param binary_argument_of_periastron_deg: Argument of periastron in degrees for the binary orbit.
        :param binary_epoch_periastron_days: Time (in days) of periastron passage for the binary orbit.
        :param times_days: Array of time points in days.
        :return: A tuple (x1_bary_proj, y1_bary_proj, z1_bary_los,
                          x2_bary_proj, y2_bary_proj, z2_bary_los)
                 where coordinates are in stellar radii (consistent with binary_semimajor_axis_stellar_radii).
                 All outputs are numpy arrays. Returns zeros if input parameters are invalid.
        """
        total_mass_solar = star1_mass_solar + star2_mass_solar
        
        if total_mass_solar <= 0 or binary_period_days <= 0 or binary_semimajor_axis_stellar_radii <= 0:
            zeros_array = np.zeros_like(times_days, dtype=np.float64)
            return (zeros_array, zeros_array, zeros_array, zeros_array, zeros_array, zeros_array)

        # Individual semi-major axes relative to barycenter
        a1_bary = binary_semimajor_axis_stellar_radii * star2_mass_solar / total_mass_solar
        a2_bary = binary_semimajor_axis_stellar_radii * star1_mass_solar / total_mass_solar

        # Calculate Mean Anomaly relative to periastron
        mean_anomaly = 2 * np.pi * (times_days - binary_epoch_periastron_days) / binary_period_days

        # Solve Kepler's equation for Eccentric Anomaly (E)
        eccentric_anomaly = OrbitalSolver._solve_kepler_equation(mean_anomaly, binary_eccentricity)

        # Calculate True Anomaly (f) from Eccentric Anomaly (E)
        true_anomaly = 2 * np.arctan2(np.sqrt(1 + binary_eccentricity) * np.sin(eccentric_anomaly / 2),
                                      np.sqrt(1 - binary_eccentricity) * np.cos(eccentric_anomaly / 2))

        # Calculate instantaneous orbital radius from barycenter for each star
        r1_bary = a1_bary * (1 - binary_eccentricity**2) / (1 + binary_eccentricity * np.cos(true_anomaly))
        r2_bary = a2_bary * (1 - binary_eccentricity**2) / (1 + binary_eccentricity * np.cos(true_anomaly))
        
        # Convert inclination and argument of periastron to radians
        inclination_rad = np.deg2rad(binary_inclination_deg)
        argument_of_periastron_rad = np.deg2rad(binary_argument_of_periastron_deg)

        # Angle in orbital plane (f + omega)
        angle_in_orbital_plane = true_anomaly + argument_of_periastron_rad

        # Projected X, Y positions on sky plane and Z along line of sight for each star
        # X is typically parallel to the line of nodes (intersection of orbital plane and sky plane)
        # Y is in the sky plane, perpendicular to X
        # Z is along the line of sight (depth)

        # Star1's positions (conventionally, this gives positions relative to barycenter)
        # The negative sign for X and Y in the `sin` and `cos` terms (and for `z`)
        # depends on the chosen coordinate system convention for observer view vs. orbital elements.
        # A common convention for transits/eclipses is:
        # X = r * sin(f+omega) (along line of nodes, x-axis)
        # Y = -r * cos(f+omega) * cos(i) (perpendicular to X in sky plane)
        # Z = -r * cos(f+omega) * sin(i) (along line of sight, positive means away)
        # Here we follow a convention that for transits (angle_in_orbital_plane close to pi/2), X is separation.
        # And when the object is 'behind' (eclipse), Z is positive.
        
        x1_bary_proj = r1_bary * np.sin(angle_in_orbital_plane)
        y1_bary_proj = r1_bary * np.cos(angle_in_orbital_plane) * np.cos(inclination_rad)
        z1_bary_los  = r1_bary * np.cos(angle_in_orbital_plane) * np.sin(inclination_rad)

        # Star2's positions (opposite direction from barycenter)
        x2_bary_proj = -r2_bary * np.sin(angle_in_orbital_plane)
        y2_bary_proj = -r2_bary * np.cos(angle_in_orbital_plane) * np.cos(inclination_rad)
        z2_bary_los  = -r2_bary * np.cos(angle_in_orbital_plane) * np.sin(inclination_rad)

        return (x1_bary_proj.astype(np.float64), y1_bary_proj.astype(np.float64), z1_bary_los.astype(np.float64),
                x2_bary_proj.astype(np.float64), y2_bary_proj.astype(np.float64), z2_bary_los.astype(np.float64))