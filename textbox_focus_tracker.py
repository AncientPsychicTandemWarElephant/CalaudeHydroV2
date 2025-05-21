"""
textbox_focus_tracker.py - Track which textbox has focus to disable shortcuts
"""

import state

# Global focus tracking
_focused_textbox = None

def set_textbox_focus(textbox):
    """Mark a textbox as having focus"""
    global _focused_textbox
    _focused_textbox = textbox

def clear_textbox_focus():
    """Clear textbox focus"""
    global _focused_textbox
    _focused_textbox = None

def has_textbox_focus():
    """Check if any textbox currently has focus"""
    global _focused_textbox
    return _focused_textbox is not None

def is_comment_textbox_focused():
    """Check if a comment textbox specifically has focus"""
    if not has_textbox_focus():
        return False
    
    # Check if it's one of the comment textboxes
    if hasattr(state, 'comment_input') and _focused_textbox == state.comment_input:
        return True
    if hasattr(state, 'notes_input') and _focused_textbox == state.notes_input:
        return True
    
    return False

def setup_textbox_focus_tracking(state):
    """Setup focus tracking for textboxes"""
    
    # Track focus for comment input
    if hasattr(state, 'comment_input'):
        original_begin = state.comment_input.begin_typing
        original_stop = state.comment_input.stop_typing
        
        def tracked_begin(*args, **kwargs):
            set_textbox_focus(state.comment_input)
            return original_begin(*args, **kwargs)
        
        def tracked_stop(*args, **kwargs):
            clear_textbox_focus()
            return original_stop(*args, **kwargs)
        
        state.comment_input.begin_typing = tracked_begin
        state.comment_input.stop_typing = tracked_stop
    
    # Track focus for notes input
    if hasattr(state, 'notes_input'):
        original_begin = state.notes_input.begin_typing
        original_stop = state.notes_input.stop_typing
        
        def tracked_begin(*args, **kwargs):
            set_textbox_focus(state.notes_input)
            return original_begin(*args, **kwargs)
        
        def tracked_stop(*args, **kwargs):
            clear_textbox_focus()
            return original_stop(*args, **kwargs)
        
        state.notes_input.begin_typing = tracked_begin
        state.notes_input.stop_typing = tracked_stop
    
    # Also track when clicking outside textboxes
    if hasattr(state, 'fig'):
        original_button_press = None
        
        # Get the current button press handler
        for cid, func in state.fig.canvas.callbacks.callbacks.get('button_press_event', {}).items():
            if func.__name__ == 'on_button_press':
                original_button_press = func
                break
        
        def tracked_button_press(event):
            # Clear focus if clicking outside textboxes
            if event.inaxes:
                if hasattr(state, 'comment_input') and event.inaxes != state.comment_input.ax:
                    if hasattr(state, 'notes_input') and event.inaxes != state.notes_input.ax:
                        clear_textbox_focus()
            
            # Call original handler if it exists
            if original_button_press:
                original_button_press(event)
        
        # Replace the handler
        state.fig.canvas.mpl_connect('button_press_event', tracked_button_press)