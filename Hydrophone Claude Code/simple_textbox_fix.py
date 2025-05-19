"""
simple_textbox_fix.py - Simple fix for textbox lag
Just reduce update frequency without changing the widget
"""

import time
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox

def apply_simple_lag_fix(state):
    """Apply simple lag fixes without replacing widgets"""
    
    # Disable blitting for textboxes
    if hasattr(state, 'comment_input'):
        state.comment_input._use_blit = False
        if hasattr(state.comment_input, 'useblit'):
            state.comment_input.useblit = False
        state.comment_input._animated = False
    
    if hasattr(state, 'notes_input'):
        state.notes_input._use_blit = False
        if hasattr(state.notes_input, 'useblit'):
            state.notes_input.useblit = False
        state.notes_input._animated = False
    
    # Create throttled update functions
    def create_throttled_handler(textbox, delay=0.1):
        last_update = [0]
        original_keypress = textbox._on_keypress
        
        def throttled_keypress(event):
            # Always process the key
            original_keypress(event)
            
            # But throttle canvas updates
            current_time = time.time()
            if current_time - last_update[0] > delay:
                last_update[0] = current_time
                if hasattr(textbox.ax.figure.canvas, 'draw_idle'):
                    textbox.ax.figure.canvas.draw_idle()
                else:
                    textbox.ax.figure.canvas.draw()
        
        textbox._on_keypress = throttled_keypress
    
    # Apply throttling
    if hasattr(state, 'comment_input'):
        create_throttled_handler(state.comment_input, delay=0.05)
    
    if hasattr(state, 'notes_input'):
        create_throttled_handler(state.notes_input, delay=0.05)
    
    # Optimize matplotlib settings
    plt.rcParams['figure.autolayout'] = False
    plt.rcParams['path.simplify'] = True
    plt.rcParams['path.simplify_threshold'] = 1.0
    
    # Disable figure-wide blitting
    if hasattr(state.fig.canvas, 'supports_blit'):
        state.fig.canvas.supports_blit = False
    
    return state