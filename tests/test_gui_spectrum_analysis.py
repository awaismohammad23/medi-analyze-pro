"""
Unit tests for Spectrum Analysis Tab
Tests signal loading, FFT analysis, and visualization functionality
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from src.gui.tabs.spectrum_analysis_tab import SpectrumAnalysisTab


class TestSpectrumAnalysisTab(unittest.TestCase):
    """Test cases for Spectrum Analysis Tab"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test application"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures"""
        self.tab = SpectrumAnalysisTab()
    
    def test_tab_initialization(self):
        """Test that tab initializes correctly"""
        self.assertIsNotNone(self.tab)
        self.assertIsNone(self.tab.current_signal)
        self.assertIsNone(self.tab.current_sampling_rate)
        self.assertIsNone(self.tab.spectrum_data)
    
    def test_signal_type_combo(self):
        """Test signal type combo box"""
        self.assertEqual(self.tab.signal_type_combo.count(), 3)
        self.assertEqual(self.tab.signal_type_combo.itemText(0), "ECG")
        self.assertEqual(self.tab.signal_type_combo.itemText(1), "EEG")
        self.assertEqual(self.tab.signal_type_combo.itemText(2), "Custom")
    
    def test_window_function_combo(self):
        """Test window function combo box"""
        self.assertEqual(self.tab.window_combo.count(), 4)
        self.assertEqual(self.tab.window_combo.currentText(), "Hann")
    
    def test_analysis_type_combo(self):
        """Test analysis type combo box"""
        self.assertEqual(self.tab.analysis_type_combo.count(), 4)
        self.assertIn("Full Analysis", [self.tab.analysis_type_combo.itemText(i) 
                                        for i in range(self.tab.analysis_type_combo.count())])
    
    def test_generate_synthetic_ecg(self):
        """Test generating synthetic ECG signal"""
        with patch('src.gui.tabs.spectrum_analysis_tab.SignalGenerator') as mock_gen:
            mock_generator = Mock()
            mock_generator.generate_ecg.return_value = (
                np.random.randn(2500),  # signal
                250.0,  # sampling rate
                {'duration': 10.0, 'mean': 0.0, 'std': 1.0}  # metadata
            )
            mock_gen.return_value = mock_generator
            
            # Trigger button click
            self.tab._generate_synthetic_signal('ECG')
            
            # Check that signal was loaded
            self.assertIsNotNone(self.tab.current_signal)
            self.assertEqual(self.tab.current_sampling_rate, 250.0)
            self.assertIsNotNone(self.tab.current_metadata)
    
    def test_generate_synthetic_eeg(self):
        """Test generating synthetic EEG signal"""
        with patch('src.gui.tabs.spectrum_analysis_tab.SignalGenerator') as mock_gen:
            mock_generator = Mock()
            mock_generator.generate_eeg.return_value = (
                np.random.randn(2560),  # signal
                256.0,  # sampling rate
                {'duration': 10.0, 'mean': 0.0, 'std': 1.0}  # metadata
            )
            mock_gen.return_value = mock_generator
            
            # Trigger button click
            self.tab._generate_synthetic_signal('EEG')
            
            # Check that signal was loaded
            self.assertIsNotNone(self.tab.current_signal)
            self.assertEqual(self.tab.current_sampling_rate, 256.0)
    
    def test_reset_all(self):
        """Test reset functionality"""
        # Set some values
        self.tab.current_signal = np.random.randn(1000)
        self.tab.current_sampling_rate = 250.0
        self.tab.spectrum_data = {'frequencies': [1, 2, 3]}
        
        # Reset
        self.tab._reset_all()
        
        # Check that everything is reset
        self.assertIsNone(self.tab.current_signal)
        self.assertIsNone(self.tab.current_sampling_rate)
        self.assertIsNone(self.tab.spectrum_data)
        self.assertEqual(self.tab.window_combo.currentText(), "Hann")
        self.assertEqual(self.tab.nfft_spin.value(), 0)
    
    def test_plot_time_domain(self):
        """Test time domain plotting"""
        # Set up signal
        self.tab.current_signal = np.random.randn(1000)
        self.tab.current_sampling_rate = 250.0
        
        # Plot
        self.tab._plot_time_domain()
        
        # Check that plot was created
        self.assertEqual(len(self.tab.time_fig.axes), 1)
    
    def test_update_status(self):
        """Test status update functionality"""
        self.tab._update_status("Test message", "info")
        self.assertEqual(self.tab.status_label.text(), "Test message")
        
        self.tab._update_status("Success message", "success")
        self.assertEqual(self.tab.status_label.text(), "Success message")
    
    def test_analyze_spectrum_no_signal(self):
        """Test that analysis fails gracefully when no signal is loaded"""
        with patch('PyQt5.QtWidgets.QMessageBox.warning') as mock_warning:
            self.tab._analyze_spectrum()
            mock_warning.assert_called_once()
    
    def test_frequency_range_controls(self):
        """Test frequency range spin boxes"""
        self.assertEqual(self.tab.freq_min_spin.value(), 0.0)
        self.assertEqual(self.tab.freq_max_spin.value(), 100.0)
        self.assertEqual(self.tab.freq_min_spin.minimum(), 0.0)
        self.assertEqual(self.tab.freq_max_spin.maximum(), 1000.0)
    
    def test_fft_size_control(self):
        """Test FFT size control"""
        self.assertEqual(self.tab.nfft_spin.value(), 0)  # Auto
        self.assertEqual(self.tab.nfft_spin.minimum(), 0)
        self.assertEqual(self.tab.nfft_spin.maximum(), 100000)
    
    def test_visualization_tabs(self):
        """Test that visualization tabs are created"""
        self.assertEqual(self.tab.viz_tabs.count(), 4)
        self.assertEqual(self.tab.viz_tabs.tabText(0), "Time Domain")
        self.assertEqual(self.tab.viz_tabs.tabText(1), "Frequency Domain")
        self.assertEqual(self.tab.viz_tabs.tabText(2), "Power Spectrum")
        self.assertEqual(self.tab.viz_tabs.tabText(3), "Time-Frequency")
    
    def test_update_visualizations(self):
        """Test visualization update with spectrum data"""
        # Set up signal
        self.tab.current_signal = np.random.randn(1000)
        self.tab.current_sampling_rate = 250.0
        
        # Create mock spectrum data
        frequencies = np.linspace(0, 125, 500)
        fft_values = np.random.randn(500) + 1j * np.random.randn(500)
        power_spectrum = np.abs(fft_values) ** 2
        
        result = {
            'frequencies': frequencies.tolist(),
            'fft_values': fft_values.tolist(),
            'power_spectrum': power_spectrum.tolist()
        }
        
        # Update visualizations
        self.tab._update_visualizations(result)
        
        # Check that plots were updated
        self.assertEqual(len(self.tab.freq_fig.axes), 1)
        self.assertEqual(len(self.tab.power_fig.axes), 1)
        self.assertEqual(len(self.tab.tf_fig.axes), 2)  # Two subplots
    
    def test_update_results_text(self):
        """Test results text update"""
        result = {
            'dominant_frequencies': [
                {'frequency': 10.5, 'power': 1.2, 'amplitude': 1.1},
                {'frequency': 20.3, 'power': 0.8, 'amplitude': 0.9}
            ],
            'total_power': 100.0,
            'mean_power': 10.0,
            'max_power': 50.0,
            'max_frequency': 10.5,
            'frequency_resolution': 0.1,
            'fft_size': 1000,
            'sampling_rate': 250.0,
            'frequencies': np.linspace(0, 125, 500).tolist()
        }
        
        self.tab._update_results_text(result)
        
        text = self.tab.results_text.toPlainText()
        self.assertIn("Spectrum Analysis Results", text)
        self.assertIn("Dominant Frequencies", text)
        self.assertIn("10.5", text)
        self.assertIn("Total Power", text)


if __name__ == '__main__':
    unittest.main()
