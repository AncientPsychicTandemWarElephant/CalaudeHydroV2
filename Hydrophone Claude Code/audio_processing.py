"""
audio_processing.py - Functions for audio playback and processing
"""

import sounddevice as sd
import numpy as np
import logging
import time
import threading
import matplotlib.pyplot as plt

# Import state directly
import state

from utils import add_log_entry, update_time_display
from visualization import update_fft, update_fft_range, update_audio_visualizer, update_vu_meter

def update_volume(val):
    """Update the audio volume level"""
    state.audio_volume = val
    # Update volume display
    if state.ax_vu_meter:
        state.ax_vu_meter.set_title(f'Volume: {int(state.audio_volume * 100)}%', fontsize=9, pad=4)
        plt.draw()

def update_play_button_text():
    """Update play button text based on state"""
    if state.btn_audio_play:
        # First, clear the old label to prevent overlapping text
        if hasattr(state.btn_audio_play, 'label') and state.btn_audio_play.label:
            # Some versions of matplotlib store the label text directly
            if hasattr(state.ax_audio_play, 'texts') and state.ax_audio_play.texts:
                for text in state.ax_audio_play.texts:
                    text.remove()
        
        # Set the new button text
        if state.audio_playing:
            state.btn_audio_play.label.set_text('Stop Audio')
            # Set a distinct color for the Stop button
            state.btn_audio_play.color = 'lightcoral'
        else:
            state.btn_audio_play.label.set_text('Play Audio')
            # Reset to normal color
            state.btn_audio_play.color = '0.85'
        
        # Force a redraw of the specific axes rather than the whole figure
        if hasattr(state.ax_audio_play, 'figure'):
            state.ax_audio_play.figure.canvas.draw_idle()
        else:
            # Fall back to full redraw if needed
            plt.draw()

def play_audio(start_idx, end_idx):
    """Play audio for selected time range"""
    try:
        # Map FFT indices to audio samples
        if not hasattr(state, 'audio_segments') or not state.audio_segments:
            add_log_entry("No audio segments available")
            return
            
        audio_start_offset = state.audio_segments[0][0] if state.audio_segments else 0
        
        # Convert FFT indices to actual audio time
        audio_start_time = max(0, start_idx - audio_start_offset)
        audio_end_time = max(0, end_idx - audio_start_offset)
        
        # Calculate sample positions
        start_sample = int(audio_start_time * state.audio_sample_rate)
        end_sample = int(audio_end_time * state.audio_sample_rate)
        
        # Ensure bounds are valid
        if not hasattr(state, 'audio_data') or state.audio_data is None:
            add_log_entry("No audio data available")
            return
            
        # Ensure we stay within audio data boundaries
        audio_length = len(state.audio_data)
        start_sample = max(0, min(start_sample, audio_length - 1))
        end_sample = max(start_sample + 1, min(end_sample, audio_length))
        
        if start_sample >= end_sample - 1:
            add_log_entry(f"Invalid audio range: {start_sample}-{end_sample}")
            return
        
        # Debug info
        add_log_entry(f"Audio samples: {start_sample}-{end_sample} from audio length {audio_length}")
        
        # Extract audio segment and apply volume
        segment = state.audio_data[start_sample:end_sample].copy() * state.audio_volume
        
        # Clip to prevent distortion at high volumes
        segment = np.clip(segment, -1.0, 1.0)
        
        # Create or update playback tracking lines
        try:
            if hasattr(state, 'audio_playback_line') and state.audio_playback_line:
                try:
                    state.audio_playback_line.remove()
                except (ValueError, NotImplementedError, AttributeError):
                    # If the line can't be removed, create a new one anyway
                    pass
                    
            # Create a new playback line
            if hasattr(state, 'ax_spec') and state.ax_spec:
                state.audio_playback_line = state.ax_spec.axvline(
                    start_idx, color='yellow', linewidth=2, linestyle='-', alpha=0.8)
        except Exception as e:
            logging.error(f"Error creating spectrogram playback line: {e}")
            state.audio_playback_line = None
        
        # Create timeline playback line
        try:
            if hasattr(state, 'ax_audio_timeline') and state.ax_audio_timeline:
                if hasattr(state, 'audio_playback_line_timeline') and state.audio_playback_line_timeline:
                    try:
                        state.audio_playback_line_timeline.remove()
                    except (ValueError, NotImplementedError, AttributeError):
                        pass
                        
                # Create a new timeline playback line
                state.audio_playback_line_timeline = state.ax_audio_timeline.axvline(
                    start_idx, color='red', linewidth=2, linestyle='-', alpha=0.8)
        except Exception as e:
            logging.error(f"Error creating timeline playback line: {e}")
            state.audio_playback_line_timeline = None
        
        # Set playback state flags
        state.audio_playing = True
        state.audio_stop_flag = False
        
        # Start playback in a separate thread - use daemon to ensure it exits with main program
        state.audio_thread = threading.Thread(
            target=lambda: play_and_track(segment, start_idx, end_idx), 
            daemon=True)
        state.audio_thread.start()
        
        # Force an immediate redraw to show playback lines
        if hasattr(state, 'fig') and state.fig and hasattr(state.fig, 'canvas'):
            state.fig.canvas.draw_idle()
            
    except Exception as e:
        add_log_entry(f"Error starting audio playback: {str(e)}")
        logging.error("Error in play_audio", exc_info=True)
        state.audio_playing = False

