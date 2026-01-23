"""
Image processing module for MediAnalyze Pro
Provides various image processing operations for medical images
"""

import logging
from typing import Optional, Tuple, Union
import numpy as np
import cv2

# Optional skimage import (for advanced features)
try:
    from skimage import exposure
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Provides image processing operations for medical images
    """
    
    @staticmethod
    def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
        """
        Convert image to grayscale
        
        Args:
            image: Input image (RGB or grayscale)
        
        Returns:
            Grayscale image
        """
        if len(image.shape) == 2:
            # Already grayscale
            return image.copy()
        
        if len(image.shape) == 3:
            if image.shape[2] == 3:
                # RGB to grayscale
                return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            elif image.shape[2] == 4:
                # RGBA to grayscale
                return cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
            else:
                # Single channel, take first channel
                return image[:, :, 0]
        
        raise ValueError(f"Invalid image shape: {image.shape}")
    
    @staticmethod
    def apply_gaussian_blur(
        image: np.ndarray,
        kernel_size: int = 5,
        sigma: Optional[float] = None
    ) -> np.ndarray:
        """
        Apply Gaussian blur to image
        
        Args:
            image: Input image
            kernel_size: Size of Gaussian kernel (must be odd)
            sigma: Standard deviation (if None, calculated from kernel_size)
        
        Returns:
            Blurred image
        """
        if kernel_size % 2 == 0:
            kernel_size += 1
            logger.warning(f"Kernel size must be odd, using {kernel_size}")
        
        if sigma is None:
            # Calculate sigma from kernel size
            sigma = 0.3 * ((kernel_size - 1) * 0.5 - 1) + 0.8
        
        blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)
        return blurred
    
    @staticmethod
    def apply_median_blur(
        image: np.ndarray,
        kernel_size: int = 5
    ) -> np.ndarray:
        """
        Apply median blur to image (effective for salt-and-pepper noise)
        
        Args:
            image: Input image
            kernel_size: Size of median filter kernel (must be odd)
        
        Returns:
            Filtered image
        """
        if kernel_size % 2 == 0:
            kernel_size += 1
            logger.warning(f"Kernel size must be odd, using {kernel_size}")
        
        if len(image.shape) == 3:
            # Multi-channel image
            blurred = cv2.medianBlur(image, kernel_size)
        else:
            # Grayscale
            blurred = cv2.medianBlur(image, kernel_size)
        
        return blurred
    
    @staticmethod
    def apply_canny_edge_detection(
        image: np.ndarray,
        threshold1: float = 100.0,
        threshold2: float = 200.0,
        aperture_size: int = 3
    ) -> np.ndarray:
        """
        Apply Canny edge detection
        
        Args:
            image: Input image (grayscale or RGB)
            threshold1: First threshold for hysteresis procedure
            threshold2: Second threshold for hysteresis procedure
            aperture_size: Aperture size for Sobel operator
        
        Returns:
            Binary edge image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = ImageProcessor.convert_to_grayscale(image)
        else:
            gray = image
        
        # Ensure uint8
        if gray.dtype != np.uint8:
            gray = (gray * 255 / gray.max()).astype(np.uint8)
        
        edges = cv2.Canny(gray, threshold1, threshold2, apertureSize=aperture_size)
        return edges
    
    @staticmethod
    def apply_threshold(
        image: np.ndarray,
        threshold_value: float = 127.0,
        max_value: float = 255.0,
        threshold_type: str = 'binary'
    ) -> np.ndarray:
        """
        Apply thresholding to image
        
        Args:
            image: Input image (grayscale)
            threshold_value: Threshold value
            max_value: Maximum value for binary thresholding
            threshold_type: Type of thresholding
                - 'binary': Binary thresholding
                - 'binary_inv': Inverse binary thresholding
                - 'trunc': Truncate thresholding
                - 'tozero': To zero thresholding
                - 'tozero_inv': Inverse to zero thresholding
        
        Returns:
            Thresholded image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = ImageProcessor.convert_to_grayscale(image)
        else:
            gray = image
        
        # Normalize to 0-255 if needed
        if gray.dtype != np.uint8:
            if gray.max() > 255:
                gray = (gray * 255 / gray.max()).astype(np.uint8)
            else:
                gray = gray.astype(np.uint8)
        
        # Map threshold type
        type_map = {
            'binary': cv2.THRESH_BINARY,
            'binary_inv': cv2.THRESH_BINARY_INV,
            'trunc': cv2.THRESH_TRUNC,
            'tozero': cv2.THRESH_TOZERO,
            'tozero_inv': cv2.THRESH_TOZERO_INV
        }
        
        if threshold_type not in type_map:
            raise ValueError(f"Unknown threshold type: {threshold_type}")
        
        _, thresholded = cv2.threshold(
            gray,
            threshold_value,
            max_value,
            type_map[threshold_type]
        )
        
        return thresholded
    
    @staticmethod
    def apply_adaptive_threshold(
        image: np.ndarray,
        max_value: float = 255.0,
        adaptive_method: str = 'mean',
        threshold_type: str = 'binary',
        block_size: int = 11,
        C: float = 2.0
    ) -> np.ndarray:
        """
        Apply adaptive thresholding
        
        Args:
            image: Input image (grayscale)
            max_value: Maximum value for binary thresholding
            adaptive_method: Adaptive method ('mean' or 'gaussian')
            threshold_type: Type of thresholding ('binary' or 'binary_inv')
            block_size: Size of neighborhood (must be odd)
            C: Constant subtracted from mean
        
        Returns:
            Thresholded image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = ImageProcessor.convert_to_grayscale(image)
        else:
            gray = image
        
        # Normalize to 0-255 if needed
        if gray.dtype != np.uint8:
            if gray.max() > 255:
                gray = (gray * 255 / gray.max()).astype(np.uint8)
            else:
                gray = gray.astype(np.uint8)
        
        # Ensure block_size is odd
        if block_size % 2 == 0:
            block_size += 1
        
        # Map adaptive method
        adaptive_map = {
            'mean': cv2.ADAPTIVE_THRESH_MEAN_C,
            'gaussian': cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        }
        
        # Map threshold type
        type_map = {
            'binary': cv2.THRESH_BINARY,
            'binary_inv': cv2.THRESH_BINARY_INV
        }
        
        if adaptive_method not in adaptive_map:
            raise ValueError(f"Unknown adaptive method: {adaptive_method}")
        if threshold_type not in type_map:
            raise ValueError(f"Unknown threshold type: {threshold_type}")
        
        thresholded = cv2.adaptiveThreshold(
            gray,
            max_value,
            adaptive_map[adaptive_method],
            type_map[threshold_type],
            block_size,
            C
        )
        
        return thresholded
    
    @staticmethod
    def enhance_contrast(
        image: np.ndarray,
        method: str = 'clahe',
        clip_limit: float = 2.0
    ) -> np.ndarray:
        """
        Enhance image contrast
        
        Args:
            image: Input image
            method: Enhancement method ('clahe', 'histogram_eq', 'adaptive')
            clip_limit: Clip limit for CLAHE
        
        Returns:
            Contrast-enhanced image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = ImageProcessor.convert_to_grayscale(image)
        else:
            gray = image
        
        # Normalize to 0-255 if needed
        if gray.dtype != np.uint8:
            if gray.max() > 255:
                gray = (gray * 255 / gray.max()).astype(np.uint8)
            else:
                gray = gray.astype(np.uint8)
        
        if method == 'clahe':
            # Contrast Limited Adaptive Histogram Equalization
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
        
        elif method == 'histogram_eq':
            # Global histogram equalization
            enhanced = cv2.equalizeHist(gray)
        
        elif method == 'adaptive':
            # Adaptive histogram equalization (using skimage if available)
            if HAS_SKIMAGE:
                try:
                    enhanced = exposure.equalize_adapthist(gray, clip_limit=clip_limit)
                    enhanced = (enhanced * 255).astype(np.uint8)
                except Exception as e:
                    logger.warning(f"Error with skimage adaptive equalization: {e}, using CLAHE instead")
                    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
                    enhanced = clahe.apply(gray)
            else:
                logger.debug("skimage not available, using CLAHE instead")
                clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
                enhanced = clahe.apply(gray)
        
        else:
            raise ValueError(f"Unknown enhancement method: {method}")
        
        return enhanced
    
    @staticmethod
    def normalize_image(
        image: np.ndarray,
        method: str = 'minmax',
        range_min: float = 0.0,
        range_max: float = 255.0
    ) -> np.ndarray:
        """
        Normalize image values
        
        Args:
            image: Input image
            method: Normalization method ('minmax' or 'zscore')
            range_min: Minimum value for minmax normalization
            range_max: Maximum value for minmax normalization
        
        Returns:
            Normalized image
        """
        if method == 'minmax':
            min_val = np.min(image)
            max_val = np.max(image)
            if max_val == min_val:
                return np.zeros_like(image)
            normalized = (image - min_val) / (max_val - min_val) * (range_max - range_min) + range_min
            return normalized.astype(np.uint8) if range_max <= 255 else normalized
        
        elif method == 'zscore':
            mean = np.mean(image)
            std = np.std(image)
            if std == 0:
                return np.zeros_like(image)
            normalized = (image - mean) / std
            # Scale to 0-255 for visualization
            normalized = ((normalized - normalized.min()) / (normalized.max() - normalized.min()) * 255).astype(np.uint8)
            return normalized
        
        else:
            raise ValueError(f"Unknown normalization method: {method}")
    
    @staticmethod
    def apply_morphological_operations(
        image: np.ndarray,
        operation: str = 'opening',
        kernel_size: int = 5,
        iterations: int = 1
    ) -> np.ndarray:
        """
        Apply morphological operations
        
        Args:
            image: Input binary image
            operation: Operation type ('opening', 'closing', 'erosion', 'dilation')
            kernel_size: Size of morphological kernel
            iterations: Number of iterations
        
        Returns:
            Processed image
        """
        # Ensure binary image
        if image.dtype != np.uint8:
            image = (image * 255 / image.max()).astype(np.uint8)
        
        # Create kernel
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        
        if operation == 'opening':
            result = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=iterations)
        elif operation == 'closing':
            result = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel, iterations=iterations)
        elif operation == 'erosion':
            result = cv2.erode(image, kernel, iterations=iterations)
        elif operation == 'dilation':
            result = cv2.dilate(image, kernel, iterations=iterations)
        else:
            raise ValueError(f"Unknown morphological operation: {operation}")
        
        return result
    
    @staticmethod
    def process_image_pipeline(
        image: np.ndarray,
        operations: list
    ) -> np.ndarray:
        """
        Apply multiple image processing operations in sequence
        
        Args:
            image: Input image
            operations: List of operation dictionaries
                Example: [
                    {'operation': 'convert_to_grayscale'},
                    {'operation': 'gaussian_blur', 'kernel_size': 5},
                    {'operation': 'canny_edge', 'threshold1': 100, 'threshold2': 200}
                ]
        
        Returns:
            Processed image
        """
        processed = image.copy()
        
        for i, op_config in enumerate(operations):
            operation = op_config.pop('operation', None)
            
            if operation == 'convert_to_grayscale':
                processed = ImageProcessor.convert_to_grayscale(processed)
            
            elif operation == 'gaussian_blur':
                processed = ImageProcessor.apply_gaussian_blur(processed, **op_config)
            
            elif operation == 'median_blur':
                processed = ImageProcessor.apply_median_blur(processed, **op_config)
            
            elif operation == 'canny_edge':
                processed = ImageProcessor.apply_canny_edge_detection(processed, **op_config)
            
            elif operation == 'threshold':
                processed = ImageProcessor.apply_threshold(processed, **op_config)
            
            elif operation == 'adaptive_threshold':
                processed = ImageProcessor.apply_adaptive_threshold(processed, **op_config)
            
            elif operation == 'enhance_contrast':
                processed = ImageProcessor.enhance_contrast(processed, **op_config)
            
            elif operation == 'normalize':
                processed = ImageProcessor.normalize_image(processed, **op_config)
            
            elif operation == 'morphological':
                processed = ImageProcessor.apply_morphological_operations(processed, **op_config)
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            logger.debug(f"Applied operation {i+1}/{len(operations)}: {operation}")
        
        return processed
