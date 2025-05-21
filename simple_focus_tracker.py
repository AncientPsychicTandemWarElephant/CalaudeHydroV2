"""
simple_focus_tracker.py - Simple focus tracking for textboxes
Uses matplotlib's event system to track which widget has focus
"""

import state
from matplotlib.widgets import TextBox

# Global variable to track focused textbox
_active_textbox = None

def is_textbox_focused():
    """Check if any textbox currently has focus"""
    # Check comment textboxes
    if hasattr(state, 'comment_input') and isinstance(state.comment_input, TextBox):
        if state.comment_input.active:
            return True
    
    if hasattr(state, 'notes_input') and isinstance(state.notes_input, TextBox):
        if state.notes_input.active:
            return True
    
    return False

def setup_simple_focus_tracking(state):
    """Setup simple focus tracking using matplotlib's click events"""
    # Nothing special needed - matplotlib TextBox already tracks 'active' state
    # Just need to check it in the event handlers
    pass