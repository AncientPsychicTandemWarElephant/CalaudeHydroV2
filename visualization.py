"""
visualization.py - Functions for visualizing hydrophone data
"""

import matplotlib.pyplot as plt
import numpy as np
import logging
from matplotlib.transforms import blended_transform_factory
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
import time
import os

# Import state directly
import state

from utils import add_log_entry, update_spectrogram_xaxis

# Setup detailed logging specifically for navigation/zoom functions
zoom_log_dir = 'logs'
if not os.path.exists(zoom_log_dir):
    os.makedirs(zoom_log_dir)
    
zoom_log_path = os.path.join(zoom_log_dir, f'zoom_detailed_{time.strftime("%Y%m%d_%H%M%S")}.log')
zoom_logger = logging.getLogger('zoom_logger')
zoom_logger.setLevel(logging.DEBUG)

# File handler for zoom-specific logging
zoom_file_handler = logging.FileHandler(zoom_log_path)
zoom_file_handler.setLevel(logging.DEBUG)
zoom_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
zoom_logger.addHandler(zoom_file_handler)

def log_zoom_event(message):
    """Log a zoom-related event with a timestamp"""
    # Use datetime for microsecond formatting instead of time.strftime
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    zoom_logger.debug(f"{message}")
    # Also add to the general log at info level
    add_log_entry(f"[ZOOM] {message}")

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
    
    # Convert frequency to kHz for display
    freqs_khz = [f/1000 for f in freqs]
    state.ax_fft.set_xlim(freqs_khz[0], freqs_khz[-1])
    
    # Don't set title repeatedly
    
    # Plot new data with frequencies in kHz
    state.ax_fft.plot(freqs_khz, data[idx], color='lime')
    
    # Re-draw frequency markers if they exist
    for i, (_, _, _, freq, hline) in enumerate(state.freq_markers):
        if freq is not None:
            color = 'red' if i == 0 else 'blue'
            # Convert to kHz
            freq_khz = freq/1000
            # Display marker in kHz
            line = state.ax_fft.axvline(freq_khz, color=color)
            # Add label with kHz format inside the plot
            label = state.ax_fft.text(freq_khz, state.fft_ymax * 0.95, f"{freq_khz:.2f} kHz", 
                               va='top', ha='left', color=color, fontsize=8,
                               bbox=dict(facecolor='black', alpha=0.7, pad=2))
            state.freq_markers[i] = (line, label, i, freq, hline)

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
    
    # Convert frequency to kHz for display
    freqs_khz = [f/1000 for f in freqs]
    state.ax_fft.set_xlim(freqs_khz[0], freqs_khz[-1])
    
    # Update the title only if it's different
    # Convert indices to time labels for display
    start_time = state.time_labels_all[start] if 0 <= start < len(state.time_labels_all) else str(start)
    end_time = state.time_labels_all[end] if 0 <= end < len(state.time_labels_all) else str(end)
    
    # Show HH:MM format if available
    if start_time != "GAP" and len(start_time) >= 5:
        start_time = start_time[:5]  # HH:MM
    if end_time != "GAP" and len(end_time) >= 5:
        end_time = end_time[:5]  # HH:MM
    
    new_title = f'Stacked FFTs from {start_time} to {end_time}'
    if not hasattr(state.ax_fft, '_current_title') or state.ax_fft._current_title != new_title:
        state.ax_fft.set_title(new_title, fontsize=12, color='#ffffff')
        state.ax_fft._current_title = new_title
    
    # Plot the stacked FFT data with frequencies in kHz
    for i in range(start, end+1):
        state.ax_fft.plot(freqs_khz, data[i], color='lime', alpha=0.2)
    
    # Re-draw frequency markers if they exist
    for i, (_, _, _, freq, hline) in enumerate(state.freq_markers):
        if freq is not None:
            color = 'red' if i == 0 else 'blue'
            # Convert to kHz
            freq_khz = freq/1000
            # Display marker in kHz
            line = state.ax_fft.axvline(freq_khz, color=color)
            # Add label with kHz format inside the plot
            label = state.ax_fft.text(freq_khz, state.fft_ymax * 0.95, f"{freq_khz:.2f} kHz", 
                               va='top', ha='left', color=color, fontsize=8,
                               bbox=dict(facecolor='black', alpha=0.7, pad=2))
            state.freq_markers[i] = (line, label, i, freq, hline)

