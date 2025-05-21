"""
focused_textbox_fix.py - Focused optimization for comment textbox lag
Implements smart region-based updates to minimize redrawing
"""

import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox
import numpy as np
import time

class SmartTextBox(TextBox):
    """Optimized TextBox with region-based updates"""
    
    def __init__(self, ax, label, initial='', **kwargs):
        super().__init__(ax, label, initial=initial, **kwargs)
        
        # Disable blitting for this widget
        self._use_blit = False
        self._animated = False
        
        # Track update timing
        self._last_update = 0
        self._update_threshold = 0.03  # 30ms threshold
        
        # Cache the background
        self._background = None
        self._needs_background_update = True
        
        # Override the submit to not trigger on every character
        self._submit_on_enter_only = True
        
        # Store original methods - check for the correct attribute name
        if hasattr(self, '_keypress'):
            self._original_on_keypress = self._keypress
            self._keypress = self._smart_on_keypress
        elif hasattr(self, '_on_keypress'):
            self._original_on_keypress = self._on_keypress
            self._on_keypress = self._smart_on_keypress
        elif hasattr(self, 'on_keypress'):
            self._original_on_keypress = self.on_keypress
            self.on_keypress = self._smart_on_keypress
    
    def _cache_background(self):
        """Cache the background for faster updates"""
        if self._needs_background_update and self.ax.figure.canvas:
            self._background = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)
            self._needs_background_update = False
    
    def _smart_on_keypress(self, event):
        """Smart keypress handler with region-based updates"""
        # Process the key through the parent handler
        self._original_on_keypress(event)
        
        # Smart update based on timing
        current_time = time.time()
        if current_time - self._last_update > self._update_threshold:
            self._smart_update()
            self._last_update = current_time
    
    def _smart_update(self):
        """Update only the text region"""
        if not self.ax.figure.canvas:
            return
            
        try:
            # Cache background if needed
            if self._background is None:
                self._cache_background()
            
            # Restore the cached background
            if self._background:
                self.ax.figure.canvas.restore_region(self._background)
            
            # Redraw only the text
            self.ax.draw_artist(self.text_disp)
            
            # Blit only this axis region
            self.ax.figure.canvas.blit(self.ax.bbox)
        except:
            # Fallback to idle draw on error
            self.ax.figure.canvas.draw_idle()
    
    def set_val(self, val):
        """Optimized value setter"""
        # Call parent's set_val
        super().set_val(val)
        
        # Use smart update for visual refresh
        self._smart_update()
    
    def _format_text(self, text):
        """Format text for display with cursor"""
        # For SmartTextBox, we just return the text as-is
        # The parent class handles cursor display
        return text


class MinimalTextBox:
    """Ultra-minimal text box for maximum performance"""
    
    def __init__(self, ax, label='', initial='', color='.95'):
        self.ax = ax
        self.text = initial
        self.observers = {'change': [], 'submit': []}
        
        # Setup the axes
        self.ax.set_facecolor(color)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        # Create the text display
        self.text_display = self.ax.text(0.02, 0.5, initial,
                                        transform=self.ax.transAxes,
                                        verticalalignment='center',
                                        fontsize=10)
        
        # Simple cursor
        self.cursor_line = self.ax.axvline(x=0.02, ymin=0.2, ymax=0.8,
                                          color='black', linewidth=1,
                                          visible=False)
        
        # Track state
        self.active = False
        self._last_update = 0
        
        # Connect events
        self.cid_click = ax.figure.canvas.mpl_connect('button_press_event', self._on_click)
        self.cid_key = ax.figure.canvas.mpl_connect('key_press_event', self._on_key)
    
    def _on_click(self, event):
        """Handle mouse clicks"""
        self.active = event.inaxes == self.ax
        self.cursor_line.set_visible(self.active)
        self._update_display()
    
    def _on_key(self, event):
        """Handle key presses"""
        if not self.active:
            return
            
        if event.key == 'backspace':
            if self.text:
                self.text = self.text[:-1]
                self._update_display()
        elif event.key == 'enter':
            self._notify_observers('submit')
        elif event.key and len(event.key) == 1:
            self.text += event.key
            self._update_display()
            self._notify_observers('change')
    
    def _update_display(self):
        """Update the display with minimal redrawing"""
        current_time = time.time()
        if current_time - self._last_update > 0.02:  # 20ms throttle
            self.text_display.set_text(self.text)
            
            # Only update the text area
            bbox = self.ax.bbox
            self.ax.figure.canvas.draw_artist(self.text_display)
            if self.active:
                self.ax.figure.canvas.draw_artist(self.cursor_line)
            self.ax.figure.canvas.blit(bbox)
            
            self._last_update = current_time
    
    def _notify_observers(self, event_type):
        """Notify observers of events"""
        for callback in self.observers.get(event_type, []):
            callback(self.text)
    
    def on_text_change(self, func):
        """Register a change callback"""
        self.observers['change'].append(func)
    
    def on_submit(self, func):
        """Register a submit callback"""
        self.observers['submit'].append(func)
    
    def set_val(self, val):
        """Set the text value"""
        self.text = str(val)
        self._update_display()
    
    def disconnect_events(self):
        """Disconnect all events"""
        self.ax.figure.canvas.mpl_disconnect(self.cid_click)
        self.ax.figure.canvas.mpl_disconnect(self.cid_key)


def apply_focused_fix(state):
    """Apply focused optimization to comment textboxes"""
    
    # Check what type of textbox we have
    if hasattr(state, 'comment_input') and isinstance(state.comment_input, TextBox):
        # Replace with SmartTextBox
        ax = state.comment_input.ax
        initial = state.comment_input.text
        state.comment_input.disconnect_events()
        ax.clear()
        
        state.comment_input = SmartTextBox(ax, '', initial=initial)
        state.comment_input.text_disp.set_fontsize(8)
    
    if hasattr(state, 'notes_input') and isinstance(state.notes_input, TextBox):
        # Replace with SmartTextBox  
        ax = state.notes_input.ax
        initial = state.notes_input.text
        state.notes_input.disconnect_events()
        ax.clear()
        
        state.notes_input = SmartTextBox(ax, '', initial=initial)
        state.notes_input.text_disp.set_fontsize(8)
    
    # Set optimal matplotlib parameters
    plt.rcParams['figure.autolayout'] = False
    plt.rcParams['axes.autoscale_enable'] = False
    
    # Optimize the figure canvas
    if hasattr(state.fig.canvas, 'draw_idle'):
        # Replace the draw method with draw_idle for better performance
        state.fig.canvas.draw = state.fig.canvas.draw_idle
    
    return state


def test_performance():
    """Test the performance of different textbox implementations"""
    import time
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(6, 4))
    
    # Standard TextBox
    tb1 = TextBox(ax1, 'Standard:', initial='Type here...')
    
    # SmartTextBox
    tb2 = SmartTextBox(ax2, 'Smart:', initial='Type here...')
    
    # MinimalTextBox
    tb3 = MinimalTextBox(ax3, 'Minimal:', initial='Type here...')
    
    # Performance counter
    update_times = []
    
    def measure_update(text):
        start = time.time()
        fig.canvas.draw_idle()
        update_times.append(time.time() - start)
        print(f"Update time: {update_times[-1]*1000:.1f}ms")
    
    tb1.on_text_change(measure_update)
    tb2.on_text_change(measure_update)
    tb3.on_text_change(measure_update)
    
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    test_performance()