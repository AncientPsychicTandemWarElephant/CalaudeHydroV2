"""
textbox_lag_fix.py - Aggressive optimization for comment textbox lag issues
Reduces redraw frequency and optimizes event handling
"""

import time
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox

class LazyTextBox(TextBox):
    """Custom TextBox with lazy updates to reduce lag"""
    
    def __init__(self, ax, label, initial='', color='.95', hovercolor='1',
                 label_pad=.01, textalignment="left"):
        super().__init__(ax, label, initial=initial, color=color, 
                        hovercolor=hovercolor, label_pad=label_pad,
                        textalignment=textalignment)
        
        # Disable all blitting and animation
        self._use_blit = False
        self.useblit = False
        self._animated = False
        
        # Track last update time
        self._last_update = 0
        self._update_delay = 0.1  # Update at most every 100ms
        self._pending_text = None
        self._update_scheduled = False
        
        # Override key handler - use the correct attribute name
        if hasattr(self, '_keypress'):
            self._original_on_key = self._keypress
            self._keypress = self._lazy_on_keypress
        elif hasattr(self, '_on_keypress'):
            self._original_on_key = self._on_keypress
            self._on_keypress = self._lazy_on_keypress
        elif hasattr(self, 'on_keypress'):
            self._original_on_key = self.on_keypress
            self.on_keypress = self._lazy_on_keypress
    
    def _lazy_on_keypress(self, event):
        """Lazy keypress handler that batches updates"""
        # Process the key immediately
        self._original_on_key(event)
        
        # Store pending text
        self._pending_text = self.text
        
        # Schedule update if not already scheduled
        current_time = time.time()
        if not self._update_scheduled and current_time - self._last_update > self._update_delay:
            self._update_scheduled = True
            self.ax.figure.canvas.draw_idle()
            self._last_update = current_time
            self._update_scheduled = False
    
    def set_val(self, val):
        """Override set_val to use lazy updates"""
        if self.text == val:
            return
        self.text = str(val)
        self.text_disp.set_text(self._format_text(self.text))
        
        # Use draw_idle for better performance
        if self.eventson:
            self._observers.process('change', self.text)
            if hasattr(self.ax.figure.canvas, 'draw_idle'):
                current_time = time.time()
                if current_time - self._last_update > self._update_delay:
                    self.ax.figure.canvas.draw_idle()
                    self._last_update = current_time
    
    def _format_text(self, text):
        """Format text for display with cursor"""
        return text + self.cursor


def create_optimized_textbox(ax, label='', initial='', **kwargs):
    """Create an optimized textbox with reduced lag"""
    textbox = LazyTextBox(ax, label, initial=initial, **kwargs)
    return textbox


def apply_aggressive_optimization(state, use_fast_widget=True):
    """Apply aggressive optimization to existing textboxes"""
    
    if use_fast_widget:
        # Use the ultra-fast widget
        try:
            from fast_text_widget import create_fast_text_widget
            
            if hasattr(state, 'comment_input'):
                ax = state.comment_input.ax
                initial = state.comment_input.text
                state.comment_input.disconnect_events()
                ax.clear()
                state.comment_input = create_fast_text_widget(ax, '', initial=initial)
            
            if hasattr(state, 'notes_input'):
                ax = state.notes_input.ax
                initial = state.notes_input.text
                state.notes_input.disconnect_events()
                ax.clear()
                state.notes_input = create_fast_text_widget(ax, '', initial=initial)
                
        except ImportError:
            # Fallback to lazy textbox
            use_fast_widget = False
    
    if not use_fast_widget:
        # Replace existing textboxes with lazy versions
        if hasattr(state, 'comment_input'):
            ax = state.comment_input.ax
            initial = state.comment_input.text
            state.comment_input.disconnect_events()
            ax.clear()
            state.comment_input = create_optimized_textbox(ax, '', initial=initial)
            state.comment_input.label.set_fontsize(8)
        
        if hasattr(state, 'notes_input'):
            ax = state.notes_input.ax
            initial = state.notes_input.text
            state.notes_input.disconnect_events()
            ax.clear()
            state.notes_input = create_optimized_textbox(ax, '', initial=initial)
            state.notes_input.label.set_fontsize(8)
    
    # Disable global blitting for the figure
    if hasattr(state.fig.canvas, 'supports_blit'):
        state.fig.canvas.supports_blit = False
    
    # Set matplotlib to use lazy rendering
    plt.rcParams['figure.autolayout'] = False
    plt.rcParams['figure.max_open_warning'] = 0
    
    # Reduce update frequency
    if hasattr(state.fig.canvas, 'set_window_update_rate'):
        try:
            state.fig.canvas.set_window_update_rate(10)  # Max 10 updates per second
        except:
            pass
    
    return state


def patch_textbox_globally():
    """Global patch to make all TextBox instances less laggy"""
    
    # Patch the TextBox class itself
    original_init = TextBox.__init__
    
    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # Disable blitting by default
        self._use_blit = False
        self.useblit = False
        self._animated = False
    
    TextBox.__init__ = patched_init
    
    # Patch the keypress handler - check for all possible attribute names
    if hasattr(TextBox, '_keypress'):
        original_keypress = TextBox._keypress
        attr_name = '_keypress'
    elif hasattr(TextBox, '_on_keypress'):
        original_keypress = TextBox._on_keypress
        attr_name = '_on_keypress'
    elif hasattr(TextBox, 'on_keypress'):
        original_keypress = TextBox.on_keypress
        attr_name = 'on_keypress'
    else:
        return  # Skip patching if no keypress attribute exists
    
    def patched_keypress(self, event):
        original_keypress(self, event)
        # Use draw_idle instead of draw
        if hasattr(self.ax.figure.canvas, 'draw_idle'):
            self.ax.figure.canvas.draw_idle()
    
    setattr(TextBox, attr_name, patched_keypress)


# Apply the global patch on import
patch_textbox_globally()