def audio_callback(outdata, frames, time_info, status):
    """Callback function for sounddevice's OutputStream"""
    if status:
        logging.warning(f"Audio status: {status}")
    
    # Get current position from global state
    if not hasattr(state, 'audio_position') or state.audio_position is None:
        logging.error("Audio position not initialized")
        return
    
    if not hasattr(state, 'audio_buffer') or state.audio_buffer is None:
        logging.error("Audio buffer not initialized")
        return
    
    # Add some debug info
    logging.info(f"Audio callback: pos={state.audio_position}, frames={frames}, buffer_length={len(state.audio_buffer)}")
    
    # Calculate how many frames to pull from the buffer
    pos = state.audio_position
    
    # Safety check to ensure we don't go beyond buffer bounds
    if pos >= len(state.audio_buffer):
        logging.info("End of audio buffer reached")
        outdata.fill(0)
        if hasattr(state, 'audio_stream') and state.audio_stream is not None:
            state.audio_finished = True
        return
    
    # Calculate actual frames to read (might be less than requested if near end of buffer)
    frames_to_read = min(frames, len(state.audio_buffer) - pos)
    
    try:
        # Get audio chunk
        chunk = state.audio_buffer[pos:pos + frames_to_read]
        
        # Make sure chunk is right shape for output
        if len(chunk.shape) == 1:  # Mono
            chunk = chunk.reshape(-1, 1)
        
        # If we don't have enough frames, pad with zeros
        if len(chunk) < frames:
            logging.info(f"Padding audio buffer: got {len(chunk)} frames, needed {frames}")
            outdata[:len(chunk)] = chunk
            outdata[len(chunk):] = 0
            # Signal that playback should stop after this buffer
            if hasattr(state, 'audio_stream') and state.audio_stream is not None:
                state.audio_finished = True
        else:
            outdata[:] = chunk
            
        # Update position for next callback
        state.audio_position += frames_to_read
        
    except Exception as e:
        logging.error(f"Error in audio callback: {e}")
        # On error, fill with silence and stop playback
        outdata.fill(0)
        if hasattr(state, 'audio_stream') and state.audio_stream is not None:
            state.audio_finished = True

