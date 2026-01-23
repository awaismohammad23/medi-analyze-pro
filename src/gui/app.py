"""
Application entry point for MediAnalyze Pro GUI
Initializes and runs the PyQt5 application
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.gui.main_window import MainWindow


def create_application() -> QApplication:
    """
    Create and configure the QApplication instance
    
    Returns:
        Configured QApplication
    """
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("MediAnalyze Pro")
    app.setOrganizationName("MediAnalyze")
    app.setApplicationVersion("1.0.0")
    
    return app


def main():
    """Main entry point for the GUI application"""
    try:
        # Create application
        app = create_application()
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Run event loop
        sys.exit(app.exec_())
    
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
