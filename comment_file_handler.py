"""
comment_file_handler.py - Comment Export and Import Management

This module manages the persistence of comments to allow sharing annotations
between sessions and users. It provides functionality for:

1. Exporting comments to external .comments.json files
2. Importing comments from .comments.json files
3. Automatic detection and loading of comment files during data import

The comment files use a standard JSON format with version tracking to ensure
future compatibility as the application evolves.
"""

import os
import json
import logging
from utils import add_log_entry
import state

def export_comments_to_file(data_filepath):
    """
    Export comments to a JSON file associated with the source data file
    
    Args:
        data_filepath: Path to the data file the comments are associated with
        
    Returns:
        bool: True if export was successful, False otherwise
        
    This function creates a companion .comments.json file that contains all
    comment data in a structured format. The file is created alongside the
    original data file and can be automatically detected and loaded when
    the data file is opened in a future session.
    """
    try:
        # Check if we have any comments to export
        if not hasattr(state, 'comments') or not state.comments:
            add_log_entry("No comments to export")
            return False
            
        # Generate comment file path by adding .comments.json to the data filepath
        comment_filepath = f"{data_filepath}.comments.json"
        
        # Prepare the comment data structure
        comment_data = {
            "version": "1.0",
            "data_file": os.path.basename(data_filepath),
            "comment_count": len(state.comments),
            "comments": []
        }
        
        # Add all comments to the data structure
        for comment in state.comments:
            # Create a copy to avoid modifying the original
            comment_copy = comment.copy()
            # Convert all numeric ID values to str for JSON compatibility
            comment_copy['id'] = str(comment_copy['id'])
            comment_data["comments"].append(comment_copy)
            
        # Write the comment data to file
        with open(comment_filepath, 'w') as f:
            json.dump(comment_data, f, indent=2)
            
        add_log_entry(f"Exported {len(state.comments)} comments to {comment_filepath}")
        return True
        
    except Exception as e:
        add_log_entry(f"Error exporting comments: {str(e)}")
        logging.error(f"Error exporting comments: {str(e)}", exc_info=True)
        return False

def import_comments_from_file(comment_filepath, merge=True):
    """
    Import comments from a JSON comment file
    
    Args:
        comment_filepath: Path to the comment file
        merge: If True, merge with existing comments, otherwise replace them
        
    Returns:
        bool: True if import was successful, False otherwise
        
    This function loads comments from a .comments.json file, validates the data
    structure, and either adds them to existing comments or replaces all comments.
    It handles ID management, ensuring each comment has a unique identifier, and
    validates comment data fields for consistency.
    """
    try:
        # Check if the file exists
        if not os.path.exists(comment_filepath):
            add_log_entry(f"Comment file not found: {comment_filepath}")
            return False
            
        # Read the comment data from the file
        with open(comment_filepath, 'r') as f:
            comment_data = json.load(f)
            
        # Validate the data
        if not isinstance(comment_data, dict) or 'comments' not in comment_data:
            add_log_entry("Invalid comment file format")
            return False
            
        # Get the comments array
        comments = comment_data.get('comments', [])
        
        # Initialize state.comments if it doesn't exist
        if not hasattr(state, 'comments'):
            state.comments = []
            
        # Initialize state.comment_id_counter if it doesn't exist
        if not hasattr(state, 'comment_id_counter'):
            state.comment_id_counter = 1
            
        # If not merging, clear existing comments
        if not merge:
            state.comments = []
            
        # Add detailed diagnostics about the comments we're importing
        add_log_entry(f"Comment file contains {len(comments)} comments")
        for i, comment in enumerate(comments[:3]):  # Log the first 3 comments for diagnostics
            add_log_entry(f"Comment {i}: text='{comment.get('text', '')}', notes='{comment.get('user_notes', '')[:20]}...'")
        
        # Process all comments
        imported_count = 0
        for comment in comments:
            # Convert ID back to int
            if 'id' in comment:
                try:
                    comment['id'] = int(comment['id'])
                except (ValueError, TypeError):
                    # If conversion fails, assign a new ID
                    comment['id'] = state.comment_id_counter
                    state.comment_id_counter += 1
            else:
                # If no ID present, assign a new ID
                comment['id'] = state.comment_id_counter
                state.comment_id_counter += 1
            
            # Make sure all required fields are present
            if 'text' not in comment:
                comment['text'] = f"Comment {comment['id']}"
            if 'user_notes' not in comment:
                comment['user_notes'] = ""
            if 'start_idx' not in comment or 'end_idx' not in comment:
                # Skip invalid comments
                add_log_entry(f"Skipping invalid comment without position: {comment}")
                continue
                
            # Add the comment to state.comments
            state.comments.append(comment)
            imported_count += 1
            
            # Update comment_id_counter to be greater than the highest used ID
            state.comment_id_counter = max(state.comment_id_counter, comment['id'] + 1)
            
        add_log_entry(f"Imported {imported_count} comments from {comment_filepath}")
        
        # Display some diagnostic information about the state after import
        add_log_entry(f"After import: state.comments has {len(state.comments)} comments")
        add_log_entry(f"comments_visible={getattr(state, 'comments_visible', False)}")
        return True
        
    except Exception as e:
        add_log_entry(f"Error importing comments: {str(e)}")
        logging.error(f"Error importing comments: {str(e)}", exc_info=True)
        return False

def check_and_import_comment_file(data_filepath):
    """
    Automatically detect and load comment file for a data file
    
    Args:
        data_filepath: Path to the data file to check for comments
        
    Returns:
        bool: True if comments were found and imported, False otherwise
        
    This function is used during file loading to check for and import
    any associated comment files. It attempts to find a .comments.json
    file with the same base name as the data file and imports any
    comments it contains.
    """
    # Generate the expected comment file path
    comment_filepath = f"{data_filepath}.comments.json"
    
    # Check if the file exists
    if os.path.exists(comment_filepath):
        add_log_entry(f"Found comment file for {data_filepath}")
        return import_comments_from_file(comment_filepath)
    else:
        add_log_entry(f"No comment file found for {data_filepath}")
        return False