"""
visualization.py - Functions for visualizing hydrophone data
"""

import matplotlib.pyplot as plt
import numpy as np
import logging
from matplotlib.transforms import blended_transform_factory

# Import state directly
import state

from utils import add_log_entry, update_spectrogram_xaxis

def update_fft(idx, freqs, data):
    """Update the FFT display for a specific index"""
    if state.ax_fft is None:
        return
        
    # Clear only lines, not all artists
    for line in state.ax_fft.lines[:]:
        line.remove()
    
    # Keep the existing properties
    state.ax_fft.set_facecolor('black')
    state.ax_fft.grid(True, axis='y', linestyle='--', color='gray', alpha=0.3)
    state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
    state.ax_fft.set_xlim(freqs[0], freqs[-1])
    
    # Don't set title repeatedly
    
    # Plot new data
    state.ax_fft.plot(freqs, data[idx], color='lime')
    
    # Re-draw frequency markers if they exist
    for i, (_, _, _, freq, hline) in enumerate(state.freq_markers):
        if freq is not None:
            color = 'red' if i == 0 else 'blue'
            line = state.ax_fft.axvline(freq, color=color)
            state.freq_markers[i] = (line, None, i, freq, hline)

def update_fft_range(start, end, freqs, data):
    """Update the FFT display for a range of indices (stacked)"""
    if state.ax_fft is None:
        return
        
    # Clear only lines, not all artists
    for line in state.ax_fft.lines[:]:
        line.remove()
    
    # Keep the existing properties
    state.ax_fft.set_facecolor('black')
    state.ax_fft.grid(True, axis='y', linestyle='--', color='gray', alpha=0.3)
    state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
    state.ax_fft.set_xlim(freqs[0], freqs[-1])
    
    # Don't set title repeatedly
    
    # Stack multiple curves from the range
    num_curves = min(100, end - start + 1)  # Limit to max 100 curves
    increment = (end - start) / (num_curves - 1) if num_curves > 1 else 1
    alpha_values = np.linspace(0.1, 1.0, num_curves)
    
    for i in range(num_curves):
        idx = min(int(start + i * increment), len(data) - 1)
        state.ax_fft.plot(freqs, data[idx], color='lime', alpha=alpha_values[i], linewidth=0.8)
    
    # Re-draw frequency markers if they exist
    for i, (_, _, _, freq, hline) in enumerate(state.freq_markers):
        if freq is not None:
            color = 'red' if i == 0 else 'blue'
            line = state.ax_fft.axvline(freq, color=color)
            state.freq_markers[i] = (line, None, i, freq, hline)

def update_marker(n, xpos):
    """Update frequency marker"""
    # Update state
    if n < len(state.freq_markers):
        vline, text, index, old_freq, hline = state.freq_markers[n]
        
        # Remove old lines
        if vline is not None:
            try:
                vline.remove()
            except:
                pass
        if text is not None:
            try:
                text.remove()
            except:
                pass
        if hline is not None:
            try:
                hline.remove()
            except:
                pass
                
        # Create new lines
        color = 'red' if n == 0 else 'blue'
        vline = state.ax_fft.axvline(xpos, color=color, linestyle='-', linewidth=1, alpha=0.8)
        
        # Add horizontal line and amplitude text in the data at this frequency
        # Find the closest data sample to the selected frequency
        if state.spec_click_line is not None:
            time_idx = int(state.spec_click_line.get_xdata()[0])
            if 0 <= time_idx < len(state.data_global):
                freq_data = state.data_global[time_idx]
                freq_idx = np.abs(state.freqs_global - xpos).argmin()
                if 0 <= freq_idx < len(freq_data):
                    amp = freq_data[freq_idx]
                    
                    # Add horizontal line at amplitude level
                    hline = state.ax_fft.axhline(amp, color=color, linestyle='--', linewidth=1, alpha=0.8,
                                        xmin=0.95 * (xpos / state.freqs_global[-1]))
                    
                    # Add text label
                    text = state.ax_fft.text(xpos, amp, f"{xpos:.1f} Hz\n{amp:.1f} dB", color=color,
                                        fontsize=8, ha='left', va='bottom', bbox=dict(
                                            facecolor='black', alpha=0.7, boxstyle='round'))
                else:
                    text = state.ax_fft.text(xpos, state.fft_ymax * 0.8, f"{xpos:.1f} Hz",
                                        color=color, fontsize=8, ha='left', va='bottom')
                    hline = None
            else:
                text = state.ax_fft.text(xpos, state.fft_ymax * 0.8, f"{xpos:.1f} Hz",
                                    color=color, fontsize=8, ha='left', va='bottom')
                hline = None
        else:
            text = state.ax_fft.text(xpos, state.fft_ymax * 0.8, f"{xpos:.1f} Hz",
                                color=color, fontsize=8, ha='left', va='bottom')
            hline = None
            
        # Update state with the new elements
        state.freq_markers[n] = (vline, text, n, xpos, hline)
        
        # Update text for info display
        if state.ax_info:
            hz_text = f"{xpos:.1f} Hz"
            
            try:
                if n == 0 and xpos > 0:
                    state.info_labels['marker1'].set_text(f"Marker 1: {hz_text}")
                elif n == 1 and xpos > 0:
                    state.info_labels['marker2'].set_text(f"Marker 2: {hz_text}")
                    
                # If both markers are set, calculate and display difference
                if (state.freq_markers[0][3] is not None and 
                    state.freq_markers[1][3] is not None and 
                    state.freq_markers[0][3] > 0 and 
                    state.freq_markers[1][3] > 0):
                    
                    freq1 = state.freq_markers[0][3]
                    freq2 = state.freq_markers[1][3]
                    diff = abs(freq2 - freq1)
                    state.info_labels['diff'].set_text(f"Difference: {diff:.1f} Hz")
            except (KeyError, AttributeError) as e:
                logging.warning(f"Error updating info labels: {e}")
        
        # Force a redraw
        plt.draw()