def update_marker(n, xpos):
    """Update frequency marker at position xpos"""
    # Important: xpos is now in kHz in the displayed plot, but we need to convert back to Hz for storage
    # Convert kHz to Hz for internal storage
    freq = xpos * 1000  # Convert user-clicked kHz back to Hz for storage
    
    # Remove old marker from FFT display
    if state.freq_markers[n][0]:
        try:
            state.freq_markers[n][0].remove()
        except Exception:
            pass
    if state.freq_markers[n][1]:
        try:
            state.freq_markers[n][1].remove()
        except Exception:
            pass
    
    # Remove old marker from spectrogram
    for artist in state.ax_spec.lines[:]:
        if hasattr(artist, 'is_marker') and artist.is_marker == n:
            try:
                artist.remove()
            except Exception:
                pass
    for artist in state.ax_spec.texts[:]:
        if hasattr(artist, 'is_marker') and artist.is_marker == n:
            try:
                artist.remove()
            except Exception:
                pass
    
    color = 'red' if n == 0 else 'blue'
    
    # Display frequency in kHz since that's what's shown on the axis
    freq_khz = xpos  # Already in kHz from user click
    
    # Create marker in FFT display
    line = state.ax_fft.axvline(freq_khz, color=color)
    
    # Add label with kHz format inside the plot
    label = state.ax_fft.text(freq_khz, state.fft_ymax * 0.95, f"{freq_khz:.2f} kHz", 
                       va='top', ha='left', color=color, fontsize=8,
                       bbox=dict(facecolor='black', alpha=0.7, pad=2))
    
    # Add horizontal line on spectrogram at the frequency
    hline = state.ax_spec.axhline(freq_khz, color=color, linestyle='--', linewidth=1)
    
    # Add frequency label on spectrogram inside the plot
    label_spec = state.ax_spec.text(state.ax_spec.get_xlim()[0] + 10, freq_khz, f"{freq_khz:.2f} kHz", 
                             va='center', ha='left', fontsize=8, color=color,
                             bbox=dict(facecolor='black', alpha=0.7, pad=2))
    
    # Mark these objects to be able to find them later
    label_spec.is_marker = n
    hline.is_marker = n
    
    # Store the marker info - keeping the original Hz value as well
    state.freq_markers[n] = (line, label, n, freq, hline)
    
    # Log the marker creation
    add_log_entry(f"Frequency marker {n+1} set at {freq_khz:.2f} kHz")
    
    # Force a redraw
    plt.draw()

def update_gain(val):
    """Update the gain slider values for the spectrogram"""
    try:
        lo, hi = val
        
        # Add some debugging information
        add_log_entry(f"Updating gain values: {lo:.2f} to {hi:.2f}")
        
        # Ensure the values are valid and have enough separation
        # Clamp the values to reasonable limits to prevent display issues
        min_limit = 0   # Absolute minimum for lower bound
        max_limit = 10  # Absolute maximum for upper bound
        min_separation = 0.1  # Minimum separation between lo and hi
        
        # Ensure values are within absolute limits
        lo = max(min_limit, min(lo, max_limit - min_separation))
        hi = max(min_limit + min_separation, min(hi, max_limit))
        
        # Ensure minimum separation between lo and hi
        if hi - lo < min_separation:
            # If they're too close, adjust based on which one was likely changed
            # If lo increased, push hi up
            if hasattr(state.spec_img, 'norm') and lo > state.spec_img.norm.vmin:
                hi = lo + min_separation
            # If hi decreased, push lo down
            else:
                lo = hi - min_separation
        
        # Check if the gain has changed enough to actually update
        should_update = True
        if state.spec_img and hasattr(state.spec_img, 'norm'):
            current_lo, current_hi = state.spec_img.get_clim()
            if abs(current_lo - lo) < 0.001 and abs(current_hi - hi) < 0.001:
                # Skip the update if the values haven't changed enough
                should_update = False
        
        if should_update:
            # Set new values with safety checks
            add_log_entry(f"Setting gain to {lo:.2f} - {hi:.2f}")
            state.spec_img.set_clim(lo, hi)
            
            # Store the current values
            current_clim = state.spec_img.get_clim()
            add_log_entry(f"Current gain is now: {current_clim[0]:.2f} - {current_clim[1]:.2f}")
            
            # Force update of the slider to match the actual values
            if state.gain_slider and hasattr(state.gain_slider, 'set_val'):
                # Only update if values changed significantly to avoid feedback loops
                if abs(state.gain_slider.val[0] - lo) > 0.001 or abs(state.gain_slider.val[1] - hi) > 0.001:
                    state.gain_slider.set_val((lo, hi))
            
            # Force a redraw to update the visualization
            if state.fig:
                state.fig.canvas.draw_idle()
        
    except Exception as e:
        add_log_entry(f"Error updating gain: {str(e)}")
        logging.error(f"Error updating gain: {str(e)}", exc_info=True)

