"""
comment_file_handler.py - Functions for handling comment export and import to/from files

This module contains functions for:
1. Exporting comments to external .comments.json files
2. Importing comments from external .comments.json files
3. Checking for existing comment files during data import
"""

import os
import json
import logging
from utils import add_log_entry
import state

def export_comments_to_file(data_filepath):
    """Export all comments to a .comments.json file associated with the data file
    
    Args:
        data_filepath: Path to the data file the comments are associated with
        
    Returns:
        bool: True if export was successful, False otherwise
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
    """Import comments from a .comments.json file
    
    Args:
        comment_filepath: Path to the comment file
        merge: If True, merge with existing comments, otherwise replace them
        
    Returns:
        bool: True if import was successful, False otherwise
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
    """Check if a comment file exists for the given data file and import it if found
    
    Args:
        data_filepath: Path to the data file to check for comments
        
    Returns:
        bool: True if comments were found and imported, False otherwise
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