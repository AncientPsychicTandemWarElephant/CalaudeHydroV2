"""
main.py - Main entry point for the hydrophone visualization program
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import logging
import sys
import os
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Button

# Import our modules
import state
from data_parser import parse_hydrophone_data
from utils import setup_logging, add_log_entry, update_log_display, update_time_labels_for_timezone
from event_handlers import on_key_press, setup_event_handlers
from ui_layout import create_modern_layout, initialize_ui, update_ui_for_data

# Set up logging
setup_logging()

def setup_viewer(file_paths):
    """
    Set up the viewer with the specified files.
    
    Args:
        file_paths: List of file paths to load
    """
    # Reset state
    state.reset_state()
    
    # Store file paths
    state.file_paths = file_paths
    
    # Create the main figure
    fig = plt.figure(figsize=(14, 8))
    fig.set_facecolor('#1E1E1E')
    
    # Initialize UI
    initialize_ui(fig)
    
    # Set window title
    if len(file_paths) == 1:
        state.set_window_title(f"Hydrophone Analyzer - {os.path.basename(file_paths[0])}")
    else:
        state.set_window_title(f"Hydrophone Analyzer - {len(file_paths)} files")
    
    # Add initial log entry
    add_log_entry(f"Loading {len(file_paths)} file(s)...")
    
    # Parse input files
    parse_hydrophone_data(file_paths)
    
    # Update UI for loaded data
    update_ui_for_data()
    
    # Update time labels with default timezone
    update_time_labels_for_timezone()
    
    # Show the figure
    plt.show()

def on_key_press_global(event):
    """Global key press handler"""
    if event.key == 'q':
        plt.close('all')
        sys.exit(0)

def main():
    """Main function"""
    # Check if any files were specified
    if len(sys.argv) > 1:
        file_paths = sys.argv[1:]
    else:
        # Use a default for testing
        file_paths = ["example_data.txt"]
    
    # Set up the viewer
    setup_viewer(file_paths)

if __name__ == "__main__":
    # Enable interactive mode for better performance
    plt.ion()
    
    # Register global key press handler
    plt.rcParams['keymap.quit'] = []  # Disable default quit binding
    plt.connect('key_press_event', on_key_press_global)
    
    # Start the application
    main()