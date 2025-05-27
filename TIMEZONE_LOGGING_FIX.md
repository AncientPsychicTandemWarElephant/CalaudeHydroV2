# Timezone Logging Fix

## Problem Description
The Hydrophone Viewer was generating excessive log output when processing export-tool-processed files. The issue was that the log message `"Export tool processed file - timestamps already in {timezone}"` was being printed for every single data row in the file, instead of just once per file.

## Root Cause
The log message was located inside the data processing loop (`for line in lines[start_idx + 1:]:`) in `data_parser.py` on line 171. This caused the message to be logged thousands of times for files with many data points.

## Original Code (Problematic)
```python
for line in lines[start_idx + 1:]:
    # ... data processing code ...
    if export_tool_processed:
        # This was INSIDE the loop - causing excessive logging
        add_log_entry(f"Export tool processed file - timestamps already in {metadata['timezone']}")
        # ... rest of processing ...
```

## Fixed Code
```python
# Log export tool processing status once per file
if export_tool_processed:
    add_log_entry(f"Export tool processed file - timestamps already in {metadata['timezone']}")

for line in lines[start_idx + 1:]:
    # ... data processing code ...
    if export_tool_processed:
        # Log message moved OUTSIDE the loop
        # ... rest of processing ...
```

## Impact
- **Before**: Thousands of identical log messages per file (e.g., one message per data row)
- **After**: One log message per file, regardless of file size
- **Performance**: Significantly reduced log output and improved processing speed
- **Usability**: Much cleaner, readable log output

## Files Modified
- `/home/ntrevean/ClaudeHydro/Hydrophone Claude Code/data_parser.py` (lines 121-123 added, line 171 removed)

## Testing
The fix was applied to the `parse_hydrophone_file` function in `data_parser.py`. When processing multiple export-tool-processed files, users should now see:
- One "Export tool processed file" message per file
- No more repetitive logging spam
- Clean, manageable log output

This fix resolves the issue described where the viewer log output was overwhelming and difficult to read due to excessive repetitive timezone logging.