"""
Unit tests for Image Processing Tab
Tests image loading, processing operations, and visualization
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from src.gui.tabs.image_processing_tab import ImageProcessingTab


class TestImageProcessingTab(unittest.TestCase):
    """Test cases for Image Processing Tab"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test application"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures"""
        self.tab = ImageProcessingTab()
    
    def test_tab_initialization(self):
        """Test that tab initializes correctly"""
        self.assertIsNotNone(self.tab)
        self.assertIsNone(self.tab.original_image)
        self.assertIsNone(self.tab.processed_image)
        self.assertIsNone(self.tab.original_metadata)
    
    def test_operation_combo(self):
        """Test operation combo box"""
        self.assertEqual(self.tab.operation_combo.count(), 7)
        operations = [
            "Grayscale Conversion",
            "Gaussian Blur",
            "Median Blur",
            "Canny Edge Detection",
            "Threshold",
            "Adaptive Threshold",
            "Contrast Enhancement (CLAHE)"
        ]
        for i, op in enumerate(operations):
            self.assertEqual(self.tab.operation_combo.itemText(i), op)
    
    def test_process_button_disabled_initially(self):
        """Test that process button is disabled initially"""
        self.assertFalse(self.tab.process_btn.isEnabled())
        self.assertFalse(self.tab.save_btn.isEnabled())
    
    def test_operation_changed_updates_parameters(self):
        """Test that changing operation updates parameter controls"""
        # Test Grayscale (no parameters)
        self.tab.operation_combo.setCurrentText("Grayscale Conversion")
        self.tab._on_operation_changed("Grayscale Conversion")
        self.assertEqual(self.tab.params_layout.count(), 0)
        
        # Test Gaussian Blur (has kernel size)
        self.tab.operation_combo.setCurrentText("Gaussian Blur")
        self.tab._on_operation_changed("Gaussian Blur")
        self.assertGreater(self.tab.params_layout.count(), 0)
        self.assertTrue(hasattr(self.tab, 'gaussian_kernel_spin'))
        self.assertEqual(self.tab.gaussian_kernel_spin.value(), 5)
    
    def test_canny_edge_parameters(self):
        """Test Canny edge detection parameters"""
        self.tab.operation_combo.setCurrentText("Canny Edge Detection")
        self.tab._on_operation_changed("Canny Edge Detection")
        
        self.assertTrue(hasattr(self.tab, 'canny_thresh1_spin'))
        self.assertTrue(hasattr(self.tab, 'canny_thresh2_spin'))
        self.assertEqual(self.tab.canny_thresh1_spin.value(), 100.0)
        self.assertEqual(self.tab.canny_thresh2_spin.value(), 200.0)
    
    def test_threshold_parameters(self):
        """Test threshold parameters"""
        self.tab.operation_combo.setCurrentText("Threshold")
        self.tab._on_operation_changed("Threshold")
        
        self.assertTrue(hasattr(self.tab, 'thresh_value_spin'))
        self.assertTrue(hasattr(self.tab, 'thresh_type_combo'))
        self.assertEqual(self.tab.thresh_value_spin.value(), 127.0)
        self.assertEqual(self.tab.thresh_type_combo.count(), 5)
    
    def test_adaptive_threshold_parameters(self):
        """Test adaptive threshold parameters"""
        self.tab.operation_combo.setCurrentText("Adaptive Threshold")
        self.tab._on_operation_changed("Adaptive Threshold")
        
        self.assertTrue(hasattr(self.tab, 'adaptive_block_spin'))
        self.assertTrue(hasattr(self.tab, 'adaptive_c_spin'))
        self.assertEqual(self.tab.adaptive_block_spin.value(), 11)
        self.assertEqual(self.tab.adaptive_c_spin.value(), 2.0)
    
    def test_reset_all(self):
        """Test reset functionality"""
        # Set some values
        self.tab.original_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        self.tab.processed_image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        self.tab.process_btn.setEnabled(True)
        self.tab.save_btn.setEnabled(True)
        
        # Reset
        self.tab._reset_all()
        
        # Check that everything is reset
        self.assertIsNone(self.tab.original_image)
        self.assertIsNone(self.tab.processed_image)
        self.assertFalse(self.tab.process_btn.isEnabled())
        self.assertFalse(self.tab.save_btn.isEnabled())
        self.assertEqual(self.tab.operation_combo.currentIndex(), 0)
    
    def test_update_status(self):
        """Test status update functionality"""
        self.tab._update_status("Test message", "info")
        self.assertEqual(self.tab.status_label.text(), "Test message")
        
        self.tab._update_status("Success message", "success")
        self.assertEqual(self.tab.status_label.text(), "Success message")
    
    def test_apply_processing_no_image(self):
        """Test that processing fails gracefully when no image is loaded"""
        with patch('PyQt5.QtWidgets.QMessageBox.warning') as mock_warning:
            self.tab._apply_processing()
            mock_warning.assert_called_once()
    
    def test_display_images_no_image(self):
        """Test display images with no image loaded"""
        self.tab._display_images()
        # Should show placeholder
        self.assertEqual(len(self.tab.comparison_fig.axes), 1)
    
    def test_display_images_with_original(self):
        """Test display images with original image only"""
        # Create test image
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        self.tab.original_image = test_image
        
        self.tab._display_images()
        
        # Should show original image
        self.assertEqual(len(self.tab.comparison_fig.axes), 1)
    
    def test_display_images_with_both(self):
        """Test display images with both original and processed"""
        # Create test images
        original = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        processed = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        self.tab.original_image = original
        self.tab.processed_image = processed
        
        self.tab._display_images()
        
        # Should show side-by-side comparison
        self.assertEqual(len(self.tab.comparison_fig.axes), 2)
    
    def test_update_metadata_display(self):
        """Test metadata display update"""
        metadata = {
            'filename': 'test.png',
            'width': 100,
            'height': 100,
            'channels': 3,
            'dtype': 'uint8',
            'image_type': 'X-ray',
            'is_grayscale': False,
            'min_value': 0.0,
            'max_value': 255.0,
            'mean_value': 127.5,
            'std_value': 50.0,
            'file_size_mb': 0.1
        }
        
        self.tab._update_metadata_display(metadata)
        
        text = self.tab.metadata_text.toPlainText()
        self.assertIn("Original Image Metadata", text)
        self.assertIn("test.png", text)
        self.assertIn("100 × 100", text)
        self.assertIn("X-ray", text)


if __name__ == '__main__':
    unittest.main()
