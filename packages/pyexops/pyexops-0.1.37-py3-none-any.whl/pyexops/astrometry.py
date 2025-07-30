# pyexops/src/pyexops/astrometry.py

import numpy as np
from scipy.signal import correlate2d
from scipy.ndimage import shift, center_of_mass
from typing import Tuple

class Astrometry:
    """
    A class containing static methods for astrometric tasks,
    such as estimating and applying image shifts for precise alignment.
    """

    @staticmethod
    def estimate_shift(image_ref: np.ndarray, image_target: np.ndarray,
                       search_box_half_size: int = 10) -> Tuple[float, float]:
        """
        Estimates the sub-pixel shift between a reference image and a target image
        using cross-correlation on a cutout around the brightest pixel.

        :param image_ref: The 2D numpy array of the reference image.
        :param image_target: The 2D numpy array of the image to be shifted.
        :param search_box_half_size: Half size of the square cutout around the brightest pixel
                                     for cross-correlation.
        :return: A tuple (dy, dx) representing the estimated shift in y and x pixels.
        """
        if image_ref.shape != image_target.shape:
            raise ValueError("Reference and target images must have the same shape.")

        # Find the brightest pixel in the reference image (assumed to be the star)
        ref_peak_y, ref_peak_x = np.unravel_index(np.argmax(image_ref), image_ref.shape)

        # Define cutout boundaries
        y_min = max(0, ref_peak_y - search_box_half_size)
        y_max = min(image_ref.shape[0], ref_peak_y + search_box_half_size + 1)
        x_min = max(0, ref_peak_x - search_box_half_size)
        x_max = min(image_ref.shape[1], ref_peak_x + search_box_half_size + 1)

        ref_cutout = image_ref[y_min:y_max, x_min:x_max]
        target_cutout = image_target[y_min:y_max, x_min:x_max]

        if ref_cutout.size == 0 or target_cutout.size == 0:
            return 0.0, 0.0 # Return no shift if cutouts are empty

        # Compute cross-correlation
        # 'full' output provides the full cross-correlation array
        correlation = correlate2d(ref_cutout, target_cutout, mode='full', boundary='fill', fillvalue=0)

        # Find the peak of the correlation
        peak_corr_y, peak_corr_x = np.unravel_index(np.argmax(correlation), correlation.shape)

        # Convert peak position to shift relative to the center of the correlation map
        # The center of the 'full' correlation map is (H_cutout - 1, W_cutout - 1)
        # where H_cutout, W_cutout are dimensions of the cutouts.
        h_cutout, w_cutout = ref_cutout.shape
        dy_shift_int = peak_corr_y - (h_cutout - 1)
        dx_shift_int = peak_corr_x - (w_cutout - 1)

        # For sub-pixel precision, compute center of mass on a small region around the peak.
        # Define a small window around the integer peak for CoM calculation.
        com_window_half_size = 2 # e.g., a 5x5 window
        com_y_min = max(0, peak_corr_y - com_window_half_size)
        com_y_max = min(correlation.shape[0], peak_corr_y + com_window_half_size + 1)
        com_x_min = max(0, peak_corr_x - com_window_half_size)
        com_x_max = min(correlation.shape[1], peak_corr_x + com_window_half_size + 1)

        com_region = correlation[com_y_min:com_y_max, com_x_min:com_x_max]
        if np.sum(com_region) == 0: # Avoid division by zero if region is all zeros
            com_y_rel, com_x_rel = com_window_half_size, com_window_half_size # Fallback to center of window
        else:
            com_y_rel, com_x_rel = center_of_mass(com_region)
        
        # Convert CoM relative to its window to full correlation map coords
        com_y_full = com_y_min + com_y_rel
        com_x_full = com_x_min + com_x_rel

        # Sub-pixel shift relative to correlation center
        dy_shift_subpixel = com_y_full - (h_cutout - 1)
        dx_shift_subpixel = com_x_full - (w_cutout - 1)

        return float(dy_shift_subpixel), float(dx_shift_subpixel)

    @staticmethod
    def apply_shift(image: np.ndarray, dy: float, dx: float, order: int = 3) -> np.ndarray:
        """
        Applies a sub-pixel shift to an image using spline interpolation.

        :param image: The 2D numpy array to be shifted.
        :param dy: The shift amount in the y-direction (pixels).
        :param dx: The shift amount in the x-direction (pixels).
        :param order: The order of the spline interpolation (0-5). Higher order is slower but smoother.
        :return: The shifted 2D numpy array.
        """
        return shift(image, shift=(dy, dx), order=order, mode='constant', cval=0.0)