"""
comment_operations.py - Comment Management Operations

This module provides core functionality for comment management, including
deletion and other operations that affect comments. It centralizes comment
operations to maintain consistency across the application UI.
"""

import matplotlib.pyplot as plt
from tkinter import messagebox
from utils import add_log_entry
import state

def delete_selected_comment():
    """
    Delete the currently selected comment with confirmation dialog
    
    This function handles the complete comment deletion workflow:
    - Verifies a comment is selected
    - Displays a confirmation dialog
    - Removes the comment if confirmed
    - Updates all relevant UI components to reflect the change
    
    Returns:
        bool: True if comment was deleted, False otherwise
    """
    add_log_entry("Delete selected comment called")
    
    # Check if a comment is selected
    if not hasattr(state, 'selected_comment_id') or state.selected_comment_id is None:
        add_log_entry("No comment selected to delete")
        messagebox.showinfo("No Selection", "Please select a comment to delete.")
        return
    
    # Find the selected comment
    comment_to_delete = None
    for i, comment in enumerate(state.comments):
        if comment['id'] == state.selected_comment_id:
            comment_to_delete = comment
            comment_index = i
            break
    
    if comment_to_delete is None:
        add_log_entry("Selected comment not found")
        return
    
    # Confirm deletion
    result = messagebox.askyesno(
        "Confirm Delete", 
        f"Delete comment '{comment_to_delete['text'][:30]}...'?",
        icon='warning'
    )
    
    if result:
        # Remove the comment
        state.comments.pop(comment_index)
        add_log_entry(f"Deleted comment: {comment_to_delete['text']}")
        
        # Clear selection
        state.selected_comment_id = None
        
        # Update the display
        from visualization import update_comment_markers
        update_comment_markers()
        
        # No need to clear the comment display window as it has been removed
        # We just need to update the comment list
        
        # Update delete button state since no comment is selected
        try:
            from ui_state_updates import update_delete_button_state
            update_delete_button_state(state)
        except ImportError:
            # If update_delete_button_state is not available, try to update the button text directly
            if hasattr(state, 'update_add_comment_button_text'):
                state.update_add_comment_button_text()
            pass
        
        # Update comment list display if available
        try:
            import sys
            if 'comment_list' in sys.modules:
                from comment_list import update_comment_list_display
                update_comment_list_display()
        except ImportError:
            pass
        
        plt.draw()
        add_log_entry("Comment deleted successfully")
        return True
    else:
        add_log_entry("Delete cancelled")
        return False