# pyexops/src/pyexops/photometer.py

import numpy as np
from scipy.optimize import least_squares
from scipy.ndimage import center_of_mass, convolve 
from typing import Optional, Tuple

from .astrometry import Astrometry 

class Photometer:
    """
    Simulates photometric extraction from an image, defining target and background pixels.
    Supports Simple Aperture Photometry (SAP), Optimal Photometry, PSF Fitting,
    and Difference Imaging Photometry (DIP).
    """
    def __init__(self, target_aperture_radius_pixels: float, 
                 background_aperture_inner_radius_pixels: float, 
                 background_aperture_outer_radius_pixels: float,
                 psf_kernel: Optional[np.ndarray] = None, 
                 read_noise_std: float = 5.0,
                 system_center_pixel: Tuple[int, int] = (0, 0)): # CORRECTED: Changed parameter name from star_center_pixel
        """
        Initializes the photometer.

        :param target_aperture_radius_pixels: Radius of the main photometric aperture in pixels.
        :param background_aperture_inner_radius_pixels: Inner radius of the background annulus in pixels.
        :param background_aperture_outer_radius_pixels: Outer radius of the background annulus in pixels.
        :param psf_kernel: A 2D numpy array representing the PSF kernel, normalized to sum to 1.
                           Required for 'optimal' and 'psf_fitting' photometry, and for PSF matching in DIP.
        :param read_noise_std: Standard deviation of Gaussian read noise, used for optimal weighting.
        :param system_center_pixel: (x_pixel, y_pixel) of the system's nominal barycenter/star center.
                                   Used for defining apertures and as initial guess for PSF fitting/alignment.
        :raises ValueError: If aperture radii are not correctly ordered.
        """
        self.target_aperture_radius = target_aperture_radius_pixels
        self.bg_inner_radius = background_aperture_inner_radius_pixels
        self.bg_outer_radius = background_aperture_outer_radius_pixels
        self.psf_kernel = psf_kernel
        self.read_noise_std = read_noise_std
        self.system_center_pixel = system_center_pixel # Store it, now for the system barycenter

        if self.bg_inner_radius <= self.target_aperture_radius:
            raise ValueError("Background inner radius must be strictly greater than target aperture radius.")
        if self.bg_outer_radius <= self.bg_inner_radius:
            raise ValueError("Background outer radius must be strictly greater than inner radius.")

    def define_apertures(self, center_x: int, center_y: int, 
                         image_shape: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates boolean masks for target and background apertures based on a given center.
        These masks are used to select the relevant pixels for flux summation.

        :param center_x: X-coordinate of the aperture center in pixels.
        :param center_y: Y-coordinate of the aperture center in pixels.
        :param image_shape: (height, width) of the image.
        :return: (target_mask, background_mask) - boolean numpy arrays.
        """
        height, width = image_shape
        
        y_coords, x_coords = np.indices((height, width))
        
        distances = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
        
        target_mask = distances <= self.target_aperture_radius
        
        background_mask = (distances >= self.bg_inner_radius) & \
                          (distances <= self.bg_outer_radius)
        
        return target_mask, background_mask

    def _estimate_background(self, image_data: np.ndarray, background_mask: np.ndarray) -> Tuple[float, int]:
        """
        Estimates the average background flux per pixel and the count of background pixels.

        :param image_data: The 2D numpy array of image pixel values.
        :param background_mask: Boolean mask for the background annulus.
        :return: (avg_background_flux_per_pixel, background_pixels_count)
        """
        background_pixels_count = np.sum(background_mask)
        if background_pixels_count > 0:
            avg_background_flux_per_pixel = np.sum(image_data[background_mask]) / background_pixels_count
        else:
            avg_background_flux_per_pixel = 0.0
        return float(avg_background_flux_per_pixel), int(background_pixels_count)

    def extract_sap_flux(self, image_data: np.ndarray, target_mask: np.ndarray, 
                     background_mask: np.ndarray) -> Tuple[float, float]:
        """
        Extracts flux using Simple Aperture Photometry (SAP).

        :param image_data: The 2D numpy array of image pixel values.
        :param target_mask: Boolean mask for the target aperture.
        :param background_mask: Boolean mask for the background annulus.
        :return: (extracted_star_flux, estimated_background_flux_per_pixel)
        """
        total_target_flux = np.sum(image_data[target_mask])
        avg_background_flux_per_pixel, _ = self._estimate_background(image_data, background_mask)
        
        target_pixels_count = np.sum(target_mask)
        estimated_background_in_target = avg_background_flux_per_pixel * target_pixels_count
        
        extracted_star_flux = total_target_flux - estimated_background_in_target
        
        return float(extracted_star_flux), float(avg_background_flux_per_pixel)

    def extract_optimal_flux(self, image_data: np.ndarray, target_mask: np.ndarray,
                            background_mask: np.ndarray, centroid_guess: Tuple[int, int]) -> Tuple[float, float]: 
        """
        Extracts flux using Optimal Photometry (based on a PSF kernel).

        :param image_data: The 2D numpy array of image pixel values.
        :param target_mask: Boolean mask for the target aperture.
        :param background_mask: Boolean mask for the background annulus.
        :param centroid_guess: (x_pixel, y_pixel) guess for the light source's center.
        :return: (extracted_star_flux, estimated_background_flux_per_pixel)
        :raises ValueError: If `psf_kernel` was not provided during Photometer initialization.
        """
        if self.psf_kernel is None:
            raise ValueError("Optimal Photometry requires a PSF kernel to be provided during Photometer initialization.")

        avg_background_flux_per_pixel, _ = self._estimate_background(image_data, background_mask)

        k_h, k_w = self.psf_kernel.shape
        cropped_psf_model = np.zeros_like(image_data, dtype=float)
        
        px_start = int(centroid_guess[0] - k_w // 2)
        py_start = int(centroid_guess[1] - k_h // 2)
        
        img_px_start = max(0, px_start)
        img_py_start = max(0, py_start)
        img_px_end = min(image_data.shape[1], px_start + k_w)
        img_py_end = min(image_data.shape[0], py_start + k_h)

        kernel_px_start = img_px_start - px_start
        kernel_py_start = img_py_start - py_start
        kernel_px_end = img_px_end - px_start
        kernel_py_end = img_py_end - py_start

        cropped_psf_model[img_py_start:img_py_end, img_px_start:img_px_end] = \
            self.psf_kernel[kernel_py_start:kernel_py_end, kernel_px_start:kernel_px_end]
        
        estimated_star_image = image_data - avg_background_flux_per_pixel
        estimated_star_image[estimated_star_image < 0] = 0 
        
        pixel_noise_variance = estimated_star_image + (self.read_noise_std**2) 
        pixel_noise_variance[pixel_noise_variance <= 0] = 1e-9 
        
        weights = cropped_psf_model[target_mask] / pixel_noise_variance[target_mask]
        
        optimal_flux = np.sum((image_data[target_mask] - avg_background_flux_per_pixel) * weights) / \
                       np.sum(cropped_psf_model[target_mask] * weights)
        
        return float(optimal_flux), float(avg_background_flux_per_pixel)

    def _psf_model_func(self, coords: Tuple[np.ndarray, np.ndarray], flux: float, x_0: float, y_0: float, psf_kernel: np.ndarray) -> np.ndarray:
        """
        Helper function to generate a PSF model for fitting using scipy.ndimage.shift.
        """
        from scipy.ndimage import shift
        
        kernel_h, kernel_w = psf_kernel.shape
        
        dy_shift = y_0 - (kernel_h / 2.0)
        dx_shift = x_0 - (kernel_w / 2.0)

        shifted_kernel = shift(psf_kernel, shift=(dy_shift, dx_shift), order=3, mode='constant', cval=0.0)
        
        if np.sum(shifted_kernel) > 0:
            shifted_kernel /= np.sum(shifted_kernel)
        else: 
            shifted_kernel = np.zeros_like(shifted_kernel)

        model_image = flux * shifted_kernel[:coords[0].shape[0], :coords[0].shape[1]]

        return model_image.ravel() 

    def extract_psf_fitting_flux(self, image_data: np.ndarray, centroid_guess: Tuple[int, int], background_mask: np.ndarray) -> Tuple[float, float, float, float]: 
        """
        Extracts flux and centroid using PSF Fitting Photometry.
        """
        if self.psf_kernel is None:
            raise ValueError("PSF Fitting Photometry requires a PSF kernel to be provided during Photometer initialization.")

        avg_background_flux_per_pixel, _ = self._estimate_background(image_data, background_mask)
        
        cutout_half_size = int(np.ceil(max(self.psf_kernel.shape) / 2.0) + 2) 
        
        x_start_cutout = max(0, int(centroid_guess[0]) - cutout_half_size)
        x_end_cutout = min(image_data.shape[1], int(centroid_guess[0]) + cutout_half_size)
        y_start_cutout = max(0, int(centroid_guess[1]) - cutout_half_size)
        y_end_cutout = min(image_data.shape[0], int(centroid_guess[1]) + cutout_half_size)
        
        target_region_data = image_data[y_start_cutout:y_end_cutout, x_start_cutout:x_end_cutout]
        
        target_region_data_bg_subtracted = target_region_data - avg_background_flux_per_pixel

        Y_coords_cutout, X_coords_cutout = np.indices(target_region_data.shape)
        
        initial_flux_guess = np.sum(target_region_data_bg_subtracted)
        initial_x_guess_rel_cutout = centroid_guess[0] - x_start_cutout
        initial_y_guess_rel_cutout = centroid_guess[1] - y_start_cutout

        initial_params = [initial_flux_guess, initial_x_guess_rel_cutout, initial_y_guess_rel_cutout]

        bounds_min = [0, 0, 0]
        bounds_max = [np.inf, target_region_data.shape[1], target_region_data.shape[0]]

        try:
            result = least_squares(lambda p, data_ravel, coords_tuple, kernel: self._psf_model_func(coords_tuple, p[0], p[1], p[2], kernel) - data_ravel,
                                   initial_params, 
                                   args=(target_region_data_bg_subtracted.ravel(), (Y_coords_cutout, X_coords_cutout), self.psf_kernel),
                                   bounds=(bounds_min, bounds_max),
                                   method='trf', verbose=0)
            
            fitted_flux, fitted_x_offset_rel_cutout, fitted_y_offset_rel_cutout = result.x
            
            fitted_x = fitted_x_offset_rel_cutout + x_start_cutout
            fitted_y = fitted_y_offset_rel_cutout + y_start_cutout

        except Exception as e:
            print(f"PSF Fitting failed: {e}. Falling back to SAP for this frame.")
            target_mask_sap, _ = self.define_apertures(int(centroid_guess[0]), int(centroid_guess[1]), image_data.shape)
            fitted_flux, avg_background_flux_per_pixel = self.extract_sap_flux(image_data, target_mask_sap, background_mask)
            fitted_x, fitted_y = float(centroid_guess[0]), float(centroid_guess[1]) 
            
        return float(fitted_flux), float(avg_background_flux_per_pixel), float(fitted_x), float(fitted_y)


    def extract_difference_imaging_flux(self, image_data: np.ndarray, template_image: np.ndarray, 
                                        system_center_pixel: Tuple[int, int], background_mask: np.ndarray, 
                                        perform_alignment: bool = True, 
                                        apply_psf_matching_kernel: bool = False) -> Tuple[float, float]: 
        """
        Extracts flux using a simplified Difference Imaging Photometry (DIP) approach.
        """
        if image_data.shape != template_image.shape:
            raise ValueError("Image data and template image must have the same shape for Difference Imaging.")
        
        processed_template = np.copy(template_image) 

        if perform_alignment: 
            dy, dx = Astrometry.estimate_shift(processed_template, image_data)
            image_data_aligned = Astrometry.apply_shift(image_data, dy, dx)
        else:
            image_data_aligned = image_data

        if apply_psf_matching_kernel: 
            if self.psf_kernel is None:
                raise ValueError("PSF matching for DIP requires a PSF kernel to be provided during Photometer initialization.")
            processed_template = convolve(processed_template, self.psf_kernel, mode='constant', cval=0.0)

        difference_image = image_data_aligned - processed_template 

        target_mask, _ = self.define_apertures(int(system_center_pixel[0]), int(system_center_pixel[1]), image_data.shape)

        total_difference_flux = np.sum(difference_image[target_mask])

        avg_background_difference_per_pixel, _ = self._estimate_background(difference_image, background_mask)

        template_star_flux, _ = self.extract_sap_flux(template_image, target_mask, background_mask)
        
        extracted_star_flux = template_star_flux + total_difference_flux - (avg_background_difference_per_pixel * np.sum(target_mask))

        return float(extracted_star_flux), float(avg_background_difference_per_pixel)

    def _find_centroid(self, image_data: np.ndarray, centroid_guess: Tuple[int, int], search_radius_pixels: int = 5) -> Tuple[float, float]: 
        """
        Estimates the centroid of the light source using center of mass in a local region.
        """
        x_guess, y_guess = int(centroid_guess[0]), int(centroid_guess[1])
        
        x_min = max(0, x_guess - search_radius_pixels)
        x_max = min(image_data.shape[1], x_guess + search_radius_pixels + 1)
        y_min = max(0, y_guess - search_radius_pixels)
        y_max = min(image_data.shape[0], y_guess + search_radius_pixels + 1)
        
        cutout = image_data[y_min:y_max, x_min:x_max]

        cutout_positive = np.copy(cutout)
        cutout_positive[cutout_positive < 0] = 0

        if np.sum(cutout_positive) == 0:
            return float(x_guess), float(y_guess) 
            
        com_y, com_x = center_of_mass(cutout_positive)
        
        centroid_x = x_min + com_x
        centroid_y = y_min + com_y
        
        return float(centroid_x), float(centroid_y)