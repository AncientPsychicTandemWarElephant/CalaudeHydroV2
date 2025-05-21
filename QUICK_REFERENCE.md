# Hydrophone Analyzer - Quick Reference Guide

## Getting Started
1. **Launch:** `python main.py`
2. **Load Files:** Click "Open Files" or select files at startup
3. **Navigate:** Use navigation panel or zoom/pan controls
4. **Analyze:** Adjust gain controls for optimal viewing

## Essential Controls

### File Operations
- **Open Files:** Load hydrophone data files
- **Save Project:** Save current analysis session  
- **Load Project:** Restore previous session
- **Export:** Export processed data

### Navigation
- **Zoom In/Out:** Magnify or reduce view
- **Pan Left/Right:** Move horizontally through data
- **Reset Zoom:** Return to full dataset view
- **Navigation Panel:** Click to jump to any location

### Display Controls
- **Gain Slider:** Adjust color intensity mapping
- **Auto G:** Automatically optimize display
- **+Max/-Max:** Fine-tune maximum display level
- **+Min/-Min:** Fine-tune minimum display level

### Comments & Annotations
- **Add Comment:** Create new annotation
- **Edit Comment:** Modify selected comment
- **Delete Comment:** Remove selected comment
- **Comment List:** View and navigate all comments

## Keyboard Shortcuts

| Key | Action | Key | Action |
|-----|--------|-----|--------|
| `A` | Pan left | `D` | Pan right |
| `W` | Zoom in | `S` | Zoom out |
| `R` | Reset zoom | `Space` | Play/pause audio |
| `C` | Add comment | `E` | Edit comment |
| `+` | Increase gain | `-` | Decrease gain |

## Interface Layout

```
┌─────────────────────────────────────────────────────────┐
│ [File Controls]                            [Timezone]   │
├─────────────────────────────────────────────────────────┤
│ [FFT Display]                              [Navigation] │
├─────────────────────────────────────────────────────────┤
│ [Navigation Overview]                      [File List]  │
├─────────────────────────────────────────────────────────┤
│ [Main Spectrogram]                         [Audio]      │
├─────────────────────────────────────────────────────────┤
│ [Comment Timeline]                         [FFT Ctrls]  │
├─────────────────────────────────────────────────────────┤
│ [Audio Timeline]                                        │
├─────────────────────────────────────────────────────────┤
│ [Comments] [Comment List]                     [Log]     │
└─────────────────────────────────────────────────────────┘
[Gain Controls]
```

## Common Tasks

### Basic Analysis
1. Load data files
2. Adjust gain for optimal viewing
3. Navigate to areas of interest
4. Use FFT display for detailed analysis

### Adding Comments
1. Navigate to time of interest
2. Click "Add Comment"
3. Enter title (24 chars max)
4. Add detailed notes if needed
5. Click "Add" to save

### Exporting Data
1. Click "Export" button
2. Choose output directory
3. Configure export options
4. Click "Export" to process

### Audio Playback
1. Click "Load Audio" to select audio files
2. Use "Play Audio" to start playback
3. Adjust volume as needed
4. Audio syncs with spectrogram view

## Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| Blank/dark display | Click "Auto G" button |
| Can't see details | Use "Zoom In" button |
| Lost in data | Click "Reset Zoom" |
| No audio | Check "Load Audio" and file format |
| Comments not visible | Click "Show Comments" |
| Wrong timezone | Use Timezone buttons (upper right) |

## File Formats
- **Data Files:** .txt files with time/frequency/amplitude data
- **Project Files:** .hap files (save/load sessions)
- **Comment Files:** .comments.json (exported with data)
- **Audio Files:** .wav files (for playback)

## Tips & Best Practices
- **Start with Auto Gain** for initial setup
- **Use comments liberally** to mark interesting events
- **Save projects frequently** to preserve analysis
- **Export data with comments** for sharing
- **Check timezone settings** before analysis
- **Use navigation overview** for quick positioning

## System Requirements
- **Python:** 3.8 or higher
- **RAM:** 4GB minimum, 8GB+ recommended
- **Storage:** 500MB + data file space
- **Display:** 1920x1080 minimum resolution

## Getting Help
- Check **error_log.txt** in application directory
- Refer to full **USER_MANUAL.md** for detailed instructions
- Note system specs and error messages when reporting issues

---
*Quick Reference Guide - Hydrophone Analyzer v2.3.4*