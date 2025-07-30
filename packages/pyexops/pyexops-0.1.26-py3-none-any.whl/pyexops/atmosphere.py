# pyexops/src/pyexops/atmosphere.py

import numpy as np
from typing import List, Tuple, Union

class Atmosphere:
    """
    Represents an exoplanet's atmosphere, defining its effective (apparent) radius
    at different wavelengths due to absorption or scattering.
    """
    def __init__(self, planet_solid_radius_stellar_radii: float, transmission_model_data: List[Tuple[float, float]]):
        """
        Initializes the Atmosphere.
        :param planet_solid_radius_stellar_radii: The solid (base) radius of the planet in stellar radii.
                                                  This is the radius from the Planet class.
        :param transmission_model_data: A list of (wavelength_nm, effective_radius_stellar_radii) tuples.
                                        This data defines how the planet's apparent size changes with wavelength.
                                        The effective radius should already be in stellar radii.
                                        Data should be sorted by wavelength.
        """
        if not all(isinstance(x, (int, float)) and isinstance(y, (int, float)) for x, y in transmission_model_data):
            raise ValueError("transmission_model_data must be a list of (float, float) tuples.")
        if not all(transmission_model_data[i][0] <= transmission_model_data[i+1][0] for i in range(len(transmission_model_data) - 1)):
            raise ValueError("transmission_model_data must be sorted by wavelength.")

        self.planet_solid_radius_stellar_radii = planet_solid_radius_stellar_radii
        
        if not transmission_model_data:
            self.wavelengths_nm = np.array([])
            self.effective_radii_at_wavelengths = np.array([])
        else:
            self.wavelengths_nm = np.array([item[0] for item in transmission_model_data])
            self.effective_radii_at_wavelengths = np.array([item[1] for item in transmission_model_data])

    def get_effective_radius(self, wavelength_nm: float) -> float:
        """
        Returns the effective radius of the planet (including atmosphere) for a given wavelength.
        Performs linear interpolation if the wavelength is not directly in the model data.
        Extrapolates using the nearest known value if wavelength is outside the data range.

        :param wavelength_nm: The wavelength in nanometers.
        :return: The effective radius in stellar radii.
        """
        if len(self.wavelengths_nm) == 0:
            return self.planet_solid_radius_stellar_radii
        
        # Use np.interp for linear interpolation and extrapolation by nearest value
        effective_radius = np.interp(
            wavelength_nm, 
            self.wavelengths_nm, 
            self.effective_radii_at_wavelengths,
            left=self.effective_radii_at_wavelengths[0],  # Use first value for extrapolation below min wavelength
            right=self.effective_radii_at_wavelengths[-1] # Use last value for extrapolation above max wavelength
        )
        return float(effective_radius)