def normalize_data(data):
    """Normalize data to a good range for display"""
    try:
        # Skip empty data
        if data is None or len(data) == 0:
            return 0, 1
            
        # Remove infinities and NaNs
        valid_data = data[np.isfinite(data)]
        
        if len(valid_data) == 0:
            return 0, 1
            
        # Get min/max
        vmin = np.min(valid_data)
        vmax = np.max(valid_data)
        
        # If all values are the same, use a default range
        if vmin == vmax:
            vmean = vmin
            vmin = vmean - 0.05
            vmax = vmean + 0.05
            
        add_log_entry(f"Data range analysis: min={np.min(valid_data):.4f}, max={np.max(valid_data):.4f}")
        add_log_entry(f"Normalized range: vmin={vmin:.4f}, vmax={vmax:.4f}")
        
        return vmin, vmax
        
    except Exception as e:
        add_log_entry(f"Error normalizing data: {str(e)}")
        logging.error(f"Error normalizing data: {str(e)}", exc_info=True)
        return 0, 1  # Default values

def update_time_zoom(val):
    """Update the time zoom based on values"""
    state.time_zoom_start, state.time_zoom_end = val
    
    # Debug logging
    add_log_entry(f"update_time_zoom called: {state.time_zoom_start} - {state.time_zoom_end}")
    
    # Ensure values are integers
    state.time_zoom_start = int(state.time_zoom_start)
    state.time_zoom_end = int(state.time_zoom_end)
    
    # Update spectrogram x-axis limits
    if state.ax_spec:
        state.ax_spec.set_xlim(state.time_zoom_start, state.time_zoom_end)
        add_log_entry(f"Updated spec xlim: {state.time_zoom_start} - {state.time_zoom_end}")
    else:
        add_log_entry("ax_spec is None!")
    
    # Update spectrogram x-axis labels
    update_spectrogram_xaxis()
    
    # Update audio timeline x-axis limits
    if state.ax_audio_timeline:
        state.ax_audio_timeline.set_xlim(state.time_zoom_start, state.time_zoom_end)
    
    # Update navigation box and visual elements
    if state.ax_nav_spec:
        width = state.time_zoom_end - state.time_zoom_start
        handle_width = width * 0.05
        
        add_log_entry(f"Updating nav box with width: {width}")
        
        # Clear and redraw all navigation elements
        # Remove old patches except the spectrogram image
        for patch in state.ax_nav_spec.patches[:]:
            patch.remove()
            
        # Redraw navigation box - thick red border
        state.nav_box = plt.Rectangle((state.time_zoom_start, state.freqs_global[0]), 
                               width, 
                               state.freqs_global[-1] - state.freqs_global[0],
                               fill=False, edgecolor='red', linewidth=3, alpha=1.0,
                               zorder=10)
        state.ax_nav_spec.add_patch(state.nav_box)
        
        # Redraw white highlight
        nav_highlight = plt.Rectangle((state.time_zoom_start, state.freqs_global[0]), 
                                     width, 
                                     state.freqs_global[-1] - state.freqs_global[0],
                                     fill=True, facecolor='white', alpha=0.2,
                                     zorder=5)
        state.ax_nav_spec.add_patch(nav_highlight)
        
        # Redraw edge handles
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
        
        # Update position indicator text
        for text in state.ax_nav_spec.texts[:]:
            text.remove()
            
        zoom_percent = (width / (len(state.data_global) - 1)) * 100
        center_idx = int((state.time_zoom_start + state.time_zoom_end) / 2)
        if 0 <= center_idx < len(state.time_labels_all):
            center_time = state.time_labels_all[center_idx]
        else:
            center_time = "N/A"
            
        position_text = state.ax_nav_spec.text(0.02, 0.95, 
                                       f'Zoom: {zoom_percent:.0f}% | Center: {center_time}', 
                                       transform=state.ax_nav_spec.transAxes, 
                                       fontsize=8, color='white', va='top',
                                       bbox=dict(boxstyle="round,pad=0.3", 
                                               facecolor='black', alpha=0.7))
    else:
        add_log_entry("ax_nav_spec is None!")
        
    # Force a redraw
    plt.draw()

