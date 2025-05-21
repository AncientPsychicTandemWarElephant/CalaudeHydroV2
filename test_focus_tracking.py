#!/usr/bin/env python3
"""
test_focus_tracking.py - Test keyboard shortcut disabling while typing
"""

import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button
import state

# Initialize minimal state
state.comment_input = None
state.notes_input = None

# Track key events
key_events = []

def on_key_press(event):
    """Test keyboard handler"""
    # Apply our focus checking logic
    if hasattr(state, 'comment_input') and hasattr(state.comment_input, 'active') and state.comment_input.active:
        status = "BLOCKED (comment active)"
    elif hasattr(state, 'notes_input') and hasattr(state.notes_input, 'active') and state.notes_input.active:
        status = "BLOCKED (notes active)"
    else:
        status = "PROCESSED"
    
    key_events.append(f"Key '{event.key}': {status}")
    update_display()

def update_display():
    """Update the event display"""
    if key_events:
        display_text = '\n'.join(key_events[-10:])  # Show last 10 events
    else:
        display_text = "Press keys to test..."
    
    event_display.set_text(display_text)
    fig.canvas.draw_idle()

# Create test interface
fig = plt.figure(figsize=(10, 6))
fig.suptitle('Keyboard Focus Test', fontsize=16)

# Create textboxes
ax_comment = fig.add_axes([0.1, 0.7, 0.8, 0.05])
state.comment_input = TextBox(ax_comment, 'Comment:', initial='Click here and type...')

ax_notes = fig.add_axes([0.1, 0.6, 0.8, 0.05])
state.notes_input = TextBox(ax_notes, 'Notes:', initial='Click here and type...')

# Create event display
ax_display = fig.add_axes([0.1, 0.1, 0.8, 0.4])
ax_display.axis('off')
event_display = ax_display.text(0, 1, 'Press keys to test...', 
                               va='top', fontsize=10, family='monospace')

# Connect key handler
fig.canvas.mpl_connect('key_press_event', on_key_press)

# Instructions
fig.text(0.5, 0.55, 'Instructions:', ha='center', fontsize=12, weight='bold')
fig.text(0.5, 0.52, '1. Click in a textbox and type - keys should be BLOCKED', ha='center', fontsize=10)
fig.text(0.5, 0.49, '2. Click outside textboxes and type - keys should be PROCESSED', ha='center', fontsize=10)
fig.text(0.5, 0.46, '3. Test spacebar and other shortcuts', ha='center', fontsize=10)

# Clear button
ax_clear = fig.add_axes([0.4, 0.02, 0.2, 0.05])
btn_clear = Button(ax_clear, 'Clear Log')
btn_clear.on_clicked(lambda x: (key_events.clear(), update_display()))

plt.show()