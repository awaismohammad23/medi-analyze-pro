"""
Image Processing Tab for MediAnalyze Pro GUI
Provides medical image processing and analysis capabilities
"""

import sys
import os
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSlider, QSpinBox, QDoubleSpinBox, QGroupBox,
    QTextEdit, QSplitter, QScrollArea, QMessageBox, QFileDialog,
    QFormLayout, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import numpy as np
import matplotlib
# Use Qt5Agg backend for interactive plots in GUI
try:
    matplotlib.use('Qt5Agg')
except:
    matplotlib.use('Agg')  # Fallback to non-interactive
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.image_processing import ImageLoader, ImageProcessor, ImageMetadataHandler
from ..styles import COLORS


class ImageProcessingWorker(QThread):
    """Worker thread for image processing operations to prevent UI freezing"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(np.ndarray)
    error = pyqtSignal(str)
    
    def __init__(self, operation: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs
    
    def run(self):
        """Run image processing in background thread"""
        try:
            processor = ImageProcessor()
            image = self.kwargs['image']
            
            if self.operation == 'grayscale':
                self.progress.emit(50, "Converting to grayscale...")
                result = processor.convert_to_grayscale(image)
                
            elif self.operation == 'gaussian_blur':
                self.progress.emit(50, "Applying Gaussian blur...")
                kernel_size = self.kwargs.get('kernel_size', 5)
                sigma = self.kwargs.get('sigma', None)
                result = processor.apply_gaussian_blur(image, kernel_size, sigma)
                
            elif self.operation == 'median_blur':
                self.progress.emit(50, "Applying median blur...")
                kernel_size = self.kwargs.get('kernel_size', 5)
                result = processor.apply_median_blur(image, kernel_size)
                
            elif self.operation == 'canny_edge':
                self.progress.emit(50, "Detecting edges...")
                threshold1 = self.kwargs.get('threshold1', 100.0)
                threshold2 = self.kwargs.get('threshold2', 200.0)
                result = processor.apply_canny_edge_detection(image, threshold1, threshold2)
                
            elif self.operation == 'threshold':
                self.progress.emit(50, "Applying threshold...")
                threshold_value = self.kwargs.get('threshold_value', 127.0)
                threshold_type = self.kwargs.get('threshold_type', 'binary')
                result = processor.apply_threshold(image, threshold_value, 255.0, threshold_type)
                
            elif self.operation == 'adaptive_threshold':
                self.progress.emit(50, "Applying adaptive threshold...")
                adaptive_method = self.kwargs.get('adaptive_method', 'mean')
                threshold_type = self.kwargs.get('threshold_type', 'binary')
                block_size = self.kwargs.get('block_size', 11)
                C = self.kwargs.get('C', 2.0)
                result = processor.apply_adaptive_threshold(
                    image, 255.0, adaptive_method, threshold_type, block_size, C
                )
                
            elif self.operation == 'contrast_enhancement':
                self.progress.emit(50, "Enhancing contrast...")
                result = processor.enhance_contrast(image, method='clahe')
                
            else:
                raise ValueError(f"Unknown operation: {self.operation}")
            
            self.progress.emit(100, "Processing complete!")
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))


class ImageProcessingTab(QWidget):
    """Image Processing Tab - Medical Image Processing and Analysis"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_image = None
        self.processed_image = None
        self.original_metadata = None
        self.processed_metadata = None
        self.processing_worker = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Controls
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS['background']};
            }}
        """)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(8, 8, 8, 8)
        
        # Image upload section
        upload_group = self._create_upload_group()
        left_layout.addWidget(upload_group)
        
        # Processing controls
        processing_group = self._create_processing_group()
        left_layout.addWidget(processing_group)
        
        # Metadata display
        metadata_group = self._create_metadata_group()
        left_layout.addWidget(metadata_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.clicked.connect(self._reset_all)
        self.reset_btn.setMinimumHeight(38)
        self.reset_btn.setToolTip("Clear uploaded image and reset all processing settings")
        self.reset_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['secondary']}; "
            f"color: {COLORS['primary']}; "
            f"border: 1px solid {COLORS['primary']};"
            f"border-radius: 8px;"
            f"font-weight: 600;"
            f"font-size: 11pt;"
            f"padding: 8px 16px;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {COLORS['primary']}; "
            f"color: {COLORS['button_text']};"
            f"}}"
        )
        action_layout.addWidget(self.reset_btn)
        
        self.save_btn = QPushButton("Save Processed Image")
        self.save_btn.clicked.connect(self._save_processed_image)
        self.save_btn.setMinimumHeight(38)
        self.save_btn.setEnabled(False)
        self.save_btn.setToolTip("Save the processed image to a file (PNG or JPEG)")
        self.save_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['success']}; "
            f"color: {COLORS['button_text']}; "
            f"border: none;"
            f"border-radius: 8px;"
            f"font-weight: 600;"
            f"font-size: 11pt;"
            f"padding: 8px 16px;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: #27AE60;"
            f"}}"
            f"QPushButton:disabled {{"
            f"background-color: {COLORS['border']}; "
            f"color: {COLORS['text_secondary']}; "
            f"opacity: 0.5;"
            f"}}"
        )
        action_layout.addWidget(self.save_btn)
        
        left_layout.addLayout(action_layout)
        left_layout.addStretch()
        
        left_widget.setMinimumWidth(380)
        scroll_area.setWidget(left_widget)
        scroll_area.setMinimumWidth(400)
        scroll_area.setMaximumWidth(420)
        splitter.addWidget(scroll_area)
        
        # Right side: Image Display
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Image comparison display
        self.comparison_fig = Figure(figsize=(12, 6), dpi=100)
        self.comparison_canvas = FigureCanvas(self.comparison_fig)
        self.comparison_canvas.setFocusPolicy(Qt.ClickFocus)
        # Enable mouse wheel zoom
        self.comparison_canvas.mpl_connect('scroll_event', self._on_image_scroll)
        self.comparison_toolbar = NavigationToolbar(self.comparison_canvas, self)
        # Store original view limits for reset
        self.image_original_limits = None
        
        comparison_widget = QWidget()
        comparison_layout = QVBoxLayout(comparison_widget)
        comparison_layout.setContentsMargins(0, 0, 0, 0)
        comparison_layout.setSpacing(0)
        comparison_layout.addWidget(self.comparison_toolbar)
        comparison_layout.addWidget(self.comparison_canvas)
        
        right_layout.addWidget(comparison_widget)
        
        # Status bar
        self.status_label = QLabel("Ready - Upload an image to begin")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_primary']};
                padding: 8px;
                border-radius: 4px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        right_layout.addWidget(self.status_label)
        
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0)  # Left panel fixed width
        splitter.setStretchFactor(1, 1)   # Right panel takes remaining space
        
        main_layout.addWidget(splitter)
        
        # Initialize empty display
        self._init_image_display()
    
    def _create_upload_group(self) -> QGroupBox:
        """Create image upload section"""
        group = QGroupBox("Image Upload")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 12pt;
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: {COLORS['surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 20, 12, 12)
        
        # Upload button with clear label
        self.upload_btn = QPushButton("Upload Medical Image (X-ray, MRI, CT)")
        self.upload_btn.clicked.connect(self._upload_image)
        self.upload_btn.setMinimumHeight(42)
        self.upload_btn.setToolTip("Click to browse and upload a medical image file (PNG, JPEG, DICOM, etc.)")
        self.upload_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['primary']}; "
            f"color: {COLORS['button_text']}; "
            f"border: none;"
            f"border-radius: 8px;"
            f"font-weight: 600;"
            f"font-size: 11pt;"
            f"padding: 10px 20px;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {COLORS['primary_dark']};"
            f"}}"
        )
        layout.addWidget(self.upload_btn)
        
        # Image info
        self.image_info_label = QLabel("No image loaded")
        self.image_info_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['background']};
                color: {COLORS['text_secondary']};
                padding: 8px;
                border-radius: 6px;
                border: 1px solid {COLORS['border']};
                font-size: 10pt;
            }}
        """)
        self.image_info_label.setWordWrap(True)
        layout.addWidget(self.image_info_label)
        
        group.setLayout(layout)
        return group
    
    def _create_processing_group(self) -> QGroupBox:
        """Create image processing controls section"""
        group = QGroupBox("Image Processing")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 12pt;
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: {COLORS['surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 20, 12, 12)
        
        # Processing operation selection
        operation_layout = QVBoxLayout()
        operation_label = QLabel("Processing Operation:")
        operation_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        operation_layout.addWidget(operation_label)
        self.operation_combo = QComboBox()
        self.operation_combo.addItems([
            "Grayscale Conversion",
            "Gaussian Blur",
            "Median Blur",
            "Canny Edge Detection",
            "Threshold",
            "Adaptive Threshold",
            "Contrast Enhancement (CLAHE)"
        ])
        self.operation_combo.setMinimumHeight(38)
        self.operation_combo.currentTextChanged.connect(self._on_operation_changed)
        self.operation_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                padding: 8px 14px;
                border-radius: 8px;
                font-size: 11pt;
            }}
            QComboBox:hover {{
                border: 2px solid {COLORS['primary_light']};
                background-color: {COLORS['background']};
            }}
            QComboBox:focus {{
                border: 2px solid {COLORS['primary']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['surface']};
                border: 2px solid {COLORS['primary']};
                border-radius: 6px;
                selection-background-color: {COLORS['primary']};
                selection-color: white;
                padding: 4px;
                font-size: 11pt;
            }}
        """)
        operation_layout.addWidget(self.operation_combo)
        layout.addLayout(operation_layout)
        
        # Parameters container
        self.params_container = QWidget()
        self.params_layout = QVBoxLayout(self.params_container)
        self.params_layout.setSpacing(10)
        self.params_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.params_container)
        
        # Process button with clear label
        self.process_btn = QPushButton("Apply Image Processing")
        self.process_btn.clicked.connect(self._apply_processing)
        self.process_btn.setMinimumHeight(42)
        self.process_btn.setEnabled(False)
        self.process_btn.setToolTip("Click to apply the selected processing operation to the uploaded image")
        self.process_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['primary']}; "
            f"color: {COLORS['button_text']}; "
            f"border: none;"
            f"border-radius: 8px;"
            f"font-weight: 600;"
            f"font-size: 11pt;"
            f"padding: 10px 20px;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {COLORS['primary_dark']};"
            f"}}"
            f"QPushButton:disabled {{"
            f"background-color: {COLORS['border']}; "
            f"color: {COLORS['text_secondary']}; "
            f"opacity: 0.5;"
            f"}}"
        )
        layout.addWidget(self.process_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_metadata_group(self) -> QGroupBox:
        """Create metadata display section"""
        group = QGroupBox("Image Metadata")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 12pt;
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: {COLORS['surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 20, 12, 12)
        
        self.metadata_text = QTextEdit()
        self.metadata_text.setReadOnly(True)
        self.metadata_text.setMinimumHeight(150)
        self.metadata_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
            }}
        """)
        self.metadata_text.setPlainText("No image metadata available.")
        layout.addWidget(self.metadata_text)
        
        group.setLayout(layout)
        return group
    
    def _on_operation_changed(self, operation: str):
        """Update parameter controls based on selected operation"""
        # Clear existing parameters
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if operation == "Grayscale Conversion":
            # No parameters needed
            pass
            
        elif operation == "Gaussian Blur":
            # Kernel size
            kernel_layout = QVBoxLayout()
            kernel_label = QLabel("Kernel Size:")
            kernel_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
            kernel_layout.addWidget(kernel_label)
            self.gaussian_kernel_spin = QSpinBox()
            self.gaussian_kernel_spin.setMinimum(3)
            self.gaussian_kernel_spin.setMaximum(31)
            self.gaussian_kernel_spin.setValue(5)
            self.gaussian_kernel_spin.setSingleStep(2)
            self.gaussian_kernel_spin.setMinimumHeight(38)
            self.gaussian_kernel_spin.setStyleSheet(f"""
                QSpinBox {{
                    background-color: {COLORS['surface']};
                    color: {COLORS['text_primary']};
                    border: 2px solid {COLORS['border']};
                    padding: 8px 14px;
                    border-radius: 8px;
                    font-size: 11pt;
                }}
                QSpinBox:hover {{
                    border: 2px solid {COLORS['primary_light']};
                    background-color: {COLORS['background']};
                }}
                QSpinBox:focus {{
                    border: 2px solid {COLORS['primary']};
                }}
            """)
            kernel_layout.addWidget(self.gaussian_kernel_spin)
            self.params_layout.addLayout(kernel_layout)
            
        elif operation == "Median Blur":
            # Kernel size
            kernel_layout = QVBoxLayout()
            kernel_label = QLabel("Kernel Size:")
            kernel_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
            kernel_layout.addWidget(kernel_label)
            self.median_kernel_spin = QSpinBox()
            self.median_kernel_spin.setMinimum(3)
            self.median_kernel_spin.setMaximum(31)
            self.median_kernel_spin.setValue(5)
            self.median_kernel_spin.setSingleStep(2)
            self.median_kernel_spin.setMinimumHeight(38)
            self.median_kernel_spin.setStyleSheet(f"""
                QSpinBox {{
                    background-color: {COLORS['surface']};
                    color: {COLORS['text_primary']};
                    border: 2px solid {COLORS['border']};
                    padding: 8px 14px;
                    border-radius: 8px;
                    font-size: 11pt;
                }}
                QSpinBox:hover {{
                    border: 2px solid {COLORS['primary_light']};
                    background-color: {COLORS['background']};
                }}
                QSpinBox:focus {{
                    border: 2px solid {COLORS['primary']};
                }}
            """)
            kernel_layout.addWidget(self.median_kernel_spin)
            self.params_layout.addLayout(kernel_layout)
            
        elif operation == "Canny Edge Detection":
            # Threshold 1
            thresh1_layout = QVBoxLayout()
            thresh1_label = QLabel("Threshold 1:")
            thresh1_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
            thresh1_layout.addWidget(thresh1_label)
            self.canny_thresh1_spin = QDoubleSpinBox()
            self.canny_thresh1_spin.setMinimum(0.0)
            self.canny_thresh1_spin.setMaximum(500.0)
            self.canny_thresh1_spin.setValue(100.0)
            self.canny_thresh1_spin.setSingleStep(10.0)
            self.canny_thresh1_spin.setMinimumHeight(38)
            self.canny_thresh1_spin.setStyleSheet(f"""
                QDoubleSpinBox {{
                    background-color: {COLORS['surface']};
                    color: {COLORS['text_primary']};
                    border: 2px solid {COLORS['border']};
                    padding: 8px 14px;
                    border-radius: 8px;
                    font-size: 11pt;
                }}
                QDoubleSpinBox:hover {{
                    border: 2px solid {COLORS['primary_light']};
                    background-color: {COLORS['background']};
                }}
                QDoubleSpinBox:focus {{
                    border: 2px solid {COLORS['primary']};
                }}
            """)
            thresh1_layout.addWidget(self.canny_thresh1_spin)
            self.params_layout.addLayout(thresh1_layout)
            
            # Threshold 2
            thresh2_layout = QVBoxLayout()
            thresh2_label = QLabel("Threshold 2:")
            thresh2_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
            thresh2_layout.addWidget(thresh2_label)
            self.canny_thresh2_spin = QDoubleSpinBox()
            self.canny_thresh2_spin.setMinimum(0.0)
            self.canny_thresh2_spin.setMaximum(500.0)
            self.canny_thresh2_spin.setValue(200.0)
            self.canny_thresh2_spin.setSingleStep(10.0)
            self.canny_thresh2_spin.setMinimumHeight(38)
            self.canny_thresh2_spin.setStyleSheet(f"""
                QDoubleSpinBox {{
                    background-color: {COLORS['surface']};
                    color: {COLORS['text_primary']};
                    border: 2px solid {COLORS['border']};
                    padding: 8px 14px;
                    border-radius: 8px;
                    font-size: 11pt;
                }}
                QDoubleSpinBox:hover {{
                    border: 2px solid {COLORS['primary_light']};
                    background-color: {COLORS['background']};
                }}
                QDoubleSpinBox:focus {{
                    border: 2px solid {COLORS['primary']};
                }}
            """)
            thresh2_layout.addWidget(self.canny_thresh2_spin)
            self.params_layout.addLayout(thresh2_layout)
            
        elif operation == "Threshold":
            # Threshold value
            thresh_layout = QVBoxLayout()
            thresh_label = QLabel("Threshold Value:")
            thresh_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
            thresh_layout.addWidget(thresh_label)
            self.thresh_value_spin = QDoubleSpinBox()
            self.thresh_value_spin.setMinimum(0.0)
            self.thresh_value_spin.setMaximum(255.0)
            self.thresh_value_spin.setValue(127.0)
            self.thresh_value_spin.setSingleStep(1.0)
            self.thresh_value_spin.setMinimumHeight(38)
            self.thresh_value_spin.setStyleSheet(f"""
                QDoubleSpinBox {{
                    background-color: {COLORS['surface']};
                    color: {COLORS['text_primary']};
                    border: 2px solid {COLORS['border']};
                    padding: 8px 14px;
                    border-radius: 8px;
                    font-size: 11pt;
                }}
                QDoubleSpinBox:hover {{
                    border: 2px solid {COLORS['primary_light']};
                    background-color: {COLORS['background']};
                }}
                QDoubleSpinBox:focus {{
                    border: 2px solid {COLORS['primary']};
                }}
            """)
            thresh_layout.addWidget(self.thresh_value_spin)
            self.params_layout.addLayout(thresh_layout)
            
            # Threshold type
            type_layout = QVBoxLayout()
            type_label = QLabel("Threshold Type:")
            type_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
            type_layout.addWidget(type_label)
            self.thresh_type_combo = QComboBox()
            self.thresh_type_combo.addItems(["Binary", "Binary Inverse", "Truncate", "To Zero", "To Zero Inverse"])
            self.thresh_type_combo.setMinimumHeight(38)
            self.thresh_type_combo.setStyleSheet(f"""
                QComboBox {{
                    background-color: {COLORS['surface']};
                    color: {COLORS['text_primary']};
                    border: 2px solid {COLORS['border']};
                    padding: 8px 14px;
                    border-radius: 8px;
                    font-size: 11pt;
                }}
                QComboBox:hover {{
                    border: 2px solid {COLORS['primary_light']};
                    background-color: {COLORS['background']};
                }}
                QComboBox:focus {{
                    border: 2px solid {COLORS['primary']};
                }}
                QComboBox QAbstractItemView {{
                    background-color: {COLORS['surface']};
                    border: 2px solid {COLORS['primary']};
                    border-radius: 6px;
                    selection-background-color: {COLORS['primary']};
                    selection-color: white;
                    padding: 4px;
                    font-size: 11pt;
                }}
            """)
            type_layout.addWidget(self.thresh_type_combo)
            self.params_layout.addLayout(type_layout)
            
        elif operation == "Adaptive Threshold":
            # Block size
            block_layout = QVBoxLayout()
            block_label = QLabel("Block Size:")
            block_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
            block_layout.addWidget(block_label)
            self.adaptive_block_spin = QSpinBox()
            self.adaptive_block_spin.setMinimum(3)
            self.adaptive_block_spin.setMaximum(31)
            self.adaptive_block_spin.setValue(11)
            self.adaptive_block_spin.setSingleStep(2)
            self.adaptive_block_spin.setMinimumHeight(38)
            self.adaptive_block_spin.setStyleSheet(f"""
                QSpinBox {{
                    background-color: {COLORS['surface']};
                    color: {COLORS['text_primary']};
                    border: 2px solid {COLORS['border']};
                    padding: 8px 14px;
                    border-radius: 8px;
                    font-size: 11pt;
                }}
                QSpinBox:hover {{
                    border: 2px solid {COLORS['primary_light']};
                    background-color: {COLORS['background']};
                }}
                QSpinBox:focus {{
                    border: 2px solid {COLORS['primary']};
                }}
            """)
            block_layout.addWidget(self.adaptive_block_spin)
            self.params_layout.addLayout(block_layout)
            
            # C value
            c_layout = QVBoxLayout()
            c_label = QLabel("C Value:")
            c_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
            c_layout.addWidget(c_label)
            self.adaptive_c_spin = QDoubleSpinBox()
            self.adaptive_c_spin.setMinimum(-50.0)
            self.adaptive_c_spin.setMaximum(50.0)
            self.adaptive_c_spin.setValue(2.0)
            self.adaptive_c_spin.setSingleStep(0.5)
            self.adaptive_c_spin.setMinimumHeight(38)
            self.adaptive_c_spin.setStyleSheet(f"""
                QDoubleSpinBox {{
                    background-color: {COLORS['surface']};
                    color: {COLORS['text_primary']};
                    border: 2px solid {COLORS['border']};
                    padding: 8px 14px;
                    border-radius: 8px;
                    font-size: 11pt;
                }}
                QDoubleSpinBox:hover {{
                    border: 2px solid {COLORS['primary_light']};
                    background-color: {COLORS['background']};
                }}
                QDoubleSpinBox:focus {{
                    border: 2px solid {COLORS['primary']};
                }}
            """)
            c_layout.addWidget(self.adaptive_c_spin)
            self.params_layout.addLayout(c_layout)
            
        elif operation == "Contrast Enhancement (CLAHE)":
            # No parameters needed for basic CLAHE
            pass
    
    def _init_image_display(self):
        """Initialize empty image display"""
        self.comparison_fig.clear()
        ax = self.comparison_fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Upload a medical image to begin processing', 
                ha='center', va='center', transform=ax.transAxes,
                fontsize=14, color=COLORS['text_secondary'])
        ax.axis('off')
        self.comparison_fig.tight_layout()
        self.comparison_canvas.draw()
    
    def _upload_image(self):
        """Upload and load medical image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Upload Medical Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;DICOM Files (*.dcm *.dicom);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            self._update_status("Loading image...", "info")
            loader = ImageLoader()
            image, metadata = loader.load_image(file_path)
            
            self.original_image = image
            self.processed_image = None
            self.original_metadata = metadata
            
            # Update image info
            info_text = f"Image loaded:\n"
            info_text += f"Size: {metadata['width']} × {metadata['height']} px\n"
            info_text += f"Channels: {metadata['channels']}\n"
            info_text += f"Type: {metadata.get('image_type', 'Unknown')}\n"
            if 'file_size_mb' in metadata:
                info_text += f"File Size: {metadata['file_size_mb']} MB"
            self.image_info_label.setText(info_text)
            
            # Update metadata display
            self._update_metadata_display(metadata)
            
            # Display original image
            self._display_images()
            
            # Enable process button
            self.process_btn.setEnabled(True)
            
            self._update_status("Image loaded successfully", "success")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
    
    def _apply_processing(self):
        """Apply selected image processing operation"""
        if self.original_image is None:
            QMessageBox.warning(self, "No Image", "Please upload an image first.")
            return
        
        if self.processing_worker is not None and self.processing_worker.isRunning():
            QMessageBox.warning(self, "Processing", "Processing is already in progress. Please wait.")
            return
        
        operation = self.operation_combo.currentText()
        
        # Map operation to worker operation name
        operation_map = {
            "Grayscale Conversion": "grayscale",
            "Gaussian Blur": "gaussian_blur",
            "Median Blur": "median_blur",
            "Canny Edge Detection": "canny_edge",
            "Threshold": "threshold",
            "Adaptive Threshold": "adaptive_threshold",
            "Contrast Enhancement (CLAHE)": "contrast_enhancement"
        }
        
        worker_op = operation_map.get(operation)
        if not worker_op:
            QMessageBox.warning(self, "Invalid Operation", f"Unknown operation: {operation}")
            return
        
        # Prepare kwargs
        kwargs = {'image': self.original_image}
        
        if operation == "Gaussian Blur":
            kwargs['kernel_size'] = self.gaussian_kernel_spin.value()
        elif operation == "Median Blur":
            kwargs['kernel_size'] = self.median_kernel_spin.value()
        elif operation == "Canny Edge Detection":
            kwargs['threshold1'] = self.canny_thresh1_spin.value()
            kwargs['threshold2'] = self.canny_thresh2_spin.value()
        elif operation == "Threshold":
            kwargs['threshold_value'] = self.thresh_value_spin.value()
            type_map = {
                "Binary": "binary",
                "Binary Inverse": "binary_inv",
                "Truncate": "trunc",
                "To Zero": "tozero",
                "To Zero Inverse": "tozero_inv"
            }
            kwargs['threshold_type'] = type_map.get(self.thresh_type_combo.currentText(), "binary")
        elif operation == "Adaptive Threshold":
            kwargs['block_size'] = self.adaptive_block_spin.value()
            kwargs['C'] = self.adaptive_c_spin.value()
        
        # Start worker thread
        self.processing_worker = ImageProcessingWorker(worker_op, **kwargs)
        self.processing_worker.progress.connect(self._on_processing_progress)
        self.processing_worker.finished.connect(self._on_processing_finished)
        self.processing_worker.error.connect(self._on_processing_error)
        
        self.process_btn.setEnabled(False)
        self._update_status("Processing image...", "info")
        self.processing_worker.start()
    
    def _on_processing_progress(self, value: int, message: str):
        """Handle processing progress updates"""
        self._update_status(f"{message} ({value}%)", "info")
    
    def _on_processing_finished(self, processed_image: np.ndarray):
        """Handle processing completion"""
        self.processed_image = processed_image
        self.process_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        # Update metadata for processed image
        if self.original_metadata:
            handler = ImageMetadataHandler()
            operation = self.operation_combo.currentText()
            self.processed_metadata = handler.extract_metadata(
                processed_image,
                self.original_metadata.get('file_path', ''),
                processing_method=operation
            )
        
        # Update display
        self._display_images()
        
        # Update metadata display
        if self.processed_metadata:
            self._update_metadata_display(self.processed_metadata, is_processed=True)
        
        self._update_status("Processing complete!", "success")
    
    def _on_processing_error(self, error_msg: str):
        """Handle processing errors"""
        self.process_btn.setEnabled(True)
        QMessageBox.critical(self, "Processing Error", f"Failed to process image:\n{error_msg}")
        self._update_status(f"Error: {error_msg}", "error")
    
    def _display_images(self):
        """Display original and processed images side by side"""
        self.comparison_fig.clear()
        
        if self.original_image is None:
            self._init_image_display()
            return
        
        if self.processed_image is not None:
            # Side-by-side comparison
            ax1 = self.comparison_fig.add_subplot(121)
            ax2 = self.comparison_fig.add_subplot(122)
            
            # Original image
            if len(self.original_image.shape) == 2:
                ax1.imshow(self.original_image, cmap='gray')
            else:
                ax1.imshow(self.original_image)
            ax1.set_title('Original Image', fontsize=12, fontweight='bold')
            ax1.axis('off')
            
            # Processed image
            if len(self.processed_image.shape) == 2:
                ax2.imshow(self.processed_image, cmap='gray')
            else:
                ax2.imshow(self.processed_image)
            ax2.set_title('Processed Image', fontsize=12, fontweight='bold')
            ax2.axis('off')
            
            # Store original limits for reset
            self.image_original_limits = {
                0: (ax1.get_xlim(), ax1.get_ylim()),
                1: (ax2.get_xlim(), ax2.get_ylim())
            }
            
        else:
            # Only original image
            ax = self.comparison_fig.add_subplot(111)
            if len(self.original_image.shape) == 2:
                ax.imshow(self.original_image, cmap='gray')
            else:
                ax.imshow(self.original_image)
            ax.set_title('Original Image', fontsize=12, fontweight='bold')
            ax.axis('off')
            
            # Store original limits for reset
            self.image_original_limits = {
                0: (ax.get_xlim(), ax.get_ylim())
            }
        
        self.comparison_fig.tight_layout()
        self.comparison_canvas.draw()
        if hasattr(self, 'comparison_toolbar'):
            self.comparison_toolbar.update()
    
    def _update_metadata_display(self, metadata: Dict[str, Any], is_processed: bool = False):
        """Update metadata text display"""
        title = "Processed Image Metadata" if is_processed else "Original Image Metadata"
        text = f"{title}\n{'=' * 40}\n\n"
        
        text += f"Filename: {metadata.get('filename', 'N/A')}\n"
        text += f"Dimensions: {metadata.get('width', 'N/A')} × {metadata.get('height', 'N/A')} px\n"
        text += f"Channels: {metadata.get('channels', 'N/A')}\n"
        text += f"Data Type: {metadata.get('dtype', 'N/A')}\n"
        text += f"Image Type: {metadata.get('image_type', 'Unknown')}\n"
        text += f"Grayscale: {'Yes' if metadata.get('is_grayscale', False) else 'No'}\n\n"
        
        text += "Statistics:\n"
        text += f"  Min Value: {metadata.get('min_value', 'N/A'):.2f}\n"
        text += f"  Max Value: {metadata.get('max_value', 'N/A'):.2f}\n"
        text += f"  Mean Value: {metadata.get('mean_value', 'N/A'):.2f}\n"
        text += f"  Std Dev: {metadata.get('std_value', 'N/A'):.2f}\n\n"
        
        if 'file_size_mb' in metadata:
            text += f"File Size: {metadata['file_size_mb']} MB\n"
        
        if 'processing_method' in metadata and metadata['processing_method']:
            text += f"\nProcessing Method: {metadata['processing_method']}\n"
        
        self.metadata_text.setPlainText(text)
    
    def _save_processed_image(self):
        """Save processed image to file"""
        if self.processed_image is None:
            QMessageBox.warning(self, "No Processed Image", "No processed image to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Processed Image",
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            import cv2
            # Convert RGB to BGR for OpenCV
            if len(self.processed_image.shape) == 3:
                save_image = cv2.cvtColor(self.processed_image, cv2.COLOR_RGB2BGR)
            else:
                save_image = self.processed_image
            
            cv2.imwrite(file_path, save_image)
            QMessageBox.information(self, "Success", f"Processed image saved to:\n{file_path}")
            self._update_status("Image saved successfully", "success")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save image:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
    
    def _reset_all(self):
        """Reset all controls and images"""
        self.original_image = None
        self.processed_image = None
        self.original_metadata = None
        self.processed_metadata = None
        self.image_original_limits = None
        
        self.image_info_label.setText("No image loaded")
        self.metadata_text.setPlainText("No image metadata available.")
        self.process_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        
        # Reset operation combo
        self.operation_combo.setCurrentIndex(0)
        self._on_operation_changed(self.operation_combo.currentText())
        
        # Reset display
        self._init_image_display()
        
        self._update_status("Reset complete", "info")
    
    def _update_status(self, message: str, status_type: str = "info"):
        """Update status label"""
        color_map = {
            'info': COLORS['info'],
            'success': COLORS['success'],
            'warning': COLORS['warning'],
            'error': COLORS['error']
        }
        color = color_map.get(status_type, COLORS['text_primary'])
        
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['surface']};
                color: {color};
                padding: 8px;
                border-radius: 4px;
                border: 1px solid {COLORS['border']};
                font-weight: 500;
            }}
        """)
    
    def _on_image_scroll(self, event):
        """Handle mouse wheel zoom for image display"""
        if not self.comparison_fig.axes:
            return
        
        # Determine which subplot (if side-by-side) or single plot
        ax = None
        for a in self.comparison_fig.axes:
            if event.inaxes == a:
                ax = a
                break
        
        if ax is None:
            return
        
        # Get current limits
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        
        # Store original limits on first interaction
        if self.image_original_limits is None:
            self.image_original_limits = {}
            for i, a in enumerate(self.comparison_fig.axes):
                self.image_original_limits[i] = (a.get_xlim(), a.get_ylim())
        
        xdata = event.xdata
        ydata = event.ydata
        
        if xdata is None or ydata is None:
            return
        
        # Zoom factor (scroll up = zoom in, scroll down = zoom out)
        zoom_factor = 1.1 if event.button == 'up' else 0.9
        
        # Get distance from the cursor
        x_left = xdata - cur_xlim[0]
        x_right = cur_xlim[1] - xdata
        y_bottom = ydata - cur_ylim[0]
        y_top = cur_ylim[1] - ydata
        
        # Apply zoom centered on cursor position
        ax.set_xlim([xdata - x_left * zoom_factor, xdata + x_right * zoom_factor])
        ax.set_ylim([ydata - y_bottom * zoom_factor, ydata + y_top * zoom_factor])
        
        self.comparison_canvas.draw()