def fix_spectrogram():
    """Fix the spectrogram display - restore settings like color map, etc."""
    if not hasattr(state, 'spec_img') or state.spec_img is None:
        add_log_entry("No spectrogram image to fix")
        return
        
    # Reset color map to original
    state.spec_img.set_cmap('viridis')
    
    # Reset gain to default values
    state.spec_img.set_clim(0, 5.0)
    
    # Reset x and y limits
    if state.ax_spec:
        state.ax_spec.set_xlim(state.time_zoom_start, state.time_zoom_end)
        state.ax_spec.set_ylim(state.freqs_global[0], state.freqs_global[-1])
    
    # Reset navigation spectrogram too
    if state.ax_nav_spec and hasattr(state, 'nav_spec_img') and state.nav_spec_img:
        state.nav_spec_img.set_cmap('viridis')
        state.nav_spec_img.set_clim(0, 5.0)
        state.ax_nav_spec.set_xlim(0, len(state.data_global) - 1)
        state.ax_nav_spec.set_ylim(state.freqs_global[0], state.freqs_global[-1])
    
    # Reset FFT display
    state.fft_ymin = 0
    state.fft_ymax = 120
    if state.ax_fft:
        state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
        state.ax_fft.set_xlim(state.freqs_global[0], state.freqs_global[-1])
    
    # Force a redraw
    plt.draw()
    
    add_log_entry("Reset spectrogram display settings")

def update_audio_timeline_visualization():
    """Update the audio timeline visualization"""
    if state.ax_audio_timeline is None:
        return
    
    # Clear existing elements
    state.ax_audio_timeline.clear()
    
    # Set up basic layout
    state.ax_audio_timeline.set_facecolor('black')
    state.ax_audio_timeline.set_title('Audio Coverage', fontsize=9, pad=4)
    state.ax_audio_timeline.set_xlim(0, len(state.data_global) - 1)
    state.ax_audio_timeline.set_ylim(0, 1)
    state.ax_audio_timeline.set_yticks([])
    
    # Get total duration of FFT data
    fft_duration = len(state.data_global) - 1
    
    # Draw segments
    for i, (start_time, end_time) in enumerate(state.audio_segments):
        # Convert time to FFT indices (assuming 1 second per FFT sample)
        start_idx = int(start_time)
        end_idx = int(end_time)
        
        # Clamp to valid range
        start_idx = max(0, min(start_idx, fft_duration))
        end_idx = max(0, min(end_idx, fft_duration))
        
        if start_idx < end_idx:
            # Draw rectangle for this audio segment
            rect = plt.Rectangle((start_idx, 0.1), end_idx - start_idx, 0.8,
                               facecolor='#4CAF50', edgecolor='#2E7D32',
                               alpha=0.7)
            state.ax_audio_timeline.add_patch(rect)
            
            # Add file number label
            center_idx = (start_idx + end_idx) / 2
            state.ax_audio_timeline.text(center_idx, 0.5, f'Audio {i+1}',
                                 ha='center', va='center', fontsize=8,
                                 color='white', weight='bold')
    
    # Add grid lines to match spectrogram
    state.ax_audio_timeline.grid(True, axis='x', alpha=0.3, linestyle=':')
    
    plt.draw()

