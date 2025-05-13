"""
ui_tabs.py - Implementation of specific tabs for the modernized UI

This module provides the specific tab implementations for:
- Analysis Tab: FFT analysis and measurement tools
- Filter Tab: Background noise filtering and profile management
- Annotations Tab: Adding and managing annotations
- Export Tab: Exporting audio, images, and reports
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Button, Slider, CheckButtons, TextBox
import numpy as np
import logging
import os

# Import state directly
import state
from utils import add_log_entry
from ui_tab_system import TabBase, UIColors
from visualization import auto_adjust_fft_range, update_fft, update_fft_range

class AnalysisTab(TabBase):
    """
    The Analysis Tab provides enhanced FFT analysis tools 
    and visualization controls.
    """
    
    def __init__(self, fig, parent_ax):
        super().__init__(fig, parent_ax)
        self.fft_min_val = 0
        self.fft_max_val = 120
        
    def build(self):
        """Build the Analysis Tab UI"""
        # Create sections
        self.fft_section = self.create_section("FFT Controls", 0.65, 0.30)
        self.measurement_section = self.create_section("Measurements", 0.30, 0.30)
        self.statistics_section = self.create_section("Statistics", 0.05, 0.20)
        
        # FFT Y-axis control buttons
        # Max controls
        self.create_button(
            self.fft_section, "+Max", 
            lambda event: self.adjust_fft_max(10),
            [0.05, 0.70, 0.18, 0.20], (0.18, 0.20),
            color=UIColors.BUTTON_DEFAULT
        )
        
        self.create_button(
            self.fft_section, "-Max", 
            lambda event: self.adjust_fft_max(-10),
            [0.25, 0.70, 0.18, 0.20], (0.18, 0.20),
            color=UIColors.BUTTON_DEFAULT
        )
        
        # Min controls
        self.create_button(
            self.fft_section, "+Min", 
            lambda event: self.adjust_fft_min(10),
            [0.05, 0.45, 0.18, 0.20], (0.18, 0.20),
            color=UIColors.BUTTON_DEFAULT
        )
        
        self.create_button(
            self.fft_section, "-Min", 
            lambda event: self.adjust_fft_min(-10),
            [0.25, 0.45, 0.18, 0.20], (0.18, 0.20),
            color=UIColors.BUTTON_DEFAULT
        )
        
        # Auto button
        self.create_button(
            self.fft_section, "Auto Y", 
            self.on_auto_y,
            [0.05, 0.20, 0.38, 0.20], (0.38, 0.20),
            color=UIColors.ACCENT_BLUE,
            text_color=UIColors.TEXT_PRIMARY
        )
        
        # Reset button
        self.create_button(
            self.fft_section, "Reset", 
            self.on_reset_fft,
            [0.50, 0.45, 0.18, 0.20], (0.18, 0.20),
            color=UIColors.ACCENT_RED,
            text_color=UIColors.TEXT_PRIMARY
        )
        
        # Current range display
        range_ax = plt.Axes(
            self.fig, 
            [0.50, 0.70, 0.45, 0.20],
            frameon=True
        )
        self.fig.add_axes(range_ax)
        range_ax.set_facecolor(UIColors.BACKGROUND_MEDIUM)
        range_ax.set_xticks([])
        range_ax.set_yticks([])
        
        self.range_text = range_ax.text(
            0.5, 0.5, f"Range: {self.fft_min_val:.1f} - {self.fft_max_val:.1f}",
            ha='center', va='center',
            color=UIColors.TEXT_PRIMARY,
            fontsize=10
        )
        
        self.axes["range_display"] = range_ax
        
        # Peak detection controls
        self.create_button(
            self.measurement_section, "Find Peaks", 
            self.on_find_peaks,
            [0.05, 0.70, 0.30, 0.20], (0.30, 0.20),
            color=UIColors.BUTTON_DEFAULT
        )
        
        self.create_button(
            self.measurement_section, "Measure", 
            self.on_measure,
            [0.40, 0.70, 0.30, 0.20], (0.30, 0.20),
            color=UIColors.BUTTON_DEFAULT
        )
        
        self.create_button(
            self.measurement_section, "Clear", 
            self.on_clear_measurements,
            [0.75, 0.70, 0.20, 0.20], (0.20, 0.20),
            color=UIColors.BUTTON_DEFAULT
        )
        
        # Measurement results display
        results_ax = plt.Axes(
            self.fig, 
            [0.05, 0.10, 0.90, 0.50],
            frameon=True
        )
        self.fig.add_axes(results_ax)
        results_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        results_ax.set_xticks([])
        results_ax.set_yticks([])
        
        self.results_text = results_ax.text(
            0.5, 0.5, "No measurements",
            ha='center', va='center',
            color=UIColors.TEXT_PRIMARY,
            fontsize=9
        )
        
        self.axes["results_display"] = results_ax
        
        # Statistics display
        stats_ax = plt.Axes(
            self.fig, 
            [0.05, 0.10, 0.90, 0.80],
            frameon=True
        )
        self.fig.add_axes(stats_ax)
        stats_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        stats_ax.set_xticks([])
        stats_ax.set_yticks([])
        
        self.stats_text = stats_ax.text(
            0.5, 0.5, "No statistics available",
            ha='center', va='center',
            color=UIColors.TEXT_PRIMARY,
            fontsize=9
        )
        
        self.axes["stats_display"] = stats_ax
        
    def adjust_fft_min(self, delta):
        """Adjust the FFT Y-axis minimum value"""
        old_min = self.fft_min_val
        
        # Calculate new value and ensure it's valid
        new_min = max(old_min + delta, -20)  # Don't go below -20
        new_min = min(new_min, self.fft_max_val - 10)  # Ensure gap with max
        
        # Update stored value
        self.fft_min_val = new_min
        
        # Update the actual FFT display
        if hasattr(state, 'ax_fft') and state.ax_fft is not None:
            state.fft_ymin = new_min
            state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
            plt.draw()
            
        # Update range display
        self.update_range_display()
        
        add_log_entry(f"Adjusted FFT minimum to {new_min:.1f}")
        
    def adjust_fft_max(self, delta):
        """Adjust the FFT Y-axis maximum value"""
        old_max = self.fft_max_val
        
        # Calculate new value and ensure it's valid
        new_max = max(old_max + delta, self.fft_min_val + 10)  # Ensure gap with min
        
        # Update stored value
        self.fft_max_val = new_max
        
        # Update the actual FFT display
        if hasattr(state, 'ax_fft') and state.ax_fft is not None:
            state.fft_ymax = new_max
            state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
            plt.draw()
            
        # Update range display
        self.update_range_display()
        
        add_log_entry(f"Adjusted FFT maximum to {new_max:.1f}")
        
    def update_range_display(self):
        """Update the range display text"""
        if hasattr(self, 'range_text'):
            self.range_text.set_text(f"Range: {self.fft_min_val:.1f} - {self.fft_max_val:.1f}")
            plt.draw()
            
    def on_auto_y(self, event):
        """Handle Auto Y button click"""
        # Call the auto-adjust function
        auto_adjust_fft_range()
        
        # Update our stored values to match
        if hasattr(state, 'fft_ymin') and hasattr(state, 'fft_ymax'):
            self.fft_min_val = state.fft_ymin
            self.fft_max_val = state.fft_ymax
            
        # Update range display
        self.update_range_display()
        
    def on_reset_fft(self, event):
        """Handle Reset button click"""
        # Reset to default values
        self.fft_min_val = 0
        self.fft_max_val = 120
        
        # Update the FFT display
        if hasattr(state, 'ax_fft') and state.ax_fft is not None:
            state.fft_ymin = self.fft_min_val
            state.fft_ymax = self.fft_max_val
            state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
            plt.draw()
            
        # Update range display
        self.update_range_display()
        
        add_log_entry("Reset FFT range to defaults")
        
    def on_find_peaks(self, event):
        """Handle Find Peaks button click"""
        # Find peaks in the current FFT data
        if (hasattr(state, 'freqs_global') and 
            hasattr(state, 'data_global') and 
            state.freqs_global is not None and 
            state.data_global is not None):
            
            # Get current selected FFT data
            if hasattr(state, 'spec_click_line') and state.spec_click_line is not None:
                idx = int(state.spec_click_line.get_xdata()[0])
                if 0 <= idx < len(state.data_global):
                    fft_data = state.data_global[idx]
                    
                    # Find peaks in the data
                    from scipy.signal import find_peaks
                    peaks, properties = find_peaks(fft_data, height=self.fft_min_val + 10, distance=5)
                    
                    # Check if any peaks were found
                    if len(peaks) > 0:
                        # Get the frequencies and amplitudes at the peaks
                        peak_freqs = state.freqs_global[peaks]
                        peak_amps = fft_data[peaks]
                        
                        # Sort by amplitude (descending)
                        sort_idx = np.argsort(peak_amps)[::-1]
                        peak_freqs = peak_freqs[sort_idx]
                        peak_amps = peak_amps[sort_idx]
                        
                        # Limit to top 5 peaks
                        if len(peak_freqs) > 5:
                            peak_freqs = peak_freqs[:5]
                            peak_amps = peak_amps[:5]
                            
                        # Update results display
                        results_text = "Top peaks:\n"
                        for i, (freq, amp) in enumerate(zip(peak_freqs, peak_amps)):
                            results_text += f"{i+1}. {freq:.1f} Hz: {amp:.1f} dB\n"
                            
                        self.results_text.set_text(results_text)
                        plt.draw()
                        
                        add_log_entry(f"Found {len(peak_freqs)} peaks in FFT data")
                    else:
                        self.results_text.set_text("No peaks found above threshold")
                        plt.draw()
                        add_log_entry("No peaks found in FFT data")
        
    def on_measure(self, event):
        """Handle Measure button click"""
        # Measure the current FFT data
        if (hasattr(state, 'freqs_global') and 
            hasattr(state, 'data_global') and 
            state.freqs_global is not None and 
            state.data_global is not None):
            
            # Get current FFT data based on selection
            fft_data = None
            if hasattr(state, 'selected_range') and state.selected_range is not None:
                start, end = state.selected_range
                # Get data for all points in the range
                data_points = []
                for i in range(start, end + 1):
                    if 0 <= i < len(state.data_global):
                        data_points.append(state.data_global[i])
                
                if data_points:
                    # Convert to numpy array for easier analysis
                    fft_data = np.vstack(data_points)
                    # Get mean across all FFTs in the range
                    fft_data = np.mean(fft_data, axis=0)
            elif hasattr(state, 'spec_click_line') and state.spec_click_line is not None:
                idx = int(state.spec_click_line.get_xdata()[0])
                if 0 <= idx < len(state.data_global):
                    fft_data = state.data_global[idx]
            
            if fft_data is not None:
                # Calculate some basic stats
                mean_amp = np.mean(fft_data)
                max_amp = np.max(fft_data)
                min_amp = np.min(fft_data)
                std_amp = np.std(fft_data)
                
                # Find the frequency with maximum amplitude
                max_freq_idx = np.argmax(fft_data)
                max_freq = state.freqs_global[max_freq_idx]
                
                # Update results display
                results_text = "FFT Measurements:\n"
                results_text += f"Mean Amplitude: {mean_amp:.1f} dB\n"
                results_text += f"Max Amplitude: {max_amp:.1f} dB at {max_freq:.1f} Hz\n"
                results_text += f"Min Amplitude: {min_amp:.1f} dB\n"
                results_text += f"Std Deviation: {std_amp:.1f} dB"
                
                self.results_text.set_text(results_text)
                plt.draw()
                
                add_log_entry("Measured FFT data")
        
    def on_clear_measurements(self, event):
        """Handle Clear button click"""
        self.results_text.set_text("No measurements")
        plt.draw()
        add_log_entry("Cleared measurements")
        
    def on_show(self):
        """Called when the tab is shown"""
        # Update to current values
        if hasattr(state, 'fft_ymin') and hasattr(state, 'fft_ymax'):
            self.fft_min_val = state.fft_ymin
            self.fft_max_val = state.fft_ymax
            self.update_range_display()
            
        # Update statistics display
        self.update_statistics()
        
    def on_update(self):
        """Called to update the tab"""
        self.update_statistics()
        
    def update_statistics(self):
        """Update the statistics display"""
        # Calculate statistics based on current selection
        if (hasattr(state, 'freqs_global') and 
            hasattr(state, 'data_global') and 
            state.freqs_global is not None and 
            state.data_global is not None):
            
            # Check if we have a selection or single point
            if hasattr(state, 'selected_range') and state.selected_range is not None:
                start, end = state.selected_range
                stats_text = f"Statistics for selection ({start} - {end}):\n"
                
                # Calculate statistics for the selection
                fft_data = []
                for i in range(start, end + 1):
                    if 0 <= i < len(state.data_global):
                        fft_data.append(state.data_global[i])
                
                if fft_data:
                    # Stack all FFT data
                    fft_data = np.vstack(fft_data)
                    
                    # Calculate overall statistics
                    mean_amp = np.mean(fft_data)
                    max_amp = np.max(fft_data)
                    
                    # Find the frequency bands with most energy
                    band_energy = np.sum(fft_data, axis=0)
                    band_idx = np.argsort(band_energy)[::-1][:3]  # Top 3 bands
                    
                    stats_text += f"Mean Amplitude: {mean_amp:.1f} dB\n"
                    stats_text += f"Max Amplitude: {max_amp:.1f} dB\n\n"
                    stats_text += "Top Frequency Bands:\n"
                    
                    for i, idx in enumerate(band_idx):
                        freq = state.freqs_global[idx]
                        energy = band_energy[idx]
                        stats_text += f"{i+1}. {freq:.1f} Hz: {energy:.1f} total energy\n"
                    
                    self.stats_text.set_text(stats_text)
                    plt.draw()
            elif hasattr(state, 'spec_click_line') and state.spec_click_line is not None:
                idx = int(state.spec_click_line.get_xdata()[0])
                stats_text = f"Statistics for point {idx}:\n"
                
                if 0 <= idx < len(state.data_global):
                    fft_data = state.data_global[idx]
                    
                    # Calculate statistics
                    mean_amp = np.mean(fft_data)
                    max_amp = np.max(fft_data)
                    max_idx = np.argmax(fft_data)
                    max_freq = state.freqs_global[max_idx]
                    
                    stats_text += f"Mean Amplitude: {mean_amp:.1f} dB\n"
                    stats_text += f"Max Amplitude: {max_amp:.1f} dB at {max_freq:.1f} Hz\n"
                    
                    # Calculate percentiles
                    p90 = np.percentile(fft_data, 90)
                    p75 = np.percentile(fft_data, 75)
                    stats_text += f"90th Percentile: {p90:.1f} dB\n"
                    stats_text += f"75th Percentile: {p75:.1f} dB"
                    
                    self.stats_text.set_text(stats_text)
                    plt.draw()
            else:
                self.stats_text.set_text("Select a point or range to view statistics")
                plt.draw()


class FilterTab(TabBase):
    """
    The Filter Tab provides tools for background noise filtering
    and profile management.
    """
    
    def __init__(self, fig, parent_ax):
        super().__init__(fig, parent_ax)
        self.noise_profiles = []  # List to store noise profiles
        self.active_profile = None
        self.filter_intensity = 0.5  # Default filter intensity (0-1)
        
    def build(self):
        """Build the Filter Tab UI"""
        # Create sections
        self.capture_section = self.create_section("Capture Background Profile", 0.65, 0.30)
        self.profiles_section = self.create_section("Noise Profiles", 0.30, 0.30)
        self.filtering_section = self.create_section("Apply Filtering", 0.05, 0.20)
        
        # Capture section controls
        self.create_button(
            self.capture_section, "Capture Current Selection", 
            self.on_capture_profile,
            [0.05, 0.70, 0.90, 0.20], (0.90, 0.20),
            color=UIColors.ACCENT_BLUE,
            text_color=UIColors.TEXT_PRIMARY
        )
        
        # Profile name input
        name_ax = plt.Axes(
            self.fig, 
            [0.05, 0.40, 0.60, 0.20],
            frameon=True
        )
        self.fig.add_axes(name_ax)
        name_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        name_ax.set_xticks([])
        name_ax.set_yticks([])
        name_ax.text(0.05, 0.5, "Profile Name:", va='center', fontsize=9)
        
        self.name_input = TextBox(
            name_ax, '', 
            initial='Background Profile',
            color=UIColors.BACKGROUND_LIGHT,
            hovercolor=UIColors.BACKGROUND_LIGHT
        )
        self.name_input.label.set_color(UIColors.TEXT_PRIMARY)
        self.name_input.text_disp.set_color(UIColors.TEXT_PRIMARY)
        
        self.axes["name_input_ax"] = name_ax
        self.components["name_input"] = self.name_input
        
        # Save button
        self.create_button(
            self.capture_section, "Save Profile", 
            self.on_save_profile,
            [0.70, 0.40, 0.25, 0.20], (0.25, 0.20),
            color=UIColors.ACCENT_GREEN,
            text_color=UIColors.TEXT_PRIMARY
        )
        
        # Metadata display
        metadata_ax = plt.Axes(
            self.fig, 
            [0.05, 0.10, 0.90, 0.20],
            frameon=True
        )
        self.fig.add_axes(metadata_ax)
        metadata_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        metadata_ax.set_xticks([])
        metadata_ax.set_yticks([])
        
        self.metadata_text = metadata_ax.text(
            0.02, 0.5, "Selection: None",
            va='center', fontsize=9,
            color=UIColors.TEXT_PRIMARY
        )
        
        self.axes["metadata_display"] = metadata_ax
        
        # Profiles section - list display
        profiles_list_ax = plt.Axes(
            self.fig, 
            [0.05, 0.10, 0.60, 0.80],
            frameon=True
        )
        self.fig.add_axes(profiles_list_ax)
        profiles_list_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        profiles_list_ax.set_xticks([])
        profiles_list_ax.set_yticks([])
        
        self.profiles_text = profiles_list_ax.text(
            0.02, 0.98, "No profiles available",
            va='top', fontsize=9,
            color=UIColors.TEXT_PRIMARY
        )
        
        self.axes["profiles_list"] = profiles_list_ax
        
        # Profile management buttons
        self.create_button(
            self.profiles_section, "Load", 
            self.on_load_profile,
            [0.70, 0.70, 0.25, 0.20], (0.25, 0.20),
            color=UIColors.BUTTON_DEFAULT
        )
        
        self.create_button(
            self.profiles_section, "Delete", 
            self.on_delete_profile,
            [0.70, 0.45, 0.25, 0.20], (0.25, 0.20),
            color=UIColors.BUTTON_DEFAULT
        )
        
        self.create_button(
            self.profiles_section, "Export", 
            self.on_export_profile,
            [0.70, 0.20, 0.25, 0.20], (0.25, 0.20),
            color=UIColors.BUTTON_DEFAULT
        )
        
        # Filtering controls
        # Intensity slider
        intensity_ax = plt.Axes(
            self.fig, 
            [0.25, 0.60, 0.70, 0.20],
            frameon=True
        )
        self.fig.add_axes(intensity_ax)
        intensity_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        intensity_ax.set_xticks([])
        intensity_ax.set_yticks([])
        
        self.intensity_slider = Slider(
            intensity_ax, 'Intensity', 
            0.0, 1.0, valinit=0.5,
            color=UIColors.ACCENT_BLUE
        )
        self.intensity_slider.label.set_color(UIColors.TEXT_PRIMARY)
        self.intensity_slider.valtext.set_color(UIColors.TEXT_PRIMARY)
        
        # Connect callback
        self.intensity_slider.on_changed(self.on_intensity_change)
        
        self.axes["intensity_slider_ax"] = intensity_ax
        self.components["intensity_slider"] = self.intensity_slider
        
        # Label for slider
        intensity_ax.text(
            0.5, 0.8, "Filter Intensity",
            ha='center', va='bottom', fontsize=9,
            color=UIColors.TEXT_PRIMARY
        )
        
        # Toggle buttons for filter on/off
        self.create_button(
            self.filtering_section, "Apply Filter", 
            self.on_toggle_filter,
            [0.05, 0.20, 0.40, 0.30], (0.40, 0.30),
            color=UIColors.BUTTON_DEFAULT
        )
        
        self.create_button(
            self.filtering_section, "Reset", 
            self.on_reset_filter,
            [0.50, 0.20, 0.30, 0.30], (0.30, 0.30),
            color=UIColors.BUTTON_DEFAULT
        )
        
        # Filter status display
        status_ax = plt.Axes(
            self.fig, 
            [0.05, 0.60, 0.15, 0.20],
            frameon=True
        )
        self.fig.add_axes(status_ax)
        status_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        status_ax.set_xticks([])
        status_ax.set_yticks([])
        
        self.status_light = plt.Circle(
            (0.5, 0.5), 0.3, color='gray'
        )
        status_ax.add_patch(self.status_light)
        
        self.status_text = status_ax.text(
            0.5, 0.5, "OFF",
            ha='center', va='center', fontsize=8,
            color=UIColors.TEXT_PRIMARY
        )
        
        self.axes["filter_status"] = status_ax
        
    def on_capture_profile(self, event):
        """Handle Capture Profile button click"""
        # Check if we have a selection
        if hasattr(state, 'selected_range') and state.selected_range is not None:
            start, end = state.selected_range
            
            # Update metadata display
            metadata_text = f"Selection: {start} - {end}\n"
            
            # Add additional metadata if available
            if hasattr(state, 'time_labels_all') and state.time_labels_all is not None:
                start_time = state.time_labels_all[start] if start < len(state.time_labels_all) else "N/A"
                end_time = state.time_labels_all[end] if end < len(state.time_labels_all) else "N/A"
                metadata_text += f"Time: {start_time} - {end_time}\n"
            
            self.metadata_text.set_text(metadata_text)
            plt.draw()
            
            add_log_entry(f"Captured background profile for range {start}-{end}")
        else:
            self.metadata_text.set_text("Selection: None\nSelect a region in the spectrogram first")
            plt.draw()
            add_log_entry("Cannot capture profile - no selection")
            
    def on_save_profile(self, event):
        """Handle Save Profile button click"""
        # Check if we have a valid selection
        if hasattr(state, 'selected_range') and state.selected_range is not None:
            start, end = state.selected_range
            
            # Get the profile name
            profile_name = self.name_input.text
            if not profile_name:
                profile_name = f"Background Profile {len(self.noise_profiles) + 1}"
            
            # Extract the FFT data for the selection
            if (hasattr(state, 'data_global') and 
                state.data_global is not None and 
                start < len(state.data_global) and 
                end < len(state.data_global)):
                
                # Get all FFT data in the selection
                profile_data = []
                for i in range(start, end + 1):
                    profile_data.append(state.data_global[i])
                
                # Convert to numpy array and calculate mean
                profile_data = np.vstack(profile_data)
                mean_profile = np.mean(profile_data, axis=0)
                
                # Create profile object
                profile = {
                    'name': profile_name,
                    'range': (start, end),
                    'data': mean_profile,
                    'time': '',  # Could add timestamp
                    'metadata': {}  # Could add additional metadata
                }
                
                # Add time info if available
                if hasattr(state, 'time_labels_all') and state.time_labels_all is not None:
                    start_time = state.time_labels_all[start] if start < len(state.time_labels_all) else "N/A"
                    end_time = state.time_labels_all[end] if end < len(state.time_labels_all) else "N/A"
                    profile['time'] = f"{start_time} - {end_time}"
                
                # Add to profiles list
                self.noise_profiles.append(profile)
                
                # Update profiles display
                self.update_profiles_display()
                
                add_log_entry(f"Saved background profile '{profile_name}'")
                
                # Clear the input field for next profile
                self.name_input.set_val("")
            else:
                add_log_entry("Cannot save profile - invalid data range")
        else:
            add_log_entry("Cannot save profile - no selection")
            
    def update_profiles_display(self):
        """Update the profiles list display"""
        if not self.noise_profiles:
            self.profiles_text.set_text("No profiles available")
            plt.draw()
            return
            
        # Create profiles list text
        profiles_text = "Available Profiles:\n\n"
        
        for i, profile in enumerate(self.noise_profiles):
            # Mark the active profile
            marker = "→ " if profile == self.active_profile else "  "
            profiles_text += f"{marker}{i+1}. {profile['name']}\n"
            
            # Add range info
            start, end = profile['range']
            profiles_text += f"    Range: {start} - {end}\n"
            
            # Add time info if available
            if profile['time']:
                profiles_text += f"    Time: {profile['time']}\n"
            
            profiles_text += "\n"
            
        self.profiles_text.set_text(profiles_text)
        plt.draw()
        
    def on_load_profile(self, event):
        """Handle Load Profile button click"""
        # For now, just load the first profile if available
        if self.noise_profiles:
            self.active_profile = self.noise_profiles[0]
            self.update_profiles_display()
            
            # Update filter status
            self.status_light.set_color('orange')
            self.status_text.set_text("READY")
            plt.draw()
            
            add_log_entry(f"Loaded profile '{self.active_profile['name']}'")
        else:
            add_log_entry("No profiles available to load")
            
    def on_delete_profile(self, event):
        """Handle Delete Profile button click"""
        # For now, just delete the first profile if available
        if self.noise_profiles:
            deleted_profile = self.noise_profiles.pop(0)
            
            # If we deleted the active profile, clear it
            if deleted_profile == self.active_profile:
                self.active_profile = None
                
                # Update filter status
                self.status_light.set_color('gray')
                self.status_text.set_text("OFF")
                
            self.update_profiles_display()
            plt.draw()
            
            add_log_entry(f"Deleted profile '{deleted_profile['name']}'")
        else:
            add_log_entry("No profiles available to delete")
            
    def on_export_profile(self, event):
        """Handle Export Profile button click"""
        # For now, just log that this would export the profile
        if self.active_profile:
            add_log_entry(f"Export profile '{self.active_profile['name']}' (not implemented)")
        else:
            add_log_entry("No active profile to export")
            
    def on_intensity_change(self, val):
        """Handle intensity slider change"""
        self.filter_intensity = val
        add_log_entry(f"Filter intensity set to {val:.2f}")
        
    def on_toggle_filter(self, event):
        """Handle Apply Filter button click"""
        if self.active_profile:
            # Toggle filter state
            if self.status_text.get_text() == "ON":
                # Turn off filtering
                self.status_light.set_color('orange')
                self.status_text.set_text("READY")
                add_log_entry("Filtering turned off")
            else:
                # Turn on filtering
                self.status_light.set_color('green')
                self.status_text.set_text("ON")
                add_log_entry(f"Filtering turned on (intensity: {self.filter_intensity:.2f})")
        else:
            add_log_entry("Cannot apply filter - no profile loaded")
            
    def on_reset_filter(self, event):
        """Handle Reset button click"""
        # Reset filtering state
        self.status_light.set_color('gray')
        self.status_text.set_text("OFF")
        self.active_profile = None
        self.update_profiles_display()
        plt.draw()
        
        add_log_entry("Reset filtering")
        
    def on_show(self):
        """Called when the tab is shown"""
        # Update to current values
        self.update_profiles_display()
        
        # Update metadata based on current selection
        if hasattr(state, 'selected_range') and state.selected_range is not None:
            start, end = state.selected_range
            metadata_text = f"Selection: {start} - {end}\n"
            
            # Add additional metadata if available
            if hasattr(state, 'time_labels_all') and state.time_labels_all is not None:
                start_time = state.time_labels_all[start] if start < len(state.time_labels_all) else "N/A"
                end_time = state.time_labels_all[end] if end < len(state.time_labels_all) else "N/A"
                metadata_text += f"Time: {start_time} - {end_time}\n"
            
            self.metadata_text.set_text(metadata_text)
        else:
            self.metadata_text.set_text("Selection: None\nSelect a region in the spectrogram first")


class AnnotationsTab(TabBase):
    """
    The Annotations Tab provides tools for adding and managing
    annotations on the spectrogram.
    """
    
    def __init__(self, fig, parent_ax):
        super().__init__(fig, parent_ax)
        self.annotations = []  # List to store annotations
        self.current_annotation = None  # Currently selected annotation
        
    def build(self):
        """Build the Annotations Tab UI"""
        # Create sections
        self.create_section = self.create_section("Create Annotation", 0.70, 0.25)
        self.list_section = self.create_section("Annotations List", 0.35, 0.30)
        self.edit_section = self.create_section("Edit Annotation", 0.05, 0.25)
        
        # Create section controls
        self.create_button(
            self.create_section, "Add Annotation", 
            self.on_add_annotation,
            [0.05, 0.60, 0.40, 0.30], (0.40, 0.30),
            color=UIColors.ACCENT_BLUE,
            text_color=UIColors.TEXT_PRIMARY
        )
        
        # Classification dropdown
        class_ax = plt.Axes(
            self.fig, 
            [0.50, 0.60, 0.45, 0.30],
            frameon=True
        )
        self.fig.add_axes(class_ax)
        class_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        class_ax.set_xticks([])
        class_ax.set_yticks([])
        
        # Add label
        class_ax.text(0.5, 0.9, "Classification", ha='center', va='top', fontsize=9)
        
        # Add radio buttons for classification
        class_ax.set_visible(False)  # Hide until implemented
        
        self.axes["classification_ax"] = class_ax
        
        # Label for current selection
        self.create_button(
            self.create_section, "Clear Selection", 
            self.on_clear_selection,
            [0.05, 0.10, 0.40, 0.30], (0.40, 0.30),
            color=UIColors.BUTTON_DEFAULT
        )
        
        selection_ax = plt.Axes(
            self.fig, 
            [0.50, 0.10, 0.45, 0.30],
            frameon=True
        )
        self.fig.add_axes(selection_ax)
        selection_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        selection_ax.set_xticks([])
        selection_ax.set_yticks([])
        
        self.selection_text = selection_ax.text(
            0.5, 0.5, "No selection",
            ha='center', va='center', fontsize=9,
            color=UIColors.TEXT_PRIMARY
        )
        
        self.axes["selection_display"] = selection_ax
        
        # Annotations list
        list_ax = plt.Axes(
            self.fig, 
            [0.05, 0.10, 0.90, 0.80],
            frameon=True
        )
        self.fig.add_axes(list_ax)
        list_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        list_ax.set_xticks([])
        list_ax.set_yticks([])
        
        self.annotations_text = list_ax.text(
            0.02, 0.98, "No annotations",
            va='top', fontsize=9,
            color=UIColors.TEXT_PRIMARY
        )
        
        self.axes["annotations_list"] = list_ax
        
        # Edit section controls
        comment_ax = plt.Axes(
            self.fig, 
            [0.05, 0.40, 0.90, 0.40],
            frameon=True
        )
        self.fig.add_axes(comment_ax)
        comment_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        comment_ax.set_xticks([])
        comment_ax.set_yticks([])
        comment_ax.text(0.02, 0.95, "Comment:", va='top', fontsize=9)
        
        # Comment box (placeholder - not functional)
        comment_ax.set_visible(False)
        
        self.axes["comment_box"] = comment_ax
        
        # Edit buttons
        self.create_button(
            self.edit_section, "Delete", 
            self.on_delete_annotation,
            [0.05, 0.10, 0.28, 0.25], (0.28, 0.25),
            color=UIColors.ACCENT_RED,
            text_color=UIColors.TEXT_PRIMARY
        )
        
        self.create_button(
            self.edit_section, "Jump To", 
            self.on_jump_to_annotation,
            [0.38, 0.10, 0.28, 0.25], (0.28, 0.25),
            color=UIColors.BUTTON_DEFAULT
        )
        
        self.create_button(
            self.edit_section, "Export", 
            self.on_export_annotations,
            [0.71, 0.10, 0.24, 0.25], (0.24, 0.25),
            color=UIColors.BUTTON_DEFAULT
        )
        
    def on_add_annotation(self, event):
        """Handle Add Annotation button click"""
        # Check if we have a selection
        if hasattr(state, 'selected_range') and state.selected_range is not None:
            start, end = state.selected_range
            
            # Create annotation object
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            annotation = {
                'id': len(self.annotations) + 1,
                'range': (start, end),
                'classification': "General",
                'comment': "",
                'time_created': timestamp,
                'color': UIColors.ACCENT_YELLOW
            }
            
            # Add time info if available
            if hasattr(state, 'time_labels_all') and state.time_labels_all is not None:
                if start < len(state.time_labels_all) and end < len(state.time_labels_all):
                    annotation['time_range'] = f"{state.time_labels_all[start]} - {state.time_labels_all[end]}"
            
            # Add to annotations list
            self.annotations.append(annotation)
            
            # Update annotations display
            self.update_annotations_display()
            
            # Highlight the annotation on the spectrogram
            self.highlight_annotation(annotation)
            
            add_log_entry(f"Added annotation at range {start}-{end}")
        else:
            add_log_entry("Cannot add annotation - no selection")
            
    def on_clear_selection(self, event):
        """Handle Clear Selection button click"""
        # Clear the current selection
        if hasattr(state, 'fft_patch') and state.fft_patch is not None:
            state.fft_patch.remove()
            state.fft_patch = None
            state.selected_range = None
            
            # Update selection display
            self.selection_text.set_text("No selection")
            plt.draw()
            
            add_log_entry("Cleared selection")
        
    def update_annotations_display(self):
        """Update the annotations list display"""
        if not self.annotations:
            self.annotations_text.set_text("No annotations")
            plt.draw()
            return
            
        # Create annotations list text
        annotations_text = ""
        
        for i, annotation in enumerate(self.annotations):
            # Get range info
            start, end = annotation['range']
            
            # Mark the current annotation
            marker = "→ " if annotation == self.current_annotation else "  "
            annotations_text += f"{marker}{annotation['id']}. Range: {start}-{end}\n"
            
            # Add classification
            annotations_text += f"    Type: {annotation['classification']}\n"
            
            # Add time info if available
            if 'time_range' in annotation:
                annotations_text += f"    Time: {annotation['time_range']}\n"
            
            # Add a portion of the comment if available
            if annotation['comment']:
                # Truncate comment if too long
                comment = annotation['comment']
                if len(comment) > 30:
                    comment = comment[:27] + "..."
                annotations_text += f"    Comment: {comment}\n"
            
            annotations_text += "\n"
            
        self.annotations_text.set_text(annotations_text)
        plt.draw()
        
    def highlight_annotation(self, annotation):
        """Highlight an annotation on the spectrogram"""
        # This would create a visual highlight for the annotation
        # Not fully implemented in this example
        
        # Just update the current annotation for now
        self.current_annotation = annotation
        
        # Update selection display
        start, end = annotation['range']
        selection_text = f"Selection: {start}-{end}\n"
        selection_text += f"Type: {annotation['classification']}"
        self.selection_text.set_text(selection_text)
        plt.draw()
        
    def on_delete_annotation(self, event):
        """Handle Delete Annotation button click"""
        # Delete the current annotation if one is selected
        if self.current_annotation:
            self.annotations.remove(self.current_annotation)
            add_log_entry(f"Deleted annotation {self.current_annotation['id']}")
            
            self.current_annotation = None
            self.update_annotations_display()
            
            # Update selection display
            self.selection_text.set_text("No selection")
            plt.draw()
        else:
            add_log_entry("No annotation selected to delete")
            
    def on_jump_to_annotation(self, event):
        """Handle Jump To button click"""
        # Jump to the current annotation if one is selected
        if self.current_annotation:
            start, end = self.current_annotation['range']
            
            # Set the selection range
            state.selected_range = (start, end)
            
            # Update the FFT display
            update_fft_range(start, end, state.freqs_global, state.data_global)
            
            # Create or update the selection patch
            if hasattr(state, 'fft_patch') and state.fft_patch is not None:
                state.fft_patch.remove()
            
            state.fft_patch = state.ax_spec.axvspan(start, end, color='red', alpha=0.3)
            plt.draw()
            
            add_log_entry(f"Jumped to annotation {self.current_annotation['id']}")
        else:
            add_log_entry("No annotation selected to jump to")
            
    def on_export_annotations(self, event):
        """Handle Export Annotations button click"""
        if self.annotations:
            # This would export all annotations
            # Not fully implemented in this example
            add_log_entry(f"Export {len(self.annotations)} annotations (not implemented)")
        else:
            add_log_entry("No annotations to export")
        
    def on_show(self):
        """Called when the tab is shown"""
        # Update displays
        self.update_annotations_display()
        
        # Update selection display
        if hasattr(state, 'selected_range') and state.selected_range is not None:
            start, end = state.selected_range
            self.selection_text.set_text(f"Selection: {start}-{end}")
        else:
            self.selection_text.set_text("No selection")


class ExportTab(TabBase):
    """
    The Export Tab provides tools for exporting audio, images,
    and reports.
    """
    
    def __init__(self, fig, parent_ax):
        super().__init__(fig, parent_ax)
        
    def build(self):
        """Build the Export Tab UI"""
        # Create sections
        self.audio_section = self.create_section("Export Audio", 0.70, 0.25)
        self.image_section = self.create_section("Export Images", 0.40, 0.25)
        self.report_section = self.create_section("Generate Report", 0.10, 0.25)
        
        # Audio export controls
        self.create_button(
            self.audio_section, "Export Selected Audio", 
            self.on_export_audio,
            [0.05, 0.55, 0.40, 0.35], (0.40, 0.35),
            color=UIColors.ACCENT_BLUE,
            text_color=UIColors.TEXT_PRIMARY
        )
        
        # Format selection
        format_ax = plt.Axes(
            self.fig, 
            [0.50, 0.55, 0.45, 0.35],
            frameon=True
        )
        self.fig.add_axes(format_ax)
        format_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        format_ax.set_xticks([])
        format_ax.set_yticks([])
        
        format_ax.text(0.5, 0.9, "Format", ha='center', va='top', fontsize=9)
        
        # Create radio buttons for format
        # Note: not fully implemented
        format_ax.set_visible(False)
        
        self.axes["format_selection"] = format_ax
        
        # Selection info
        selection_ax = plt.Axes(
            self.fig, 
            [0.05, 0.10, 0.90, 0.35],
            frameon=True
        )
        self.fig.add_axes(selection_ax)
        selection_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        selection_ax.set_xticks([])
        selection_ax.set_yticks([])
        
        self.selection_text = selection_ax.text(
            0.02, 0.5, "No audio selected for export",
            va='center', fontsize=9,
            color=UIColors.TEXT_PRIMARY
        )
        
        self.axes["audio_selection"] = selection_ax
        
        # Image export controls
        self.create_button(
            self.image_section, "Export Spectrogram", 
            self.on_export_spectrogram,
            [0.05, 0.55, 0.40, 0.35], (0.40, 0.35),
            color=UIColors.ACCENT_BLUE,
            text_color=UIColors.TEXT_PRIMARY
        )
        
        self.create_button(
            self.image_section, "Export FFT Plot", 
            self.on_export_fft,
            [0.50, 0.55, 0.40, 0.35], (0.40, 0.35),
            color=UIColors.ACCENT_BLUE,
            text_color=UIColors.TEXT_PRIMARY
        )
        
        # Include annotations checkbox
        annotations_ax = plt.Axes(
            self.fig, 
            [0.05, 0.10, 0.40, 0.35],
            frameon=True
        )
        self.fig.add_axes(annotations_ax)
        annotations_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        annotations_ax.set_xticks([])
        annotations_ax.set_yticks([])
        
        # Add a checkbox for including annotations
        # Note: not fully implemented
        annotations_ax.set_visible(False)
        
        self.axes["annotations_checkbox"] = annotations_ax
        
        # Resolution selection
        resolution_ax = plt.Axes(
            self.fig, 
            [0.50, 0.10, 0.45, 0.35],
            frameon=True
        )
        self.fig.add_axes(resolution_ax)
        resolution_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        resolution_ax.set_xticks([])
        resolution_ax.set_yticks([])
        
        resolution_ax.text(0.5, 0.9, "Resolution", ha='center', va='top', fontsize=9)
        
        # Create radio buttons for resolution
        # Note: not fully implemented
        resolution_ax.set_visible(False)
        
        self.axes["resolution_selection"] = resolution_ax
        
        # Report controls
        self.create_button(
            self.report_section, "Generate Report", 
            self.on_generate_report,
            [0.05, 0.60, 0.90, 0.30], (0.90, 0.30),
            color=UIColors.ACCENT_BLUE,
            text_color=UIColors.TEXT_PRIMARY
        )
        
        # Report options
        options_ax = plt.Axes(
            self.fig, 
            [0.05, 0.10, 0.90, 0.40],
            frameon=True
        )
        self.fig.add_axes(options_ax)
        options_ax.set_facecolor(UIColors.BACKGROUND_LIGHT)
        options_ax.set_xticks([])
        options_ax.set_yticks([])
        
        options_ax.text(0.5, 0.9, "Report Options", ha='center', va='top', fontsize=9)
        
        # Create checkboxes for report options
        # Note: not fully implemented
        options_ax.set_visible(False)
        
        self.axes["report_options"] = options_ax
        
    def on_export_audio(self, event):
        """Handle Export Audio button click"""
        # Check if we have a selection
        if hasattr(state, 'selected_range') and state.selected_range is not None:
            start, end = state.selected_range
            
            # Log that this would export the audio
            add_log_entry(f"Export audio for range {start}-{end} (not implemented)")
            
            # Update selection display
            self.selection_text.set_text(f"Selected audio: {start}-{end}\nDuration: {end - start} seconds")
            plt.draw()
        else:
            add_log_entry("Cannot export audio - no selection")
            self.selection_text.set_text("No audio selected for export")
            plt.draw()
            
    def on_export_spectrogram(self, event):
        """Handle Export Spectrogram button click"""
        add_log_entry("Export spectrogram (not implemented)")
        
    def on_export_fft(self, event):
        """Handle Export FFT Plot button click"""
        add_log_entry("Export FFT plot (not implemented)")
        
    def on_generate_report(self, event):
        """Handle Generate Report button click"""
        add_log_entry("Generate report (not implemented)")
        
    def on_show(self):
        """Called when the tab is shown"""
        # Update selection display
        if hasattr(state, 'selected_range') and state.selected_range is not None:
            start, end = state.selected_range
            self.selection_text.set_text(f"Selected audio: {start}-{end}\nDuration: {end - start} seconds")
        else:
            self.selection_text.set_text("No audio selected for export")