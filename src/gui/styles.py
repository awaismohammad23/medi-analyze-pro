"""
Styling definitions for MediAnalyze Pro GUI
Provides professional medical application theme
"""

# Color scheme - Professional medical theme
COLORS = {
    'primary': '#2C3E50',          # Dark blue-gray
    'secondary': '#3498DB',         # Bright blue
    'accent': '#1ABC9C',            # Teal
    'background': '#ECF0F1',        # Light gray
    'surface': '#FFFFFF',           # White
    'text_primary': '#2C3E50',      # Dark text
    'text_secondary': '#7F8C8D',    # Gray text
    'success': '#27AE60',           # Green
    'warning': '#F39C12',           # Orange
    'error': '#E74C3C',             # Red
    'sidebar': '#34495E',           # Dark sidebar
    'sidebar_hover': '#2C3E50',     # Sidebar hover
    'sidebar_selected': '#3498DB',  # Selected item
    'border': '#BDC3C7',            # Light border
}

# Font settings
FONTS = {
    'default': 'Segoe UI, Arial, sans-serif',
    'monospace': 'Consolas, Courier New, monospace',
    'title': 'Segoe UI, Arial, sans-serif',
    'size_default': 10,
    'size_title': 14,
    'size_large': 16,
    'size_small': 9,
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
        border-bottom: 1px solid {COLORS['border']};
        padding: 4px;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: 6px 12px;
        border-radius: 4px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {COLORS['secondary']};
        color: white;
    }}
    
    QMenu {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 4px;
    }}
    
    QMenu::item {{
        padding: 6px 24px 6px 12px;
        border-radius: 3px;
    }}
    
    QMenu::item:selected {{
        background-color: {COLORS['secondary']};
        color: white;
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {COLORS['border']};
        margin: 4px 0px;
    }}
    
    /* Sidebar Navigation */
    QListWidget {{
        background-color: {COLORS['sidebar']};
        color: white;
        border: none;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
        padding: 8px;
        outline: none;
    }}
    
    QListWidget::item {{
        padding: 12px 16px;
        border-radius: 6px;
        margin: 2px 0px;
        background-color: transparent;
    }}
    
    QListWidget::item:hover {{
        background-color: {COLORS['sidebar_hover']};
    }}
    
    QListWidget::item:selected {{
        background-color: {COLORS['sidebar_selected']};
        color: white;
    }}
    
    /* Tabs */
    QTabWidget::pane {{
        border: 1px solid {COLORS['border']};
        background-color: {COLORS['surface']};
        border-radius: 4px;
    }}
    
    QTabBar::tab {{
        background-color: {COLORS['background']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 8px 20px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
    }}
    
    QTabBar::tab:selected {{
        background-color: {COLORS['surface']};
        color: {COLORS['secondary']};
        border-bottom: 2px solid {COLORS['secondary']};
    }}
    
    QTabBar::tab:hover {{
        background-color: {COLORS['background']};
    }}
    
    /* Buttons */
    QPushButton {{
        background-color: {COLORS['secondary']};
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: #2980B9;
    }}
    
    QPushButton:pressed {{
        background-color: #21618C;
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS['border']};
        color: {COLORS['text_secondary']};
    }}
    
    /* Status Bar */
    QStatusBar {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border-top: 1px solid {COLORS['border']};
        padding: 4px;
        font-size: {FONTS['size_small']}pt;
        font-family: '{FONTS['default']}';
    }}
    
    /* Labels */
    QLabel {{
        color: {COLORS['text_primary']};
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
    }}
    
    /* Line Edit */
    QLineEdit {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 6px;
        border-radius: 4px;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
    }}
    
    QLineEdit:focus {{
        border: 2px solid {COLORS['secondary']};
    }}
    
    /* Text Edit */
    QTextEdit {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        font-size: {FONTS['size_default']}pt;
        font-family: '{FONTS['default']}';
    }}
    
    /* Scroll Bar */
    QScrollBar:vertical {{
        background-color: {COLORS['background']};
        width: 12px;
        border: none;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {COLORS['border']};
        min-height: 20px;
        border-radius: 6px;
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
        width: 2px;
    }}
    
    QSplitter::handle:vertical {{
        height: 2px;
    }}
    """
