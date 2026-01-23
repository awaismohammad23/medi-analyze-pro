"""
Unit tests for visualization modules
Tests all plotting functionality
"""

import pytest
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set matplotlib backend before importing
import matplotlib
matplotlib.use('Agg')

from src.visualization.time_series import TimeSeriesPlotter
from src.visualization.scatter import ScatterPlotter
from src.visualization.heatmap import HeatmapPlotter
from src.visualization.spectrum_plot import SpectrumPlotter
from src.visualization.image_viewer import ImageViewer
from src.visualization.utils import VisualizationUtils


@pytest.fixture
def sample_time_series_data():
    """Create sample time-series data"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    return pd.DataFrame({
        'timestamp': dates,
        'heart_rate': np.random.randint(60, 100, 100),
        'blood_pressure': np.random.randint(110, 140, 100),
        'temperature': np.random.uniform(36.5, 37.5, 100)
    })


@pytest.fixture
def sample_signal():
    """Create sample signal for FFT testing"""
    sample_rate = 1000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    signal_data = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 120 * t)
    return signal_data, sample_rate


@pytest.fixture
def sample_image():
    """Create sample image"""
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)


class TestTimeSeriesPlotter:
    """Test time-series plotting"""
    
    def test_plot_health_metrics_dataframe(self, sample_time_series_data):
        """Test plotting from DataFrame"""
        plotter = TimeSeriesPlotter()
        fig = plotter.plot_health_metrics(
            sample_time_series_data,
            time_column='timestamp',
            show_plot=False
        )
        assert fig is not None
    
    def test_plot_single_metric(self, sample_time_series_data):
        """Test plotting single metric"""
        plotter = TimeSeriesPlotter()
        fig = plotter.plot_single_metric(
            sample_time_series_data['timestamp'],
            sample_time_series_data['heart_rate'].values,
            metric_name='Heart Rate',
            show_plot=False
        )
        assert fig is not None
    
    def test_plot_with_statistics(self, sample_time_series_data):
        """Test plotting with statistics"""
        plotter = TimeSeriesPlotter()
        fig = plotter.plot_with_statistics(
            sample_time_series_data['timestamp'],
            sample_time_series_data['heart_rate'].values,
            metric_name='Heart Rate',
            show_plot=False
        )
        assert fig is not None


class TestScatterPlotter:
    """Test scatter plotting"""
    
    def test_plot_correlation(self):
        """Test correlation scatter plot"""
        plotter = ScatterPlotter()
        x_data = np.random.randn(100)
        y_data = x_data + np.random.randn(100) * 0.5
        fig = plotter.plot_correlation(
            x_data, y_data,
            x_label='Variable X',
            y_label='Variable Y',
            show_plot=False
        )
        assert fig is not None
    
    def test_plot_from_dataframe(self):
        """Test scatter plot from DataFrame"""
        plotter = ScatterPlotter()
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'color': np.random.randint(0, 3, 100)
        })
        fig = plotter.plot_from_dataframe(
            df, 'x', 'y', color_column='color',
            show_plot=False
        )
        assert fig is not None
    
    def test_plot_with_regression(self):
        """Test scatter plot with regression"""
        plotter = ScatterPlotter()
        x_data = np.random.randn(100)
        y_data = 2 * x_data + np.random.randn(100) * 0.5
        fig = plotter.plot_with_regression(
            x_data, y_data,
            regression_type='linear',
            show_plot=False
        )
        assert fig is not None


class TestHeatmapPlotter:
    """Test heatmap plotting"""
    
    def test_plot_correlation_matrix(self):
        """Test correlation matrix heatmap"""
        plotter = HeatmapPlotter()
        data = pd.DataFrame({
            'var1': np.random.randn(100),
            'var2': np.random.randn(100),
            'var3': np.random.randn(100)
        })
        fig = plotter.plot_correlation_matrix(data, show_plot=False)
        assert fig is not None
    
    def test_plot_data_heatmap(self):
        """Test general data heatmap"""
        plotter = HeatmapPlotter()
        data = np.random.rand(10, 10)
        fig = plotter.plot_data_heatmap(data, show_plot=False)
        assert fig is not None


class TestSpectrumPlotter:
    """Test spectrum plotting"""
    
    def test_plot_fft_spectrum(self, sample_signal):
        """Test FFT spectrum plot"""
        plotter = SpectrumPlotter()
        signal_data, sample_rate = sample_signal
        fig = plotter.plot_fft_spectrum(
            signal_data, sample_rate,
            show_plot=False
        )
        assert fig is not None
    
    def test_plot_power_spectrum(self, sample_signal):
        """Test power spectrum plot"""
        plotter = SpectrumPlotter()
        signal_data, sample_rate = sample_signal
        fig = plotter.plot_power_spectrum(
            signal_data, sample_rate,
            method='welch',
            show_plot=False
        )
        assert fig is not None
    
    def test_plot_time_frequency(self, sample_signal):
        """Test time-frequency plot"""
        plotter = SpectrumPlotter()
        signal_data, sample_rate = sample_signal
        fig = plotter.plot_time_frequency(
            signal_data, sample_rate,
            show_plot=False
        )
        assert fig is not None


class TestImageViewer:
    """Test image viewing"""
    
    def test_compare_images(self, sample_image):
        """Test image comparison"""
        viewer = ImageViewer()
        processed = sample_image // 2  # Simple processing
        fig = viewer.compare_images(
            sample_image, processed,
            show_plot=False
        )
        assert fig is not None
    
    def test_display_image(self, sample_image):
        """Test single image display"""
        viewer = ImageViewer()
        fig = viewer.display_image(
            sample_image,
            show_plot=False
        )
        assert fig is not None
    
    def test_display_multiple_images(self, sample_image):
        """Test multiple image display"""
        viewer = ImageViewer()
        images = [sample_image, sample_image // 2, sample_image // 4]
        fig = viewer.display_multiple_images(
            images,
            titles=['Original', 'Processed 1', 'Processed 2'],
            show_plot=False
        )
        assert fig is not None


class TestVisualizationUtils:
    """Test visualization utilities"""
    
    def test_create_color_palette(self):
        """Test color palette creation"""
        colors = VisualizationUtils.create_color_palette(5)
        assert len(colors) == 5
        assert all(isinstance(c, tuple) for c in colors)
    
    def test_format_large_numbers(self):
        """Test number formatting"""
        assert '1.00K' in VisualizationUtils.format_large_numbers(1000)
        assert '1.00M' in VisualizationUtils.format_large_numbers(1000000)
    
    def test_save_figure(self):
        """Test figure saving"""
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        
        import tempfile
        fd, temp_path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        
        try:
            success = VisualizationUtils.save_figure(fig, temp_path.replace('.png', ''), formats=['png'])
            assert success
            assert os.path.exists(f'{temp_path.replace(".png", "")}.png')
        finally:
            if os.path.exists(f'{temp_path.replace(".png", "")}.png'):
                os.remove(f'{temp_path.replace(".png", "")}.png')
            plt.close(fig)
