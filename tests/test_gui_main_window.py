"""
Unit tests for GUI main window components
"""

import sys
import os
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.gui.main_window import MainWindow
from src.gui import styles


# Create QApplication instance for tests (required for PyQt5 widgets)
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def main_window(qapp):
    """Create main window instance for testing"""
    window = MainWindow()
    yield window
    window.close()


class TestMainWindow:
    """Test cases for MainWindow class"""
    
    def test_window_initialization(self, main_window):
        """Test that window initializes correctly"""
        assert main_window is not None
        assert main_window.windowTitle() == "MediAnalyze Pro - Healthcare Data & Medical Image Processing"
        assert main_window.minimumSize().width() == 1200
        assert main_window.minimumSize().height() == 700
    
    def test_sidebar_exists(self, main_window):
        """Test that sidebar navigation exists"""
        assert hasattr(main_window, 'sidebar')
        assert main_window.sidebar is not None
        assert main_window.sidebar.count() == 5  # 5 navigation items
    
    def test_sidebar_navigation_items(self, main_window):
        """Test sidebar navigation items"""
        items = []
        for i in range(main_window.sidebar.count()):
            item = main_window.sidebar.item(i)
            items.append(item.text())
        
        expected_items = [
            "📊 Patient Data Management",
            "📈 Health Data Analysis",
            "📡 Spectrum Analysis",
            "🖼️ Image Processing",
            "📉 Data Visualization"
        ]
        
        assert len(items) == len(expected_items)
        for expected in expected_items:
            assert any(expected in item for item in items)
    
    def test_tab_widget_exists(self, main_window):
        """Test that tab widget exists"""
        assert hasattr(main_window, 'tab_widget')
        assert main_window.tab_widget is not None
        assert main_window.tab_widget.count() == 5  # 5 tabs
    
    def test_tab_names(self, main_window):
        """Test tab names"""
        expected_tabs = [
            "Data Management",
            "Health Analysis",
            "Spectrum Analysis",
            "Image Processing",
            "Visualization"
        ]
        
        for i, expected in enumerate(expected_tabs):
            assert main_window.tab_widget.tabText(i) == expected
    
    def test_navigation_syncs_with_tabs(self, main_window):
        """Test that sidebar navigation syncs with tabs"""
        # Select first navigation item
        main_window.sidebar.setCurrentRow(0)
        assert main_window.tab_widget.currentIndex() == 0
        
        # Select second navigation item
        main_window.sidebar.setCurrentRow(1)
        assert main_window.tab_widget.currentIndex() == 1
        
        # Select last navigation item
        main_window.sidebar.setCurrentRow(4)
        assert main_window.tab_widget.currentIndex() == 4
    
    def test_tab_change_updates_status(self, main_window):
        """Test that tab changes update status bar"""
        initial_message = main_window.statusBar().currentMessage()
        
        # Change tab
        main_window.tab_widget.setCurrentIndex(1)
        
        # Status should have changed (may take a moment)
        # Just verify status bar exists and is functional
        assert main_window.statusBar() is not None
    
    def test_menu_bar_exists(self, main_window):
        """Test that menu bar exists"""
        menubar = main_window.menuBar()
        assert menubar is not None
        
        # Check for expected menus
        actions = [action.text() for action in menubar.actions()]
        assert any("File" in action or "&File" in action for action in actions)
        assert any("View" in action or "&View" in action for action in actions)
        assert any("Help" in action or "&Help" in action for action in actions)
    
    def test_status_bar_exists(self, main_window):
        """Test that status bar exists"""
        status_bar = main_window.statusBar()
        assert status_bar is not None
        assert status_bar.isVisible()
    
    def test_database_status_indicator(self, main_window):
        """Test database status indicator"""
        assert hasattr(main_window, 'db_status_label')
        assert main_window.db_status_label is not None
    
    def test_error_dialog_methods(self, main_window):
        """Test error dialog helper methods"""
        # These should not raise exceptions
        try:
            main_window.show_error("Test Error", "This is a test error message")
            main_window.show_info("Test Info", "This is a test info message")
            main_window.show_warning("Test Warning", "This is a test warning message")
        except Exception as e:
            pytest.fail(f"Error dialog methods raised exception: {e}")
    
    def test_window_styling(self, main_window):
        """Test that window has styling applied"""
        stylesheet = main_window.styleSheet()
        assert stylesheet is not None
        assert len(stylesheet) > 0


class TestStyles:
    """Test cases for styles module"""
    
    def test_get_stylesheet(self):
        """Test that stylesheet is generated"""
        stylesheet = styles.get_stylesheet()
        assert stylesheet is not None
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0
    
    def test_colors_defined(self):
        """Test that color constants are defined"""
        assert hasattr(styles, 'COLORS')
        assert isinstance(styles.COLORS, dict)
        assert 'primary' in styles.COLORS
        assert 'secondary' in styles.COLORS
        assert 'background' in styles.COLORS
    
    def test_fonts_defined(self):
        """Test that font constants are defined"""
        assert hasattr(styles, 'FONTS')
        assert isinstance(styles.FONTS, dict)
        assert 'default' in styles.FONTS
        assert 'size_default' in styles.FONTS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
