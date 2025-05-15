"""
main.py - Entry point for the Hydrophone Viewer application
With updated keyboard shortcuts using 1.0 increments
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox
import pytz
from datetime import datetime, timedelta
import sys
import time
import logging

# Configure logging with more control over verbosity
# Remove old log file if it exists to start fresh
if os.path.exists('error_log.txt'):
    try:
        os.remove('error_log.txt')
    except:
        # If we can't remove it, create a new one with a timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_filename = f'error_log_{timestamp}.txt'
    else:
        log_filename = 'error_log.txt'
else:
    log_filename = 'error_log.txt'

# Configure a more concise logger
logging.basicConfig(
    filename=log_filename,
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
    """Log an exception with a limited traceback for brevity"""
    import traceback
    tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
    # Only include the most relevant parts of the traceback
    if len(tb_lines) > 5:
        tb_text = ''.join([tb_lines[0]] + tb_lines[-4:])
    else:
        tb_text = ''.join(tb_lines)
    logging.error(f"{message}: {str(e)}\n{tb_text}")

# Import state first and ensure it's initialized
import state
# Reset all state variables to ensure clean starting point
state.reset_state()

# Import the rest of the modules after state is initialized
from data_parser import parse_hydrophone_file
from utils import (
    init_debug_log, add_log_entry, update_time_labels_for_timezone,
    update_spectrogram_xaxis
)
from visualization import (
    update_time_zoom, create_audio_timeline_axis, fix_spectrogram
)
from ui_components import (
    create_menu_ui, create_gain_controls, create_nav_controls,
    create_audio_controls, create_log_display, create_file_list,
    create_fft_controls, create_selection_span, create_timezone_button,
    setup_fft_display, setup_navigation_spectrogram, setup_main_spectrogram
)
from event_handlers import setup_event_handlers

def setup_viewer(file_paths_arg):
    """Set up the hydrophone viewer with the specified files"""
    # Explicitly update the global file_paths in state module
    state.file_paths = file_paths_arg.copy()
    
    print(f"Setting up viewer with {len(file_paths_arg)} files")
    
    # Process the hydrophone data files
    state.freqs_global = None
    data_list = []
    idx_offset = 0
    
    last_time = None
    for path in file_paths_arg:
        try:
            print(f"Processing {path}")
            t, f, d, t_objs = parse_hydrophone_file(path)
            
            # Store UTC times globally
            state.time_objects_utc.extend(t_objs)
            
            # Handle gaps
            if last_time and (t_objs[0] - last_time).total_seconds() > 1.5:
                gap_len = int((t_objs[0] - last_time).total_seconds())
                if gap_len > 1:
                    gap_array = np.full((gap_len, d.shape[1]), np.nan)
                    data_list.append(gap_array)
                    # Add None entries for gaps in time_objects_utc
                    state.time_objects_utc.extend([None] * gap_len)
                    state.time_labels_all.extend(["GAP"] * gap_len)
                    idx_offset += gap_len
            
            last_time = t_objs[-1]
            state.time_labels_all.extend(t)
            data_list.append(d)
            state.file_ranges.append((idx_offset, idx_offset + len(d) - 1))
            idx_offset += len(d)
            
            if state.freqs_global is None:
                state.freqs_global = f
            elif state.freqs_global != f:
                raise ValueError("Frequency bins don't match")
        except Exception as e:
            log_exception(e, f"Error processing file {path}")
            print(f"Error processing file {path}: {str(e)}")
            continue
    
    if not data_list:
        print("No valid data loaded")
        messagebox.showerror("Error", "No valid data could be loaded from the selected files")
        return
    
    # Set up the FFT timeline
    if state.time_objects_utc and state.time_objects_utc[0] is not None:
        state.fft_start_time = state.time_objects_utc[0]
        state.fft_time_axis = []
        
        # Build the timeline, assuming 1 second per sample
        current_time = state.fft_start_time
        for i in range(len(state.time_labels_all)):
            if state.time_objects_utc[i] is not None:
                state.fft_time_axis.append(state.time_objects_utc[i])
                current_time = state.time_objects_utc[i]
            else:
                # For gaps, increment time
                current_time += timedelta(seconds=1)
                state.fft_time_axis.append(current_time)
    
    # Stack the data arrays
    state.data_global = np.vstack(data_list)
    
    # Initialize time zoom variables
    state.time_zoom_start = 0
    state.time_zoom_end = len(state.data_global) - 1
    
    print("Creating figure")
    
    try:
        # CREATE FIGURE FIRST - CRITICAL FIX
        state.fig = plt.figure(figsize=(24, 14))
        print("Figure created successfully:", state.fig)
        
        # Position the title below the buttons
        title_text = f'Project: {state.project_name}'
        
        # Position title in a safe area below the buttons (buttons are at y=0.97)
        title_x = 0.5  # Centered horizontally
        title_y = 0.945  # Below the buttons with sufficient spacing
        
        # Create title with slightly smaller font to avoid overlaps
        title = state.fig.text(title_x, title_y, title_text, fontsize=12, weight='bold', 
                             ha='center', va='center',
                             color='black')
        
        # Version label
        state.fig.text(0.99, 0.005, 'v2.3.2', fontsize=8, color='gray', ha='right', va='bottom')
        
        # Adjust margins to better accommodate title and buttons
        state.fig.subplots_adjust(top=0.92, bottom=0.11)  # Even more space to keep title separate from plots
        
        # Main plot areas - Create all axes BEFORE calling any UI functions
        state.ax_fft = state.fig.add_axes([0.1, 0.78, 0.7, 0.16])
        print("Created ax_fft:", state.ax_fft)
        
        state.ax_nav_spec = state.fig.add_axes([0.1, 0.67, 0.7, 0.08])
        print("Created ax_nav_spec:", state.ax_nav_spec)
        
        state.ax_spec = state.fig.add_axes([0.1, 0.24, 0.7, 0.40])
        print("Created ax_spec:", state.ax_spec)
        
        # Now that the figure and main axes are created, set up event handlers
        setup_event_handlers(state.fig)
        
        # Create horizontal file menu button bar
        menu_btn = create_menu_ui()
        
        # Timezone button on right
        timezone_btn = create_timezone_button()
        
        # Create UI components
        create_gain_controls()
        create_nav_controls()
        create_audio_controls()
        create_log_display()
        create_file_list()
        create_fft_controls()
        selection_span = create_selection_span()
        
        # Setup main display areas
        setup_fft_display()
        setup_navigation_spectrogram()
        setup_main_spectrogram()
        
        # Create audio timeline
        audio_timeline = create_audio_timeline_axis()
        
        # Initially show a zoomed view to test the navigation
        initial_zoom_span = min(1000, len(state.data_global) // 4)
        initial_zoom_start = 0
        initial_zoom_end = initial_zoom_span
        add_log_entry(f"Setting initial zoom to {initial_zoom_start}-{initial_zoom_end}")
        
        # Force the initial zoom
        update_time_zoom((initial_zoom_start, initial_zoom_end))
        
        # Run the spectrogram fix function to ensure correct display
        fix_spectrogram()
        
        # Create a Reset button manually
        state.ax_reset = state.fig.add_axes([0.02, 0.21, 0.07, 0.03])
        state.btn_reset = plt.Button(state.ax_reset, 'Reset', color='0.85')
        state.btn_reset.on_clicked(lambda event: fix_spectrogram())
        
        # Apply state variable button fix
        try:
            from state_buttons_fix import apply_state_button_fix
            apply_state_button_fix()
        except Exception as e:
            add_log_entry(f"Could not apply state button fix: {str(e)}")
        
        # Add keyboard shortcuts for file controls only
        def on_key_press(event):
            """Handle keyboard shortcuts for file controls"""
            try:
                # File list scrolling
                if event.key == '5':  # Scroll file list up
                    from event_handlers import display_file_list
                    state.file_scroll_position = max(0, state.file_scroll_position - 1)
                    display_file_list()
                    add_log_entry(f"File list scrolled up to {state.file_scroll_position} [5 key]")
                    
                elif event.key == '6':  # Scroll file list down
                    from event_handlers import display_file_list
                    max_position = max(0, len(state.file_paths) - state.visible_files)
                    state.file_scroll_position = min(max_position, state.file_scroll_position + 1)
                    display_file_list()
                    add_log_entry(f"File list scrolled down to {state.file_scroll_position} [6 key]")
                    
            except Exception as e:
                add_log_entry(f"Error handling keyboard shortcut: {str(e)}")
        
        # Add keyboard handler for shortcuts
        state.fig.canvas.mpl_connect('key_press_event', on_key_press)
        
        # Add instruction text for shortcuts
        state.fig.text(0.01, 0.01, 
                      "Keyboard shortcuts: 5=Files↑, 6=Files↓", 
                      fontsize=8, color='darkred', ha='left', va='bottom')
        
        print("Showing figure")
        plt.show()
        
    except Exception as e:
        log_exception(e, "Error during UI setup")
        print(f"Error during UI setup: {str(e)}")
        raise
    
    return state.fig

# Main execution
if __name__ == '__main__':
    try:
        print("Starting Hydrophone Viewer")
        root = tk.Tk()
        root.withdraw()  # Hide the main tkinter window
        
        # Initialize debug logging
        init_debug_log()
        
        print("Opening file dialog")
        file_paths = filedialog.askopenfilenames(
            title="Select Hydrophone Data Files",
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
        )
        
        if file_paths:
            print(f"Selected {len(file_paths)} files")
            setup_viewer(list(file_paths))
        else:
            print("No files selected")
            sys.exit()
            
    except Exception as e:
        log_exception(e, "An error occurred while launching the viewer")
        print(f"An error occurred: {str(e)}")
        print(f"Please check {log_filename} for details.")
        messagebox.showerror("Error", f"An error occurred: {str(e)}")