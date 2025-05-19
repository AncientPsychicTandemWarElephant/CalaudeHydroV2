"""
ui_state_updates.py - Functions to update UI element states based on application state
"""

import matplotlib.pyplot as plt

def update_delete_button_state(state):
    """Update the delete button's visual state based on comment selection"""
    if not hasattr(state, 'btn_delete_comment') or state.btn_delete_comment is None:
        return
        
    if hasattr(state, 'selected_comment_id') and state.selected_comment_id is not None:
        # Enable the button
        state.btn_delete_comment.ax.set_alpha(1.0)
        state.btn_delete_comment.color = '0.85'
        # Update the face color of button components
        for child in state.btn_delete_comment.ax.get_children():
            if hasattr(child, 'set_facecolor'):
                child.set_facecolor('0.85')
    else:
        # Disable the button
        state.btn_delete_comment.ax.set_alpha(0.5)
        state.btn_delete_comment.color = '0.95'
        # Update the face color of button components
        for child in state.btn_delete_comment.ax.get_children():
            if hasattr(child, 'set_facecolor'):
                child.set_facecolor('0.95')