def play_and_track(segment, start_idx, end_idx):
    """Play audio segment and track position in visualization"""
    try:
        # First, make sure audio state is clean
        state.audio_playing = True
        state.audio_stop_flag = False
        
        # Make sure callback knows about our data
        state.audio_buffer = segment
        state.audio_position = 0
        
        # Start playing audio - this is the main playback call
        sd.play(segment, state.audio_sample_rate, blocking=False)
        add_log_entry(f"Playing audio: {start_idx}-{end_idx} at {int(state.audio_volume * 100)}% volume")
        
        # Track playback position
        duration = len(segment) / state.audio_sample_rate
        start_play_time = time.time()
        
        # Set selected range for visualization reference
        state.selected_range = (start_idx, end_idx)
        
        # Loop to update visualization during playback
        while state.audio_playing and not state.audio_stop_flag:
            # Check if sounddevice is still playing
            if not sd.get_stream().active:
                add_log_entry("Audio stream no longer active")
                break
                
            elapsed = time.time() - start_play_time
            
            if elapsed >= duration:
                add_log_entry("Playback duration exceeded")
                break
            
            # Calculate current position in FFT indices
            progress = elapsed / duration
            current_idx = start_idx + (end_idx - start_idx) * progress
            current_idx_int = int(current_idx)
            
            # Update FFT display
            if current_idx_int < len(state.data_global):
                update_fft(current_idx_int, state.freqs_global, state.data_global)
            
            # Update playback lines with robustness checks
            try:
                if hasattr(state, 'audio_playback_line') and state.audio_playback_line:
                    state.audio_playback_line.set_xdata([current_idx, current_idx])
                # If playback line doesn't exist or was removed, recreate it
                elif hasattr(state, 'ax_spec') and state.ax_spec:
                    state.audio_playback_line = state.ax_spec.axvline(
                        current_idx, color='yellow', linewidth=2, linestyle='-', alpha=0.8)
                    add_log_entry("Recreated spectrogram playback line")
            except Exception as e:
                logging.warning(f"Error updating spectrogram playback line: {e}")
                # Try to recreate the line if there was an error
                try:
                    if hasattr(state, 'ax_spec') and state.ax_spec:
                        state.audio_playback_line = state.ax_spec.axvline(
                            current_idx, color='yellow', linewidth=2, linestyle='-', alpha=0.8)
                except Exception:
                    pass  # If recreation fails, just continue
            
            # Update timeline playback line with similar robustness
            try:
                if hasattr(state, 'audio_playback_line_timeline') and state.audio_playback_line_timeline:
                    state.audio_playback_line_timeline.set_xdata([current_idx, current_idx])
                # If timeline line doesn't exist or was removed, recreate it
                elif hasattr(state, 'ax_audio_timeline') and state.ax_audio_timeline:
                    state.audio_playback_line_timeline = state.ax_audio_timeline.axvline(
                        current_idx, color='red', linewidth=2, linestyle='-', alpha=0.8)
            except Exception as e:
                logging.warning(f"Error updating timeline playback line: {e}")
            
            # Update time display
            update_time_display(elapsed, duration)
            
            # Get current audio chunk for visualization
            current_sample = int(elapsed * state.audio_sample_rate)
            viz_window = int(0.2 * state.audio_sample_rate)  # 200ms window for better visualization
            
            if current_sample < len(segment) - viz_window:
                # Get audio data for visualization - ensure we have a copy to prevent modification
                audio_chunk = segment[current_sample:current_sample + viz_window].copy()
                
                # Add some debug info
                add_log_entry(f"Audio chunk at {elapsed:.2f}s: min={np.min(audio_chunk):.3f}, max={np.max(audio_chunk):.3f}")
                
                # Check if the audio chunk has meaningful variation
                audio_range = np.max(audio_chunk) - np.min(audio_chunk)
                
                # Always amplify the audio signal for better visualization
                # Hydrophone data is often very low amplitude
                # Use a consistent scaling factor for stability - 50x amplification
                # This doesn't affect playback, only visualization
                audio_chunk = audio_chunk * 50.0
                
                # Clip to prevent excessive values
                audio_chunk = np.clip(audio_chunk, -1.0, 1.0)
                
                add_log_entry(f"Visualizing audio: range={audio_range:.5f}, amplified for display")
                
                # Update visualizers with the processed chunk
                update_audio_visualizer(audio_chunk, state.audio_sample_rate, elapsed, duration)
                update_vu_meter(audio_chunk)
            
            # Force redraw - use draw_idle for better performance
            if hasattr(state.fig, 'canvas'):
                state.fig.canvas.draw_idle()
            else:
                plt.draw()
            
            # Small sleep to prevent CPU overload - adjusted for better performance
            time.sleep(0.03)
        
        # Cleanup after playback
        sd.stop()
        
        # Remove playback lines safely
        try:
            if state.audio_playback_line:
                state.audio_playback_line.remove()
                state.audio_playback_line = None
        except Exception as e:
            logging.warning(f"Error removing playback line: {e}")
            state.audio_playback_line = None
            
        try:
            if state.audio_playback_line_timeline:
                state.audio_playback_line_timeline.remove()
                state.audio_playback_line_timeline = None
        except Exception as e:
            logging.warning(f"Error removing timeline playback line: {e}")
            state.audio_playback_line_timeline = None
    
    except Exception as e:
        add_log_entry(f"Audio error: {str(e)}")
        logging.error(f"Error during audio playback", exc_info=True)
    finally:
        # Always ensure audio is marked as not playing in the end
        state.audio_playing = False
        
        # Always clean up resources
        sd.stop()
        
        # Clear buffer references
        state.audio_buffer = None
        state.audio_position = None
        
        add_log_entry("Audio finished")

