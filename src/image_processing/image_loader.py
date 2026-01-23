"""
Image loader module for MediAnalyze Pro
Loads medical images from various file formats
"""

import logging
import os
from typing import Dict, Optional, Tuple, Union
import numpy as np
import cv2
from PIL import Image, ImageOps
import imghdr

logger = logging.getLogger(__name__)


class ImageLoader:
    """
    Loads medical images from files (PNG, JPEG, DICOM)
    """
    
    SUPPORTED_FORMATS = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']
    DICOM_FORMATS = ['.dcm', '.dicom']
    
    def __init__(self):
        """Initialize image loader"""
        pass
    
    def load_image(
        self,
        file_path: str,
        grayscale: bool = False,
        target_size: Optional[Tuple[int, int]] = None
    ) -> Tuple[np.ndarray, Dict[str, any]]:
        """
        Load image from file
        
        Args:
            file_path: Path to image file
            grayscale: Whether to convert to grayscale immediately
            target_size: Optional target size (width, height) for resizing
        
        Returns:
            Tuple of (image_array, metadata)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        try:
            # Detect image format
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Check if DICOM
            if file_ext in self.DICOM_FORMATS:
                return self._load_dicom(file_path, grayscale, target_size)
            
            # Load using OpenCV (supports most formats)
            if grayscale:
                image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
            else:
                image = cv2.imread(file_path, cv2.IMREAD_COLOR)
                # Convert BGR to RGB (OpenCV uses BGR by default)
                if image is not None and len(image.shape) == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            if image is None:
                raise ValueError(f"Could not load image from {file_path}")
            
            # Resize if target size specified
            if target_size:
                image = cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, image)
            
            logger.info(
                f"Loaded image: {metadata['width']}x{metadata['height']}, "
                f"channels: {metadata['channels']}, format: {metadata['format']}"
            )
            
            return image, metadata
            
        except Exception as e:
            logger.error(f"Error loading image {file_path}: {e}")
            raise
    
    def _load_dicom(
        self,
        file_path: str,
        grayscale: bool,
        target_size: Optional[Tuple[int, int]]
    ) -> Tuple[np.ndarray, Dict[str, any]]:
        """
        Load DICOM image (if pydicom is available)
        
        Args:
            file_path: Path to DICOM file
            grayscale: Whether to return grayscale
            target_size: Optional target size
        
        Returns:
            Tuple of (image_array, metadata)
        """
        try:
            import pydicom
            ds = pydicom.dcmread(file_path)
            
            # Get pixel array
            image = ds.pixel_array.astype(np.float32)
            
            # Apply rescale slope and intercept if available
            if hasattr(ds, 'RescaleSlope') and hasattr(ds, 'RescaleIntercept'):
                image = image * ds.RescaleSlope + ds.RescaleIntercept
            
            # Normalize to 0-255 range
            image = ((image - image.min()) / (image.max() - image.min()) * 255).astype(np.uint8)
            
            # Convert to grayscale if needed
            if grayscale and len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Resize if needed
            if target_size:
                image = cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, image)
            metadata['dicom'] = True
            metadata['modality'] = getattr(ds, 'Modality', 'UNKNOWN')
            metadata['patient_id'] = getattr(ds, 'PatientID', None)
            
            return image, metadata
            
        except ImportError:
            raise ImportError(
                "pydicom is required for DICOM support. Install with: pip install pydicom"
            )
        except Exception as e:
            logger.error(f"Error loading DICOM file {file_path}: {e}")
            raise
    
    def _extract_metadata(
        self,
        file_path: str,
        image: np.ndarray
    ) -> Dict[str, any]:
        """
        Extract metadata from image
        
        Args:
            file_path: Path to image file
            image: Image array
        
        Returns:
            Dictionary with metadata
        """
        file_stat = os.stat(file_path)
        
        height, width = image.shape[:2]
        channels = 1 if len(image.shape) == 2 else image.shape[2]
        
        # Get image format
        file_ext = os.path.splitext(file_path)[1].lower()
        format_name = file_ext[1:].upper() if file_ext else 'UNKNOWN'
        
        metadata = {
            'file_path': file_path,
            'filename': os.path.basename(file_path),
            'width': int(width),
            'height': int(height),
            'channels': int(channels),
            'format': format_name,
            'file_size': int(file_stat.st_size),
            'file_size_mb': round(file_stat.st_size / (1024 * 1024), 2),
            'dtype': str(image.dtype),
            'is_grayscale': channels == 1,
            'min_value': float(np.min(image)),
            'max_value': float(np.max(image)),
            'mean_value': float(np.mean(image)),
            'std_value': float(np.std(image))
        }
        
        return metadata
    
    def load_image_batch(
        self,
        directory: str,
        pattern: str = "*.jpg",
        max_images: Optional[int] = None,
        grayscale: bool = False
    ) -> list:
        """
        Load multiple images from directory
        
        Args:
            directory: Directory containing images
            pattern: File pattern (e.g., "*.jpg", "*.png")
            max_images: Maximum number of images to load
            grayscale: Whether to load as grayscale
        
        Returns:
            List of (image_array, metadata) tuples
        """
        import glob
        
        if not os.path.isdir(directory):
            raise ValueError(f"Directory not found: {directory}")
        
        # Find all matching files
        search_pattern = os.path.join(directory, "**", pattern)
        image_files = glob.glob(search_pattern, recursive=True)
        
        if max_images:
            image_files = image_files[:max_images]
        
        logger.info(f"Found {len(image_files)} images in {directory}")
        
        images = []
        for file_path in image_files:
            try:
                image, metadata = self.load_image(file_path, grayscale=grayscale)
                images.append((image, metadata))
            except Exception as e:
                logger.warning(f"Skipping {file_path}: {e}")
        
        return images
    
    def save_image(
        self,
        image: np.ndarray,
        output_path: str,
        format: Optional[str] = None
    ) -> bool:
        """
        Save image to file
        
        Args:
            image: Image array
            output_path: Output file path
            format: Image format (if None, inferred from extension)
        
        Returns:
            True if successful
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # Determine format from extension if not provided
            if format is None:
                ext = os.path.splitext(output_path)[1].lower()
                format = ext[1:] if ext else 'PNG'
            
            # Convert to appropriate format
            if len(image.shape) == 3 and image.shape[2] == 3:
                # RGB image - convert BGR to RGB for OpenCV
                image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                cv2.imwrite(output_path, image_bgr)
            else:
                # Grayscale or single channel
                cv2.imwrite(output_path, image)
            
            logger.info(f"Saved image to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return False
    
    @staticmethod
    def validate_image(image: np.ndarray) -> Tuple[bool, Optional[str]]:
        """
        Validate image array
        
        Args:
            image: Image array to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if image is None:
            return False, "Image is None"
        
        if not isinstance(image, np.ndarray):
            return False, f"Image must be numpy array, got {type(image)}"
        
        if image.size == 0:
            return False, "Image is empty"
        
        if len(image.shape) < 2 or len(image.shape) > 3:
            return False, f"Invalid image shape: {image.shape}"
        
        if len(image.shape) == 3 and image.shape[2] not in [1, 3, 4]:
            return False, f"Invalid number of channels: {image.shape[2]}"
        
        return True, None
