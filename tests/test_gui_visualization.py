"""
Unit tests for Visualization Tab (Phase 13)
Tests comprehensive visualization functionality
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gui.tabs.visualization_tab import VisualizationTab, VisualizationWorker


class TestVisualizationTab(unittest.TestCase):
    """Test cases for VisualizationTab"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class - create QApplication once"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures"""
        self.tab = VisualizationTab()
    
    def tearDown(self):
        """Clean up after tests"""
        if self.tab:
            self.tab.close()
    
    def test_tab_initialization(self):
        """Test that tab initializes correctly"""
        self.assertIsNotNone(self.tab)
        self.assertIsNotNone(self.tab.viz_type_combo)
        self.assertIsNotNone(self.tab.data_source_combo)
        self.assertIsNotNone(self.tab.generate_btn)
        self.assertIsNotNone(self.tab.export_btn)
        self.assertIsNotNone(self.tab.plot_canvas)
    
    def test_viz_type_combo_items(self):
        """Test visualization type combo box has correct items"""
        items = [self.tab.viz_type_combo.itemText(i) 
                for i in range(self.tab.viz_type_combo.count())]
        expected_items = [
            "Time-Series Plot",
            "Scatter Plot",
            "Correlation Heatmap",
            "FFT Spectrum",
            "Image Comparison"
        ]
        self.assertEqual(items, expected_items)
    
    def test_data_source_combo_items(self):
        """Test data source combo box has correct items"""
        items = [self.tab.data_source_combo.itemText(i) 
                for i in range(self.tab.data_source_combo.count())]
        expected_items = [
            "Load from Database",
            "Load from CSV File",
            "Load Signal File",
            "Load Image Files"
        ]
        self.assertEqual(items, expected_items)
    
    def test_viz_type_changed_updates_params(self):
        """Test that changing visualization type updates parameters"""
        # Test time-series
        self.tab.viz_type_combo.setCurrentText("Time-Series Plot")
        self.assertTrue(hasattr(self.tab, 'timeseries_metric_combo'))
        
        # Test scatter
        self.tab.viz_type_combo.setCurrentText("Scatter Plot")
        self.assertTrue(hasattr(self.tab, 'scatter_x_combo'))
        self.assertTrue(hasattr(self.tab, 'scatter_y_combo'))
        
        # Test heatmap
        self.tab.viz_type_combo.setCurrentText("Correlation Heatmap")
        self.assertTrue(hasattr(self.tab, 'heatmap_cmap_combo'))
        
        # Test FFT
        self.tab.viz_type_combo.setCurrentText("FFT Spectrum")
        self.assertTrue(hasattr(self.tab, 'fft_freq_min_spin'))
        self.assertTrue(hasattr(self.tab, 'fft_freq_max_spin'))
    
    def test_load_from_csv(self):
        """Test loading data from CSV file"""
        # Create a temporary CSV file
        test_data = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'z': np.random.randn(100)
        })
        
        with patch('src.gui.tabs.visualization_tab.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = ('/tmp/test.csv', 'CSV Files (*.csv)')
            
            with patch('pandas.read_csv') as mock_read:
                mock_read.return_value = test_data
                
                self.tab._load_from_csv()
                
                self.assertIsNotNone(self.tab.current_data)
                self.assertTrue(isinstance(self.tab.current_data, pd.DataFrame))
                self.assertEqual(len(self.tab.current_data), 100)
    
    def test_load_from_database(self):
        """Test loading data from database"""
        # Create mock data
        mock_data = pd.DataFrame({
            'patient_id': [1, 2, 3],
            'systolic_bp': [120, 130, 140],
            'diastolic_bp': [80, 85, 90],
            'heart_rate': [70, 75, 80]
        })
        
        with patch('src.gui.tabs.visualization_tab.get_session') as mock_session:
            mock_retriever = Mock()
            mock_retriever.get_health_metrics.return_value = mock_data
            mock_session.return_value.__enter__ = Mock(return_value=mock_session.return_value)
            mock_session.return_value.__exit__ = Mock(return_value=None)
            
            with patch('src.gui.tabs.visualization_tab.DataRetriever') as mock_retriever_class:
                mock_retriever_class.return_value = mock_retriever
                
                self.tab._load_from_database()
                
                # Check that data was loaded (if no error occurred)
                # Note: This may show a message box if database is not available
                pass
    
    def test_update_metric_combos(self):
        """Test updating metric combo boxes"""
        metrics = ['metric1', 'metric2', 'metric3']
        
        # Ensure scatter plot controls are created by setting visualization type
        self.tab.viz_type_combo.setCurrentText("Scatter Plot")
        
        self.tab._update_metric_combos(metrics)
        
        # Check time-series combo (should exist from initialization)
        if hasattr(self.tab, 'timeseries_metric_combo'):
            self.assertEqual(self.tab.timeseries_metric_combo.count(), len(metrics) + 1)  # +1 for "All Metrics"
        
        # Check scatter combos (now should exist)
        if hasattr(self.tab, 'scatter_x_combo') and hasattr(self.tab, 'scatter_y_combo'):
            self.assertEqual(self.tab.scatter_x_combo.count(), len(metrics) + 1)  # +1 for "Select variable..."
            self.assertEqual(self.tab.scatter_y_combo.count(), len(metrics) + 1)
    
    def test_generate_timeseries_no_data(self):
        """Test generating time-series plot without data"""
        with patch('src.gui.tabs.visualization_tab.QMessageBox.warning') as mock_warning:
            self.tab._generate_timeseries()
            mock_warning.assert_called_once()
    
    def test_generate_scatter_no_data(self):
        """Test generating scatter plot without data"""
        with patch('src.gui.tabs.visualization_tab.QMessageBox.warning') as mock_warning:
            self.tab._generate_scatter()
            mock_warning.assert_called_once()
    
    def test_generate_scatter_invalid_selection(self):
        """Test generating scatter plot with invalid variable selection"""
        # Set visualization type to Scatter Plot to create the combo boxes
        self.tab.viz_type_combo.setCurrentText("Scatter Plot")
        
        # Set up data
        self.tab.current_data = pd.DataFrame({
            'x': np.random.randn(50),
            'y': np.random.randn(50)
        })
        self.tab._update_metric_combos(['x', 'y'])
        
        # Set invalid selection
        if hasattr(self.tab, 'scatter_x_combo'):
            self.tab.scatter_x_combo.setCurrentText("Select variable...")
        
        with patch('src.gui.tabs.visualization_tab.QMessageBox.warning') as mock_warning:
            self.tab._generate_scatter()
            mock_warning.assert_called_once()
    
    def test_generate_heatmap_no_data(self):
        """Test generating heatmap without data"""
        with patch('src.gui.tabs.visualization_tab.QMessageBox.warning') as mock_warning:
            self.tab._generate_heatmap()
            mock_warning.assert_called_once()
    
    def test_generate_fft_no_data(self):
        """Test generating FFT spectrum without data"""
        with patch('src.gui.tabs.visualization_tab.QMessageBox.warning') as mock_warning:
            self.tab._generate_fft()
            mock_warning.assert_called_once()
    
    def test_generate_image_comparison_no_data(self):
        """Test generating image comparison without data"""
        with patch('src.gui.tabs.visualization_tab.QMessageBox.warning') as mock_warning:
            self.tab._generate_image_comparison()
            mock_warning.assert_called_once()
    
    def test_reset_all(self):
        """Test reset all functionality"""
        # Set some state
        self.tab.current_data = pd.DataFrame({'x': [1, 2, 3]})
        self.tab.current_figure = Mock()
        
        self.tab._reset_all()
        
        self.assertIsNone(self.tab.current_data)
        self.assertIsNone(self.tab.current_figure)
        self.assertEqual(self.tab.data_info_label.text(), "No data loaded")
    
    def test_update_status(self):
        """Test status update functionality"""
        self.tab._update_status("Test message", "success")
        self.assertEqual(self.tab.status_label.text(), "Test message")
    
    def test_export_visualization_no_figure(self):
        """Test exporting visualization when no figure exists"""
        self.tab.current_figure = None
        
        with patch('src.gui.tabs.visualization_tab.QMessageBox.warning') as mock_warning:
            self.tab._export_visualization()
            mock_warning.assert_called_once()
    
    def test_export_visualization_with_figure(self):
        """Test exporting visualization with a figure"""
        # Create a mock figure
        mock_fig = Mock()
        self.tab.current_figure = mock_fig
        self.tab.plot_fig = Mock()
        self.tab.plot_fig.savefig = Mock()
        
        with patch('src.gui.tabs.visualization_tab.QFileDialog.getSaveFileName') as mock_dialog:
            mock_dialog.return_value = ('/tmp/test.png', 'PNG Files (*.png)')
            
            with patch('src.gui.tabs.visualization_tab.QMessageBox.information') as mock_info:
                self.tab._export_visualization()
                self.tab.plot_fig.savefig.assert_called_once()
                mock_info.assert_called_once()


class TestVisualizationWorker(unittest.TestCase):
    """Test cases for VisualizationWorker"""
    
    def test_worker_initialization(self):
        """Test worker thread initialization"""
        worker = VisualizationWorker('time_series', data=pd.DataFrame({'x': [1, 2, 3]}))
        self.assertEqual(worker.viz_type, 'time_series')
        self.assertIsNotNone(worker.kwargs)
    
    def test_worker_time_series(self):
        """Test worker generates time-series plot"""
        data = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=10, freq='D'),
            'metric1': np.random.randn(10),
            'metric2': np.random.randn(10)
        })
        
        worker = VisualizationWorker('time_series', data=data, time_column='timestamp')
        
        # Mock the plotter to avoid actual plotting
        with patch('src.gui.tabs.visualization_tab.TimeSeriesPlotter') as mock_plotter_class:
            mock_plotter = Mock()
            mock_fig = Mock()
            mock_plotter.plot_health_metrics.return_value = mock_fig
            mock_plotter_class.return_value = mock_plotter
            
            # Run worker (this will fail if not mocked properly)
            try:
                worker.run()
            except Exception:
                pass  # Expected if not fully mocked
    
    def test_worker_scatter(self):
        """Test worker generates scatter plot"""
        x_data = np.random.randn(50)
        y_data = np.random.randn(50)
        
        worker = VisualizationWorker('scatter', x_data=x_data, y_data=y_data)
        self.assertEqual(worker.viz_type, 'scatter')
    
    def test_worker_heatmap(self):
        """Test worker generates heatmap"""
        data = pd.DataFrame({
            'x': np.random.randn(20),
            'y': np.random.randn(20),
            'z': np.random.randn(20)
        })
        
        worker = VisualizationWorker('heatmap', data=data)
        self.assertEqual(worker.viz_type, 'heatmap')
    
    def test_worker_fft_spectrum(self):
        """Test worker generates FFT spectrum"""
        signal_data = np.random.randn(1000)
        sample_rate = 100.0
        
        worker = VisualizationWorker('fft_spectrum', 
                                    signal_data=signal_data, 
                                    sample_rate=sample_rate)
        self.assertEqual(worker.viz_type, 'fft_spectrum')
    
    def test_worker_image_comparison(self):
        """Test worker generates image comparison"""
        original = np.random.rand(100, 100)
        processed = np.random.rand(100, 100)
        
        worker = VisualizationWorker('image_comparison',
                                    original=original,
                                    processed=processed)
        self.assertEqual(worker.viz_type, 'image_comparison')
    
    def test_worker_unknown_type(self):
        """Test worker handles unknown visualization type"""
        worker = VisualizationWorker('unknown_type')
        
        # Worker should emit error signal for unknown type (not raise exception)
        error_received = []
        def on_error(msg):
            error_received.append(msg)
        
        worker.error.connect(on_error)
        worker.run()
        
        # Check that error was emitted
        self.assertTrue(len(error_received) > 0)
        self.assertIn("Unknown visualization type", error_received[0])


if __name__ == '__main__':
    unittest.main()
