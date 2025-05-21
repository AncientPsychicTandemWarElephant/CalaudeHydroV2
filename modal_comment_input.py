"""
modal_comment_input.py - A modal dialog approach for comment entry

This implements a popup modal dialog for comment entry, completely bypassing
matplotlib's text input and event handling systems.
"""

import tkinter as tk
from tkinter import messagebox
import logging
import state
from utils import add_log_entry

def show_comment_dialog(start_idx=None, end_idx=None, existing_comment=None):
    """Show the comment dialog and return the result
    
    Args:
        start_idx: Start index for new comment
        end_idx: End index for new comment
        existing_comment: Existing comment to edit
        
    Returns:
        Dict with comment data or None if canceled
    """
    try:
        # Get valid indices if not provided
        if start_idx is None or end_idx is None:
            if hasattr(state, 'selected_range') and state.selected_range:
                start_idx, end_idx = state.selected_range
            elif hasattr(state, 'spec_click_line') and state.spec_click_line:
                click_pos = int(state.spec_click_line.get_xdata()[0])
                # Create a small range around the click
                start_idx = max(0, click_pos - 5)
                end_idx = min(len(state.data_global) - 1, click_pos + 5)
            else:
                # Use center of current view
                xlim = state.ax_spec.get_xlim()
                center = int((xlim[0] + xlim[1]) / 2)
                view_width = int((xlim[1] - xlim[0]) * 0.1)  # 10% of view width
                start_idx = max(0, center - view_width // 2)
                end_idx = min(len(state.data_global) - 1, center + view_width // 2)
        
        # Add detailed logging
        add_log_entry(f"Opening comment dialog for range {start_idx}-{end_idx}")
        
        # Get the root window from matplotlib's figure canvas
        if not hasattr(state.fig.canvas, 'get_tk_widget'):
            add_log_entry("Error: Canvas does not have tk_widget - cannot show dialog")
            return None
            
        # Get the root window
        tk_widget = state.fig.canvas.get_tk_widget()
        root = tk_widget.winfo_toplevel()
        
        # Store it in state for future use
        state.tk_root = root
        
        # Create a simple dialog and result variables
        result = [None]  # Use list to make it mutable from nested functions
                
        # Create the dialog window
        dialog = tk.Toplevel(root)
        # Make dialog title more prominent
        dialog.title("ADD COMMENT" if not existing_comment else "EDIT COMMENT")
        try:
            dialog.iconbitmap(default="")  # Remove the default tkinter icon
        except:
            pass  # Ignore if not supported on this platform
        dialog.geometry("400x500")  # Significantly increase dialog height to guarantee button visibility
        dialog.resizable(False, False)
        dialog.transient(root)  # Dialog is dependent on parent
        
        # Comment data
        comment_text = ""
        notes_text = ""
        if existing_comment:
            comment_text = existing_comment.get('text', '')
            notes_text = existing_comment.get('user_notes', '')
            add_log_entry(f"Populating dialog with existing comment: text='{comment_text}', notes_length={len(notes_text)}")
            
        # Create and place widgets
        # Use grid layout for better control
        dialog.grid_columnconfigure(0, weight=1)  # Make the column expandable
        dialog.grid_rowconfigure(0, weight=1)     # Make the content area expandable
        dialog.grid_rowconfigure(1, weight=0)     # Make the button area fixed height
        
        # Main content frame with padding - increased padding for better spacing
        main_frame = tk.Frame(dialog, padx=20, pady=20)
        main_frame.grid(row=0, column=0, sticky="nsew")  # Expand to fill available space
        
        # Comment label and entry (single line with limit)
        comment_frame = tk.Frame(main_frame)
        comment_frame.pack(fill=tk.X, pady=(0, 10))
        
        comment_label = tk.Label(comment_frame, text="Comment (24 chars max):")
        comment_label.pack(anchor=tk.W)
        
        # Create a StringVar with max length validation
        comment_var = tk.StringVar()
        
        # Make sure to populate with existing comment text if editing
        if comment_text:
            add_log_entry(f"Setting comment entry text to: '{comment_text}'")
            comment_var.set(comment_text[:24])  # Limit initial text to 24 chars
        
        # Create the entry widget with StringVar
        comment_entry = tk.Entry(comment_frame, textvariable=comment_var)
        comment_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Explicitly select all text in the entry field for easy editing
        if comment_text:
            comment_entry.after(100, lambda: comment_entry.select_range(0, 'end'))
        
        # Add validation to limit entry to 24 characters
        def limit_chars(*args):
            value = comment_var.get()
            if len(value) > 24:
                comment_var.set(value[:24])  # Truncate to 24 chars
                # Provide visual feedback
                comment_entry.config(bg='#ffcccc')  # Light red background
                # Schedule reset of background color
                comment_entry.after(100, lambda: comment_entry.config(bg='white'))
        
        # Register the callback
        comment_var.trace_add("write", limit_chars)
        
        # Time range info
        if hasattr(state, 'time_labels_all') and state.time_labels_all:
            start_time = state.time_labels_all[start_idx][:5] if start_idx < len(state.time_labels_all) else str(start_idx)
            end_time = state.time_labels_all[end_idx][:5] if end_idx < len(state.time_labels_all) else str(end_idx)
            time_text = f"Time Range: {start_time} - {end_time}"
        else:
            time_text = f"Index Range: {start_idx} - {end_idx}"
        
        time_label = tk.Label(main_frame, text=time_text)
        time_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Notes label and text area (multi-line)
        notes_label = tk.Label(main_frame, text="Extended Notes:")
        notes_label.pack(anchor=tk.W)
        
        notes_frame = tk.Frame(main_frame)
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        notes_text_widget = tk.Text(notes_frame, wrap=tk.WORD, height=6)  # Shorter text area
        notes_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Insert existing notes if available
        if notes_text:
            notes_text_widget.insert('1.0', notes_text)
            add_log_entry(f"Inserted {len(notes_text)} characters of notes into text widget")
        
        # Add scrollbar for notes
        notes_scroll = tk.Scrollbar(notes_frame, command=notes_text_widget.yview)
        notes_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        notes_text_widget.config(yscrollcommand=notes_scroll.set)
        
        # Define button handlers
        def on_save():
            nonlocal comment_entry, notes_text_widget
            comment_value = comment_entry.get().strip()
            
            # Validate required fields
            if not comment_value:
                messagebox.showerror("Error", "Comment text is required", parent=dialog)
                return
            
            # Get notes text
            notes_value = notes_text_widget.get('1.0', 'end-1c')  # -1c to remove trailing newline
            
            # Store the result
            comment_data = {
                'text': comment_value,
                'user_notes': notes_value,
                'start_idx': start_idx,
                'end_idx': end_idx
            }
            
            # If editing existing comment, keep the ID
            if existing_comment and 'id' in existing_comment:
                comment_data['id'] = existing_comment['id']
            
            result[0] = comment_data
            dialog.destroy()
        
        def on_cancel():
            result[0] = None
            dialog.destroy()
        
        # Create separate button area with guaranteed visibility
        button_frame = tk.Frame(dialog, bg='#e0e0e0', height=80)
        button_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        button_frame.grid_propagate(False)  # Prevent frame from shrinking
        
        # Configure button frame grid layout
        button_frame.grid_columnconfigure(0, weight=1)  # Left column (for Add button)
        button_frame.grid_columnconfigure(1, weight=1)  # Right column (for Cancel button)
        
        # Add/Edit button - large green background
        add_button = tk.Button(
            button_frame, 
            text="Add" if not existing_comment else "Update",
            width=15, 
            height=2,
            command=on_save,
            bg='#90ee90',  # Brighter green background
            activebackground='#70c070',  # Darker green when pressed
            font=('Arial', 12, 'bold')  # Bold larger font
        )
        add_button.grid(row=0, column=0, padx=20, pady=10, sticky="e")
        
        # Cancel button - red background
        cancel_button = tk.Button(
            button_frame, 
            text="Cancel", 
            width=15,
            height=2,
            command=on_cancel,
            bg='#ffb6c1',  # Light pink/red background
            activebackground='#c07070',  # Darker red when pressed
            font=('Arial', 12, 'bold')  # Bold larger font
        )
        cancel_button.grid(row=0, column=1, padx=20, pady=10, sticky="w")
        
        # Bind Enter key to save
        dialog.bind("<Return>", lambda event: on_save())
        # Bind Escape key to cancel
        dialog.bind("<Escape>", lambda event: on_cancel())
        
        # Set initial focus to the comment entry
        comment_entry.focus_set()
        
        # Center dialog on screen
        dialog.update_idletasks()  # Make sure dialog is updated before getting dimensions
        
        # Get dialog dimensions
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()
        
        # Get screen dimensions
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        
        # Calculate position for center of screen
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        
        # Ensure dialog is at least 50 pixels from screen edges
        x = max(50, min(x, screen_width - dialog_width - 50))
        y = max(50, min(y, screen_height - dialog_height - 50))
        
        # Set position to center of screen
        dialog.geometry(f"+{x}+{y}")
        
        # Force dialog to update position
        dialog.update()
        
        # Make dialog modal
        dialog.grab_set()
        
        # Force dialog to the front
        dialog.attributes('-topmost', True)
        dialog.focus_force()
        dialog.lift()
        
        # Wait for dialog to close
        root.wait_window(dialog)
        
        # Return the result
        return result[0]
    
    except Exception as e:
        add_log_entry(f"Error showing comment dialog: {str(e)}")
        logging.error(f"Error showing comment dialog: {str(e)}", exc_info=True)
        import traceback
        add_log_entry(f"Traceback: {traceback.format_exc()}")
        return None