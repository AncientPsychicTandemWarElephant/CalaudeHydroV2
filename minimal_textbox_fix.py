"""
minimal_textbox_fix.py - Minimal fix for textbox lag that avoids breaking functionality
Just optimizes the existing TextBox without creating new classes
"""

def apply_minimal_fix(state):
    """Apply minimal optimizations to existing textboxes without replacing them"""
    
    # Just disable blitting and use draw_idle for existing textboxes
    if hasattr(state, 'comment_input'):
        tb = state.comment_input
        # Disable blitting
        if hasattr(tb, '_use_blit'):
            tb._use_blit = False
        if hasattr(tb, 'useblit'):
            tb.useblit = False
        if hasattr(tb, '_animated'):
            tb._animated = False
    
    if hasattr(state, 'notes_input'):
        tb = state.notes_input
        # Disable blitting
        if hasattr(tb, '_use_blit'):
            tb._use_blit = False
        if hasattr(tb, 'useblit'):
            tb.useblit = False
        if hasattr(tb, '_animated'):
            tb._animated = False
    
    # Optimize figure settings
    if hasattr(state.fig.canvas, 'supports_blit'):
        state.fig.canvas.supports_blit = False
    
    return state