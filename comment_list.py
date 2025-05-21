"""
comment_list.py - Functions for displaying and managing the comment list
"""

import matplotlib.pyplot as plt
import logging
from matplotlib.widgets import Button
import numpy as np
import state
from utils import add_log_entry
from visualization import update_comment_markers, display_selected_comment

def create_comment_list_display():
    """Create the comment list display panel"""
    # Get spectrogram position to align with
    spec_pos = state.ax_spec.get_position() if hasattr(state, 'ax_spec') else None
    
    # Define position for the comment list panel
    comment_list_width = 0.45  # Wider to fit more text
    comment_list_height = 0.13  # Previous height
    
    # Position near the bottom of the screen, less to the right and further down
    comment_list_left = (spec_pos.x0 if spec_pos else 0.15) + 0.05  # Less offset to the right
    comment_list_bottom = 0.005  # Very close to the bottom of the window
    
    # Create axes for the comment list with enhanced appearance
    state.ax_comment_list = state.fig.add_axes(
        [comment_list_left, comment_list_bottom, comment_list_width, comment_list_height], 
        frameon=True, 
        facecolor='#e6f2ff'  # Light blue background for better visibility
    )
    
    # Set title with larger font and better styling
    state.ax_comment_list.set_title("Comment List", fontsize=12, pad=8, color='#1E3A8A', weight='bold', loc='left')
    state.ax_comment_list.axis("off")
    
    # Add enhanced border for better visibility
    for spine in state.ax_comment_list.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor('#4682B4')  # Steel blue border
        spine.set_linewidth(2)
    
    # Initialize state variables for comment list
    if not hasattr(state, 'comment_list_position'):
        state.comment_list_position = 0
    if not hasattr(state, 'visible_comments'):
        state.visible_comments = 4  # Show 4 comments with the shorter boxes
    if not hasattr(state, 'comment_texts'):
        state.comment_texts = []
    
    # Create scroll buttons - adjusted for new position
    button_width = 0.03
    button_height = 0.025
    
    ax_comment_up = state.fig.add_axes([comment_list_left - button_width - 0.01, 
                                      comment_list_bottom + comment_list_height - button_height - 0.01, 
                                      button_width, button_height])
    state.btn_comment_up = Button(ax_comment_up, '▲', color='0.85')
    
    ax_comment_down = state.fig.add_axes([comment_list_left - button_width - 0.01, 
                                        comment_list_bottom + 0.01, 
                                        button_width, button_height])
    state.btn_comment_down = Button(ax_comment_down, '▼', color='0.85')
    
    # Connect event handlers
    state.btn_comment_up.on_clicked(scroll_comments_up)
    state.btn_comment_down.on_clicked(scroll_comments_down)
    
    # Initialize the comment list display
    update_comment_list_display()
    
    return state.ax_comment_list

