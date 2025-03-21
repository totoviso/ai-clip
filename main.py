#!/usr/bin/env python3
"""
ClipMaster - Self-hosted video clipping software with YouTube integration

This is the main entry point for the application.
"""
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.frontend.main_window import MainWindow
from PyQt6.QtWidgets import QApplication


def main():
    """Main entry point for the application."""
    # Create the application
    app = QApplication(sys.argv)
    app.setApplicationName("ClipMaster")
    app.setApplicationVersion("1.0.0")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
