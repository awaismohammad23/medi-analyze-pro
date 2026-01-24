"""
Unit tests for Data Management Tab GUI
"""

import sys
import os
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.gui.tabs.data_management_tab import DataManagementTab, PatientDialog


# Create QApplication instance for tests
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def data_tab(qapp):
    """Create data management tab instance for testing"""
    tab = DataManagementTab()
    yield tab
    tab.close()


@pytest.fixture
def patient_dialog(qapp):
    """Create patient dialog instance for testing"""
    dialog = PatientDialog()
    yield dialog
    dialog.close()


class TestDataManagementTab:
    """Test cases for DataManagementTab class"""
    
    def test_tab_initialization(self, data_tab):
        """Test that tab initializes correctly"""
        assert data_tab is not None
        assert hasattr(data_tab, 'table')
        assert hasattr(data_tab, 'load_csv_btn')
        assert hasattr(data_tab, 'import_btn')
        assert hasattr(data_tab, 'insert_btn')
        assert hasattr(data_tab, 'retrieve_btn')
        assert hasattr(data_tab, 'update_btn')
        assert hasattr(data_tab, 'delete_btn')
    
    def test_file_operations_widgets_exist(self, data_tab):
        """Test that file operation widgets exist"""
        assert data_tab.load_csv_btn is not None
        assert data_tab.import_btn is not None
        assert data_tab.file_path_label is not None
        assert data_tab.progress_bar is not None
    
    def test_database_operations_widgets_exist(self, data_tab):
        """Test that database operation widgets exist"""
        assert data_tab.insert_btn is not None
        assert data_tab.retrieve_btn is not None
        assert data_tab.update_btn is not None
        assert data_tab.delete_btn is not None
        assert data_tab.db_status_label is not None
    
    def test_table_widget_exists(self, data_tab):
        """Test that table widget exists"""
        assert data_tab.table is not None
        assert data_tab.table.rowCount() >= 0
        assert data_tab.table.columnCount() >= 0
    
    def test_initial_button_states(self, data_tab):
        """Test initial button states"""
        # Import button should be disabled until CSV is loaded
        assert not data_tab.import_btn.isEnabled()
        # Update and delete should be disabled until row is selected
        assert not data_tab.update_btn.isEnabled()
        assert not data_tab.delete_btn.isEnabled()
        # Other buttons should be enabled
        assert data_tab.load_csv_btn.isEnabled()
        assert data_tab.insert_btn.isEnabled()
        assert data_tab.retrieve_btn.isEnabled()
    
    def test_status_label_exists(self, data_tab):
        """Test that status label exists"""
        assert hasattr(data_tab, 'status_label')
        assert data_tab.status_label is not None
    
    def test_table_info_label_exists(self, data_tab):
        """Test that table info label exists"""
        assert hasattr(data_tab, 'table_info_label')
        assert data_tab.table_info_label is not None
    
    def test_database_connection(self, data_tab):
        """Test that database connection is established"""
        assert data_tab.db_connection is not None
    
    def test_update_status_method(self, data_tab):
        """Test status update method"""
        # Should not raise exception
        data_tab._update_status("Test message", "info")
        data_tab._update_status("Success message", "success")
        data_tab._update_status("Error message", "error")
        data_tab._update_status("Warning message", "warning")
    
    def test_table_selection_handling(self, data_tab):
        """Test table selection change handling"""
        # Initially, update and delete should be disabled
        assert not data_tab.update_btn.isEnabled()
        assert not data_tab.delete_btn.isEnabled()
        
        # Method should exist and not raise exception
        data_tab._on_table_selection_changed()


class TestPatientDialog:
    """Test cases for PatientDialog class"""
    
    def test_dialog_initialization(self, patient_dialog):
        """Test that dialog initializes correctly"""
        assert patient_dialog is not None
        assert hasattr(patient_dialog, 'name_edit')
        assert hasattr(patient_dialog, 'age_spin')
        assert hasattr(patient_dialog, 'gender_combo')
        assert hasattr(patient_dialog, 'height_spin')
        assert hasattr(patient_dialog, 'weight_spin')
    
    def test_dialog_widgets_exist(self, patient_dialog):
        """Test that all form widgets exist"""
        assert patient_dialog.name_edit is not None
        assert patient_dialog.age_spin is not None
        assert patient_dialog.gender_combo is not None
        assert patient_dialog.height_spin is not None
        assert patient_dialog.weight_spin is not None
    
    def test_dialog_default_values(self, patient_dialog):
        """Test default form values"""
        assert patient_dialog.age_spin.value() > 0
        assert patient_dialog.height_spin.value() > 0
        assert patient_dialog.weight_spin.value() > 0
        assert patient_dialog.gender_combo.count() == 2  # Female, Male
    
    def test_get_data_method(self, patient_dialog):
        """Test get_data method"""
        data = patient_dialog.get_data()
        assert isinstance(data, dict)
        assert 'name' in data
        assert 'age' in data
        assert 'gender' in data
        assert 'height' in data
        assert 'weight' in data
        assert data['age'] > 0
        assert data['height'] > 0
        assert data['weight'] > 0
        assert data['gender'] in [1, 2]  # 1=female, 2=male
    
    def test_dialog_with_patient_data(self, qapp):
        """Test dialog with existing patient data"""
        patient_data = {
            'name': 'Test Patient',
            'age': 10950,
            'gender': 1,
            'height': 170.0,
            'weight': 70.0
        }
        dialog = PatientDialog(patient_data=patient_data)
        
        assert dialog.name_edit.text() == 'Test Patient'
        assert dialog.age_spin.value() == 10950
        assert dialog.gender_combo.currentIndex() == 0  # Female
        assert dialog.height_spin.value() == 170.0
        assert dialog.weight_spin.value() == 70.0
        
        dialog.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
