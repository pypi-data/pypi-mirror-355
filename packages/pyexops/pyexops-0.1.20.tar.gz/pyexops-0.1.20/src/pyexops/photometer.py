# pyexops/photometer.py

import numpy as np
from scipy.optimize import least_squares
from scipy.ndimage import center_of_mass

class Photometer:
    """
    Simulates photometric extraction from an image, defining target and background pixels.
    Supports SAP, Optimal, PSF Fitting, and Difference Imaging Photometry.
    """
    def __init__(self, target_aperture_radius_pixels: float, 
                 background_aperture_inner_radius_pixels: float, 
                 background_aperture_outer_radius_pixels: float,
                 psf_kernel: np.ndarray = None, # New: PSF kernel for Optimal/PSF Fitting
                 read_noise_std: float = 5.0):  # New: Read noise for optimal weights
        """
        Initializes the photometer.
        :param target_aperture_radius_pixels: Radius of the main photometric aperture in pixels.
        :param background_aperture_inner_radius_pixels: Inner radius of the background annulus in pixels.
        :param background_aperture_outer_radius_pixels: Outer radius of the background annulus in pixels.
        :param psf_kernel: A 2D numpy array representing the PSF kernel, normalized to sum to 1.
                           Required for 'optimal' and 'psf_fitting' photometry.
        :param read_noise_std: Standard deviation of Gaussian read noise, used for optimal weighting.
        """
        self.target_aperture_radius = target_aperture_radius_pixels
        self.bg_inner_radius = background_aperture_inner_radius_pixels
        self.bg_outer_radius = background_aperture_outer_radius_pixels
        self.psf_kernel = psf_kernel
        self.read_noise_std = read_noise_std

        if self.bg_inner_radius <= self.target_aperture_radius:
            raise ValueError("Background inner radius must be strictly greater than target aperture radius.")
        if self.bg_outer_radius <= self.bg_inner_radius:
            raise ValueError("Background outer radius must be strictly greater than inner radius.")

    def define_apertures(self, star_center_pixel_x: int, star_center_pixel_y: int, 
                         image_shape: tuple) -> tuple[np.ndarray, np.ndarray]:
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

    def _estimate_background(self, image_data: np.ndarray, background_mask: np.ndarray) -> tuple[float, int]:
        """Estimates average background flux per pixel and count of background pixels."""
        background_pixels_count = np.sum(background_mask)
        if background_pixels_count > 0:
            avg_background_flux_per_pixel = np.sum(image_data[background_mask]) / background_pixels_count
        else:
            avg_background_flux_per_pixel = 0.0
        return avg_background_flux_per_pixel, background_pixels_count

    def extract_sap_flux(self, image_data: np.ndarray, target_mask: np.ndarray, 
                     background_mask: np.ndarray) -> tuple[float, float]:
        """
        Extracts flux using Simple Aperture Photometry (SAP).
        :return: (extracted_star_flux, estimated_background_flux_per_pixel)
        """
        total_target_flux = np.sum(image_data[target_mask])
        avg_background_flux_per_pixel, _ = self._estimate_background(image_data, background_mask)
        
        target_pixels_count = np.sum(target_mask)
        estimated_background_in_target = avg_background_flux_per_pixel * target_pixels_count
        
        extracted_star_flux = total_target_flux - estimated_background_in_target
        
        return extracted_star_flux, avg_background_flux_per_pixel

    def extract_optimal_flux(self, image_data: np.ndarray, target_mask: np.ndarray,
                            background_mask: np.ndarray, star_center_pixel: tuple) -> tuple[float, float]:
        """
        Extracts flux using Optimal Photometry. Requires a PSF kernel.
        :param star_center_pixel: (x_pixel, y_pixel) of the star's center.
        :return: (extracted_star_flux, estimated_background_flux_per_pixel)
        """
        if self.psf_kernel is None:
            raise ValueError("Optimal Photometry requires a PSF kernel to be provided during Photometer initialization.")

        avg_background_flux_per_pixel, _ = self._estimate_background(image_data, background_mask)

        # Create a PSF model image centered at star_center_pixel
        # This is a simplified application for optimal weights within the aperture
        # A more robust optimal phot would use a properly sampled PSF model at sub-pixel positions
        
        # Get a small region around the star for PSF modeling.
        # This assumes psf_kernel is centered and small enough.
        k_h, k_w = self.psf_kernel.shape
        x_min = max(0, int(star_center_pixel[0] - k_w // 2))
        x_max = min(image_data.shape[1], int(star_center_pixel[0] + k_w // 2) + k_w % 2)
        y_min = max(0, int(star_center_pixel[1] - k_h // 2))
        y_max = min(image_data.shape[0], int(star_center_pixel[1] + k_h // 2) + k_h % 2)

        # Ensure the cropped_psf_model has the same dimensions as the data it's applied to
        cropped_psf_model = np.zeros_like(image_data, dtype=float)
        
        # Place the kernel at the star's center within the image
        # This requires careful handling of padding if kernel is larger than crop or star is near edge
        px_start = int(star_center_pixel[0] - k_w // 2)
        py_start = int(star_center_pixel[1] - k_h // 2)
        
        # Calculate indices for placing the kernel into the larger array
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
        # Photon noise: proportional to flux (approximated by image_data)
        # Read noise: constant (self.read_noise_std**2)
        # We need to estimate the flux to calculate photon noise, a circular problem.
        # A common approximation: use the raw image data for photon noise estimate.
        # And subtract background to get star's light roughly for Poisson noise estimate.
        estimated_star_image = image_data - avg_background_flux_per_pixel
        estimated_star_image[estimated_star_image < 0] = 0 # No negative photon counts
        
        pixel_noise_variance = estimated_star_image + (self.read_noise_std**2) 
        pixel_noise_variance[pixel_noise_variance <= 0] = 1e-9 # Avoid division by zero/very small numbers
        
        # Calculate weights: w_i = P_i / sigma_i^2, where P_i is PSF model at pixel i
        weights = cropped_psf_model[target_mask] / pixel_noise_variance[target_mask]
        
        # Extract flux using optimal weighting formula
        # F_optimal = sum( (Data_i - BG_i) * Weight_i ) / sum( PSF_i * Weight_i )
        # where Data_i - BG_i is the background-subtracted flux at pixel i
        
        optimal_flux = np.sum((image_data[target_mask] - avg_background_flux_per_pixel) * weights) / \
                       np.sum(cropped_psf_model[target_mask] * weights)
        
        return optimal_flux, avg_background_flux_per_pixel

    def _psf_model_func(self, coords, flux, x_0, y_0, psf_kernel):
        """
        Generates a PSF model for fitting.
        coords: (Y, X) pixel coordinates.
        flux: total flux of the star.
        x_0, y_0: centroid of the PSF.
        psf_kernel: the pre-generated PSF kernel.
        """
        Y, X = coords
        
        # Calculate the size of the region to model
        model_h, model_w = Y.shape
        
        # Calculate kernel offset to place its center at (x_0, y_0)
        kernel_h, kernel_w = psf_kernel.shape
        
        # Create a canvas the size of the model region
        model_image = np.zeros((model_h, model_w), dtype=float)
        
        # Calculate the starting pixel for the kernel within the model_image
        # This involves float to int conversion for pixel indices
        offset_x = x_0 - kernel_w / 2.0
        offset_y = y_0 - kernel_h / 2.0
        
        # Integers for array indexing
        px_start = int(np.floor(offset_x))
        py_start = int(np.floor(offset_y))

        # Handle fractional offsets for sub-pixel accuracy.
        # This simplified version just places the kernel at the nearest integer pixel.
        # A more rigorous approach would interpolate the kernel to sub-pixel positions.
        
        # For simplicity in initial implementation, let's just place the kernel at the integer part
        # and assume the kernel is centered appropriately for the fitting.
        # The psf_kernel should be pre-centered at (k_w//2, k_h//2)
        
        # Let's simplify and make the psf_model_func directly return a sampled PSF for the given (x_0, y_0)
        # This would require sampling the kernel at sub-pixel offsets.
        # For an initial implementation using convolve and fixed kernels, this is tricky for least_squares.
        
        # Revisit: For PSF fitting, it's often better to have the PSF model function directly generate
        # the PSF image at subpixel shifts, or use a pre-sampled grid.
        # For simplicity, let's assume the PSF_kernel is already sampled at the pixel level.
        # We need to create a shifted version of psf_kernel.
        
        # A simpler approach for `least_squares` is to assume `x_0, y_0` are relative pixel offsets
        # within a small cutout, and the kernel is pre-sampled.

        # Let's simplify the PSF fitting setup to assume `x_0, y_0` are integer pixel offsets 
        # relative to the center of the `target_region_data`.
        # For a truly robust PSF fitting with sub-pixel, we'd need to interpolate `psf_kernel` or use a dedicated library.
        
        # For initial PSF fitting, let's keep it simple: assume the PSF kernel is shifted on a pixel grid.
        # This will limit sub-pixel precision but allow the basic fitting mechanism.
        
        # A more robust PSF fitting model for least_squares:
        # It takes the full grid of pixel coordinates Y, X
        # And creates a shifted kernel at (x_0, y_0)
        
        # This requires shifting the kernel:
        from scipy.ndimage import shift
        
        shifted_kernel = shift(psf_kernel, shift=[y_0 - kernel_h/2.0, x_0 - kernel_w/2.0], order=3, mode='constant', cval=0.0)
        
        # Ensure shifted_kernel has compatible dimensions with coords (Y, X) after the shift
        # This implies that psf_kernel should be generated large enough to cover the `target_region`
        # or the target_region should be small enough to be covered by the kernel.
        
        # For simplicity, let's assume `psf_kernel` is large enough to cover the target_region.
        # We also need to normalize shifted_kernel to sum to 1
        if np.sum(shifted_kernel) > 0:
            shifted_kernel /= np.sum(shifted_kernel)
        
        # Model image is flux * normalized shifted kernel
        return flux * shifted_kernel[Y.astype(int), X.astype(int)] # This indexing might be problematic if Y,X are outside kernel extent

    def extract_psf_fitting_flux(self, image_data: np.ndarray, star_center_pixel: tuple, background_mask: np.ndarray) -> tuple[float, float, float, float]:
        """
        Extracts flux and centroid using PSF Fitting Photometry.
        Requires a PSF kernel. Returns flux and centroid (x,y).
        :param star_center_pixel: Initial guess (x,y) for star's centroid.
        :return: (extracted_star_flux, estimated_background_flux_per_pixel, fitted_x, fitted_y)
        """
        if self.psf_kernel is None:
            raise ValueError("PSF Fitting Photometry requires a PSF kernel to be provided during Photometer initialization.")

        avg_background_flux_per_pixel, _ = self._estimate_background(image_data, background_mask)
        
        # Define a small region (cutout) around the star for fitting
        cutout_half_size = int(np.ceil(max(self.psf_kernel.shape) / 2.0) + 2) # Cutout size based on PSF kernel
        
        x_start_cutout = max(0, int(star_center_pixel[0]) - cutout_half_size)
        x_end_cutout = min(image_data.shape[1], int(star_center_pixel[0]) + cutout_half_size)
        y_start_cutout = max(0, int(star_center_pixel[1]) - cutout_half_size)
        y_end_cutout = min(image_data.shape[0], int(star_center_pixel[1]) + cutout_half_size)
        
        target_region_data = image_data[y_start_cutout:y_end_cutout, x_start_cutout:x_end_cutout]
        
        # Subtract background from the cutout
        target_region_data_bg_subtracted = target_region_data - avg_background_flux_per_pixel

        # Create coordinate grids for the cutout
        Y_coords, X_coords = np.indices(target_region_data.shape)
        
        # Define the residual function for least_squares
        def residuals_func(params, data, coords, psf_kernel_input):
            flux_fit, x_offset, y_offset = params
            # Create a model PSF at the current params.
            # We need to shift the `psf_kernel_input` to the subpixel `x_offset, y_offset`
            # and then scale by flux_fit.
            
            # Shift the PSF kernel according to the fitted x_offset, y_offset
            # The `shift` function expects `shift` in (dy, dx)
            # `psf_kernel_input` is typically centered at its own (h/2, w/2)
            # We want to shift it so its center aligns with (x_offset, y_offset)
            
            # Determine the shift relative to the center of the kernel to align with (x_offset, y_offset)
            kernel_h, kernel_w = psf_kernel_input.shape
            dy_shift = y_offset - kernel_h / 2.0
            dx_shift = x_offset - kernel_w / 2.0

            shifted_psf_model = shift(psf_kernel_input, shift=(dy_shift, dx_shift), order=3, mode='constant', cval=0.0)
            
            # Ensure the shifted model has the same size as the data for residual calculation
            # This requires careful cropping/padding of shifted_psf_model
            
            # Simple approach: assume that shifted_psf_model is generated large enough
            # and then just take the central part that matches `data.shape`
            
            # Ensure summation to 1 for flux scaling
            if np.sum(shifted_psf_model) > 0:
                shifted_psf_model /= np.sum(shifted_psf_model)

            # The model is flux * shifted_psf_model_sampled_at_coords
            # Simplification: Assume shifted_psf_model is the correct shape and directly represents the model.
            model = flux_fit * shifted_psf_model[:data.shape[0], :data.shape[1]]

            # Residuals are (data - model)
            return (data - model).ravel() # Flatten for least_squares

        # Initial guess for fitting parameters: [flux, x_centroid, y_centroid]
        # Initial flux guess: sum of pixels in cutout
        initial_flux_guess = np.sum(target_region_data_bg_subtracted)
        # Initial centroid guess: center of cutout relative to cutout's own origin
        initial_x_guess = target_region_data.shape[1] / 2.0
        initial_y_guess = target_region_data.shape[0] / 2.0

        initial_params = [initial_flux_guess, initial_x_guess, initial_y_guess]

        # Use the actual PSF kernel for fitting
        psf_kernel_for_fit = self.psf_kernel 
        
        # Bounds for parameters: flux > 0, centroids within cutout
        bounds_min = [0, 0, 0]
        bounds_max = [np.inf, target_region_data.shape[1], target_region_data.shape[0]]

        try:
            result = least_squares(residuals_func, initial_params, 
                                   args=(target_region_data_bg_subtracted, (Y_coords, X_coords), psf_kernel_for_fit),
                                   bounds=(bounds_min, bounds_max),
                                   method='trf', verbose=0)
            
            fitted_flux, fitted_x_offset, fitted_y_offset = result.x
            
            # Convert fitted offsets back to image pixel coordinates
            fitted_x = fitted_x_offset + x_start_cutout
            fitted_y = fitted_y_offset + y_start_cutout

        except Exception as e:
            print(f"PSF Fitting failed: {e}. Falling back to SAP for this frame.")
            fitted_flux, avg_background_flux_per_pixel = self.extract_sap_flux(image_data, target_mask, background_mask)
            fitted_x, fitted_y = star_center_pixel # Keep initial guess if fit fails
            
        return fitted_flux, avg_background_flux_per_pixel, fitted_x, fitted_y


    def extract_difference_imaging_flux(self, image_data: np.ndarray, template_image: np.ndarray, 
                                        star_center_pixel: tuple, background_mask: np.ndarray) -> tuple[float, float]:
        """
        Extracts flux using a simplified Difference Imaging Photometry (DIP) approach.
        Assumes perfect alignment and no PSF convolution between image and template.
        :param image_data: The 2D numpy array of image pixel values (current frame).
        :param template_image: The 2D numpy array of the reference template image.
        :param star_center_pixel: (x_pixel, y_pixel) of the star's center (for defining difference aperture).
        :param background_mask: Boolean mask for background pixels (for background of the difference image).
        :return: (extracted_star_flux, estimated_background_flux_per_pixel_from_difference)
        """
        if image_data.shape != template_image.shape:
            raise ValueError("Image data and template image must have the same shape for Difference Imaging.")

        # Subtract the template from the current image
        difference_image = image_data - template_image
        
        # Define a 'difference aperture' (can be same as target aperture)
        # We need a mask for this difference aperture relative to the star's current position.
        # For simplicity, we use the same `target_mask` as if it were on the difference image.
        target_mask, _ = self.define_apertures(int(star_center_pixel[0]), int(star_center_pixel[1]), image_data.shape)

        # Sum flux within the difference aperture
        total_difference_flux = np.sum(difference_image[target_mask])

        # Estimate background in the difference image (should ideally be near zero)
        avg_background_difference_per_pixel, _ = self._estimate_background(difference_image, background_mask)

        # The extracted flux from DIP is the *change* in flux. 
        # To get the total flux, we need to add the flux of the star in the template image.
        # This requires knowing the star's flux in the template (which is usually pre-calculated or part of the template creation).
        # For simplicity in this demo, let's just return the change for now.
        # A full DIP would sum flux in template aperture and add the difference.
        
        # Let's adjust this to return the full flux (template star flux + difference)
        # For simplicity, we'll extract SAP flux from the template using the same aperture.
        # In real DIP, this template flux might be a calibrated flux.
        template_star_flux, _ = self.extract_sap_flux(template_image, target_mask, background_mask)
        
        extracted_star_flux = template_star_flux + total_difference_flux - (avg_background_difference_per_pixel * np.sum(target_mask))

        return extracted_star_flux, avg_background_difference_per_pixel

    def _find_centroid(self, image_data: np.ndarray, star_center_pixel: tuple, search_radius_pixels: int = 5) -> tuple[float, float]:
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
        
        return centroid_x, centroid_y