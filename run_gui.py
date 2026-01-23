#!/usr/bin/env python3
"""
Launcher script for MediAnalyze Pro GUI
Run this script to start the application
"""

import sys
import os

# Add src directory to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.gui.app import main

if __name__ == "__main__":
    main()