def update_visualizations(segment, start_idx, end_idx, duration):
    """Separate thread for updating visualization data during playback.
    
    This thread handles updating visualization state variables.
    The on_update_timer function in the main thread will use these to update the UI.
    """
    try:
        add_log_entry("Starting visualization thread")
        
        # Visualization update interval - less frequent for better performance
        viz_update_interval = 0.1  # 100ms
        last_viz_update = time.time()
        
        # Pre-calculate some values
        range_span = end_idx - start_idx
        
        # Initialize visualization state variables if they don't exist
        if not hasattr(state, 'viz_audio_chunk'):
            state.viz_audio_chunk = None
        if not hasattr(state, 'viz_elapsed'):
            state.viz_elapsed = 0
        if not hasattr(state, 'viz_duration'):
            state.viz_duration = duration
        if not hasattr(state, 'viz_current_idx'):
            state.viz_current_idx = start_idx
        if not hasattr(state, 'viz_update_needed'):
            state.viz_update_needed = False
        
        # Start a timer in the main thread for visualization updates
        # Using a timer is more reliable than direct matplotlib updates from a thread
        if not hasattr(state, 'viz_timer') or state.viz_timer is None:
            try:
                # Create a timer only if matplotlib is in interactive mode and figure exists
                if plt.isinteractive() and hasattr(state, 'fig') and hasattr(state.fig, 'canvas'):
                    from matplotlib import _pylab_helpers
                    
                    # This approach works on more platforms
                    if hasattr(state.fig.canvas, 'new_timer'):
                        state.viz_timer = state.fig.canvas.new_timer(interval=50)  # 50ms timer
                        state.viz_timer.add_callback(on_update_timer)
                        state.viz_timer.start()
                        add_log_entry("Created visualization timer")
                    else:
                        add_log_entry("Canvas doesn't support timers, using alternative approach")
                        # We'll update directly in this thread with plt.pause()
            except Exception as e:
                add_log_entry(f"Error creating timer: {str(e)}")
                # Continue anyway - we'll use an alternative approach
        
        # As a fallback, if we don't have a timer, we can use our own loop with plt.pause()
        use_pause_approach = not (hasattr(state, 'viz_timer') and state.viz_timer is not None)
        
        # Main visualization loop
        while state.audio_playing and not state.audio_stop_flag and not state.audio_finished:
            if not hasattr(state, 'audio_position') or state.audio_position is None:
                time.sleep(0.05)
                continue
                
            # Calculate elapsed time from current audio position
            elapsed = state.audio_position / state.audio_sample_rate
            
            # Safety check
            if elapsed > duration:
                elapsed = duration
            
            # Calculate current position in FFT indices
            progress = elapsed / duration
            current_idx = start_idx + range_span * progress
            current_idx_int = int(current_idx)
            
            # Store this information in state for the main thread to use
            state.viz_elapsed = elapsed
            state.viz_duration = duration
            state.viz_current_idx = current_idx_int
            
            # Update visualizers less frequently to reduce load
            now = time.time()
            if now - last_viz_update > viz_update_interval:
                # Get current audio chunk for visualization
                current_sample = int(elapsed * state.audio_sample_rate)
                viz_window = int(0.2 * state.audio_sample_rate)  # 200ms window
                
                if current_sample < len(segment) - viz_window:
                    # Store the audio chunk for the main thread to use
                    state.viz_audio_chunk = segment[current_sample:current_sample + viz_window].copy()
                    state.viz_update_needed = True
                
                # If we're not using a timer, update directly here
                if use_pause_approach:
                    try:
                        # Call the same function the timer would call
                        on_update_timer()
                        
                        # Briefly hand control back to the main thread
                        if hasattr(plt, 'pause'):
                            plt.pause(0.001)
                    except Exception as e:
                        add_log_entry(f"Error in visualization update: {str(e)}")
                
                last_viz_update = now
            
            # Sleep to reduce CPU usage
            time.sleep(0.05)  # 50ms
            
        add_log_entry("Visualization thread finished")
        
    except Exception as e:
        add_log_entry(f"Error in visualization thread: {str(e)}")
        logging.error(f"Visualization thread error: {e}", exc_info=True)

