"""
state.py - Global state management for the hydrophone visualization program

This module provides a central place for storing application state.
"""

import numpy as np
import datetime
import pickle
import logging
import os
import pytz
import matplotlib.pyplot as plt

# === Data Storage ===
# Raw data storage
data_global = None  # FFT data
freqs_global = None  # Frequency values
file_paths = []  # Loaded file paths
file_ranges = []  # Start/end indices for each file
time_labels_all = []  # Time labels for each FFT
timestamp_all = []  # Timestamp objects for each FFT
current_timezone = pytz.UTC  # Default timezone

# Audio data
audio_data = None  # Raw audio samples
audio_sample_rate = 44100  # Default sample rate
audio_segments = []  # Time segments with audio
audio_file_info = []  # Information about loaded audio files
audio_volume = 0.5  # Default volume (0-1)
audio_playing = False  # Flag for audio playback
audio_stop_flag = False  # Flag to request audio stop
audio_finished = False  # Flag for playback completion
audio_thread = None  # Thread for audio playback
audio_stream = None  # Audio stream for playback
audio_buffer = None  # Audio buffer for streaming
audio_position = None  # Current position in audio buffer
audio_playback_line = None  # Indicator line on spectrogram
audio_playback_line_timeline = None  # Indicator line on timeline

# Visualization state
spec_img = None  # Spectrogram image
nav_spec_img = None  # Navigation spectrogram image
time_zoom_start = 0  # Current zoom start index
time_zoom_end = 0  # Current zoom end index
nav_dragging = False  # Flag for navigation drag
nav_resizing = False  # Flag for navigation resize
nav_drag_start = None  # Starting point for drag
nav_resize_edge = None  # Which edge is being resized ('left' or 'right')
nav_box = None  # Navigation box on the nav spectrogram
spec_click_line = None  # Vertical line at clicked position
spec_click_text = None  # Text at clicked position
selected_range = None  # Selected time range (start, end)
fft_patch = None  # Highlighting patch for selected range
file_patch = None  # Highlighting patch for selected file
file_texts = []  # Text objects for file list
fft_ymin = 0  # FFT y-axis minimum
fft_ymax = 120  # FFT y-axis maximum
freq_markers = [(None, None, 0, None, None), (None, None, 1, None, None)]  # Frequency markers: (vline, text, index, freq, hline)

# Tab system state
tab_manager = None  # Tab manager instance

# UI components
file_scroll_position = 0  # Scroll position for file list
visible_files = 12  # Number of visible files in the list
scroll_position = 0  # Scroll position for log display
log_entries = []  # Log entries
info_labels = {}  # Labels for info display

# Axes objects
fig = None  # Main figure
ax_spec = None  # Main spectrogram axes
ax_nav_spec = None  # Navigation spectrogram axes
ax_fft = None  # FFT display axes
ax_audio_timeline = None  # Audio timeline axes
ax_audio_controls = None  # Audio controls axes
ax_audio_play = None  # Audio play button axes
ax_audio_visualizer = None  # Audio waveform visualizer axes
ax_vu_meter = None  # VU meter axes
ax_time_display = None  # Time display axes
ax_filelist = None  # File list axes
ax_log = None  # Log display axes
ax_info = None  # Info display axes
ax_status = None  # Status bar axes

# Button objects
btn_audio_play = None  # Audio play/stop button
btn_timezone = None  # Timezone button
gain_slider = None  # Gain slider

# Dropdown objects
timezone_dropdown = None  # Timezone dropdown

# === State Management Functions ===
def save_project(filepath):
    """Save the current state to a file"""
    try:
        # Create a state dictionary with essential data
        state_dict = {
            "file_paths": file_paths,
            "time_zoom": (time_zoom_start, time_zoom_end),
            "gain": gain_slider.val if gain_slider else (0, 1),
            "current_timezone": current_timezone.zone if hasattr(current_timezone, 'zone') else 'UTC',
        }
        
        # Add click index if available
        if spec_click_line:
            state_dict["click_index"] = int(spec_click_line.get_xdata()[0])
        
        # Add frequency markers if set
        marker_freqs = []
        for _, _, _, freq, _ in freq_markers:
            marker_freqs.append(freq)
        state_dict["freq_markers"] = marker_freqs
        
        # Save to file
        with open(filepath, 'wb') as f:
            pickle.dump(state_dict, f)
            
        logging.info(f"Project saved to {filepath}")
        return True
    
    except Exception as e:
        logging.error(f"Error saving project: {e}", exc_info=True)
        return False

