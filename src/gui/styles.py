"""
Styling definitions for MediAnalyze Pro GUI
Provides professional medical application theme - Production Level
"""

# Color scheme - Medical Blue + Soft Gray (Industry Standard)
# Recommended for professional healthcare applications
COLORS = {
    # Primary Colors (Medical Blue - Trust & Healthcare)
    'primary': '#1F4FD8',           # Medical Blue - primary buttons, headers
    'primary_dark': '#1741B5',      # Darker blue - hover states
    'primary_light': '#E8F0FE',    # Light Blue - sidebar, highlights
    
    # Secondary Colors
    'secondary': '#E8F0FE',         # Light Blue - secondary elements
    'accent': '#06B6D4',            # Cyan - accents
    
    # Neutral Colors (Clean & Clinical)
    'background': '#F5F7FA',         # Soft Gray - main background
    'surface': '#FFFFFF',            # White - cards, panels
    'border': '#E5E7EB',            # Border gray - subtle separation
    'text_primary': '#2E3440',       # Dark Slate - primary text
    'text_secondary': '#6B7280',    # Muted Gray - secondary text
    
    # Status Colors (Feedback)
    'success': '#2ECC71',           # Green - success states
    'warning': '#F59E0B',           # Amber - warnings
    'error': '#E74C3C',             # Red - errors
    'info': '#1F4FD8',              # Info blue - information
    
    # Sidebar & Navigation
    'sidebar': '#E8F0FE',           # Light Blue - sidebar background
    'sidebar_hover': '#D1E7FF',     # Lighter blue - hover
    'sidebar_selected': '#1F4FD8',  # Medical Blue - selected item
    'sidebar_text': '#2E3440',      # Dark Slate - sidebar text
    
    # Button Colors
    'button_primary': '#1F4FD8',     # Medical Blue - primary buttons
    'button_primary_hover': '#1741B5',  # Darker blue - hover
    'button_primary_pressed': '#0F2E8C', # Pressed state
    'button_secondary': '#E8F0FE',  # Light Blue - secondary buttons
    'button_secondary_text': '#1F4FD8',  # Blue text on secondary
    'button_danger': '#E74C3C',     # Red - destructive actions
    'button_success': '#2ECC71',    # Green - positive actions
    'button_text': '#FFFFFF',       # White text on buttons
}

# Font settings
FONTS = {
    'default': 'Segoe UI, Arial, sans-serif',
    'monospace': 'Consolas, Courier New, monospace',
    'title': 'Segoe UI, Arial, sans-serif',
    'size_default': 11,
    'size_title': 16,
    'size_large': 18,
    'size_small': 10,
}

