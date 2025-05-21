#!/usr/bin/env python3
"""
test_fixed_textbox.py - Test the fixed SmartTextBox implementation
"""

import matplotlib.pyplot as plt
from focused_textbox_fix import SmartTextBox

print("Testing fixed SmartTextBox...")

fig, ax = plt.subplots()
tb = SmartTextBox(ax, 'Test:', initial='')

# Test typing simulation
test_messages = [
    "Testing typing",
    "Multiple words work",
    "Clear and type again"
]

def test_typing():
    """Simulate typing in the textbox"""
    for msg in test_messages:
        # Clear first
        tb.set_val('')
        print(f"Cleared. Current text: '{tb.text}'")
        
        # Type each character
        current_text = ""
        for char in msg:
            current_text += char
            tb.set_val(current_text)
            print(f"Typed '{char}'. Current text: '{tb.text}'")
        
        print(f"Final text: '{tb.text}'")
        print("-" * 40)

# Create a button to test
ax_test = fig.add_axes([0.7, 0.01, 0.2, 0.05])
from matplotlib.widgets import Button
btn_test = Button(ax_test, 'Test Typing')
btn_test.on_clicked(lambda x: test_typing())

# Instructions
fig.text(0.1, 0.95, 'Type in the textbox or click "Test Typing"', fontsize=12)

plt.show()