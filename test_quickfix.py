#!/usr/bin/env python3
"""
test_quickfix.py - Quick test to verify textbox fixes work
"""

import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox

print("Testing TextBox attribute compatibility...")

# Test 1: Check what attributes exist
tb_test = TextBox(plt.figure().add_axes([0.1, 0.1, 0.8, 0.1]), 'Test:')
if hasattr(tb_test, '_keypress'):
    print("✓ TextBox has _keypress attribute")
elif hasattr(tb_test, '_on_keypress'):
    print("✓ TextBox has _on_keypress attribute")
elif hasattr(tb_test, 'on_keypress'):
    print("✓ TextBox has on_keypress attribute (no underscore)")
else:
    print("✗ TextBox has none of the expected keypress attributes")

# Test 2: Try importing our fixes
try:
    from textbox_lag_fix import patch_textbox_globally
    print("✓ textbox_lag_fix imports successfully")
except Exception as e:
    print(f"✗ Error importing textbox_lag_fix: {e}")

try:
    from focused_textbox_fix import SmartTextBox
    print("✓ focused_textbox_fix imports successfully")
except Exception as e:
    print(f"✗ Error importing focused_textbox_fix: {e}")

try:
    from simple_textbox_fix import apply_simple_lag_fix
    print("✓ simple_textbox_fix imports successfully")
except Exception as e:
    print(f"✗ Error importing simple_textbox_fix: {e}")

# Test 3: Try creating optimized textboxes
try:
    smart_tb = SmartTextBox(plt.figure().add_axes([0.1, 0.1, 0.8, 0.1]), 'Smart:')
    print("✓ SmartTextBox created successfully")
except Exception as e:
    print(f"✗ Error creating SmartTextBox: {e}")

print("\nAll tests completed!")
plt.close('all')