def update_comment_list_display():
    """Update the comment list display with current comments"""
    if not hasattr(state, 'ax_comment_list') or state.ax_comment_list is None:
        add_log_entry("Comment list display not initialized")
        return
    
    # Clear previous display
    state.ax_comment_list.clear()
    state.ax_comment_list.axis("off")
    state.comment_texts = []
    
    # Restore border
    for spine in state.ax_comment_list.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor('#d0d0d0')
        spine.set_linewidth(1)
    
    # Check if we have any comments
    if not hasattr(state, 'comments') or not state.comments:
        state.ax_comment_list.text(0.5, 0.5, "No comments", 
                                 ha='center', va='center', 
                                 fontsize=12, color='gray',
                                 transform=state.ax_comment_list.transAxes)
        plt.draw()
        return
    
    # Sort comments chronologically by start index (earliest first)
    sorted_comments = sorted(state.comments, key=lambda c: c['start_idx'])
    
    # Calculate visible range
    start_idx = state.comment_list_position
    end_idx = min(start_idx + state.visible_comments, len(sorted_comments))
    
    # Display comments (earliest at the top)
    for i, comment in enumerate(sorted_comments[start_idx:end_idx]):
        # Calculate vertical position (from top to bottom) - adjusted spacing for shorter boxes
        y_pos = 0.92 - (i * 0.21)  # Less space needed between comments for shorter boxes
        
        # Determine background color based on selection
        is_selected = comment['id'] == state.selected_comment_id
        bg_color = '#FFD700' if is_selected else 'white'  # Gold for selected, white for others
        
        # Create optimized comment rectangle for cleaner display
        rect_height = 0.18  # Make rectangles shorter since notes are on same line
        rect_top = y_pos - 0.01  # Position text properly within the box
        
        rect = plt.Rectangle((0.02, rect_top - rect_height), 0.96, rect_height,
                           facecolor=bg_color, alpha=0.97,  # Higher opacity for better contrast
                           edgecolor='#1E3A8A', linewidth=1.5, 
                           transform=state.ax_comment_list.transAxes,
                           picker=True, zorder=1)
        
        # Add a subtle drop shadow effect for depth
        shadow = plt.Rectangle((0.025, rect_top - rect_height - 0.01), 0.96, rect_height,
                              facecolor='#666666', alpha=0.1,
                              transform=state.ax_comment_list.transAxes,
                              zorder=0)
        state.ax_comment_list.add_patch(shadow)
        
        # Store comment ID with rectangle for click detection
        rect.comment_id = comment['id']
        state.ax_comment_list.add_patch(rect)
        
        # Convert indices to time format if possible
        if hasattr(state, 'time_labels_all') and state.time_labels_all:
            start_time = state.time_labels_all[comment['start_idx']][:5] if comment['start_idx'] < len(state.time_labels_all) else str(comment['start_idx'])
            end_time = state.time_labels_all[comment['end_idx']][:5] if comment['end_idx'] < len(state.time_labels_all) else str(comment['end_idx'])
            time_range = f"{start_time}-{end_time}"
        else:
            time_range = f"{comment['start_idx']}-{comment['end_idx']}"
        
        # Add title text with improved styling - shortened to make room for notes
        text = comment['text'][:20] + '...' if len(comment['text']) > 20 else comment['text']
        
        # Title positioned more centered within the box
        title_y = rect_top - 0.09  # Move title down more for better centering
        comment_text = state.ax_comment_list.text(0.05, title_y, text,
                                                transform=state.ax_comment_list.transAxes,
                                                fontsize=11, weight='bold', 
                                                color='#1E3A8A' if is_selected else 'black',
                                                ha='left', va='center', zorder=3)
        
        # Time range on the same line, further to the right
        time_text = state.ax_comment_list.text(0.90, title_y, f"{time_range}",
                                             transform=state.ax_comment_list.transAxes,
                                             fontsize=9, color='#333333', 
                                             ha='right', va='center', zorder=2)
        
        # Add notes content on the same line as the title
        if comment.get('user_notes'):
            # Limit notes length to fit on one line
            notes_text = comment['user_notes']
            max_length = 30  # Shorter to fit on same line
            if len(notes_text) > max_length:
                notes_text = notes_text[:max_length] + "..."
            
            # Add notes directly after title on the same line
            # Position it to the right of the title but before the time
            title_width = len(text) * 0.01  # Rough estimate of title width
            notes_x = 0.05 + title_width + 0.08  # Position after title with some spacing
            
            state.ax_comment_list.text(notes_x, title_y, f"- {notes_text}",
                                    transform=state.ax_comment_list.transAxes,
                                    fontsize=9, color='#444444', 
                                    ha='left', va='center', zorder=2)
        
        # Store text references
        state.comment_texts.append(comment_text)
    
    # Show scroll position indicator using the count of sorted comments
    if len(sorted_comments) > state.visible_comments:
        position_text = f"[{start_idx+1}-{end_idx} of {len(sorted_comments)}]"
        state.ax_comment_list.text(0.98, 0.02, position_text, 
                                transform=state.ax_comment_list.transAxes,
                                fontsize=8, ha='right', va='bottom', color='gray')
    
    # Add click handler if not already connected
    if not hasattr(state, 'comment_list_pick_connected') or not state.comment_list_pick_connected:
        state.fig.canvas.mpl_connect('pick_event', on_comment_list_pick)
        state.comment_list_pick_connected = True
    
    plt.draw()

