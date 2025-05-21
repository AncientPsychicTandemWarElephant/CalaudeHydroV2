#!/usr/bin/env python3
"""
main.py - Hydrophone Analyzer Application Entry Point

This module serves as the main entry point for the Hydrophone Analyzer application.
It handles initial setup, dependency checking, file loading, and UI initialization.
The application provides a comprehensive interface for analyzing hydrophone data
with features for visualization, annotation, and data export.
"""

import os
import sys
import time
import logging
import traceback
from datetime import datetime, timedelta

# Application constants
VERSION = "2.3.4"
LOG_FILENAME = 'error_log.txt'
DEFAULT_ZOOM_SPAN = 1000

# ===== Configure Logging First =====
# Set up logging before importing other modules to capture all messages
if os.path.exists(LOG_FILENAME):
    try:
        os.remove(LOG_FILENAME)
    except:
        # If we can't remove it, create a new one with a timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        LOG_FILENAME = f'error_log_{timestamp}.txt'

# Configure a concise logger
logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.ERROR,  # Only log errors and critical issues
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Add console handler to see errors in console too
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# Function to log exceptions with limited traceback
def log_exception(e, message="An error occurred"):
    """
    Log an exception with a limited traceback for better readability
    
    Args:
        e: The exception object to log
        message: A descriptive message about the context of the error
        
    This function creates a concise error log by trimming the traceback
    to include only the most relevant parts, making error diagnosis more
    efficient while maintaining necessary context.
    """
    tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
    # Only include the most relevant parts of the traceback
    if len(tb_lines) > 5:
        tb_text = ''.join([tb_lines[0]] + tb_lines[-4:])
    else:
        tb_text = ''.join(tb_lines)
    logging.error(f"{message}: {str(e)}\n{tb_text}")

# ===== Install Required Packages =====
try:
    # Import external dependencies
    import numpy as np
    import matplotlib.pyplot as plt
    import tkinter as tk
    from tkinter import filedialog, messagebox
    import pytz
except ImportError as e:
    log_exception(e, "Error importing core modules")
    print(f"Error importing core modules: {str(e)}")
    print("Please ensure all required packages are installed:")
    print("pip install numpy matplotlib pytz tkinter")
    sys.exit(1)

# Try to import tzlocal, install if not available
try:
    import tzlocal
except ImportError:
    try:
        import subprocess
        print("Installing tzlocal package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tzlocal"])
        import tzlocal
    except Exception as e:
        log_exception(e, "Error installing tzlocal")
        print(f"Error installing tzlocal: {str(e)}")
        print("Please install manually: pip install tzlocal")
        # Continue without tzlocal, will use UTC as fallback

# ===== Initialize State Module ======
try:
    # Import state module first
    import state
    
    # Reset state for a clean start
    state.reset_state()
    
    # Define timezone helper function here to avoid circular imports
    def get_system_timezone():
        """
        Get the system's local timezone with cross-platform compatibility
        
        Returns:
            A pytz timezone object representing the local timezone
            
        This function handles different timezone representations across
        platforms and Python versions, converting them to a consistent
        pytz timezone object for use throughout the application.
        """
        try:
            if 'tzlocal' in sys.modules:
                local_tz = tzlocal.get_localzone()
                # Convert to pytz timezone for compatibility
                if hasattr(local_tz, 'zone'):
                    # It's already a pytz timezone
                    return local_tz
                else:
                    # It's probably a zoneinfo.ZoneInfo object, convert to pytz
                    # Get the key/name of the timezone
                    if hasattr(local_tz, 'key'):
                        zone_name = local_tz.key
                    else:
                        # Fallback to string representation
                        zone_name = str(local_tz).replace('zoneinfo.ZoneInfo(key=', '').rstrip(')')
                        if zone_name.startswith("'") and zone_name.endswith("'"):
                            zone_name = zone_name[1:-1]
                    return pytz.timezone(zone_name)
            # Fallback if tzlocal is not available
            return pytz.UTC
        except Exception as e:
            logging.error(f"Error getting system timezone: {str(e)}")
            return pytz.UTC
            
    # Initialize timezone settings early - safely set defaults
    state.detected_file_timezone = pytz.UTC
    state.detected_file_timezone_source = "Default (UTC)"

    try:
        # Get system timezone if possible
        state.system_timezone = get_system_timezone()
    except Exception as e:
        logging.error(f"Error getting system timezone: {str(e)}")
        # Fallback to UTC
        state.system_timezone = pytz.UTC

    # Ensure use_local_timezone is initialized
    if not hasattr(state, 'use_local_timezone'):
        state.use_local_timezone = True
        
    # Initialize timezone selection system
    if not hasattr(state, 'timezone_selection'):
        state.timezone_selection = 'local' if state.use_local_timezone else 'file'
    
    # Initialize user timezone if needed
    if not hasattr(state, 'user_selected_timezone'):
        state.user_selected_timezone = None

    # Set current timezone based on user preference
    if state.timezone_selection == 'local':
        state.current_timezone = state.system_timezone
        state.use_local_timezone = True
    elif state.timezone_selection == 'user' and state.user_selected_timezone:
        state.current_timezone = state.user_selected_timezone
        state.use_local_timezone = False
    else:  # file
        state.current_timezone = state.detected_file_timezone
        state.use_local_timezone = False
