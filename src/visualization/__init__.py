"""
Visualization module for MediAnalyze Pro
Provides comprehensive plotting capabilities for health data, signals, and images
"""

from .time_series import TimeSeriesPlotter
from .scatter import ScatterPlotter
from .heatmap import HeatmapPlotter
from .spectrum_plot import SpectrumPlotter
from .image_viewer import ImageViewer
from .utils import VisualizationUtils

__all__ = [
    'TimeSeriesPlotter',
    'ScatterPlotter',
    'HeatmapPlotter',
    'SpectrumPlotter',
    'ImageViewer',
    'VisualizationUtils'
]

# Set default matplotlib backend (can be overridden)
import matplotlib
try:
    matplotlib.use('Agg')  # Non-interactive backend for testing
except:
    pass  # Backend may already be set
