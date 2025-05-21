"""
data_parser.py - Functions for parsing hydrophone data and audio files
"""

import numpy as np
import logging
from datetime import datetime, timedelta
import re
import os
from scipy.io import wavfile
import sounddevice as sd
import pytz

# Import state directly
import state

from utils import add_log_entry, parse_audio_timestamp
from visualization import update_audio_timeline_visualization

def parse_hydrophone_file(file_path):
    """Parse hydrophone data file and extract FFT data and timestamps"""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Debug output for file header
        add_log_entry(f"Parsing file: {file_path}")
        for i, line in enumerate(lines[:30]):
            if "Time Zone" in line or "timezone" in line.lower():
                add_log_entry(f"Found timezone info at line {i+1}: {line.strip()}")
        
        # Dictionary to store file metadata
        metadata = {
            "client": "",
            "job": "",
            "project": "",
            "site": "",
            "location": "",
            "start_date": "",
            "timezone": "UTC",  # Default timezone
        }
        
        # Try to extract Client and Job from the file header
        if not state.project_name:  # Only set if not already set
            client = ""
            job = ""
            
            # Look for Client and Job fields in the header
            for line in lines[:30]:  # Check first 30 lines
                line_lower = line.lower()
                if line.startswith("Client"):
                    client = line.split("\t", 1)[-1].strip()
                    metadata["client"] = client
                elif line.startswith("Job"):
                    job = line.split("\t", 1)[-1].strip()
                    metadata["job"] = job
                elif "project:" in line_lower:
                    metadata["project"] = line.split(":", 1)[1].strip()
                elif "site:" in line_lower:
                    metadata["site"] = line.split(":", 1)[1].strip()
                elif "location:" in line_lower:
                    metadata["location"] = line.split(":", 1)[1].strip()
                elif "timezone:" in line_lower:
                    metadata["timezone"] = line.split(":", 1)[1].strip()
                    add_log_entry(f"Found timezone in header: {metadata['timezone']}")
                # Handle the "Time Zone" format used in exported files
                elif line.startswith("Time Zone"):
                    tz_value = line.split("\t", 1)[-1].strip() if "\t" in line else ""
                    if tz_value:
                        metadata["timezone"] = tz_value
                        add_log_entry(f"Found 'Time Zone' in header: {tz_value}")
                elif line.startswith("Start Date"):
                    metadata["start_date"] = line.split("\t")[-1].strip()
                
                # If we found both, combine them for the project name
                if client and job:
                    state.project_name = f"{client} - {job}"
            
            # Fallback to other metadata if Client/Job not found
            if not state.project_name:
                if metadata["project"]:
                    state.project_name = metadata["project"]
                elif metadata["site"]:
                    state.project_name = metadata["site"]
                elif metadata["location"]:
                    state.project_name = metadata["location"]
                else:
                    for line in lines[:20]:
                        if "#" in line and not state.project_name:  # Use first comment as fallback
                            state.project_name = line.replace("#", "").strip()
                            break
            
            # If still no project name, use filename
            if not state.project_name:
                state.project_name = os.path.splitext(os.path.basename(file_path))[0]
        
        start_idx = next(i for i, line in enumerate(lines) if line.startswith("Time") and "Data Points" in line)
        header_tokens = lines[start_idx].strip().split('\t')  # Changed to tab split for Lucy format
        # Find where numeric frequency data starts (after "Data Points" column)
        data_points_idx = header_tokens.index("Data Points")
        freqs = [float(tok) for tok in header_tokens[data_points_idx+1:] if tok.replace('.', '', 1).isdigit()]
        time_labels = []
        spec = []
        time_objects = []
        comments_data = []  # Track comments for each row
        current_comment = None
        
        for line in lines[start_idx + 1:]:
            parts = line.strip().split('\t')  # Changed to tab split for Lucy format
            if len(parts) < 6:
                continue
            time_labels.append(parts[0])
            
            # Extract comment (parts[1] based on Lucy format)
            if len(parts) > 1:
                comment = parts[1].strip()
                if comment != current_comment:
                    current_comment = comment
                comments_data.append(current_comment)
            else:
                comments_data.append(current_comment)
            # Parse as UTC time - assuming the data is in UTC
            time_obj = datetime.strptime(parts[0], "%H:%M:%S")
            
            # Find the Start Date in the header
            start_date = None
            for header_line in lines[:start_idx]:
                if header_line.startswith("Start Date"):
                    start_date_str = header_line.split("\t")[-1].strip()
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                    break
            
            if start_date is None:
                # Fallback to today's date
                start_date = datetime.today().date()
                
            # Create datetime object from date and time
            local_dt = datetime.combine(start_date, time_obj.time())
                        
            # Handle timezone from metadata
            file_tz = pytz.UTC  # Default to UTC
            if metadata and "timezone" in metadata and metadata["timezone"]:
                try:
                    file_tz = pytz.timezone(metadata["timezone"])
                    # Also update the detected file timezone in state
                    if len(time_objects) == 0:  # Only do this once for the first timestamp
                        state.detected_file_timezone = file_tz
                        state.detected_file_timezone_source = f"From file: {metadata['timezone']}"
                        add_log_entry(f"Detected timezone from file: {metadata['timezone']}")
                except Exception as e:
                    logging.warning(f"Invalid timezone in file: {metadata['timezone']} - {str(e)}")
                    file_tz = pytz.UTC
            
            # Localize to file timezone first, then convert to UTC for storage
            try:
                # Localize using the file timezone
                local_time = file_tz.localize(local_dt)
                # Convert to UTC for internal storage
                utc_time = local_time.astimezone(pytz.UTC)
            except Exception:
                # Fallback to UTC if there are issues
                utc_time = pytz.UTC.localize(local_dt)
                
            time_objects.append(utc_time)
            # Skip to the column after "Data Points" value (which would be at data_points_idx)
            amplitudes = [float(val) for val in parts[data_points_idx+1:data_points_idx+1+len(freqs)]]
            spec.append(amplitudes)
        
        spec_array = np.array(spec)
        if spec_array.shape[1] != len(freqs):
            raise ValueError("Mismatch in frequency bin count")
            
        # Final debug output before returning
        add_log_entry(f"Final metadata timezone: {metadata['timezone']}")
        add_log_entry(f"Detected file timezone set to: {state.detected_file_timezone}")
        
        # Store the timezone in state before returning
        if metadata["timezone"] != "UTC":
            try:
                file_tz = pytz.timezone(metadata["timezone"])
                state.detected_file_timezone = file_tz
                state.detected_file_timezone_source = f"From file: {metadata['timezone']}"
                add_log_entry(f"Updated detected timezone to: {metadata['timezone']}")
            except Exception as e:
                add_log_entry(f"Error setting timezone: {str(e)}")
        
        # Check for an associated comments file and import if found
        try:
            # Try both the direct path and with .comments.json extension
            comment_file_paths = [
                f"{file_path}.comments.json",             # Standard format
                os.path.splitext(file_path)[0] + ".comments.json"  # Try without .txt extension
            ]
            
            for comment_file_path in comment_file_paths:
                if os.path.exists(comment_file_path):
                    add_log_entry(f"Found comment file: {comment_file_path}")
                    # Import our comment handler function
                    from comment_file_handler import import_comments_from_file
                    # Import the comments - merge with existing if any
                    import_success = import_comments_from_file(comment_file_path, merge=True)
                    if import_success:
                        add_log_entry(f"Successfully imported {len(state.comments)} comments from {comment_file_path}")
                        
                        # FORCE comments to be visible
                        state.comments_visible = True
                        
                        # Force the toggle button to show "Hide Comments" if it exists
                        try:
                            if hasattr(state, 'btn_toggle_comments'):
                                state.btn_toggle_comments.label.set_text('Hide Comments')
                                add_log_entry(f"Updated toggle button text to 'Hide Comments'")
                        except Exception as e2:
                            add_log_entry(f"Warning: Could not update toggle button: {str(e2)}")
                        
                        # Trigger UI updates if the visualization module is available
                        try:
                            from visualization import update_comment_markers, display_selected_comment
                            # Force update of comment markers
                            update_comment_markers()
                            add_log_entry(f"Called update_comment_markers() for {len(state.comments)} comments")
                            
                            # Update comment list if it exists
                            try:
                                from comment_list import update_comment_list_display
                                update_comment_list_display()
                                add_log_entry(f"Updated comment list display with {len(state.comments)} comments")
                            except Exception as e2:
                                add_log_entry(f"Warning: Could not update comment list: {str(e2)}")
                            
                            # If a comment is selected, display it
                            if hasattr(state, 'selected_comment_id') and state.selected_comment_id is not None:
                                display_selected_comment()
                                add_log_entry(f"Displayed selected comment {state.selected_comment_id}")
                            elif len(state.comments) > 0:
                                # Select first comment if none is selected
                                state.selected_comment_id = state.comments[0]['id']
                                display_selected_comment()
                                add_log_entry(f"Auto-selected first comment {state.selected_comment_id}")
                        except Exception as e2:
                            add_log_entry(f"Warning: Could not update comment display: {str(e2)}")
                        
                        # Don't check more paths if we already found one
                        break
                    else:
                        add_log_entry(f"Failed to import comments from {comment_file_path}")
            else:
                # If loop completed without finding a file
                add_log_entry(f"No comment file found for {file_path}")
        except Exception as e:
            add_log_entry(f"Error checking or importing comments file: {str(e)}")
            # Continue without comment import if there's an error
                
        return time_labels, freqs, spec_array, time_objects, metadata, comments_data
    except Exception as e:
        logging.error(f"Error parsing file {file_path}", exc_info=True)
        print(f"Error parsing file {file_path}. Check error_log.txt for details.")
        raise

