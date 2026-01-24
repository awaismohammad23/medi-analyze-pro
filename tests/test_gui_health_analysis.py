"""
Unit tests for Health Analysis Tab GUI
"""

import sys
import os
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.gui.tabs.health_analysis_tab import HealthAnalysisTab


# Create QApplication instance for tests
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def health_tab(qapp):
    """Create health analysis tab instance for testing"""
    tab = HealthAnalysisTab()
    yield tab
    tab.close()


class TestHealthAnalysisTab:
    """Test cases for HealthAnalysisTab class"""
    
    def test_tab_initialization(self, health_tab):
        """Test that tab initializes correctly"""
        assert health_tab is not None
        assert hasattr(health_tab, 'load_data_btn')
        assert hasattr(health_tab, 'patient_combo')
        assert hasattr(health_tab, 'metric_combo')
        assert hasattr(health_tab, 'filter_type_combo')
        assert hasattr(health_tab, 'results_tabs')
    
    def test_data_selection_widgets_exist(self, health_tab):
        """Test that data selection widgets exist"""
        assert health_tab.load_data_btn is not None
        assert health_tab.patient_combo is not None
        assert health_tab.metric_combo is not None
    
    def test_filtering_widgets_exist(self, health_tab):
        """Test that filtering widgets exist"""
        assert health_tab.filter_type_combo is not None
        assert health_tab.apply_filter_btn is not None
        assert health_tab.filter_params_widget is not None
    
    def test_correlation_widgets_exist(self, health_tab):
        """Test that correlation widgets exist"""
        assert health_tab.corr_metric1_combo is not None
        assert health_tab.corr_metric2_combo is not None
        assert health_tab.corr_method_combo is not None
        assert health_tab.compute_corr_btn is not None
        assert health_tab.corr_results_text is not None
    
    def test_timeseries_widgets_exist(self, health_tab):
        """Test that time-series widgets exist"""
        assert health_tab.timeseries_viz_combo is not None
        assert health_tab.generate_viz_btn is not None
    
    def test_results_tabs_exist(self, health_tab):
        """Test that results tabs exist"""
        assert health_tab.results_tabs is not None
        assert health_tab.results_tabs.count() == 2  # Statistics and Visualizations
        assert health_tab.stats_table is not None
        assert health_tab.canvas is not None
    
    def test_initial_button_states(self, health_tab):
        """Test initial button states"""
        assert health_tab.load_data_btn.isEnabled()
        assert not health_tab.apply_filter_btn.isEnabled()
        assert not health_tab.compute_corr_btn.isEnabled()
        assert not health_tab.generate_viz_btn.isEnabled()
    
    def test_filter_type_combo_options(self, health_tab):
        """Test filter type combo box options"""
        options = [health_tab.filter_type_combo.itemText(i) 
                  for i in range(health_tab.filter_type_combo.count())]
        expected = ["None", "Moving Average", "Threshold", "Remove Outliers"]
        assert options == expected
    
    def test_correlation_method_options(self, health_tab):
        """Test correlation method combo box options"""
        options = [health_tab.corr_method_combo.itemText(i) 
                  for i in range(health_tab.corr_method_combo.count())]
        expected = ["Pearson", "Spearman"]
        assert options == expected
    
    def test_timeseries_viz_options(self, health_tab):
        """Test time-series visualization options"""
        options = [health_tab.timeseries_viz_combo.itemText(i) 
                  for i in range(health_tab.timeseries_viz_combo.count())]
        expected = ["Time Series Plot", "Trend Analysis", "Anomaly Detection"]
        assert options == expected
    
    def test_reset_button_exists(self, health_tab):
        """Test that reset button exists"""
        assert hasattr(health_tab, 'reset_btn')
        assert health_tab.reset_btn is not None
    
    def test_status_label_exists(self, health_tab):
        """Test that status label exists"""
        assert hasattr(health_tab, 'status_label')
        assert health_tab.status_label is not None
    
    def test_update_status_method(self, health_tab):
        """Test status update method"""
        # Should not raise exception
        health_tab._update_status("Test message", "info")
        health_tab._update_status("Success message", "success")
        health_tab._update_status("Error message", "error")
        health_tab._update_status("Warning message", "warning")
    
    def test_interpret_correlation_method(self, health_tab):
        """Test correlation interpretation method"""
        # Test various correlation values
        result1 = health_tab._interpret_correlation(0.95)
        assert "very strong" in result1.lower()
        
        result2 = health_tab._interpret_correlation(0.6)
        assert "moderate" in result2.lower()
        
        result3 = health_tab._interpret_correlation(-0.2)
        assert "very weak" in result3.lower()
        assert "negative" in result3.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