def on_update_timer():
    """Update visualization in the main thread using timer callbacks.
    
    This function is called by a matplotlib timer in the main thread,
    so it's safe to use matplotlib functions here.
    """
    try:
        # Check if we need to update the UI
        if not state.audio_playing or state.audio_stop_flag or state.audio_finished:
            # Stop the timer when audio is not playing
            if hasattr(state, 'viz_timer') and state.viz_timer is not None:
                state.viz_timer.stop()
                state.viz_timer = None
            return
            
        # Check if we have the required playback position info
        if not hasattr(state, 'audio_position') or state.audio_position is None:
            return
            
        # Calculate current position directly from audio_position
        if hasattr(state, 'audio_sample_rate') and state.audio_sample_rate > 0:
            elapsed = state.audio_position / state.audio_sample_rate
            
            # Get duration from state or calculate it
            if hasattr(state, 'viz_duration'):
                duration = state.viz_duration
            else:
                # Default duration if not set
                duration = 10.0
                
            # Update time display directly
            update_time_display(elapsed, duration)
            
            # Calculate current index
            if hasattr(state, 'selected_range'):
                start_idx, end_idx = state.selected_range
                range_span = end_idx - start_idx
                progress = min(1.0, elapsed / duration)
                current_idx = start_idx + range_span * progress
                current_idx_int = int(current_idx)
                
                # Update playback position lines directly
                try:
                    if hasattr(state, 'audio_playback_line') and state.audio_playback_line:
                        state.audio_playback_line.set_xdata([current_idx, current_idx])
                except Exception as e:
                    logging.warning(f"Error updating spectrogram playback line: {e}")
                
                try:
                    if hasattr(state, 'audio_playback_line_timeline') and state.audio_playback_line_timeline:
                        state.audio_playback_line_timeline.set_xdata([current_idx, current_idx])
                except Exception as e:
                    logging.warning(f"Error updating timeline playback line: {e}")
                
                # Update FFT display directly
                if current_idx_int < len(state.data_global):
                    update_fft(current_idx_int, state.freqs_global, state.data_global)
                    
        # Get audio data for visualizers
        if hasattr(state, 'audio_buffer') and hasattr(state, 'audio_position'):
            try:
                # Generate a window of audio data around the current position for visualization
                viz_window = int(0.2 * state.audio_sample_rate)  # 200ms window
                pos = state.audio_position
                
                if hasattr(state, 'audio_buffer') and pos < len(state.audio_buffer) - viz_window:
                    audio_chunk = state.audio_buffer[pos:pos + viz_window]
                    
                    # Update visualizers directly
                    if audio_chunk.size > 0:
                        update_audio_visualizer(audio_chunk, state.audio_sample_rate, elapsed, duration)
                        update_vu_meter(audio_chunk)
            except Exception as e:
                logging.warning(f"Error updating audio visualizers: {e}")
        
        # Trigger a redraw of the axes that were updated
        try:
            # Batch all draw_idle calls to reduce overhead
            axes_to_redraw = []
            
            if hasattr(state, 'ax_fft') and state.ax_fft is not None:
                axes_to_redraw.append(state.ax_fft)
            if hasattr(state, 'ax_spec') and state.ax_spec is not None:
                axes_to_redraw.append(state.ax_spec)
            if hasattr(state, 'ax_audio_visualizer') and state.ax_audio_visualizer is not None:
                axes_to_redraw.append(state.ax_audio_visualizer)
            if hasattr(state, 'ax_vu_meter') and state.ax_vu_meter is not None:
                axes_to_redraw.append(state.ax_vu_meter)
            if hasattr(state, 'ax_time_display') and state.ax_time_display is not None:
                axes_to_redraw.append(state.ax_time_display)
                
            if len(axes_to_redraw) > 0 and hasattr(state, 'fig') and state.fig is not None:
                # Only call draw_idle once for the figure
                state.fig.canvas.draw_idle()
        except Exception as e:
            logging.warning(f"Error redrawing visualization: {e}")
        
    except Exception as e:
        logging.error(f"Error in visualization timer: {e}", exc_info=True)
        
        # Cleanup after playback
        sd.stop()
        
        # Remove playback lines safely
        try:
            if state.audio_playback_line:
                state.audio_playback_line.remove()
                state.audio_playback_line = None
        except ValueError:
            state.audio_playback_line = None
            
        try:
            if state.audio_playback_line_timeline:
                state.audio_playback_line_timeline.remove()
                state.audio_playback_line_timeline = None
        except ValueError:
            state.audio_playback_line_timeline = None
        
        # Clear visualizers safely
        if state.ax_audio_visualizer and state.fig:
            try:
                # Clear all artists but keep the axes
                for artist in state.ax_audio_visualizer.lines[:]:
                    artist.remove()
                for artist in state.ax_audio_visualizer.texts[:]:
                    artist.remove()
                for patch in state.ax_audio_visualizer.patches[:]:
                    patch.remove()
                
                state.ax_audio_visualizer.set_facecolor('black')
                state.ax_audio_visualizer.set_title('Audio Waveform', fontsize=9, pad=4)
                state.ax_audio_visualizer.set_xlim(0, 1)
                state.ax_audio_visualizer.set_ylim(-1, 1)
                state.ax_audio_visualizer.grid(True, alpha=0.3)
            except Exception as e:
                logging.error(f"Error clearing audio visualizer: {e}")
        
        if state.ax_vu_meter and state.fig:
            try:
                # Clear all artists but keep the axes
                for patch in state.ax_vu_meter.patches[:]:
                    patch.remove()
                for line in state.ax_vu_meter.lines[:]:
                    line.remove()
                for text in state.ax_vu_meter.texts[:]:
                    text.remove()
                
                state.ax_vu_meter.set_facecolor('black')
                state.ax_vu_meter.set_title(f'VU Meter - Volume: {int(state.audio_volume * 100)}%', 
                                    fontsize=9, pad=4)
                state.ax_vu_meter.set_xlim(-60, 0)
                state.ax_vu_meter.set_ylim(0, 1)
                state.ax_vu_meter.set_yticks([])
            except Exception as e:
                logging.error(f"Error clearing VU meter: {e}")
        
        # Restore stacked FFT view at the end
        update_fft_range(start_idx, end_idx, state.freqs_global, state.data_global)
        
        # Safe draw
        try:
            if state.fig:
                state.fig.canvas.draw_idle()
        except Exception as e:
            logging.error(f"Error during final draw: {e}")
        
    except Exception as e:
        add_log_entry(f"Audio error: {str(e)}")
        logging.error(f"Error during audio playback", exc_info=True)
    finally:
        state.audio_playing = False
        # Note: we don't call update_play_button_text() here anymore
        # because the on_play_audio function in event_handlers.py
        # will recreate the button when it checks state.audio_playing
        add_log_entry("Audio finished")

