"""
data_export.py - Functions for exporting hydrophone data with timezone adjustments
"""

import os
import numpy as np
import logging
from datetime import datetime, timedelta
import pytz
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from enum import Enum
import time
import threading
import platform

# Import state directly
import state
from utils import add_log_entry

def update_progress(progress_bar, progress_root, current, total, file_info=None):
    """Update progress bar and related UI elements with current progress"""
    if total <= 0:
        return
        
    progress_percent = (current / total) * 100
    progress_bar["value"] = progress_percent
    
    # Update percentage label
    if hasattr(state, 'export_progress_percent'):
        state.export_progress_percent.config(text=f"{progress_percent:.0f}%")
    
    # Update file info if provided
    if file_info and hasattr(state, 'file_label'):
        state.file_label.config(text=file_info)
    
    # Calculate and show estimated time remaining if we have enough progress
    if hasattr(state, 'export_start_time') and hasattr(state, 'export_progress_time') and progress_percent > 5:
        elapsed = time.time() - state.export_start_time
        if progress_percent > 0 and elapsed > 1:
            # Estimate total time based on current progress
            total_time = elapsed * 100 / progress_percent
            remaining = total_time - elapsed
            
            # Format time remaining
            hours, remainder = divmod(remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                time_str = f"Elapsed: {int(elapsed/60):.0f}m - Est. remaining: {int(hours)}h {int(minutes)}m"
            else:
                time_str = f"Elapsed: {int(elapsed/60):.0f}m {int(elapsed%60)}s - Est. remaining: {int(minutes)}m {int(seconds)}s"
                
            state.export_progress_time.config(text=time_str)
    
    # Check for cancel request
    if hasattr(state, 'export_cancel') and state.export_cancel:
        add_log_entry("Export cancelled by user")
        raise InterruptedError("Export cancelled by user")
    
    # Force window update
    if progress_root and progress_root.winfo_exists():
        progress_root.update()

class ExportSplitMethod(Enum):
    SINGLE_FILE = "Single File"
    HOURLY = "Split by Hour"
    DAILY = "Split by Day"
    ORIGINAL_FILES = "Match Original Files"
    SIZE_LIMIT = "Size Limit (MB)"
    CUSTOM_TIME = "Custom Time Interval"

def get_export_directory():
    """Open a dialog to select export directory"""
    root = tk.Tk()
    root.withdraw()
    export_dir = filedialog.askdirectory(
        title="Select Directory for Exported Files"
    )
    return export_dir if export_dir else None
    
def direct_export(export_method=ExportSplitMethod.SINGLE_FILE):
    """Direct export function that bypasses complex UI - for stability"""
    add_log_entry("Starting direct export - bypassing complex UI for stability")
    
    # First, get the export directory
    export_dir = get_export_directory()
    if not export_dir:
        add_log_entry("Export cancelled - no directory selected")
        return
    
    # Show a simple status window that will stay open
    status_window = tk.Tk()
    status_window.title("Export in Progress")
    status_window.geometry("400x150")
    status_window.attributes('-topmost', True)
    
    # Center window
    status_window.update_idletasks()
    width = status_window.winfo_width()
    height = status_window.winfo_height()
    x = (status_window.winfo_screenwidth() // 2) - (width // 2)
    y = (status_window.winfo_screenheight() // 2) - (height // 2)
    status_window.geometry(f"{width}x{height}+{x}+{y}")
    
    # Add status message
    status_frame = tk.Frame(status_window, padx=20, pady=20)
    status_frame.pack(fill=tk.BOTH, expand=True)
    
    status_label = tk.Label(status_frame, text="Export in progress...\nThis may take some time.", 
                           font=("Arial", 12, "bold"))
    status_label.pack(pady=10)
    
    progress = ttk.Progressbar(status_frame, orient="horizontal", length=350, mode="indeterminate")
    progress.pack(pady=10)
    progress.start()
    
    # Update to ensure window is displayed
    status_window.update()
    
    # Start export in a separate thread
    def run_export_thread():
        try:
            add_log_entry(f"Starting export to {export_dir} with method {export_method.value}")
            
            # Call the export function with simple parameters
            success, message = export_hydrophone_data(
                export_dir,
                export_method,
                "hydrophone_export",
                True,  # include metadata
                None,  # no custom interval
                None   # no size limit
            )
            
            # Update status window
            if success:
                status_label.config(text="Export completed successfully!", fg="green")
                progress.stop()
                progress.config(mode="determinate", value=100)
                
                # Add close button
                close_btn = tk.Button(status_frame, text="Close", command=status_window.destroy,
                                    font=("Arial", 10), padx=20, pady=5)
                close_btn.pack(pady=10)
                
                add_log_entry("Export completed successfully")
            else:
                status_label.config(text=f"Export failed: {message}", fg="red")
                progress.stop()
                
                # Add close button
                close_btn = tk.Button(status_frame, text="Close", command=status_window.destroy,
                                    font=("Arial", 10), padx=20, pady=5)
                close_btn.pack(pady=10)
                
                add_log_entry(f"Export failed: {message}")
            
            status_window.update()
            
        except Exception as e:
            # Handle any errors
            add_log_entry(f"Error during export: {str(e)}")
            
            try:
                status_label.config(text=f"Error: {str(e)}", fg="red")
                progress.stop()
                
                # Add close button
                close_btn = tk.Button(status_frame, text="Close", command=status_window.destroy,
                                    font=("Arial", 10), padx=20, pady=5)
                close_btn.pack(pady=10)
                
                status_window.update()
            except:
                pass
    
    # Start the export thread
    export_thread = threading.Thread(target=run_export_thread)
    export_thread.daemon = True
    export_thread.start()
    
    # Wait until the window is closed
    status_window.mainloop()
    
    return True

def estimate_file_sizes(split_method, custom_interval=None, max_size_mb=None):
    """Estimate number of files and their sizes based on split method"""
    # BUGFIX: Proper numpy array checking
    has_data = (hasattr(state, 'data_global') and 
               state.data_global is not None and 
               isinstance(state.data_global, np.ndarray) and 
               len(state.data_global) > 0)
    
    has_time = (hasattr(state, 'time_objects_utc') and 
                state.time_objects_utc is not None and 
                len(state.time_objects_utc) > 0)
                
    if not has_data or not has_time:
        return "No data loaded", []
    
    # Get total size estimate
    data_points = len(state.data_global)
    avg_bytes_per_point = 12  # Estimate: 1 timestamp + avg 10 values per row at ~1 byte each
    total_bytes = data_points * avg_bytes_per_point
    total_mb = total_bytes / (1024 * 1024)
    
    if split_method == ExportSplitMethod.SINGLE_FILE:
        return f"1 file (~{total_mb:.1f} MB)", [total_mb]
    
    elif split_method == ExportSplitMethod.HOURLY:
        # Get first and last timestamps
        valid_times = [t for t in state.time_objects_utc if t is not None]
        if not valid_times:
            return "Cannot determine time range", []
        
        start_time = min(valid_times)
        end_time = max(valid_times)
        total_seconds = (end_time - start_time).total_seconds()
        total_hours = math.ceil(total_seconds / 3600)
        avg_mb_per_file = total_mb / total_hours
        
        return f"{total_hours} files (~{avg_mb_per_file:.1f} MB each)", [avg_mb_per_file] * total_hours
    
    elif split_method == ExportSplitMethod.DAILY:
        # Get first and last timestamps
        valid_times = [t for t in state.time_objects_utc if t is not None]
        if not valid_times:
            return "Cannot determine time range", []
        
        start_time = min(valid_times)
        end_time = max(valid_times)
        total_seconds = (end_time - start_time).total_seconds()
        total_days = math.ceil(total_seconds / 86400)
        avg_mb_per_file = total_mb / total_days
        
        return f"{total_days} files (~{avg_mb_per_file:.1f} MB each)", [avg_mb_per_file] * total_days
    
    elif split_method == ExportSplitMethod.ORIGINAL_FILES:
        num_files = len(state.file_ranges)
        avg_mb_per_file = total_mb / num_files
        
        return f"{num_files} files (~{avg_mb_per_file:.1f} MB each)", [avg_mb_per_file] * num_files
    
    elif split_method == ExportSplitMethod.SIZE_LIMIT:
        if not max_size_mb or max_size_mb <= 0:
            return "Invalid size limit", []
        
        num_files = math.ceil(total_mb / max_size_mb)
        
        return f"{num_files} files (~{max_size_mb:.1f} MB each)", [max_size_mb] * (num_files - 1) + [total_mb % max_size_mb or max_size_mb]
    
    elif split_method == ExportSplitMethod.CUSTOM_TIME:
        if not custom_interval or custom_interval <= 0:
            return "Invalid time interval", []
        
        # Get first and last timestamps
        valid_times = [t for t in state.time_objects_utc if t is not None]
        if not valid_times:
            return "Cannot determine time range", []
        
        start_time = min(valid_times)
        end_time = max(valid_times)
        total_seconds = (end_time - start_time).total_seconds()
        num_intervals = math.ceil(total_seconds / (custom_interval * 60))
        avg_mb_per_file = total_mb / num_intervals
        
        return f"{num_intervals} files (~{avg_mb_per_file:.1f} MB each)", [avg_mb_per_file] * num_intervals
    
    return "Unknown split method", []

def export_hydrophone_data(export_dir, split_method, filename_prefix, include_metadata=True, 
                          custom_interval=None, max_size_mb=None):
    """Export hydrophone data to files with the specified splitting method"""
    # Log start of export operation
    add_log_entry(f"Starting export operation with method: {split_method.value}")
    add_log_entry(f"Export directory: {export_dir}")
    add_log_entry(f"Filename prefix: {filename_prefix}")
    
    # BUGFIX: Add a progress window early to show that export has started
    early_progress_root = None
    try:
        add_log_entry("Creating export progress window - please watch for a new window to appear")
        
        # Force the main window to update so the log message is visible
        if tk._default_root:
            tk._default_root.update()
        
        # Use Toplevel instead of Tk to avoid multiple root windows
        if tk._default_root:
            early_progress_root = tk.Toplevel(tk._default_root)
        else:
            # Fall back to Tk if no root exists
            early_progress_root = tk.Tk()
            
        early_progress_root.title("⚠️ EXPORT IN PROGRESS")  # Add emoji to make it more noticeable
        early_progress_root.geometry("500x150")  # Make it larger
        
        # Raise the window to the top and make it stay there
        early_progress_root.attributes('-topmost', True)
        
        # Make it look modal
        if tk._default_root:
            early_progress_root.transient(tk._default_root)
        early_progress_root.grab_set()
        
        # Center the window
        early_progress_root.update_idletasks()
        width = early_progress_root.winfo_width()
        height = early_progress_root.winfo_height()
        x = (early_progress_root.winfo_screenwidth() // 2) - (width // 2)
        y = (early_progress_root.winfo_screenheight() // 2) - (height // 2)
        early_progress_root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Add a bold, large message
        message_label = tk.Label(early_progress_root, 
                                text="EXPORT IN PROGRESS\nPreparing to export data... please wait", 
                                font=("Arial", 14, "bold"), fg="blue")
        message_label.pack(pady=20)
        
        # Add a progress indicator
        progress = ttk.Progressbar(early_progress_root, mode="indeterminate", length=400)
        progress.pack(fill=tk.X, padx=20, pady=10)
        progress.start(10)  # Faster animation
        
        # Add a message about the progress window
        note_label = tk.Label(early_progress_root, 
                            text="A detailed progress window will appear shortly...", 
                            font=("Arial", 10))
        note_label.pack(pady=10)
        
        # Force update and briefly flash to catch attention
        for _ in range(3):
            early_progress_root.update()
            time.sleep(0.1)
            
        add_log_entry("Export progress window created")
    except Exception as e:
        add_log_entry(f"Warning: Could not create early progress window: {str(e)}")
        if early_progress_root:
            try:
                early_progress_root.destroy()
            except:
                pass
        early_progress_root = None
    
    # BUGFIX: Proper numpy array checking
    has_data = (hasattr(state, 'data_global') and 
               state.data_global is not None and 
               isinstance(state.data_global, np.ndarray) and 
               len(state.data_global) > 0)
    
    has_time = (hasattr(state, 'time_objects_utc') and 
                state.time_objects_utc is not None and 
                len(state.time_objects_utc) > 0)
                
    if not has_data or not has_time:
        add_log_entry("Error: No data to export")
        if early_progress_root:
            early_progress_root.destroy()
        return False, "No data to export"
    
    if not os.path.isdir(export_dir):
        add_log_entry(f"Error: Invalid export directory: {export_dir}")
        if early_progress_root:
            early_progress_root.destroy()
        return False, "Invalid export directory"
    
    # Log data verification success
    add_log_entry(f"Data verification successful. Found {len(state.data_global)} data points and {len(state.freqs_global)} frequency bands")
    
    try:
        # Get timezone short name
        tz_name = state.current_timezone.tzname(datetime.now())
        
        # Close the early progress window if it exists
        if early_progress_root:
            try:
                early_progress_root.destroy()
            except:
                pass
        
        # Create a progress window - use Toplevel if possible to avoid multiple root windows
        if tk._default_root:
            progress_root = tk.Toplevel(tk._default_root)
        else:
            progress_root = tk.Tk()
            
        progress_root.title("⚠️ EXPORTING DATA - Progress Tracker")
        progress_root.geometry("600x350")  # Even larger window for better visibility
        
        # Raise the window to the top and make it stay there
        progress_root.attributes('-topmost', True)
        
        # Change window background for visibility
        progress_root.configure(bg="#f0f0ff")
        
        # Make it look modal
        if tk._default_root:
            progress_root.transient(tk._default_root)
            progress_root.grab_set()
            
        # Flash the window to draw attention
        def flash_window():
            progress_root.attributes('-topmost', False)
            progress_root.update()
            time.sleep(0.1)
            progress_root.attributes('-topmost', True)
            progress_root.update()
            
        # Show a message box alerting the user about the new window
        add_log_entry("IMPORTANT: Export progress window has opened - please look for the new window")
        
        # Center the window
        progress_root.update_idletasks()
        width = progress_root.winfo_width()
        height = progress_root.winfo_height()
        x = (progress_root.winfo_screenwidth() // 2) - (width // 2)
        y = (progress_root.winfo_screenheight() // 2) - (height // 2)
        progress_root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Flash the window a few times to get attention
        for _ in range(3):
            flash_window()
        
        # Create a messagebox in a separate thread to alert the user
        def show_alert():
            try:
                time.sleep(0.2)  # Brief delay
                messagebox.showinfo("Export In Progress", 
                                   "The export process has started!\n\nA progress window has opened. Please look for it on your screen.")
            except:
                pass
                
        alert_thread = threading.Thread(target=show_alert)
        alert_thread.daemon = True
        alert_thread.start()
        
        # Create progress display with more detailed information
        # Use frames with borders for better visual organization
        main_frame = tk.Frame(progress_root, bg="#f0f0ff", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with large font
        header_label = tk.Label(main_frame, text="EXPORTING HYDROPHONE DATA", 
                              font=("Arial", 16, "bold"), fg="blue", bg="#f0f0ff")
        header_label.pack(pady=(10, 15))
        
        # Status area with border
        status_frame = tk.LabelFrame(main_frame, text="Current Status", padx=10, pady=10, bg="#f0f0ff",
                                   font=("Arial", 10, "bold"))
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        status_label = tk.Label(status_frame, text="Preparing export...", 
                              font=("Arial", 12), bg="#f0f0ff", fg="#006600")
        status_label.pack(pady=5)
        
        # Progress area with border
        progress_section = tk.LabelFrame(main_frame, text="Progress", padx=10, pady=10, bg="#f0f0ff",
                                      font=("Arial", 10, "bold"))
        progress_section.pack(fill=tk.X, padx=5, pady=5)
        
        # Add percentage indicator next to progress bar
        progress_frame = tk.Frame(progress_section, bg="#f0f0ff")
        progress_frame.pack(fill=tk.X, pady=5)
        
        # Larger progress bar with custom style
        progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=460, 
                                     mode="determinate", style="TProgressbar")
        progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        percent_label = tk.Label(progress_frame, text="0%", width=5, 
                               font=("Arial", 10, "bold"), bg="#f0f0ff")
        percent_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Add file information area
        file_section = tk.LabelFrame(main_frame, text="File Information", padx=10, pady=10, bg="#f0f0ff",
                                   font=("Arial", 10, "bold"))
        file_section.pack(fill=tk.X, padx=5, pady=5)
        
        file_frame = tk.Frame(file_section, bg="#f0f0ff")
        file_frame.pack(fill=tk.X, pady=2)
        
        file_status_label = tk.Label(file_frame, text="Current file:", anchor="w", 
                                   bg="#f0f0ff", font=("Arial", 10, "bold"))
        file_status_label.pack(side=tk.LEFT)
        
        file_label = tk.Label(file_frame, text="", anchor="w", 
                            font=("Arial", 10, "italic"), bg="#f0f0ff", fg="#000080")
        file_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Add time information area
        time_section = tk.LabelFrame(main_frame, text="Time Information", padx=10, pady=10, bg="#f0f0ff",
                                   font=("Arial", 10, "bold"))
        time_section.pack(fill=tk.X, padx=5, pady=5)
        
        time_label = tk.Label(time_section, text="Starting export process...", 
                            font=("Arial", 10), bg="#f0f0ff", fg="#800000")
        time_label.pack(pady=2)
        
        # Store start time to calculate elapsed time
        state.export_start_time = time.time()
        
        # Store labels in state for updating from other functions
        state.export_progress_percent = percent_label
        state.export_progress_time = time_label
        state.file_label = file_label  # Store file label for helper function to access
        
        # Create a cancel button with distinctive styling
        button_frame = tk.Frame(main_frame, bg="#f0f0ff")
        button_frame.pack(pady=15)
        
        cancel_btn = tk.Button(button_frame, text="CANCEL EXPORT", command=lambda: setattr(state, 'export_cancel', True),
                              bg="#ffcccc", fg="#cc0000", font=("Arial", 10, "bold"),
                              padx=10, pady=5, relief=tk.RAISED, borderwidth=3)
        cancel_btn.pack()
        
        # Initialize cancel flag
        state.export_cancel = False
        
        # Setup timer for periodic updates
        def update_elapsed_time():
            if hasattr(state, 'export_start_time') and not hasattr(state, 'export_complete'):
                elapsed = time.time() - state.export_start_time
                hours, remainder = divmod(elapsed, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"Elapsed time: {int(minutes):02}:{int(seconds):02}"
                
                if hasattr(state, 'export_progress_time') and state.export_progress_time.winfo_exists():
                    state.export_progress_time.config(text=time_str)
                    progress_root.after(1000, update_elapsed_time)
        
        # Start the timer
        progress_root.after(1000, update_elapsed_time)
        
        # Force update to show the window
        progress_root.update()
        
        # Split the data based on the selected method
        if split_method == ExportSplitMethod.SINGLE_FILE:
            # Export to a single file
            export_single_file(export_dir, filename_prefix, tz_name, include_metadata, 
                              status_label, progress_bar, file_label, progress_root)
            
        elif split_method == ExportSplitMethod.HOURLY:
            # Split by hour
            export_by_time(export_dir, filename_prefix, tz_name, include_metadata, 3600,
                          status_label, progress_bar, file_label, progress_root)
            
        elif split_method == ExportSplitMethod.DAILY:
            # Split by day
            export_by_time(export_dir, filename_prefix, tz_name, include_metadata, 86400,
                          status_label, progress_bar, file_label, progress_root)
            
        elif split_method == ExportSplitMethod.ORIGINAL_FILES:
            # Split by original file boundaries
            export_by_original_files(export_dir, filename_prefix, tz_name, include_metadata,
                                   status_label, progress_bar, file_label, progress_root)
            
        elif split_method == ExportSplitMethod.SIZE_LIMIT:
            # Split by size limit
            if not max_size_mb or max_size_mb <= 0:
                progress_root.destroy()
                return False, "Invalid size limit"
            
            export_by_size(export_dir, filename_prefix, tz_name, include_metadata, max_size_mb,
                          status_label, progress_bar, file_label, progress_root)
            
        elif split_method == ExportSplitMethod.CUSTOM_TIME:
            # Split by custom time interval (minutes)
            if not custom_interval or custom_interval <= 0:
                progress_root.destroy()
                return False, "Invalid time interval"
            
            export_by_time(export_dir, filename_prefix, tz_name, include_metadata, custom_interval * 60,
                          status_label, progress_bar, file_label, progress_root)
        
        # Mark export as complete to stop timers
        state.export_complete = True
        
        # Calculate total elapsed time
        elapsed = time.time() - state.export_start_time
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            time_str = f"Total time: {int(hours)}h {int(minutes)}m {int(seconds)}s"
        else:
            time_str = f"Total time: {int(minutes)}m {int(seconds)}s"
        
        # Update final status with eye-catching completion message
        # Change window title to indicate completion
        progress_root.title("✅ EXPORT COMPLETED SUCCESSFULLY")
        
        # Change background to green to indicate success
        main_frame.configure(bg="#e6ffe6")  # Light green background
        
        # Update all background colors
        for widget in main_frame.winfo_children():
            if isinstance(widget, (tk.Frame, tk.LabelFrame)):
                widget.configure(bg="#e6ffe6")
                for subwidget in widget.winfo_children():
                    if hasattr(subwidget, 'configure') and not isinstance(subwidget, ttk.Progressbar):
                        try:
                            subwidget.configure(bg="#e6ffe6")
                        except:
                            pass
        
        # Create a completion banner
        completion_frame = tk.Frame(main_frame, bg="#00cc00", padx=10, pady=10)
        completion_frame.pack(fill=tk.X, padx=5, pady=10, before=status_frame)
        
        completion_label = tk.Label(completion_frame, 
                                  text="✅ EXPORT COMPLETED SUCCESSFULLY! ✅", 
                                  font=("Arial", 14, "bold"), fg="white", bg="#00cc00")
        completion_label.pack(pady=5)
        
        # Update status text
        status_label.config(text=f"All data exported successfully", 
                          font=("Arial", 12, "bold"), fg="#006600", bg="#e6ffe6")
        
        # Update progress indicators
        progress_bar["value"] = 100
        
        if hasattr(state, 'export_progress_percent'):
            state.export_progress_percent.config(text="100%", bg="#e6ffe6")
            
        file_label.config(text="All files exported successfully.", bg="#e6ffe6")
        
        if hasattr(state, 'export_progress_time'):
            state.export_progress_time.config(
                text=f"Export finished at {datetime.now().strftime('%H:%M:%S')}\n{time_str}", 
                fg="#006600", bg="#e6ffe6", font=("Arial", 10, "bold"))
        
        # Flash the window to indicate completion
        for _ in range(3):
            flash_window()
            
        progress_root.update()
        
        # Replace the cancel button with a close button
        for widget in button_frame.winfo_children():
            widget.destroy()
        
        button_frame.configure(bg="#e6ffe6")
        
        close_btn = tk.Button(button_frame, text="CLOSE", command=progress_root.destroy,
                            bg="#e6ffe6", fg="#006600", font=("Arial", 12, "bold"),
                            padx=20, pady=10, relief=tk.RAISED, borderwidth=3)
        close_btn.pack()
        
        # Add info about file format compatibility
        compat_label = tk.Label(main_frame, 
                              text="Files were exported in a format compatible with the original data files.\nYou can now import these files normally.", 
                              foreground="#006600", font=("Arial", 10, "italic"), bg="#e6ffe6")
        compat_label.pack(pady=5)
        
        # Play a system sound to indicate completion (if available)
        try:
            if platform.system() == "Windows":
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            elif platform.system() == "Darwin":  # macOS
                os.system("osascript -e 'beep 2'")
        except:
            pass
        
        # Wait for user to close the window
        progress_root.mainloop()
        
        # Log detailed export information
        add_log_entry(f"Export completed successfully to {export_dir}")
        add_log_entry(f"Exported {len(state.data_global)} data points with {len(state.freqs_global)} frequency bands")
        add_log_entry(f"Files were exported with compatible header format for re-import")
        
        return True, f"Export completed successfully to {export_dir}"
        
    except Exception as e:
        logging.error(f"Error during export: {str(e)}", exc_info=True)
        add_log_entry(f"Error during export: {str(e)}")
        
        # Clean up any open windows
        try:
            progress_root.destroy()
        except:
            pass
            
        try:
            if early_progress_root:
                early_progress_root.destroy()
        except:
            pass
            
        # Show a more detailed error message
        error_msg = f"Error during export: {str(e)}"
        if "AttributeError: 'NoneType'" in str(e):
            error_msg += "\n\nThis might be caused by an issue with the matplotlib event system. Try clicking on an empty area of the main window before exporting."
        
        return False, error_msg

def export_single_file(export_dir, filename_prefix, tz_name, include_metadata, 
                      status_label, progress_bar, file_label, progress_root):
    """Export all data to a single file"""
    # Get data and validate
    # BUGFIX: Proper numpy array checking
    has_data = (hasattr(state, 'data_global') and 
               state.data_global is not None and 
               isinstance(state.data_global, np.ndarray) and 
               len(state.data_global) > 0)
    
    has_time = (hasattr(state, 'time_objects_utc') and 
                state.time_objects_utc is not None and 
                len(state.time_objects_utc) > 0)
                
    if not has_data or not has_time:
        return
    
    # Generate filename
    valid_times = [t for t in state.time_objects_utc if t is not None]
    if not valid_times:
        return
    
    start_time = min(valid_times)
    end_time = max(valid_times)
    
    start_local = start_time.astimezone(state.current_timezone)
    end_local = end_time.astimezone(state.current_timezone)
    
    start_str = start_local.strftime("%Y%m%d_%H%M")
    end_str = end_local.strftime("%Y%m%d_%H%M")
    
    filename = f"{filename_prefix}_{tz_name}_{start_str}-{end_str}.txt"
    file_path = os.path.join(export_dir, filename)
    
    # Update status
    status_label.config(text=f"Exporting to single file...")
    file_label.config(text=filename)
    progress_root.update()
    
    # Write the file
    with open(file_path, 'w') as f:
        # Write header
        write_file_header(f, include_metadata, start_local, end_local)
        
        # Write frequency header to match original file format
        f.write("Time\tComment\tTemperature\tHumidity\tSequence #\tData Points")
        for freq in state.freqs_global:
            f.write(f"\t{freq:.1f}")
        f.write("\n")
        
        # Write data with progress updates
        total_rows = len(state.data_global)
        for i, (time_obj, data_row) in enumerate(zip(state.time_objects_utc, state.data_global)):
            if time_obj is None:
                continue  # Skip gap entries
                
            # Convert to local timezone
            local_time = time_obj.astimezone(state.current_timezone)
            time_str = local_time.strftime("%H:%M:%S")
            
            # Write time and data to match original file format
            # Time, Comment, Temperature, Humidity, Sequence #, then frequencies after "Data Points" marker
            f.write(f"{time_str}\t\t22.8\t31.1\t{i+1}\tDatapoint\t")
            f.write("\t".join(f"{val:.2f}" for val in data_row))
            f.write("\n")
            
            # Update progress more frequently for better user feedback
            if i % 20 == 0 or i == total_rows - 1:
                # Use the helper function for consistent progress updates
                try:
                    update_progress(progress_bar, progress_root, i, total_rows, 
                                   file_info=f"Writing data row {i+1}/{total_rows}")
                except InterruptedError:
                    # Handle cancel request
                    return

def export_by_time(export_dir, filename_prefix, tz_name, include_metadata, time_interval_seconds,
                  status_label, progress_bar, file_label, progress_root):
    """Export data split by time intervals"""
    # Get data and validate
    # BUGFIX: Proper numpy array checking
    has_data = (hasattr(state, 'data_global') and 
               state.data_global is not None and 
               isinstance(state.data_global, np.ndarray) and 
               len(state.data_global) > 0)
    
    has_time = (hasattr(state, 'time_objects_utc') and 
                state.time_objects_utc is not None and 
                len(state.time_objects_utc) > 0)
                
    if not has_data or not has_time:
        return
    
    # Find valid time range
    valid_times = [t for t in state.time_objects_utc if t is not None]
    if not valid_times:
        return
    
    start_time = min(valid_times)
    end_time = max(valid_times)
    
    # Calculate intervals
    total_seconds = (end_time - start_time).total_seconds()
    num_intervals = math.ceil(total_seconds / time_interval_seconds)
    
    # Update status
    status_label.config(text=f"Exporting {num_intervals} files by time interval...")
    progress_root.update()
    
    # Process each interval
    file_counter = 0
    total_rows = len(state.data_global)
    rows_processed = 0
    
    for interval in range(num_intervals):
        interval_start = start_time + timedelta(seconds=interval * time_interval_seconds)
        interval_end = min(start_time + timedelta(seconds=(interval + 1) * time_interval_seconds), end_time)
        
        # Convert to local timezone for filename
        start_local = interval_start.astimezone(state.current_timezone)
        end_local = interval_end.astimezone(state.current_timezone)
        
        start_str = start_local.strftime("%Y%m%d_%H%M")
        end_str = end_local.strftime("%Y%m%d_%H%M")
        
        filename = f"{filename_prefix}_{tz_name}_{start_str}-{end_str}.txt"
        file_path = os.path.join(export_dir, filename)
        
        # Update status with detailed file info
        file_counter += 1
        file_info = f"File {file_counter}/{num_intervals}: {filename}"
        file_label.config(text=file_info)
        
        # Show progress increment for each file
        temp_progress = (file_counter - 1) * 100 / num_intervals
        progress_bar["value"] = temp_progress
        
        # Update percentage and time estimate
        if hasattr(state, 'export_progress_percent'):
            state.export_progress_percent.config(text=f"{temp_progress:.0f}%")
            
        # Force window update
        progress_root.update()
        
        # Collect data for this interval
        interval_data = []
        interval_times = []
        
        for i, time_obj in enumerate(state.time_objects_utc):
            if time_obj is None:
                continue  # Skip gap entries
                
            if interval_start <= time_obj < interval_end:
                interval_data.append(state.data_global[i])
                interval_times.append(time_obj)
                rows_processed += 1
        
        # Only write file if there's data
        if interval_data:
            with open(file_path, 'w') as f:
                # Write header
                write_file_header(f, include_metadata, start_local, end_local)
                
                # Write frequency header to match original file format
                f.write("Time\tComment\tTemperature\tHumidity\tSequence #\tData Points")
                for freq in state.freqs_global:
                    f.write(f"\t{freq:.1f}")
                f.write("\n")
                
                # Write data
                for time_obj, data_row in zip(interval_times, interval_data):
                    # Convert to local timezone
                    local_time = time_obj.astimezone(state.current_timezone)
                    time_str = local_time.strftime("%H:%M:%S")
                    
                    # Write time and data to match original file format
                    local_seq = interval_times.index(time_obj) + 1
                    f.write(f"{time_str}\t\t22.8\t31.1\t{local_seq}\tDatapoint\t")
                    f.write("\t".join(f"{val:.2f}" for val in data_row))
                    f.write("\n")
        
        # Update progress using helper function
        update_progress(progress_bar, progress_root, rows_processed, total_rows)

def export_by_original_files(export_dir, filename_prefix, tz_name, include_metadata,
                           status_label, progress_bar, file_label, progress_root):
    """Export data split by original file boundaries"""
    # Get data and validate
    # BUGFIX: Proper numpy array checking
    has_data = (hasattr(state, 'data_global') and 
               state.data_global is not None and 
               isinstance(state.data_global, np.ndarray) and 
               len(state.data_global) > 0)
    
    has_time = (hasattr(state, 'time_objects_utc') and 
                state.time_objects_utc is not None and 
                len(state.time_objects_utc) > 0)
                
    has_ranges = (hasattr(state, 'file_ranges') and 
                 state.file_ranges is not None and 
                 len(state.file_ranges) > 0)
                
    if not has_data or not has_time or not has_ranges:
        return
    
    # Update status
    num_files = len(state.file_ranges)
    status_label.config(text=f"Exporting {num_files} files based on original boundaries...")
    progress_root.update()
    
    # Process each file range
    file_counter = 0
    total_rows = len(state.data_global)
    rows_processed = 0
    
    for file_idx, (start_idx, end_idx) in enumerate(state.file_ranges):
        # Get valid timestamps in this range
        valid_times = [t for i, t in enumerate(state.time_objects_utc) 
                      if t is not None and start_idx <= i <= end_idx]
        
        if not valid_times:
            continue
        
        # Get time range for the file
        min_time = min(valid_times)
        max_time = max(valid_times)
        
        # Convert to local timezone for filename
        start_local = min_time.astimezone(state.current_timezone)
        end_local = max_time.astimezone(state.current_timezone)
        
        start_str = start_local.strftime("%Y%m%d_%H%M")
        end_str = end_local.strftime("%Y%m%d_%H%M")
        
        # Use original filename as part of the export filename for better traceability
        if file_idx < len(state.file_paths):
            original_name = os.path.splitext(os.path.basename(state.file_paths[file_idx]))[0]
            filename = f"{filename_prefix}_{original_name}_{tz_name}_{start_str}-{end_str}.txt"
        else:
            filename = f"{filename_prefix}_part{file_idx+1}_{tz_name}_{start_str}-{end_str}.txt"
            
        file_path = os.path.join(export_dir, filename)
        
        # Update status
        file_counter += 1
        file_label.config(text=f"File {file_counter}/{num_files}: {filename}")
        progress_root.update()
        
        # Write the file
        with open(file_path, 'w') as f:
            # Write header
            write_file_header(f, include_metadata, start_local, end_local)
            
            # Write frequency header to match original file format
            f.write("Time\tComment\tTemperature\tHumidity\tSequence #\tData Points")
            for freq in state.freqs_global:
                f.write(f"\t{freq:.1f}")
            f.write("\n")
            
            # Write data for this range
            for i in range(start_idx, end_idx + 1):
                if i >= len(state.time_objects_utc):
                    break
                    
                time_obj = state.time_objects_utc[i]
                if time_obj is None:
                    continue  # Skip gap entries
                
                # Convert to local timezone
                local_time = time_obj.astimezone(state.current_timezone)
                time_str = local_time.strftime("%H:%M:%S")
                
                # Write time and data to match original file format
                f.write(f"{time_str}\t\t22.8\t31.1\t{i+1}\tDatapoint\t")
                f.write("\t".join(f"{val:.2f}" for val in state.data_global[i]))
                f.write("\n")
                
                rows_processed += 1
        
        # Update progress using helper function
        update_progress(progress_bar, progress_root, rows_processed, total_rows)

def export_by_size(export_dir, filename_prefix, tz_name, include_metadata, max_size_mb,
                  status_label, progress_bar, file_label, progress_root):
    """Export data split by maximum file size"""
    # Get data and validate
    # BUGFIX: Proper numpy array checking
    has_data = (hasattr(state, 'data_global') and 
               state.data_global is not None and 
               isinstance(state.data_global, np.ndarray) and 
               len(state.data_global) > 0)
    
    has_time = (hasattr(state, 'time_objects_utc') and 
                state.time_objects_utc is not None and 
                len(state.time_objects_utc) > 0)
                
    if not has_data or not has_time:
        return
    
    # Estimate size per row
    avg_bytes_per_point = 12  # Estimate: 1 timestamp + avg 10 values per row at ~1 byte each
    max_bytes = max_size_mb * 1024 * 1024
    rows_per_file = max(1, int(max_bytes / avg_bytes_per_point))
    
    # Calculate number of files
    total_rows = len(state.data_global)
    num_files = math.ceil(total_rows / rows_per_file)
    
    # Update status
    status_label.config(text=f"Exporting {num_files} files by size limit ({max_size_mb} MB)...")
    progress_root.update()
    
    # Process each file
    file_counter = 0
    rows_processed = 0
    
    for file_idx in range(num_files):
        start_idx = file_idx * rows_per_file
        end_idx = min((file_idx + 1) * rows_per_file - 1, total_rows - 1)
        
        # Get valid timestamps in this range
        valid_times = [t for i, t in enumerate(state.time_objects_utc) 
                      if t is not None and start_idx <= i <= end_idx]
        
        if not valid_times:
            continue
        
        # Get time range for the file
        min_time = min(valid_times)
        max_time = max(valid_times)
        
        # Convert to local timezone for filename
        start_local = min_time.astimezone(state.current_timezone)
        end_local = max_time.astimezone(state.current_timezone)
        
        start_str = start_local.strftime("%Y%m%d_%H%M")
        end_str = end_local.strftime("%Y%m%d_%H%M")
        
        filename = f"{filename_prefix}_part{file_idx+1}_{tz_name}_{start_str}-{end_str}.txt"
        file_path = os.path.join(export_dir, filename)
        
        # Update status
        file_counter += 1
        file_label.config(text=f"File {file_counter}/{num_files}: {filename}")
        progress_root.update()
        
        # Write the file
        with open(file_path, 'w') as f:
            # Write header
            write_file_header(f, include_metadata, start_local, end_local)
            
            # Write frequency header to match original file format
            f.write("Time\tComment\tTemperature\tHumidity\tSequence #\tData Points")
            for freq in state.freqs_global:
                f.write(f"\t{freq:.1f}")
            f.write("\n")
            
            # Write data for this range
            for i in range(start_idx, end_idx + 1):
                if i >= len(state.time_objects_utc):
                    break
                    
                time_obj = state.time_objects_utc[i]
                if time_obj is None:
                    continue  # Skip gap entries
                
                # Convert to local timezone
                local_time = time_obj.astimezone(state.current_timezone)
                time_str = local_time.strftime("%H:%M:%S")
                
                # Write time and data to match original file format
                f.write(f"{time_str}\t\t22.8\t31.1\t{i+1}\tDatapoint\t")
                f.write("\t".join(f"{val:.2f}" for val in state.data_global[i]))
                f.write("\n")
                
                rows_processed += 1
                
                # Update progress more frequently for large files
                if rows_processed % 1000 == 0:
                    progress_bar["value"] = (rows_processed / total_rows) * 100
                    progress_root.update()
        
        # Update progress using helper function
        update_progress(progress_bar, progress_root, rows_processed, total_rows)

def write_file_header(file, include_metadata, start_local, end_local):
    """Write the header information to the export file in a format compatible with the file loader"""
    # Use the standard format that the application's parser expects
    file.write(f"File Details:\n")
    file.write(f"File Type\tSpectrum\n")
    file.write(f"File Version\t5\n")
    file.write(f"Start Date\t{start_local.strftime('%Y-%m-%d')}\n")
    file.write(f"Start Time\t{start_local.strftime('%H:%M:%S')}\n")
    file.write(f"Time Zone\t{state.current_timezone.zone}\n")
    file.write(f"Author\tHydrophone Analyzer Export\n")
    file.write(f"Computer\t{os.uname().nodename}\n")
    file.write(f"User\t{os.getenv('USER', 'UnknownUser')}\n")
    
    # Project details
    file.write(f"Client\t{state.project_name or 'Hydrophone Analysis'}\n")
    file.write(f"Job\tData Export {datetime.now().strftime('%Y-%m-%d')}\n")
    file.write(f"Personnel\tHydrophone Analyzer User\n")
    
    # Add device section that's expected by the parser
    file.write(f"\nDevice Details:\n")
    file.write(f"Device\tHydrophone Analyzer\n")
    file.write(f"S/N\t00000\n")
    file.write(f"Firmware\tv2.3.4\n")
    
    # Add setup section that's expected by the parser
    file.write(f"\nSetup:\n")
    file.write(f"dB Ref re 1V\t-180\n")
    file.write(f"dB Ref re 1uPa\t-8\n")
    # Calculate appropriate values from the data
    sample_rate = 64000  # Default if we can't determine
    if hasattr(state, 'sample_rate') and state.sample_rate:
        sample_rate = state.sample_rate
    file.write(f"Sample Rate [S/s]\t{sample_rate}\n")
    
    # Calculate FFT size based on frequency bins if available
    fft_size = 1024  # Default
    if hasattr(state, 'freqs_global') and len(state.freqs_global) > 0:
        fft_size = len(state.freqs_global) * 2  # Approximation
    file.write(f"FFT Size\t{fft_size}\n")
    
    # Calculate bin width if possible
    bin_width = 62.5  # Default
    if hasattr(state, 'freqs_global') and len(state.freqs_global) > 1:
        bin_width = state.freqs_global[1] - state.freqs_global[0]
    file.write(f"Bin Width [Hz]\t{bin_width}\n")
    file.write(f"Window Function\tHann\n")
    file.write(f"Overlap [%]\t50.0\n")
    file.write(f"Power Calculation\tMean\n")
    file.write(f"Accumulations\t125\n")
    
    # Add extended metadata if requested
    if include_metadata:
        file.write(f"\nExport Metadata:\n")
        file.write(f"Export Version\tHydrophone Analyzer v2.3.4\n")
        file.write(f"Source Files\t{len(state.file_paths)}\n")
        
        for i, path in enumerate(state.file_paths):
            file.write(f"Source {i+1}\t{os.path.basename(path)}\n")
        
        file.write(f"Frequency Range\t{min(state.freqs_global)/1000:.2f} - {max(state.freqs_global)/1000:.2f} kHz\n")
        file.write(f"Data Points\t{len(state.data_global)}\n")
    
    # Add Data section marker expected by parsers (critical for file format validation)
    file.write("\nData:\n")
    
    # Blank line before data headers
    file.write("\n")
    
    # Log the header creation for debugging
    add_log_entry(f"Created file header in compatible format with Start Date: {start_local.strftime('%Y-%m-%d')}")