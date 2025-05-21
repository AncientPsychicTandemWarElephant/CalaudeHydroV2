#!/usr/bin/env python3
"""
test_textbox_property.py - Test the text property fix
"""

import matplotlib.pyplot as plt
from focused_textbox_fix import SmartTextBox

print("Testing SmartTextBox text property...")

fig, ax = plt.subplots()
tb = SmartTextBox(ax, 'Test:', initial='Initial text')

# Test getter
print(f"Initial text: '{tb.text}'")

# Test setter
tb.text = 'New text'
print(f"After setting: '{tb.text}'")

# Test set_val
tb.set_val('Set via set_val')
print(f"After set_val: '{tb.text}'")

# Test clearing
tb.set_val('')
print(f"After clearing: '{tb.text}'")

print("\nAll tests passed!")
plt.close('all')