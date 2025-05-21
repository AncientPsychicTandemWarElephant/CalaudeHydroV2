"""
event_handlers.py - Functions that handle user interaction events
"""

import matplotlib.pyplot as plt
import numpy as np
import logging
import os
import subprocess
import platform
import socket
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sounddevice as sd
import pytz
import threading
from matplotlib.transforms import blended_transform_factory

# Import state directly
import state

from utils import add_log_entry, update_spectrogram_xaxis, update_time_labels_for_timezone, update_log_display
from visualization import update_time_zoom, update_fft, update_fft_range

# Import from audio_processing as needed
from audio_processing import play_audio, stop_audio

def on_export_data(event):
    """Handle Export Data button click with ultra-simple approach - no threads"""
    add_log_entry("Export Data requested - using ultra-simple export method")
    
    # Show a notification in the log
    state.ax_log.clear()
    state.ax_log.set_title("Log", fontsize=9)
    state.ax_log.axis("off")
    state.ax_log.text(0.5, 0.5, "Starting export...\nPlease select directory", color='green', 
                     ha='center', va='center', fontsize=10, weight='bold',
                     transform=state.ax_log.transAxes)
    
    if hasattr(state, 'fig') and state.fig is not None:
        state.fig.canvas.draw_idle()
        state.fig.canvas.flush_events()
    
    # Import needed modules
    from tkinter import filedialog, messagebox
    import os
    import time
    
    # Get the export directory in the main thread
    export_dir = filedialog.askdirectory(title="Select Export Directory")
    if not export_dir:
        add_log_entry("Export cancelled - no directory selected")
        from utils import update_log_display
        update_log_display()
        return
    
    add_log_entry(f"Export directory selected: {export_dir}")
    
    # Just use standard messagebox for progress indication
    messagebox.showinfo("Export Starting", 
                      "Export is starting.\n\nThis may take some time to complete.\n\n"
                      "You will see a message when export is complete.")
    
    # Force redraw to ensure UI stays responsive
    if hasattr(state, 'fig') and state.fig is not None:
        state.fig.canvas.draw_idle()
        state.fig.canvas.flush_events()
    
    try:
        # Import export function
        from data_export import ExportSplitMethod
        from datetime import datetime
        
        # Create a simplified version of the export that doesn't use complex UI
        try:
            # Get time range for better file naming
            valid_times = [t for t in state.time_objects_utc if t is not None]
            if valid_times:
                start_time = min(valid_times)
                end_time = max(valid_times)
                start_local = start_time.astimezone(state.current_timezone)
                end_local = end_time.astimezone(state.current_timezone)
                date_str = start_local.strftime("%Y%m%d")
                time_str = start_local.strftime("%H%M%S")
            else:
                date_str = datetime.now().strftime("%Y%m%d")
                time_str = datetime.now().strftime("%H%M%S")
            
            # Create a name similar to the Lucy software format
            # Lucy format typically looks like: wavtS_20250423_021234.txt
            file_name = f"wavtS_{date_str}_{time_str}.txt"
            export_file_path = os.path.join(export_dir, file_name)
            
            # Get project name for client field
            project_name = "Hydrophone Analysis"
            if hasattr(state, 'project_name') and state.project_name:
                project_name = state.project_name
            
            # Create the export file with Lucy-style header
            with open(export_file_path, 'w') as f:
                # Add basic header info exactly like Lucy software
                f.write("File Details:\n")
                f.write(f"File Type\tSpectrum\n")
                f.write(f"File Version\t5\n")
                f.write(f"Start Date\t{start_local.strftime('%Y-%m-%d') if valid_times else datetime.now().strftime('%Y-%m-%d')}\n")
                f.write(f"Start Time\t{start_local.strftime('%H:%M:%S') if valid_times else datetime.now().strftime('%H:%M:%S')}\n")
                f.write(f"Time Zone\t{state.current_timezone.zone}\n")
                f.write(f"Author\tOcean Sonics' Lucy V4.4.0\n")  # Emulate Lucy software
                
                # Get computer name in a platform-independent way
                try:
                    computer_name = platform.node()
                    if not computer_name:
                        computer_name = socket.gethostname()
                except:
                    computer_name = "Unknown"
                    
                f.write(f"Computer\t{computer_name}\n")
                f.write(f"User\t{os.getenv('USER', os.getenv('USERNAME', 'UnknownUser'))}\n")
                
                # Add a more meaningful project name that will be properly extracted by the parser
                location_info = "Hydrophone Recording"
                if hasattr(state, 'time_objects_utc') and state.time_objects_utc:
                    valid_times = [t for t in state.time_objects_utc if t is not None]
                    if valid_times:
                        start_time = min(valid_times)
                        end_time = max(valid_times)
                        date_range = start_time.strftime("%Y-%m-%d")
                        if start_time.date() != end_time.date():
                            date_range += f" to {end_time.strftime('%Y-%m-%d')}"
                        location_info = f"Hydrophone Data {date_range}"
                
                # Use these fields since the parser checks for them first - but maintain Lucy format
                f.write(f"Client\t{project_name}\n")
                f.write(f"Job\t{location_info}\n")
                
                # Only include a comment in the standard Lucy format
                f.write(f"# {project_name} - {location_info}\n")
                
                f.write(f"Personnel\tHydrophone User\n")
                
                # Add starting sample if present
                if hasattr(state, 'starting_sample') and state.starting_sample:
                    f.write(f"Starting Sample\t{state.starting_sample}\n")
                else:
                    f.write(f"Starting Sample\t0\n")
                
                # Add device info
                f.write(f"\nDevice Details:\n")
                f.write(f"Device\ticListen HF\n")  # Match original device name
                f.write(f"S/N\t7014\n")
                f.write(f"Firmware\tv2.6.20\n")
                
                # Add setup info
                f.write(f"\nSetup:\n")
                f.write(f"dB Ref re 1V\t-180\n")
                f.write(f"dB Ref re 1uPa\t-8\n")
                
                # Try to use actual sample rate or default
                sample_rate = 64000  # Default
                if hasattr(state, 'sample_rate') and state.sample_rate:
                    sample_rate = state.sample_rate
                f.write(f"Sample Rate [S/s]\t{sample_rate}\n")
                
                # Calculate FFT size based on frequency bins if available
                fft_size = 1024  # Default
                if hasattr(state, 'freqs_global') and len(state.freqs_global) > 0:
                    fft_size = len(state.freqs_global) * 2  # Approximation
                f.write(f"FFT Size\t{fft_size}\n")
                
                # Calculate bin width if possible
                bin_width = 62.5  # Default
                if hasattr(state, 'freqs_global') and len(state.freqs_global) > 1:
                    bin_width = state.freqs_global[1] - state.freqs_global[0]
                f.write(f"Bin Width [Hz]\t{bin_width}\n")
                
                # Add other standard parameters
                f.write(f"Window Function\tHann\n")
                f.write(f"Overlap [%]\t50.0\n")
                f.write(f"Power Calculation\tMean\n")
                f.write(f"Accumulations\t125\n")
                
                # Add data marker
                f.write("\nData:\n\n")
                
                # Write column headers - exactly like Lucy format
                f.write("Time\tComment\tTemperature\tHumidity\tSequence #\tData Points")
                for freq in state.freqs_global:
                    f.write(f"\t{freq:.1f}")
                f.write("\n")
                
                # Write a progress update every 100 rows
                num_rows = len(state.data_global)
                for i, (time_obj, data_row) in enumerate(zip(state.time_objects_utc, state.data_global)):
                    if time_obj is None:
                        continue
                    
                    # Convert to local timezone
                    local_time = time_obj.astimezone(state.current_timezone)
                    time_str = local_time.strftime("%H:%M:%S")
                    
                    # Get the comment for this time point
                    comment_text = ""
                    if hasattr(state, 'comments') and state.comments:
                        # Find any comment that covers this time point
                        for comment in state.comments:
                            if comment['start_idx'] <= i <= comment['end_idx']:
                                comment_text = comment['text']
                                break
                    
                    # Write data row with proper comment field
                    f.write(f"{time_str}\t{comment_text}\t22.8\t31.1\t{i+1}\tDatapoint\t")
                    f.write("\t".join(f"{val:.2f}" for val in data_row))
                    f.write("\n")
                    
                    # Show progress update in log every 1000 rows
                    if i % 1000 == 0 or i == num_rows - 1:
                        progress_pct = int((i / num_rows) * 100)
                        add_log_entry(f"Export progress: {progress_pct}% ({i}/{num_rows} rows)")
                        
                        # Update log display
                        from utils import update_log_display
                        update_log_display()
                        
                        # Force redraw to keep UI responsive
                        if hasattr(state, 'fig') and state.fig is not None:
                            state.fig.canvas.draw_idle()
                            state.fig.canvas.flush_events()
            
            add_log_entry(f"Created export file: {export_file_path}")
            
            # Success message with detailed information about the exported data
            
            # Get time range information for the message
            time_range_info = "Unknown time range"
            total_duration = "Unknown duration"
            if valid_times:
                start_time = min(valid_times)
                end_time = max(valid_times)
                start_local = start_time.astimezone(state.current_timezone)
                end_local = end_time.astimezone(state.current_timezone)
                
                # Format the time range
                time_range_info = f"{start_local.strftime('%Y-%m-%d %H:%M:%S')} to {end_local.strftime('%Y-%m-%d %H:%M:%S')}"
                
                # Calculate total duration
                duration_seconds = (end_time - start_time).total_seconds()
                hours, remainder = divmod(duration_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours > 0:
                    total_duration = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
                else:
                    total_duration = f"{int(minutes)}m {int(seconds)}s"
            
            # Calculate additional metadata
            num_rows = len(state.data_global)
            freq_min = min(state.freqs_global) if len(state.freqs_global) > 0 else 0
            freq_max = max(state.freqs_global) if len(state.freqs_global) > 0 else 0
            
            # Get file size
            try:
                file_size_bytes = os.path.getsize(export_file_path)
                if file_size_bytes > 1024*1024:
                    file_size = f"{file_size_bytes/(1024*1024):.2f} MB"
                else:
                    file_size = f"{file_size_bytes/1024:.2f} KB"
            except:
                file_size = "Unknown"
            
            # Get input files summary
            input_file_count = len(state.file_paths) if hasattr(state, 'file_paths') else 0
            input_files_summary = f"{input_file_count} input files merged into 1 export file"
            
            if input_file_count > 0 and input_file_count <= 3:
                # For a small number of files, show the names
                input_files_list = '\n- '.join([os.path.basename(path) for path in state.file_paths])
                input_files_summary += f"\nInput files:\n- {input_files_list}"
            
            # Get original file timezone
            original_tz = state.detected_file_timezone.zone if hasattr(state, 'detected_file_timezone') else 'Unknown'
            export_tz = state.current_timezone.zone
            
            # Export comments to a separate comments file if there are any
            comment_file_created = False
            comment_count = 0
            if hasattr(state, 'comments') and state.comments:
                try:
                    # Import our comment file handler
                    from comment_file_handler import export_comments_to_file
                    
                    # Export comments to a file associated with the main data file
                    comment_file_created = export_comments_to_file(export_file_path)
                    comment_count = len(state.comments)
                    
                    # Also create a second version without the .txt extension
                    # (This ensures import will work even if user renames the file)
                    base_path = os.path.splitext(export_file_path)[0]
                    export_comments_to_file(base_path)
                    
                    add_log_entry(f"Exported {comment_count} comments to {export_file_path}.comments.json")
                except Exception as e:
                    add_log_entry(f"Error exporting comments to separate file: {str(e)}")
                    # Continue with main export even if comment export fails
            
            # Format the export details message
            message = (f"Export completed successfully to:\n{export_dir}\n\n"
                      f"File created:\n{file_name}\n\n"
                      f"Project: {project_name}\n"
                      f"Original file timezone: {original_tz}\n"
                      f"Data exported using: {export_tz}\n"
                      f"Time Range: {time_range_info}\n"
                      f"Total Duration: {total_duration}\n\n"
                      f"Data Summary:\n"
                      f"- {num_rows} rows exported\n"
                      f"- Frequency range: {freq_min:.1f} Hz - {freq_max:.1f} Hz\n"
                      f"- {input_files_summary}\n"
                      f"- File size: {file_size}")
                      
            # Add comment export information if applicable
            if comment_file_created:
                message += f"\n\nAdditional Files:\n- Comment file with {comment_count} comments and details"
            
            messagebox.showinfo("Export Complete", message)
            
        except Exception as e:
            add_log_entry(f"Error during file export: {str(e)}")
            messagebox.showerror("Export Error", f"An error occurred during export:\n\n{str(e)}")
    
    except Exception as e:
        add_log_entry(f"Error in export process: {str(e)}")
        messagebox.showerror("Export Error", f"An error occurred:\n\n{str(e)}")
    
    # Restore the log display
    from utils import update_log_display
    update_log_display()

# === Navigation Handlers ===

def on_nav_press(event):
    """Handle mouse press on navigation spectrogram"""
    if event.inaxes != state.ax_nav_spec or event.button != 1:
        return
    
    x = event.xdata
    if x is None:
        return
    
    # CRITICAL FIX: Convert x to integer indices
    x_idx = int(x)
    
    # CRITICAL FIX: Validate and limit to data range
    data_length = len(state.data_global) if hasattr(state, 'data_global') and state.data_global is not None else 0
    if data_length == 0:
        add_log_entry("Error: Cannot navigate - no data available", debug_only=True)
        return
    
    # Log the click for debugging
    add_log_entry(f"Nav click at x={x_idx} (of {data_length-1}), current view: {state.time_zoom_start}-{state.time_zoom_end}", debug_only=True)
    
    # Check if clicking near edges for resizing
    edge_tolerance = max(int((state.time_zoom_end - state.time_zoom_start) * 0.1), 5)  # At least 5 data points
    
    if abs(x_idx - state.time_zoom_start) < edge_tolerance:
        # Clicking near left edge - resize
        state.nav_resizing = True
        state.nav_resize_edge = 'left'
        state.nav_drag_start = x_idx
        add_log_entry(f"Starting left edge resize from {state.time_zoom_start}", debug_only=True)
    elif abs(x_idx - state.time_zoom_end) < edge_tolerance:
        # Clicking near right edge - resize
        state.nav_resizing = True
        state.nav_resize_edge = 'right'
        state.nav_drag_start = x_idx
        add_log_entry(f"Starting right edge resize from {state.time_zoom_end}", debug_only=True)
    elif state.time_zoom_start <= x_idx <= state.time_zoom_end:
        # Clicking inside the box - start dragging
        state.nav_dragging = True
        state.nav_drag_start = x_idx
        add_log_entry(f"Starting drag from position {x_idx}", debug_only=True)
    else:
        # Clicking outside the box - jump to that position
        span = state.time_zoom_end - state.time_zoom_start
        
        # CRITICAL FIX: Ensure x_idx is clamped to valid range
        x_idx = max(0, min(x_idx, data_length - 1))
        
        # Center the view on the click point while maintaining the exact zoom span
        new_start = max(0, x_idx - span//2)  # Integer division
        new_end = min(data_length - 1, new_start + span)  # Ensure exact span
        
        # If we would go beyond the right edge, adjust both start and end
        if new_end >= data_length - 1:
            new_end = data_length - 1
            new_start = max(0, new_end - span)  # Ensure we maintain the span
        
        add_log_entry(f"Nav jump to x={x_idx}, setting view: {new_start}-{new_end}", debug_only=True)
        update_time_zoom((new_start, new_end))

def on_nav_motion(event):
    """Handle mouse motion on navigation spectrogram"""
    if event.inaxes != state.ax_nav_spec:
        return
    
    x = event.xdata
    if x is None:
        return
    
    # CRITICAL FIX: Validate data availability and convert to integer indices
    data_length = len(state.data_global) if hasattr(state, 'data_global') and state.data_global is not None else 0
    if data_length == 0:
        return
    
    # Convert to integer index
    x_idx = int(x)
    
    # Ensure x is within valid range
    x_idx = max(0, min(x_idx, data_length - 1))
    
    if state.nav_dragging and state.nav_drag_start is not None:
        # Calculate the drag offset - how many indices we've moved
        offset = x_idx - state.nav_drag_start
        
        # Only process if there's an actual change
        if offset == 0:
            return
            
        span = state.time_zoom_end - state.time_zoom_start
        
        # Apply the offset to both start and end, maintaining exact span
        new_start = state.time_zoom_start + offset
        new_end = state.time_zoom_end + offset
        
        # Handle boundary conditions while preserving span
        if new_start < 0:
            # Hit left boundary
            new_start = 0
            new_end = new_start + span  # Ensure exact span is maintained
        elif new_end >= data_length - 1:
            # Hit right boundary - ensure no overflow
            new_end = data_length - 1
            new_start = max(0, new_end - span)  # Ensure exact span is maintained
        
        # Update the drag start position for next motion
        state.nav_drag_start = x_idx
        
        # Log the drag operation
        add_log_entry(f"Nav drag to x={x_idx}, setting view: {new_start}-{new_end}", debug_only=True)
        
        # Update zoom
        update_time_zoom((new_start, new_end))
    
    elif state.nav_resizing and state.nav_drag_start is not None:
        # CRITICAL FIX: Validate data availability
        data_length = len(state.data_global) if hasattr(state, 'data_global') and state.data_global is not None else 0
        if data_length == 0:
            return
            
        # CRITICAL FIX: Convert to integer index
        x_idx = int(x)
        
        # CRITICAL FIX: Ensure x is within valid range
        x_idx = max(0, min(x_idx, data_length - 1))
        
        if state.nav_resize_edge == 'left':
            # Ensure minimum width and prevent crossing right edge
            min_width = 10  # Minimum width of 10 data points
            max_allowed_start = state.time_zoom_end - min_width
            
            # Restrict to valid range and prevent crossing right edge
            new_start = max(0, min(x_idx, max_allowed_start))
            
            # Log the resize operation
            add_log_entry(f"Nav resize left edge to x={x_idx}, setting view: {new_start}-{state.time_zoom_end}", debug_only=True)
            
            # Apply the update
            update_time_zoom((new_start, state.time_zoom_end))
            state.nav_drag_start = x_idx  # Update drag position
            
        elif state.nav_resize_edge == 'right':
            # Ensure minimum width and prevent crossing left edge
            min_width = 10  # Minimum width of 10 data points
            min_allowed_end = state.time_zoom_start + min_width
            
            # Restrict to valid range and prevent crossing left edge
            new_end = min(data_length - 1, max(x_idx, min_allowed_end))
            
            # Log the resize operation
            add_log_entry(f"Nav resize right edge to x={x_idx}, setting view: {state.time_zoom_start}-{new_end}", debug_only=True)
            
            # Apply the update
            update_time_zoom((state.time_zoom_start, new_end))
            state.nav_drag_start = x_idx  # Update drag position

def on_nav_release(event):
    """Handle mouse release on navigation spectrogram"""
    state.nav_dragging = False
    state.nav_resizing = False
    state.nav_drag_start = None
    state.nav_resize_edge = None

def on_nav_scroll(event):
    """Handle mouse scroll on navigation spectrogram for zooming"""
    if event.inaxes != state.ax_nav_spec:
        return
    
    x = event.xdata
    if x is None:
        return
    
    # Current span
    span = state.time_zoom_end - state.time_zoom_start
    
    # Zoom factor
    if event.button == 'up':
        # Zoom in
        factor = 0.8
    else:
        # Zoom out
        factor = 1.2
    
    # Calculate new span
    new_span = span * factor
    new_span = max(10, min(new_span, len(state.data_global) - 1))  # Limit zoom range
    
    # Center zoom on mouse position
    left_ratio = (x - state.time_zoom_start) / span
    right_ratio = (state.time_zoom_end - x) / span
    
    new_start = x - new_span * left_ratio
    new_end = x + new_span * right_ratio
    
    # Ensure within bounds
    if new_start < 0:
        new_start = 0
        new_end = new_span
    elif new_end > len(state.data_global) - 1:
        new_end = len(state.data_global) - 1
        new_start = new_end - new_span
    
    update_time_zoom((new_start, new_end))

# === Zoom Control Functions ===

def reset_time_zoom(event):
    """Reset time zoom to show all data"""
    try:
        if state.data_global is not None:
            add_log_entry("Resetting zoom to show all data")
            update_time_zoom((0, len(state.data_global) - 1))
        else:
            add_log_entry("No data available to zoom")
    except Exception as e:
        add_log_entry(f"Error in reset_time_zoom: {str(e)}")

def zoom_in_time(event):
    """Zoom in on the time axis"""
    try:
        current_span = state.time_zoom_end - state.time_zoom_start
        center = (state.time_zoom_start + state.time_zoom_end) / 2
        
        # Zoom in by 50%
        new_span = current_span * 0.5
        new_start = max(0, center - new_span / 2)
        new_end = min(len(state.data_global) - 1, center + new_span / 2)
        
        add_log_entry(f"Zooming in: {new_start:.1f}-{new_end:.1f}")
        update_time_zoom((new_start, new_end))
    except Exception as e:
        add_log_entry(f"Error in zoom_in_time: {str(e)}")

def zoom_out_time(event):
    """Zoom out on the time axis"""
    try:
        current_span = state.time_zoom_end - state.time_zoom_start
        center = (state.time_zoom_start + state.time_zoom_end) / 2
        
        # Zoom out by 50%
        new_span = current_span * 2
        new_start = max(0, center - new_span / 2)
        new_end = min(len(state.data_global) - 1, center + new_span / 2)
        
        # Ensure we don't zoom out beyond the data
        if new_span > len(state.data_global) - 1:
            new_start = 0
            new_end = len(state.data_global) - 1
        
        add_log_entry(f"Zooming out: {new_start:.1f}-{new_end:.1f}")
        update_time_zoom((new_start, new_end))
    except Exception as e:
        add_log_entry(f"Error in zoom_out_time: {str(e)}")

def pan_left(event):
    """Pan left on the time axis"""
    try:
        span = state.time_zoom_end - state.time_zoom_start
        shift = span * 0.1  # Pan by 10% of the visible span
        
        new_start = max(0, state.time_zoom_start - shift)
        new_end = new_start + span
        
        if new_end > len(state.data_global) - 1:
            new_end = len(state.data_global) - 1
            new_start = new_end - span
        
        add_log_entry(f"Panning left: {new_start:.1f}-{new_end:.1f}")
        update_time_zoom((new_start, new_end))
    except Exception as e:
        add_log_entry(f"Error in pan_left: {str(e)}")

def pan_right(event):
    """Pan right on the time axis"""
    try:
        span = state.time_zoom_end - state.time_zoom_start
        shift = span * 0.1  # Pan by 10% of the visible span
        
        new_end = min(len(state.data_global) - 1, state.time_zoom_end + shift)
        new_start = new_end - span
        
        if new_start < 0:
            new_start = 0
            new_end = new_start + span
        
        add_log_entry(f"Panning right: {new_start:.1f}-{new_end:.1f}")
        update_time_zoom((new_start, new_end))
    except Exception as e:
        add_log_entry(f"Error in pan_right: {str(e)}")

# === Gain Control Functions ===

def adjust_min_gain(delta, event=None):
    """Adjust minimum gain with bounds checking"""
    try:
        if not hasattr(state, 'gain_slider') or not state.gain_slider:
            add_log_entry("Gain slider not initialized")
            return
            
        lo, hi = state.gain_slider.val
        
        # Calculate new value with bounds checking
        new_lo = lo + delta
        new_lo = max(0, min(new_lo, hi - 0.1))
        
        # Update slider and apply to spectrogram
        state.gain_slider.set_val((new_lo, hi))
        
        # Apply directly to the spectrogram
        if state.spec_img:
            state.spec_img.set_clim(new_lo, hi)
            add_log_entry(f"Updated min gain: {new_lo:.2f}")
            plt.draw()
    except Exception as e:
        add_log_entry(f"Error adjusting min gain: {str(e)}")

def adjust_max_gain(delta, event=None):
    """Adjust maximum gain with bounds checking"""
    try:
        if not hasattr(state, 'gain_slider') or not state.gain_slider:
            add_log_entry("Gain slider not initialized")
            return
            
        lo, hi = state.gain_slider.val
        
        # Calculate new value with bounds checking
        new_hi = hi + delta
        new_hi = max(lo + 0.1, min(new_hi, 10))
        
        # Update slider and apply to spectrogram
        state.gain_slider.set_val((lo, new_hi))
        
        # Apply directly to the spectrogram
        if state.spec_img:
            state.spec_img.set_clim(lo, new_hi)
            add_log_entry(f"Updated max gain: {new_hi:.2f}")
            plt.draw()
    except Exception as e:
        add_log_entry(f"Error adjusting max gain: {str(e)}")

# === UI Event Handlers ===

def on_timezone_change(event):
    """Handle timezone change event"""
    selected_tz_name = state.timezone_dropdown.get()
    try:
        state.current_timezone = pytz.timezone(selected_tz_name)
        
        # Update time labels
        update_time_labels_for_timezone()
        
        # Update x-axis display
        update_spectrogram_xaxis()
        
        # Update click text if it exists
        if state.spec_click_text and state.spec_click_line:
            idx = int(state.spec_click_line.get_xdata()[0])
            time_str = state.time_labels_all[idx]
            display_time = time_str[:5] if time_str != "GAP" else "GAP"
            state.spec_click_text.set_text(display_time)
        
        # Update audio timeline
        if state.ax_audio_timeline:
            # Import here to avoid circular import
            from visualization import update_audio_timeline_visualization
            update_audio_timeline_visualization()
        
        # Update FFT display - both single point and range
        if hasattr(state, 'spec_click_line') and state.spec_click_line:
            # Single point FFT
            idx = int(state.spec_click_line.get_xdata()[0])
            from visualization import update_fft
            update_fft(idx, state.freqs_global, state.data_global)
        
        # Update FFT title if it's showing a stacked range
        if hasattr(state, 'selected_range') and state.selected_range:
            start, end = state.selected_range
            from visualization import update_fft_range
            update_fft_range(start, end, state.freqs_global, state.data_global)
        
        # Update button text
        if state.btn_timezone:
            state.btn_timezone.label.set_text(f'Timezone: {selected_tz_name.split("/")[-1]}')
        
        # Close dropdown window
        state.timezone_dropdown.master.destroy()
        
        add_log_entry(f"Timezone changed to {selected_tz_name}")
        
        # Force complete redraw to update all matplotlib elements
        if hasattr(state, 'fig') and state.fig:
            state.fig.canvas.draw_idle()
        
        plt.draw()
        
    except Exception as e:
        add_log_entry(f"Error changing timezone: {str(e)}")
        logging.error(f"Error changing timezone", exc_info=True)

def on_tz_file_clicked(event):
    """Handle file timezone button click"""
    if state.timezone_selection == 'file':
        return  # Already selected
    
    state.timezone_selection = 'file'
    state.use_local_timezone = False
    state.current_timezone = state.detected_file_timezone
    
    # Update button states - this must be called to change colors
    from ui_components import update_timezone_button_states
    update_timezone_button_states()
    
    # Safely get timezone name
    try:
        if hasattr(state.detected_file_timezone, 'zone'):
            file_tz_name = state.detected_file_timezone.zone
        else:
            file_tz_name = str(state.detected_file_timezone)
    except Exception:
        file_tz_name = "UTC"
    
    add_log_entry(f"Switched to file timezone: {file_tz_name}")
    
    # Update time displays
    update_timezone_display()
    
    # Force complete redraw to ensure button colors update
    if hasattr(state, 'fig') and state.fig:
        state.fig.canvas.draw_idle()

def on_tz_local_clicked(event):
    """Handle local timezone button click"""
    if state.timezone_selection == 'local':
        return  # Already selected
    
    state.timezone_selection = 'local'
    state.use_local_timezone = True
    state.current_timezone = state.system_timezone
    
    # Update button states - this must be called to change colors
    from ui_components import update_timezone_button_states
    update_timezone_button_states()
    
    # Safely get timezone name
    try:
        if hasattr(state.system_timezone, 'zone'):
            system_tz_name = state.system_timezone.zone
        else:
            system_tz_name = str(state.system_timezone)
    except Exception:
        system_tz_name = "Local"
    
    add_log_entry(f"Switched to local timezone: {system_tz_name}")
    
    # Update time displays
    update_timezone_display()
    
    # Force complete redraw to ensure button colors update
    if hasattr(state, 'fig') and state.fig:
        state.fig.canvas.draw_idle()

def on_tz_user_clicked(event):
    """Handle user select timezone button click"""
    # Create timezone selection dialog
    from tkinter import Toplevel, Listbox, Scrollbar, SINGLE, END
    
    # Create dialog window
    dialog = Toplevel()
    dialog.title("Select Timezone")
    dialog.geometry("300x400")
    
    # Create listbox with scrollbar
    frame = tk.Frame(dialog)
    frame.pack(fill=tk.BOTH, expand=1, padx=10, pady=10)
    
    scrollbar = Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    listbox = Listbox(frame, yscrollcommand=scrollbar.set, selectmode=SINGLE)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
    scrollbar.config(command=listbox.yview)
    
    # Add all pytz timezones
    tz_list = sorted(pytz.all_timezones)
    for tz in tz_list:
        listbox.insert(END, tz)
    
    # Set current selection if user timezone exists
    if hasattr(state, 'user_selected_timezone') and state.user_selected_timezone:
        try:
            current_tz = state.user_selected_timezone.zone
            index = tz_list.index(current_tz)
            listbox.selection_set(index)
            listbox.see(index)
        except:
            pass
    
    def on_select():
        selection = listbox.curselection()
        if selection:
            tz_name = listbox.get(selection[0])
            state.user_selected_timezone = pytz.timezone(tz_name)
            state.timezone_selection = 'user'
            state.current_timezone = state.user_selected_timezone
            
            # Update button label
            if hasattr(state, 'btn_tz_user'):
                user_label = f"User TZ: {tz_name.split('/')[-1]}"  # Single line
                state.btn_tz_user.label.set_text(user_label)
            
            # Update button states - this must be called to change colors
            from ui_components import update_timezone_button_states
            update_timezone_button_states()
            
            add_log_entry(f"Switched to user-selected timezone: {tz_name}")
            
            # Update time displays
            update_timezone_display()
            
            dialog.destroy()
            
            # Force complete redraw to ensure button colors update
            if hasattr(state, 'fig') and state.fig:
                state.fig.canvas.draw_idle()
    
    # Add select button
    select_btn = tk.Button(dialog, text="Select", command=on_select)
    select_btn.pack(pady=10)
    
    # Add cancel button
    cancel_btn = tk.Button(dialog, text="Cancel", command=dialog.destroy)
    cancel_btn.pack(pady=5)

def update_timezone_display():
    """Update all time-related displays after timezone change"""
    try:
        # Update time labels
        update_time_labels_for_timezone()
        
        # Update x-axis display
        update_spectrogram_xaxis()
        
        # Update click text if it exists
        if state.spec_click_text and state.spec_click_line:
            idx = int(state.spec_click_line.get_xdata()[0])
            time_str = state.time_labels_all[idx]
            display_time = time_str[:5] if time_str != "GAP" else "GAP"
            state.spec_click_text.set_text(display_time)
        
        # Update audio timeline
        if state.ax_audio_timeline:
            # Import here to avoid circular import
            from visualization import update_audio_timeline_visualization
            update_audio_timeline_visualization()
        
        # Update FFT display - both single point and range
        if hasattr(state, 'spec_click_line') and state.spec_click_line:
            # Single point FFT
            idx = int(state.spec_click_line.get_xdata()[0])
            from visualization import update_fft
            update_fft(idx, state.freqs_global, state.data_global)
        
        # Update FFT title if it's showing a stacked range
        if hasattr(state, 'selected_range') and state.selected_range:
            start, end = state.selected_range
            from visualization import update_fft_range
            update_fft_range(start, end, state.freqs_global, state.data_global)
        
        # Force complete redraw to update all matplotlib elements
        if hasattr(state, 'fig') and state.fig:
            state.fig.canvas.draw_idle()
        
        plt.draw()
        
    except Exception as e:
        add_log_entry(f"Error updating timezone display: {str(e)}")
        logging.error(f"Error updating timezone display", exc_info=True)

def create_timezone_dropdown():
    """This function is deprecated but kept for backward compatibility"""
    # Show a message indicating the functionality has changed
    messagebox.showinfo(
        "Timezone Selection", 
        f"Timezone selection is now automatic.\n\n"
        f"File timezone: {state.detected_file_timezone.zone}\n"
        f"Local timezone: {state.system_timezone.zone}\n\n"
        f"Use the checkbox to toggle between file timezone and local timezone."
    )

def on_load_audio(event):
    """Load audio files with timestamp-based alignment"""
    from data_parser import load_and_merge_audio_with_timestamp_alignment
    
    wav_paths = filedialog.askopenfilenames(
        title="Select WAV files",
        filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
    )
    
    if wav_paths:
        try:
            # Attempt to load audio files with timestamp alignment
            load_and_merge_audio_with_timestamp_alignment(wav_paths)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load audio: {str(e)}")
            logging.error(f"Error loading audio files", exc_info=True)

def on_play_audio(event):
    """Handle play/stop audio button click"""
    add_log_entry("Play/stop button clicked")
    
    # Check if audio is currently playing - if so, stop it
    if state.audio_playing:
        add_log_entry("Audio was playing - stopping it")
        
        # First call stop_audio to ensure playback is stopped
        stop_audio()
        
        # Recreate the button to ensure clean display with no overlapping text
        from matplotlib.widgets import Button
        if hasattr(state, 'ax_audio_play') and state.ax_audio_play is not None:
            # Clear the axis first
            state.ax_audio_play.clear()
            
            # Recreate the button with original color
            state.btn_audio_play = Button(state.ax_audio_play, 'Play Audio', color='0.85')
            state.btn_audio_play.on_clicked(on_play_audio)
            
            # Force redraw of just this axis
            if hasattr(state.ax_audio_play, 'figure') and hasattr(state.ax_audio_play.figure, 'canvas'):
                state.ax_audio_play.figure.canvas.draw_idle()
        
        # Exit early to avoid starting playback again
        return
    
    # Validate we have audio data
    if not hasattr(state, 'audio_data') or state.audio_data is None or len(state.audio_data) == 0:
        add_log_entry("No audio loaded")
        return
    
    # Validate sample rate
    if not hasattr(state, 'audio_sample_rate') or state.audio_sample_rate <= 0:
        add_log_entry("Invalid audio sample rate")
        return
    
    # Check for selection
    if not hasattr(state, 'selected_range') or state.selected_range is None:
        add_log_entry("Select a time range first")
        return
    
    # Check audio coverage
    start_idx, end_idx = state.selected_range
    start_time = start_idx  # Assuming 1 second per FFT
    end_time = end_idx
    
    # Validate selection
    if end_idx <= start_idx:
        add_log_entry(f"Invalid selection range: {start_idx}-{end_idx}")
        return
    
    # Print debug info
    add_log_entry(f"Selection range: {start_idx}-{end_idx}")
    
    # Check if this range is covered by audio
    has_coverage = False
    if hasattr(state, 'audio_segments') and state.audio_segments:
        for seg_start, seg_end in state.audio_segments:
            if not (end_time <= seg_start or start_time >= seg_end):
                has_coverage = True
                add_log_entry(f"Found audio coverage in segment {seg_start}-{seg_end}")
                break
    else:
        add_log_entry("No audio segments defined")
        return
    
    if not has_coverage:
        add_log_entry("No audio available for selected range")
        return
    
    # Make sure no playback is happening
    sd.stop()
    
    # Reset state flags to ensure clean start
    state.audio_stop_flag = False
    state.audio_finished = False
    
    # Recreate the button as a stop button
    from matplotlib.widgets import Button
    if hasattr(state, 'ax_audio_play') and state.ax_audio_play is not None:
        # Clear the axis first
        state.ax_audio_play.clear()
        
        # Recreate the button as a Stop button with red color
        state.btn_audio_play = Button(state.ax_audio_play, 'Stop Audio', color='lightcoral')
        state.btn_audio_play.on_clicked(on_play_audio)
        
        # Force redraw of just this axis
        if hasattr(state.ax_audio_play, 'figure') and hasattr(state.ax_audio_play.figure, 'canvas'):
            state.ax_audio_play.figure.canvas.draw_idle()
    
    # Set audio playing flag just before starting playback
    state.audio_playing = True
    
    # Play audio for the selected range
    play_audio(start_idx, end_idx)

def on_spec_click(event):
    """Handle click on the spectrogram"""
    if event.inaxes == state.ax_spec:
        idx = max(0, min(int(event.xdata), state.data_global.shape[0] - 1))
        
        # Check if audio is playing and click is within the selected range
        if state.audio_playing and state.selected_range and event.button == 1:
            start_idx, end_idx = state.selected_range
            
            # Check if click is within the playing range
            if start_idx <= idx <= end_idx:
                # Stop current playback
                stop_audio()
                
                # Start playback from new position
                new_start_idx = idx
                state.selected_range = (new_start_idx, end_idx)
                play_audio(new_start_idx, end_idx)
                return
        
        # Normal click behavior when audio is not playing
        if event.button == 1:
            if state.fft_patch:
                state.fft_patch.remove()
                state.fft_patch = None
            state.selected_range = None
            update_fft(idx, state.freqs_global, state.data_global)
            if state.spec_click_line:
                state.spec_click_line.remove()
            if state.spec_click_text:
                state.spec_click_text.remove()
            state.spec_click_line = state.ax_spec.axvline(idx, color='white', linewidth=1)
            time_str = state.time_labels_all[idx]
            # Show HH:MM format
            display_time = time_str[:5] if time_str != "GAP" else "GAP"
            state.spec_click_text = state.ax_spec.text(idx, 0, display_time,
                                         transform=blended_transform_factory(state.ax_spec.transData, state.ax_spec.transAxes),
                                         color='white', rotation=90, va='top', ha='center', clip_on=False)
            
            # Auto-adjust the FFT Y-axis range for the selected point (only if not manually set)
            if not state.fft_manual_gain:
                from visualization import auto_adjust_fft_range
                auto_adjust_fft_range()
            
        elif event.button == 3:
            if state.spec_click_line:
                start = int(state.spec_click_line.get_xdata()[0])
                end = idx
                if start > end:
                    start, end = end, start
                if state.fft_patch:
                    state.fft_patch.remove()
                state.fft_patch = state.ax_spec.axvspan(start, end, color='red', alpha=0.3)
                state.selected_range = (start, end)
                update_fft_range(start, end, state.freqs_global, state.data_global)
                
                # Auto-adjust the FFT Y-axis range for the selected range (only if not manually set)
                if not state.fft_manual_gain:
                    from visualization import auto_adjust_fft_range
                    auto_adjust_fft_range()
                
    plt.draw()

def on_click(event):
    """Handle mouse clicks with modifiers for frequency markers"""
    if event.key == 'control' and event.inaxes == state.ax_fft:
        # The x-coordinate is already in kHz since we've updated the FFT display
        # No need to convert here, the update_marker function will handle it
        if event.button == 1:
            # Log the click for debugging
            add_log_entry(f"Setting marker 1 at {event.xdata:.2f} kHz")
            update_marker(0, event.xdata)
        elif event.button == 3:
            add_log_entry(f"Setting marker 2 at {event.xdata:.2f} kHz")
            update_marker(1, event.xdata)

def on_key_press(event):
    """Handle keyboard shortcuts"""
    # Check if any textbox has focus - if so, ignore keyboard shortcuts
    try:
        from simple_focus_tracker import is_textbox_focused
        if is_textbox_focused():
            return
    except ImportError:
        pass
    
    # Also check the older way for compatibility
    if hasattr(state, 'comment_input') and hasattr(state.comment_input, 'active') and state.comment_input.active:
        return
    if hasattr(state, 'notes_input') and hasattr(state.notes_input, 'active') and state.notes_input.active:
        return
    
    # Zoom controls with keyboard
    if event.key == '+' or event.key == '=':
        zoom_in_time(None)
    elif event.key == '-':
        zoom_out_time(None)
    elif event.key == '0':
        reset_time_zoom(None)
    elif event.key == 'a':
        pan_left(None)
    elif event.key == 'd':
        pan_right(None)
    
    # Comment-related shortcuts
    elif event.key == 'delete':
        # Delete selected comment
        if hasattr(state, 'selected_comment_id') and state.selected_comment_id is not None:
            from comment_operations import delete_selected_comment
            delete_selected_comment()
    
    # Original navigation controls
    elif state.spec_click_line is not None and event.key in ['left', 'right']:
        if state.fft_patch:
            state.fft_patch.remove()
            state.fft_patch = None
        current = state.spec_click_line.get_xdata()[0]
        idx = int(current) + (-1 if event.key == 'left' else 1)
        # Keep within current zoom range
        idx = max(state.time_zoom_start, min(idx, state.time_zoom_end))
        # Import here to avoid circular import
        update_fft(idx, state.freqs_global, state.data_global)
        state.spec_click_line.set_xdata([idx, idx])
        time_str = state.time_labels_all[idx]
        display_time = time_str[:5] if time_str != "GAP" else "GAP"
        state.spec_click_text.set_text(display_time)
        state.spec_click_text.set_position((idx, 0))
        plt.draw()

def on_key_press_audio(event):
    """Handle keyboard shortcuts for audio control"""
    # Check if any textbox has focus - if so, ignore audio shortcuts
    try:
        from simple_focus_tracker import is_textbox_focused
        if is_textbox_focused():
            return
    except ImportError:
        pass
    
    # Also check the older way for compatibility
    if hasattr(state, 'comment_input') and hasattr(state.comment_input, 'active') and state.comment_input.active:
        return
    if hasattr(state, 'notes_input') and hasattr(state.notes_input, 'active') and state.notes_input.active:
        return
    
    if event.key == ' ':  # Spacebar for play/stop
        on_play_audio(None)
    elif event.key == 'escape' and state.audio_playing:  # Escape to stop
        stop_audio()

def on_key_release(event):
    """Handle key release events"""
    if event.key == 'control':
        # This would normally deactivate the span selector
        pass

def on_pick(event):
    """Handle pick events for file list items"""
    if event.artist in state.file_texts:
        # Get the actual file index from the stored attribute
        idx = event.artist._file_index
        start, end = state.file_ranges[idx]
        try:
            if state.file_patch:
                state.file_patch.remove()
        except ValueError:
            state.file_patch = None
        # Highlight on navigation spectrogram instead of main spectrogram
        state.file_patch = state.ax_nav_spec.axvspan(start, end, color='yellow', alpha=0.4, zorder=2)
        for txt in state.file_texts:
            txt.set_backgroundcolor('yellow' if txt._file_index == idx else None)
        plt.draw()

def clear_file_highlight(event):
    """Clear file highlight from the navigation view"""
    if state.file_patch:
        try:
            state.file_patch.remove()
        except ValueError:
            pass
        state.file_patch = None
    for txt in state.file_texts:
        txt.set_backgroundcolor(None)
    plt.draw()

def scroll_log_up(event):
    """Scroll log display up"""
    state.scroll_position = max(0, state.scroll_position - 1)
    update_log_display()

def scroll_log_down(event):
    """Scroll log display down"""
    max_position = max(0, len(state.log_entries) - 5)
    state.scroll_position = min(max_position, state.scroll_position + 1)
    update_log_display()

def scroll_files_up(event):
    """Scroll file list up"""
    state.file_scroll_position = max(0, state.file_scroll_position - 1)
    display_file_list()

def scroll_files_down(event):
    """Scroll file list down"""
    max_position = max(0, len(state.file_paths) - state.visible_files)
    state.file_scroll_position = min(max_position, state.file_scroll_position + 1)
    display_file_list()

def display_file_list():
    """Display the file list with current scroll position"""
    # FIXED: Use state.ax_filelist instead of ax_filelist
    if not state.ax_filelist:
        return
    
    state.ax_filelist.clear()
    # Title is now set via fig.text in ui_components
    state.ax_filelist.axis("off")
    state.ax_filelist.set_facecolor('#f0f0f0')
    
    # Calculate which files to show
    start_idx = state.file_scroll_position
    end_idx = min(start_idx + state.visible_files, len(state.file_paths))
    
    # Display files
    state.file_texts.clear()
    for i, path in enumerate(state.file_paths[start_idx:end_idx]):
        y = 1 - (i + 1) * (1.0 / (state.visible_files + 1))
        txt = state.ax_filelist.text(0.05, y, os.path.basename(path)[:30] + '...' if len(os.path.basename(path)) > 30 else os.path.basename(path), 
                              transform=state.ax_filelist.transAxes, fontsize=7, 
                              verticalalignment='top', picker=True)
        txt._file_index = start_idx + i  # Store the actual file index
        state.file_texts.append(txt)
    
    # Show scroll position indicator
    if len(state.file_paths) > state.visible_files:
        position_text = f"[{start_idx+1}-{end_idx} of {len(state.file_paths)}]"
        state.ax_filelist.text(0.98, 0.02, position_text, transform=state.ax_filelist.transAxes, 
                       fontsize=6, ha='right', va='bottom', color='gray')
    
    plt.draw()

def on_open(event):
    """Open new hydrophone data files"""
    new_paths = filedialog.askopenfilenames(filetypes=[('Text', '*.txt')])
    if new_paths:
        plt.close(state.fig)
        # The setup_viewer function will be called from main with the new paths
        from main import setup_viewer
        setup_viewer(list(new_paths))

def on_save_project(event):
    """Save the current project to a file"""
    save_path = filedialog.asksaveasfilename(defaultextension=".hproj", 
                                           filetypes=[("Hydrophone Project", "*.hproj")])
    if not save_path:
        return
    state.save_project(save_path)

def on_load_project(event):
    """Load a project from a file"""
    load_path = filedialog.askopenfilename(filetypes=[("Hydrophone Project", "*.hproj")])
    if not load_path:
        return
    
    loaded_state = state.load_project(load_path)
    if not loaded_state:
        add_log_entry("Error loading project")
        return
    
    # Close current figure and setup viewer with new file paths
    plt.close(state.fig)
    
    # The setup_viewer function will be called from main
    from main import setup_viewer
    setup_viewer(loaded_state["file_paths"])
    
    # Apply loaded state
    if state.spec_img and "gain" in loaded_state:
        state.spec_img.set_clim(*loaded_state["gain"])
    
    # Update displays
    update_log_display()
    
    # If a position was saved, restore it
    if "click_index" in loaded_state and loaded_state["click_index"] is not None:
        update_fft(loaded_state["click_index"], state.freqs_global, state.data_global)
        idx = loaded_state["click_index"]
        state.spec_click_line = state.ax_spec.axvline(idx, color='white', linewidth=1)
        time_str = state.time_labels_all[idx]
        display_time = time_str[:5] if time_str != "GAP" else "GAP"
        state.spec_click_text = state.ax_spec.text(idx, 0, display_time,
                                     transform=blended_transform_factory(state.ax_spec.transData, state.ax_spec.transAxes),
                                     color='white', rotation=90, va='top', ha='center', clip_on=False)
    
    # If frequency markers were saved, restore them
    if "freq_markers" in loaded_state:
        # Import here to avoid circular import
        from visualization import update_marker
        for i, freq in enumerate(loaded_state["freq_markers"]):
            if freq is not None:
                update_marker(i, freq)

def on_view_debug_logs(event):
    """Open the folder containing debug logs"""
    current_dir = os.getcwd()
    if platform.system() == "Windows":
        os.startfile(current_dir)
    elif platform.system() == "Darwin":  # macOS
        subprocess.Popen(["open", current_dir])
    else:  # Linux
        subprocess.Popen(["xdg-open", current_dir])
    
    add_log_entry("Opened debug logs folder")

def on_timeline_hover(event):
    """Handle hover events on the audio timeline"""
    if state.ax_audio_timeline and state.audio_segments and event.inaxes == state.ax_audio_timeline:
        x = event.xdata
        if x is None:
            return
        
        # Check if hovering over an audio segment
        for i, (start_time, end_time) in enumerate(state.audio_segments):
            if start_time <= x <= end_time:
                # Show tooltip with file info
                if i < len(state.audio_file_info):
                    info = state.audio_file_info[i]
                    tooltip_text = f"File: {os.path.basename(info['path'])}\n"
                    tooltip_text += f"Duration: {info['duration']:.1f}s\n"
                    tooltip_text += f"Time: {info['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    # Check if tooltip already exists
                    for txt in state.ax_audio_timeline.texts:
                        if hasattr(txt, 'is_tooltip'):
                            txt.remove()
                    
                    # Create tooltip
                    tooltip = state.ax_audio_timeline.text(
                        x, 1.5, tooltip_text,
                        transform=blended_transform_factory(state.ax_audio_timeline.transData, state.ax_audio_timeline.transAxes),
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='khaki', alpha=0.8),
                        ha='center', va='bottom', fontsize=8
                    )
                    tooltip.is_tooltip = True
                    plt.draw()
                    return
        
        # Remove tooltip if not hovering over a segment
        for txt in state.ax_audio_timeline.texts:
            if hasattr(txt, 'is_tooltip'):
                txt.remove()
                plt.draw()

def update_marker(n, xpos):
    """Update frequency marker at position xpos"""
    from visualization import update_marker as viz_update_marker
    viz_update_marker(n, xpos)

def fix_spectrogram(event=None):
    """Fix the spectrogram display (reset button handler)"""
    from visualization import fix_spectrogram as viz_fix_spectrogram
    viz_fix_spectrogram()
    add_log_entry("Reset spectrogram display")

def setup_event_handlers(figure):
    """Set up all event handlers for the given figure"""
    # Store the figure in state
    state.fig = figure
    
    # Connect mouse event handlers
    figure.canvas.mpl_connect('button_press_event', on_spec_click)
    figure.canvas.mpl_connect('button_press_event', on_click)
    figure.canvas.mpl_connect('button_press_event', on_nav_press)
    figure.canvas.mpl_connect('motion_notify_event', on_nav_motion)
    figure.canvas.mpl_connect('button_release_event', on_nav_release)
    figure.canvas.mpl_connect('scroll_event', on_nav_scroll)
    
    # Connect keyboard event handlers
    figure.canvas.mpl_connect('key_press_event', on_key_press)
    figure.canvas.mpl_connect('key_release_event', on_key_release)
    figure.canvas.mpl_connect('key_press_event', on_key_press_audio)
    
    # Connect other event handlers
    figure.canvas.mpl_connect('pick_event', on_pick)
    
    # Timeline hover events are connected in UI components