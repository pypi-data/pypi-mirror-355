# pyexops/star.py

import numpy as np

class Spot:
    """Represents a single stellar spot (umbra + penumbra)."""
    def __init__(self, center_x: float, center_y: float, 
                 radius_umbra: float, radius_penumbra: float, 
                 contrast_umbra: float, contrast_penumbra: float):
        """
        Initializes a stellar spot.
        Coordinates (center_x, center_y) are relative to the star's center,
        in units of stellar radii. Radii are also in stellar radii.
        Contrast is flux reduction factor (e.g., 0.2 for 80% flux reduction, 
        meaning 20% of normal flux passes through the spot).
        """
        self.center_x = center_x
        self.center_y = center_y
        self.radius_umbra = radius_umbra
        self.radius_penumbra = radius_penumbra
        self.contrast_umbra = contrast_umbra
        self.contrast_penumbra = contrast_penumbra

    def get_flux_factor(self, x_rel: float, y_rel: float) -> float:
        """
        Calculates the flux reduction factor at a given point (x_rel, y_rel)
        relative to the star's center.
        """
        dist_from_spot_center = np.sqrt((x_rel - self.center_x)**2 + (y_rel - self.center_y)**2)

        if dist_from_spot_center <= self.radius_umbra:
            return self.contrast_umbra
        elif dist_from_spot_center <= self.radius_penumbra:
            if self.radius_penumbra == self.radius_umbra: 
                return self.contrast_umbra 
            
            factor = self.contrast_umbra + (1.0 - self.contrast_umbra) * \
                     (dist_from_spot_center - self.radius_umbra) / \
                     (self.radius_penumbra - self.radius_umbra)
            return factor
        else:
            return 1.0

class Star:
    """Represents the host star with limb darkening and spots."""
    def __init__(self, radius: float, base_flux: float, limb_darkening_coeffs: tuple = (0.5, 0.2)):
        """
        Initializes the star.
        :param radius: Radius of the star. In this simulator, this will implicitly be in "pixels"
                       or a consistent unit that determines its apparent size on the image.
        :param base_flux: Maximum flux of the star at its center (arbitrary units).
        :param limb_darkening_coeffs: (u1, u2) for quadratic limb darkening model:
                                      I(mu) = I(1) * [1 - u1*(1-mu) - u2*(1-mu)^2]
        """
        self.radius = radius
        self.base_flux = base_flux
        self.u1, self.u2 = limb_darkening_coeffs
        self.spots = []

    def add_spot(self, spot: Spot):
        """Adds a spot to the star's surface."""
        self.spots.append(spot)

    def get_pixel_flux(self, x_rel: float, y_rel: float) -> float:
        """
        Calculates the flux of a single point (pixel) on the star's surface,
        relative to the star's center. Accounts for limb darkening and spots.
        :param x_rel, y_rel: Coordinates relative to the star's center, in units of stellar radii.
        :return: Flux value at that point.
        """
        r_prime = np.sqrt(x_rel**2 + y_rel**2) 

        if r_prime > 1.0: 
            return 0.0

        mu = np.sqrt(1.0 - r_prime**2) 
        limb_darkened_flux = self.base_flux * (1.0 - self.u1 * (1.0 - mu) - self.u2 * (1.0 - mu)**2)

        spot_factor = 1.0
        for spot in self.spots:
            spot_factor *= spot.get_flux_factor(x_rel, y_rel)
        
        return limb_darkened_flux * spot_factor