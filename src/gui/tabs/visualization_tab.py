"""
Data Visualization Tab for MediAnalyze Pro GUI
Provides comprehensive visualization capabilities for all data types
"""

import sys
import os
import logging
from typing import Optional, Dict, Any, List, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSlider, QSpinBox, QDoubleSpinBox, QGroupBox,
    QTextEdit, QSplitter, QScrollArea, QMessageBox, QFileDialog,
    QFormLayout, QTabWidget, QLineEdit, QCheckBox, QStyle, QStyleOptionButton
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QPen, QColor
import pandas as pd
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

from src.database import get_session
from src.data_processing import DataRetriever, CorrelationAnalyzer
from src.signal_processing import SpectrumAnalyzer, SignalLoader
from src.image_processing import ImageLoader
from src.visualization import (
    TimeSeriesPlotter, ScatterPlotter, HeatmapPlotter,
    SpectrumPlotter, ImageViewer
)
from ..styles import COLORS

logger = logging.getLogger(__name__)


class CheckBoxWithTick(QCheckBox):
    """Custom checkbox with visible checkmark tick"""
    
    def __init__(self, text=""):
        super().__init__(text)
        self.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_primary']};
                font-size: 11pt;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {COLORS['border']};
                border-radius: 4px;
                background-color: {COLORS['surface']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}
        """)
    
    def paintEvent(self, event):
        """Override paint event to draw checkmark"""
        super().paintEvent(event)
        
        if self.isChecked():
            # Get the indicator rectangle
            opt = QStyleOptionButton()
            self.initStyleOption(opt)
            style = self.style()
            indicator_rect = style.subElementRect(QStyle.SE_CheckBoxIndicator, opt, self)
            
            # Draw checkmark
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor("white"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            
            # Draw checkmark path
            x = indicator_rect.x() + indicator_rect.width() * 0.2
            y = indicator_rect.y() + indicator_rect.height() * 0.5
            x2 = indicator_rect.x() + indicator_rect.width() * 0.4
            y2 = indicator_rect.y() + indicator_rect.height() * 0.7
            x3 = indicator_rect.x() + indicator_rect.width() * 0.8
            y3 = indicator_rect.y() + indicator_rect.height() * 0.3
            
            painter.drawLine(int(x), int(y), int(x2), int(y2))
            painter.drawLine(int(x2), int(y2), int(x3), int(y3))
            painter.end()


class VisualizationWorker(QThread):
    """Worker thread for visualization generation to prevent UI freezing"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object)  # Emits figure object
    error = pyqtSignal(str)
    
    def __init__(self, viz_type: str, **kwargs):
        super().__init__()
        self.viz_type = viz_type
        self.kwargs = kwargs
    
    def run(self):
        """Run visualization generation in background thread"""
        # Use non-interactive backend in worker thread to avoid GUI warnings
        # Note: Backend should be set before any matplotlib operations
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend for worker threads
        import warnings
        warnings.filterwarnings('ignore', category=UserWarning, message='.*GUI outside of the main thread.*')
        
        try:
            if self.viz_type == 'time_series':
                self.progress.emit(50, "Generating time-series plot...")
                plotter = TimeSeriesPlotter(figsize=(12, 6), dpi=100)
                fig = plotter.plot_health_metrics(
                    data=self.kwargs['data'],
                    time_column=self.kwargs.get('time_column'),
                    metrics=self.kwargs.get('metrics'),
                    title=self.kwargs.get('title', 'Health Metrics Over Time'),
                    show_plot=False
                )
                
            elif self.viz_type == 'scatter':
                self.progress.emit(50, "Generating scatter plot...")
                plotter = ScatterPlotter(figsize=(10, 8), dpi=100)
                fig = plotter.plot_correlation(
                    x_data=self.kwargs['x_data'],
                    y_data=self.kwargs['y_data'],
                    x_label=self.kwargs.get('x_label', 'Variable X'),
                    y_label=self.kwargs.get('y_label', 'Variable Y'),
                    title=self.kwargs.get('title'),
                    show_trendline=self.kwargs.get('show_trendline', True),
                    show_correlation=self.kwargs.get('show_correlation', True),
                    show_plot=False
                )
                
            elif self.viz_type == 'heatmap':
                self.progress.emit(50, "Generating heatmap...")
                plotter = HeatmapPlotter(figsize=(10, 8), dpi=100)
                fig = plotter.plot_correlation_matrix(
                    data=self.kwargs['data'],
                    title=self.kwargs.get('title', 'Correlation Matrix'),
                    cmap=self.kwargs.get('cmap', 'coolwarm'),
                    annotate=self.kwargs.get('annotate', True),
                    show_plot=False
                )
                
            elif self.viz_type == 'fft_spectrum':
                self.progress.emit(50, "Generating FFT spectrum...")
                plotter = SpectrumPlotter(figsize=(12, 6), dpi=100)
                fig = plotter.plot_fft_spectrum(
                    signal_data=self.kwargs['signal_data'],
                    sample_rate=self.kwargs['sample_rate'],
                    title=self.kwargs.get('title', 'FFT Spectrum'),
                    xlim=self.kwargs.get('xlim'),
                    show_plot=False
                )
                
            elif self.viz_type == 'image_comparison':
                self.progress.emit(50, "Generating image comparison...")
                viewer = ImageViewer(figsize=(14, 6), dpi=100)
                fig = viewer.compare_images(
                    original=self.kwargs['original'],
                    processed=self.kwargs['processed'],
                    original_title=self.kwargs.get('original_title', 'Original'),
                    processed_title=self.kwargs.get('processed_title', 'Processed'),
                    title=self.kwargs.get('title', 'Image Comparison'),
                    show_plot=False
                )
                
            else:
                raise ValueError(f"Unknown visualization type: {self.viz_type}")
            
            self.progress.emit(100, "Visualization complete!")
            self.finished.emit(fig)
            
        except Exception as e:
            self.error.emit(str(e))


