# pyexops/src/pyexops/photometer.py

import numpy as np
from scipy.optimize import least_squares
from scipy.ndimage import center_of_mass, convolve 
from typing import Optional, Tuple

from .astrometry import Astrometry 

class Photometer:
    """
    Simulates photometric extraction from an image, defining target and background pixels.
    Supports SAP, Optimal, PSF Fitting, and Difference Imaging Photometry.
    """
    def __init__(self, target_aperture_radius_pixels: float, 
                 background_aperture_inner_radius_pixels: float, 
                 background_aperture_outer_radius_pixels: float,
                 psf_kernel: Optional[np.ndarray] = None, 
                 read_noise_std: float = 5.0,
                 star_center_pixel: Tuple[int, int] = (0, 0)): # NEW: star_center_pixel
        """
        Initializes the photometer.
        :param target_aperture_radius_pixels: Radius of the main photometric aperture in pixels.
        :param background_aperture_inner_radius_pixels: Inner radius of the background annulus in pixels.
        :param background_aperture_outer_radius_pixels: Outer radius of the background annulus in pixels.
        :param psf_kernel: A 2D numpy array representing the PSF kernel, normalized to sum to 1.
                           Required for 'optimal' and 'psf_fitting' photometry, and for PSF matching in DIP.
        :param read_noise_std: Standard deviation of Gaussian read noise, used for optimal weighting.
        :param star_center_pixel: (x_pixel, y_pixel) of the star's nominal center. Used for defining apertures
                                  and as initial guess for PSF fitting/alignment.
        """
        self.target_aperture_radius = target_aperture_radius_pixels
        self.bg_inner_radius = background_aperture_inner_radius_pixels
        self.bg_outer_radius = background_aperture_outer_radius_pixels
        self.psf_kernel = psf_kernel
        self.read_noise_std = read_noise_std
        self.star_center_pixel = star_center_pixel # Store it

        if self.bg_inner_radius <= self.target_aperture_radius:
            raise ValueError("Background inner radius must be strictly greater than target aperture radius.")
        if self.bg_outer_radius <= self.bg_inner_radius:
            raise ValueError("Background outer radius must be strictly greater than inner radius.")

    def define_apertures(self, star_center_pixel_x: int, star_center_pixel_y: int, 
                         image_shape: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates boolean masks for target and background apertures based on the star's center.
        These masks are used to select the relevant pixels for flux summation.
        :param star_center_pixel_x, star_center_pixel_y: Center of the star in pixels.
        :param image_shape: (height, width) of the image.
        :return: (target_mask, background_mask) - boolean numpy arrays.
        """
        height, width = image_shape
        
        y_coords, x_coords = np.indices((height, width))
        
        distances = np.sqrt((x_coords - star_center_pixel_x)**2 + (y_coords - star_center_pixel_y)**2)
        
        target_mask = distances <= self.target_aperture_radius
        
        background_mask = (distances >= self.bg_inner_radius) & \
                          (distances <= self.bg_outer_radius)
        
        return target_mask, background_mask

    def _estimate_background(self, image_data: np.ndarray, background_mask: np.ndarray) -> Tuple[float, int]:
        """Estimates average background flux per pixel and count of background pixels."""
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
                            background_mask: np.ndarray, star_center_pixel: Tuple[int, int]) -> Tuple[float, float]:
        """
        Extracts flux using Optimal Photometry. Requires a PSF kernel.
        :param image_data: The 2D numpy array of image pixel values.
        :param target_mask: Boolean mask for the target aperture.
        :param background_mask: Boolean mask for the background annulus.
        :param star_center_pixel: (x_pixel, y_pixel) of the star's center.
        :return: (extracted_star_flux, estimated_background_flux_per_pixel)
        """
        if self.psf_kernel is None:
            raise ValueError("Optimal Photometry requires a PSF kernel to be provided during Photometer initialization.")

        avg_background_flux_per_pixel, _ = self._estimate_background(image_data, background_mask)

        # Create a PSF model image centered at star_center_pixel
        # This is a simplified application for optimal weights within the aperture
        # A more robust optimal phot would use a properly sampled PSF model at sub-pixel positions
        
        k_h, k_w = self.psf_kernel.shape
        cropped_psf_model = np.zeros_like(image_data, dtype=float)
        
        px_start = int(star_center_pixel[0] - k_w // 2)
        py_start = int(star_center_pixel[1] - k_h // 2)
        
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


        # Define noise variance for each pixel (sum of photon noise and read noise)
        estimated_star_image = image_data - avg_background_flux_per_pixel
        estimated_star_image[estimated_star_image < 0] = 0 
        
        pixel_noise_variance = estimated_star_image + (self.read_noise_std**2) 
        pixel_noise_variance[pixel_noise_variance <= 0] = 1e-9 
        
        # Calculate weights: w_i = P_i / sigma_i^2, where P_i is PSF model at pixel i
        weights = cropped_psf_model[target_mask] / pixel_noise_variance[target_mask]
        
        optimal_flux = np.sum((image_data[target_mask] - avg_background_flux_per_pixel) * weights) / \
                       np.sum(cropped_psf_model[target_mask] * weights)
        
        return float(optimal_flux), float(avg_background_flux_per_pixel)

    def _psf_model_func(self, coords, flux, x_0, y_0, psf_kernel):
        """
        Helper function to generate a PSF model for fitting using scipy.ndimage.shift.
        coords: (Y, X) pixel coordinates from the cutout.
        flux: total flux of the star.
        x_0, y_0: centroid of the PSF relative to the cutout's origin.
        psf_kernel: the pre-generated PSF kernel (should be larger than the cutout or handled).
        """
        from scipy.ndimage import shift
        
        kernel_h, kernel_w = psf_kernel.shape
        
        # Calculate the required shift for the kernel to align its center with (x_0, y_0) in the cutout
        # The kernel is typically centered at (kernel_w/2.0, kernel_h/2.0)
        dy_shift = y_0 - (kernel_h / 2.0)
        dx_shift = x_0 - (kernel_w / 2.0)

        # Shift the kernel. Order 3 (cubic spline) is a good balance of speed and accuracy.
        shifted_kernel = shift(psf_kernel, shift=(dy_shift, dx_shift), order=3, mode='constant', cval=0.0)
        
        # Ensure the shifted kernel is normalized to conserve flux
        if np.sum(shifted_kernel) > 0:
            shifted_kernel /= np.sum(shifted_kernel)
        else: # Handle edge case where shift moves kernel completely out
            shifted_kernel = np.zeros_like(shifted_kernel)
            # Potentially place a single pixel if needed, or raise warning/error.
            # For fitting, it implies model is bad or star is outside.

        # The model is flux * the portion of the shifted_kernel that matches the data cutout shape.
        # This assumes psf_kernel is large enough that its shifted version covers the cutout.
        # If the shifted_kernel is smaller than the cutout, it will be implicitly padded by array slicing.
        model_image = flux * shifted_kernel[:coords[0].shape[0], :coords[0].shape[1]]

        return model_image.ravel() # Flatten for least_squares

    def extract_psf_fitting_flux(self, image_data: np.ndarray, star_center_pixel: Tuple[int, int], background_mask: np.ndarray) -> Tuple[float, float, float, float]:
        """
        Extracts flux and centroid using PSF Fitting Photometry.
        Requires a PSF kernel. Returns flux and centroid (x,y).
        :param image_data: The 2D numpy array of image pixel values.
        :param star_center_pixel: Initial guess (x,y) for star's centroid.
        :param background_mask: Boolean mask for background pixels (for background of the fitting region).
        :return: (extracted_star_flux, estimated_background_flux_per_pixel, fitted_x, fitted_y)
        """
        if self.psf_kernel is None:
            raise ValueError("PSF Fitting Photometry requires a PSF kernel to be provided during Photometer initialization.")

        avg_background_flux_per_pixel, _ = self._estimate_background(image_data, background_mask)
        
        # Define a small region (cutout) around the star for fitting
        # Cutout size based on PSF kernel, ensuring it's large enough to capture the PSF
        cutout_half_size = int(np.ceil(max(self.psf_kernel.shape) / 2.0) + 2) 
        
        x_start_cutout = max(0, int(star_center_pixel[0]) - cutout_half_size)
        x_end_cutout = min(image_data.shape[1], int(star_center_pixel[0]) + cutout_half_size)
        y_start_cutout = max(0, int(star_center_pixel[1]) - cutout_half_size)
        y_end_cutout = min(image_data.shape[0], int(star_center_pixel[1]) + cutout_half_size)
        
        target_region_data = image_data[y_start_cutout:y_end_cutout, x_start_cutout:x_end_cutout]
        
        # Subtract background from the cutout
        target_region_data_bg_subtracted = target_region_data - avg_background_flux_per_pixel

        # Create coordinate grids for the cutout (relative to cutout's top-left)
        Y_coords_cutout, X_coords_cutout = np.indices(target_region_data.shape)
        
        # Initial guess for fitting parameters: [flux, x_centroid_rel_cutout, y_centroid_rel_cutout]
        initial_flux_guess = np.sum(target_region_data_bg_subtracted)
        initial_x_guess_rel_cutout = star_center_pixel[0] - x_start_cutout
        initial_y_guess_rel_cutout = star_center_pixel[1] - y_start_cutout

        initial_params = [initial_flux_guess, initial_x_guess_rel_cutout, initial_y_guess_rel_cutout]

        # Bounds for parameters: flux > 0, centroids within cutout
        bounds_min = [0, 0, 0]
        bounds_max = [np.inf, target_region_data.shape[1], target_region_data.shape[0]]

        try:
            result = least_squares(self._psf_model_func, initial_params, 
                                   args=(target_region_data_bg_subtracted.ravel(), (Y_coords_cutout, X_coords_cutout), self.psf_kernel),
                                   bounds=(bounds_min, bounds_max),
                                   method='trf', verbose=0)
            
            fitted_flux, fitted_x_offset_rel_cutout, fitted_y_offset_rel_cutout = result.x
            
            # Convert fitted offsets back to global image pixel coordinates
            fitted_x = fitted_x_offset_rel_cutout + x_start_cutout
            fitted_y = fitted_y_offset_rel_cutout + y_start_cutout

        except Exception as e:
            # Fallback to SAP if PSF fitting fails
            # Note: For real applications, this fallback strategy needs careful consideration
            print(f"PSF Fitting failed: {e}. Falling back to SAP for this frame.")
            target_mask, _ = self.define_apertures(int(star_center_pixel[0]), int(star_center_pixel[1]), image_data.shape)
            fitted_flux, avg_background_flux_per_pixel = self.extract_sap_flux(image_data, target_mask, background_mask)
            fitted_x, fitted_y = float(star_center_pixel[0]), float(star_center_pixel[1]) # Keep initial guess if fit fails
            
        return float(fitted_flux), float(avg_background_flux_per_pixel), float(fitted_x), float(fitted_y)


    def extract_difference_imaging_flux(self, image_data: np.ndarray, template_image: np.ndarray, 
                                        star_center_pixel: Tuple[int, int], background_mask: np.ndarray,
                                        perform_alignment: bool = True, # NEW
                                        apply_psf_matching_kernel: bool = False) -> Tuple[float, float]: # NEW
        """
        Extracts flux using a simplified Difference Imaging Photometry (DIP) approach.
        Optionally performs image alignment and/or PSF matching.
        :param image_data: The 2D numpy array of image pixel values (current frame).
        :param template_image: The 2D numpy array of the reference template image.
        :param star_center_pixel: (x_pixel, y_pixel) of the star's center (for defining difference aperture).
        :param background_mask: Boolean mask for background pixels (for background of the difference image).
        :param perform_alignment: If True, uses Astrometry to align image_data to template_image.
        :param apply_psf_matching_kernel: If True, convolves the template_image with the photometer's psf_kernel
                                          before subtraction, to attempt PSF matching.
        :return: (extracted_star_flux, estimated_background_flux_per_pixel_from_difference)
        """
        if image_data.shape != template_image.shape:
            raise ValueError("Image data and template image must have the same shape for Difference Imaging.")
        
        processed_template = np.copy(template_image) # Work on a copy

        if perform_alignment: # NEW
            dy, dx = Astrometry.estimate_shift(processed_template, image_data)
            # Shift the current image to align with the template
            image_data_aligned = Astrometry.apply_shift(image_data, dy, dx)
            # Update star_center_pixel (though for DIP this is often not used for apertures, but good practice)
            # This shift is only applied to the image data, not the underlying star_center_pixel directly.
            # The apertures remain fixed for now relative to the detector, as they are usually defined.
            # For a more complex DIP, apertures would track the star.
        else:
            image_data_aligned = image_data

        if apply_psf_matching_kernel: # NEW
            if self.psf_kernel is None:
                raise ValueError("PSF matching for DIP requires a PSF kernel to be provided during Photometer initialization.")
            # Convolve the template with the representative PSF to smooth it, mimicking PSF matching
            processed_template = convolve(processed_template, self.psf_kernel, mode='constant', cval=0.0)

        # Subtract the processed template from the current image
        difference_image = image_data_aligned - processed_template # Use aligned image

        # Define a 'difference aperture' (can be same as target aperture)
        target_mask, _ = self.define_apertures(int(star_center_pixel[0]), int(star_center_pixel[1]), image_data.shape)

        # Sum flux within the difference aperture
        total_difference_flux = np.sum(difference_image[target_mask])

        # Estimate background in the difference image (should ideally be near zero)
        avg_background_difference_per_pixel, _ = self._estimate_background(difference_image, background_mask)

        # The extracted flux from DIP is the *change* in flux plus the template flux.
        template_star_flux, _ = self.extract_sap_flux(template_image, target_mask, background_mask)
        
        extracted_star_flux = template_star_flux + total_difference_flux - (avg_background_difference_per_pixel * np.sum(target_mask))

        return float(extracted_star_flux), float(avg_background_difference_per_pixel)

    def _find_centroid(self, image_data: np.ndarray, star_center_pixel: Tuple[int, int], search_radius_pixels: int = 5) -> Tuple[float, float]:
        """
        Estimates the centroid of the star using center of mass in a local region.
        :param image_data: The 2D numpy array of image pixel values.
        :param star_center_pixel: (x,y) initial guess for the star's center.
        :param search_radius_pixels: Radius of the square region around the initial guess to search.
        :return: (centroid_x, centroid_y) in pixel coordinates (float).
        """
        x_guess, y_guess = int(star_center_pixel[0]), int(star_center_pixel[1])
        
        # Define a cutout region around the star
        x_min = max(0, x_guess - search_radius_pixels)
        x_max = min(image_data.shape[1], x_guess + search_radius_pixels + 1)
        y_min = max(0, y_guess - search_radius_pixels)
        y_max = min(image_data.shape[0], y_guess + search_radius_pixels + 1)
        
        cutout = image_data[y_min:y_max, x_min:x_max]

        # Calculate center of mass. Handle cases with zero or negative flux.
        # Temporarily set negative fluxes to zero for center of mass calculation to avoid issues.
        cutout_positive = np.copy(cutout)
        cutout_positive[cutout_positive < 0] = 0

        # Avoid division by zero if cutout is all zeros
        if np.sum(cutout_positive) == 0:
            return float(x_guess), float(y_guess) # Fallback to initial guess
            
        com_y, com_x = center_of_mass(cutout_positive)
        
        # Convert back to global image coordinates
        centroid_x = x_min + com_x
        centroid_y = y_min + com_y
        
        return float(centroid_x), float(centroid_y)