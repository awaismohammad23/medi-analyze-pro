"""
GUI tabs module for MediAnalyze Pro
Contains individual tab implementations for each module
"""

from .data_management_tab import DataManagementTab
from .health_analysis_tab import HealthAnalysisTab
from .spectrum_analysis_tab import SpectrumAnalysisTab
from .image_processing_tab import ImageProcessingTab

__all__ = ['DataManagementTab', 'HealthAnalysisTab', 'SpectrumAnalysisTab', 'ImageProcessingTab']
