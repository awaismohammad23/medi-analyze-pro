"""
Unit tests for image processing modules
Tests image loading, processing operations, and metadata handling
"""

import pytest
import os
import sys
import tempfile
import numpy as np
import cv2

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.image_processing.image_loader import ImageLoader
from src.image_processing.processor import ImageProcessor
from src.image_processing.metadata import ImageMetadataHandler
from src.database.connection import DatabaseConnection


@pytest.fixture
def sample_image():
    """Create sample test image"""
    # Create a simple test image (100x100 RGB)
    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    return image


@pytest.fixture
def sample_grayscale_image():
    """Create sample grayscale image"""
    image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
    return image


@pytest.fixture
def test_image_file(sample_image):
    """Create temporary image file for testing"""
    fd, image_path = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    
    # Save image
    cv2.imwrite(image_path, cv2.cvtColor(sample_image, cv2.COLOR_RGB2BGR))
    
    yield image_path
    
    if os.path.exists(image_path):
        os.remove(image_path)


@pytest.fixture
def db_connection():
    """Create a temporary database for testing"""
    import tempfile
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db_url = f'sqlite:///{db_path}'
    db_conn = DatabaseConnection(db_url)
    db_conn.create_tables()
    
    yield db_conn
    
    db_conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


class TestImageLoader:
    """Test image loading functionality"""
    
    def test_load_image(self, test_image_file):
        """Test loading image from file"""
        loader = ImageLoader()
        image, metadata = loader.load_image(test_image_file)
        
        assert image is not None
        assert len(image.shape) == 3  # RGB image
        assert metadata['width'] == 100
        assert metadata['height'] == 100
        assert metadata['channels'] == 3
    
    def test_load_image_grayscale(self, test_image_file):
        """Test loading image as grayscale"""
        loader = ImageLoader()
        image, metadata = loader.load_image(test_image_file, grayscale=True)
        
        assert len(image.shape) == 2  # Grayscale
        assert metadata['channels'] == 1
        assert metadata['is_grayscale'] is True
    
    def test_load_image_resize(self, test_image_file):
        """Test loading image with resizing"""
        loader = ImageLoader()
        image, metadata = loader.load_image(test_image_file, target_size=(50, 50))
        
        assert image.shape[:2] == (50, 50)
        assert metadata['width'] == 50
        assert metadata['height'] == 50
    
    def test_save_image(self, sample_image):
        """Test saving image to file"""
        loader = ImageLoader()
        
        fd, output_path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        
        try:
            success = loader.save_image(sample_image, output_path)
            assert success
            assert os.path.exists(output_path)
            
            # Verify can load it back
            loaded_image, _ = loader.load_image(output_path)
            assert loaded_image.shape == sample_image.shape
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_validate_image(self, sample_image):
        """Test image validation"""
        is_valid, error = ImageLoader.validate_image(sample_image)
        assert is_valid
        assert error is None
    
    def test_validate_image_invalid(self):
        """Test validation of invalid image"""
        # Test None
        is_valid, error = ImageLoader.validate_image(None)
        assert not is_valid
        assert error is not None
        
        # Test empty array
        empty_image = np.array([])
        is_valid, error = ImageLoader.validate_image(empty_image)
        assert not is_valid


class TestImageProcessor:
    """Test image processing operations"""
    
    def test_convert_to_grayscale(self, sample_image):
        """Test grayscale conversion"""
        gray = ImageProcessor.convert_to_grayscale(sample_image)
        
        assert len(gray.shape) == 2
        assert gray.shape[:2] == sample_image.shape[:2]
    
    def test_apply_gaussian_blur(self, sample_image):
        """Test Gaussian blur"""
        blurred = ImageProcessor.apply_gaussian_blur(sample_image, kernel_size=5)
        
        assert blurred.shape == sample_image.shape
        assert not np.array_equal(blurred, sample_image)  # Should be different
    
    def test_apply_median_blur(self, sample_image):
        """Test median blur"""
        blurred = ImageProcessor.apply_median_blur(sample_image, kernel_size=5)
        
        assert blurred.shape == sample_image.shape
    
    def test_apply_canny_edge_detection(self, sample_grayscale_image):
        """Test Canny edge detection"""
        edges = ImageProcessor.apply_canny_edge_detection(
            sample_grayscale_image,
            threshold1=100,
            threshold2=200
        )
        
        assert len(edges.shape) == 2
        assert edges.shape == sample_grayscale_image.shape
        # Edge image should be binary (0 or 255)
        assert np.all((edges == 0) | (edges == 255))
    
    def test_apply_threshold_binary(self, sample_grayscale_image):
        """Test binary thresholding"""
        thresholded = ImageProcessor.apply_threshold(
            sample_grayscale_image,
            threshold_value=127,
            threshold_type='binary'
        )
        
        assert thresholded.shape == sample_grayscale_image.shape
        # Binary threshold should be 0 or max_value
        assert np.all((thresholded == 0) | (thresholded == 255))
    
    def test_apply_adaptive_threshold(self, sample_grayscale_image):
        """Test adaptive thresholding"""
        thresholded = ImageProcessor.apply_adaptive_threshold(
            sample_grayscale_image,
            adaptive_method='mean',
            block_size=11
        )
        
        assert thresholded.shape == sample_grayscale_image.shape
        assert np.all((thresholded == 0) | (thresholded == 255))
    
    def test_enhance_contrast(self, sample_grayscale_image):
        """Test contrast enhancement"""
        enhanced = ImageProcessor.enhance_contrast(
            sample_grayscale_image,
            method='clahe'
        )
        
        assert enhanced.shape == sample_grayscale_image.shape
        assert enhanced.dtype == np.uint8
    
    def test_normalize_image(self, sample_image):
        """Test image normalization"""
        normalized = ImageProcessor.normalize_image(
            sample_image,
            method='minmax'
        )
        
        assert normalized.shape == sample_image.shape
        assert normalized.min() >= 0
        assert normalized.max() <= 255
    
    def test_apply_morphological_operations(self, sample_grayscale_image):
        """Test morphological operations"""
        # Create binary image first
        binary = ImageProcessor.apply_threshold(sample_grayscale_image, threshold_value=127)
        
        # Test opening
        opened = ImageProcessor.apply_morphological_operations(
            binary,
            operation='opening',
            kernel_size=5
        )
        
        assert opened.shape == binary.shape
    
    def test_process_image_pipeline(self, sample_image):
        """Test processing pipeline"""
        operations = [
            {'operation': 'convert_to_grayscale'},
            {'operation': 'gaussian_blur', 'kernel_size': 5},
            {'operation': 'canny_edge', 'threshold1': 100, 'threshold2': 200}
        ]
        
        processed = ImageProcessor.process_image_pipeline(sample_image, operations)
        
        assert processed is not None
        assert len(processed.shape) == 2  # Should be grayscale after first operation