def normalize_spectrogram_data():
    """Analyze and normalize spectrogram data for better visualization"""
    try:
        if state.data_global is None:
            add_log_entry("No data to normalize")
            return None, None
            
        # Get data and analyze
        data = state.data_global
        non_nan_mask = ~np.isnan(data)
        
        if np.sum(non_nan_mask) == 0:
            add_log_entry("Warning: Data contains only NaN values")
            return 0, 1  # Default values
            
        # Get non-NaN values
        valid_data = data[non_nan_mask]
        
        # Use percentiles to avoid outliers skewing the range
        vmin = np.percentile(valid_data, 1)  # 1st percentile
        vmax = np.percentile(valid_data, 99)  # 99th percentile
        
        # Ensure reasonable range
        if vmax - vmin < 0.1:
            vmean = (vmax + vmin) / 2
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
    start_time = time.time()
    log_zoom_event(f"ZOOM START: updating zoom to {val[0]:.2f} - {val[1]:.2f}")
    
    # Store the pre-update values for comparison
    prev_start = state.time_zoom_start if hasattr(state, 'time_zoom_start') else None
    prev_end = state.time_zoom_end if hasattr(state, 'time_zoom_end') else None
    log_zoom_event(f"Previous zoom was: {prev_start} - {prev_end}")
    
    # Update state values
    state.time_zoom_start, state.time_zoom_end = val
    
    # Debug logging
    add_log_entry(f"update_time_zoom called: {state.time_zoom_start} - {state.time_zoom_end}")
    
    # Check data validity
    if hasattr(state, 'data_global') and state.data_global is not None:
        # CRITICAL FIX: Use the first dimension (time samples) for navigation bounds
        data_length = len(state.data_global)
        log_zoom_event(f"Data length: {data_length}")
        
        # CRITICAL FIX: Ensure zoom range is within data bounds
        # Use data_length - 1 as the maximum valid index (zero-based indexing)
        if state.time_zoom_end > data_length - 1:
            log_zoom_event(f"WARNING: Zoom end ({state.time_zoom_end}) exceeds data length, clamping to {data_length-1}")
            state.time_zoom_end = data_length - 1
        if state.time_zoom_start < 0:
            log_zoom_event(f"WARNING: Zoom start ({state.time_zoom_start}) is negative, clamping to 0")
            state.time_zoom_start = 0
            
        # CRITICAL FIX: Validate zoom span to ensure it's reasonable
        # Enforce a minimum span to avoid pathological cases
        min_span = 10
        current_span = state.time_zoom_end - state.time_zoom_start
        if current_span < min_span:
            log_zoom_event(f"WARNING: Zoom span ({current_span}) is too small, enforcing minimum span of {min_span}")
            # Prefer to expand the end to maintain the start position
            new_end = min(data_length - 1, state.time_zoom_start + min_span)
            # If that doesn't work, adjust the start
            if new_end - state.time_zoom_start < min_span:
                new_start = max(0, new_end - min_span)
                state.time_zoom_start = new_start
            state.time_zoom_end = new_end
    else:
        log_zoom_event("WARNING: data_global is None or not accessible")
    
    # Ensure values are integers
    state.time_zoom_start = int(state.time_zoom_start)
    state.time_zoom_end = int(state.time_zoom_end)
    
    # Calculate zoom metrics
    zoom_width = state.time_zoom_end - state.time_zoom_start
    log_zoom_event(f"Zoom width: {zoom_width}")
    
    # Update spectrogram x-axis limits
    if state.ax_spec:
        prev_xlim = state.ax_spec.get_xlim()
        log_zoom_event(f"Previous spec xlim: {prev_xlim}")
        
        state.ax_spec.set_xlim(state.time_zoom_start, state.time_zoom_end)
        new_xlim = state.ax_spec.get_xlim()
        log_zoom_event(f"New spec xlim: {new_xlim}")
        
        add_log_entry(f"Updated spec xlim: {state.time_zoom_start} - {state.time_zoom_end}")
    else:
        log_zoom_event("ERROR: ax_spec is None!")
        add_log_entry("ax_spec is None!")
    
    # Update spectrogram x-axis labels
    log_zoom_event("Updating spectrogram x-axis labels...")
    try:
        update_spectrogram_xaxis()
        log_zoom_event("X-axis labels updated successfully")
    except Exception as e:
        log_zoom_event(f"ERROR updating x-axis labels: {str(e)}")
    
    # Update audio timeline x-axis limits
    if state.ax_audio_timeline:
        prev_timeline_xlim = state.ax_audio_timeline.get_xlim()
        log_zoom_event(f"Previous timeline xlim: {prev_timeline_xlim}")
        
        state.ax_audio_timeline.set_xlim(state.time_zoom_start, state.time_zoom_end)
        new_timeline_xlim = state.ax_audio_timeline.get_xlim()
        log_zoom_event(f"New timeline xlim: {new_timeline_xlim}")
        
        # Update the audio timeline visualization to ensure labels are properly drawn
        update_audio_timeline_visualization()
    else:
        log_zoom_event("ax_audio_timeline is None or not accessible")
    
    # Update navigation box and visual elements
    if state.ax_nav_spec:
        width = state.time_zoom_end - state.time_zoom_start
        handle_width = width * 0.05
        
        log_zoom_event(f"Updating nav box with width: {width}")
        
        # Count patches before removal
        patch_count_before = len(state.ax_nav_spec.patches) if hasattr(state.ax_nav_spec, 'patches') else 0
        log_zoom_event(f"Navigation patches before removal: {patch_count_before}")
        
        # Clear and redraw all navigation elements
        # Remove old patches except the spectrogram image
        for patch in state.ax_nav_spec.patches[:]:
            patch.remove()
        
        # Count patches after removal
        patch_count_after = len(state.ax_nav_spec.patches) if hasattr(state.ax_nav_spec, 'patches') else 0
        log_zoom_event(f"Navigation patches after removal: {patch_count_after}")
        
        # Redraw navigation box - thick red border
        log_zoom_event("Creating new navigation box...")
        try:
            # Use frequency in kHz
            state.nav_box = plt.Rectangle((state.time_zoom_start, state.freqs_global[0]/1000), 
                               width, 
                               (state.freqs_global[-1] - state.freqs_global[0])/1000,
                               fill=False, edgecolor='red', linewidth=3, alpha=1.0,
                               zorder=10)
            state.ax_nav_spec.add_patch(state.nav_box)
            log_zoom_event("Navigation box created successfully")
        except Exception as e:
            log_zoom_event(f"ERROR creating navigation box: {str(e)}")
        
        # Redraw white highlight
        log_zoom_event("Creating navigation highlight...")
        try:
            # Use frequency in kHz
            nav_highlight = plt.Rectangle((state.time_zoom_start, state.freqs_global[0]/1000), 
                                     width, 
                                     (state.freqs_global[-1] - state.freqs_global[0])/1000,
                                     fill=True, facecolor='white', alpha=0.2,
                                     zorder=5)
            state.ax_nav_spec.add_patch(nav_highlight)
            log_zoom_event("Navigation highlight created successfully")
        except Exception as e:
            log_zoom_event(f"ERROR creating navigation highlight: {str(e)}")
        
        # Redraw edge handles
        log_zoom_event("Creating edge handles...")
        try:
            # Use frequency in kHz
            left_handle = plt.Rectangle((state.time_zoom_start, state.freqs_global[0]/1000), 
                                   handle_width, 
                                   (state.freqs_global[-1] - state.freqs_global[0])/1000,
                                   fill=True, facecolor='red', alpha=0.3,
                                   zorder=6)
            right_handle = plt.Rectangle((state.time_zoom_end - handle_width, state.freqs_global[0]/1000), 
                                    handle_width, 
                                    (state.freqs_global[-1] - state.freqs_global[0])/1000,
                                    fill=True, facecolor='red', alpha=0.3,
                                    zorder=6)
            state.ax_nav_spec.add_patch(left_handle)
            state.ax_nav_spec.add_patch(right_handle)
            log_zoom_event("Edge handles created successfully")
        except Exception as e:
            log_zoom_event(f"ERROR creating edge handles: {str(e)}")
        
        # Update position indicator text
        text_count_before = len(state.ax_nav_spec.texts) if hasattr(state.ax_nav_spec, 'texts') else 0
        log_zoom_event(f"Text elements before removal: {text_count_before}")
        
        for text in state.ax_nav_spec.texts[:]:
            text.remove()
            
        text_count_after = len(state.ax_nav_spec.texts) if hasattr(state.ax_nav_spec, 'texts') else 0
        log_zoom_event(f"Text elements after removal: {text_count_after}")
        
        log_zoom_event("Creating position indicator text...")
        try:
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
            log_zoom_event("Position indicator text created successfully")
        except Exception as e:
            log_zoom_event(f"ERROR creating position text: {str(e)}")
    else:
        log_zoom_event("ERROR: ax_nav_spec is None!")
        add_log_entry("ax_nav_spec is None!")
    
    # Count patches after all updates
    patch_count_final = len(state.ax_nav_spec.patches) if hasattr(state.ax_nav_spec, 'patches') else 0
    log_zoom_event(f"Final navigation patch count: {patch_count_final}")
    
    # Force redraw
    log_zoom_event("Forcing canvas redraw...")
    if state.fig:
        try:
            state.fig.canvas.draw_idle()
            log_zoom_event("Canvas redraw completed successfully")
        except Exception as e:
            log_zoom_event(f"ERROR during canvas redraw: {str(e)}")
    else:
        log_zoom_event("ERROR: fig is None!")
        add_log_entry("fig is None!")
    
    # Update comment markers if they're visible
    if state.comments_visible:
        update_comment_markers()
    
    # Release any mouse grabs to prevent conflicts with other UI elements
    try:
        if hasattr(state, 'fig') and state.fig is not None:
            state.fig.canvas.release_mouse()
    except:
        pass  # Ignore if no grab exists or method not supported
    
    end_time = time.time()
    duration = (end_time - start_time) * 1000  # Convert to ms
    log_zoom_event(f"ZOOM COMPLETE: Time taken: {duration:.2f}ms")
    add_log_entry(f"update_time_zoom complete")

