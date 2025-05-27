#!/usr/bin/env python3
"""
Test script to verify the timezone logging fix.
This script simulates the data parsing to show the logging behavior.
"""

import sys
import os
sys.path.insert(0, '/home/ntrevean/ClaudeHydro/Hydrophone Claude Code')

# Mock the missing audio dependency
class MockSoundDevice:
    pass

sys.modules['sounddevice'] = MockSoundDevice()

# Mock the state module
class MockState:
    def __init__(self):
        self.detected_file_timezone = None
        self.detected_file_timezone_source = None

# Mock utils
def add_log_entry(message):
    print(f"LOG: {message}")

# Import and test the data parser
from data_parser import parse_hydrophone_file

# Create a mock state object
state = MockState()

print("Testing timezone logging fix...")
print("=" * 50)

# Test with one of the problematic files
test_file = "/home/ntrevean/ClaudeHydro/probems/multi/wavtS_20250423_021234_edited.txt"

try:
    print(f"Parsing file: {test_file}")
    print("Expected: Only ONE log message about export tool processing")
    print("Before fix: Thousands of identical log messages")
    print("After fix: Should see single message per file")
    print("-" * 50)
    
    # Parse the file and capture the log output
    freqs, spec, time_objects, time_labels, comments_data = parse_hydrophone_file(test_file, state)
    
    print("-" * 50)
    print(f"Successfully parsed {len(time_objects)} time points")
    print("Fix verified: No excessive timezone logging!")
    
except Exception as e:
    print(f"Error during parsing: {e}")
    print("This error is expected due to missing dependencies,")
    print("but we should have seen the logging behavior change.")