def load_project(filepath):
    """Load state from a file"""
    try:
        with open(filepath, 'rb') as f:
            state_dict = pickle.load(f)
            
        logging.info(f"Project loaded from {filepath}")
        return state_dict
    
    except Exception as e:
        logging.error(f"Error loading project: {e}", exc_info=True)
        return None

def reset_state():
    """Reset state to initial values"""
    global data_global, freqs_global, file_paths, file_ranges, time_labels_all
    global timestamp_all, audio_data, audio_sample_rate, audio_segments
    global audio_file_info, audio_volume, audio_playing, audio_stop_flag
    global audio_finished, audio_thread, audio_playback_line
    global audio_playback_line_timeline, spec_img, nav_spec_img
    global time_zoom_start, time_zoom_end, nav_dragging, nav_resizing
    global nav_drag_start, nav_resize_edge, nav_box, spec_click_line
    global spec_click_text, selected_range, fft_patch, file_patch
    global file_texts, log_entries, info_labels, fig, ax_spec
    global ax_nav_spec, ax_fft, ax_audio_timeline, ax_audio_controls
    global ax_audio_play, ax_audio_visualizer, ax_vu_meter, ax_time_display
    global ax_filelist, ax_log, ax_info, ax_status, btn_audio_play
    global btn_timezone, gain_slider, timezone_dropdown
    
    # Reset data storage
    data_global = None
    freqs_global = None
    file_paths = []
    file_ranges = []
    time_labels_all = []
    timestamp_all = []
    current_timezone = pytz.UTC
    
    # Reset audio data
    audio_data = None
    audio_sample_rate = 44100
    audio_segments = []
    audio_file_info = []
    audio_volume = 0.5
    audio_playing = False
    audio_stop_flag = False
    audio_finished = False
    audio_thread = None
    audio_playback_line = None
    audio_playback_line_timeline = None
    
    # Reset visualization state
    spec_img = None
    nav_spec_img = None
    time_zoom_start = 0
    time_zoom_end = 0
    nav_dragging = False
    nav_resizing = False
    nav_drag_start = None
    nav_resize_edge = None
    nav_box = None
    spec_click_line = None
    spec_click_text = None
    selected_range = None
    fft_patch = None
    file_patch = None
    file_texts = []
    fft_ymin = 0
    fft_ymax = 120
    freq_markers = [(None, None, 0, None, None), (None, None, 1, None, None)]
    
    # Reset UI state
    file_scroll_position = 0
    visible_files = 12
    scroll_position = 0
    log_entries = []
    info_labels = {}
    
    # Note: We don't reset axes and UI component references here
    # Those will be recreated when setting up the UI

def set_window_title(title):
    """Set the window title"""
    if fig and hasattr(fig.canvas, 'manager') and fig.canvas.manager:
        try:
            fig.canvas.manager.set_window_title(title)
        except Exception as e:
            logging.error(f"Error setting window title: {e}")

def get_project_metadata():
    """Get metadata about the current project"""
    metadata = {
        "file_count": len(file_paths),
        "data_points": len(data_global) if data_global is not None else 0,
        "has_audio": audio_data is not None,
        "timezone": current_timezone.zone if hasattr(current_timezone, 'zone') else 'UTC',
    }
    
    # Add time range if available
    if timestamp_all and len(timestamp_all) > 0:
        metadata["start_time"] = timestamp_all[0]
        metadata["end_time"] = timestamp_all[-1]
        metadata["duration"] = (timestamp_all[-1] - timestamp_all[0]).total_seconds()
    
    return metadata