def fix_spectrogram():
    """Fix the spectrogram display by normalizing the data and setting appropriate color limits"""
    try:
        # First, check if we have the necessary components
        if not hasattr(state, 'data_global') or state.data_global is None:
            add_log_entry("No data available to fix spectrogram")
            return False
        
        # Get the current spectrogram axes
        if not hasattr(state, 'ax_spec') or state.ax_spec is None:
            add_log_entry("Spectrogram axes not available")
            return False
        
        # Analyze the data and get appropriate vmin/vmax
        vmin, vmax = normalize_spectrogram_data()
        
        # Force a direct reset of the color limits
        if state.spec_img is not None:
            add_log_entry(f"Fixing spectrogram with vmin={vmin:.4f}, vmax={vmax:.4f}")
            state.spec_img.set_clim(vmin, vmax)
            
            # Force the slider to update as well
            if hasattr(state, 'gain_slider') and state.gain_slider is not None:
                state.gain_slider.set_val((vmin, vmax))
            
            # Force redraw
            plt.draw()
            return True
        else:
            add_log_entry("No spectrogram image exists to fix")
            return False
            
    except Exception as e:
        add_log_entry(f"Error fixing spectrogram: {str(e)}")
        logging.error(f"Error fixing spectrogram: {str(e)}", exc_info=True)
        return False