def load_and_merge_audio_with_timestamp_alignment(wav_paths):
    """Load audio files and align them based on timestamps"""
    if not state.fft_start_time or not state.fft_time_axis:
        add_log_entry("Error: FFT timeline not established")
        return
    
    # Parse timestamps from filenames and sort
    files_with_timestamps = []
    for wav_path in wav_paths:
        # Pass full path to allow metadata extraction
        timestamp = parse_audio_timestamp(wav_path)
        if timestamp:
            files_with_timestamps.append({
                'path': wav_path,
                'timestamp': timestamp
            })
    
    if not files_with_timestamps:
        add_log_entry("No valid audio files with timestamps found")
        return
    
    # Sort by timestamp
    files_with_timestamps.sort(key=lambda x: x['timestamp'])
    
    # Load all audio files
    audio_buffers = []
    for item in files_with_timestamps:
        rate, data = wavfile.read(item['path'])
        
        if state.audio_sample_rate is None:
            state.audio_sample_rate = rate
        elif state.audio_sample_rate != rate:
            raise ValueError(f"Inconsistent sample rate in {item['path']}")
        
        # Convert to mono if stereo
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        
        audio_buffers.append({
            'data': data,
            'timestamp': item['timestamp'],
            'path': item['path'],
            'duration': len(data) / rate
        })
    
    # Calculate total timeline duration
    first_audio_timestamp = audio_buffers[0]['timestamp']
    last_audio_timestamp = audio_buffers[-1]['timestamp']
    last_audio_duration = audio_buffers[-1]['duration']
    
    # Total duration in seconds
    total_duration_sec = (last_audio_timestamp - first_audio_timestamp).total_seconds() + last_audio_duration
    total_samples = int(total_duration_sec * state.audio_sample_rate)
    
    # Create merged buffer with proper gaps
    merged_data = np.zeros(total_samples, dtype=np.float32)
    
    # Fill in each audio segment at its correct position
    state.audio_segments = []
    state.audio_file_info = []
    
    for buffer_info in audio_buffers:
        # Calculate offset from the first audio file
        offset_sec = (buffer_info['timestamp'] - first_audio_timestamp).total_seconds()
        offset_samples = int(offset_sec * state.audio_sample_rate)
        
        # Copy audio data to correct position
        data = buffer_info['data']
        end_samples = offset_samples + len(data)
        
        if end_samples <= len(merged_data):
            merged_data[offset_samples:end_samples] = data
        else:
            # Truncate if it would exceed buffer
            available = len(merged_data) - offset_samples
            merged_data[offset_samples:] = data[:available]
        
        # Calculate segment position relative to FFT timeline
        fft_offset = (buffer_info['timestamp'] - state.fft_start_time).total_seconds()
        fft_end = fft_offset + buffer_info['duration']
        
        state.audio_segments.append((fft_offset, fft_end))
        
        state.audio_file_info.append({
            'path': buffer_info['path'],
            'duration': buffer_info['duration'],
            'start_time': fft_offset,
            'end_time': fft_end,
            'timestamp': buffer_info['timestamp'],
            'samples': len(data)
        })
    
    # Normalize audio data
    state.audio_data = merged_data.astype(np.float32)
    max_val = np.max(np.abs(state.audio_data))
    if max_val > 0:
        state.audio_data /= max_val
    
    # Calculate audio timeline relative to FFT start
    audio_timeline_start = (first_audio_timestamp - state.fft_start_time).total_seconds()
    audio_timeline_end = audio_timeline_start + total_duration_sec
    
    add_log_entry(f"Audio loaded: {total_duration_sec:.1f} seconds")
    
    # Update the audio timeline visualization
    update_audio_timeline_visualization()