def auto_adjust_fft_range():
    """
    Automatically adjust the FFT Y-axis range based on current data.
    
    This function analyzes the current FFT data - either a single point or a selected range,
    and determines the optimal Y-axis range for visualization. It sets the minimum to 0
    (or slightly below the minimum if negative) and the maximum to about 20% above the data 
    maximum to ensure good visibility.
    """
    try:
        # Check if we have a valid FFT display and data
        if state.ax_fft is None or state.data_global is None or state.freqs_global is None:
            add_log_entry("Cannot adjust FFT range: missing display or data")
            return
        
        # Determine if we're looking at a single point or a range
        if state.selected_range is not None:
            # We have a selected range
            start, end = state.selected_range
            # Get data for all points in the range
            data_points = []
            for i in range(start, end + 1):
                if 0 <= i < len(state.data_global):
                    data_points.append(state.data_global[i])
            
            if not data_points:
                add_log_entry("No valid data points in selected range")
                return
                
            # Convert to numpy array for easier analysis
            data = np.vstack(data_points)
            # Get min and max across all FFTs in the range
            data_min = np.min(data)
            data_max = np.max(data)
            
            add_log_entry(f"Analyzing FFT range {start}-{end}: min={data_min:.1f}, max={data_max:.1f}")
            
        elif hasattr(state, 'spec_click_line') and state.spec_click_line is not None:
            # We have a single selected point
            idx = int(state.spec_click_line.get_xdata()[0])
            if 0 <= idx < len(state.data_global):
                data = state.data_global[idx]
                data_min = np.min(data)
                data_max = np.max(data)
                
                add_log_entry(f"Analyzing FFT at point {idx}: min={data_min:.1f}, max={data_max:.1f}")
            else:
                add_log_entry("Selected point is out of data range")
                return
        else:
            # No selection - use default values
            add_log_entry("No selection, using default FFT range (0-120)")
            state.fft_ymin = 0
            state.fft_ymax = 120
            state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
            plt.draw()
            return
        
        # Set minimum Y value - use 0 or slightly below data minimum if negative
        new_ymin = min(0, data_min - 1) if data_min < 0 else 0
        
        # Set maximum Y value - add 20% headroom above the maximum
        new_ymax = data_max * 1.2
        
        # Ensure a minimum range of at least 10 units for visibility
        if new_ymax - new_ymin < 10:
            new_ymax = new_ymin + 10
        
        # Apply the new range
        state.fft_ymin = new_ymin
        state.fft_ymax = new_ymax
        state.ax_fft.set_ylim(state.fft_ymin, state.fft_ymax)
        
        add_log_entry(f"Auto-adjusted FFT Y-axis range: {state.fft_ymin:.1f} to {state.fft_ymax:.1f}")
        
        # Force redraw
        plt.draw()
        
    except Exception as e:
        add_log_entry(f"Error in auto_adjust_fft_range: {str(e)}")
        logging.error(f"Error in auto_adjust_fft_range: {str(e)}", exc_info=True)