def create_comment_timeline_axis():
    """Create the comment timeline visualization axis"""
    # Get the position of the spectrogram
    spec_pos = state.ax_spec.get_position()
    
    # Create timeline axis directly below the spectrogram
    timeline_height = 0.055  # Same height as audio waveform for consistency
    # Position directly below spectrogram
    timeline_bottom = spec_pos.y0 - timeline_height
    
    state.ax_comment_timeline = state.fig.add_axes([spec_pos.x0, timeline_bottom, 
                                        spec_pos.width, timeline_height], zorder=10)
    state.ax_comment_timeline.set_xlim(state.ax_spec.get_xlim())
    state.ax_comment_timeline.set_ylim(0, 1)  # Back to 0-1 since we have more height now
    state.ax_comment_timeline.set_yticks([])
    state.ax_comment_timeline.set_xticks([])  # Remove x-axis ticks and labels
    state.ax_comment_timeline.set_xlabel('')
    # Remove title from axis, will add as text element instead
    
    # Style the axis
    state.ax_comment_timeline.spines['top'].set_visible(False)  # Remove top spine to avoid double line
    state.ax_comment_timeline.spines['top'].set_linewidth(0.5)
    state.ax_comment_timeline.spines['top'].set_color('#999999')
    state.ax_comment_timeline.spines['right'].set_visible(False)
    state.ax_comment_timeline.spines['left'].set_visible(False)
    state.ax_comment_timeline.spines['bottom'].set_visible(False)  # Hide bottom spine to merge with next section
    state.ax_comment_timeline.spines['bottom'].set_linewidth(0.5)
    state.ax_comment_timeline.spines['bottom'].set_color('#999999')
    state.ax_comment_timeline.patch.set_facecolor('#e0e0e0')  # Darker gray for better contrast
    state.ax_comment_timeline.patch.set_alpha(1.0)  # Full opacity
    state.ax_comment_timeline.set_clip_on(False)  # Don't clip outside bounds
    
    # Add label to the left of the timeline - slightly higher than center
    state.fig.text(spec_pos.x0 - 0.01, timeline_bottom + timeline_height * 0.75, 
                   'Comments', fontsize=11, weight='bold', 
                   ha='right', va='center')
    
    return state.ax_comment_timeline

