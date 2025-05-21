"""
ui_components.py - UI setup, layout, and configuration
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, SpanSelector, RangeSlider, CheckButtons
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import pytz
import sys

# Import state directly
import state

from utils import add_log_entry, format_nav_time_axis, update_log_display
from visualization import update_fft, update_fft_range, normalize_spectrogram_data, update_time_zoom, fix_spectrogram, update_comment_markers

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
    
    # Create the Export Data button
    ax_export = state.fig.add_axes([0.01 + 3 * (button_width + button_margin), 
                                  top_position, button_width, button_height])
    btn_export = Button(ax_export, 'Export', color='#e6f0ff')  # Same color as other buttons
    btn_export.on_clicked(on_export_data)
    button_list.append(btn_export)
    
    # View Logs button removed as per request
    
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
    state.btn_max_up = Button(ax_max_up, '+Max', color='0.85')
    state.btn_max_down = Button(ax_max_down, '-Max', color='0.85')
    state.btn_min_up = Button(ax_min_up, '+Min', color='0.85')
    state.btn_min_down = Button(ax_min_down, '-Min', color='0.85')
    
    # Direct button handlers that manipulate the spectrogram directly
    def on_max_up(event):
        try:
            add_log_entry("+Max button clicked")
            
            # Check if gain_slider exists
            if not hasattr(state, 'gain_slider') or state.gain_slider is None:
                add_log_entry("Error: Gain slider not initialized")
                return
                
            # Get current values
            lo, hi = state.gain_slider.val
            # Increase max value
            new_hi = hi + 0.1
            # Apply to slider and spectrogram
            state.gain_slider.set_val((lo, new_hi))
            if hasattr(state, 'spec_img') and state.spec_img:
                state.spec_img.set_clim(lo, new_hi)
                add_log_entry(f"Max gain increased to {new_hi:.2f}")
            else:
                add_log_entry("Warning: spec_img not available")
            plt.draw()
        except Exception as e:
            add_log_entry(f"Error in +Max button: {str(e)}")
            import traceback
            add_log_entry(f"Traceback: {traceback.format_exc()}")
    
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
    state.btn_max_up.on_clicked(on_max_up)
    state.btn_max_down.on_clicked(on_max_down)
    state.btn_min_up.on_clicked(on_min_up)
    state.btn_min_down.on_clicked(on_min_down)
    
    # Connect our direct updater rather than going through the visualization module
    state.gain_slider.on_changed(direct_update_gain)
    
    # Make sure to apply initial values directly as well
    direct_update_gain((vmin, vmax))

def create_nav_controls():
    """Create navigation and zoom control buttons"""
        
    zoom_section_y = 0.52  # Starting Y position for zoom controls
    
    # Add section label for navigation controls
    state.fig.text(0.885, zoom_section_y + 0.04, 'Navigation', fontsize=10, 
             weight='bold', ha='center', va='bottom')
    
    # Define button handlers directly here
    
    def on_zoom_in(event):
        """Zoom in on time axis"""
        try:
            # Check if data is available
            if not hasattr(state, 'data_global') or state.data_global is None:
                add_log_entry("Error: No data loaded for zoom")
                return
                
            if not hasattr(state, 'time_zoom_start') or not hasattr(state, 'time_zoom_end'):
                add_log_entry("Error: Zoom variables not initialized")
                return
                
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
            import traceback
            add_log_entry(f"Traceback: {traceback.format_exc()}")
    
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
    state.btn_zoom_in = Button(ax_zoom_in, 'Zoom In', color='0.85')
    state.btn_zoom_in.on_clicked(on_zoom_in)
    
    ax_zoom_out = state.fig.add_axes([0.89, zoom_section_y, 0.06, 0.03])
    state.btn_zoom_out = Button(ax_zoom_out, 'Zoom Out', color='0.85')
    state.btn_zoom_out.on_clicked(on_zoom_out)
    
    # Pan buttons below zoom
    ax_pan_left = state.fig.add_axes([0.82, zoom_section_y - 0.04, 0.06, 0.03])
    state.btn_pan_left = Button(ax_pan_left, '◀ Pan', color='0.85')
    state.btn_pan_left.on_clicked(on_pan_left)
    
    ax_pan_right = state.fig.add_axes([0.89, zoom_section_y - 0.04, 0.06, 0.03])
    state.btn_pan_right = Button(ax_pan_right, 'Pan ▶', color='0.85')
    state.btn_pan_right.on_clicked(on_pan_right)
    
    # Reset button centered below pan buttons
    ax_zoom_reset = state.fig.add_axes([0.855, zoom_section_y - 0.08, 0.08, 0.03])
    state.btn_zoom_reset = Button(ax_zoom_reset, 'Reset Zoom', color='0.85')
    state.btn_zoom_reset.on_clicked(on_reset_zoom)
    
    add_log_entry("Navigation controls created")

def create_audio_controls():
    """Create audio control buttons and sliders"""
        
    # Import event handlers here to avoid circular imports
    from event_handlers import on_load_audio, on_play_audio
    
    # Audio controls section - moved lower to create separation from navigation
    audio_section_y = 0.32  # Create more space from navigation controls
    
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
        # Update volume in label since VU meter is removed
        if hasattr(state, 'volume_label'):
            state.volume_label.set_text(f'Volume: {int(state.audio_volume * 100)}%')
        plt.draw()
    
    state.volume_slider = plt.Slider(state.ax_volume_slider, '', 0.0, 3.0, valinit=state.audio_volume,
                              valstep=0.1, color='blue')
    state.volume_slider.on_changed(update_volume)
    
    # Add volume label above the slider
    volume_label = state.fig.text(0.885, audio_section_y - 0.03, 'Volume: 100%', fontsize=9, 
             ha='center', va='bottom')
    state.volume_label = volume_label  # Store reference for updates
    
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
    
    # VU meter removed - space now available for comment display

def create_log_display():
    """Create the log display area and controls"""
    
    # Import event handlers here to avoid circular imports
    from event_handlers import scroll_log_up, scroll_log_down
    
    # Create scrollable log with grey background - moved further to the right and slightly up
    state.ax_log = state.fig.add_axes([0.82, 0.025, 0.16, 0.09], frameon=True, facecolor='#e0e0e0')
    state.ax_log.set_title("Log", fontsize=10, pad=8, color='black', weight='bold', loc='left')
    state.ax_log.axis("off")
    
    # Create scroll buttons for log - adjusted to new position
    ax_log_up = state.fig.add_axes([0.78, 0.09, 0.03, 0.025])
    btn_log_up = Button(ax_log_up, '▲', color='0.85')
    ax_log_down = state.fig.add_axes([0.78, 0.06, 0.03, 0.025]) 
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
    
    # Import event handlers here to avoid circular imports
    from event_handlers import clear_file_highlight, display_file_list
    
    # Add section label for file list
    state.fig.text(0.885, 0.82, 'Files', fontsize=10, 
                   weight='bold', ha='center', va='bottom')
    
    # File list with scrollable area and more compact design - reduce height to give more space to TZ
    state.ax_filelist = state.fig.add_axes([0.82, 0.64, 0.14, 0.17], frameon=True, facecolor='#f0f0f0')
    state.ax_filelist.axis("off")
    state.ax_filelist.set_facecolor('#f0f0f0')
    
    # Add border for clarity
    for spine in state.ax_filelist.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor('#d0d0d0')
        spine.set_linewidth(1)
    
    # File list scroll buttons with custom styling - moved inside file list area
    ax_files_up = state.fig.add_axes([0.93, 0.785, 0.02, 0.025])
    ax_files_down = state.fig.add_axes([0.93, 0.645, 0.02, 0.025])
    
    btn_files_up = Button(ax_files_up, '▲', color='0.85')
    btn_files_down = Button(ax_files_down, '▼', color='0.85')
    
    # Store in state to prevent duplication
    state.btn_files_up = btn_files_up
    state.btn_files_down = btn_files_down
    
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
            add_log_entry("Clear Highlight button clicked")
            
            if hasattr(state, 'file_patch') and state.file_patch:
                try:
                    state.file_patch.remove()
                except ValueError:
                    pass
                state.file_patch = None
                add_log_entry("Removed file patch")
            else:
                add_log_entry("No file patch to clear")
                
            if hasattr(state, 'file_texts'):
                for txt in state.file_texts:
                    txt.set_backgroundcolor(None)
                add_log_entry(f"Cleared background from {len(state.file_texts)} file texts")
            else:
                add_log_entry("No file texts to clear")
                
            plt.draw()
            add_log_entry("Cleared file highlight")
        except Exception as e:
            add_log_entry(f"Error clearing file highlight: {str(e)}")
            import traceback
            add_log_entry(f"Traceback: {traceback.format_exc()}")
    
    btn_clear.on_clicked(on_clear_file)
    
    # Initial file list display
    display_file_list()

def create_fft_controls():
    """Create FFT display controls with enhanced Y-axis controls"""
        
    # Add section label for FFT Y controls - align with controls
    state.fig.text(0.025, 0.95, 'FFT Y Controls', fontsize=9, 
                   weight='bold', ha='center', va='bottom')
    
    # Adjusting vertical scale buttons position to match FFT location
    btn_width = 0.04
    btn_height = 0.04
    
    # Create axes for buttons - align with spectrogram controls
    fft_btn_left = 0.005  # Same as spectrogram buttons
    ax_max_up = state.fig.add_axes([fft_btn_left, 0.90, btn_width, btn_height])
    ax_max_down = state.fig.add_axes([fft_btn_left, 0.85, btn_width, btn_height])
    ax_min_up = state.fig.add_axes([fft_btn_left, 0.80, btn_width, btn_height])
    ax_min_down = state.fig.add_axes([fft_btn_left, 0.75, btn_width, btn_height])
    # Make the Auto Y button the same size as other buttons to prevent overlap
    ax_auto_y = state.fig.add_axes([fft_btn_left, 0.70, btn_width, btn_height])
    
    # Create gain slider for FFT - align with spectrogram slider
    from matplotlib.widgets import RangeSlider
    fft_slider_left = 0.045  # Same as spectrogram slider
    ax_fft_gain = state.fig.add_axes([fft_slider_left, 0.70, 0.02, 0.23], facecolor='lightgray')
    
    # Initialize FFT gain slider with sensible defaults
    fft_min = getattr(state, 'fft_ymin', 0)
    fft_max = getattr(state, 'fft_ymax', 100)
    state.fft_gain_slider = RangeSlider(ax_fft_gain, 'Gain', 0, max(200, fft_max*1.5), 
                                       valinit=(fft_min, fft_max),
                                       orientation='vertical')
    
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
            lo, hi = state.fft_gain_slider.val
            new_hi = hi + 10
            state.fft_gain_slider.set_val((lo, new_hi))
            state.fft_ymax = new_hi
            state.ax_fft.set_ylim(lo, new_hi)
            add_log_entry(f"Increased FFT Y-max to {new_hi}")
            plt.draw()
        except Exception as e:
            add_log_entry(f"Error adjusting FFT Y-max: {str(e)}")
    
    def adjust_fft_max_down(event):
        try:
            lo, hi = state.fft_gain_slider.val
            new_hi = max(lo + 10, hi - 10)
            state.fft_gain_slider.set_val((lo, new_hi))
            state.fft_ymax = new_hi
            state.ax_fft.set_ylim(lo, new_hi)
            add_log_entry(f"Decreased FFT Y-max to {new_hi}")
            plt.draw()
        except Exception as e:
            add_log_entry(f"Error adjusting FFT Y-max: {str(e)}")
            
    def adjust_fft_min_up(event):
        try:
            lo, hi = state.fft_gain_slider.val
            new_lo = min(hi - 10, lo + 10)
            state.fft_gain_slider.set_val((new_lo, hi))
            state.fft_ymin = new_lo
            state.ax_fft.set_ylim(new_lo, hi)
            add_log_entry(f"Increased FFT Y-min to {new_lo}")
            plt.draw()
        except Exception as e:
            add_log_entry(f"Error adjusting FFT Y-min: {str(e)}")
            
    def adjust_fft_min_down(event):
        try:
            lo, hi = state.fft_gain_slider.val
            new_lo = max(0, lo - 10)
            state.fft_gain_slider.set_val((new_lo, hi))
            state.fft_ymin = new_lo
            state.ax_fft.set_ylim(new_lo, hi)
            add_log_entry(f"Decreased FFT Y-min to {new_lo}")
            plt.draw()
        except Exception as e:
            add_log_entry(f"Error adjusting FFT Y-min: {str(e)}")
            
    def auto_adjust_y(event):
        try:
            from visualization import auto_adjust_fft_range
            state.fft_manual_gain = False  # Reset manual gain flag
            auto_adjust_fft_range()
        except Exception as e:
            add_log_entry(f"Error auto-adjusting FFT Y-axis: {str(e)}")
    
    # Add slider update function
    def update_fft_gain(val):
        """Direct update when FFT gain slider changes"""
        lo, hi = val
        state.fft_ymin = lo
        state.fft_ymax = hi
        state.fft_manual_gain = True  # Mark that user has manually adjusted gain
        state.ax_fft.set_ylim(lo, hi)
        plt.draw()
    
    # Connect slider to update function
    state.fft_gain_slider.on_changed(update_fft_gain)
    
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
    """Create the timezone control buttons for timezone selection"""
    from utils import get_system_timezone
    
    # Import at function level to avoid circular imports
    from event_handlers import on_tz_file_clicked, on_tz_local_clicked, on_tz_user_clicked
    
    # Get the system timezone if not already set
    if state.system_timezone == pytz.UTC:
        state.system_timezone = get_system_timezone()
    
    # Timezone controls area title
    state.fig.text(0.885, 0.94, 'Timezone Settings', fontsize=10, 
                   weight='bold', ha='center', va='bottom')
    
    # Get readable timezone names
    file_tz_name = "UTC"
    try:
        if hasattr(state.detected_file_timezone, 'zone'):
            file_tz_name = state.detected_file_timezone.zone
        else:
            if hasattr(state.detected_file_timezone, 'key'):
                file_tz_name = state.detected_file_timezone.key
            else:
                file_tz_name = str(state.detected_file_timezone)
    except Exception:
        file_tz_name = "UTC"
    
    system_tz_name = "Local"
    try:
        if hasattr(state.system_timezone, 'zone'):
            system_tz_name = state.system_timezone.zone
        else:
            if hasattr(state.system_timezone, 'key'):
                system_tz_name = state.system_timezone.key
            else:
                system_tz_name = str(state.system_timezone)
    except Exception:
        system_tz_name = "Local"
    
    # Create timezone control buttons
    button_width = 0.14
    button_height = 0.025  # Reduced height
    button_margin = 0.003
    
    # Initialize which button is selected based on current state
    if not hasattr(state, 'timezone_selection'):
        # Initialize based on existing state
        if state.use_local_timezone:
            state.timezone_selection = 'local'
        else:
            state.timezone_selection = 'file'
    
    # Button 1: Detected File Timezone
    state.ax_tz_file = state.fig.add_axes([0.82, 0.90, button_width, button_height])
    file_label = f"File TZ: {file_tz_name.split('/')[-1]}"  # Single line
    initial_file_color = '#90EE90' if state.timezone_selection == 'file' else '0.85'
    state.btn_tz_file = Button(state.ax_tz_file, file_label, color=initial_file_color)
    state.btn_tz_file.label.set_fontsize(10)  # Larger text
    state.btn_tz_file.on_clicked(on_tz_file_clicked)
    
    # Button 2: Apply Local Timezone
    state.ax_tz_local = state.fig.add_axes([0.82, 0.90 - button_height - button_margin, button_width, button_height])
    local_label = f"Local TZ: {system_tz_name.split('/')[-1]}"  # Single line
    initial_local_color = '#90EE90' if state.timezone_selection == 'local' else '0.85'
    state.btn_tz_local = Button(state.ax_tz_local, local_label, color=initial_local_color)
    state.btn_tz_local.label.set_fontsize(10)  # Larger text
    state.btn_tz_local.on_clicked(on_tz_local_clicked)
    
    # Button 3: User Select Timezone
    state.ax_tz_user = state.fig.add_axes([0.82, 0.90 - 2*(button_height + button_margin), button_width, button_height])
    # Display current user timezone if one has been selected
    if hasattr(state, 'user_selected_timezone') and state.user_selected_timezone:
        try:
            if hasattr(state.user_selected_timezone, 'zone'):
                user_tz_name = state.user_selected_timezone.zone.split('/')[-1]
            else:
                user_tz_name = str(state.user_selected_timezone).split('/')[-1]
        except:
            user_tz_name = "None"
    else:
        user_tz_name = "None"
    
    user_label = f"User TZ: {user_tz_name}"  # Single line
    initial_user_color = '#90EE90' if state.timezone_selection == 'user' else '0.85'
    state.btn_tz_user = Button(state.ax_tz_user, user_label, color=initial_user_color)
    state.btn_tz_user.label.set_fontsize(10)  # Larger text
    state.btn_tz_user.on_clicked(on_tz_user_clicked)
    
    return None

def update_timezone_button_states():
    """Update the color states of timezone buttons based on current selection"""
    # Define colors
    inactive_color = '0.85'  # Light gray
    active_color = '#90EE90'  # Light green
    
    # Update button colors based on selection
    if hasattr(state, 'btn_tz_file') and state.btn_tz_file:
        if state.timezone_selection == 'file':
            state.btn_tz_file.color = active_color
            # Also update the actual button widget
            for widget in state.btn_tz_file.ax.get_children():
                if hasattr(widget, 'set_facecolor'):
                    widget.set_facecolor(active_color)
        else:
            state.btn_tz_file.color = inactive_color
            for widget in state.btn_tz_file.ax.get_children():
                if hasattr(widget, 'set_facecolor'):
                    widget.set_facecolor(inactive_color)
    
    if hasattr(state, 'btn_tz_local') and state.btn_tz_local:
        if state.timezone_selection == 'local':
            state.btn_tz_local.color = active_color
            for widget in state.btn_tz_local.ax.get_children():
                if hasattr(widget, 'set_facecolor'):
                    widget.set_facecolor(active_color)
        else:
            state.btn_tz_local.color = inactive_color
            for widget in state.btn_tz_local.ax.get_children():
                if hasattr(widget, 'set_facecolor'):
                    widget.set_facecolor(inactive_color)
    
    if hasattr(state, 'btn_tz_user') and state.btn_tz_user:
        if state.timezone_selection == 'user':
            state.btn_tz_user.color = active_color
            for widget in state.btn_tz_user.ax.get_children():
                if hasattr(widget, 'set_facecolor'):
                    widget.set_facecolor(active_color)
        else:
            state.btn_tz_user.color = inactive_color
            for widget in state.btn_tz_user.ax.get_children():
                if hasattr(widget, 'set_facecolor'):
                    widget.set_facecolor(inactive_color)
    
    # Force redraw
    if hasattr(state, 'fig') and state.fig:
        plt.draw()

def create_fix_spectrogram_button():
    """Create a button to reset the spectrogram if it displays incorrectly"""
        
    # Create the button inline with gain control buttons
    gain_slider_left = 0.045
    gain_slider_bottom = 0.30
    gain_slider_height = 0.30
    btn_width = 0.035
    btn_height = 0.04
    btn_left = gain_slider_left - btn_width - 0.005
    btn_y = gain_slider_bottom + gain_slider_height * 0.05  # Below -Min button
    
    ax_fix = state.fig.add_axes([btn_left, btn_y, btn_width, btn_height])
    btn_fix = Button(ax_fix, 'Auto G', color='0.85')
    state.btn_fix = btn_fix  # Store button in state
    
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
    
    # Convert frequency to kHz for display
    freqs_khz = [f/1000 for f in state.freqs_global]
    state.ax_fft.plot(freqs_khz, state.data_global[0], color='lime')
    state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
    
    # Set appropriate labels positioned to avoid overlap
    state.ax_fft.set_xlabel('Frequency (kHz)', fontsize=10, x=0.25, ha='center')
    state.ax_fft.set_ylabel('Amplitude', fontsize=10)

def setup_navigation_spectrogram():
    """Set up the navigation spectrogram display"""
    # Get normalized data values for better visualization
    vmin, vmax = normalize_spectrogram_data()
    if vmin is None or vmax is None:
        # Fallback to sensible defaults
        vmin, vmax = 0.0, 0.5
    
    # Create the navigation spectrogram with data-driven color limits
    # Use kHz for y-axis - divide frequency values by 1000
    state.nav_spec_img = state.ax_nav_spec.imshow(
        state.data_global.T,
        aspect='auto', origin='lower',
        extent=[0, state.data_global.shape[0]-1, state.freqs_global[0]/1000, state.freqs_global[-1]/1000],
        cmap='viridis',
        vmin=vmin, vmax=vmax,
        alpha=0.7  # Slightly transparent to help highlight stand out
    )
    state.ax_nav_spec.set_title('Navigation View', fontsize=9)
    state.ax_nav_spec.set_ylabel('Freq (kHz)', fontsize=8)
    # Add navigation instructions in a separate text at the right side
    state.ax_nav_spec.text(0.98, 0.98, 'click/drag/scroll to navigate', 
                          transform=state.ax_nav_spec.transAxes,
                          fontsize=7, ha='right', va='top',
                          bbox=dict(facecolor='white', alpha=0.7, pad=2))
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
    # Use kHz for y-axis
    state.ax_nav_spec.set_ylim(state.freqs_global[0]/1000, state.freqs_global[-1]/1000)

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
    # Use kHz for y-axis - divide frequency values by 1000
    state.spec_img = state.ax_spec.imshow(
        state.data_global.T,
        aspect='auto', 
        origin='lower',
        extent=[0, state.data_global.shape[0]-1, state.freqs_global[0]/1000, state.freqs_global[-1]/1000],
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
    
    # Remove bottom margin to eliminate gap
    state.ax_spec.set_position([state.ax_spec.get_position().x0,
                               state.ax_spec.get_position().y0,
                               state.ax_spec.get_position().width,
                               state.ax_spec.get_position().height])
    state.ax_spec.margins(x=0, y=0)
    state.ax_spec.set_adjustable('box')
    
    # Also remove bottom tick padding
    state.ax_spec.tick_params(axis='x', bottom=False, labelbottom=False, length=0, pad=0)
    state.ax_spec.spines['bottom'].set_visible(False)
    
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

def create_comment_section():
    """Create the comment section UI elements"""
    
    # Position comment controls on the left side, just above bottom
    comment_controls_left = 0.02  # Further left
    comment_controls_bottom = 0.15  # Lower position
    
    # Get spectrogram position to align with Comments label (similar to visualization.py)
    spec_pos = state.ax_spec.get_position()
    timeline_height = 0.055
    timeline_bottom = spec_pos.y0 - timeline_height
    
    # Move the position for comment controls even lower
    comment_controls_left = 0.02  # Further left
    comment_controls_bottom = 0.07  # Much lower position
    
    # Add/Edit button - moved to far left and up
    ax_add_comment = state.fig.add_axes([comment_controls_left, comment_controls_bottom, 0.080, 0.025])
    state.btn_add_comment = Button(ax_add_comment, 'Add Comment', color='#e6f2ff')  # Light blue background
    state.btn_add_comment.label.set_fontsize(9)
    
    # Update the button text based on whether a comment is selected
    def update_add_comment_button_text():
        """Update the Add Comment button text based on selection state"""
        if hasattr(state, 'selected_comment_id') and state.selected_comment_id is not None:
            state.btn_add_comment.label.set_text('Edit Comment')
        else:
            state.btn_add_comment.label.set_text('Add Comment')
    
    # Store the function for use elsewhere
    state.update_add_comment_button_text = update_add_comment_button_text
    
    # Initial update
    update_add_comment_button_text()
    
    # Delete button - below Add button
    ax_delete_comment = state.fig.add_axes([comment_controls_left, comment_controls_bottom - 0.030, 0.080, 0.025])
    state.btn_delete_comment = Button(ax_delete_comment, 'Delete Comment', color='0.85')
    state.btn_delete_comment.label.set_fontsize(9)
    # Initially disable if no comment is selected
    if not hasattr(state, 'selected_comment_id') or state.selected_comment_id is None:
        state.btn_delete_comment.ax.set_alpha(0.5)  # Visual indication of disabled state
        
    # Toggle Comments button - below Delete button with same size
    ax_toggle_comments = state.fig.add_axes([comment_controls_left, comment_controls_bottom - 0.060, 0.080, 0.025])
    
    # Set button text according to current comments_visible state
    initial_text = 'Hide Comments'
    if not hasattr(state, 'comments_visible') or not state.comments_visible:
        # If comments aren't visible, set text to "Show Comments"
        initial_text = 'Show Comments'
        # Also update the state for consistency
        state.comments_visible = False
    else:
        # If comments are visible, ensure state is consistent
        state.comments_visible = True
        
    state.btn_toggle_comments = Button(ax_toggle_comments, initial_text, color='0.85')
    state.btn_toggle_comments.label.set_fontsize(9)
    
    # Log the initial button state
    add_log_entry(f"Toggle comments button initialized to '{initial_text}' (comments_visible={state.comments_visible})")
    
    # Create hidden TextBox placeholders for backward compatibility
    # These text boxes are not visible but still exist for functions that reference them
    from matplotlib.widgets import TextBox
    
    # Create tiny, invisible axes for the TextBox widgets
    ax_comment_input = state.fig.add_axes([0.01, 0.01, 0.001, 0.001])
    ax_notes_input = state.fig.add_axes([0.01, 0.01, 0.001, 0.001])
    
    # Create the TextBox widgets but make them invisible
    state.comment_input = TextBox(ax_comment_input, '', initial='')
    state.notes_input = TextBox(ax_notes_input, '', initial='')
    
    # Hide the axes and text boxes
    ax_comment_input.set_visible(False)
    ax_notes_input.set_visible(False)
    
    # Keep the set_val method available for backward compatibility
    # Create a dummy TextBox that just stores text but doesn't render
    class DummyTextBox:
        def __init__(self):
            self.text = ""
            
        def set_val(self, val):
            self.text = val
            return val
            
    # Replace the real TextBox objects with our dummy ones
    state.comment_input = DummyTextBox()
    state.notes_input = DummyTextBox()
    
    add_log_entry("Using modal dialog for comment input - TextBox widgets are hidden")
    
    # Create a dummy Save button for backward compatibility
    # Place it in a tiny, invisible axes
    ax_save_comment = state.fig.add_axes([0.01, 0.01, 0.001, 0.001])
    state.btn_save_comment = Button(ax_save_comment, '', color='white')
    ax_save_comment.set_visible(False)
    
    # We've removed the separate comment display window since
    # notes are now shown directly in the comment list
    state.ax_comment_display = None
    
    # Add section title above comment buttons on the left side
    state.fig.text(comment_controls_left, comment_controls_bottom + 0.030, 'Comment Controls', fontsize=9, 
                   weight='bold', ha='left', va='bottom')
    
    # Remove the old text display since we have a new comment display window
    if hasattr(state, 'ax_comment_text') and state.ax_comment_text is not None:
        state.ax_comment_text.remove()
    
    # Add placeholder event handlers (no logic yet)
    def on_toggle_comments(event):
        from visualization import update_comment_markers
        
        # Toggle visibility state
        state.comments_visible = not state.comments_visible
        add_log_entry(f"Comments visibility: {'ON' if state.comments_visible else 'OFF'}")
        
        # Update comment timeline visualization
        update_comment_markers()
        
        # Update button text to show current state
        if state.comments_visible:
            state.btn_toggle_comments.label.set_text('Hide Comments')
        else:
            state.btn_toggle_comments.label.set_text('Show Comments')
        plt.draw()
    
    def on_add_comment(event):
        add_log_entry("Add comment button clicked")
        try:
            # Release any existing mouse grabs to prevent conflicts
            try:
                event.canvas.release_mouse(event.inaxes)
            except:
                pass  # Ignore if no grab exists
                
            from visualization import display_selected_comment, update_comment_markers
            from modal_comment_input import show_comment_dialog
            
            # Check if a comment is already selected (editing mode)
            existing_comment = None
            if hasattr(state, 'selected_comment_id') and state.selected_comment_id is not None:
                for comment in state.comments:
                    if comment['id'] == state.selected_comment_id:
                        existing_comment = comment
                        add_log_entry(f"Found existing comment for editing: id={comment['id']}, text='{comment['text']}'")
                        # Make sure we have user_notes field even if it doesn't exist
                        if 'user_notes' not in comment:
                            comment['user_notes'] = ""
                        break
            
            # Show different log messages based on mode
            if existing_comment:
                add_log_entry(f"Editing comment {existing_comment['id']}: '{existing_comment['text']}'")
            else:
                add_log_entry("Adding new comment")
            
            # Get the root window from matplotlib's figure canvas
            # The canvas has the tk_widget, which gives us access to the main window
            if not hasattr(state.fig.canvas, 'get_tk_widget'):
                add_log_entry("Error: Canvas does not have tk_widget - cannot show dialog")
                return
                
            # Get the root window
            tk_widget = state.fig.canvas.get_tk_widget()
            root = tk_widget.winfo_toplevel()
            
            # Store it in state for future use
            state.tk_root = root
                
            # Show modal dialog for comment entry
            comment_data = show_comment_dialog(
                start_idx=existing_comment['start_idx'] if existing_comment else None,
                end_idx=existing_comment['end_idx'] if existing_comment else None,
                existing_comment=existing_comment
            )
            
            # If user cancelled, just return
            if not comment_data:
                add_log_entry("Comment operation cancelled")
                return
            
            # Get comment data from dialog
            start_idx = comment_data['start_idx']
            end_idx = comment_data['end_idx']
            comment_text = comment_data['text']
            notes_text = comment_data['user_notes']
            
            add_log_entry(f"Got comment data: text='{comment_text}', range={start_idx}-{end_idx}")
            
            # If we're editing an existing comment, update it
            if existing_comment and 'id' in comment_data:
                add_log_entry(f"Updating comment {existing_comment['id']}: '{comment_text}'")
                
                # Update the existing comment
                for i, comment in enumerate(state.comments):
                    if comment['id'] == comment_data['id']:
                        state.comments[i]['text'] = comment_text
                        state.comments[i]['user_notes'] = notes_text
                        state.comments[i]['start_idx'] = start_idx
                        state.comments[i]['end_idx'] = end_idx
                        
                        # Keep the same comment selected
                        state.selected_comment_id = comment_data['id']
                        break
            else:
                # Create new comment
                add_log_entry(f"Creating new comment: '{comment_text}' at range {start_idx}-{end_idx}")
                
                # Check for overlaps
                overlapping_comments = []
                for comment in state.comments:
                    if (start_idx <= comment['end_idx'] and end_idx >= comment['start_idx']):
                        overlapping_comments.append(comment)
                
                # If overlaps exist, just log for now (could add confirmation later)
                if overlapping_comments:
                    add_log_entry(f"Warning: Comment overlaps with {len(overlapping_comments)} existing comments")
                
                # Create new comment (only if we're not editing)
                new_comment = {
                    'id': state.comment_id_counter,
                    'start_idx': start_idx,
                    'end_idx': end_idx,
                    'text': comment_text,
                    'user_notes': notes_text
                }
                state.comments.append(new_comment)
                state.comment_id_counter += 1
                state.selected_comment_id = new_comment['id']
            
            # Update display
            state.comments_visible = True
            state.btn_toggle_comments.label.set_text('Hide Comments')
            update_comment_markers()
            display_selected_comment()
            
            # Update the comment list if it exists
            if 'comment_list' in sys.modules:
                from comment_list import update_comment_list_display
                update_comment_list_display()
            
            # Update delete button state
            try:
                from ui_state_updates import update_delete_button_state
                update_delete_button_state(state)
            except ImportError:
                pass
            
            add_log_entry(f"Comment saved successfully")
            
        except Exception as e:
            add_log_entry(f"Error in on_add_comment: {str(e)}")
            import traceback
            add_log_entry(f"Traceback: {traceback.format_exc()}")
    
    def on_save_comment(event):
        """Save the comment entered in the text fields (legacy method, using direct modal dialog now)"""
        add_log_entry("Save comment button clicked - redirecting to modal dialog")
        # Just call on_add_comment to use the new modal dialog approach
        on_add_comment(event)
    
    def on_delete_comment(event):
        """Delete the currently selected comment"""
        add_log_entry("Delete comment button clicked")
        
        # Release any existing mouse grabs
        try:
            event.canvas.release_mouse(event.inaxes)
        except:
            pass
        
        # Use the centralized delete function
        from comment_operations import delete_selected_comment
        delete_selected_comment()
    
    # Connect handlers
    state.btn_toggle_comments.on_clicked(on_toggle_comments)
    state.btn_add_comment.on_clicked(on_add_comment)
    state.btn_save_comment.on_clicked(on_save_comment)
    state.btn_delete_comment.on_clicked(on_delete_comment)
    
    add_log_entry("Comment section UI created")