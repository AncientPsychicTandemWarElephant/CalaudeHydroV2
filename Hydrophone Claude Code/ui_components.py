"""
ui_components.py - UI setup, layout, and configuration
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, SpanSelector, RangeSlider
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os

# Import state directly
import state

from utils import add_log_entry, format_nav_time_axis, update_log_display
from visualization import update_fft, update_fft_range, normalize_spectrogram_data, update_time_zoom, fix_spectrogram

def create_menu_ui():
    """Create the file menu UI elements as a horizontal button bar"""
    # Import here to avoid circular imports
    from event_handlers import on_open, on_save_project, on_load_project, on_view_debug_logs, on_export_data
    
    # Store buttons in a list to keep references
    button_list = []
    
    # Calculate button dimensions and positions - keep buttons within visible area
    button_width = 0.06  # Reduced width 
    button_height = 0.02  # Small height
    button_margin = 0.004  # Small margin between buttons
    top_position = 0.97  # Lower position to avoid clipping at top of window
    
    # Create the Open Files button
    ax_open = state.fig.add_axes([0.01, top_position, button_width, button_height])
    btn_open = Button(ax_open, 'Open Files', color='#e6f0ff')
    btn_open.on_clicked(on_open)
    button_list.append(btn_open)
    
    # Create the Save Project button
    ax_save = state.fig.add_axes([0.01 + (button_width + button_margin), 
                                top_position, button_width, button_height])
    btn_save = Button(ax_save, 'Save Project', color='#e6f0ff')
    btn_save.on_clicked(on_save_project)
    button_list.append(btn_save)
    
    # Create the Load Project button
    ax_load = state.fig.add_axes([0.01 + 2 * (button_width + button_margin), 
                                top_position, button_width, button_height])
    btn_load = Button(ax_load, 'Load Project', color='#e6f0ff')
    btn_load.on_clicked(on_load_project)
    button_list.append(btn_load)
    
    # Create the Export Data button with highlight color
    ax_export = state.fig.add_axes([0.01 + 3 * (button_width + button_margin), 
                                  top_position, button_width, button_height])
    btn_export = Button(ax_export, 'Export', color='#ccffcc')  # Light green for visibility
    btn_export.label.set_fontweight('bold')  # Make text bold
    btn_export.on_clicked(on_export_data)
    button_list.append(btn_export)
    
    # Create the View Debug Logs button
    ax_view_logs = state.fig.add_axes([0.01 + 4 * (button_width + button_margin), 
                                     top_position, button_width, button_height])
    btn_view_logs = Button(ax_view_logs, 'View Logs', color='#e6f0ff')
    btn_view_logs.on_clicked(on_view_debug_logs)
    button_list.append(btn_view_logs)
    
    # Store buttons in state for potential future reference
    state.menu_buttons = button_list
    
    # Update canvas
    plt.draw()
    
    return button_list

def create_gain_controls():
    """Create gain control sliders and buttons"""
    # Gain controls - adjusted positions for better layout
    gain_slider_left = 0.045
    gain_slider_bottom = 0.30
    gain_slider_width = 0.02
    gain_slider_height = 0.30
    ax_gain = state.fig.add_axes([gain_slider_left, gain_slider_bottom, gain_slider_width, gain_slider_height])
    
    # Get data normalization values for initial slider settings
    vmin, vmax = normalize_spectrogram_data()
    if vmin is None or vmax is None:
        # Use sensible defaults if normalization fails
        vmin, vmax = 0.0, 0.5
    
    # Create a direct gain updater that skips the visualization module
    def direct_update_gain(val):
        try:
            lo, hi = val
            
            # Hardcoded constraints with safety checks
            if lo >= hi:
                lo = hi - 0.1
            
            # Apply directly to the spectrogram image
            if state.spec_img is not None:
                state.spec_img.set_clim(lo, hi)
                add_log_entry(f"Gain updated to: {lo:.2f} - {hi:.2f}")
                
                # Force a redraw to ensure it updates
                plt.draw()
        except Exception as e:
            add_log_entry(f"Error in direct gain update: {str(e)}")
    
    # Initialize with calculated values based on data
    state.gain_slider = RangeSlider(ax_gain, 'Gain', 0, max(2.0, vmax*1.5), 
                                  valinit=(vmin, vmax),  # Data-driven initial values 
                                  orientation='vertical')
    
    # Gain adjustment buttons with custom styling
    btn_width = 0.035
    btn_height = 0.04
    btn_left = gain_slider_left - btn_width - 0.005
    btn_y = [
        gain_slider_bottom + gain_slider_height * 0.75,
        gain_slider_bottom + gain_slider_height * 0.60,
        gain_slider_bottom + gain_slider_height * 0.35,
        gain_slider_bottom + gain_slider_height * 0.20,
    ]
    
    # Create button axes
    ax_max_up = state.fig.add_axes([btn_left, btn_y[0], btn_width, btn_height])
    ax_max_down = state.fig.add_axes([btn_left, btn_y[1], btn_width, btn_height])
    ax_min_up = state.fig.add_axes([btn_left, btn_y[2], btn_width, btn_height])
    ax_min_down = state.fig.add_axes([btn_left, btn_y[3], btn_width, btn_height])
    
    # Create buttons with light gray background for better hover detection
    btn_max_up = Button(ax_max_up, '+Max', color='0.85')
    btn_max_down = Button(ax_max_down, '-Max', color='0.85')
    btn_min_up = Button(ax_min_up, '+Min', color='0.85')
    btn_min_down = Button(ax_min_down, '-Min', color='0.85')
    
    # Direct button handlers that manipulate the spectrogram directly
    def on_max_up(event):
        try:
            # Get current values
            lo, hi = state.gain_slider.val
            # Increase max value
            new_hi = hi + 0.1
            # Apply to slider and spectrogram
            state.gain_slider.set_val((lo, new_hi))
            if state.spec_img:
                state.spec_img.set_clim(lo, new_hi)
                add_log_entry(f"Max gain increased to {new_hi:.2f}")
            plt.draw()
        except Exception as e:
            add_log_entry(f"Error in +Max button: {str(e)}")
    
    def on_max_down(event):
        try:
            # Get current values
            lo, hi = state.gain_slider.val
            # Decrease max value with minimum separation check
            new_hi = max(lo + 0.1, hi - 0.1)
            # Apply to slider and spectrogram
            state.gain_slider.set_val((lo, new_hi))
            if state.spec_img:
                state.spec_img.set_clim(lo, new_hi)
                add_log_entry(f"Max gain decreased to {new_hi:.2f}")
            plt.draw()
        except Exception as e:
            add_log_entry(f"Error in -Max button: {str(e)}")
    
    def on_min_up(event):
        try:
            # Get current values
            lo, hi = state.gain_slider.val
            # Increase min value with maximum limit check
            new_lo = min(hi - 0.1, lo + 0.1)
            # Apply to slider and spectrogram
            state.gain_slider.set_val((new_lo, hi))
            if state.spec_img:
                state.spec_img.set_clim(new_lo, hi)
                add_log_entry(f"Min gain increased to {new_lo:.2f}")
            plt.draw()
        except Exception as e:
            add_log_entry(f"Error in +Min button: {str(e)}")
    
    def on_min_down(event):
        try:
            # Get current values
            lo, hi = state.gain_slider.val
            # Decrease min value with minimum limit check
            new_lo = max(0, lo - 0.1)
            # Apply to slider and spectrogram
            state.gain_slider.set_val((new_lo, hi))
            if state.spec_img:
                state.spec_img.set_clim(new_lo, hi)
                add_log_entry(f"Min gain decreased to {new_lo:.2f}")
            plt.draw()
        except Exception as e:
            add_log_entry(f"Error in -Min button: {str(e)}")
    
    # Connect the button handlers
    btn_max_up.on_clicked(on_max_up)
    btn_max_down.on_clicked(on_max_down)
    btn_min_up.on_clicked(on_min_up)
    btn_min_down.on_clicked(on_min_down)
    
    # Connect our direct updater rather than going through the visualization module
    state.gain_slider.on_changed(direct_update_gain)
    
    # Make sure to apply initial values directly as well
    direct_update_gain((vmin, vmax))

def create_nav_controls():
    """Create navigation and zoom control buttons"""
    # Check if buttons were already created by state_buttons_fix
    if hasattr(state, 'btn_zoom_in') and state.btn_zoom_in is not None:
        add_log_entry("Navigation controls already created by state_buttons_fix")
        return
        
    zoom_section_y = 0.52  # Starting Y position for zoom controls
    
    # Add section label for navigation controls
    state.fig.text(0.885, zoom_section_y + 0.04, 'Navigation', fontsize=10, 
             weight='bold', ha='center', va='bottom')
    
    # Define button handlers directly here
    
    def on_zoom_in(event):
        """Zoom in on time axis"""
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
            add_log_entry(f"Error in Zoom In button: {str(e)}")
    
    def on_zoom_out(event):
        """Zoom out on time axis"""
        try:
            current_span = state.time_zoom_end - state.time_zoom_start
            center = (state.time_zoom_start + state.time_zoom_end) / 2
            
            # Zoom out by 100%
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
            add_log_entry(f"Error in Zoom Out button: {str(e)}")
    
    def on_pan_left(event):
        """Pan left on time axis"""
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
            add_log_entry(f"Error in Pan Left button: {str(e)}")
    
    def on_pan_right(event):
        """Pan right on time axis"""
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
            add_log_entry(f"Error in Pan Right button: {str(e)}")
    
    def on_reset_zoom(event):
        """Reset zoom to show all data"""
        try:
            if state.data_global is not None:
                add_log_entry("Resetting zoom to show all data")
                update_time_zoom((0, len(state.data_global) - 1))
            else:
                add_log_entry("No data available to zoom")
        except Exception as e:
            add_log_entry(f"Error in Reset Zoom button: {str(e)}")
    
    # Zoom buttons in a logical layout
    ax_zoom_in = state.fig.add_axes([0.82, zoom_section_y, 0.06, 0.03])
    btn_zoom_in = Button(ax_zoom_in, 'Zoom In', color='0.85')
    btn_zoom_in.on_clicked(on_zoom_in)
    
    ax_zoom_out = state.fig.add_axes([0.89, zoom_section_y, 0.06, 0.03])
    btn_zoom_out = Button(ax_zoom_out, 'Zoom Out', color='0.85')
    btn_zoom_out.on_clicked(on_zoom_out)
    
    # Pan buttons below zoom
    ax_pan_left = state.fig.add_axes([0.82, zoom_section_y - 0.04, 0.06, 0.03])
    btn_pan_left = Button(ax_pan_left, '◀ Pan', color='0.85')
    btn_pan_left.on_clicked(on_pan_left)
    
    ax_pan_right = state.fig.add_axes([0.89, zoom_section_y - 0.04, 0.06, 0.03])
    btn_pan_right = Button(ax_pan_right, 'Pan ▶', color='0.85')
    btn_pan_right.on_clicked(on_pan_right)
    
    # Reset button centered below pan buttons
    ax_zoom_reset = state.fig.add_axes([0.855, zoom_section_y - 0.08, 0.08, 0.03])
    btn_zoom_reset = Button(ax_zoom_reset, 'Reset Zoom', color='0.85')
    btn_zoom_reset.on_clicked(on_reset_zoom)
    
    add_log_entry("Navigation controls created")

def create_audio_controls():
    """Create audio control buttons and sliders"""
    # Check if buttons were already created and fixed by state_buttons_fix
    if hasattr(state, 'btn_audio_load') and state.btn_audio_load is not None and hasattr(state, 'btn_audio_load') and hasattr(state.btn_audio_load, '_connection_id') and state.btn_audio_load._connection_id is not None:
        add_log_entry("Audio controls already created and fixed by state_buttons_fix")
        return
        
    # Import event handlers here to avoid circular imports
    from event_handlers import on_load_audio, on_play_audio
    
    # Audio controls section - in bottom right corner
    audio_section_y = 0.32  # Starting Y position for audio controls
    
    # Add section label for audio controls
    state.fig.text(0.885, audio_section_y + 0.05, 'Audio Controls', fontsize=10, 
             weight='bold', ha='center', va='bottom')
    
    # Audio buttons
    state.ax_audio_load = state.fig.add_axes([0.82, audio_section_y, 0.06, 0.04])
    state.btn_audio_load = Button(state.ax_audio_load, 'Load Audio', color='0.85')
    state.btn_audio_load.on_clicked(on_load_audio)
    
    state.ax_audio_play = state.fig.add_axes([0.89, audio_section_y, 0.06, 0.04])
    state.btn_audio_play = Button(state.ax_audio_play, 'Play Audio', color='0.85')
    state.btn_audio_play.on_clicked(on_play_audio)
    
    # Volume control slider
    state.ax_volume_slider = state.fig.add_axes([0.82, audio_section_y - 0.05, 0.14, 0.02])
    
    def update_volume(val):
        """Update the audio volume level"""
        state.audio_volume = val
        # Update volume display
        if state.ax_vu_meter:
            state.ax_vu_meter.set_title(f'Volume: {int(state.audio_volume * 100)}%', fontsize=9, pad=4)
            plt.draw()
    
    state.volume_slider = plt.Slider(state.ax_volume_slider, '', 0.0, 3.0, valinit=state.audio_volume,
                              valstep=0.1, color='blue')
    state.volume_slider.on_changed(update_volume)
    
    # Add volume label above the slider
    state.fig.text(0.885, audio_section_y - 0.03, 'Volume', fontsize=9, 
             ha='center', va='bottom')
    
    # Time display - create with persistent text object
    state.ax_time_display = state.fig.add_axes([0.82, audio_section_y - 0.09, 0.14, 0.03], 
                                 frameon=True, facecolor='lightgray')
    state.ax_time_display.set_title("Playback Time", fontsize=9, pad=4)
    state.ax_time_display.axis("off")
    
    # Create a persistent text object that we'll update
    state.ax_time_display._time_text = state.ax_time_display.text(0.5, 0.5, "00:00:00 / 00:00:00", 
                                                     transform=state.ax_time_display.transAxes, 
                                                     fontsize=10, ha='center', va='center')
    
    # Audio visualizer - waveform display
    state.ax_audio_visualizer = state.fig.add_axes([0.82, audio_section_y - 0.16, 0.14, 0.06], 
                                     frameon=True, facecolor='black')
    state.ax_audio_visualizer.set_title('Audio Waveform', fontsize=9, pad=4)
    state.ax_audio_visualizer.set_xlim(0, 1)
    state.ax_audio_visualizer.set_ylim(-1, 1)
    state.ax_audio_visualizer.grid(True, alpha=0.3)
    state.ax_audio_visualizer.tick_params(axis='both', which='both', labelsize=6)
    
    # VU meter display - with pre-created scale labels
    state.ax_vu_meter = state.fig.add_axes([0.82, audio_section_y - 0.24, 0.14, 0.05],
                              frameon=True, facecolor='black')
    state.ax_vu_meter.set_title(f'VU Meter - Volume: {int(state.audio_volume * 100)}%', fontsize=9, pad=4)
    state.ax_vu_meter.set_xlim(-60, 0)
    state.ax_vu_meter.set_ylim(0, 1)
    state.ax_vu_meter.set_yticks([])
    state.ax_vu_meter.tick_params(axis='x', which='both', labelsize=6)
    state.ax_vu_meter.spines['top'].set_visible(False)
    state.ax_vu_meter.spines['right'].set_visible(False)
    state.ax_vu_meter.spines['left'].set_visible(False)
    
    # Pre-create scale labels that won't be removed during updates
    for db in [-60, -40, -20, -10, -6, -3, 0]:
        state.ax_vu_meter.text(db, 0.05, f'{db}', ha='center', va='bottom', 
                       color='white', fontsize=7, zorder=20)

def create_log_display():
    """Create the log display area and controls"""
    # Check if buttons were already created by state_buttons_fix
    if hasattr(state, 'btn_log_up') and state.btn_log_up is not None:
        add_log_entry("Log controls already created by state_buttons_fix")
        
        # Still create the log display area if not already created
        if not hasattr(state, 'ax_log') or state.ax_log is None:
            state.ax_log = state.fig.add_axes([0.05, 0.02, 0.72, 0.08], frameon=True, facecolor='#e0e0e0')
            state.ax_log.set_title("Log", fontsize=9, pad=4, color='black')
            state.ax_log.axis("off")
            
            # Initialize the log display
            update_log_display()
        
        return
    
    # Import event handlers here to avoid circular imports
    from event_handlers import scroll_log_up, scroll_log_down
    
    # Create scrollable log with grey background - adjusted to avoid audio conflicts
    state.ax_log = state.fig.add_axes([0.05, 0.02, 0.72, 0.08], frameon=True, facecolor='#e0e0e0')
    state.ax_log.set_title("Log", fontsize=9, pad=4, color='black')
    state.ax_log.axis("off")
    
    # Create scroll buttons for log - moved to the left side
    ax_log_up = state.fig.add_axes([0.01, 0.07, 0.03, 0.025])
    btn_log_up = Button(ax_log_up, '▲', color='0.85')
    ax_log_down = state.fig.add_axes([0.01, 0.025, 0.03, 0.025])
    btn_log_down = Button(ax_log_down, '▼', color='0.85')
    
    # Direct handlers for log scrolling
    def on_log_up(event):
        try:
            state.scroll_position = max(0, state.scroll_position - 1)
            update_log_display()
        except Exception as e:
            print(f"Error scrolling log up: {str(e)}")
    
    def on_log_down(event):
        try:
            max_position = max(0, len(state.log_entries) - 5)
            state.scroll_position = min(max_position, state.scroll_position + 1)
            update_log_display()
        except Exception as e:
            print(f"Error scrolling log down: {str(e)}")
    
    btn_log_up.on_clicked(on_log_up)
    btn_log_down.on_clicked(on_log_down)
    
    # Initialize the log display
    update_log_display()

def create_file_list():
    """Create the file list display and controls"""
    # Check if buttons were already created by state_buttons_fix
    if hasattr(state, 'btn_files_up') and state.btn_files_up is not None and hasattr(state, 'btn_clear_highlight') and state.btn_clear_highlight is not None:
        add_log_entry("File list controls already created by state_buttons_fix")
        
        # Still create the file list area if not already created
        if not hasattr(state, 'ax_filelist') or state.ax_filelist is None:
            state.ax_filelist = state.fig.add_axes([0.82, 0.64, 0.14, 0.30], frameon=True, facecolor='#f0f0f0')
            state.ax_filelist.set_title("Files", fontsize=9, pad=8)
            state.ax_filelist.axis("off")
            state.ax_filelist.set_facecolor('#f0f0f0')
            
            # Add border for clarity
            for spine in state.ax_filelist.spines.values():
                spine.set_visible(True)
                spine.set_edgecolor('#d0d0d0')
                spine.set_linewidth(1)
            
            # Initial file list display
            from event_handlers import display_file_list
            display_file_list()
        
        return
    
    # Import event handlers here to avoid circular imports
    from event_handlers import clear_file_highlight, display_file_list
    
    # File list with scrollable area and more compact design
    state.ax_filelist = state.fig.add_axes([0.82, 0.64, 0.14, 0.30], frameon=True, facecolor='#f0f0f0')
    state.ax_filelist.set_title("Files", fontsize=9, pad=8)
    state.ax_filelist.axis("off")
    state.ax_filelist.set_facecolor('#f0f0f0')
    
    # Add border for clarity
    for spine in state.ax_filelist.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor('#d0d0d0')
        spine.set_linewidth(1)
    
    # File list scroll buttons with custom styling
    ax_files_up = state.fig.add_axes([0.96, 0.92, 0.02, 0.025])
    ax_files_down = state.fig.add_axes([0.96, 0.65, 0.02, 0.025])
    
    btn_files_up = Button(ax_files_up, '▲', color='0.85')
    btn_files_down = Button(ax_files_down, '▼', color='0.85')
    
    # Direct scroll handlers
    def on_files_up(event):
        try:
            state.file_scroll_position = max(0, state.file_scroll_position - 1)
            display_file_list()
            add_log_entry(f"Scrolled file list up, position: {state.file_scroll_position}")
        except Exception as e:
            add_log_entry(f"Error scrolling file list up: {str(e)}")
    
    def on_files_down(event):
        try:
            max_position = max(0, len(state.file_paths) - state.visible_files)
            state.file_scroll_position = min(max_position, state.file_scroll_position + 1)
            display_file_list()
            add_log_entry(f"Scrolled file list down, position: {state.file_scroll_position}")
        except Exception as e:
            add_log_entry(f"Error scrolling file list down: {str(e)}")
    
    btn_files_up.on_clicked(on_files_up)
    btn_files_down.on_clicked(on_files_down)
    
    # Clear highlight button
    ax_clear = state.fig.add_axes([0.82, 0.59, 0.14, 0.03])
    btn_clear = Button(ax_clear, 'Clear Highlight', color='0.85')
    
    def on_clear_file(event):
        try:
            if state.file_patch:
                try:
                    state.file_patch.remove()
                except ValueError:
                    pass
                state.file_patch = None
            for txt in state.file_texts:
                txt.set_backgroundcolor(None)
            plt.draw()
            add_log_entry("Cleared file highlight")
        except Exception as e:
            add_log_entry(f"Error clearing file highlight: {str(e)}")
    
    btn_clear.on_clicked(on_clear_file)
    
    # Initial file list display
    display_file_list()

def create_fft_controls():
    """Create FFT display controls with enhanced Y-axis controls"""
    # Check if buttons were already created by state_buttons_fix
    if hasattr(state, 'btn_fft_up') and state.btn_fft_up is not None:
        add_log_entry("FFT controls already created by state_buttons_fix")
        return
        
    # Add section label for FFT Y controls
    state.fig.text(0.06, 0.95, 'FFT Y Controls', fontsize=9, 
                   weight='bold', ha='center', va='bottom')
    
    # Adjusting vertical scale buttons position to match FFT location
    btn_width = 0.04
    btn_height = 0.04
    
    # Create axes for buttons
    ax_max_up = state.fig.add_axes([0.03, 0.90, btn_width, btn_height])
    ax_max_down = state.fig.add_axes([0.03, 0.85, btn_width, btn_height])
    ax_min_up = state.fig.add_axes([0.03, 0.80, btn_width, btn_height])
    ax_min_down = state.fig.add_axes([0.03, 0.75, btn_width, btn_height])
    # Make the Auto Y button the same size as other buttons to prevent overlap
    ax_auto_y = state.fig.add_axes([0.03, 0.70, btn_width, btn_height])
    
    # Create buttons
    btn_max_up = Button(ax_max_up, '+Max', color='0.85')
    btn_max_down = Button(ax_max_down, '-Max', color='0.85')
    btn_min_up = Button(ax_min_up, '+Min', color='0.85')
    btn_min_down = Button(ax_min_down, '-Min', color='0.85')
    btn_auto_y = Button(ax_auto_y, 'Auto Y', color='lightblue')
    
    # Store buttons in state for access from other modules
    state.btn_fft_up = btn_max_up
    state.btn_fft_down = btn_max_down
    state.btn_fft_min_up = btn_min_up
    state.btn_fft_min_down = btn_min_down
    state.btn_auto_y = btn_auto_y
    
    # Direct handlers
    def adjust_fft_max_up(event):
        try:
            state.fft_ymax = max(state.fft_ymin + 10, state.fft_ymax + 10)
            state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
            add_log_entry(f"Increased FFT Y-max to {state.fft_ymax}")
            plt.draw()
        except Exception as e:
            add_log_entry(f"Error adjusting FFT Y-max: {str(e)}")
    
    def adjust_fft_max_down(event):
        try:
            state.fft_ymax = max(state.fft_ymin + 10, state.fft_ymax - 10)
            state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
            add_log_entry(f"Decreased FFT Y-max to {state.fft_ymax}")
            plt.draw()
        except Exception as e:
            add_log_entry(f"Error adjusting FFT Y-max: {str(e)}")
            
    def adjust_fft_min_up(event):
        try:
            state.fft_ymin = min(state.fft_ymax - 10, state.fft_ymin + 10)
            state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
            add_log_entry(f"Increased FFT Y-min to {state.fft_ymin}")
            plt.draw()
        except Exception as e:
            add_log_entry(f"Error adjusting FFT Y-min: {str(e)}")
            
    def adjust_fft_min_down(event):
        try:
            state.fft_ymin = max(0, state.fft_ymin - 10)
            state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
            add_log_entry(f"Decreased FFT Y-min to {state.fft_ymin}")
            plt.draw()
        except Exception as e:
            add_log_entry(f"Error adjusting FFT Y-min: {str(e)}")
            
    def auto_adjust_y(event):
        try:
            from visualization import auto_adjust_fft_range
            auto_adjust_fft_range()
        except Exception as e:
            add_log_entry(f"Error auto-adjusting FFT Y-axis: {str(e)}")
    
    # Connect handlers to buttons
    btn_max_up.on_clicked(adjust_fft_max_up)
    btn_max_down.on_clicked(adjust_fft_max_down)
    btn_min_up.on_clicked(adjust_fft_min_up)
    btn_min_down.on_clicked(adjust_fft_min_down)
    btn_auto_y.on_clicked(auto_adjust_y)

def create_selection_span():
    """Create the selection span tool for the spectrogram"""
    # Import at function level to avoid circular imports
    from visualization import update_fft_range
    
    def ctrl_select(xmin, xmax):
        # Ensure selection is within current zoom
        start = max(int(xmin), int(state.time_zoom_start))
        end = min(int(xmax), int(state.time_zoom_end))
        
        if start < end:
            state.selected_range = (start, end)
            if state.fft_patch:
                state.fft_patch.remove()
            state.fft_patch = state.ax_spec.axvspan(start, end, color='red', alpha=0.3)
            update_fft_range(start, end, state.freqs_global, state.data_global)
    
    span = SpanSelector(state.ax_spec, lambda *args: None, 'horizontal', 
                       useblit=True, props=dict(alpha=0.3, facecolor='red'))
    span.set_active(False)
    
    span.onselect = ctrl_select
    
    return span

def create_timezone_button():
    """Create the timezone selection button"""
    # Import at function level to avoid circular imports
    from event_handlers import create_timezone_dropdown
    
    # Timezone button on right - use state.fig instead of fig
    state.ax_timezone = state.fig.add_axes([0.89, 0.965, 0.1, 0.025])
    state.btn_timezone = Button(state.ax_timezone, 'Timezone: UTC', color='0.85')
    
    def on_timezone_click(event):
        try:
            create_timezone_dropdown()
        except Exception as e:
            add_log_entry(f"Error creating timezone dropdown: {str(e)}")
    
    state.btn_timezone.on_clicked(on_timezone_click)
    
    return state.btn_timezone

def create_fix_spectrogram_button():
    """Create a button to reset the spectrogram if it displays incorrectly"""
    # Check if button was already created by state_buttons_fix
    if hasattr(state, 'btn_reset') and state.btn_reset is not None:
        add_log_entry("Reset button already created by state_buttons_fix")
        return None
        
    # Create the button at a lower position to avoid clashing with gain slider
    # Moved down and renamed to "Reset"
    ax_fix = state.fig.add_axes([0.02, 0.21, 0.07, 0.03])
    btn_fix = Button(ax_fix, 'Reset', color='0.85')
    
    def on_reset(event):
        """Reset the spectrogram display"""
        try:
            add_log_entry("Resetting spectrogram display")
            fix_spectrogram()
        except Exception as e:
            add_log_entry(f"Error in Reset button: {str(e)}")
    
    btn_fix.on_clicked(on_reset)
    return btn_fix

def setup_fft_display():
    """Set up the FFT display area"""
    state.ax_fft.set_facecolor('black')
    state.ax_fft.set_title('FFT Slice', fontsize=12, color='#ffffff')
    state.ax_fft._current_title = 'FFT Slice'  # Track the current title
    state.ax_fft.grid(True, axis='y', linestyle='--', color='gray', alpha=0.3)
    state.ax_fft.plot(state.freqs_global, state.data_global[0], color='lime')
    state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)

def setup_navigation_spectrogram():
    """Set up the navigation spectrogram display"""
    # Get normalized data values for better visualization
    vmin, vmax = normalize_spectrogram_data()
    if vmin is None or vmax is None:
        # Fallback to sensible defaults
        vmin, vmax = 0.0, 0.5
    
    # Create the navigation spectrogram with data-driven color limits
    state.nav_spec_img = state.ax_nav_spec.imshow(
        state.data_global.T,
        aspect='auto', origin='lower',
        extent=[0, state.data_global.shape[0]-1, state.freqs_global[0], state.freqs_global[-1]],
        cmap='viridis',
        vmin=vmin, vmax=vmax,
        alpha=0.7  # Slightly transparent to help highlight stand out
    )
    state.ax_nav_spec.set_title('Navigation View (click/drag/scroll to navigate)', fontsize=9)
    state.ax_nav_spec.set_ylabel('Freq (Hz)', fontsize=8)
    state.ax_nav_spec.tick_params(axis='both', which='major', labelsize=8)
    
    # Add time formatting to navigation x-axis
    from matplotlib.ticker import FuncFormatter, MaxNLocator
    state.ax_nav_spec.xaxis.set_major_formatter(FuncFormatter(format_nav_time_axis))
    state.ax_nav_spec.xaxis.set_major_locator(MaxNLocator(integer=True, prune='both', nbins=8))
    plt.setp(state.ax_nav_spec.xaxis.get_majorticklabels(), rotation=45, ha='right')
    state.ax_nav_spec.tick_params(axis='x', which='major', pad=5, labelsize=8)
    
    # Create initial navigation visualization
    width = state.time_zoom_end - state.time_zoom_start
    handle_width = width * 0.05
    
    # Create rectangle to show current view - thick red border
    state.nav_box = plt.Rectangle((state.time_zoom_start, state.freqs_global[0]), 
                           width, 
                           state.freqs_global[-1] - state.freqs_global[0],
                           fill=False, edgecolor='red', linewidth=3, alpha=1.0,
                           zorder=10)
    state.ax_nav_spec.add_patch(state.nav_box)
    
    # Add semi-transparent white overlay for current view
    nav_highlight = plt.Rectangle((state.time_zoom_start, state.freqs_global[0]), 
                                 width, 
                                 state.freqs_global[-1] - state.freqs_global[0],
                                 fill=True, facecolor='white', alpha=0.2,
                                 zorder=5)
    state.ax_nav_spec.add_patch(nav_highlight)
    
    # Add edge handles for visual feedback
    left_handle = plt.Rectangle((state.time_zoom_start, state.freqs_global[0]), 
                               handle_width, 
                               state.freqs_global[-1] - state.freqs_global[0],
                               fill=True, facecolor='red', alpha=0.3,
                               zorder=6)
    right_handle = plt.Rectangle((state.time_zoom_end - handle_width, state.freqs_global[0]), 
                                handle_width, 
                                state.freqs_global[-1] - state.freqs_global[0],
                                fill=True, facecolor='red', alpha=0.3,
                                zorder=6)
    state.ax_nav_spec.add_patch(left_handle)
    state.ax_nav_spec.add_patch(right_handle)
    
    # Add position indicator text
    zoom_percent = (width / (len(state.data_global) - 1)) * 100
    center_idx = int((state.time_zoom_start + state.time_zoom_end) / 2)
    center_time = state.time_labels_all[center_idx] if 0 <= center_idx < len(state.time_labels_all) else "N/A"
    
    position_text = state.ax_nav_spec.text(0.02, 0.95, 
                                   f'Zoom: {zoom_percent:.0f}% | Center: {center_time}', 
                                   transform=state.ax_nav_spec.transAxes, 
                                   fontsize=8, color='white', va='top',
                                   bbox=dict(boxstyle="round,pad=0.3", 
                                           facecolor='black', alpha=0.7))
    
    # Make navigation spectrogram stay at full view
    state.ax_nav_spec.set_xlim(0, state.data_global.shape[0]-1)
    state.ax_nav_spec.set_ylim(state.freqs_global[0], state.freqs_global[-1])

def setup_main_spectrogram():
    """Set up the main spectrogram display"""
    # Import at function level to avoid circular imports
    from utils import update_spectrogram_xaxis
    from event_handlers import on_timeline_hover
    
    # Get data-driven normalization values for better visualization
    vmin, vmax = normalize_spectrogram_data()
    if vmin is None or vmax is None:
        # Fallback to sensible defaults that usually work well
        vmin, vmax = 0.0, 0.5
    
    add_log_entry(f"Setting up spectrogram with data-driven range: {vmin:.4f}-{vmax:.4f}")
    
    # Create spectrogram with data-driven limits
    state.spec_img = state.ax_spec.imshow(
        state.data_global.T,
        aspect='auto', 
        origin='lower',
        extent=[0, state.data_global.shape[0]-1, state.freqs_global[0], state.freqs_global[-1]],
        cmap='viridis',
        vmin=vmin,
        vmax=vmax
    )
    
    # Force the colorbar limits 
    state.spec_img.set_clim(vmin, vmax)
    
    # Update gain slider to match
    if hasattr(state, 'gain_slider') and state.gain_slider is not None:
        try:
            state.gain_slider.set_val((vmin, vmax))
        except Exception as e:
            add_log_entry(f"Could not update gain slider: {str(e)}")
    
    # Set up time axis formatting
    update_spectrogram_xaxis()
    
    # Connect timeline hover event for audio timeline
    state.fig.canvas.mpl_connect('motion_notify_event', on_timeline_hover)
    
    # This extra draw call helps ensure the display updates immediately
    plt.draw()

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