def update_comment_markers():
    """Update comment timeline visualization"""
    if state.ax_comment_timeline is None:
        return
    
    # Clear previous timeline
    state.ax_comment_timeline.clear()
    state.ax_comment_timeline.set_xlim(state.ax_spec.get_xlim())
    state.ax_comment_timeline.set_ylim(0, 1)  # Back to 0-1 since we have more height now
    state.ax_comment_timeline.set_yticks([])
    state.ax_comment_timeline.set_xticks([])  # Remove x-axis ticks and labels
    # No title here - it's drawn as a text element in create function
    
    # Restore the grey background after clearing
    state.ax_comment_timeline.patch.set_facecolor('#e0e0e0')
    state.ax_comment_timeline.patch.set_alpha(1.0)
    
    # Clear previous spectrogram comment markers
    if hasattr(state, 'spectrogram_comment_markers'):
        for marker in state.spectrogram_comment_markers:
            try:
                marker.remove()
            except:
                pass
    state.spectrogram_comment_markers = []
    
    # Clear previous navigation comment highlight
    if hasattr(state, 'nav_comment_highlight'):
        try:
            state.nav_comment_highlight.remove()
        except:
            pass
        state.nav_comment_highlight = None
    
    # Hide axis if comments not visible
    if not hasattr(state, 'comments_visible') or not state.comments_visible:
        add_log_entry(f"Comments not visible, hiding timeline (comments_visible={getattr(state, 'comments_visible', False)})")
        state.ax_comment_timeline.set_visible(False)
        state.fig.canvas.draw_idle()
        return
    else:
        add_log_entry(f"Showing comments timeline with {len(state.comments)} comments")
        state.ax_comment_timeline.set_visible(True)
        
        # Make sure button text matches state
        if hasattr(state, 'btn_toggle_comments'):
            if state.btn_toggle_comments.label.get_text() != 'Hide Comments':
                add_log_entry(f"Fixing button text mismatch: was '{state.btn_toggle_comments.label.get_text()}', setting to 'Hide Comments'")
                state.btn_toggle_comments.label.set_text('Hide Comments')
    
    # Draw comment blocks - first sort by start position to handle overlaps
    sorted_comments = sorted(state.comments, key=lambda c: c['start_idx'])
    
    # Track vertical positions for overlapping comments
    comment_levels = []  # List of (start, end, level) tuples
    
    for comment in sorted_comments:
        # Check if comment is in timeline range  
        if comment['end_idx'] < 0 or comment['start_idx'] >= len(state.data_global):
            continue
            
        # Get current xlim to check if comment is at least partially visible
        xlim = state.ax_comment_timeline.get_xlim()
        if comment['end_idx'] < xlim[0] or comment['start_idx'] > xlim[1]:
            continue  # Skip comments completely outside the view
            
        # Find appropriate level for this comment to avoid overlaps
        level = 0
        for existing_start, existing_end, existing_level in comment_levels:
            if comment['start_idx'] <= existing_end and comment['end_idx'] >= existing_start:
                level = max(level, existing_level + 1)
        
        comment_levels.append((comment['start_idx'], comment['end_idx'], level))
        
        # Calculate vertical position based on level - make blocks fill the entire timeline
        if level == 0:
            y_bottom = 0.0  # Start at the very bottom
            y_height = 1.0  # Fill entire height (timeline has ylim 0-1)
        else:
            # For overlapping comments, stack them
            y_bottom = 0.0 + (level * 0.5)
            y_height = 0.5
            
        # Determine colors based on selection
        is_selected = comment['id'] == state.selected_comment_id
        if is_selected:
            color = '#FFD700'  # Gold for selected
            alpha = 0.95
            edgecolor = '#FFA500'  # Orange edge
            edgewidth = 2.5
            text_color = 'black'  # Black text on yellow background
        else:
            color = '#4682B4'  # Brighter steel blue
            alpha = 0.85
            edgecolor = '#1E3A8A'  # Dark blue edge
            edgewidth = 1.5
            text_color = 'white'  # White text on blue background
        
        # Create rectangle for comment with calculated position
        rect = plt.Rectangle((comment['start_idx'], y_bottom), 
                           comment['end_idx'] - comment['start_idx'], 
                           y_height,
                           facecolor=color,
                           edgecolor=edgecolor,
                           linewidth=edgewidth,
                           alpha=alpha,
                           picker=True)  # Make it clickable
        # Store the comment ID with the rectangle for accurate click detection
        rect.comment_id = comment['id']
        state.ax_comment_timeline.add_patch(rect)
        
        # Add text label - position it to stay visible when zoomed
        # Calculate the visible portion of the comment
        visible_start = max(comment['start_idx'], xlim[0])
        visible_end = min(comment['end_idx'], xlim[1])
        
        # Position text in the center of the visible portion
        text_x = (visible_start + visible_end) / 2
        
        # Add some padding from the edges for better visibility
        padding = (xlim[1] - xlim[0]) * 0.02
        text_x = max(visible_start + padding, min(visible_end - padding, text_x))
        
        text = comment['text'][:25] + '...' if len(comment['text']) > 25 else comment['text']
        text_y = y_bottom + y_height / 2  # Center text vertically in its rectangle
        state.ax_comment_timeline.text(text_x, text_y, text,
                                     ha='center', va='center',
                                     fontsize=11, color='black',  # Always use black text for better readability
                                     weight='bold',
                                     clip_on=True)
        
        # If this comment is selected, add markers to spectrogram and navigation
        if is_selected and state.ax_spec is not None:
            # Add vertical dashed lines on main spectrogram
            xlim = state.ax_spec.get_xlim()
            if comment['start_idx'] >= xlim[0] and comment['start_idx'] <= xlim[1]:
                line_start = state.ax_spec.axvline(
                    x=comment['start_idx'],
                    color='red',
                    linestyle='--',
                    alpha=0.8,
                    linewidth=2
                )
                state.spectrogram_comment_markers.append(line_start)
            
            if comment['end_idx'] >= xlim[0] and comment['end_idx'] <= xlim[1]:
                line_end = state.ax_spec.axvline(
                    x=comment['end_idx'],
                    color='red',
                    linestyle='--',
                    alpha=0.8,
                    linewidth=2
                )
                state.spectrogram_comment_markers.append(line_end)
            
            # Add yellow highlight on navigation spectrogram
            if state.ax_nav_spec is not None:
                nav_highlight = state.ax_nav_spec.axvspan(
                    comment['start_idx'],
                    comment['end_idx'],
                    facecolor='yellow',
                    alpha=0.5,
                    zorder=10
                )
                state.nav_comment_highlight = nav_highlight
    
    # Update x-axis to match spectrogram
    state.ax_comment_timeline.set_xlim(state.ax_spec.get_xlim())
    
    # Add hover and click handlers
    def on_comment_click(event):
        if event.artist in state.ax_comment_timeline.patches and hasattr(event.artist, 'comment_id'):
            clicked_comment_id = event.artist.comment_id
            
            # Toggle selection - unselect if already selected
            if state.selected_comment_id == clicked_comment_id:
                state.selected_comment_id = None
                # Clear the comment text display
                if state.ax_comment_text is not None:
                    state.ax_comment_text.clear()
                    state.ax_comment_text.axis("off")
            else:
                state.selected_comment_id = clicked_comment_id
                display_selected_comment()
            
            # Update delete button state
            try:
                from ui_state_updates import update_delete_button_state
                update_delete_button_state(state)
            except ImportError:
                # If update_delete_button_state is not available, update the button text directly
                if hasattr(state, 'update_add_comment_button_text'):
                    state.update_add_comment_button_text()
                pass  # Module not available
            
            update_comment_markers()
    
    state.fig.canvas.mpl_connect('pick_event', on_comment_click)
    state.fig.canvas.draw_idle()

