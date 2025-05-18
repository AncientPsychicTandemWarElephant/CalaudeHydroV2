"""
state.py - Global state variables and management for Hydrophone Viewer
"""

import pickle
import os
import numpy as np
import logging
import pytz
from datetime import datetime

# === Global State Variables ===
spec_img = None
ax_fft = None
ax_spec = None
ax_nav_spec = None  # Navigation spectrogram
nav_spec_img = None
nav_box = None  # Box showing current view in navigation
ax_filelist = None
ax_log = None
fig = None
file_ranges = []
file_texts = []
file_paths = []  # Added the missing file_paths variable
freq_markers = [(None, None, None, None, None), (None, None, None, None, None)]
fft_patch = None
file_patch = None
spec_click_line = None
spec_click_text = None
time_labels_all = []
data_global = None
freqs_global = None
selected_range = None
comments = []
log_entries = []
comment_buttons = []
scroll_position = 0
gain_slider = None
fft_ymin = 0
fft_ymax = 120
fft_manual_gain = False  # Track if user has manually adjusted FFT gain
vmin = 0
vmax = 1
project_name = ""  # Add project name global

# === Time Zoom Globals ===
time_zoom_start = 0
time_zoom_end = None  # Will be set to data length
ax_time_zoom = None
time_zoom_slider = None

# === Navigation Interaction Globals ===
nav_dragging = False
nav_drag_start = None
nav_resizing = False
nav_resize_edge = None  # 'left' or 'right'

# === Debug Log Globals ===
debug_log_file = None
debug_log_counter = 0
debug_log_entries = 0
max_log_entries_per_file = 100  # Increased since we're only logging zoom events

# === Audio Globals ===
audio_data = None
audio_sample_rate = None
audio_timeline = []
audio_playback_line = None
audio_playing = False
audio_stop_flag = False
audio_thread = None
ax_audio_load = None
ax_audio_play = None
btn_audio_load = None
btn_audio_play = None
ax_time_display = None
audio_volume = 1.0  # Volume level (1.0 = 100%, can go higher for boost)
ax_volume_slider = None
volume_slider = None
ax_audio_visualizer = None
audio_viz_line = None
ax_vu_meter = None
vu_meter_bars = []
vu_meter_peak = None

# === Audio Timeline Globals ===
ax_audio_timeline = None
audio_segments = []
audio_file_info = []
audio_playback_line_timeline = None

# === Timezone Globals ===
current_timezone = pytz.UTC
detected_file_timezone = pytz.UTC
detected_file_timezone_source = "Default (UTC)"
system_timezone = pytz.UTC
use_local_timezone = True  # Whether to adjust times to local timezone
time_objects_utc = []
user_selected_timezone = None  # User's custom selected timezone
timezone_selection = 'local'  # Which timezone button is selected ('file', 'local', 'user')

# Timezone UI elements
ax_tz_file = None
btn_tz_file = None
ax_tz_local = None
btn_tz_local = None
ax_tz_user = None
btn_tz_user = None

# === Comment Section UI Elements ===
btn_toggle_comments = None
btn_add_comment = None
btn_delete_comment = None
ax_comment_text = None

# === Comment System Data ===
comments = []  # List of comment dictionaries
selected_comment_id = None
comments_visible = False
comment_id_counter = 0  # For generating unique IDs
comment_markers = []  # Matplotlib artists for visual comment markers (deprecated)
ax_comment_timeline = None  # Axes for comment timeline visualization
spectrogram_comment_markers = []  # Vertical lines on spectrogram for selected comment
nav_comment_highlight = None  # Yellow highlight on navigation spec for selected comment

# === FFT Timeline Globals ===
fft_start_time = None  # UTC datetime of first FFT sample
fft_time_axis = []  # List of UTC datetimes for each FFT sample

# === File List Globals ===
file_scroll_position = 0
visible_files = 10

def save_project(save_path):
    """Save the current project state to a file"""
    global comments, fft_ymin, fft_ymax, spec_img, file_paths, freq_markers, log_entries
    global spec_click_line, current_timezone, project_name, fft_start_time
    global detected_file_timezone, detected_file_timezone_source, system_timezone, use_local_timezone
    global user_selected_timezone, timezone_selection
    
    state = {
        "comments": comments,
        "y_scale": (fft_ymin, fft_ymax),
        "gain": spec_img.get_clim(),
        "file_paths": file_paths if 'file_paths' in globals() else [],
        "freq_markers": [(m[3] if m else None) for m in freq_markers],
        "log_entries": log_entries,
        "click_index": int(spec_click_line.get_xdata()[0]) if spec_click_line else None,
        "timezone": str(current_timezone),  # Save current timezone
        "detected_file_timezone": str(detected_file_timezone),  # Save detected file timezone
        "detected_file_timezone_source": detected_file_timezone_source,  # Save source description
        "system_timezone": str(system_timezone),  # Save system timezone
        "use_local_timezone": use_local_timezone,  # Save user preference
        "project_name": project_name,  # Save project name
        "fft_start_time": fft_start_time,  # Save FFT start time
        "user_selected_timezone": str(user_selected_timezone) if user_selected_timezone else None,  # Save user selected timezone
        "timezone_selection": timezone_selection,  # Save which button is selected
    }
    
    with open(save_path, 'wb') as f:
        pickle.dump(state, f)
    
    from utils import add_log_entry
    add_log_entry(f"Project saved to {os.path.basename(save_path)}")
    return True

