"""
Main window for MediAnalyze Pro GUI
Provides navigation structure and tab system
"""

import sys
import os
from typing import Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTabWidget, QMenuBar, QMenu,
    QStatusBar, QMessageBox, QLabel, QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database import get_db_connection, init_database
from .styles import get_stylesheet, COLORS
from .tabs import DataManagementTab


class MainWindow(QMainWindow):
    """Main application window with navigation and tabs"""
    
    # Signals for future use
    database_connected = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        """Initialize the main window"""
        super().__init__(parent)
        
        # Window properties
        self.setWindowTitle("MediAnalyze Pro - Healthcare Data & Medical Image Processing")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 900)
        
        # Initialize database connection
        self.db_connection = None
        self._init_database()
        
        # Setup UI
        self._setup_ui()
        self._apply_styles()
        
        # Connect signals
        self._connect_signals()
        
        # Update status
        self.statusBar().showMessage("Ready - Application initialized successfully", 5000)
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            self.db_connection = get_db_connection()
            # Ensure tables exist
            self.db_connection.create_tables()
            self.db_status = True
        except Exception as e:
            print(f"Warning: Database initialization failed: {e}")
            self.db_status = False
    
    def _setup_ui(self):
        """Setup the user interface"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for sidebar and content
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create sidebar
        self._create_sidebar(splitter)
        
        # Create main content area
        self._create_content_area(splitter)
        
        # Set splitter proportions (sidebar: 20%, content: 80%)
        splitter.setSizes([280, 1120])
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_sidebar(self, parent):
        """Create left sidebar navigation"""
        sidebar = QListWidget()
        sidebar.setMaximumWidth(300)
        sidebar.setMinimumWidth(250)
        
        # Navigation items
        nav_items = [
            ("📊 Patient Data Management", 0),
            ("📈 Health Data Analysis", 1),
            ("📡 Spectrum Analysis", 2),
            ("🖼️ Image Processing", 3),
            ("📉 Data Visualization", 4),
        ]
        
        for text, index in nav_items:
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, index)
            sidebar.addItem(item)
        
        # Set first item as selected
        sidebar.setCurrentRow(0)
        
        self.sidebar = sidebar
        parent.addWidget(sidebar)
    
    def _create_content_area(self, parent):
        """Create main content area with tabs"""
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        
        # Create placeholder tabs (will be replaced in Phases 9-13)
        self._create_placeholder_tabs()
        
        parent.addWidget(self.tab_widget)
    
    def _create_placeholder_tabs(self):
        """Create placeholder tabs for each module"""
        # Tab 1: Patient Data Management (Phase 9 - Real Implementation)
        tab1 = DataManagementTab()
        self.tab_widget.addTab(tab1, "Data Management")
        
        # Tab 2: Health Data Analysis
        tab2 = self._create_placeholder_tab(
            "Health Data Analysis",
            "This tab will allow you to:\n"
            "• Apply filters to health metrics\n"
            "• Perform correlation analysis\n"
            "• Analyze time-series data\n"
            "• Visualize health trends\n\n"
            "Implementation: Phase 10"
        )
        self.tab_widget.addTab(tab2, "Health Analysis")
        
        # Tab 3: Spectrum Analysis
        tab3 = self._create_placeholder_tab(
            "Spectrum Analysis",
            "This tab will allow you to:\n"
            "• Load ECG/EEG signal files\n"
            "• Perform FFT analysis\n"
            "• View power spectral density\n"
            "• Analyze frequency components\n\n"
            "Implementation: Phase 11"
        )
        self.tab_widget.addTab(tab3, "Spectrum Analysis")
        
        # Tab 4: Image Processing
        tab4 = self._create_placeholder_tab(
            "Medical Image Processing",
            "This tab will allow you to:\n"
            "• Upload medical images (X-ray, MRI, CT)\n"
            "• Apply image processing operations\n"
            "• View before/after comparisons\n"
            "• Extract image metadata\n\n"
            "Implementation: Phase 12"
        )
        self.tab_widget.addTab(tab4, "Image Processing")
        
        # Tab 5: Data Visualization
        tab5 = self._create_placeholder_tab(
            "Data Visualization",
            "This tab will allow you to:\n"
            "• Create time-series plots\n"
            "• Generate scatter plots and heatmaps\n"
            "• Visualize FFT spectra\n"
            "• Compare medical images\n"
            "• Export visualizations\n\n"
            "Implementation: Phase 13"
        )
        self.tab_widget.addTab(tab5, "Visualization")
    
    def _create_placeholder_tab(self, title: str, description: str) -> QWidget:
        """Create a placeholder tab widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['secondary']};")
        layout.addWidget(title_label)
        
        # Description
        desc_text = QTextEdit()
        desc_text.setReadOnly(True)
        desc_text.setPlainText(description)
        desc_text.setStyleSheet(f"background-color: {COLORS['background']}; border: none; padding: 10px;")
        layout.addWidget(desc_text)
        
        # Database status
        db_status_widget = self._create_db_status_widget()
        layout.addWidget(db_status_widget)
        
        # Spacer
        layout.addStretch()
        
        return widget
    
    def _create_db_status_widget(self) -> QWidget:
        """Create database status indicator widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        status_label = QLabel("Database Status:")
        status_label.setStyleSheet(f"font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(status_label)
        
        if self.db_status:
            status_indicator = QLabel("● Connected")
            status_indicator.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
        else:
            status_indicator = QLabel("● Disconnected")
            status_indicator.setStyleSheet(f"color: {COLORS['error']}; font-weight: bold;")
        
        layout.addWidget(status_indicator)
        layout.addStretch()
        
        return widget
    
    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        new_action = file_menu.addAction("&New")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._on_new)
        
        open_action = file_menu.addAction("&Open...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open)
        
        file_menu.addSeparator()
        
        save_action = file_menu.addAction("&Save")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save)
        
        save_as_action = file_menu.addAction("Save &As...")
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._on_save_as)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        
        toolbar_action = view_menu.addAction("&Toolbar")
        toolbar_action.setCheckable(True)
        toolbar_action.setChecked(False)
        toolbar_action.triggered.connect(self._toggle_toolbar)
        
        statusbar_action = view_menu.addAction("&Status Bar")
        statusbar_action.setCheckable(True)
        statusbar_action.setChecked(True)
        statusbar_action.triggered.connect(self._toggle_statusbar)
        
        view_menu.addSeparator()
        
        reset_layout_action = view_menu.addAction("&Reset Layout")
        reset_layout_action.triggered.connect(self._reset_layout)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self._show_about)
        
        docs_action = help_menu.addAction("&Documentation")
        docs_action.triggered.connect(self._show_documentation)
        
        help_menu.addSeparator()
        
        shortcuts_action = help_menu.addAction("&Keyboard Shortcuts")
        shortcuts_action.triggered.connect(self._show_shortcuts)
    
    def _create_status_bar(self):
        """Create status bar"""
        status_bar = self.statusBar()
        status_bar.showMessage("Ready")
        
        # Add permanent widgets
        self.db_status_label = QLabel("DB: ●")
        self.db_status_label.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
        status_bar.addPermanentWidget(self.db_status_label)
    
    def _apply_styles(self):
        """Apply stylesheet to the window"""
        self.setStyleSheet(get_stylesheet())
    
    def _connect_signals(self):
        """Connect signals and slots"""
        # Sidebar navigation
        self.sidebar.currentItemChanged.connect(self._on_navigation_changed)
        
        # Tab changes
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def _on_navigation_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle navigation item selection"""
        if current is None:
            return
        
        tab_index = current.data(Qt.UserRole)
        self.tab_widget.setCurrentIndex(tab_index)
        
        # Update status
        tab_name = self.tab_widget.tabText(tab_index)
        self.statusBar().showMessage(f"Switched to {tab_name}", 2000)
    
    def _on_tab_changed(self, index: int):
        """Handle tab change"""
        # Update sidebar to match selected tab
        for i in range(self.sidebar.count()):
            item = self.sidebar.item(i)
            if item.data(Qt.UserRole) == index:
                self.sidebar.setCurrentRow(i)
                break
        
        tab_name = self.tab_widget.tabText(index)
        self.statusBar().showMessage(f"Viewing: {tab_name}", 2000)
    
    # Menu action handlers
    def _on_new(self):
        """Handle New action"""
        self.statusBar().showMessage("New file action (to be implemented)", 2000)
        QMessageBox.information(self, "New File", "New file functionality will be implemented in future phases.")
    
    def _on_open(self):
        """Handle Open action"""
        self.statusBar().showMessage("Open file action (to be implemented)", 2000)
        QMessageBox.information(self, "Open File", "Open file functionality will be implemented in Phase 9.")
    
    def _on_save(self):
        """Handle Save action"""
        self.statusBar().showMessage("Save action (to be implemented)", 2000)
        QMessageBox.information(self, "Save", "Save functionality will be implemented in future phases.")
    
    def _on_save_as(self):
        """Handle Save As action"""
        self.statusBar().showMessage("Save As action (to be implemented)", 2000)
        QMessageBox.information(self, "Save As", "Save As functionality will be implemented in future phases.")
    
    def _toggle_toolbar(self, checked: bool):
        """Toggle toolbar visibility"""
        # Toolbar not implemented yet
        self.statusBar().showMessage("Toolbar toggle (to be implemented)", 2000)
    
    def _toggle_statusbar(self, checked: bool):
        """Toggle status bar visibility"""
        self.statusBar().setVisible(checked)
    
    def _reset_layout(self):
        """Reset window layout to default"""
        self.resize(1400, 900)
        self.statusBar().showMessage("Layout reset to default", 2000)
    
    def _show_about(self):
        """Show About dialog"""
        QMessageBox.about(
            self,
            "About MediAnalyze Pro",
            "<h2>MediAnalyze Pro</h2>"
            "<p><b>Version:</b> 1.0.0</p>"
            "<p><b>Description:</b> Healthcare Data and Medical Image Processing Tool</p>"
            "<p>Comprehensive application for managing patient data, analyzing health metrics, "
            "processing medical images, and performing spectrum analysis on biomedical signals.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Patient Data Management</li>"
            "<li>Health Data Analysis & Correlation</li>"
            "<li>Biomedical Signal Spectrum Analysis</li>"
            "<li>Medical Image Processing</li>"
            "<li>Interactive Data Visualization</li>"
            "</ul>"
        )
    
    def _show_documentation(self):
        """Show documentation"""
        QMessageBox.information(
            self,
            "Documentation",
            "Documentation is available in the project README.md file.\n\n"
            "For detailed usage instructions, please refer to the project documentation."
        )
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts_text = (
            "<h3>Keyboard Shortcuts</h3>"
            "<table>"
            "<tr><td><b>Ctrl+N</b></td><td>New File</td></tr>"
            "<tr><td><b>Ctrl+O</b></td><td>Open File</td></tr>"
            "<tr><td><b>Ctrl+S</b></td><td>Save</td></tr>"
            "<tr><td><b>Ctrl+Shift+S</b></td><td>Save As</td></tr>"
            "<tr><td><b>Ctrl+Q</b></td><td>Exit Application</td></tr>"
            "</table>"
        )
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts_text)
    
    def show_error(self, title: str, message: str):
        """Show error message dialog"""
        QMessageBox.critical(self, title, message)
        self.statusBar().showMessage(f"Error: {title}", 5000)
    
    def show_info(self, title: str, message: str):
        """Show info message dialog"""
        QMessageBox.information(self, title, message)
        self.statusBar().showMessage(message, 3000)
    
    def show_warning(self, title: str, message: str):
        """Show warning message dialog"""
        QMessageBox.warning(self, title, message)
        self.statusBar().showMessage(f"Warning: {title}", 3000)
    
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self,
            "Exit Application",
            "Are you sure you want to exit MediAnalyze Pro?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Close database connection if needed
            if self.db_connection:
                try:
                    self.db_connection.close()
                except:
                    pass
            event.accept()
        else:
            event.ignore()
