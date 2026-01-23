"""
Image metadata handler for MediAnalyze Pro
Manages image metadata and processing history
"""

import logging
import os
from typing import Dict, List, Optional
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session

from ..database import get_session, crud

logger = logging.getLogger(__name__)


class ImageMetadataHandler:
    """
    Handles image metadata and processing history
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize metadata handler
        
        Args:
            session: Database session (if None, creates new session)
        """
        self.session = session
    
    def extract_metadata(
        self,
        image: np.ndarray,
        file_path: str,
        processing_method: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Extract comprehensive metadata from image
        
        Args:
            image: Image array
            file_path: Path to image file
            processing_method: Applied processing method
        
        Returns:
            Dictionary with metadata
        """
        file_stat = os.stat(file_path) if os.path.exists(file_path) else None
        
        height, width = image.shape[:2]
        channels = 1 if len(image.shape) == 2 else image.shape[2]
        
        metadata = {
            'filename': os.path.basename(file_path),
            'file_path': file_path,
            'width': int(width),
            'height': int(height),
            'channels': int(channels),
            'dtype': str(image.dtype),
            'is_grayscale': channels == 1,
            'min_value': float(np.min(image)),
            'max_value': float(np.max(image)),
            'mean_value': float(np.mean(image)),
            'std_value': float(np.std(image)),
            'processing_method': processing_method
        }
        
        if file_stat:
            metadata['file_size'] = int(file_stat.st_size)
            metadata['file_size_mb'] = round(file_stat.st_size / (1024 * 1024), 2)
            metadata['modified_date'] = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
        
        # Determine image type from filename/path
        metadata['image_type'] = self._detect_image_type(file_path)
        
        return metadata
    
    def _detect_image_type(self, file_path: str) -> str:
        """
        Detect image type from file path/name
        
        Args:
            file_path: Path to image file
        
        Returns:
            Detected image type
        """
        path_lower = file_path.lower()
        
        if 'xray' in path_lower or 'x-ray' in path_lower or 'chest' in path_lower:
            return 'X-ray'
        elif 'mri' in path_lower:
            return 'MRI'
        elif 'ct' in path_lower or 'ct_scan' in path_lower:
            return 'CT scan'
        elif 'ultrasound' in path_lower:
            return 'Ultrasound'
        else:
            return 'Unknown'
    
    def store_image_metadata(
        self,
        image: np.ndarray,
        file_path: str,
        output_path: Optional[str] = None,
        patient_id: Optional[int] = None,
        processing_method: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Store image metadata in database
        
        Args:
            image: Image array
            file_path: Original file path
            output_path: Path to processed image (if processed)
            patient_id: Optional patient ID
            processing_method: Applied processing method
            notes: Additional notes
        
        Returns:
            Image ID from database
        """
        session = self.session or get_session()
        should_close = self.session is None
        
        try:
            # Extract metadata
            metadata = self.extract_metadata(image, file_path, processing_method)
            
            # Use output_path if provided, otherwise use original path
            image_path = output_path or file_path
            
            # Store in database
            image_record = crud.insert_image_metadata(
                session=session,
                filename=metadata['filename'],
                image_path=image_path,
                patient_id=patient_id,
                image_type=metadata.get('image_type'),
                processing_method=processing_method,
                file_size=metadata.get('file_size'),
                width=metadata['width'],
                height=metadata['height'],
                notes=notes
            )
            
            session.commit()
            logger.info(f"Stored image metadata in database: image_id={image_record.image_id}")
            
            return image_record.image_id
            
        except Exception as e:
            logger.error(f"Error storing image metadata: {e}")
            session.rollback()
            raise
        finally:
            if should_close:
                session.close()
    
    def get_processing_history(
        self,
        image_id: Optional[int] = None,
        patient_id: Optional[int] = None
    ) -> List[Dict[str, any]]:
        """
        Get processing history for images
        
        Args:
            image_id: Filter by image ID
            patient_id: Filter by patient ID
        
        Returns:
            List of image records with metadata
        """
        session = self.session or get_session()
        should_close = self.session is None
        
        try:
            images = crud.retrieve_image_metadata(
                session=session,
                image_id=image_id,
                patient_id=patient_id
            )
            
            history = []
            for img in images:
                history.append({
                    'image_id': img.image_id,
                    'filename': img.filename,
                    'image_path': img.image_path,
                    'image_type': img.image_type,
                    'processing_method': img.processing_method,
                    'width': img.width,
                    'height': img.height,
                    'upload_date': img.upload_date.isoformat() if img.upload_date else None,
                    'notes': img.notes
                })
            
            return history
            
        finally:
            if should_close:
                session.close()