def stop_audio():
    """Stop audio playback"""
    # Set state flags first - these control playback loops
    state.audio_stop_flag = True
    state.audio_playing = False
    
    # Ensure playback is stopped - this is the main call to stop audio
    sd.stop()
    
    # Log that the audio was stopped
    add_log_entry("Audio stopped by user")
    
    # Clean up any resources properly
    # Stop visualization timer if it exists
    if hasattr(state, 'viz_timer') and state.viz_timer is not None:
        try:
            state.viz_timer.stop()
            state.viz_timer = None
        except Exception as e:
            logging.error(f"Error stopping visualization timer: {e}")
    
    # Clear position indicators with more specific error handling
    if hasattr(state, 'audio_playback_line') and state.audio_playback_line:
        try:
            state.audio_playback_line.remove()
        except (ValueError, NotImplementedError, AttributeError) as e:
            # Just log the error and continue
            logging.warning(f"Could not remove spectrogram playback line: {e}")
        except Exception as e:
            logging.error(f"Unexpected error removing spectrogram playback line: {e}")
        # Set to None anyway to prevent further use
        state.audio_playback_line = None
    
    if hasattr(state, 'audio_playback_line_timeline') and state.audio_playback_line_timeline:
        try:
            state.audio_playback_line_timeline.remove()
        except (ValueError, NotImplementedError, AttributeError) as e:
            # Just log the error and continue
            logging.warning(f"Could not remove timeline playback line: {e}")
        except Exception as e:
            logging.error(f"Unexpected error removing timeline playback line: {e}")
        # Set to None anyway to prevent further use
        state.audio_playback_line_timeline = None
    
    # Reset global state
    state.viz_update_needed = False
    state.audio_buffer = None
    state.audio_position = None
    
    # Note: we don't call update_play_button_text() here anymore
    # because the on_play_audio function in event_handlers.py
    # will recreate the button with the correct label
    
    # Clear audio visualizer safely
    if hasattr(state, 'ax_audio_visualizer') and state.ax_audio_visualizer and hasattr(state, 'fig') and state.fig:
        try:
            # Clear all artists but keep the axes
            for artist in state.ax_audio_visualizer.lines[:]:
                artist.remove()
            for artist in state.ax_audio_visualizer.texts[:]:
                artist.remove()
            state.ax_audio_visualizer.set_facecolor('black')
            state.ax_audio_visualizer.set_title('Audio Waveform', fontsize=9, pad=4)
            state.ax_audio_visualizer.set_xlim(0, 1)
            state.ax_audio_visualizer.set_ylim(-1, 1)
            state.ax_audio_visualizer.grid(True, alpha=0.3)
        except Exception as e:
            logging.error(f"Error clearing audio visualizer on stop: {e}")
    
    # Clear VU meter safely
    if hasattr(state, 'ax_vu_meter') and state.ax_vu_meter and hasattr(state, 'fig') and state.fig:
        try:
            # Clear all artists but keep the axes
            for patch in state.ax_vu_meter.patches[:]:
                patch.remove()
            for line in state.ax_vu_meter.lines[:]:
                line.remove()
            for text in state.ax_vu_meter.texts[:]:
                text.remove()
            state.ax_vu_meter.set_facecolor('black')
            state.ax_vu_meter.set_title(f'VU Meter - Volume: {int(state.audio_volume * 100)}%', 
                                fontsize=9, pad=4)
            state.ax_vu_meter.set_xlim(-60, 0)
            state.ax_vu_meter.set_ylim(0, 1)
            state.ax_vu_meter.set_yticks([])
        except Exception as e:
            logging.error(f"Error clearing VU meter on stop: {e}")
    
    # Safe draw
    try:
        if hasattr(state, 'fig') and state.fig and hasattr(state.fig, 'canvas'):
            state.fig.canvas.draw_idle()
    except Exception as e:
        logging.error(f"Error during draw on stop: {e}")
        # Fallback to plt.draw() if needed
        try:
            plt.draw()
        except Exception as e2:
            logging.error(f"Error during plt.draw fallback: {e2}")
    
    # Final status update
    add_log_entry("Audio playback fully stopped")