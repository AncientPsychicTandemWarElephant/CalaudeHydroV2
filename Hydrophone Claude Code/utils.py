"""
utils.py - Helper functions and utilities for Hydrophone Viewer
"""

import logging
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import time
from matplotlib.ticker import FuncFormatter, MaxNLocator
import re
import os
import pytz
import tzlocal

# Import state directly
import state

# === Timezone Functions ===
def get_system_timezone():
    """Get the system's local timezone"""
    try:
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
    except Exception as e:
        logging.error(f"Error getting system timezone: {str(e)}")
        return pytz.UTC

def get_file_timezone(metadata=None):
    """
    Detect timezone from file metadata or filename pattern
    Returns a tuple of (timezone, source_description)
    """
    # If metadata contains timezone info, use that
    if metadata and 'timezone' in metadata:
        try:
            return (pytz.timezone(metadata['timezone']), f"From metadata: {metadata['timezone']}")
        except Exception as e:
            logging.error(f"Error parsing timezone from metadata: {str(e)}")
    
    # Default to UTC with indication it's the default
    return (pytz.UTC, "Default (UTC)")

# === Time Formatting Functions ===
def format_time_axis(x, pos=None):
    """Format x-axis labels with dynamic resolution based on zoom level"""
    try:
        idx = int(round(x))  # Round to nearest integer for index
        
        # Always ensure we have time labels
        if state.time_labels_all is None or len(state.time_labels_all) == 0:
            # Return formatted time even without labels
            hours = int(idx // 3600)
            minutes = int((idx % 3600) // 60)
            return f"{hours:02d}:{minutes:02d}"
        
        if 0 <= idx < len(state.time_labels_all):
            time_str = state.time_labels_all[idx]
            if time_str == "GAP":
                return "GAP"
            
            # Ensure time_str has the expected format HH:MM:SS or HH:MM
            if len(time_str) >= 5 and ':' in time_str:
                # Always show HH:MM for consistency
                return time_str[:5]
            else:
                # If not in expected format, return as is
                return time_str
        
        # Default formatting if index out of range
        hours = int(idx // 3600)
        minutes = int((idx % 3600) // 60)
        return f"{hours:02d}:{minutes:02d}"
    except Exception as e:
        # If anything goes wrong, return HH:MM format
        return "00:00"

def format_nav_time_axis(x, pos=None):
    """Format navigation x-axis labels to show HH:MM"""
    idx = int(x)
    if 0 <= idx < len(state.time_labels_all):
        time_str = state.time_labels_all[idx]
        if time_str == "GAP":
            return "GAP"
        
        # Return HH:MM format
        return time_str[:5]  # HH:MM
    return ""

def update_spectrogram_xaxis():
    """Update the spectrogram x-axis formatting based on zoom level"""
    if state.ax_spec is None:
        return
    
    # Force the xlim to be set on spectrogram
    if hasattr(state, 'time_zoom_start') and hasattr(state, 'time_zoom_end'):
        state.ax_spec.set_xlim(state.time_zoom_start, state.time_zoom_end)
    
    # Remove x-axis labels from spectrogram - they'll be on the audio timeline instead
    state.ax_spec.set_xticklabels([])
    state.ax_spec.tick_params(axis='x', which='both', labelbottom=False)
    state.ax_spec.set_xlabel('')  # Clear any xlabel
    
    # Update the audio timeline x-axis instead if it exists
    if hasattr(state, 'ax_audio_timeline') and state.ax_audio_timeline is not None:
        # Force the xlim to be set (this seems to trigger proper formatting)
        if hasattr(state, 'time_zoom_start') and hasattr(state, 'time_zoom_end'):
            state.ax_audio_timeline.set_xlim(state.time_zoom_start, state.time_zoom_end)
        
        # Set up the formatter for audio timeline (removed NullFormatter to avoid clearing)
        state.ax_audio_timeline.xaxis.set_major_formatter(FuncFormatter(format_time_axis))
        
        # Adjust number of ticks based on zoom level
        if state.time_zoom_end is None or state.time_labels_all is None:
            zoom_span = len(state.time_labels_all) if state.time_labels_all else 1000
        else:
            zoom_span = state.time_zoom_end - state.time_zoom_start
        
        if zoom_span < 60:  # Less than 1 minute
            state.ax_audio_timeline.xaxis.set_major_locator(MaxNLocator(integer=True, prune='both', nbins=20))
        elif zoom_span < 600:  # Less than 10 minutes
            state.ax_audio_timeline.xaxis.set_major_locator(MaxNLocator(integer=True, prune='both', nbins=15))
        else:
            state.ax_audio_timeline.xaxis.set_major_locator(MaxNLocator(integer=True, prune='both', nbins=10))
        
        # Rotate labels for better readability
        plt.setp(state.ax_audio_timeline.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Set label properties
        state.ax_audio_timeline.tick_params(axis='x', which='major', pad=8, labelsize=9)
        
        # Re-apply formatter after setting locator
        state.ax_audio_timeline.xaxis.set_major_formatter(FuncFormatter(format_time_axis))
    
    plt.draw()

def update_time_labels_for_timezone():
    """Update time labels based on the current timezone"""
    if not state.time_objects_utc:
        return
    
    state.time_labels_all = []
    for utc_time in state.time_objects_utc:
        # Handle GAP entries
        if utc_time is None:
            state.time_labels_all.append("GAP")
        else:
            # Convert to selected timezone
            local_time = utc_time.astimezone(state.current_timezone)
            state.time_labels_all.append(local_time.strftime("%H:%M:%S"))

def parse_audio_timestamp(filename):
    """Extract timestamp from audio file - first try metadata, then filename"""
    import struct
    
    # First try to extract from WAV metadata
    if os.path.exists(filename) and filename.endswith('.wav'):
        try:
            with open(filename, 'rb') as f:
                # Read RIFF header
                riff = f.read(4)
                if riff == b'RIFF':
                    file_size = struct.unpack('<I', f.read(4))[0]
                    wave = f.read(4)
                    if wave == b'WAVE':
                        # Search for INFO chunk
                        while f.tell() < file_size:
                            chunk_id = f.read(4)
                            if not chunk_id:
                                break
                                
                            chunk_size = struct.unpack('<I', f.read(4))[0]
                            
                            if chunk_id == b'LIST':
                                list_type = f.read(4)
                                if list_type == b'INFO':
                                    # Read INFO subchunks
                                    info_end = f.tell() + chunk_size - 4
                                    while f.tell() < info_end:
                                        sub_chunk_id = f.read(4)
                                        if not sub_chunk_id:
                                            break
                                        sub_chunk_size = struct.unpack('<I', f.read(4))[0]
                                        
                                        if sub_chunk_id == b'ICRD':  # Creation date
                                            date_data = f.read(sub_chunk_size)
                                            # Remove null bytes and decode
                                            date_str = date_data.rstrip(b'\x00').decode('utf-8')
                                            # Parse ISO format: 2025-04-30T06:31:47+00
                                            if 'T' in date_str:
                                                if '+' in date_str:
                                                    date_str = date_str.split('+')[0]
                                                dt = datetime.fromisoformat(date_str)
                                                # Assume UTC
                                                return pytz.UTC.localize(dt)
                                        else:
                                            f.seek(sub_chunk_size, 1)
                                else:
                                    f.seek(chunk_size - 4, 1)
                            else:
                                f.seek(chunk_size, 1)
        except Exception as e:
            add_log_entry(f"Error reading WAV metadata from {filename}: {str(e)}")
    
    # Fallback to filename parsing
    basename = os.path.basename(filename)
    match = re.match(r'wl_(\d{8})_(\d{6})\.wav$', basename)
    if not match:
        return None
    
    date_str = match.group(1)
    time_str = match.group(2)
    
    year = int(date_str[0:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    hour = int(time_str[0:2])
    minute = int(time_str[2:4])
    second = int(time_str[4:6])
    
    # Create UTC datetime
    dt = datetime(year, month, day, hour, minute, second)
    return pytz.UTC.localize(dt)

def init_debug_log():
    """Initialize a new debug log file"""
    if state.debug_log_file:
        state.debug_log_file.close()
    
    state.debug_log_counter += 1
    state.debug_log_entries = 0
    filename = f'zoom_debug_log_{state.debug_log_counter:03d}.txt'
    state.debug_log_file = open(filename, 'w')
    state.debug_log_file.write(f"Zoom Debug Log File #{state.debug_log_counter}\n")
    state.debug_log_file.write(f"Created at: {datetime.now()}\n")
    state.debug_log_file.write("This log contains only zoom-related debugging information\n")
    state.debug_log_file.write("-" * 50 + "\n")
    state.debug_log_file.flush()
    
    print(f"Created new zoom debug log: {filename}")

def write_debug_log(msg):
    """Write a message to the debug log, creating a new file if needed"""
    # Initialize log if needed
    if state.debug_log_file is None:
        init_debug_log()
    
    # Write the message
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    state.debug_log_file.write(f"[{timestamp}] {msg}\n")
    state.debug_log_file.flush()
    state.debug_log_entries += 1
    
    # Check if we need a new file
    if state.debug_log_entries >= state.max_log_entries_per_file:
        init_debug_log()

def update_log_display():
    """Update the log display with current scroll position"""
    if state.ax_log:
        state.ax_log.clear()
        state.ax_log.set_title("Log", fontsize=10, pad=8, color='black', weight='bold', loc='left')
        state.ax_log.axis("off")
        state.ax_log.set_facecolor('#e0e0e0')
        
        # Calculate which entries to show
        start_idx = state.scroll_position
        end_idx = min(start_idx + 5, len(state.log_entries))
        
        # Show entries - increased font size and adjusted spacing
        display_entries = state.log_entries[start_idx:end_idx]
        for i, entry in enumerate(display_entries):
            state.ax_log.text(0.02, 0.85 - i*0.17, entry, transform=state.ax_log.transAxes, 
                       fontsize=10, va='top')
        
        # Show scroll position indicator
        if len(state.log_entries) > 5:
            position_text = f"[{start_idx+1}-{end_idx} of {len(state.log_entries)}]"
            state.ax_log.text(0.98, 0.02, position_text, transform=state.ax_log.transAxes, 
                       fontsize=7, ha='right', va='bottom', color='gray')
        
        plt.draw()

def add_log_entry(msg, debug_only=False):
    """Add entry to log display and debug file"""
    # Only add zoom-related messages to the debug file
    zoom_keywords = ['zoom', 'pan', 'update_time_zoom', 'navigation', 'nav_', 'reset_time_zoom']
    is_zoom_related = any(keyword.lower() in msg.lower() for keyword in zoom_keywords)
    
    # If debug_only is True, only write to debug file, not to display
    if not debug_only:
        # Add to display log
        state.log_entries.append(msg)
        print(f"Log: {msg}")
        
        # Auto-scroll to bottom when new entry is added
        state.scroll_position = max(0, len(state.log_entries) - 5)
        update_log_display()
    
    # Write to debug file only if zoom-related
    if is_zoom_related:
        write_debug_log(msg)

def update_time_display(current_time, total_time):
    """Update the time display with current playback position"""
    if state.ax_time_display and state.fig:
        try:
            # Only update the text content, not create new text
            # Find the existing text object
            if hasattr(state.ax_time_display, '_time_text'):
                current_str = time.strftime('%H:%M:%S', time.gmtime(current_time))
                total_str = time.strftime('%H:%M:%S', time.gmtime(total_time))
                state.ax_time_display._time_text.set_text(f"{current_str} / {total_str}")
            
        except Exception as e:
            logging.error(f"Error updating time display: {e}")