def on_comment_list_pick(event):
    """Handle click on a comment in the comment list"""
    if (hasattr(event.artist, 'comment_id') and 
        hasattr(state, 'ax_comment_list') and 
        event.artist in state.ax_comment_list.patches):
        
        # Get the clicked comment ID
        clicked_comment_id = event.artist.comment_id
        
        # Find the comment object
        selected_comment = None
        for comment in state.comments:
            if comment['id'] == clicked_comment_id:
                selected_comment = comment
                break
                
        if selected_comment:
            # Update selection state
            state.selected_comment_id = clicked_comment_id
            
            # Center view on this comment
            center_on_comment(selected_comment)
            
            # Update UI
            update_comment_list_display()
            display_selected_comment()
            update_comment_markers()
            
            # Update delete button state
            try:
                from ui_state_updates import update_delete_button_state
                update_delete_button_state(state)
            except ImportError:
                pass  # Module not available
                
            # Directly update the Add Comment button text if available
            if hasattr(state, 'update_add_comment_button_text'):
                state.update_add_comment_button_text()
            
            add_log_entry(f"Selected comment {clicked_comment_id} and centered view")
        else:
            add_log_entry(f"Comment {clicked_comment_id} not found")

def scroll_comments_up(event):
    """Scroll the comment list up"""
    state.comment_list_position = max(0, state.comment_list_position - 1)
    update_comment_list_display()

def scroll_comments_down(event):
    """Scroll the comment list down"""
    # Calculate max position using the sorted comments count
    sorted_comments = sorted(state.comments, key=lambda c: c['start_idx'])
    max_position = max(0, len(sorted_comments) - state.visible_comments)
    state.comment_list_position = min(max_position, state.comment_list_position + 1)
    update_comment_list_display()
    
def center_on_comment(comment):
    """Center the main view on the selected comment"""
    if not comment or not hasattr(state, 'ax_spec'):
        return
        
    try:
        # Calculate the center point of the comment
        start_idx = comment['start_idx']
        end_idx = comment['end_idx']
        center_idx = (start_idx + end_idx) // 2
        
        # Get current zoom width
        current_width = state.time_zoom_end - state.time_zoom_start
        
        # Calculate new zoom range centered on the comment
        # Make sure the range is at least 20% wider than the comment itself
        comment_width = end_idx - start_idx
        zoom_width = max(current_width, int(comment_width * 1.4))
        
        # Calculate half of the zoom width
        half_width = zoom_width // 2
        
        # Calculate new start and end, ensuring they're within data bounds
        new_start = max(0, center_idx - half_width)
        new_end = min(len(state.data_global) - 1, center_idx + half_width)
        
        # Adjust if we hit the boundaries to maintain the exact width
        if new_start == 0:
            new_end = min(len(state.data_global) - 1, new_start + zoom_width)
        elif new_end == len(state.data_global) - 1:
            new_start = max(0, new_end - zoom_width)
        
        # Update the zoom to center on the comment
        from visualization import update_time_zoom
        update_time_zoom((new_start, new_end))
        
        # Log the operation
        add_log_entry(f"Centered view on comment at position {center_idx} (range: {new_start}-{new_end})")
        
    except Exception as e:
        add_log_entry(f"Error centering on comment: {str(e)}")
        import traceback
        add_log_entry(f"Traceback: {traceback.format_exc()}")