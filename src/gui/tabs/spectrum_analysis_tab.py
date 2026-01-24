"""
Spectrum Analysis Tab for MediAnalyze Pro GUI
Provides FFT analysis and frequency domain visualization for biomedical signals
"""

import sys
import os
from typing import Optional, Dict, Any, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSlider, QSpinBox, QDoubleSpinBox, QGroupBox,
    QTextEdit, QSplitter, QScrollArea, QMessageBox, QFileDialog,
    QFormLayout, QTabWidget, QLineEdit
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
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.signal_processing import SignalLoader, SpectrumAnalyzer, SignalGenerator
from src.visualization import SpectrumPlotter
from ..styles import COLORS


class SpectrumWorker(QThread):
    """Worker thread for spectrum analysis operations to prevent UI freezing"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, operation: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs
    
    def run(self):
        """Run spectrum analysis in background thread"""
        try:
            if self.operation == 'fft':
                self.progress.emit(30, "Computing FFT...")
                analyzer = SpectrumAnalyzer()
                signal = self.kwargs['signal']
                sampling_rate = self.kwargs['sampling_rate']
                window = self.kwargs.get('window', 'hann')
                nfft = self.kwargs.get('nfft', None)
                
                frequencies, fft_values = analyzer.compute_fft(signal, sampling_rate, window, nfft)
                
                self.progress.emit(60, "Computing power spectrum...")
                _, power_spectrum = analyzer.compute_power_spectrum(signal, sampling_rate, window, nfft)
                
                self.progress.emit(80, "Finding dominant frequencies...")
                dominant_freqs = analyzer.find_dominant_frequencies(frequencies, power_spectrum, n_peaks=5)
                
                self.progress.emit(100, "Analysis complete!")
                self.finished.emit({
                    'frequencies': frequencies,
                    'fft_values': fft_values,
                    'power_spectrum': power_spectrum,
                    'dominant_frequencies': dominant_freqs
                })
            elif self.operation == 'psd':
                self.progress.emit(50, "Computing PSD...")
                analyzer = SpectrumAnalyzer()
                signal = self.kwargs['signal']
                sampling_rate = self.kwargs['sampling_rate']
                method = self.kwargs.get('method', 'welch')
                nperseg = self.kwargs.get('nperseg', None)
                
                frequencies, psd = analyzer.compute_psd(signal, sampling_rate, method, nperseg)
                
                self.progress.emit(100, "PSD computed!")
                self.finished.emit({
                    'frequencies': frequencies,
                    'psd': psd
                })
            elif self.operation == 'full_analysis':
                self.progress.emit(20, "Performing full spectrum analysis...")
                analyzer = SpectrumAnalyzer()
                signal = self.kwargs['signal']
                sampling_rate = self.kwargs['sampling_rate']
                window = self.kwargs.get('window', 'hann')
                
                result = analyzer.analyze_spectrum(signal, sampling_rate, window=window)
                
                self.progress.emit(100, "Full analysis complete!")
                self.finished.emit(result)
                
        except Exception as e:
            self.error.emit(str(e))


class SpectrumAnalysisTab(QWidget):
    """Spectrum Analysis Tab - FFT and Frequency Domain Analysis"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_signal = None
        self.current_sampling_rate = None
        self.current_metadata = None
        self.spectrum_data = None
        self.spectrum_worker = None
        
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
        
        # Signal loading section
        load_group = self._create_signal_loading_group()
        left_layout.addWidget(load_group)
        
        # FFT analysis controls
        fft_group = self._create_fft_controls_group()
        left_layout.addWidget(fft_group)
        
        # Visualization options
        viz_group = self._create_visualization_group()
        left_layout.addWidget(viz_group)
        
        # Analysis results
        results_group = self._create_results_group()
        left_layout.addWidget(results_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        self.reset_btn = QPushButton("🔄 Reset")
        self.reset_btn.clicked.connect(self._reset_all)
        self.reset_btn.setMinimumHeight(38)
        self.reset_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['secondary']}; "
            f"color: {COLORS['primary']}; "
            f"border: 1px solid {COLORS['primary']};"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {COLORS['primary']}; "
            f"color: {COLORS['button_text']};"
            f"}}"
        )
        action_layout.addWidget(self.reset_btn)
        
        self.analyze_btn = QPushButton("🔍 Perform FFT Analysis")
        self.analyze_btn.clicked.connect(self._analyze_spectrum)
        self.analyze_btn.setMinimumHeight(38)
        self.analyze_btn.setToolTip("Click to perform spectrum analysis (FFT) on the loaded signal")
        self.analyze_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['primary']}; "
            f"color: {COLORS['button_text']}; "
            f"border: none;"
            f"border-radius: 8px;"
            f"font-weight: 600;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {COLORS['primary_dark']};"
            f"}}"
            f"QPushButton:pressed {{"
            f"background-color: {COLORS['button_primary_pressed']};"
            f"}}"
            f"QPushButton:disabled {{"
            f"background-color: {COLORS['border']}; "
            f"color: {COLORS['text_secondary']}; "
            f"opacity: 0.5;"
            f"}}"
        )
        action_layout.addWidget(self.analyze_btn)
        
        left_layout.addLayout(action_layout)
        left_layout.addStretch()
        
        left_widget.setMinimumWidth(380)
        scroll_area.setWidget(left_widget)
        scroll_area.setMinimumWidth(400)
        scroll_area.setMaximumWidth(420)
        splitter.addWidget(scroll_area)
        
        # Right side: Visualizations
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create tab widget for different visualizations
        self.viz_tabs = QTabWidget()
        self.viz_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                background-color: {COLORS['surface']};
                border-radius: 6px;
            }}
            QTabBar::tab {{
                background-color: {COLORS['background']};
                color: {COLORS['text_primary']};
                padding: 10px 20px;
                border: 1px solid {COLORS['border']};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['button_text']};
            }}
            QTabBar::tab:hover {{
                background-color: {COLORS['primary_light']};
            }}
        """)
        
        # Time domain plot
        self.time_fig = Figure(figsize=(10, 4), dpi=100)
        self.time_canvas = FigureCanvas(self.time_fig)
        # Enable interactive mode and mouse wheel zoom
        self.time_canvas.setFocusPolicy(Qt.ClickFocus)
        self.time_canvas.mpl_connect('scroll_event', self._on_time_scroll)
        self.time_toolbar = NavigationToolbar(self.time_canvas, self)
        # Store original view limits for reset
        self.time_original_limits = None
        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(0)
        time_layout.addWidget(self.time_toolbar)
        time_layout.addWidget(self.time_canvas)
        self.viz_tabs.addTab(time_widget, "Time Domain")
        
        # Frequency domain plot (FFT Magnitude)
        self.freq_fig = Figure(figsize=(10, 4), dpi=100)
        self.freq_canvas = FigureCanvas(self.freq_fig)
        self.freq_canvas.setFocusPolicy(Qt.ClickFocus)
        self.freq_canvas.mpl_connect('scroll_event', self._on_freq_scroll)
        self.freq_toolbar = NavigationToolbar(self.freq_canvas, self)
        self.freq_original_limits = None
        freq_widget = QWidget()
        freq_layout = QVBoxLayout(freq_widget)
        freq_layout.setContentsMargins(0, 0, 0, 0)
        freq_layout.setSpacing(0)
        freq_layout.addWidget(self.freq_toolbar)
        freq_layout.addWidget(self.freq_canvas)
        self.viz_tabs.addTab(freq_widget, "Frequency Domain")
        
        # Power Spectrum plot
        self.power_fig = Figure(figsize=(10, 4), dpi=100)
        self.power_canvas = FigureCanvas(self.power_fig)
        self.power_canvas.setFocusPolicy(Qt.ClickFocus)
        self.power_canvas.mpl_connect('scroll_event', self._on_power_scroll)
        self.power_toolbar = NavigationToolbar(self.power_canvas, self)
        self.power_original_limits = None
        power_widget = QWidget()
        power_layout = QVBoxLayout(power_widget)
        power_layout.setContentsMargins(0, 0, 0, 0)
        power_layout.setSpacing(0)
        power_layout.addWidget(self.power_toolbar)
        power_layout.addWidget(self.power_canvas)
        self.viz_tabs.addTab(power_widget, "Power Spectrum")
        
        # Time-Frequency plot
        self.tf_fig = Figure(figsize=(10, 6), dpi=100)
        self.tf_canvas = FigureCanvas(self.tf_fig)
        self.tf_canvas.setFocusPolicy(Qt.ClickFocus)
        self.tf_canvas.mpl_connect('scroll_event', self._on_tf_scroll)
        self.tf_toolbar = NavigationToolbar(self.tf_canvas, self)
        self.tf_original_limits = None
        tf_widget = QWidget()
        tf_layout = QVBoxLayout(tf_widget)
        tf_layout.setContentsMargins(0, 0, 0, 0)
        tf_layout.setSpacing(0)
        tf_layout.addWidget(self.tf_toolbar)
        tf_layout.addWidget(self.tf_canvas)
        self.viz_tabs.addTab(tf_widget, "Time-Frequency")
        
        right_layout.addWidget(self.viz_tabs)
        
        # Status bar
        self.status_label = QLabel("Ready")
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
        
        # Initialize empty plots
        self._init_plots()
    
    def _create_signal_loading_group(self) -> QGroupBox:
        """Create signal loading section"""
        group = QGroupBox("Signal Loading")
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
        
        # Signal type selection
        type_layout = QVBoxLayout()
        type_label = QLabel("Signal Type:")
        type_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        type_layout.addWidget(type_label)
        self.signal_type_combo = QComboBox()
        self.signal_type_combo.addItems(["ECG", "EEG", "Custom"])
        self.signal_type_combo.setMinimumHeight(38)
        self.signal_type_combo.setStyleSheet(f"""
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
        type_layout.addWidget(self.signal_type_combo)
        layout.addLayout(type_layout)
        
        # File loading
        file_layout = QVBoxLayout()
        file_label = QLabel("Load Signal File:")
        file_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        file_layout.addWidget(file_label)
        
        file_btn_layout = QHBoxLayout()
        self.load_file_btn = QPushButton("📁 Browse File")
        self.load_file_btn.clicked.connect(self._load_signal_file)
        self.load_file_btn.setMinimumHeight(38)
        self.load_file_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['primary']}; "
            f"color: {COLORS['button_text']}; "
            f"border: none;"
            f"border-radius: 8px;"
            f"font-weight: 600;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {COLORS['primary_dark']};"
            f"}}"
        )
        file_btn_layout.addWidget(self.load_file_btn)
        layout.addLayout(file_layout)
        layout.addLayout(file_btn_layout)
        
        # Or generate synthetic signal
        synth_layout = QVBoxLayout()
        synth_label = QLabel("Generate Synthetic Signal:")
        synth_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        synth_layout.addWidget(synth_label)
        
        synth_btn_layout = QHBoxLayout()
        self.generate_ecg_btn = QPushButton("📊 Generate ECG")
        self.generate_ecg_btn.clicked.connect(lambda: self._generate_synthetic_signal('ECG'))
        self.generate_ecg_btn.setMinimumHeight(38)
        self.generate_ecg_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['success']}; "
            f"color: {COLORS['button_text']}; "
            f"border: none;"
            f"border-radius: 8px;"
            f"font-weight: 600;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: #27AE60;"
            f"}}"
        )
        synth_btn_layout.addWidget(self.generate_ecg_btn)
        
        self.generate_eeg_btn = QPushButton("📈 Generate EEG")
        self.generate_eeg_btn.clicked.connect(lambda: self._generate_synthetic_signal('EEG'))
        self.generate_eeg_btn.setMinimumHeight(38)
        self.generate_eeg_btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['success']}; "
            f"color: {COLORS['button_text']}; "
            f"border: none;"
            f"border-radius: 8px;"
            f"font-weight: 600;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: #27AE60;"
            f"}}"
        )
        synth_btn_layout.addWidget(self.generate_eeg_btn)
        synth_layout.addLayout(synth_btn_layout)
        layout.addLayout(synth_layout)
        
        # Signal info display
        self.signal_info_label = QLabel("No signal loaded")
        self.signal_info_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['background']};
                color: {COLORS['text_secondary']};
                padding: 8px;
                border-radius: 6px;
                border: 1px solid {COLORS['border']};
                font-size: 10pt;
            }}
        """)
        self.signal_info_label.setWordWrap(True)
        layout.addWidget(self.signal_info_label)
        
        group.setLayout(layout)
        return group
    
    def _create_fft_controls_group(self) -> QGroupBox:
        """Create FFT analysis controls section"""
        group = QGroupBox("FFT Analysis Controls")
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
        
        # Window function
        window_layout = QVBoxLayout()
        window_label = QLabel("Window Function:")
        window_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        window_layout.addWidget(window_label)
        self.window_combo = QComboBox()
        self.window_combo.addItems(["None", "Hann", "Hamming", "Blackman"])
        self.window_combo.setCurrentText("Hann")
        self.window_combo.setMinimumHeight(38)
        self.window_combo.setStyleSheet(f"""
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
        window_layout.addWidget(self.window_combo)
        layout.addLayout(window_layout)
        
        # FFT size
        nfft_layout = QVBoxLayout()
        nfft_label = QLabel("FFT Size (0 = auto):")
        nfft_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        nfft_layout.addWidget(nfft_label)
        self.nfft_spin = QSpinBox()
        self.nfft_spin.setMinimum(0)
        self.nfft_spin.setMaximum(100000)
        self.nfft_spin.setValue(0)
        self.nfft_spin.setMinimumHeight(38)
        self.nfft_spin.setStyleSheet(f"""
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
        nfft_layout.addWidget(self.nfft_spin)
        layout.addLayout(nfft_layout)
        
        # Frequency range
        freq_range_layout = QVBoxLayout()
        freq_range_label = QLabel("Frequency Range (Hz):")
        freq_range_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        freq_range_layout.addWidget(freq_range_label)
        
        freq_min_layout = QHBoxLayout()
        freq_min_layout.addWidget(QLabel("Min:"))
        self.freq_min_spin = QDoubleSpinBox()
        self.freq_min_spin.setMinimum(0.0)
        self.freq_min_spin.setMaximum(1000.0)
        self.freq_min_spin.setValue(0.0)
        self.freq_min_spin.setSingleStep(1.0)
        self.freq_min_spin.setMinimumHeight(38)
        self.freq_min_spin.setStyleSheet(f"""
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
        freq_min_layout.addWidget(self.freq_min_spin)
        
        freq_max_layout = QHBoxLayout()
        freq_max_layout.addWidget(QLabel("Max:"))
        self.freq_max_spin = QDoubleSpinBox()
        self.freq_max_spin.setMinimum(0.0)
        self.freq_max_spin.setMaximum(1000.0)
        self.freq_max_spin.setValue(100.0)
        self.freq_max_spin.setSingleStep(1.0)
        self.freq_max_spin.setMinimumHeight(38)
        self.freq_max_spin.setStyleSheet(f"""
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
        freq_max_layout.addWidget(self.freq_max_spin)
        
        freq_range_layout.addLayout(freq_min_layout)
        freq_range_layout.addLayout(freq_max_layout)
        layout.addLayout(freq_range_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_visualization_group(self) -> QGroupBox:
        """Create visualization options section"""
        group = QGroupBox("Visualization Options")
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
        
        # Analysis type
        analysis_layout = QVBoxLayout()
        analysis_label = QLabel("Analysis Type:")
        analysis_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 11pt;")
        analysis_layout.addWidget(analysis_label)
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems(["FFT Magnitude", "Power Spectrum", "PSD (Welch)", "Full Analysis"])
        self.analysis_type_combo.setCurrentText("Full Analysis")
        self.analysis_type_combo.setMinimumHeight(38)
        self.analysis_type_combo.setStyleSheet(f"""
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
        analysis_layout.addWidget(self.analysis_type_combo)
        layout.addLayout(analysis_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_results_group(self) -> QGroupBox:
        """Create analysis results display section"""
        group = QGroupBox("Analysis Results")
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
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(150)
        self.results_text.setStyleSheet(f"""
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
        self.results_text.setPlainText("No analysis performed yet.")
        layout.addWidget(self.results_text)
        
        group.setLayout(layout)
        return group
    
    def _init_plots(self):
        """Initialize empty plots"""
        # Time domain
        self.time_fig.clear()
        ax = self.time_fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Load a signal to view time domain plot', 
                ha='center', va='center', transform=ax.transAxes,
                fontsize=12, color=COLORS['text_secondary'])
        ax.set_xlabel('Time (s)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Amplitude', fontsize=11, fontweight='bold')
        ax.set_title('Time Domain Signal', fontsize=12, fontweight='bold')
        self.time_fig.tight_layout()
        self.time_canvas.draw()
        
        # Frequency domain
        self.freq_fig.clear()
        ax = self.freq_fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Perform FFT analysis to view frequency domain', 
                ha='center', va='center', transform=ax.transAxes,
                fontsize=12, color=COLORS['text_secondary'])
        ax.set_xlabel('Frequency (Hz)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Magnitude', fontsize=11, fontweight='bold')
        ax.set_title('FFT Magnitude Spectrum', fontsize=12, fontweight='bold')
        self.freq_fig.tight_layout()
        self.freq_canvas.draw()
        
        # Power spectrum
        self.power_fig.clear()
        ax = self.power_fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Perform analysis to view power spectrum', 
                ha='center', va='center', transform=ax.transAxes,
                fontsize=12, color=COLORS['text_secondary'])
        ax.set_xlabel('Frequency (Hz)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Power', fontsize=11, fontweight='bold')
        ax.set_title('Power Spectrum', fontsize=12, fontweight='bold')
        self.power_fig.tight_layout()
        self.power_canvas.draw()
        
        # Time-frequency
        self.tf_fig.clear()
        ax = self.tf_fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Load signal and analyze to view time-frequency plot', 
                ha='center', va='center', transform=ax.transAxes,
                fontsize=12, color=COLORS['text_secondary'])
        ax.set_xlabel('Time (s)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Frequency (Hz)', fontsize=11, fontweight='bold')
        ax.set_title('Time-Frequency Analysis', fontsize=12, fontweight='bold')
        self.tf_fig.tight_layout()
        self.tf_canvas.draw()
    
    def _load_signal_file(self):
        """Load signal from file"""
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
            
            self.current_signal = signal_data
            self.current_sampling_rate = sampling_rate
            self.current_metadata = metadata
            
            # Update signal info
            info_text = f"Signal loaded:\n"
            info_text += f"Length: {len(signal_data)} samples\n"
            info_text += f"Duration: {metadata['duration']:.2f} s\n"
            info_text += f"Sampling Rate: {sampling_rate:.2f} Hz\n"
            info_text += f"Mean: {metadata['mean']:.4f}\n"
            info_text += f"Std: {metadata['std']:.4f}"
            self.signal_info_label.setText(info_text)
            
            # Update frequency range based on sampling rate
            nyquist = sampling_rate / 2
            self.freq_max_spin.setMaximum(nyquist)
            self.freq_max_spin.setValue(min(100.0, nyquist))
            
            # Plot time domain
            self._plot_time_domain()
            
            self._update_status("Signal loaded successfully", "success")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load signal:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
    
    def _generate_synthetic_signal(self, signal_type: str):
        """Generate synthetic signal"""
        try:
            self._update_status(f"Generating synthetic {signal_type} signal...", "info")
            generator = SignalGenerator()
            
            if signal_type == 'ECG':
                signal_data, sampling_rate, metadata = generator.generate_ecg(
                    duration=10.0,
                    sampling_rate=250.0,
                    heart_rate=72.0
                )
            elif signal_type == 'EEG':
                signal_data, sampling_rate, metadata = generator.generate_eeg(
                    duration=10.0,
                    sampling_rate=256.0
                )
            else:
                return
            
            self.current_signal = signal_data
            self.current_sampling_rate = sampling_rate
            self.current_metadata = metadata
            
            # Calculate statistics from signal data
            signal_mean = float(np.mean(signal_data))
            signal_std = float(np.std(signal_data))
            signal_min = float(np.min(signal_data))
            signal_max = float(np.max(signal_data))
            
            # Update signal info
            info_text = f"Synthetic {signal_type} signal:\n"
            info_text += f"Length: {len(signal_data)} samples\n"
            info_text += f"Duration: {metadata.get('duration', len(signal_data) / sampling_rate):.2f} s\n"
            info_text += f"Sampling Rate: {sampling_rate:.2f} Hz\n"
            info_text += f"Mean: {signal_mean:.4f}\n"
            info_text += f"Std: {signal_std:.4f}\n"
            info_text += f"Min: {signal_min:.4f}\n"
            info_text += f"Max: {signal_max:.4f}"
            
            # Add signal-specific info
            if signal_type == 'ECG' and 'heart_rate' in metadata:
                info_text += f"\nHeart Rate: {metadata['heart_rate']:.1f} bpm"
            
            self.signal_info_label.setText(info_text)
            
            # Update frequency range
            nyquist = sampling_rate / 2
            self.freq_max_spin.setMaximum(nyquist)
            self.freq_max_spin.setValue(min(100.0, nyquist))
            
            # Plot time domain
            self._plot_time_domain()
            
            self._update_status(f"Synthetic {signal_type} signal generated", "success")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate signal:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
    
    def _plot_time_domain(self):
        """Plot time domain signal"""
        if self.current_signal is None:
            return
        
        self.time_fig.clear()
        ax = self.time_fig.add_subplot(111)
        
        time = np.arange(len(self.current_signal)) / self.current_sampling_rate
        ax.plot(time, self.current_signal, color=COLORS['primary'], linewidth=1.5, alpha=0.8)
        
        ax.set_xlabel('Time (s)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Amplitude', fontsize=11, fontweight='bold')
        ax.set_title('Time Domain Signal', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Enable interactive features
        ax.set_xlim(auto=True)
        ax.set_ylim(auto=True)
        
        # Store original limits for reset
        self.time_original_limits = (ax.get_xlim(), ax.get_ylim())
        
        self.time_fig.tight_layout()
        self.time_canvas.draw()
        
        # Force toolbar update
        if hasattr(self, 'time_toolbar'):
            self.time_toolbar.update()
    
    def _analyze_spectrum(self):
        """Perform spectrum analysis"""
        if self.current_signal is None:
            QMessageBox.warning(self, "No Signal", "Please load or generate a signal first.")
            return
        
        if self.spectrum_worker is not None and self.spectrum_worker.isRunning():
            QMessageBox.warning(self, "Analysis Running", "Analysis is already in progress. Please wait.")
            return
        
        # Get analysis parameters
        window_text = self.window_combo.currentText().lower()
        window = None if window_text == 'none' else window_text
        nfft = self.nfft_spin.value() if self.nfft_spin.value() > 0 else None
        analysis_type = self.analysis_type_combo.currentText()
        
        # Start worker thread
        if analysis_type == "Full Analysis":
            self.spectrum_worker = SpectrumWorker(
                'full_analysis',
                signal=self.current_signal,
                sampling_rate=self.current_sampling_rate,
                window=window
            )
        elif analysis_type == "PSD (Welch)":
            self.spectrum_worker = SpectrumWorker(
                'psd',
                signal=self.current_signal,
                sampling_rate=self.current_sampling_rate,
                method='welch'
            )
        else:
            self.spectrum_worker = SpectrumWorker(
                'fft',
                signal=self.current_signal,
                sampling_rate=self.current_sampling_rate,
                window=window,
                nfft=nfft
            )
        
        self.spectrum_worker.progress.connect(self._on_analysis_progress)
        self.spectrum_worker.finished.connect(self._on_analysis_finished)
        self.spectrum_worker.error.connect(self._on_analysis_error)
        
        self.analyze_btn.setEnabled(False)
        self._update_status("Starting analysis...", "info")
        self.spectrum_worker.start()
    
    def _on_analysis_progress(self, value: int, message: str):
        """Handle analysis progress updates"""
        self._update_status(f"{message} ({value}%)", "info")
    
    def _on_analysis_finished(self, result: Dict[str, Any]):
        """Handle analysis completion"""
        self.spectrum_data = result
        self.analyze_btn.setEnabled(True)
        
        # Update visualizations
        self._update_visualizations(result)
        
        # Update results text
        self._update_results_text(result)
        
        self._update_status("Analysis complete!", "success")
    
    def _on_analysis_error(self, error_msg: str):
        """Handle analysis errors"""
        self.analyze_btn.setEnabled(True)
        QMessageBox.critical(self, "Analysis Error", f"Failed to perform analysis:\n{error_msg}")
        self._update_status(f"Error: {error_msg}", "error")
    
    def _update_visualizations(self, result: Dict[str, Any]):
        """Update all visualization plots"""
        freq_min = self.freq_min_spin.value()
        freq_max = self.freq_max_spin.value()
        
        # Frequency domain (FFT Magnitude)
        if 'frequencies' in result and 'fft_values' in result:
            frequencies = np.array(result['frequencies'])
            fft_values = np.array(result['fft_values'])
            fft_magnitude = np.abs(fft_values)
            
            # Filter by frequency range
            freq_mask = (frequencies >= freq_min) & (frequencies <= freq_max)
            frequencies_filtered = frequencies[freq_mask]
            fft_magnitude_filtered = fft_magnitude[freq_mask]
            
            self.freq_fig.clear()
            ax = self.freq_fig.add_subplot(111)
            ax.plot(frequencies_filtered, fft_magnitude_filtered, 
                   color=COLORS['primary'], linewidth=2, alpha=0.8)
            ax.set_xlabel('Frequency (Hz)', fontsize=11, fontweight='bold')
            ax.set_ylabel('Magnitude', fontsize=11, fontweight='bold')
            ax.set_title('FFT Magnitude Spectrum', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(auto=True)
            ax.set_ylim(auto=True)
            self.freq_original_limits = (ax.get_xlim(), ax.get_ylim())
            self.freq_fig.tight_layout()
            self.freq_canvas.draw()
            if hasattr(self, 'freq_toolbar'):
                self.freq_toolbar.update()
        
        # Power spectrum
        if 'frequencies' in result and 'power_spectrum' in result:
            frequencies = np.array(result['frequencies'])
            power_spectrum = np.array(result['power_spectrum'])
            
            # Filter by frequency range
            freq_mask = (frequencies >= freq_min) & (frequencies <= freq_max)
            frequencies_filtered = frequencies[freq_mask]
            power_spectrum_filtered = power_spectrum[freq_mask]
            
            self.power_fig.clear()
            ax = self.power_fig.add_subplot(111)
            ax.plot(frequencies_filtered, power_spectrum_filtered, 
                   color=COLORS['success'], linewidth=2, alpha=0.8)
            ax.set_xlabel('Frequency (Hz)', fontsize=11, fontweight='bold')
            ax.set_ylabel('Power', fontsize=11, fontweight='bold')
            ax.set_title('Power Spectrum', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(auto=True)
            ax.set_ylim(auto=True)
            self.power_original_limits = (ax.get_xlim(), ax.get_ylim())
            self.power_fig.tight_layout()
            self.power_canvas.draw()
            if hasattr(self, 'power_toolbar'):
                self.power_toolbar.update()
        
        # Time-Frequency plot
        if self.current_signal is not None and 'frequencies' in result:
            self.tf_fig.clear()
            ax1 = self.tf_fig.add_subplot(211)
            ax2 = self.tf_fig.add_subplot(212)
            
            # Time domain
            time = np.arange(len(self.current_signal)) / self.current_sampling_rate
            ax1.plot(time, self.current_signal, color=COLORS['primary'], linewidth=1.5, alpha=0.8)
            ax1.set_xlabel('Time (s)', fontsize=11, fontweight='bold')
            ax1.set_ylabel('Amplitude', fontsize=11, fontweight='bold')
            ax1.set_title('Time Domain', fontsize=11, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            
            # Frequency domain
            frequencies = np.array(result['frequencies'])
            if 'fft_values' in result:
                fft_values = np.array(result['fft_values'])
                fft_magnitude = np.abs(fft_values)
            elif 'power_spectrum' in result:
                power_spectrum = np.array(result['power_spectrum'])
                fft_magnitude = np.sqrt(power_spectrum)
            else:
                fft_magnitude = np.zeros_like(frequencies)
            
            freq_mask = (frequencies >= freq_min) & (frequencies <= freq_max)
            frequencies_filtered = frequencies[freq_mask]
            fft_magnitude_filtered = fft_magnitude[freq_mask]
            
            ax2.plot(frequencies_filtered, fft_magnitude_filtered, 
                    color=COLORS['success'], linewidth=2, alpha=0.8)
            ax2.set_xlabel('Frequency (Hz)', fontsize=11, fontweight='bold')
            ax2.set_ylabel('Magnitude', fontsize=11, fontweight='bold')
            ax2.set_title('Frequency Domain', fontsize=11, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax1.set_xlim(auto=True)
            ax1.set_ylim(auto=True)
            ax2.set_xlim(auto=True)
            ax2.set_ylim(auto=True)
            
            # Store original limits for reset
            self.tf_original_limits = {
                0: (ax1.get_xlim(), ax1.get_ylim()),
                1: (ax2.get_xlim(), ax2.get_ylim())
            }
            
            self.tf_fig.suptitle('Time-Frequency Analysis', fontsize=13, fontweight='bold')
            self.tf_fig.tight_layout()
            self.tf_canvas.draw()
            if hasattr(self, 'tf_toolbar'):
                self.tf_toolbar.update()
    
    def _update_results_text(self, result: Dict[str, Any]):
        """Update results text display"""
        text = "=== Spectrum Analysis Results ===\n\n"
        
        if 'dominant_frequencies' in result:
            text += "Dominant Frequencies:\n"
            for i, freq_info in enumerate(result['dominant_frequencies'][:5], 1):
                text += f"  {i}. {freq_info['frequency']:.4f} Hz "
                text += f"(Power: {freq_info['power']:.4e}, "
                text += f"Amplitude: {freq_info['amplitude']:.4f})\n"
            text += "\n"
        
        if 'total_power' in result:
            text += f"Total Power: {result['total_power']:.4e}\n"
            text += f"Mean Power: {result.get('mean_power', 0):.4e}\n"
            text += f"Max Power: {result.get('max_power', 0):.4e}\n"
            text += f"Max Frequency: {result.get('max_frequency', 0):.4f} Hz\n"
            text += f"Frequency Resolution: {result.get('frequency_resolution', 0):.4f} Hz\n"
            text += f"FFT Size: {result.get('fft_size', 0)}\n"
            text += f"Sampling Rate: {result.get('sampling_rate', 0):.2f} Hz\n"
        
        if 'frequencies' in result:
            text += f"\nFrequency Range: {np.min(result['frequencies']):.2f} - "
            text += f"{np.max(result['frequencies']):.2f} Hz\n"
            text += f"Number of Frequency Bins: {len(result['frequencies'])}\n"
        
        self.results_text.setPlainText(text)
    
    def _reset_all(self):
        """Reset all controls and plots"""
        self.current_signal = None
        self.current_sampling_rate = None
        self.current_metadata = None
        self.spectrum_data = None
        
        self.signal_info_label.setText("No signal loaded")
        self.results_text.setPlainText("No analysis performed yet.")
        
        # Reset controls
        self.window_combo.setCurrentText("Hann")
        self.nfft_spin.setValue(0)
        self.freq_min_spin.setValue(0.0)
        self.freq_max_spin.setValue(100.0)
        self.analysis_type_combo.setCurrentText("Full Analysis")
        
        # Reset plots
        self._init_plots()
        
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
    
    def _on_time_scroll(self, event):
        """Handle mouse wheel zoom for time domain plot"""
        if not self.time_fig.axes or event.inaxes != self.time_fig.axes[0]:
            return
        
        ax = self.time_fig.axes[0]
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        
        # Store original limits on first interaction
        if self.time_original_limits is None:
            self.time_original_limits = (cur_xlim, cur_ylim)
        
        xdata = event.xdata
        ydata = event.ydata
        
        if xdata is None or ydata is None:
            return
        
        # Zoom factor
        zoom_factor = 1.1 if event.button == 'up' else 0.9
        
        # Get distance from the cursor
        x_left = xdata - cur_xlim[0]
        x_right = cur_xlim[1] - xdata
        y_bottom = ydata - cur_ylim[0]
        y_top = cur_ylim[1] - ydata
        
        # Apply zoom
        ax.set_xlim([xdata - x_left * zoom_factor, xdata + x_right * zoom_factor])
        ax.set_ylim([ydata - y_bottom * zoom_factor, ydata + y_top * zoom_factor])
        
        self.time_canvas.draw()
    
    def _on_freq_scroll(self, event):
        """Handle mouse wheel zoom for frequency domain plot"""
        if not self.freq_fig.axes or event.inaxes != self.freq_fig.axes[0]:
            return
        
        ax = self.freq_fig.axes[0]
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        
        if self.freq_original_limits is None:
            self.freq_original_limits = (cur_xlim, cur_ylim)
        
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
        
        self.freq_canvas.draw()
    
    def _on_power_scroll(self, event):
        """Handle mouse wheel zoom for power spectrum plot"""
        if not self.power_fig.axes or event.inaxes != self.power_fig.axes[0]:
            return
        
        ax = self.power_fig.axes[0]
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        
        if self.power_original_limits is None:
            self.power_original_limits = (cur_xlim, cur_ylim)
        
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
        
        self.power_canvas.draw()
    
    def _on_tf_scroll(self, event):
        """Handle mouse wheel zoom for time-frequency plot"""
        if not self.tf_fig.axes:
            return
        
        # Determine which subplot
        ax = None
        for a in self.tf_fig.axes:
            if event.inaxes == a:
                ax = a
                break
        
        if ax is None:
            return
        
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        
        if self.tf_original_limits is None:
            self.tf_original_limits = {i: (a.get_xlim(), a.get_ylim()) 
                                      for i, a in enumerate(self.tf_fig.axes)}
        
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
        
        self.tf_canvas.draw()