def display_selected_comment():
    """Function now just handles refreshing the comment list display"""
    # Since we're now showing notes directly in the comment list,
    # this function just refreshes the comment list display
    if hasattr(state, 'ax_comment_list') and state.ax_comment_list is not None:
        # Import and call the update function for the comment list
        try:
            import sys
            if 'comment_list' in sys.modules:
                from comment_list import update_comment_list_display
                update_comment_list_display()
        except ImportError:
            pass
        
        # Force a redraw
        if hasattr(state, 'fig'):
            state.fig.canvas.draw_idle()

def create_audio_timeline_axis():
    """Create the audio timeline visualization axis"""
    # Get the position of the spectrogram
    spec_pos = state.ax_spec.get_position()
    
    # Get the position of the comment timeline if it exists
    if hasattr(state, 'ax_comment_timeline') and state.ax_comment_timeline is not None:
        comment_pos = state.ax_comment_timeline.get_position()
        # Small overlap to close gap
        timeline_bottom = comment_pos.y0 - 0.04  # Increased separation
    else:
        # Fallback to below spectrogram directly
        timeline_bottom = spec_pos.y0 - 0.10
    
    # Create timeline axis below the comment timeline - increased height
    timeline_height = 0.04
    
    state.ax_audio_timeline = state.fig.add_axes([spec_pos.x0, timeline_bottom, 
                                      spec_pos.width, timeline_height], zorder=10, sharex=None)
    state.ax_audio_timeline.set_xlim(state.ax_spec.get_xlim())
    state.ax_audio_timeline.set_ylim(0, 1)
    state.ax_audio_timeline.set_yticks([])
    # Keep x-axis for time labels
    # Remove title from axis, will add as text element instead
    
    # Style the axis
    state.ax_audio_timeline.spines['top'].set_visible(False)
    state.ax_audio_timeline.spines['right'].set_visible(False)
    state.ax_audio_timeline.spines['left'].set_visible(False)
    state.ax_audio_timeline.spines['bottom'].set_visible(False)
    state.ax_audio_timeline.patch.set_facecolor('#d0d0d0')  # Darker gray for better contrast
    
    # Ensure x-axis labels are visible - increased padding and font size for better readability
    state.ax_audio_timeline.tick_params(axis='x', which='both', labelbottom=True, labelsize=9, pad=5)
    
    # Enable clipping to prevent content from appearing outside timeline bounds
    state.ax_audio_timeline.set_clip_on(True)
    # Set clipping box to axis bounds
    state.ax_audio_timeline.set_clip_box(state.ax_audio_timeline.bbox)
    
    # Add label to the left of the timeline
    state.fig.text(spec_pos.x0 - 0.01, timeline_bottom + timeline_height/2, 
                   'Audio', fontsize=11, weight='bold', 
                   ha='right', va='center')
    
    # Don't set formatter here - let update_spectrogram_xaxis handle it
    from utils import update_spectrogram_xaxis
    update_spectrogram_xaxis()
    
    return state.ax_audio_timeline