def get_stylesheet() -> str:
    """
    Get the complete stylesheet for the application
    
    Returns:
        CSS-like stylesheet string
    """
    return f"""
    /* Main Window */
    QMainWindow {{
        background-color: {COLORS['background']};
        color: {COLORS['text_primary']};
    }}
    
    /* Menu Bar */
    QMenuBar {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border-bottom: 2px solid {COLORS['border']};
        padding: 6px;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
        font-weight: 500;
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: 8px 16px;
        border-radius: 6px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {COLORS['primary']};
        color: white;
    }}
    
    QMenu {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 6px;
        border-radius: 6px;
    }}
    
    QMenu::item {{
        padding: 8px 32px 8px 16px;
        border-radius: 4px;
    }}
    
    QMenu::item:selected {{
        background-color: {COLORS['primary']};
        color: white;
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {COLORS['border']};
        margin: 6px 0px;
    }}
    
    /* Sidebar Navigation - Medical Blue Theme */
    QListWidget {{
        background-color: {COLORS['sidebar']};
        color: {COLORS['sidebar_text']};
        border: none;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
        padding: 10px;
        outline: none;
    }}
    
    QListWidget::item {{
        padding: 12px 16px;
        border-radius: 6px;
        margin: 3px 0px;
        background-color: transparent;
        font-weight: 500;
        color: {COLORS['text_primary']};
    }}
    
    QListWidget::item:hover {{
        background-color: {COLORS['sidebar_hover']};
    }}
    
    QListWidget::item:selected {{
        background-color: {COLORS['sidebar_selected']};
        color: {COLORS['button_text']};
        font-weight: 600;
    }}
    
    /* Tabs */
    QTabWidget::pane {{
        border: 1px solid {COLORS['border']};
        background-color: {COLORS['surface']};
        border-radius: 8px;
    }}
    
    QTabBar::tab {{
        background-color: {COLORS['background']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 10px 24px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
        font-weight: 500;
    }}
    
    QTabBar::tab:selected {{
        background-color: {COLORS['surface']};
        color: {COLORS['primary']};
        border-bottom: 3px solid {COLORS['primary']};
        font-weight: 600;
    }}
    
    QTabBar::tab:hover {{
        background-color: {COLORS['surface']};
    }}
    
    /* Buttons - Professional Medical Styling */
    QPushButton {{
        background-color: {COLORS['button_primary']};
        color: {COLORS['button_text']};
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
        font-weight: 500;
        min-height: 38px;
        min-width: 130px;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['button_primary_hover']};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS['button_primary_pressed']};
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS['border']};
        color: {COLORS['text_secondary']};
        opacity: 0.5;
    }}
    
    /* Success Buttons */
    QPushButton#successButton {{
        background-color: {COLORS['button_success']};
        color: {COLORS['button_text']};
    }}
    
    QPushButton#successButton:hover {{
        background-color: #27AE60;
    }}
    
    QPushButton#successButton:pressed {{
        background-color: #229954;
    }}
    
    /* Danger Buttons */
    QPushButton#dangerButton {{
        background-color: {COLORS['button_danger']};
        color: {COLORS['button_text']};
    }}
    
    QPushButton#dangerButton:hover {{
        background-color: #C0392B;
    }}
    
    QPushButton#dangerButton:pressed {{
        background-color: #A93226;
    }}
    
    /* Group Box Styling - Clean Medical Cards */
    QGroupBox {{
        font-weight: 600;
        font-size: {FONTS['size_default']}pt;
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 14px;
        background-color: {COLORS['surface']};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 14px;
        padding: 0 8px;
        background-color: {COLORS['surface']};
        color: {COLORS['primary']};
    }}
    
    /* Status Bar */
    QStatusBar {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border-top: 2px solid {COLORS['border']};
        padding: 6px;
        font-size: {FONTS['size_small']}pt;
        font-family: '{FONTS['default']}';
    }}
    
    /* Labels */
    QLabel {{
        color: {COLORS['text_primary']};
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
    }}
    
    /* Line Edit - Enhanced Interactive Design */
    QLineEdit {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border: 2px solid {COLORS['border']};
        padding: 10px 14px;
        border-radius: 8px;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
        min-height: 22px;
    }}
    
    QLineEdit:hover {{
        border: 2px solid {COLORS['primary_light']};
        background-color: {COLORS['background']};
    }}
    
    QLineEdit:focus {{
        border: 2px solid {COLORS['primary']};
        background-color: {COLORS['surface']};
        outline: none;
    }}
    
    /* SpinBox - Enhanced Interactive Design */
    QSpinBox, QDoubleSpinBox {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border: 2px solid {COLORS['border']};
        padding: 10px 14px;
        border-radius: 8px;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
        min-height: 22px;
    }}
    
    QSpinBox:hover, QDoubleSpinBox:hover {{
        border: 2px solid {COLORS['primary_light']};
        background-color: {COLORS['background']};
    }}
    
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {COLORS['primary']};
        background-color: {COLORS['surface']};
        outline: none;
    }}
    
    QSpinBox::up-button, QDoubleSpinBox::up-button {{
        background-color: {COLORS['primary']};
        border-top-right-radius: 6px;
        width: 24px;
        height: 20px;
    }}
    
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
        background-color: {COLORS['button_primary_hover']};
    }}
    
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 5px solid white;
        width: 0;
        height: 0;
    }}
    
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        background-color: {COLORS['primary']};
        border-bottom-right-radius: 6px;
        width: 24px;
        height: 20px;
    }}
    
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
        background-color: {COLORS['button_primary_hover']};
    }}
    
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid white;
        width: 0;
        height: 0;
    }}
    
    /* ComboBox - Enhanced Interactive Design */
    QComboBox {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border: 2px solid {COLORS['border']};
        padding: 10px 14px;
        border-radius: 8px;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
        min-height: 22px;
    }}
    
    QComboBox:hover {{
        border: 2px solid {COLORS['primary_light']};
        background-color: {COLORS['background']};
    }}
    
    QComboBox:focus {{
        border: 2px solid {COLORS['primary']};
        background-color: {COLORS['surface']};
        outline: none;
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 30px;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
        background-color: {COLORS['primary']};
    }}
    
    QComboBox::drop-down:hover {{
        background-color: {COLORS['button_primary_hover']};
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid white;
        width: 0;
        height: 0;
        margin-right: 8px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {COLORS['surface']};
        border: 2px solid {COLORS['primary']};
        border-radius: 6px;
        selection-background-color: {COLORS['primary']};
        selection-color: white;
        padding: 4px;
    }}
    
    /* Text Edit */
    QTextEdit {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border: 2px solid {COLORS['border']};
        border-radius: 6px;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
        padding: 8px;
    }}
    
    /* Table Widget - Professional Medical Tables */
    QTableWidget {{
        background-color: {COLORS['surface']};
        alternate-background-color: #EEF2FF;
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        gridline-color: {COLORS['border']};
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
    }}
    
    QTableWidget::item {{
        padding: 8px 12px;
        border: none;
    }}
    
    QTableWidget::item:hover {{
        background-color: #EEF2FF;
    }}
    
    QTableWidget::item:selected {{
        background-color: {COLORS['primary']};
        color: {COLORS['button_text']};
    }}
    
    QHeaderView::section {{
        background-color: {COLORS['secondary']};
        color: {COLORS['text_primary']};
        padding: 10px 12px;
        border: 1px solid {COLORS['border']};
        font-weight: 600;
        font-size: {FONTS['size_default']}pt;
    }}
    
    /* Scroll Bar */
    QScrollBar:vertical {{
        background-color: {COLORS['background']};
        width: 14px;
        border: none;
        border-radius: 7px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {COLORS['border']};
        min-height: 30px;
        border-radius: 7px;
        margin: 2px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['text_secondary']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    /* Splitter */
    QSplitter::handle {{
        background-color: {COLORS['border']};
    }}
    
    QSplitter::handle:horizontal {{
        width: 3px;
    }}
    
    QSplitter::handle:vertical {{
        height: 3px;
    }}
    
    /* Progress Bar */
    QProgressBar {{
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        text-align: center;
        background-color: {COLORS['background']};
        color: {COLORS['text_primary']};
        font-weight: 600;
        height: 24px;
    }}
    
    QProgressBar::chunk {{
        background-color: {COLORS['primary']};
        border-radius: 6px;
    }}
    
    /* Message Boxes - Make text visible */
    QMessageBox {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
    }}
    
    QMessageBox QLabel {{
        color: {COLORS['text_primary']};
        font-size: {FONTS['size_default']}pt;
        min-width: 300px;
    }}
    
    QMessageBox QPushButton {{
        background-color: {COLORS['button_primary']};
        color: {COLORS['button_text']};
        border: none;
        padding: 8px 20px;
        border-radius: 4px;
        font-weight: 500;
        min-width: 80px;
    }}
    
    QMessageBox QPushButton:hover {{
        background-color: {COLORS['button_primary_hover']};
    }}
    
    /* Dialog Styling */
    QDialog {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
    }}
    
    QDialog QLabel {{
        color: {COLORS['text_primary']};
        font-weight: 500;
    }}
    
    /* Form Layout Labels */
    QFormLayout QLabel {{
        color: {COLORS['text_primary']};
        font-weight: 500;
        font-size: {FONTS['size_default']}pt;
    }}
    """