class VisualizationTab(QWidget):
    """Data Visualization Tab - Comprehensive Visualization Interface"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = None
        self.current_plot = None
        self.current_figure = None
        self.visualization_worker = None
        
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
        
        # Visualization type selection
        viz_type_group = self._create_viz_type_group()
        left_layout.addWidget(viz_type_group)
        
        # Data source selection
        data_source_group = self._create_data_source_group()
        left_layout.addWidget(data_source_group)
        
        # Visualization parameters
        params_group = self._create_parameters_group()
        left_layout.addWidget(params_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.clicked.connect(self._reset_all)
        self.reset_btn.setMinimumHeight(38)
        self.reset_btn.setToolTip("Clear current visualization and reset all settings")
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
        
        self.generate_btn = QPushButton("Generate Visualization")
        self.generate_btn.clicked.connect(self._generate_visualization)
        self.generate_btn.setMinimumHeight(38)
        self.generate_btn.setToolTip("Generate the selected visualization type with current parameters")
        self.generate_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['primary']}; "
            f"color: {COLORS['button_text']}; "
            f"border: none;"
            f"border-radius: 8px;"
            f"font-weight: 600;"
            f"font-size: 11pt;"
            f"padding: 8px 16px;"
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
        action_layout.addWidget(self.generate_btn)
        
        left_layout.addLayout(action_layout)
        left_layout.addStretch()
        
        left_widget.setMinimumWidth(380)
        scroll_area.setWidget(left_widget)
        scroll_area.setMinimumWidth(400)
        scroll_area.setMaximumWidth(420)
        splitter.addWidget(scroll_area)
        
        # Right side: Visualization Display
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Plot canvas
        self.plot_fig = Figure(figsize=(12, 8), dpi=100)
        self.plot_canvas = FigureCanvas(self.plot_fig)
        self.plot_canvas.setFocusPolicy(Qt.ClickFocus)
        # Enable mouse wheel zoom
        self.plot_canvas.mpl_connect('scroll_event', self._on_plot_scroll)
        self.plot_toolbar = NavigationToolbar(self.plot_canvas, self)
        self.plot_original_limits = None
        
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(0)
        plot_layout.addWidget(self.plot_toolbar)
        plot_layout.addWidget(self.plot_canvas)
        
        right_layout.addWidget(plot_widget)
        
        # Export button
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        self.export_btn = QPushButton("Export Visualization")
        self.export_btn.clicked.connect(self._export_visualization)
        self.export_btn.setMinimumHeight(38)
        self.export_btn.setEnabled(False)
        self.export_btn.setToolTip("Save the current visualization as an image file (PNG, JPEG, PDF)")
        self.export_btn.setStyleSheet(
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
        export_layout.addWidget(self.export_btn)
        right_layout.addLayout(export_layout)
        
        # Status bar
        self.status_label = QLabel("Ready - Select visualization type and generate plot")
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
        
        # Initialize default visualization type parameters
        # This ensures combo boxes exist when data is loaded
        self._on_viz_type_changed(self.viz_type_combo.currentText())
        
        # Initialize empty plot
        self._init_empty_plot()
    
    def _create_viz_type_group(self) -> QGroupBox:
        """Create visualization type selection group"""
        group = QGroupBox("Visualization Type")
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
        
        viz_type_label = QLabel("Select Visualization:")
        viz_type_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        layout.addWidget(viz_type_label)
        
        self.viz_type_combo = QComboBox()
        self.viz_type_combo.addItems([
            "Time-Series Plot",
            "Scatter Plot",
            "Correlation Heatmap",
            "FFT Spectrum",
            "Image Comparison"
        ])
        self.viz_type_combo.setMinimumHeight(38)
        self.viz_type_combo.currentTextChanged.connect(self._on_viz_type_changed)
        self.viz_type_combo.setStyleSheet(f"""
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
        layout.addWidget(self.viz_type_combo)
        
        group.setLayout(layout)
        return group
    
    def _create_data_source_group(self) -> QGroupBox:
        """Create data source selection group"""
        group = QGroupBox("Data Source")
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
        
        source_label = QLabel("Data Source:")
        source_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        layout.addWidget(source_label)
        
        self.data_source_combo = QComboBox()
        self.data_source_combo.addItems([
            "Load from Database",
            "Load from CSV File",
            "Load Signal File",
            "Load Image Files"
        ])
        self.data_source_combo.setMinimumHeight(38)
        self.data_source_combo.currentTextChanged.connect(self._on_data_source_changed)
        self.data_source_combo.setStyleSheet(f"""
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
        layout.addWidget(self.data_source_combo)
        
        # Load button
        self.load_data_btn = QPushButton("Load Data")
        self.load_data_btn.clicked.connect(self._load_data)
        self.load_data_btn.setMinimumHeight(38)
        self.load_data_btn.setToolTip("Load data from the selected source")
        self.load_data_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['primary']}; "
            f"color: {COLORS['button_text']}; "
            f"border: none;"
            f"border-radius: 8px;"
            f"font-weight: 600;"
            f"font-size: 11pt;"
            f"padding: 8px 16px;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {COLORS['primary_dark']};"
            f"}}"
        )
        layout.addWidget(self.load_data_btn)
        
        # Data info
        self.data_info_label = QLabel("No data loaded")
        self.data_info_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['background']};
                color: {COLORS['text_secondary']};
                padding: 8px;
                border-radius: 6px;
                border: 1px solid {COLORS['border']};
                font-size: 10pt;
            }}
        """)
        self.data_info_label.setWordWrap(True)
        layout.addWidget(self.data_info_label)
        
        group.setLayout(layout)
        return group
    
    def _create_parameters_group(self) -> QGroupBox:
        """Create visualization parameters group"""
        group = QGroupBox("Visualization Parameters")
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
        
        # Parameters container (dynamic based on viz type)
        self.params_container = QWidget()
        self.params_layout = QVBoxLayout(self.params_container)
        self.params_layout.setSpacing(10)
        self.params_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.params_container)
        
        group.setLayout(layout)
        return group
    
    def _on_viz_type_changed(self, viz_type: str):
        """Update parameter controls based on selected visualization type"""
        # Clear existing parameters completely
        # First, remove all items from layout
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child is None:
                continue
                
            widget = child.widget()
            if widget is not None:
                widget.setParent(None)
                widget.hide()
                widget.deleteLater()
            else:
                child_layout = child.layout()
                if child_layout is not None:
                    self._clear_layout(child_layout)
        
        # Process events to ensure widgets are actually deleted
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Force update to ensure widgets are removed
        self.params_container.update()
        self.params_container.repaint()
        
        if viz_type == "Time-Series Plot":
            self._create_timeseries_params()
        elif viz_type == "Scatter Plot":
            self._create_scatter_params()
        elif viz_type == "Correlation Heatmap":
            self._create_heatmap_params()
        elif viz_type == "FFT Spectrum":
            self._create_fft_params()
        elif viz_type == "Image Comparison":
            self._create_image_comparison_params()
    
    def _clear_layout(self, layout):
        """Recursively clear a layout and all its widgets"""
        if layout is None:
            return
        
        while layout.count():
            child = layout.takeAt(0)
            if child is None:
                continue
                
            widget = child.widget()
            if widget is not None:
                widget.setParent(None)
                widget.hide()
                widget.deleteLater()
            else:
                child_layout = child.layout()
                if child_layout is not None:
                    self._clear_layout(child_layout)
    
    def _create_timeseries_params(self):
        """Create parameters for time-series plot"""
        # Metric selection
        metric_layout = QVBoxLayout()
        metric_label = QLabel("Metric to Plot:")
        metric_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        metric_layout.addWidget(metric_label)
        self.timeseries_metric_combo = QComboBox()
        self.timeseries_metric_combo.addItem("All Metrics")
        self.timeseries_metric_combo.setMinimumHeight(38)
        self.timeseries_metric_combo.setStyleSheet(f"""
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
        metric_layout.addWidget(self.timeseries_metric_combo)
        self.params_layout.addLayout(metric_layout)
    
    def _create_scatter_params(self):
        """Create parameters for scatter plot"""
        # X variable
        x_layout = QVBoxLayout()
        x_label = QLabel("X Variable:")
        x_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        x_layout.addWidget(x_label)
        self.scatter_x_combo = QComboBox()
        self.scatter_x_combo.setMinimumHeight(38)
        self.scatter_x_combo.setStyleSheet(f"""
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
        x_layout.addWidget(self.scatter_x_combo)
        self.params_layout.addLayout(x_layout)
        
        # Y variable
        y_layout = QVBoxLayout()
        y_label = QLabel("Y Variable:")
        y_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        y_layout.addWidget(y_label)
        self.scatter_y_combo = QComboBox()
        self.scatter_y_combo.setMinimumHeight(38)
        self.scatter_y_combo.setStyleSheet(f"""
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
        y_layout.addWidget(self.scatter_y_combo)
        self.params_layout.addLayout(y_layout)
        
        # Options
        options_layout = QVBoxLayout()
        self.scatter_trendline_check = CheckBoxWithTick("Show Trend Line")
        self.scatter_trendline_check.setChecked(True)
        options_layout.addWidget(self.scatter_trendline_check)
        
        self.scatter_correlation_check = CheckBoxWithTick("Show Correlation Coefficient")
        self.scatter_correlation_check.setChecked(True)
        options_layout.addWidget(self.scatter_correlation_check)
        self.params_layout.addLayout(options_layout)
    
    def _create_heatmap_params(self):
        """Create parameters for correlation heatmap"""
        # Color map
        cmap_layout = QVBoxLayout()
        cmap_label = QLabel("Color Map:")
        cmap_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        cmap_layout.addWidget(cmap_label)
        self.heatmap_cmap_combo = QComboBox()
        self.heatmap_cmap_combo.addItems(["coolwarm", "viridis", "plasma", "RdYlBu", "seismic"])
        self.heatmap_cmap_combo.setMinimumHeight(38)
        self.heatmap_cmap_combo.setStyleSheet(f"""
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
        cmap_layout.addWidget(self.heatmap_cmap_combo)
        self.params_layout.addLayout(cmap_layout)
        
        # Annotate checkbox
        self.heatmap_annotate_check = CheckBoxWithTick("Show Correlation Values")
        self.heatmap_annotate_check.setChecked(True)
        self.params_layout.addWidget(self.heatmap_annotate_check)
    
    def _create_fft_params(self):
        """Create parameters for FFT spectrum"""
        # Frequency range
        freq_min_layout = QVBoxLayout()
        freq_min_label = QLabel("Min Frequency (Hz):")
        freq_min_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        freq_min_layout.addWidget(freq_min_label)
        self.fft_freq_min_spin = QDoubleSpinBox()
        self.fft_freq_min_spin.setMinimum(0.0)
        self.fft_freq_min_spin.setMaximum(1000.0)
        self.fft_freq_min_spin.setValue(0.0)
        self.fft_freq_min_spin.setSingleStep(1.0)
        self.fft_freq_min_spin.setMinimumHeight(38)
        self.fft_freq_min_spin.setStyleSheet(f"""
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
        freq_min_layout.addWidget(self.fft_freq_min_spin)
        self.params_layout.addLayout(freq_min_layout)
        
        freq_max_layout = QVBoxLayout()
        freq_max_label = QLabel("Max Frequency (Hz):")
        freq_max_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        freq_max_layout.addWidget(freq_max_label)
        self.fft_freq_max_spin = QDoubleSpinBox()
        self.fft_freq_max_spin.setMinimum(0.0)
        self.fft_freq_max_spin.setMaximum(1000.0)
        self.fft_freq_max_spin.setValue(100.0)
        self.fft_freq_max_spin.setSingleStep(1.0)
        self.fft_freq_max_spin.setMinimumHeight(38)
        self.fft_freq_max_spin.setStyleSheet(f"""
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
        freq_max_layout.addWidget(self.fft_freq_max_spin)
        self.params_layout.addLayout(freq_max_layout)
    
    def _create_image_comparison_params(self):
        """Create parameters for image comparison"""
        # Instructions
        info_label = QLabel("Select two image files to compare side by side")
        info_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt; padding: 8px 0px; margin-bottom: 12px;")
        info_label.setWordWrap(True)
        self.params_layout.addWidget(info_label)
        
        # Add spacing
        self.params_layout.addSpacing(8)
        
        # Original Image Section
        original_layout = QVBoxLayout()
        original_layout.setSpacing(8)
        original_layout.setContentsMargins(0, 0, 0, 0)
        original_label = QLabel("Original Image:")
        original_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt; margin-top: 4px;")
        original_layout.addWidget(original_label)
        
        original_btn_layout = QHBoxLayout()
        self.image_original_btn = QPushButton("Select Original Image")
        self.image_original_btn.clicked.connect(self._select_original_image)
        self.image_original_btn.setMinimumHeight(38)
        self.image_original_btn.setToolTip("Select the original image file (X-ray, MRI, CT, etc.)")
        self.image_original_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['primary']}; "
            f"color: {COLORS['button_text']}; "
            f"border: none;"
            f"border-radius: 8px;"
            f"font-weight: 600;"
            f"font-size: 11pt;"
            f"padding: 8px 16px;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {COLORS['primary_dark']};"
            f"}}"
        )
        original_btn_layout.addWidget(self.image_original_btn)
        original_layout.addLayout(original_btn_layout)
        
        self.image_original_label = QLabel("No file selected")
        self.image_original_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['background']};
                color: {COLORS['text_secondary']};
                padding: 6px;
                border-radius: 6px;
                border: 1px solid {COLORS['border']};
                font-size: 10pt;
            }}
        """)
        self.image_original_label.setWordWrap(True)
        original_layout.addWidget(self.image_original_label)
        self.params_layout.addLayout(original_layout)
        
        # Add spacing between sections
        self.params_layout.addSpacing(12)
        
        # Processed Image Section
        processed_layout = QVBoxLayout()
        processed_layout.setSpacing(8)
        processed_layout.setContentsMargins(0, 0, 0, 0)
        processed_label = QLabel("Processed Image:")
        processed_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt; margin-top: 4px;")
        processed_layout.addWidget(processed_label)
        
        processed_btn_layout = QHBoxLayout()
        self.image_processed_btn = QPushButton("Select Processed Image")
        self.image_processed_btn.clicked.connect(self._select_processed_image)
        self.image_processed_btn.setMinimumHeight(38)
        self.image_processed_btn.setToolTip("Select the processed image file to compare with the original")
        self.image_processed_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['primary']}; "
            f"color: {COLORS['button_text']}; "
            f"border: none;"
            f"border-radius: 8px;"
            f"font-weight: 600;"
            f"font-size: 11pt;"
            f"padding: 8px 16px;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {COLORS['primary_dark']};"
            f"}}"
        )
        processed_btn_layout.addWidget(self.image_processed_btn)
        processed_layout.addLayout(processed_btn_layout)
        
        self.image_processed_label = QLabel("No file selected")
        self.image_processed_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['background']};
                color: {COLORS['text_secondary']};
                padding: 6px;
                border-radius: 6px;
                border: 1px solid {COLORS['border']};
                font-size: 10pt;
            }}
        """)
        self.image_processed_label.setWordWrap(True)
        processed_layout.addWidget(self.image_processed_label)
        self.params_layout.addLayout(processed_layout)
        
        # Store image paths
        self.image_original_path = None
        self.image_processed_path = None
    
    def _on_data_source_changed(self, source: str):
        """Update UI based on data source selection"""
        # Update button text and behavior
        if source == "Load from Database":
            self.load_data_btn.setText("Load from Database")
        elif source == "Load from CSV File":
            self.load_data_btn.setText("Browse CSV File")
        elif source == "Load Signal File":
            self.load_data_btn.setText("Browse Signal File")
        elif source == "Load Image Files":
            self.load_data_btn.setText("Browse Image Files")
    
    def _load_data(self):
        """Load data based on selected source"""
        source = self.data_source_combo.currentText()
        viz_type = self.viz_type_combo.currentText()
        
        # Check if data source is appropriate for visualization type
        if viz_type == "Image Comparison":
            if source not in ["Load Image Files"]:
                QMessageBox.warning(
                    self,
                    "Invalid Data Source",
                    "Image Comparison requires image files.\n\n"
                    "Please use 'Load Image Files' or use the 'Select Original Image' and 'Select Processed Image' buttons in the Visualization Parameters section."
                )
                return
        elif viz_type == "FFT Spectrum":
            if source not in ["Load Signal File"]:
                QMessageBox.warning(
                    self,
                    "Invalid Data Source",
                    "FFT Spectrum requires signal files.\n\n"
                    "Please select 'Load Signal File' as the data source."
                )
                return
        
        try:
            if source == "Load from Database":
                self._load_from_database()
            elif source == "Load from CSV File":
                self._load_from_csv()
            elif source == "Load Signal File":
                self._load_signal_file()
            elif source == "Load Image Files":
                self._load_image_files()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
    
    def _load_from_database(self):
        """Load health metrics from database"""
        # Check if current visualization type supports database data
        viz_type = self.viz_type_combo.currentText()
        if viz_type in ["Image Comparison", "FFT Spectrum"]:
            QMessageBox.warning(
                self,
                "Invalid Data Source",
                f"'{viz_type}' does not support database data.\n\n"
                f"For Image Comparison, please use image files.\n"
                f"For FFT Spectrum, please use signal files."
            )
            return
        
        self._update_status("Loading data from database...", "info")
        session = get_session()
        retriever = DataRetriever(session=session)
        
        try:
            metrics_df = retriever.get_health_metrics(limit=1000, as_dataframe=True)
            
            if metrics_df is None or len(metrics_df) == 0:
                QMessageBox.information(
                    self,
                    "No Data",
                    "No health metrics found in database.\n\nPlease import data first using the Data Management tab."
                )
                self._update_status("No data found", "warning")
                return
            
            self.current_data = metrics_df
            
            # Update metric combos (with safety check) - only for visualization types that need them
            if viz_type in ["Time-Series Plot", "Scatter Plot", "Correlation Heatmap"]:
                numeric_cols = metrics_df.select_dtypes(include=[np.number]).columns.tolist()
                if len(numeric_cols) > 0:
                    self._update_metric_combos(numeric_cols)
            
            # Update data info
            info_text = f"Data loaded from database:\n"
            info_text += f"Rows: {len(metrics_df)}\n"
            info_text += f"Columns: {len(metrics_df.columns)}\n"
            info_text += f"Metrics: {len(numeric_cols)}"
            self.data_info_label.setText(info_text)
            
            self._update_status(f"Data loaded successfully - {len(metrics_df)} rows, {len(numeric_cols)} metrics", "success")
            
        finally:
            session.close()
    
    def _load_from_csv(self):
        """Load data from CSV file"""
        # Check if current visualization type supports CSV data
        viz_type = self.viz_type_combo.currentText()
        if viz_type in ["Image Comparison", "FFT Spectrum"]:
            QMessageBox.warning(
                self,
                "Invalid Data Source",
                f"'{viz_type}' does not support CSV data.\n\n"
                f"For Image Comparison, please use image files.\n"
                f"For FFT Spectrum, please use signal files."
            )
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load CSV File",
            "",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            self._update_status("Loading CSV file...", "info")
            df = pd.read_csv(file_path)
            
            if df.empty:
                QMessageBox.warning(self, "Empty File", "The CSV file is empty.")
                return
            
            self.current_data = df
            
            # Update metric combos - only for visualization types that need them
            if viz_type in ["Time-Series Plot", "Scatter Plot", "Correlation Heatmap"]:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                self._update_metric_combos(numeric_cols)
            
            # Update data info
            info_text = f"Data loaded from CSV:\n"
            info_text += f"Rows: {len(df)}\n"
            info_text += f"Columns: {len(df.columns)}\n"
            info_text += f"File: {os.path.basename(file_path)}"
            self.data_info_label.setText(info_text)
            
            self._update_status("CSV file loaded successfully", "success")
            
        except Exception as e:
            raise Exception(f"Error loading CSV: {str(e)}")
    
    def _load_signal_file(self):
        """Load signal file for FFT visualization"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Signal File",
            "",
            "CSV Files (*.csv);;Text Files (*.txt);;Data Files (*.dat);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            self._update_status("Loading signal file...", "info")
            loader = SignalLoader()
            signal_data, sampling_rate, metadata = loader.load_signal_from_csv(file_path)
            
            self.current_data = {
                'signal': signal_data,
                'sampling_rate': sampling_rate,
                'metadata': metadata
            }
            
            # Update frequency range (if FFT controls exist)
            if hasattr(self, 'fft_freq_max_spin') and self.fft_freq_max_spin is not None:
                nyquist = sampling_rate / 2
                self.fft_freq_max_spin.setMaximum(nyquist)
                self.fft_freq_max_spin.setValue(min(100.0, nyquist))
            
            # Update data info
            info_text = f"Signal loaded:\n"
            info_text += f"Length: {len(signal_data)} samples\n"
            info_text += f"Duration: {metadata['duration']:.2f} s\n"
            info_text += f"Sampling Rate: {sampling_rate:.2f} Hz"
            self.data_info_label.setText(info_text)
            
            self._update_status("Signal file loaded successfully", "success")
            
        except Exception as e:
            raise Exception(f"Error loading signal: {str(e)}")
    
    def _select_original_image(self):
        """Select original image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Original Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.dcm);;All Files (*.*)"
        )
        
        if file_path:
            self.image_original_path = file_path
            filename = os.path.basename(file_path)
            self.image_original_label.setText(f"Selected: {filename}")
            self.image_original_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLORS['success']};
                    color: white;
                    padding: 6px;
                    border-radius: 6px;
                    border: 1px solid {COLORS['success']};
                    font-size: 10pt;
                    font-weight: 500;
                }}
            """)
            self._check_and_load_images()
    
    def _select_processed_image(self):
        """Select processed image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Processed Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.dcm);;All Files (*.*)"
        )
        
        if file_path:
            self.image_processed_path = file_path
            filename = os.path.basename(file_path)
            self.image_processed_label.setText(f"Selected: {filename}")
            self.image_processed_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLORS['success']};
                    color: white;
                    padding: 6px;
                    border-radius: 6px;
                    border: 1px solid {COLORS['success']};
                    font-size: 10pt;
                    font-weight: 500;
                }}
            """)
            self._check_and_load_images()
    
    def _check_and_load_images(self):
        """Check if both images are selected and load them"""
        if self.image_original_path and self.image_processed_path:
            try:
                self._update_status("Loading image files...", "info")
                loader = ImageLoader()
                
                original, _ = loader.load_image(self.image_original_path)
                processed, _ = loader.load_image(self.image_processed_path)
                
                self.current_data = {
                    'original': original,
                    'processed': processed,
                    'original_path': self.image_original_path,
                    'processed_path': self.image_processed_path
                }
                
                # Update data info
                info_text = f"Images ready for comparison:\n"
                info_text += f"Original: {os.path.basename(self.image_original_path)}\n"
                info_text += f"Processed: {os.path.basename(self.image_processed_path)}"
                self.data_info_label.setText(info_text)
                
                self._update_status("Both images loaded successfully - Ready to generate comparison", "success")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load images:\n{str(e)}")
                self._update_status(f"Error: {str(e)}", "error")
    
    def _load_image_files(self):
        """Load two image files for comparison (legacy method - now uses individual selectors)"""
        # This method is kept for backward compatibility but redirects to the new UI
        if hasattr(self, 'image_original_btn') and hasattr(self, 'image_processed_btn'):
            QMessageBox.information(
                self,
                "Image Selection",
                "Please use the 'Select Original Image' and 'Select Processed Image' buttons above to select your images."
            )
        else:
            # Fallback to old method if new UI not available
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                "Load Image Files (Select 2 images)",
                "",
                "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;All Files (*.*)"
            )
            
            if len(file_paths) < 2:
                QMessageBox.warning(self, "Insufficient Files", "Please select exactly 2 image files for comparison.")
                return
            
            if len(file_paths) > 2:
                QMessageBox.warning(self, "Too Many Files", "Please select exactly 2 image files. Using first 2 files.")
            
            try:
                self._update_status("Loading image files...", "info")
                loader = ImageLoader()
                
                original, _ = loader.load_image(file_paths[0])
                processed, _ = loader.load_image(file_paths[1])
                
                self.current_data = {
                    'original': original,
                    'processed': processed,
                    'original_path': file_paths[0],
                    'processed_path': file_paths[1]
                }
                
                # Update data info
                info_text = f"Images loaded:\n"
                info_text += f"Original: {os.path.basename(file_paths[0])}\n"
                info_text += f"Processed: {os.path.basename(file_paths[1])}"
                self.data_info_label.setText(info_text)
                
                self._update_status("Image files loaded successfully", "success")
                
            except Exception as e:
                raise Exception(f"Error loading images: {str(e)}")
    
    def _update_metric_combos(self, metrics: List[str]):
        """Update metric combo boxes with available metrics"""
        # Helper function to safely update combo box
        def safe_update_combo(combo_attr_name, default_item=None):
            if not hasattr(self, combo_attr_name):
                return False
            combo = getattr(self, combo_attr_name, None)
            if combo is None:
                return False
            try:
                # Check if widget still exists and is valid
                if not combo.isVisible() and combo.parent() is None:
                    return False
                combo.clear()
                if default_item:
                    combo.addItem(default_item)
                combo.addItems(metrics)
                return True
            except RuntimeError:
                # Widget has been deleted
                return False
            except Exception:
                # Any other error
                return False
        
        # Update time-series metric combo (if it exists and is valid)
        safe_update_combo('timeseries_metric_combo', "All Metrics")
        
        # Update scatter plot combos (if they exist and are valid)
        safe_update_combo('scatter_x_combo', "Select variable...")
        safe_update_combo('scatter_y_combo', "Select variable...")
    
    def _generate_visualization(self):
        """Generate visualization based on selected type"""
        viz_type = self.viz_type_combo.currentText()
        
        if self.visualization_worker is not None and self.visualization_worker.isRunning():
            QMessageBox.warning(self, "Processing", "Visualization is already being generated. Please wait.")
            return
        
        try:
            if viz_type == "Time-Series Plot":
                self._generate_timeseries()
            elif viz_type == "Scatter Plot":
                self._generate_scatter()
            elif viz_type == "Correlation Heatmap":
                self._generate_heatmap()
            elif viz_type == "FFT Spectrum":
                self._generate_fft()
            elif viz_type == "Image Comparison":
                self._generate_image_comparison()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate visualization:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
    
    def _generate_timeseries(self):
        """Generate time-series plot"""
        if self.current_data is None:
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return
        
        if not isinstance(self.current_data, pd.DataFrame):
            QMessageBox.warning(self, "Invalid Data", f"Expected DataFrame, got {type(self.current_data)}. Please load data first.")
            return
        
        if len(self.current_data) == 0:
            QMessageBox.warning(self, "Empty Data", "The loaded data is empty. Please load data with content.")
            return
        
        # Check if combo box exists and is valid
        metrics = None
        selected_metric = None
        if hasattr(self, 'timeseries_metric_combo') and self.timeseries_metric_combo is not None:
            try:
                selected_metric = self.timeseries_metric_combo.currentText()
                if selected_metric != "All Metrics":
                    metrics = [selected_metric]
            except RuntimeError:
                # Widget was deleted, use all metrics
                metrics = None
                selected_metric = None
        
        # Start worker thread
        title = f"Time-Series: {selected_metric}" if metrics and selected_metric else "Health Metrics Over Time"
        self.visualization_worker = VisualizationWorker(
            'time_series',
            data=self.current_data,
            metrics=metrics,
            title=title
        )
        self.visualization_worker.progress.connect(self._on_viz_progress)
        self.visualization_worker.finished.connect(self._on_viz_finished)
        self.visualization_worker.error.connect(self._on_viz_error)
        
        self.generate_btn.setEnabled(False)
        self._update_status("Generating time-series plot...", "info")
        self.visualization_worker.start()
    
    def _generate_scatter(self):
        """Generate scatter plot"""
        if self.current_data is None or not isinstance(self.current_data, pd.DataFrame):
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return
        
        # Check if combo boxes exist and are valid
        if not hasattr(self, 'scatter_x_combo') or self.scatter_x_combo is None or \
           not hasattr(self, 'scatter_y_combo') or self.scatter_y_combo is None:
            QMessageBox.warning(self, "Error", "Scatter plot controls are not available. Please select Scatter Plot visualization type.")
            return
        
        try:
            x_var = self.scatter_x_combo.currentText()
            y_var = self.scatter_y_combo.currentText()
        except RuntimeError:
            QMessageBox.warning(self, "Error", "Controls are not available. Please try again.")
            return
        
        if x_var == "Select variable..." or y_var == "Select variable...":
            QMessageBox.warning(self, "Invalid Selection", "Please select both X and Y variables.")
            return
        
        if x_var == y_var:
            QMessageBox.warning(self, "Invalid Selection", "Please select two different variables.")
            return
        
        x_data = self.current_data[x_var].dropna().values
        y_data = self.current_data[y_var].dropna().values
        
        # Align data lengths
        min_len = min(len(x_data), len(y_data))
        x_data = x_data[:min_len]
        y_data = y_data[:min_len]
        
        # Start worker thread
        self.visualization_worker = VisualizationWorker(
            'scatter',
            x_data=x_data,
            y_data=y_data,
            x_label=x_var,
            y_label=y_var,
            title=f"Scatter Plot: {x_var} vs {y_var}",
            show_trendline=self.scatter_trendline_check.isChecked(),
            show_correlation=self.scatter_correlation_check.isChecked()
        )
        self.visualization_worker.progress.connect(self._on_viz_progress)
        self.visualization_worker.finished.connect(self._on_viz_finished)
        self.visualization_worker.error.connect(self._on_viz_error)
        
        self.generate_btn.setEnabled(False)
        self._update_status("Generating scatter plot...", "info")
        self.visualization_worker.start()
    
    def _generate_heatmap(self):
        """Generate correlation heatmap"""
        if self.current_data is None or not isinstance(self.current_data, pd.DataFrame):
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return
        
        # Start worker thread
        self.visualization_worker = VisualizationWorker(
            'heatmap',
            data=self.current_data,
            title="Correlation Matrix",
            cmap=self.heatmap_cmap_combo.currentText(),
            annotate=self.heatmap_annotate_check.isChecked()
        )
        self.visualization_worker.progress.connect(self._on_viz_progress)
        self.visualization_worker.finished.connect(self._on_viz_finished)
        self.visualization_worker.error.connect(self._on_viz_error)
        
        self.generate_btn.setEnabled(False)
        self._update_status("Generating correlation heatmap...", "info")
        self.visualization_worker.start()
    
    def _generate_fft(self):
        """Generate FFT spectrum plot"""
        if self.current_data is None or not isinstance(self.current_data, dict):
            QMessageBox.warning(self, "No Signal", "Please load a signal file first.")
            return
        
        if 'signal' not in self.current_data:
            QMessageBox.warning(self, "Invalid Data", "Signal data not found.")
            return
        
        signal_data = self.current_data['signal']
        sampling_rate = self.current_data['sampling_rate']
        
        # Check if FFT controls exist
        if not hasattr(self, 'fft_freq_min_spin') or self.fft_freq_min_spin is None:
            QMessageBox.warning(self, "Error", "FFT controls not initialized. Please select FFT Spectrum visualization type first.")
            return
        
        freq_min = self.fft_freq_min_spin.value()
        freq_max = self.fft_freq_max_spin.value()
        
        # Start worker thread
        self.visualization_worker = VisualizationWorker(
            'fft_spectrum',
            signal_data=signal_data,
            sample_rate=sampling_rate,
            title="FFT Spectrum",
            xlim=(freq_min, freq_max) if freq_max > freq_min else None
        )
        self.visualization_worker.progress.connect(self._on_viz_progress)
        self.visualization_worker.finished.connect(self._on_viz_finished)
        self.visualization_worker.error.connect(self._on_viz_error)
        
        self.generate_btn.setEnabled(False)
        self._update_status("Generating FFT spectrum...", "info")
        self.visualization_worker.start()
    
    def _generate_image_comparison(self):
        """Generate image comparison"""
        if self.current_data is None or not isinstance(self.current_data, dict):
            QMessageBox.warning(self, "No Images", "Please load two image files first.")
            return
        
        if 'original' not in self.current_data or 'processed' not in self.current_data:
            QMessageBox.warning(self, "Invalid Data", "Image data not found.")
            return
        
        original = self.current_data['original']
        processed = self.current_data['processed']
        original_title = os.path.basename(self.current_data.get('original_path', 'Original'))
        processed_title = os.path.basename(self.current_data.get('processed_path', 'Processed'))
        
        # Start worker thread
        self.visualization_worker = VisualizationWorker(
            'image_comparison',
            original=original,
            processed=processed,
            original_title=original_title,
            processed_title=processed_title,
            title="Image Comparison"
        )
        self.visualization_worker.progress.connect(self._on_viz_progress)
        self.visualization_worker.finished.connect(self._on_viz_finished)
        self.visualization_worker.error.connect(self._on_viz_error)
        
        self.generate_btn.setEnabled(False)
        self._update_status("Generating image comparison...", "info")
        self.visualization_worker.start()
    
    def _on_viz_progress(self, value: int, message: str):
        """Handle visualization progress updates"""
        self._update_status(f"{message} ({value}%)", "info")
    
    def _on_viz_finished(self, figure):
        """Handle visualization completion"""
        self.generate_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.current_figure = figure
        
        # Display the figure in our canvas by replacing the figure
        # Clear current figure
        self.plot_fig.clear()
        
        # Get layout info from original figure
        num_axes = len(figure.axes)
        
        if num_axes == 0:
            self._update_status("Warning: No axes found in figure", "warning")
            return
        
        # Create subplots matching the original layout
        if num_axes == 1:
            new_ax = self.plot_fig.add_subplot(111)
            axes_list = [new_ax]
        elif num_axes == 2:
            new_ax1 = self.plot_fig.add_subplot(121)
            new_ax2 = self.plot_fig.add_subplot(122)
            axes_list = [new_ax1, new_ax2]
        else:
            # For more complex layouts, use a grid
            ncols = 2 if num_axes <= 4 else 3
            nrows = (num_axes + ncols - 1) // ncols
            axes_list = []
            for i in range(num_axes):
                axes_list.append(self.plot_fig.add_subplot(nrows, ncols, i + 1))
        
        # Recreate each axis content (can't copy artists between figures)
        for orig_ax, new_ax in zip(figure.axes, axes_list):
            # Recreate lines
            for line in orig_ax.lines:
                xdata = line.get_xdata()
                ydata = line.get_ydata()
                new_ax.plot(xdata, ydata,
                           color=line.get_color(),
                           linestyle=line.get_linestyle(),
                           linewidth=line.get_linewidth(),
                           label=line.get_label(),
                           alpha=line.get_alpha(),
                           marker=line.get_marker() if hasattr(line, 'get_marker') and line.get_marker() != 'None' else None,
                           markersize=line.get_markersize() if hasattr(line, 'get_markersize') else None)
            
            # Recreate collections (scatter plots, etc.) by extracting data
            for collection in orig_ax.collections:
                try:
                    # For PathCollection (scatter plots)
                    if hasattr(collection, 'get_offsets'):
                        offsets = collection.get_offsets()
                        if len(offsets) > 0:
                            sizes = collection.get_sizes() if hasattr(collection, 'get_sizes') else None
                            colors = collection.get_facecolors() if hasattr(collection, 'get_facecolors') else None
                            new_ax.scatter(offsets[:, 0], offsets[:, 1], 
                                         s=sizes, c=colors, 
                                         alpha=collection.get_alpha() if hasattr(collection, 'get_alpha') else 1.0,
                                         edgecolors=collection.get_edgecolors() if hasattr(collection, 'get_edgecolors') else None)
                    # For other collection types, try to extract paths
                    elif hasattr(collection, 'get_paths'):
                        paths = collection.get_paths()
                        for path in paths:
                            vertices = path.vertices
                            if len(vertices) > 0:
                                new_ax.plot(vertices[:, 0], vertices[:, 1],
                                          color=collection.get_edgecolor() if hasattr(collection, 'get_edgecolor') else 'black',
                                          alpha=collection.get_alpha() if hasattr(collection, 'get_alpha') else 1.0)
                except Exception as e:
                    # If we can't recreate the collection, skip it
                    logger.warning(f"Could not recreate collection: {e}")
                    pass
            
            # Recreate images (heatmaps, image displays)
            for image in orig_ax.images:
                try:
                    im_data = image.get_array()
                    if im_data is not None:
                        cmap = image.get_cmap() if hasattr(image, 'get_cmap') else 'viridis'
                        extent = image.get_extent() if hasattr(image, 'get_extent') else None
                        aspect = image.get_aspect() if hasattr(image, 'get_aspect') else 'auto'
                        interpolation = image.get_interpolation() if hasattr(image, 'get_interpolation') else 'nearest'
                        vmin = image.get_clim()[0] if hasattr(image, 'get_clim') else None
                        vmax = image.get_clim()[1] if hasattr(image, 'get_clim') else None
                        
                        if extent:
                            new_ax.imshow(im_data, cmap=cmap, extent=extent,
                                        aspect=aspect, interpolation=interpolation,
                                        vmin=vmin, vmax=vmax)
                        else:
                            new_ax.imshow(im_data, cmap=cmap, aspect=aspect,
                                        interpolation=interpolation, vmin=vmin, vmax=vmax)
                except Exception as e:
                    logger.warning(f"Could not recreate image: {e}")
                    pass
            
            # Recreate patches (rectangles, circles, etc.) by copying properties
            for patch in orig_ax.patches:
                try:
                    from matplotlib.patches import Rectangle, Circle, Ellipse, Polygon, FancyBboxPatch
                    patch_type = type(patch).__name__
                    
                    if isinstance(patch, Rectangle):
                        new_patch = Rectangle((patch.get_x(), patch.get_y()),
                                            patch.get_width(), patch.get_height(),
                                            angle=patch.get_angle(),
                                            facecolor=patch.get_facecolor(),
                                            edgecolor=patch.get_edgecolor(),
                                            linewidth=patch.get_linewidth(),
                                            alpha=patch.get_alpha())
                        new_ax.add_patch(new_patch)
                    elif isinstance(patch, (Circle, Ellipse)):
                        center = patch.get_center()
                        if isinstance(patch, Circle):
                            new_patch = Circle(center, patch.get_radius(),
                                             facecolor=patch.get_facecolor(),
                                             edgecolor=patch.get_edgecolor(),
                                             linewidth=patch.get_linewidth(),
                                             alpha=patch.get_alpha())
                        else:
                            new_patch = Ellipse(center, patch.get_width(), patch.get_height(),
                                              angle=patch.get_angle(),
                                              facecolor=patch.get_facecolor(),
                                              edgecolor=patch.get_edgecolor(),
                                              linewidth=patch.get_linewidth(),
                                              alpha=patch.get_alpha())
                        new_ax.add_patch(new_patch)
                    elif isinstance(patch, Polygon):
                        vertices = patch.get_xy()
                        new_patch = Polygon(vertices,
                                          facecolor=patch.get_facecolor(),
                                          edgecolor=patch.get_edgecolor(),
                                          linewidth=patch.get_linewidth(),
                                          alpha=patch.get_alpha())
                        new_ax.add_patch(new_patch)
                except Exception as e:
                    logger.warning(f"Could not recreate patch: {e}")
                    pass
            
            # Recreate text elements
            for text in orig_ax.texts:
                try:
                    pos = text.get_position()
                    new_ax.text(pos[0], pos[1], text.get_text(),
                              fontsize=text.get_fontsize(),
                              color=text.get_color(),
                              ha=text.get_ha(),
                              va=text.get_va(),
                              transform=text.get_transform())
                except Exception as e:
                    logger.warning(f"Could not recreate text: {e}")
                    pass
            
            # Copy axis properties
            new_ax.set_xlabel(orig_ax.get_xlabel(), fontsize=orig_ax.xaxis.label.get_fontsize() if orig_ax.xaxis.label.get_fontsize() else 12)
            new_ax.set_ylabel(orig_ax.get_ylabel(), fontsize=orig_ax.yaxis.label.get_fontsize() if orig_ax.yaxis.label.get_fontsize() else 12)
            new_ax.set_title(orig_ax.get_title(), fontsize=orig_ax.title.get_fontsize() if orig_ax.title.get_fontsize() else 14)
            new_ax.set_xlim(orig_ax.get_xlim())
            new_ax.set_ylim(orig_ax.get_ylim())
            # Check if grid is enabled - use private attribute as it's the most reliable
            try:
                grid_enabled = getattr(orig_ax.xaxis, '_gridOnMajor', False) or \
                              getattr(orig_ax.yaxis, '_gridOnMajor', False)
            except AttributeError:
                # Fallback: check if gridlines exist
                try:
                    grid_enabled = len(orig_ax.get_xgridlines()) > 0 or len(orig_ax.get_ygridlines()) > 0
                except (AttributeError, TypeError):
                    grid_enabled = False  # Default to no grid if we can't determine
            new_ax.grid(grid_enabled)
            
            # Recreate legend if exists
            if orig_ax.get_legend():
                try:
                    handles, labels = orig_ax.get_legend_handles_labels()
                    if handles and labels:
                        new_ax.legend(handles, labels, loc=orig_ax.get_legend().get_loc())
                except Exception as e:
                    logger.warning(f"Could not recreate legend: {e}")
                    pass
        
        # Copy figure title if exists
        if hasattr(figure, '_suptitle') and figure._suptitle:
            self.plot_fig.suptitle(figure._suptitle.get_text(),
                                 fontsize=figure._suptitle.get_fontsize(),
                                 fontweight=figure._suptitle.get_fontweight())
        
        self.plot_fig.tight_layout()
        self.plot_canvas.draw()
        if hasattr(self, 'plot_toolbar'):
            self.plot_toolbar.update()
        
        # Store original limits for reset
        if self.plot_fig.axes:
            self.plot_original_limits = {}
            for i, ax in enumerate(self.plot_fig.axes):
                self.plot_original_limits[i] = (ax.get_xlim(), ax.get_ylim())
        
        self._update_status("Visualization generated successfully!", "success")
    
    def _on_viz_error(self, error_msg: str):
        """Handle visualization errors"""
        self.generate_btn.setEnabled(True)
        QMessageBox.critical(self, "Visualization Error", f"Failed to generate visualization:\n{error_msg}")
        self._update_status(f"Error: {error_msg}", "error")
    
    def _on_plot_scroll(self, event):
        """Handle mouse wheel zoom for plot display"""
        if not self.plot_fig.axes:
            return
        
        # Determine which subplot
        ax = None
        for a in self.plot_fig.axes:
            if event.inaxes == a:
                ax = a
                break
        
        if ax is None:
            return
        
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        
        if self.plot_original_limits is None:
            self.plot_original_limits = {}
            for i, a in enumerate(self.plot_fig.axes):
                self.plot_original_limits[i] = (a.get_xlim(), a.get_ylim())
        
        xdata = event.xdata
        ydata = event.ydata
        
        if xdata is None or ydata is None:
            return
        
        zoom_factor = 1.1 if event.button == 'up' else 0.9
        
        x_left = xdata - cur_xlim[0]
        x_right = cur_xlim[1] - xdata
        y_bottom = ydata - cur_ylim[0]
        y_top = cur_ylim[1] - ydata
        
        ax.set_xlim([xdata - x_left * zoom_factor, xdata + x_right * zoom_factor])
        ax.set_ylim([ydata - y_bottom * zoom_factor, ydata + y_top * zoom_factor])
        
        self.plot_canvas.draw()
    
    def _export_visualization(self):
        """Export current visualization to file"""
        if self.current_figure is None:
            QMessageBox.warning(self, "No Visualization", "No visualization to export. Please generate one first.")
            return
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Visualization",
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            self._update_status("Exporting visualization...", "info")
            
            # Determine format from extension
            ext = os.path.splitext(file_path)[1].lower()
            if not ext:
                # Use filter to determine format
                if 'PNG' in selected_filter:
                    ext = '.png'
                elif 'JPEG' in selected_filter:
                    ext = '.jpg'
                elif 'PDF' in selected_filter:
                    ext = '.pdf'
                elif 'SVG' in selected_filter:
                    ext = '.svg'
                else:
                    ext = '.png'
                file_path += ext
            
            # Save using current figure
            self.plot_fig.savefig(file_path, dpi=300, bbox_inches='tight', 
                                 facecolor='white', edgecolor='none')
            
            QMessageBox.information(self, "Success", f"Visualization exported to:\n{file_path}")
            self._update_status("Visualization exported successfully", "success")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export visualization:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
    
    def _init_empty_plot(self):
        """Initialize empty plot display"""
        self.plot_fig.clear()
        ax = self.plot_fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Select visualization type and generate plot', 
                ha='center', va='center', transform=ax.transAxes,
                fontsize=14, color=COLORS['text_secondary'])
        ax.axis('off')
        self.plot_fig.tight_layout()
        self.plot_canvas.draw()
    
    def _reset_all(self):
        """Reset all controls and visualizations"""
        self.current_data = None
        self.current_figure = None
        self.plot_original_limits = None
        
        # Reset image paths and labels
        if hasattr(self, 'image_original_path'):
            self.image_original_path = None
        if hasattr(self, 'image_processed_path'):
            self.image_processed_path = None
        if hasattr(self, 'image_original_label'):
            self.image_original_label.setText("No file selected")
            self.image_original_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLORS['background']};
                    color: {COLORS['text_secondary']};
                    padding: 6px;
                    border-radius: 6px;
                    border: 1px solid {COLORS['border']};
                    font-size: 10pt;
                }}
            """)
        if hasattr(self, 'image_processed_label'):
            self.image_processed_label.setText("No file selected")
            self.image_processed_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLORS['background']};
                    color: {COLORS['text_secondary']};
                    padding: 6px;
                    border-radius: 6px;
                    border: 1px solid {COLORS['border']};
                    font-size: 10pt;
                }}
            """)
        
        self.data_info_label.setText("No data loaded")
        self.generate_btn.setEnabled(True)
        self.export_btn.setEnabled(False)
        
        # Reset visualization type
        self.viz_type_combo.setCurrentIndex(0)
        self._on_viz_type_changed(self.viz_type_combo.currentText())
        
        # Reset data source
        self.data_source_combo.setCurrentIndex(0)
        
        # Reset display
        self._init_empty_plot()
        
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
