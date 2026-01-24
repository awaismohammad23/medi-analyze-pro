"""
Health Data Analysis Tab for MediAnalyze Pro GUI
Provides filtering, correlation analysis, and time-series visualization
"""

import sys
import os
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSlider, QSpinBox, QDoubleSpinBox, QGroupBox,
    QTextEdit, QSplitter, QScrollArea, QMessageBox, QCheckBox,
    QFormLayout, QTabWidget, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
import pandas as pd
import numpy as np
import matplotlib
# Use Qt5Agg backend for interactive plots in GUI
try:
    matplotlib.use('Qt5Agg')
except:
    matplotlib.use('Agg')  # Fallback to non-interactive
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.database import get_db_connection, get_session
from src.data_processing import DataRetriever, DataFilter, CorrelationAnalyzer, TimeSeriesAnalyzer
from src.visualization import TimeSeriesPlotter, ScatterPlotter, HeatmapPlotter
from ..styles import COLORS


class AnalysisWorker(QThread):
    """Worker thread for analysis operations to prevent UI freezing"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, operation: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs
    
    def run(self):
        """Run analysis in background thread"""
        try:
            if self.operation == 'correlation':
                self.progress.emit(50, "Computing correlation...")
                analyzer = CorrelationAnalyzer()
                method = self.kwargs.get('method', 'pearson')
                x = self.kwargs['x']
                y = self.kwargs['y']
                
                try:
                    if method == 'pearson':
                        corr, p_value, n = analyzer.compute_pearson_correlation(x, y)
                    else:
                        corr, p_value, n = analyzer.compute_spearman_correlation(x, y)
                    
                    self.progress.emit(100, "Correlation computed!")
                    self.finished.emit({
                        'correlation': corr,
                        'p_value': p_value,
                        'n': n,
                        'method': method
                    })
                except np.linalg.LinAlgError as e:
                    # SVD convergence issue - try alternative computation
                    import warnings
                    warnings.filterwarnings('ignore')
                    if method == 'pearson':
                        corr, p_value, n = analyzer.compute_pearson_correlation(x, y)
                    else:
                        corr, p_value, n = analyzer.compute_spearman_correlation(x, y)
                    
                    self.progress.emit(100, "Correlation computed!")
                    self.finished.emit({
                        'correlation': corr,
                        'p_value': p_value,
                        'n': n,
                        'method': method
                    })
            elif self.operation == 'filter':
                self.progress.emit(50, "Applying filter...")
                filter_type = self.kwargs['filter_type']
                data = self.kwargs['data']
                
                if filter_type == 'moving_average':
                    window = self.kwargs.get('window_size', 5)
                    filtered = DataFilter.moving_average(data, window_size=window)
                elif filter_type == 'threshold':
                    min_val = self.kwargs.get('min_value')
                    max_val = self.kwargs.get('max_value')
                    filtered, mask = DataFilter.threshold_filter(data, min_val, max_val)
                elif filter_type == 'outlier':
                    method = self.kwargs.get('outlier_method', 'iqr')
                    threshold = self.kwargs.get('threshold', 1.5)
                    filtered, mask = DataFilter.remove_outliers(data, method=method, threshold=threshold)
                else:
                    filtered = data
                
                self.progress.emit(100, "Filter applied!")
                self.finished.emit({'filtered_data': filtered})
                
        except Exception as e:
            self.error.emit(str(e))


class HealthAnalysisTab(QWidget):
    """Health Data Analysis Tab - Filtering, Correlation, and Time-Series"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = None
        self.filtered_data = None
        self.db_connection = get_db_connection()
        self.analysis_worker = None
        self._setup_ui()
        self._load_available_metrics()
    
    def _setup_ui(self):
        """Setup the tab UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Create splitter for side-by-side layout
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side: Controls (with scroll area to prevent overlapping)
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
        
        # Data selection section
        data_group = self._create_data_selection_group()
        left_layout.addWidget(data_group)
        
        # Filtering section
        filter_group = self._create_filtering_group()
        left_layout.addWidget(filter_group)
        
        # Correlation section
        correlation_group = self._create_correlation_group()
        left_layout.addWidget(correlation_group)
        
        # Time-series section
        timeseries_group = self._create_timeseries_group()
        left_layout.addWidget(timeseries_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.clicked.connect(self._reset_all)
        self.reset_btn.setMinimumHeight(38)
        self.reset_btn.setToolTip("Clear all filters, correlations, and visualizations and reset to default state")
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
        
        self.apply_btn = QPushButton("Apply Analysis")
        self.apply_btn.clicked.connect(self._apply_analysis)
        self.apply_btn.setMinimumHeight(38)
        self.apply_btn.setToolTip("Apply the selected filter to the data and update statistics")
        self.apply_btn.setStyleSheet(
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
        action_layout.addWidget(self.apply_btn)
        
        left_layout.addLayout(action_layout)
        left_layout.addStretch()
        
        # Set fixed width for left panel (wider for better readability)
        left_widget.setMinimumWidth(380)
        scroll_area.setWidget(left_widget)
        scroll_area.setMinimumWidth(400)
        scroll_area.setMaximumWidth(420)
        splitter.addWidget(scroll_area)
        
        # Right side: Results and Visualizations
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(12)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Results tabs
        self.results_tabs = QTabWidget()
        
        # Statistics tab
        stats_tab = self._create_statistics_tab()
        self.results_tabs.addTab(stats_tab, "Statistics")
        
        # Visualization tab
        viz_tab = self._create_visualization_tab()
        self.results_tabs.addTab(viz_tab, "Visualizations")
        
        right_layout.addWidget(self.results_tabs)
        splitter.addWidget(right_widget)
        
        # Set splitter proportions (wider left panel for readability)
        splitter.setSizes([420, 980])
        
        # Status area
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready - Load data to begin analysis")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 5px;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)
    
    def _create_data_selection_group(self) -> QGroupBox:
        """Create data selection group"""
        group = QGroupBox("Data Selection")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Load data button
        self.load_data_btn = QPushButton("Load Health Metrics from Database")
        self.load_data_btn.clicked.connect(self._load_health_metrics)
        self.load_data_btn.setMinimumHeight(40)
        self.load_data_btn.setToolTip("Load health metrics data from the database for analysis")
        self.load_data_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['primary']}; "
            f"color: {COLORS['button_text']}; "
            f"border: none;"
            f"border-radius: 8px;"
            f"font-weight: 600;"
            f"font-size: 11pt;"
            f"padding: 10px 16px;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {COLORS['primary_dark']};"
            f"}}"
        )
        layout.addWidget(self.load_data_btn)
        
        # Patient selection with proper spacing
        patient_layout = QVBoxLayout()
        patient_label = QLabel("Patient:")
        patient_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        patient_layout.addWidget(patient_label)
        self.patient_combo = QComboBox()
        self.patient_combo.addItem("All Patients")
        self.patient_combo.currentTextChanged.connect(self._on_patient_changed)
        self.patient_combo.setMinimumHeight(38)
        self.patient_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                padding: 8px 14px;
                border-radius: 8px;
                font-size: 11pt;
                min-height: 22px;
            }}
            QComboBox:hover {{
                border: 2px solid {COLORS['primary_light']};
                background-color: {COLORS['background']};
            }}
            QComboBox:focus {{
                border: 2px solid {COLORS['primary']};
                background-color: {COLORS['surface']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: {COLORS['primary']};
            }}
            QComboBox::drop-down:hover {{
                background-color: {COLORS['button_primary_hover']};
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid white;
                width: 0;
                height: 0;
                margin-right: 8px;
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
        patient_layout.addWidget(self.patient_combo)
        layout.addLayout(patient_layout)
        
        # Metric selection with proper spacing
        metric_layout = QVBoxLayout()
        metric_label = QLabel("Metric:")
        metric_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        metric_layout.addWidget(metric_label)
        self.metric_combo = QComboBox()
        self.metric_combo.addItem("Select metric...")
        self.metric_combo.currentTextChanged.connect(self._on_metric_changed)
        self.metric_combo.setMinimumHeight(38)
        self.metric_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                padding: 8px 14px;
                border-radius: 8px;
                font-size: 11pt;
                min-height: 22px;
            }}
            QComboBox:hover {{
                border: 2px solid {COLORS['primary_light']};
                background-color: {COLORS['background']};
            }}
            QComboBox:focus {{
                border: 2px solid {COLORS['primary']};
                background-color: {COLORS['surface']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: {COLORS['primary']};
            }}
            QComboBox::drop-down:hover {{
                background-color: {COLORS['button_primary_hover']};
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid white;
                width: 0;
                height: 0;
                margin-right: 8px;
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
        metric_layout.addWidget(self.metric_combo)
        layout.addLayout(metric_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_filtering_group(self) -> QGroupBox:
        """Create filtering controls group"""
        group = QGroupBox("Data Filtering")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 15, 12, 12)
        
        # Filter type with proper spacing
        filter_type_layout = QVBoxLayout()
        filter_type_label = QLabel("Filter Type:")
        filter_type_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        filter_type_layout.addWidget(filter_type_label)
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems([
            "None",
            "Moving Average",
            "Threshold",
            "Remove Outliers"
        ])
        self.filter_type_combo.currentTextChanged.connect(self._on_filter_type_changed)
        self.filter_type_combo.setMinimumHeight(38)
        self.filter_type_combo.setStyleSheet(f"""
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
            QComboBox::drop-down {{
                border: none;
                width: 30px;
                background-color: {COLORS['primary']};
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
        filter_type_layout.addWidget(self.filter_type_combo)
        layout.addLayout(filter_type_layout)
        
        # Filter parameters (dynamic based on filter type)
        self.filter_params_widget = QWidget()
        self.filter_params_layout = QVBoxLayout(self.filter_params_widget)
        self.filter_params_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_params_layout.setSpacing(10)
        layout.addWidget(self.filter_params_widget)
        
        # Apply filter button
        self.apply_filter_btn = QPushButton("Apply Filter")
        self.apply_filter_btn.clicked.connect(self._apply_filter)
        self.apply_filter_btn.setEnabled(False)
        self.apply_filter_btn.setMinimumHeight(38)
        self.apply_filter_btn.setToolTip("Apply the selected filter type to the chosen metric")
        self.apply_filter_btn.setStyleSheet(
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
        layout.addWidget(self.apply_filter_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_correlation_group(self) -> QGroupBox:
        """Create correlation analysis group"""
        group = QGroupBox("Correlation Analysis")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 15, 12, 12)
        
        # Metric 1 with proper spacing
        metric1_layout = QVBoxLayout()
        metric1_label = QLabel("Metric 1:")
        metric1_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        metric1_layout.addWidget(metric1_label)
        self.corr_metric1_combo = QComboBox()
        self.corr_metric1_combo.addItem("Select metric...")
        self.corr_metric1_combo.setMinimumHeight(38)
        self.corr_metric1_combo.setStyleSheet(f"""
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
        metric1_layout.addWidget(self.corr_metric1_combo)
        layout.addLayout(metric1_layout)
        
        # Metric 2 with proper spacing
        metric2_layout = QVBoxLayout()
        metric2_label = QLabel("Metric 2:")
        metric2_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        metric2_layout.addWidget(metric2_label)
        self.corr_metric2_combo = QComboBox()
        self.corr_metric2_combo.addItem("Select metric...")
        self.corr_metric2_combo.setMinimumHeight(38)
        self.corr_metric2_combo.setStyleSheet(f"""
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
        metric2_layout.addWidget(self.corr_metric2_combo)
        layout.addLayout(metric2_layout)
        
        # Correlation method with proper spacing
        method_layout = QVBoxLayout()
        method_label = QLabel("Method:")
        method_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        method_layout.addWidget(method_label)
        self.corr_method_combo = QComboBox()
        self.corr_method_combo.addItems(["Pearson", "Spearman"])
        self.corr_method_combo.setMinimumHeight(38)
        self.corr_method_combo.setStyleSheet(f"""
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
        method_layout.addWidget(self.corr_method_combo)
        layout.addLayout(method_layout)
        
        # Compute button
        self.compute_corr_btn = QPushButton("Compute Correlation")
        self.compute_corr_btn.clicked.connect(self._compute_correlation)
        self.compute_corr_btn.setEnabled(False)
        self.compute_corr_btn.setMinimumHeight(38)
        self.compute_corr_btn.setToolTip("Calculate correlation between the two selected metrics using the chosen method (Pearson or Spearman)")
        self.compute_corr_btn.setStyleSheet(
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
        layout.addWidget(self.compute_corr_btn)
        
        # Results display
        self.corr_results_text = QTextEdit()
        self.corr_results_text.setReadOnly(True)
        self.corr_results_text.setMinimumHeight(100)
        self.corr_results_text.setMaximumHeight(150)
        self.corr_results_text.setPlaceholderText("Correlation results will appear here...")
        self.corr_results_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 10pt;
                font-family: 'Consolas', monospace;
            }}
        """)
        layout.addWidget(self.corr_results_text)
        
        group.setLayout(layout)
        return group
    
    def _create_timeseries_group(self) -> QGroupBox:
        """Create time-series analysis group"""
        group = QGroupBox("Time-Series Analysis")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 15, 12, 12)
        
        # Visualization type with proper spacing
        viz_type_layout = QVBoxLayout()
        viz_type_label = QLabel("Visualization:")
        viz_type_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        viz_type_layout.addWidget(viz_type_label)
        self.timeseries_viz_combo = QComboBox()
        self.timeseries_viz_combo.addItems([
            "Time Series Plot",
            "Trend Analysis",
            "Anomaly Detection"
        ])
        self.timeseries_viz_combo.setMinimumHeight(38)
        self.timeseries_viz_combo.setStyleSheet(f"""
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
        viz_type_layout.addWidget(self.timeseries_viz_combo)
        layout.addLayout(viz_type_layout)
        
        # Generate button
        self.generate_viz_btn = QPushButton("Generate Time-Series Visualization")
        self.generate_viz_btn.clicked.connect(self._generate_visualization)
        self.generate_viz_btn.setEnabled(False)
        self.generate_viz_btn.setMinimumHeight(38)
        self.generate_viz_btn.setToolTip("Generate the selected time-series visualization type (Time Series Plot, Trend Analysis, Anomaly Detection, etc.)")
        self.generate_viz_btn.setStyleSheet(
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
        layout.addWidget(self.generate_viz_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_statistics_tab(self) -> QWidget:
        """Create statistics display tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Statistic", "Value"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.stats_table)
        
        return widget
    
    def _create_visualization_tab(self) -> QWidget:
        """Create visualization display tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Matplotlib canvas
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        return widget
    
    def _on_filter_type_changed(self, filter_type: str):
        """Update filter parameters UI based on filter type"""
        # Clear existing parameters
        while self.filter_params_layout.count():
            child = self.filter_params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if filter_type == "None":
            self.apply_filter_btn.setEnabled(False)
            return
        
        self.apply_filter_btn.setEnabled(True)
        
        if filter_type == "Moving Average":
            window_layout = QVBoxLayout()
            window_label = QLabel("Window Size:")
            window_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
            window_layout.addWidget(window_label)
            self.window_size_spin = QSpinBox()
            self.window_size_spin.setMinimum(3)
            self.window_size_spin.setMaximum(100)
            self.window_size_spin.setValue(5)
            self.window_size_spin.setMinimumHeight(38)
            window_layout.addWidget(self.window_size_spin)
            self.filter_params_layout.addLayout(window_layout)
            
        elif filter_type == "Threshold":
            min_layout = QVBoxLayout()
            min_label = QLabel("Min Value:")
            min_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
            min_layout.addWidget(min_label)
            self.min_value_spin = QDoubleSpinBox()
            self.min_value_spin.setMinimum(-999999)
            self.min_value_spin.setMaximum(999999)
            self.min_value_spin.setValue(0)
            self.min_value_spin.setMinimumHeight(38)
            min_layout.addWidget(self.min_value_spin)
            self.filter_params_layout.addLayout(min_layout)
            
            max_layout = QVBoxLayout()
            max_label = QLabel("Max Value:")
            max_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
            max_layout.addWidget(max_label)
            self.max_value_spin = QDoubleSpinBox()
            self.max_value_spin.setMinimum(-999999)
            self.max_value_spin.setMaximum(999999)
            self.max_value_spin.setValue(200)
            self.max_value_spin.setMinimumHeight(38)
            max_layout.addWidget(self.max_value_spin)
            self.filter_params_layout.addLayout(max_layout)
            
        elif filter_type == "Remove Outliers":
            method_layout = QVBoxLayout()
            method_label = QLabel("Method:")
            method_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
            method_layout.addWidget(method_label)
            self.outlier_method_combo = QComboBox()
            self.outlier_method_combo.addItems(["IQR", "Z-Score"])
            self.outlier_method_combo.setMinimumHeight(38)
            self.outlier_method_combo.setStyleSheet(f"""
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
            method_layout.addWidget(self.outlier_method_combo)
            self.filter_params_layout.addLayout(method_layout)
            
            threshold_layout = QVBoxLayout()
            threshold_label = QLabel("Threshold:")
            threshold_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
            threshold_layout.addWidget(threshold_label)
            self.outlier_threshold_spin = QDoubleSpinBox()
            self.outlier_threshold_spin.setMinimum(0.1)
            self.outlier_threshold_spin.setMaximum(5.0)
            self.outlier_threshold_spin.setValue(1.5)
            self.outlier_threshold_spin.setSingleStep(0.1)
            self.outlier_threshold_spin.setMinimumHeight(38)
            threshold_layout.addWidget(self.outlier_threshold_spin)
            self.filter_params_layout.addLayout(threshold_layout)
    
    def _load_health_metrics(self):
        """Load health metrics from database"""
        try:
            self._update_status("Loading health metrics...", "info")
            session = get_session()
            retriever = DataRetriever(session=session)
            
            # Get health metrics
            metrics_df = retriever.get_health_metrics(limit=1000, as_dataframe=True)
            
            if metrics_df is None or len(metrics_df) == 0:
                QMessageBox.information(
                    self,
                    "No Data",
                    "No health metrics found in database.\n\nPlease import data first using the Data Management tab."
                )
                self._update_status("No health metrics found", "warning")
                return
            
            self.current_data = metrics_df
            self.filtered_data = metrics_df.copy()
            
            # Update patient list
            self._update_patient_list()
            
            # Update metric lists
            self._update_metric_lists()
            
            self._update_status(f"Loaded {len(metrics_df)} health metric records", "success")
            self.apply_filter_btn.setEnabled(True)
            self.compute_corr_btn.setEnabled(True)
            self.generate_viz_btn.setEnabled(True)
            
            # Update statistics
            self._update_statistics()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load health metrics:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
    
    def _update_patient_list(self):
        """Update patient selection dropdown"""
        if self.current_data is None:
            return
        
        self.patient_combo.clear()
        self.patient_combo.addItem("All Patients")
        
        if 'patient_id' in self.current_data.columns:
            unique_patients = sorted(self.current_data['patient_id'].unique())
            for pid in unique_patients:
                self.patient_combo.addItem(f"Patient {pid}")
    
    def _update_metric_lists(self):
        """Update metric selection dropdowns"""
        if self.current_data is None:
            return
        
        # Get numeric columns only
        numeric_cols = self.current_data.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove patient_id and other non-metric columns
        exclude_cols = ['patient_id', 'metric_id', 'id']
        metric_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        # Update metric combo
        self.metric_combo.clear()
        self.metric_combo.addItem("Select metric...")
        self.metric_combo.addItems(metric_cols)
        
        # Update correlation metric combos
        self.corr_metric1_combo.clear()
        self.corr_metric1_combo.addItem("Select metric...")
        self.corr_metric1_combo.addItems(metric_cols)
        
        self.corr_metric2_combo.clear()
        self.corr_metric2_combo.addItem("Select metric...")
        self.corr_metric2_combo.addItems(metric_cols)
    
    def _on_patient_changed(self, patient_text: str):
        """Handle patient selection change"""
        if self.current_data is None:
            return
        
        if patient_text == "All Patients" or not patient_text:
            self.filtered_data = self.current_data.copy()
        else:
            try:
                # Extract patient ID from text like "Patient 123"
                parts = patient_text.split()
                if len(parts) >= 2 and parts[0].lower() == "patient":
                    patient_id = int(parts[-1])
                    self.filtered_data = self.current_data[self.current_data['patient_id'] == patient_id].copy()
                else:
                    # Fallback: try to extract number from text
                    import re
                    numbers = re.findall(r'\d+', patient_text)
                    if numbers:
                        patient_id = int(numbers[-1])
                        self.filtered_data = self.current_data[self.current_data['patient_id'] == patient_id].copy()
                    else:
                        self.filtered_data = self.current_data.copy()
            except (ValueError, IndexError):
                # If parsing fails, use all data
                self.filtered_data = self.current_data.copy()
        
        self._update_statistics()
    
    def _on_metric_changed(self, metric: str):
        """Handle metric selection change"""
        if metric != "Select metric...":
            self._update_statistics()
    
    def _apply_filter(self):
        """Apply selected filter to data"""
        if self.filtered_data is None or len(self.filtered_data) == 0:
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return
        
        filter_type = self.filter_type_combo.currentText()
        if filter_type == "None":
            return
        
        selected_metric = self.metric_combo.currentText()
        if selected_metric == "Select metric...":
            QMessageBox.warning(self, "No Metric", "Please select a metric to filter.")
            return
        
        try:
            data = self.filtered_data[selected_metric].values
            
            if filter_type == "Moving Average":
                window = self.window_size_spin.value()
                filtered = DataFilter.moving_average(data, window_size=window)
                self.filtered_data[selected_metric] = filtered
                
            elif filter_type == "Threshold":
                min_val = self.min_value_spin.value()
                max_val = self.max_value_spin.value()
                filtered, mask = DataFilter.threshold_filter(data, min_val, max_val)
                self.filtered_data[selected_metric] = filtered
                
            elif filter_type == "Remove Outliers":
                method = self.outlier_method_combo.currentText().lower().replace('-', '_')
                threshold = self.outlier_threshold_spin.value()
                filtered, mask = DataFilter.remove_outliers(data, method=method, threshold=threshold)
                self.filtered_data[selected_metric] = filtered
            
            self._update_status(f"Filter '{filter_type}' applied to {selected_metric}", "success")
            self._update_statistics()
            
        except Exception as e:
            QMessageBox.critical(self, "Filter Error", f"Failed to apply filter:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
    
    def _compute_correlation(self):
        """Compute correlation between two metrics"""
        # Check if combo boxes exist and are valid
        if not hasattr(self, 'corr_metric1_combo') or self.corr_metric1_combo is None or \
           not hasattr(self, 'corr_metric2_combo') or self.corr_metric2_combo is None or \
           not hasattr(self, 'corr_method_combo') or self.corr_method_combo is None:
            QMessageBox.warning(self, "Error", "Correlation controls are not available. Please try again.")
            return
        
        try:
            metric1 = self.corr_metric1_combo.currentText()
            metric2 = self.corr_metric2_combo.currentText()
            method = self.corr_method_combo.currentText().lower()
        except RuntimeError:
            QMessageBox.warning(self, "Error", "Controls are not available. Please try again.")
            return
        
        if metric1 == "Select metric..." or metric2 == "Select metric...":
            QMessageBox.warning(self, "Invalid Selection", "Please select both metrics.")
            return
        
        if metric1 == metric2:
            QMessageBox.warning(self, "Invalid Selection", "Please select two different metrics.")
            return
        
        if self.filtered_data is None or len(self.filtered_data) == 0:
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return
        
        # Check if metrics exist in the data
        if metric1 not in self.filtered_data.columns:
            QMessageBox.warning(
                self,
                "Invalid Metric",
                f"Metric '{metric1}' not found in the data.\n\n"
                f"Available metrics: {', '.join(self.filtered_data.columns.tolist()[:10])}"
            )
            return
        
        if metric2 not in self.filtered_data.columns:
            QMessageBox.warning(
                self,
                "Invalid Metric",
                f"Metric '{metric2}' not found in the data.\n\n"
                f"Available metrics: {', '.join(self.filtered_data.columns.tolist()[:10])}"
            )
            return
        
        try:
            self.compute_corr_btn.setEnabled(False)
            self._update_status("Computing correlation...", "info")
            
            # Extract data and handle NaN values
            x = self.filtered_data[metric1].values
            y = self.filtered_data[metric2].values
            
            # Convert to numeric, handling any non-numeric values
            try:
                x = pd.to_numeric(x, errors='coerce')
                y = pd.to_numeric(y, errors='coerce')
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Data Type Error",
                    f"Could not convert metrics to numeric values:\n{str(e)}\n\n"
                    f"Please ensure both metrics contain numeric data."
                )
                return
            
            # Check for valid data after conversion
            valid_mask = ~(pd.isna(x) | pd.isna(y))
            valid_count = np.sum(valid_mask)
            
            if valid_count < 2:
                QMessageBox.warning(
                    self,
                    "Insufficient Data",
                    f"Not enough valid data points for correlation.\n\n"
                    f"Valid pairs: {valid_count} (need at least 2)\n"
                    f"Total data points: {len(x)}\n"
                    f"NaN values in {metric1}: {np.sum(pd.isna(x))}\n"
                    f"NaN values in {metric2}: {np.sum(pd.isna(y))}"
                )
                return
            
            # Check for constant values (zero variance)
            x_clean = x[valid_mask]
            y_clean = y[valid_mask]
            
            if np.std(x_clean) == 0:
                QMessageBox.warning(
                    self,
                    "Invalid Data",
                    f"Metric '{metric1}' has zero variance (all values are the same).\n\n"
                    f"Cannot compute correlation with a constant variable."
                )
                return
            
            if np.std(y_clean) == 0:
                QMessageBox.warning(
                    self,
                    "Invalid Data",
                    f"Metric '{metric2}' has zero variance (all values are the same).\n\n"
                    f"Cannot compute correlation with a constant variable."
                )
                return
            
            analyzer = CorrelationAnalyzer()
            
            if method == 'pearson':
                corr, p_value, n = analyzer.compute_pearson_correlation(x_clean, y_clean)
            elif method == 'spearman':
                corr, p_value, n = analyzer.compute_spearman_correlation(x_clean, y_clean)
            else:
                QMessageBox.warning(self, "Invalid Method", f"Unknown correlation method: {method}")
                return
            
            # Validate results
            if np.isnan(corr) or np.isnan(p_value):
                QMessageBox.warning(
                    self,
                    "Computation Error",
                    "Correlation computation resulted in invalid values (NaN).\n\n"
                    "This may occur if:\n"
                    "- Data has insufficient variation\n"
                    "- All data points are identical\n"
                    "- Numerical precision issues"
                )
                return
            
            # Display results
            result_text = f"""
{method.upper()} Correlation Analysis
{'=' * 40}
Metric 1: {metric1}
Metric 2: {metric2}
{'=' * 40}
Correlation Coefficient: {corr:.4f}
P-value: {p_value:.6f}
Sample Size: {n} (out of {len(x)} total)

Interpretation:
{self._interpret_correlation(corr)}
            """.strip()
            
            self.corr_results_text.setText(result_text)
            self._update_status(f"Correlation computed: {corr:.4f}", "success")
            
            # Generate scatter plot
            self._plot_correlation(metric1, metric2, x_clean, y_clean, corr)
            
        except ValueError as e:
            QMessageBox.warning(self, "Data Validation Error", f"Invalid data for correlation:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
        except Exception as e:
            QMessageBox.critical(self, "Correlation Error", f"Failed to compute correlation:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
        finally:
            self.compute_corr_btn.setEnabled(True)
    
    def _interpret_correlation(self, corr: float) -> str:
        """Interpret correlation coefficient"""
        abs_corr = abs(corr)
        if abs_corr >= 0.9:
            strength = "very strong"
        elif abs_corr >= 0.7:
            strength = "strong"
        elif abs_corr >= 0.5:
            strength = "moderate"
        elif abs_corr >= 0.3:
            strength = "weak"
        else:
            strength = "very weak"
        
        direction = "positive" if corr > 0 else "negative"
        return f"{strength.capitalize()} {direction} correlation"
    
    def _plot_correlation(self, metric1: str, metric2: str, x: np.ndarray, y: np.ndarray, corr: float):
        """Plot correlation scatter plot"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        ax.scatter(x, y, alpha=0.6, s=30, color=COLORS['primary'])
        
        # Add trend line
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        ax.plot(x, p(x), "r--", alpha=0.8, linewidth=2, label=f'Correlation: {corr:.3f}')
        
        ax.set_xlabel(metric1, fontsize=11, fontweight='bold')
        ax.set_ylabel(metric2, fontsize=11, fontweight='bold')
        ax.set_title(f'{metric1} vs {metric2}\nCorrelation: {corr:.4f}', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        self.figure.tight_layout()
        self.canvas.draw()
        self.results_tabs.setCurrentIndex(1)  # Switch to visualization tab
    
    def _generate_visualization(self):
        """Generate time-series visualization"""
        selected_metric = self.metric_combo.currentText()
        if selected_metric == "Select metric...":
            QMessageBox.warning(self, "No Metric", "Please select a metric.")
            return
        
        if self.filtered_data is None or len(self.filtered_data) == 0:
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return
        
        viz_type = self.timeseries_viz_combo.currentText()
        
        try:
            self._update_status(f"Generating {viz_type}...", "info")
            
            data = self.filtered_data[selected_metric].values
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            if viz_type == "Time Series Plot":
                ax.plot(data, color=COLORS['primary'], linewidth=2)
                ax.set_xlabel("Time Index", fontsize=11, fontweight='bold')
                ax.set_ylabel(selected_metric, fontsize=11, fontweight='bold')
                ax.set_title(f"Time Series: {selected_metric}", fontsize=12, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
            elif viz_type == "Trend Analysis":
                analyzer = TimeSeriesAnalyzer()
                trend = analyzer.compute_trend(pd.Series(data), method='linear')
                
                ax.plot(data, color=COLORS['primary'], alpha=0.6, label='Data', linewidth=1.5)
                
                # Plot trend line (always linear for visualization)
                x = np.arange(len(data))
                if 'slope' in trend and 'intercept' in trend:
                    trend_line = trend['slope'] * x + trend['intercept']
                    ax.plot(trend_line, 'r--', linewidth=2, label=f"Trend (slope: {trend['slope']:.4f})")
                    
                    # Add trend statistics to title
                    r_squared = trend.get('r_squared', 0.0)
                    title = f"Trend Analysis: {selected_metric}\nSlope: {trend['slope']:.4f}, R²: {r_squared:.4f}"
                else:
                    # Fallback if trend computation fails
                    title = f"Trend Analysis: {selected_metric}"
                
                ax.set_xlabel("Time Index", fontsize=11, fontweight='bold')
                ax.set_ylabel(selected_metric, fontsize=11, fontweight='bold')
                ax.set_title(title, fontsize=12, fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
            elif viz_type == "Anomaly Detection":
                analyzer = TimeSeriesAnalyzer()
                anomaly_mask, anomalies = analyzer.detect_anomalies(pd.Series(data))
                
                ax.plot(data, color=COLORS['primary'], alpha=0.6, label='Data')
                ax.scatter(
                    np.where(anomaly_mask)[0],
                    anomalies,
                    color=COLORS['error'],
                    s=50,
                    marker='x',
                    label=f'Anomalies ({len(anomalies)})'
                )
                ax.set_xlabel("Time Index", fontsize=11, fontweight='bold')
                ax.set_ylabel(selected_metric, fontsize=11, fontweight='bold')
                ax.set_title(f"Anomaly Detection: {selected_metric}", fontsize=12, fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3)
            
            self.figure.tight_layout()
            self.canvas.draw()
            self.results_tabs.setCurrentIndex(1)  # Switch to visualization tab
            self._update_status(f"{viz_type} generated successfully", "success")
            
        except Exception as e:
            QMessageBox.critical(self, "Visualization Error", f"Failed to generate visualization:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
    
    def _update_statistics(self):
        """Update statistics table"""
        if self.filtered_data is None or len(self.filtered_data) == 0:
            self.stats_table.setRowCount(0)
            return
        
        selected_metric = self.metric_combo.currentText()
        if selected_metric == "Select metric...":
            return
        
        try:
            data = self.filtered_data[selected_metric].dropna()
            
            stats = {
                "Count": len(data),
                "Mean": np.mean(data),
                "Median": np.median(data),
                "Std Deviation": np.std(data),
                "Min": np.min(data),
                "Max": np.max(data),
                "25th Percentile": np.percentile(data, 25),
                "75th Percentile": np.percentile(data, 75),
            }
            
            self.stats_table.setRowCount(len(stats))
            for i, (key, value) in enumerate(stats.items()):
                self.stats_table.setItem(i, 0, QTableWidgetItem(key))
                if isinstance(value, float):
                    self.stats_table.setItem(i, 1, QTableWidgetItem(f"{value:.4f}"))
                else:
                    self.stats_table.setItem(i, 1, QTableWidgetItem(str(value)))
            
        except Exception as e:
            self._update_status(f"Error updating statistics: {str(e)}", "error")
    
    def _apply_analysis(self):
        """Apply all selected analyses"""
        if self.filtered_data is None:
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return
        
        self._update_statistics()
        self._update_status("Analysis applied successfully", "success")
    
    def _reset_all(self):
        """Reset all filters and analysis"""
        reply = QMessageBox.question(
            self,
            "Reset All",
            "Are you sure you want to reset all filters and analysis?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset filter
            self.filter_type_combo.setCurrentIndex(0)
            self._on_filter_type_changed("None")
            
            # Reset correlation
            self.corr_metric1_combo.setCurrentIndex(0)
            self.corr_metric2_combo.setCurrentIndex(0)
            self.corr_results_text.clear()
            
            # Reset data
            if self.current_data is not None:
                self.filtered_data = self.current_data.copy()
                self.patient_combo.setCurrentIndex(0)
            
            # Clear visualizations
            self.figure.clear()
            self.canvas.draw()
            self.stats_table.setRowCount(0)
            
            self._update_status("All filters and analysis reset", "success")
    
    def _load_available_metrics(self):
        """Load available metrics on initialization"""
        # This will be populated when data is loaded
        pass
    
    def _update_status(self, message: str, status_type: str = "info"):
        """Update status label"""
        color_map = {
            "info": COLORS['text_secondary'],
            "success": COLORS['success'],
            "error": COLORS['error'],
            "warning": COLORS['warning']
        }
        color = color_map.get(status_type, COLORS['text_secondary'])
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; padding: 5px;")