def load_project(load_path):
    """Load a project from a file"""
    global fft_ymin, fft_ymax, spec_click_line, spec_click_text, current_timezone, project_name
    global fft_start_time, comments, spec_img, log_entries
    global detected_file_timezone, detected_file_timezone_source, system_timezone, use_local_timezone
    global user_selected_timezone, timezone_selection
    global btn_tz_file, btn_tz_local, btn_tz_user
    
    try:
        with open(load_path, 'rb') as f:
            state = pickle.load(f)
        
        fft_ymin, fft_ymax = state["y_scale"]
        
        # Load timezone settings if available
        if "detected_file_timezone" in state:
            try:
                detected_file_timezone = pytz.timezone(state["detected_file_timezone"])
            except:
                detected_file_timezone = pytz.UTC
                
        if "detected_file_timezone_source" in state:
            detected_file_timezone_source = state["detected_file_timezone_source"]
            
        if "system_timezone" in state:
            try:
                saved_system_tz = pytz.timezone(state["system_timezone"])
                # Only use the saved system timezone if it matches the current one
                from utils import get_system_timezone
                current_system_tz = get_system_timezone()
                if str(saved_system_tz) == str(current_system_tz):
                    system_timezone = saved_system_tz
                else:
                    system_timezone = current_system_tz
            except:
                from utils import get_system_timezone
                system_timezone = get_system_timezone()
        
        if "use_local_timezone" in state:
            use_local_timezone = state["use_local_timezone"]
            
        # Load user selected timezone
        if "user_selected_timezone" in state and state["user_selected_timezone"]:
            try:
                user_selected_timezone = pytz.timezone(state["user_selected_timezone"])
            except:
                user_selected_timezone = None
        
        # Load timezone selection
        if "timezone_selection" in state:
            timezone_selection = state["timezone_selection"]
        else:
            # Backwards compatibility
            timezone_selection = 'local' if use_local_timezone else 'file'
            
        # Set the current timezone based on selection
        if timezone_selection == 'local':
            current_timezone = system_timezone
        elif timezone_selection == 'user' and user_selected_timezone:
            current_timezone = user_selected_timezone
        else:  # file
            current_timezone = detected_file_timezone
            
        # Update button states if they exist
        if btn_tz_file or btn_tz_local or btn_tz_user:
            from ui_components import update_timezone_button_states
            update_timezone_button_states()
        
        # Load project name if available
        if "project_name" in state:
            project_name = state["project_name"]
        
        # Load FFT start time if available
        if "fft_start_time" in state:
            fft_start_time = state["fft_start_time"]
        
        # Setup viewer will be called from main with the file paths
        
        # These values will be applied after setup_viewer
        for c in state.get("comments", []):
            comments.append(c)
        
        log_entries.extend(state.get("log_entries", []))
        
        # Return the state so it can be used after setup_viewer is called
        return state
    
    except Exception as e:
        logging.error(f"Error loading project: {str(e)}", exc_info=True)
        return None

def reset_state():
    """Reset global state for a new project"""
    global time_objects_utc, fft_time_axis, project_name, time_labels_all
    global data_global, file_ranges, freqs_global, time_zoom_start, time_zoom_end
    global file_paths, current_timezone, detected_file_timezone, system_timezone
    global detected_file_timezone_source, use_local_timezone, user_selected_timezone, timezone_selection
    global comments, selected_comment_id, comments_visible, comment_id_counter
    global fft_manual_gain
    
    time_objects_utc = []
    fft_time_axis = []
    project_name = ""
    time_labels_all = []
    data_global = None
    file_ranges = []
    file_paths = []  # Reset file_paths
    freqs_global = None
    
    # Reset comment system
    comments = []
    selected_comment_id = None
    comments_visible = False
    comment_id_counter = 0
    comment_markers = []
    spectrogram_comment_markers = []
    nav_comment_highlight = None
    
    # Reset FFT manual gain flag
    fft_manual_gain = False
    
    # Keep timezone defaults
    if 'current_timezone' not in globals():
        current_timezone = pytz.UTC
    if 'detected_file_timezone' not in globals():
        detected_file_timezone = pytz.UTC
    if 'detected_file_timezone_source' not in globals():
        detected_file_timezone_source = "Default (UTC)"
    if 'system_timezone' not in globals():
        system_timezone = pytz.UTC
    if 'use_local_timezone' not in globals():
        use_local_timezone = True
    if 'user_selected_timezone' not in globals():
        user_selected_timezone = None
    if 'timezone_selection' not in globals():
        timezone_selection = 'local' if use_local_timezone else 'file'