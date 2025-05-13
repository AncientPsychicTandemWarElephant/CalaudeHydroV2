"""
event_handlers.py - Functions that handle user interaction events
"""

import matplotlib.pyplot as plt
import numpy as np
import logging
import os
import subprocess
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sounddevice as sd
import pytz
import threading
import time
from matplotlib.transforms import blended_transform_factory

# Import state directly
import state

from utils import add_log_entry, update_spectrogram_xaxis, update_time_labels_for_timezone, update_log_display
from visualization import update_time_zoom, update_fft, update_fft_range

# Import from audio_processing as needed
from audio_processing import play_audio, stop_audio

# === Navigation Handlers ===

def on_nav_press(event):
    """Handle mouse press on navigation spectrogram"""
    if event.inaxes != state.ax_nav_spec or event.button != 1:
        return
    
    x = event.xdata
    if x is None:
        return
    
    # Check if clicking near edges for resizing
    edge_tolerance = (state.time_zoom_end - state.time_zoom_start) * 0.1
    
    if abs(x - state.time_zoom_start) < edge_tolerance:
        state.nav_resizing = True
        state.nav_resize_edge = 'left'
        state.nav_drag_start = x
    elif abs(x - state.time_zoom_end) < edge_tolerance:
        state.nav_resizing = True
        state.nav_resize_edge = 'right'
        state.nav_drag_start = x
    elif state.time_zoom_start <= x <= state.time_zoom_end:
        # Clicking inside the box - start dragging
        state.nav_dragging = True
        state.nav_drag_start = x
    else:
        # Clicking outside the box - jump to that position
        span = state.time_zoom_end - state.time_zoom_start
        new_start = max(0, x - span/2)
        new_end = min(len(state.data_global) - 1, x + span/2)
        
        # Adjust if at boundaries
        if new_start == 0:
            new_end = min(span, len(state.data_global) - 1)
        elif new_end == len(state.data_global) - 1:
            new_start = max(0, new_end - span)
        
        update_time_zoom((new_start, new_end))

def on_nav_motion(event):
    """Handle mouse motion on navigation spectrogram"""
    if event.inaxes != state.ax_nav_spec:
        return
    
    x = event.xdata
    if x is None:
        return
    
    if state.nav_dragging and state.nav_drag_start is not None:
        # Calculate the drag offset
        offset = x - state.nav_drag_start
        span = state.time_zoom_end - state.time_zoom_start
        
        new_start = state.time_zoom_start + offset
        new_end = state.time_zoom_end + offset
        
        # Keep within bounds
        if new_start < 0:
            new_start = 0
            new_end = span
        elif new_end > len(state.data_global) - 1:
            new_end = len(state.data_global) - 1
            new_start = new_end - span
        
        # Update the drag start position for next motion
        state.nav_drag_start = x
        
        # Update zoom
        update_time_zoom((new_start, new_end))
    
    elif state.nav_resizing and state.nav_drag_start is not None:
        if state.nav_resize_edge == 'left':
            new_start = max(0, min(x, state.time_zoom_end - 10))  # Minimum width of 10
            update_time_zoom((new_start, state.time_zoom_end))
            state.nav_drag_start = x  # Update drag position
        elif state.nav_resize_edge == 'right':
            new_end = min(len(state.data_global) - 1, max(x, state.time_zoom_start + 10))
            update_time_zoom((state.time_zoom_start, new_end))
            state.nav_drag_start = x  # Update drag position

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
        
        # Update button text
        if state.btn_timezone:
            state.btn_timezone.label.set_text(f'Timezone: {selected_tz_name.split("/")[-1]}')
        
        # Close dropdown window
        state.timezone_dropdown.master.destroy()
        
        add_log_entry(f"Timezone changed to {selected_tz_name}")
        plt.draw()
        
    except Exception as e:
        add_log_entry(f"Error changing timezone: {str(e)}")
        logging.error(f"Error changing timezone", exc_info=True)

def create_timezone_dropdown():
    """Create dropdown menu for timezone selection"""
    # Create a separate window for timezone selection
    tz_window = tk.Toplevel()
    tz_window.title("Select Timezone")
    tz_window.geometry("300x100")
    
    # Create label
    label = ttk.Label(tz_window, text="Select Timezone:")
    label.pack(pady=10)
    
    # Get all timezone names
    timezone_names = pytz.all_timezones
    
    # Create combobox
    state.timezone_dropdown = ttk.Combobox(tz_window, values=timezone_names, state='readonly', width=30)
    state.timezone_dropdown.set('UTC')  # Default to UTC
    state.timezone_dropdown.pack(pady=10)
    
    # Bind change event
    state.timezone_dropdown.bind('<<ComboboxSelected>>', on_timezone_change)
    
    # Position window
    tz_window.update_idletasks()
    tz_window.geometry("+{}+{}".format(100, 100))

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
            
            # Auto-adjust the FFT Y-axis range for the selected point
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
                
                # Auto-adjust the FFT Y-axis range for the selected range
                from visualization import auto_adjust_fft_range
                auto_adjust_fft_range()
                
    plt.draw()

def on_click(event):
    """Handle mouse clicks with modifiers for frequency markers"""
    if event.key == 'control' and event.inaxes == state.ax_fft:
        if event.button == 1:
            update_marker(0, event.xdata)
        elif event.button == 3:
            update_marker(1, event.xdata)

def on_key_press(event):
    """Handle keyboard shortcuts"""
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
    state.ax_filelist.set_title("Files", fontsize=9, pad=8)
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