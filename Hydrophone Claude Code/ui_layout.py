"""
ui_layout.py - Modern layout for the hydrophone visualization program

This module provides the new layout implementation with the tabbed interface.
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Button, Slider, RangeSlider, RadioButtons
import numpy as np
import logging

# Import state directly
import state
from utils import add_log_entry

# Import tab system
from ui_tab_system import TabManager, UIColors, apply_modern_style
from ui_tabs import AnalysisTab, FilterTab, AnnotationsTab, ExportTab

# Import other necessary components
from event_handlers import setup_event_handlers
from visualization import update_fft_range


def create_modern_layout(fig):
    """
    Create the modernized layout with tabbed interface.
    
    Args:
        fig: The main figure
    """
    # Apply modern style
    apply_modern_style()
    
    # Set up the grid layout
    # We'll use a 5x2 grid:
    # 0,0: Main spectrogram
    # 1,0: Navigation spectrogram
    # 2,0: Audio timeline
    # 3,0: Audio controls
    # 4,*: Status bar (spans both columns)
    # 0,1: Tab control bar
    # 1-3,1: Tab content area
    
    grid = gridspec.GridSpec(5, 2, height_ratios=[4, 1, 0.5, 0.5, 0.4], width_ratios=[3, 1])
    
    # Create the main spectrogram axes
    state.ax_spec = fig.add_subplot(grid[0, 0])
    state.ax_spec.set_facecolor('black')
    state.ax_spec.set_title("Spectrogram", fontsize=12, pad=10)
    
    # Create the navigation spectrogram axes
    state.ax_nav_spec = fig.add_subplot(grid[1, 0])
    state.ax_nav_spec.set_facecolor('black')
    state.ax_nav_spec.set_title("Navigation", fontsize=10, pad=8)
    
    # Create the audio timeline axes
    state.ax_audio_timeline = fig.add_subplot(grid[2, 0])
    state.ax_audio_timeline.set_facecolor('black')
    state.ax_audio_timeline.set_title("Audio Timeline", fontsize=10, pad=8)
    
    # Create the audio control axes
    state.ax_audio_controls = fig.add_subplot(grid[3, 0])
    state.ax_audio_controls.set_facecolor(UIColors.BACKGROUND_MEDIUM)
    state.ax_audio_controls.set_xticks([])
    state.ax_audio_controls.set_yticks([])
    state.ax_audio_controls.set_title("Audio Controls", fontsize=10, pad=8)
    
    # Create the status bar axes
    state.ax_status = fig.add_subplot(grid[4, :])
    state.ax_status.set_facecolor(UIColors.BACKGROUND_DARK)
    state.ax_status.set_xticks([])
    state.ax_status.set_yticks([])
    
    # Create the FFT axes in the audio controls area
    # This is just temporary - it will be replaced by proper controls
    # The actual FFT display will be in the Analysis tab
    state.ax_fft = fig.add_axes([0.05, 0.18, 0.3, 0.15])
    state.ax_fft.set_facecolor('black')
    state.ax_fft.set_title("FFT Display", fontsize=10, pad=8)
    state.ax_fft.set_ylabel("Amplitude (dB)")
    state.ax_fft.set_xlabel("Frequency (Hz)")
    
    # Set default FFT y-axis limits
    state.fft_ymin = 0
    state.fft_ymax = 120
    state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
    
    # Create audio play button
    state.ax_audio_play = fig.add_axes([0.42, 0.18, 0.1, 0.05])
    state.btn_audio_play = Button(state.ax_audio_play, 'Play Audio', color='0.85')
    
    # Create audio visualizer
    state.ax_audio_visualizer = fig.add_axes([0.55, 0.17, 0.2, 0.07])
    state.ax_audio_visualizer.set_facecolor('black')
    state.ax_audio_visualizer.set_title("Audio Waveform", fontsize=9, pad=4)
    state.ax_audio_visualizer.set_xticks([])
    state.ax_audio_visualizer.set_yticks([])
    
    # Create VU meter
    state.ax_vu_meter = fig.add_axes([0.78, 0.17, 0.15, 0.07])
    state.ax_vu_meter.set_facecolor('black')
    state.ax_vu_meter.set_title("VU Meter", fontsize=9, pad=4)
    state.ax_vu_meter.set_xticks([])
    state.ax_vu_meter.set_yticks([])
    
    # Setup log display in status bar
    state.ax_log = fig.add_axes([0.01, 0.01, 0.98, 0.05])
    state.ax_log.set_facecolor(UIColors.BACKGROUND_DARK)
    state.ax_log.set_xticks([])
    state.ax_log.set_yticks([])
    
    # Initialize the tab manager
    tab_manager = TabManager(fig, grid)
    
    # Add the tabs
    tab_manager.add_tab('analysis', AnalysisTab)
    tab_manager.add_tab('filter', FilterTab)
    tab_manager.add_tab('annotations', AnnotationsTab)
    tab_manager.add_tab('export', ExportTab)
    
    # Create the tab buttons
    tab_manager.create_tab_buttons()
    
    # Activate the first tab by default
    tab_manager.switch_to_tab('analysis')
    
    # Set up event handlers
    setup_event_handlers(fig)
    
    return fig


def setup_audio_controls(fig):
    """
    Set up the audio controls in the audio controls axes.
    
    Args:
        fig: The main figure
    """
    # Note: This is a simplified version without all controls
    # Audio controls location
    ax_audio_volume = fig.add_axes([0.42, 0.12, 0.1, 0.02])
    state.audio_volume_slider = Slider(
        ax_audio_volume, 'Volume', 
        0.0, 1.0, valinit=0.5,
        color=UIColors.ACCENT_BLUE
    )
    
    # Set label colors
    state.audio_volume_slider.label.set_color(UIColors.TEXT_PRIMARY)
    state.audio_volume_slider.valtext.set_color(UIColors.TEXT_PRIMARY)
    
    # Create time display
    state.ax_time_display = fig.add_axes([0.55, 0.12, 0.2, 0.03])
    state.ax_time_display.set_facecolor(UIColors.BACKGROUND_DARK)
    state.ax_time_display.set_xticks([])
    state.ax_time_display.set_yticks([])
    state.time_text = state.ax_time_display.text(
        0.5, 0.5, "Time: 0:00 / 0:00",
        ha='center', va='center', fontsize=8,
        color=UIColors.TEXT_PRIMARY
    )


def update_ui_for_data():
    """
    Update the UI after data is loaded.
    """
    # Update the spectrogram display
    if hasattr(state, 'spec_img') and state.spec_img is not None:
        # Set a modern colormap
        state.spec_img.set_cmap(UIColors.get_modern_cmap())
        plt.draw()
    
    # Set the navigation range
    if hasattr(state, 'data_global') and state.data_global is not None:
        # Set initial view to show all data
        state.time_zoom_start = 0
        state.time_zoom_end = len(state.data_global) - 1
        
        # Update the spectrogram view
        if state.ax_spec:
            state.ax_spec.set_xlim(state.time_zoom_start, state.time_zoom_end)
            
        # Update the audio timeline view
        if state.ax_audio_timeline:
            state.ax_audio_timeline.set_xlim(state.time_zoom_start, state.time_zoom_end)
    
    # Update tab displays
    if hasattr(state, 'tab_manager') and state.tab_manager is not None:
        state.tab_manager.update_active_tab()


def initialize_ui(fig):
    """
    Initialize the UI with the modern layout.
    
    Args:
        fig: The main figure
    """
    # Create the modern layout
    create_modern_layout(fig)
    
    # Setup audio controls
    setup_audio_controls(fig)
    
    # Make sure the figure is properly sized
    fig.set_size_inches(14, 8)
    
    # Set window title
    fig.canvas.manager.set_window_title("Hydrophone Analyzer - Modern UI")
    
    return fig