class TestImageMetadataHandler:
    """Test image metadata handling"""
    
    def test_extract_metadata(self, sample_image, test_image_file):
        """Test metadata extraction"""
        handler = ImageMetadataHandler()
        metadata = handler.extract_metadata(sample_image, test_image_file)
        
        assert 'width' in metadata
        assert 'height' in metadata
        assert 'channels' in metadata
        assert metadata['width'] == 100
        assert metadata['height'] == 100
    
    def test_detect_image_type(self):
        """Test image type detection"""
        handler = ImageMetadataHandler()
        
        assert handler._detect_image_type('/path/to/chest_xray.png') == 'X-ray'
        assert handler._detect_image_type('/path/to/mri_scan.jpg') == 'MRI'
        assert handler._detect_image_type('/path/to/ct_scan.png') == 'CT scan'
    
    def test_store_image_metadata(self, sample_image, test_image_file, db_connection):
        """Test storing image metadata in database"""
        session = db_connection.get_session()
        handler = ImageMetadataHandler(session=session)
        
        image_id = handler.store_image_metadata(
            sample_image,
            test_image_file,
            processing_method='grayscale'
        )
        
        assert image_id > 0
        
        # Verify stored
        from src.database import crud
        images = crud.retrieve_image_metadata(session, image_id=image_id)
        assert len(images) == 1
        assert images[0].processing_method == 'grayscale'
        
        session.close()
    
    def test_get_processing_history(self, sample_image, test_image_file, db_connection):
        """Test retrieving processing history"""
        session = db_connection.get_session()
        handler = ImageMetadataHandler(session=session)
        
        # Store an image
        image_id = handler.store_image_metadata(
            sample_image,
            test_image_file,
            processing_method='test'
        )
        
        # Get history
        history = handler.get_processing_history(image_id=image_id)
        
        assert len(history) > 0
        assert history[0]['image_id'] == image_id
        
        session.close()


class TestIntegration:
    """Integration tests for image processing"""
    
    def test_load_process_store(self, test_image_file, db_connection):
        """Test complete workflow: load, process, store"""
        session = db_connection.get_session()
        
        # Load image
        loader = ImageLoader()
        image, metadata = loader.load_image(test_image_file)
        
        # Process image
        gray = ImageProcessor.convert_to_grayscale(image)
        blurred = ImageProcessor.apply_gaussian_blur(gray, kernel_size=5)
        edges = ImageProcessor.apply_canny_edge_detection(blurred)
        
        # Store metadata
        handler = ImageMetadataHandler(session=session)
        image_id = handler.store_image_metadata(
            edges,
            test_image_file,
            processing_method='canny_edge_detection'
        )
        
        assert image_id > 0
        
        session.close()
    
    def test_process_pipeline_with_real_image(self):
        """Test processing pipeline with real image data"""
        # Create a more realistic test image (simulating X-ray)
        xray_like = np.random.randint(0, 255, (512, 512), dtype=np.uint8)
        
        # Apply processing pipeline
        operations = [
            {'operation': 'normalize', 'method': 'minmax'},
            {'operation': 'gaussian_blur', 'kernel_size': 5},
            {'operation': 'enhance_contrast', 'method': 'clahe'},
            {'operation': 'canny_edge', 'threshold1': 50, 'threshold2': 150}
        ]
        
        processed = ImageProcessor.process_image_pipeline(xray_like, operations)
        
        assert processed is not None
        assert processed.shape == xray_like.shape
    
    def test_load_chest_xray_images(self):
        """Test loading actual chest X-ray images from dataset"""
        # Check if chest X-ray dataset exists
        chest_xray_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'datasets',
            'chest_xray',
            'val',
            'NORMAL'
        )
        
        if os.path.exists(chest_xray_path):
            loader = ImageLoader()
            
            # Try to load one image
            image_files = [f for f in os.listdir(chest_xray_path) if f.endswith('.jpeg')]
            
            if image_files:
                test_image_path = os.path.join(chest_xray_path, image_files[0])
                image, metadata = loader.load_image(test_image_path)
                
                assert image is not None
                assert metadata['width'] > 0
                assert metadata['height'] > 0
                assert metadata['image_type'] == 'X-ray'
        else:
            pytest.skip("Chest X-ray dataset not found")
