#!/usr/bin/env python3
"""
FoldX Genetic Analyzer & Visualizer

Main application entry point.

This application automates the analysis of FoldX PSSM output files,
calculating ΔΔG values, identifying ideal mutation candidates, and
generating publication-quality visualizations.

Usage:
    python main.py
"""

import os
import sys
import customtkinter as ctk

from ui.main_window import MainWindow
from utils.logger import get_logger
from utils.config import OUTPUT_EXCELS_DIR, OUTPUT_PLOTS_DIR


def setup_directories():
    """Ensure output directories exist."""
    os.makedirs(OUTPUT_EXCELS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_PLOTS_DIR, exist_ok=True)


def main():
    """Main entry point for the application."""
    # Ensure directories exist
    setup_directories()
    
    logger = get_logger()
    
    # Configure global settings
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create and run application
    try:
        app = MainWindow()
        logger.info("Application started successfully")
        app.mainloop()
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
        
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