def update_audio_timeline_visualization():
    """Update the audio timeline visualization"""
    if state.ax_audio_timeline is None:
        return
    
    # Remove previous content without clearing axis formatting
    for patch in state.ax_audio_timeline.patches[:]:
        patch.remove()
    for text in state.ax_audio_timeline.texts[:]:
        text.remove()
    for line in state.ax_audio_timeline.lines[:]:
        line.remove()
    
    state.ax_audio_timeline.set_xlim(state.ax_spec.get_xlim())
    
    if not state.audio_segments:
        state.ax_audio_timeline.text(0.5, 0.5, 'No audio loaded', 
                              transform=state.ax_audio_timeline.transAxes,
                              ha='center', va='center', color='gray')
        plt.draw()
        return
    
    # Calculate total FFT duration
    fft_duration = len(state.time_labels_all) if state.time_labels_all else 0
    
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
            rect.set_clip_on(True)
            rect.set_clip_path(state.ax_audio_timeline.patch)
            state.ax_audio_timeline.add_patch(rect)
            
            # Add file number label
            center_idx = (start_idx + end_idx) / 2
            
            # Always create text object for all segments
            text_obj = state.ax_audio_timeline.text(center_idx, 0.5, f'Audio {i+1}',
                                 ha='center', va='center', fontsize=8,
                                 color='white', weight='bold')
            
            # Apply clipping to handle visibility automatically
            text_obj.set_clip_on(True)
            text_obj.set_clip_path(state.ax_audio_timeline.patch)
    
    # Add grid lines to match spectrogram
    state.ax_audio_timeline.grid(True, axis='x', alpha=0.3, linestyle=':')
    
    # Ensure timeline stays within bounds
    state.ax_audio_timeline.set_xlim(state.ax_spec.get_xlim())
    
    # Update the x-axis formatting to ensure time labels show
    from utils import update_spectrogram_xaxis, format_time_axis
    from matplotlib.ticker import FuncFormatter
    update_spectrogram_xaxis()
    
    # Force formatter application one more time
    formatter = FuncFormatter(format_time_axis)
    state.ax_audio_timeline.xaxis.set_major_formatter(formatter)
    
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
        
        # Update the FFT gain slider to match the auto-adjusted values
        if hasattr(state, 'fft_gain_slider') and state.fft_gain_slider:
            state.fft_gain_slider.set_val((new_ymin, new_ymax))
        
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
        
        # Add title
        state.ax_vu_meter.set_title('Audio Level', fontsize=9, pad=4)
        
        # Set up VU meter axes
        state.ax_vu_meter.set_xlim(-62, 2)
        state.ax_vu_meter.set_ylim(0, 1)
        
        # Hide Y axis
        state.ax_vu_meter.set_yticks([])
        
        # Set X axis ticks for dB scale
        state.ax_vu_meter.set_xticks([-60, -50, -40, -30, -20, -10, 0])
        state.ax_vu_meter.set_xticklabels(['-60', '', '-40', '', '-20', '', '0'], fontsize=7)
        
        # Add dB scale
        state.ax_vu_meter.plot([-60, 0], [0.5, 0.5], 'k', linewidth=1, alpha=0.3)
        
        # Draw RMS level (green)
        rms_width = rms_db + 60
        rms_rect = plt.Rectangle((-60, 0.3), rms_width, 0.2, facecolor='#4CAF50', edgecolor=None)
        state.ax_vu_meter.add_patch(rms_rect)
        
        # Draw peak level (red)
        peak_width = peak_db + 60
        peak_rect = plt.Rectangle((-60, 0.6), peak_width, 0.2, facecolor='#F44336', edgecolor=None)
        state.ax_vu_meter.add_patch(peak_rect)
        
        # Redline for levels close to 0dB
        if peak_db > -3:
            redline = plt.Rectangle((-3, 0), 3, 1, facecolor='#B71C1C', alpha=0.3)
            state.ax_vu_meter.add_patch(redline)
        
        # Add labels
        state.ax_vu_meter.text(-58, 0.4, 'RMS', fontsize=7, va='center')
        state.ax_vu_meter.text(-58, 0.7, 'Peak', fontsize=7, va='center')
        
        # Add numeric values
        state.ax_vu_meter.text(1, 0.4, f'{rms_db:.1f} dB', fontsize=7, ha='right', va='center')
        state.ax_vu_meter.text(1, 0.7, f'{peak_db:.1f} dB', fontsize=7, ha='right', va='center')
        
    except Exception as e:
        logging.error(f"Error updating VU meter: {e}", exc_info=True)