def update_audio_visualizer(audio_chunk, sample_rate, current_time, total_time):
    """Update the audio waveform visualizer"""
    if state.ax_audio_visualizer is None:
        return
    
    try:
        # Check if we actually have valid audio data
        if audio_chunk is None or len(audio_chunk) == 0:
            logging.warning("Empty audio chunk passed to visualizer")
            return
            
        # Log the audio chunk for debugging
        audio_min = np.min(audio_chunk)
        audio_max = np.max(audio_chunk)
        audio_rms = np.sqrt(np.mean(audio_chunk**2))
        logging.info(f"Audio chunk stats: min={audio_min:.3f}, max={audio_max:.3f}, rms={audio_rms:.3f}")
        
        # Clear the existing lines
        state.ax_audio_visualizer.clear()
        
        # Restore the basic setup
        state.ax_audio_visualizer.set_facecolor('black')
        state.ax_audio_visualizer.set_title('Audio Waveform', fontsize=9, pad=4)
        state.ax_audio_visualizer.grid(True, alpha=0.3)
        
        # Fixed y-axis range for stability
        state.ax_audio_visualizer.set_ylim(-1, 1)
        
        # Create time axis for the chunk - ensure correct number of points
        chunk_duration = len(audio_chunk) / sample_rate
        time_axis = np.linspace(0, chunk_duration, len(audio_chunk))
        state.ax_audio_visualizer.set_xlim(0, chunk_duration)
        
        # Plot waveform with enhanced visibility
        state.ax_audio_visualizer.plot(time_axis, audio_chunk, color='lime', linewidth=1.5)
        
        # Add zero line for reference
        state.ax_audio_visualizer.axhline(0, color='gray', linewidth=0.5, alpha=0.5)
        
        # Add playback position indicator
        progress = current_time / total_time if total_time > 0 else 0
        pos = progress * chunk_duration
        state.ax_audio_visualizer.axvline(pos, color='red', linewidth=2, alpha=0.8)
        
        # Simplify the X-axis display to avoid text errors
        state.ax_audio_visualizer.set_xticks([])
        
        # Simplify the Y-axis display to avoid text errors
        state.ax_audio_visualizer.set_yticks([-1, 0, 1])
        state.ax_audio_visualizer.set_yticklabels(["-1", "0", "1"], fontsize=7)
        
    except Exception as e:
        logging.error(f"Error updating audio visualizer: {e}", exc_info=True)

def update_vu_meter(audio_chunk):
    """Update the VU meter display"""
    if state.ax_vu_meter is None:
        return
    
    try:
        # Check for valid audio data
        if audio_chunk is None or len(audio_chunk) == 0:
            logging.warning("Empty audio chunk passed to VU meter")
            return
            
        # Calculate RMS and peak levels
        rms = np.sqrt(np.mean(audio_chunk**2))
        peak = np.max(np.abs(audio_chunk))
        
        # Log values for debugging
        logging.info(f"VU meter values: RMS={rms:.5f}, Peak={peak:.5f}")
        
        # If the audio is very low level, we still want to show something on the meter
        # Apply a minimum floor for visualization purposes
        if rms < 0.001:
            logging.info("Very low audio level detected, applying minimum floor for visualization")
            rms = max(rms, 0.001)
        if peak < 0.001:
            peak = max(peak, 0.001)
        
        # Convert to dB (with protection against log(0))
        rms_db = 20 * np.log10(rms + 1e-10)
        peak_db = 20 * np.log10(peak + 1e-10)
        
        # Clamp to visible range
        rms_db = max(-60, min(0, rms_db))
        peak_db = max(-60, min(0, peak_db))
        
        # Clear the meter
        state.ax_vu_meter.clear()
        
        # Restore basic setup
        state.ax_vu_meter.set_facecolor('black')
        state.ax_vu_meter.set_title(f'VU Meter - Volume: {int(state.audio_volume * 100)}%', fontsize=9, pad=4)
        state.ax_vu_meter.set_xlim(-60, 0)
        state.ax_vu_meter.set_ylim(0, 1)
        state.ax_vu_meter.set_yticks([])
        state.ax_vu_meter.tick_params(axis='x', which='both', labelsize=6)
        
        # Simplify axis properties to avoid errors
        for spine in state.ax_vu_meter.spines.values():
            spine.set_visible(False)
        
        # Draw background gradient - color bands for different volume levels
        for i in range(60):
            db_val = -60 + i
            if db_val < -20:
                color = 'green'
            elif db_val < -10:
                color = 'yellow'
            else:
                color = 'red'
            
            state.ax_vu_meter.bar(db_val, 0.8, width=1, bottom=0.1, 
                           color=color, alpha=0.3, edgecolor='none')
        
        # Draw RMS level with enhanced visibility
        if rms_db > -60:
            state.ax_vu_meter.bar(-60, 0.8, width=rms_db + 60, bottom=0.1,
                           color='lime', alpha=0.8, edgecolor='none')
        
        # Draw peak indicator with enhanced visibility
        if peak_db > -60:
            state.ax_vu_meter.axvline(peak_db, color='red', linewidth=3, alpha=0.9)
            
        # Simplified text display to avoid errors
        # Use basic x-axis labels instead of custom text to improve stability
        state.ax_vu_meter.set_xticks([-60, -40, -20, -10, -3, 0])
        state.ax_vu_meter.set_xticklabels(['-60', '-40', '-20', '-10', '-3', '0'], fontsize=7)
        
    except Exception as e:
        logging.error(f"Error updating VU meter: {e}", exc_info=True)