except Exception as e:
    log_exception(e, "Error initializing state module")
    print(f"Error initializing application state: {str(e)}")
    sys.exit(1)

# ===== Import Remaining Modules =====
try:
    # Now import the remaining modules after state is initialized
    from utils import (
        add_log_entry, update_time_labels_for_timezone,
        update_spectrogram_xaxis, init_debug_log
    )
    from data_parser import parse_hydrophone_file
    from visualization import (
        update_time_zoom, create_audio_timeline_axis, fix_spectrogram, 
        update_comment_markers, display_selected_comment
    )
    from ui_components import (
        create_menu_ui, create_gain_controls, create_nav_controls,
        create_audio_controls, create_log_display, create_file_list,
        create_fft_controls, create_selection_span, create_timezone_button,
        setup_fft_display, setup_navigation_spectrogram, setup_main_spectrogram
    )
    from event_handlers import setup_event_handlers
except Exception as e:
    log_exception(e, "Error importing application modules")
    print(f"Error importing application modules: {str(e)}")
    sys.exit(1)

def setup_viewer(file_paths):
    """
    Initialize and configure the main application interface
    
    Args:
        file_paths: List of paths to hydrophone data files to load
        
    This function performs the core application setup:
    - Configures the matplotlib figure and axes
    - Loads and processes hydrophone data files
    - Sets up UI components and controls
    - Initializes visualization elements
    - Prepares comment and annotation systems
    """
    try:
        print(f"Setting up viewer with {len(file_paths)} files")
        
        # Reset state to ensure clean start
        state.reset_state()
        
        # Set file paths in state
        state.file_paths = file_paths.copy() if file_paths else []
        
        # Add matplotlib optimizations for better performance
        plt.rcParams['axes.autolimit_mode'] = 'round_numbers'
        plt.rcParams['path.simplify'] = True
        plt.rcParams['path.simplify_threshold'] = 0.5
        plt.rcParams['agg.path.chunksize'] = 10000
        plt.rcParams['path.snap'] = False  # Disable pixel snapping for smoother rendering
        plt.rcParams['figure.max_open_warning'] = 0  # Disable figure warnings
        
        # Additional performance settings for text rendering
        plt.rcParams['text.usetex'] = False  # Disable LaTeX rendering
        plt.rcParams['text.antialiased'] = True  # Keep antialiasing for quality
        plt.rcParams['mathtext.default'] = 'regular'  # Use simpler math text rendering
        
        # Create main figure with appropriate size
        fig = plt.figure(figsize=(12, 10))
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.4, wspace=0.4)
        
        # Store figure reference in state
        state.fig = fig
        
        # Set up main plot areas - Create all axes BEFORE calling any UI functions
        print("Creating main axes")
        state.ax_fft = fig.add_axes([0.1, 0.78, 0.7, 0.16])
        state.ax_nav_spec = fig.add_axes([0.1, 0.67, 0.7, 0.08])
        # Reduce spectrogram height slightly to make room for comment timeline
        state.ax_spec = fig.add_axes([0.1, 0.27, 0.7, 0.37], frameon=True)
        state.ax_spec.spines['bottom'].set_visible(False)  # Hide bottom spine to reduce gap
        state.ax_spec.tick_params(axis='x', colors='lightgray', labelbottom=False, length=0, pad=0)
        state.ax_spec.tick_params(axis='y', which='both', pad=0)
        
        print("Initializing event handlers")
        # Setup event handlers once axes are created
        setup_event_handlers(fig)
        
        # Initialize debug log
        init_debug_log()
        
        print("Parsing hydrophone files")
        # Process the hydrophone data files
        state.time_objects_utc = []
        state.time_labels_all = []
        data_list = []
        all_comments_data = []  # Accumulate comments from all files
        idx_offset = 0
        
        last_time = None
        for path in file_paths:
            try:
                print(f"Processing {path}")
                time_labels, freqs, data, time_objects, metadata, comments_data = parse_hydrophone_file(path)
                
                # Store UTC times globally
                state.time_objects_utc.extend(time_objects)
                
                # Handle gaps
                if last_time and (time_objects[0] - last_time).total_seconds() > 1.5:
                    gap_len = int((time_objects[0] - last_time).total_seconds())
                    if gap_len > 1:
                        gap_array = np.full((gap_len, data.shape[1]), np.nan)
                        data_list.append(gap_array)
                        # Add None entries for gaps in time_objects_utc
                        state.time_objects_utc.extend([None] * gap_len)
                        state.time_labels_all.extend(["GAP"] * gap_len)
                        # Add None entries for gaps in comments
                        all_comments_data.extend([None] * gap_len)
                        idx_offset += gap_len
                
                last_time = time_objects[-1]
                state.time_labels_all.extend(time_labels)
                all_comments_data.extend(comments_data)  # Accumulate comments
                data_list.append(data)
                state.file_ranges.append((idx_offset, idx_offset + len(data) - 1))
                idx_offset += len(data)
                
                if state.freqs_global is None:
                    state.freqs_global = freqs
                elif len(state.freqs_global) != len(freqs):
                    raise ValueError(f"Frequency bins don't match: {len(state.freqs_global)} != {len(freqs)}")
                    
            except Exception as e:
                log_exception(e, f"Error processing file {path}")
                messagebox.showwarning("File Error", f"Failed to parse file: {os.path.basename(path)}\n\n{str(e)}")
                continue
        
        if not data_list:
            messagebox.showerror("Error", "No valid data could be loaded from the selected files")
            return
        
        # Set up the FFT timeline
        if state.time_objects_utc and state.time_objects_utc[0] is not None:
            state.fft_start_time = state.time_objects_utc[0]
            state.fft_time_axis = []
            
            # Build the timeline, assuming 1 second per sample
            current_time = state.fft_start_time
            for i in range(len(state.time_labels_all)):
                if i < len(state.time_objects_utc) and state.time_objects_utc[i] is not None:
                    state.fft_time_axis.append(state.time_objects_utc[i])
                    current_time = state.time_objects_utc[i]
                else:
                    # For gaps, increment time
                    current_time += timedelta(seconds=1)
                    state.fft_time_axis.append(current_time)
        
        # Stack the data arrays
        state.data_global = np.vstack(data_list)
        
        # Process comments data into comment objects
        state.comments = []
        current_comment_text = None
        comment_start_idx = None
        
        for idx, comment_text in enumerate(all_comments_data):
            if comment_text != current_comment_text:
                # Close previous comment if exists (but not if it's None or empty)
                if current_comment_text and comment_start_idx is not None:
                    state.comments.append({
                        'id': state.comment_id_counter,
                        'start_idx': comment_start_idx,
                        'end_idx': idx - 1,
                        'text': current_comment_text,
                        'user_notes': ''  # Lucy comments don't have extended notes
                    })
                    state.comment_id_counter += 1
                
                # Start new comment if not None or empty
                if comment_text:
                    current_comment_text = comment_text
                    comment_start_idx = idx
                else:
                    current_comment_text = None
                    comment_start_idx = None
        
        # Close final comment if exists
        if current_comment_text and comment_start_idx is not None:
            state.comments.append({
                'id': state.comment_id_counter,
                'start_idx': comment_start_idx,
                'end_idx': len(all_comments_data) - 1,
                'text': current_comment_text,
                'user_notes': ''
            })
            state.comment_id_counter += 1
        
        # Log comment import results
        if state.comments:
            add_log_entry(f"Imported {len(state.comments)} comments from Lucy data")
            for comment in state.comments[:3]:  # Log first few comments
                add_log_entry(f"Comment: '{comment['text']}' spans rows {comment['start_idx']}-{comment['end_idx']}")
        else:
            add_log_entry("No comments found in imported data")
        
        # Initialize time zoom variables
        state.time_zoom_start = 0
        state.time_zoom_end = len(state.data_global) - 1
        
        # Update time labels for selected timezone
        update_time_labels_for_timezone()
        
        print("Setting up UI components")
        # Top header bar with title
        fig.text(0.5, 0.98, f'Project: {state.project_name}', fontsize=16, weight='bold', ha='center')
        
        # Version label
        fig.text(0.99, 0.005, f'v{VERSION}', fontsize=8, color='gray', ha='right', va='bottom')
        fig.subplots_adjust(top=0.96, bottom=0.11)
        
        # Setup UI components - function signatures no longer require fig parameter
        create_menu_ui()
        create_gain_controls()
        create_nav_controls()
        create_audio_controls()
        create_log_display()
        create_file_list()
        create_fft_controls()
        
        # Setup display areas
        setup_fft_display()
        setup_navigation_spectrogram()
        setup_main_spectrogram()
        
        # Create selection span for range selection
        create_selection_span()
        
        # Create timezone control
        create_timezone_button()
        
        # Create fix/reset button
        from ui_components import create_fix_spectrogram_button, create_comment_section
        create_fix_spectrogram_button()
        
        # Create comment section
        create_comment_section()
        
        # Create comment timeline before audio timeline
        from visualization import create_comment_timeline_axis
        create_comment_timeline_axis()
        
        # Create comment list display
        from comment_list import create_comment_list_display
        create_comment_list_display()
        
        # Create audio timeline
        create_audio_timeline_axis()
        
        # Set initial view to a reasonable zoom level
        initial_zoom_span = min(DEFAULT_ZOOM_SPAN, len(state.data_global) // 4)
        initial_zoom_start = 0
        initial_zoom_end = initial_zoom_span
        add_log_entry(f"Setting initial zoom to {initial_zoom_start}-{initial_zoom_end}")
        
        # Force the initial zoom
        update_time_zoom((initial_zoom_start, initial_zoom_end))
        
        # Run the spectrogram fix function to ensure correct display
        fix_spectrogram()
        
        # Display comment markers if there are any comments
        if state.comments:
            # FORCE comments to be visible at startup
            state.comments_visible = True  # Start with comments visible if they exist
            add_log_entry(f"STARTUP: Setting comments_visible=True for {len(state.comments)} comments")
            
            # Update all UI elements consistently
            update_comment_markers()
            
            # Force button to correct state
            if hasattr(state, 'btn_toggle_comments'):
                state.btn_toggle_comments.label.set_text('Hide Comments')
                add_log_entry(f"Set toggle button text to 'Hide Comments'")
            
            # Update the comment list display if it exists
            try:
                from comment_list import update_comment_list_display
                update_comment_list_display()
                add_log_entry(f"Updated comment list with {len(state.comments)} comments")
            except Exception as e:
                add_log_entry(f"Error updating comment list: {str(e)}")
                
            # Force a redraw to ensure comments are visible
            plt.draw()
        
        print("Showing figure")
        # Show the figure
        plt.show()
        
    except Exception as e:
        log_exception(e, "Error setting up viewer")
        messagebox.showerror("Error", f"Error setting up viewer: {str(e)}")
        raise

def main():
    """
    Main entry point for the Hydrophone Analyzer application
    
    This function handles:
    - Initial environment and UI setup
    - Command-line argument processing
    - File selection dialog if no files are specified
    - Application startup and exception handling
    """
    try:
        # Create root window for dialogs but keep it hidden
        print("Starting Hydrophone Viewer application")
        root = tk.Tk()
        root.withdraw()
        
        # Store root in state for later use
        state.tk_root = root
        
        # Only continue if screen is detected
        if not plt.get_backend() or plt.get_backend() == 'Template':
            messagebox.showerror("Error", "Could not initialize display backend. Please check your matplotlib installation.")
            return
        
        # Check command line arguments for file paths
        file_paths = []
        if len(sys.argv) > 1:
            file_paths = [arg for arg in sys.argv[1:] if os.path.exists(arg) and arg.endswith('.txt')]
        
        # If no valid file paths, ask user to select files
        if not file_paths:
            print("No files specified on command line. Opening file selection dialog...")
            file_paths = filedialog.askopenfilenames(
                title="Select Hydrophone Data Files",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
        
        # If files selected, setup viewer
        if file_paths:
            print(f"Selected {len(file_paths)} files")
            setup_viewer(list(file_paths))
        else:
            print("No files selected. Exiting.")
            messagebox.showinfo("Info", "No files selected. Exiting.")
            
    except Exception as e:
        log_exception(e, "Error in main")
        print(f"An error occurred during startup: {str(e)}")
        print(f"See {LOG_FILENAME} for details.")
        messagebox.showerror("Startup Error", f"An error occurred during startup: {str(e)}")
    
    # Ensure root is destroyed
    try:
        root.destroy()
    except:
        pass

if __name__ == "__main__":
    main()