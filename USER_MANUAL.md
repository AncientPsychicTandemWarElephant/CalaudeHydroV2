# Hydrophone Analyzer User Manual

## Table of Contents
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
5. [Interface Overview](#interface-overview)
6. [Loading Data Files](#loading-data-files)
7. [Navigation and Visualization](#navigation-and-visualization)
8. [Gain and Display Controls](#gain-and-display-controls)
9. [Comment and Annotation System](#comment-and-annotation-system)
10. [Audio Playback](#audio-playback)
11. [Timezone Management](#timezone-management)
12. [Data Export](#data-export)
13. [Project Management](#project-management)
14. [Troubleshooting](#troubleshooting)
15. [Keyboard Shortcuts](#keyboard-shortcuts)
16. [Technical Support](#technical-support)

---

## Introduction

The Hydrophone Analyzer is a comprehensive software application designed for analyzing and visualizing hydrophone data. It provides advanced tools for examining acoustic recordings from underwater environments, with features for spectral analysis, annotation, and data export.

### Key Features
- Real-time spectrogram visualization with customizable gain controls
- Interactive navigation with zoom and pan capabilities
- Comment and annotation system for marking significant events
- Audio playback synchronization with visual data
- Multi-timezone support for global deployments
- Data export functionality with customizable formats
- Project management with save/load capabilities

### Target Users
This software is designed for:
- Marine biologists studying underwater acoustics
- Environmental researchers monitoring aquatic ecosystems
- Acoustic engineers analyzing hydrophone recordings
- Research institutions processing large datasets

---

## System Requirements

### Minimum Requirements
- **Operating System:** Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python:** Version 3.8 or higher
- **Memory:** 4 GB RAM minimum (8 GB recommended)
- **Storage:** 500 MB for installation plus space for data files
- **Display:** 1920x1080 resolution minimum

### Recommended Specifications
- **Memory:** 16 GB RAM or higher for large datasets
- **Storage:** SSD for improved performance
- **Display:** Dual monitor setup for enhanced workflow
- **Audio:** Sound card with good quality output for audio analysis

---

## Installation

### Step 1: Install Python Dependencies
```bash
# Install required packages
pip install numpy matplotlib pytz scipy tkinter

# Install optional packages for enhanced functionality
pip install tzlocal pillow sounddevice
```

### Step 2: Download the Application
1. Extract the Hydrophone Analyzer files to your desired directory
2. Ensure all Python files are in the same folder
3. Verify that the `main.py` file is present

### Step 3: Test Installation
```bash
# Navigate to the application directory
cd /path/to/hydrophone-analyzer

# Run the application
python main.py
```

### Installation Using Requirements File
If a `requirements.txt` file is provided:
```bash
pip install -r requirements.txt
```

---

## Getting Started

### First Launch
1. **Start the Application**
   - Double-click `main.py` or run `python main.py` from command line
   - The file selection dialog will appear automatically

2. **Select Data Files**
   - Browse to your hydrophone data files (.txt format)
   - Select one or multiple files for analysis
   - Files will be loaded and processed automatically

3. **Initial View**
   - The application will display your data with default zoom settings
   - All interface elements will be initialized and ready for use

### Basic Navigation
- Use the **Navigation View** (small panel above main spectrogram) to see the full dataset
- Click and drag in the navigation view to move around your data
- Use **Zoom In/Out** buttons for detailed analysis
- **Pan Left/Right** buttons for precise positioning

---

## Interface Overview

### Main Display Areas

#### 1. FFT Slice Display (Top)
- Shows frequency content at a specific time point
- Updates dynamically as you navigate through the data
- Y-axis shows amplitude, X-axis shows frequency in kHz
- Used for detailed spectral analysis

#### 2. Navigation Spectrogram (Upper Middle)
- Provides overview of entire dataset
- Red box shows current view area
- Click anywhere to jump to that location
- Drag the red box to navigate smoothly

#### 3. Main Spectrogram (Center)
- Primary visualization area for detailed analysis
- Color intensity represents signal strength
- Time on X-axis, Frequency on Y-axis
- Supports zoom, pan, and selection operations

#### 4. Comment Timeline (Below Main Spectrogram)
- Shows comment markers along the timeline
- Click comments to select and view details
- Different colors indicate selected vs. unselected comments

#### 5. Audio Timeline (Bottom)
- Displays audio segments if audio files are loaded
- Green bars indicate available audio sections
- Synchronized with main spectrogram view

### Control Panels

#### File Controls (Top Left)
- **Open Files:** Load new hydrophone data files
- **Save Project:** Save current analysis session
- **Load Project:** Restore previous session
- **Export:** Export data or visualizations

#### Gain Controls (Left Side)
- **Gain Slider:** Vertical slider for overall gain adjustment
- **+Max/-Max:** Fine-tune maximum display level
- **+Min/-Min:** Fine-tune minimum display level
- **Auto G:** Automatically optimize gain settings

#### Navigation Controls (Right Side)
- **Zoom In/Out:** Change magnification level
- **Pan Left/Right:** Move view horizontally
- **Reset Zoom:** Return to full dataset view

#### FFT Controls (Left Side)
- **FFT Y Controls:** Manage FFT display range
- **Auto Y:** Automatically set optimal Y-axis range
- **Manual adjustment buttons:** Fine-tune FFT display

---

## Loading Data Files

### Supported File Formats
The application supports text files (.txt) with the following structure:

```
File Details:
Device: [Device Information]
Project: [Project Name]
Start time: [Start Time]
Setup:
Sample rate: [Sample Rate]
...

[Time] [Frequency1] [Frequency2] ... [FrequencyN] [Comment]
```

### Loading Process
1. **Single File Loading**
   - Use "Open Files" button or start application without arguments
   - Select desired .txt file from dialog
   - File will be processed and displayed automatically

2. **Multiple File Loading**
   - Select multiple files in the file dialog
   - Files will be concatenated in chronological order
   - Gaps between files are automatically detected and marked

3. **Command Line Loading**
   ```bash
   python main.py /path/to/data1.txt /path/to/data2.txt
   ```

### File List Panel
- Located on the right side of the interface
- Shows all loaded files with scroll capability
- Click files to highlight corresponding data sections
- **Clear Highlight** button removes file highlighting

---

## Navigation and Visualization

### Zoom Operations
- **Zoom In Button:** Increases magnification by 50%
- **Zoom Out Button:** Decreases magnification by 50%
- **Reset Zoom:** Returns to view of entire dataset
- **Mouse Wheel:** Zoom in/out at cursor position (if supported)

### Pan Operations
- **Pan Left/Right:** Move view by 10% of current span
- **Navigation Click:** Click in navigation panel to jump to location
- **Drag Navigation Box:** Smooth navigation by dragging red box

### Selection Operations
- **Click Spectrogram:** Place selection line for FFT analysis
- **Drag Selection:** Create range selection for analysis
- **Range Analysis:** FFT display updates to show selected range

### Time Display
- Time labels automatically adjust to current timezone setting
- Supports multiple display formats (HH:MM, full timestamps)
- Navigation shows time ranges and zoom percentages

---

## Gain and Display Controls

### Understanding Gain Controls
Gain controls adjust the color mapping of the spectrogram to highlight different signal levels.

#### Main Gain Slider
- **Position:** Left side of interface, vertical orientation
- **Function:** Sets minimum and maximum display levels
- **Usage:** Drag handles to adjust range
- **Real-time:** Updates display immediately

#### Fine Adjustment Buttons
- **+Max:** Increase maximum level by 0.1 units
- **-Max:** Decrease maximum level by 0.1 units
- **+Min:** Increase minimum level by 0.1 units
- **-Min:** Decrease minimum level by 0.1 units

#### Auto Gain
- **Button:** "Auto G" button below gain controls
- **Function:** Automatically calculates optimal gain settings
- **Usage:** Click when spectrogram appears too dark or washed out

### Best Practices
1. **Start with Auto Gain** for initial optimal settings
2. **Fine-tune manually** for specific analysis needs
3. **Higher contrast** (wider range) for overview analysis
4. **Lower contrast** (narrower range) for detailed examination

---

## Comment and Annotation System

### Overview
The comment system allows you to annotate significant events, behaviors, or observations in your hydrophone data.

### Adding Comments

#### Method 1: Add Comment Button
1. Navigate to the time range of interest
2. Click **"Add Comment"** button (bottom left)
3. Modal dialog will appear with:
   - **Comment field:** Brief title (24 characters max)
   - **Time range:** Automatically set based on current view
   - **Extended notes:** Detailed observations
4. Click **"Add"** to save or **"Cancel"** to abort

#### Method 2: Selection-Based Comments
1. Click and drag on the spectrogram to select a range
2. Click **"Add Comment"** button
3. Time range will be pre-filled with your selection

### Managing Comments

#### Comment List Panel
- Located at bottom-left of interface
- Shows all comments chronologically
- **Scroll buttons** (▲▼) to navigate through comments
- **Click comment** to select and center view

#### Editing Comments
1. Select a comment from the list or timeline
2. **"Add Comment"** button changes to **"Edit Comment"**
3. Click button to open edit dialog
4. Modify text or notes as needed
5. Click **"Update"** to save changes

#### Deleting Comments
1. Select comment to delete
2. Click **"Delete Comment"** button
3. Confirm deletion in dialog box
4. Comment is permanently removed

### Comment Display

#### Timeline View
- Comments appear as colored bars on the comment timeline
- **Selected comments:** Gold/yellow highlighting
- **Unselected comments:** Blue coloring
- **Click comments** in timeline to select

#### Comment Details
- **Title:** Brief descriptive text
- **Time Range:** Start and end times
- **Extended Notes:** Detailed observations
- **Duration:** Automatically calculated

### Comment Export/Import
Comments are automatically saved with exported data and can be shared between users.

---

## Audio Playback

### Loading Audio Files
1. Click **"Load Audio"** button in audio controls section
2. Select corresponding .wav files for your hydrophone data
3. Audio will be synchronized with spectrogram timeline

### Playback Controls
- **Play Audio:** Start/stop audio playback
- **Volume Slider:** Adjust playback volume (0-300%)
- **Time Display:** Shows current playback position

### Audio Visualization
- **Waveform Display:** Real-time audio waveform
- **Timeline Markers:** Green bars show available audio sections
- **Synchronization:** Audio position matches spectrogram view

### Audio Features
- **Synchronized Playback:** Audio follows spectrogram navigation
- **Variable Speed:** Adjust playback rate if needed
- **Quality Output:** High-fidelity audio reproduction

---

## Timezone Management

### Timezone Options
The application supports three timezone modes:

#### 1. File Timezone
- Uses timezone detected from data file headers
- Automatic detection from metadata
- Default fallback: UTC

#### 2. Local Timezone  
- Uses your computer's system timezone
- Automatically detected
- Updates time displays accordingly

#### 3. User-Selected Timezone
- Choose any timezone manually
- Useful for data collected in different regions
- Persistent across sessions

### Changing Timezone
1. Locate **Timezone Settings** panel (upper right)
2. Click appropriate button:
   - **File TZ:** Use file's original timezone
   - **Local TZ:** Use system timezone
   - **User TZ:** Select custom timezone
3. Time displays update immediately throughout interface

### Timezone Effects
- **Time Labels:** All time displays update
- **Export Data:** Timestamps adjusted to selected timezone
- **Comments:** Time ranges reflect timezone choice
- **Navigation:** Timeline scales appropriately

---

## Data Export

### Export Types
The application supports multiple export formats for different needs.

#### 1. Data Export
- **Format:** Text files compatible with original format
- **Content:** Processed hydrophone data with timestamps
- **Timezone:** Adjusted to current timezone setting
- **Comments:** Included in separate .comments.json file

#### 2. Project Export  
- **Content:** Complete analysis session
- **Includes:** Data, comments, view settings, zoom levels
- **Format:** Multiple files for complete restoration

### Export Process
1. Click **"Export"** button in file controls
2. **Export dialog** appears with options:
   - **Output directory:** Choose destination folder
   - **Filename prefix:** Custom prefix for exported files
   - **File splitting:** Options for large datasets
   - **Metadata inclusion:** Include/exclude metadata
3. **Configure settings** as needed
4. Click **"Export"** to begin process
5. **Progress indicator** shows export status

### Export Options

#### File Splitting
- **Single File:** All data in one file
- **By Hour:** Split into hourly files
- **By Day:** Split into daily files
- **By Size:** Limit file sizes
- **Original Boundaries:** Match original file structure

#### Advanced Options
- **Compression:** Reduce file sizes
- **Metadata:** Include device and setup information
- **Comments:** Export annotations separately
- **Time Format:** Choose timestamp format

---

## Project Management

### Saving Projects
1. Click **"Save Project"** button
2. Choose filename and location
3. Project file (.hap) contains:
   - File references and paths
   - Current view settings
   - Zoom levels and navigation state
   - All comments and annotations
   - Timezone and display preferences

### Loading Projects
1. Click **"Load Project"** button
2. Select previously saved .hap file
3. Application restores:
   - Original data files
   - View settings and zoom levels
   - All comments and annotations
   - User preferences

### Project Contents
- **Data References:** Paths to original files
- **Analysis State:** Current zoom and navigation
- **Annotations:** All comments and notes
- **Settings:** Display preferences and configurations
- **Metadata:** Project information and timestamps

---

## Troubleshooting

### Common Issues

#### Application Won't Start
**Symptoms:** Error messages on startup, missing dependencies
**Solutions:**
1. Verify Python installation (3.8+)
2. Install required packages: `pip install numpy matplotlib pytz`
3. Check file permissions
4. Run from command line to see error messages

#### Files Won't Load
**Symptoms:** "Failed to parse file" errors
**Solutions:**
1. Verify file format matches expected structure
2. Check file permissions and accessibility
3. Ensure files aren't corrupted or truncated
4. Try loading files one at a time

#### Display Issues
**Symptoms:** Blank screens, incorrect colors, layout problems
**Solutions:**
1. Try **Auto Gain** button to fix display
2. Reset zoom to full view
3. Restart application
4. Check display drivers and resolution

#### Performance Issues
**Symptoms:** Slow response, memory errors, crashes
**Solutions:**
1. Close other applications to free memory
2. Load smaller datasets or file subsets
3. Reduce zoom levels for better performance
4. Consider system memory upgrade

#### Audio Problems
**Symptoms:** No audio playback, synchronization issues
**Solutions:**
1. Verify audio files are in correct format
2. Check system audio settings
3. Ensure audio files correspond to data files
4. Try different audio output devices

### Error Messages

#### "Cannot initialize display backend"
- **Cause:** Graphics system issues
- **Solution:** Install/update graphics drivers, check display settings

#### "Memory allocation failed"
- **Cause:** Insufficient RAM for large datasets
- **Solution:** Close other applications, load smaller files, add more RAM

#### "File format not recognized"
- **Cause:** Incompatible file format
- **Solution:** Verify file structure, check file extension, ensure proper format

### Getting Help
1. **Check Log Files:** Look for error_log.txt in application directory
2. **System Information:** Note OS version, Python version, available memory
3. **File Information:** Note file sizes, formats, and source systems
4. **Screenshots:** Capture error messages and interface issues

---

## Keyboard Shortcuts

### Navigation
| Key | Action |
|-----|--------|
| `A` | Pan left |
| `D` | Pan right |
| `W` | Zoom in |
| `S` | Zoom out |
| `R` | Reset zoom |
| `Space` | Toggle audio playback |

### View Controls
| Key | Action |
|-----|--------|
| `+` | Increase gain |
| `-` | Decrease gain |
| `0` | Auto gain |
| `F` | Full screen toggle |

### Comments
| Key | Action |
|-----|--------|
| `C` | Add comment |
| `E` | Edit selected comment |
| `Delete` | Delete selected comment |
| `Tab` | Next comment |
| `Shift+Tab` | Previous comment |

### File Operations
| Key | Action |
|-----|--------|
| `Ctrl+O` | Open files |
| `Ctrl+S` | Save project |
| `Ctrl+E` | Export data |
| `Ctrl+Q` | Quit application |

---

## Technical Support

### System Information Collection
When reporting issues, please provide:

1. **Software Version:** Check version number in bottom-right corner
2. **Operating System:** Windows/Mac/Linux version
3. **Python Version:** Run `python --version`
4. **Available Memory:** System RAM and usage
5. **File Information:** Size, format, source of data files
6. **Error Messages:** Complete text of any error messages
7. **Screenshots:** Visual representation of issues

### Performance Optimization

#### For Large Datasets
- Load files sequentially rather than all at once
- Use file splitting options during export
- Consider system with more RAM
- Close unnecessary applications

#### For Better Responsiveness
- Reduce zoom levels when not needed
- Limit number of comments for very long datasets
- Use SSD storage for data files
- Ensure adequate system cooling

### Best Practices

#### Data Management
- Keep original files as backups
- Use descriptive filenames and project names
- Organize files by date, location, or project
- Regular backups of analysis projects

#### Analysis Workflow
1. **Initial Overview:** Load files and examine full dataset
2. **Gain Adjustment:** Optimize display for your data type
3. **Systematic Review:** Work through data chronologically
4. **Annotation:** Add comments for significant events
5. **Export:** Save analysis and processed data

#### Quality Control
- Verify timezone settings before analysis
- Check comment accuracy and completeness
- Review export settings before final output
- Maintain consistent annotation standards

---

## Appendix

### File Format Specification
Detailed specification of supported file formats and data structures.

### API Reference
Information for developers integrating with the Hydrophone Analyzer.

### Change Log
Version history and feature updates.

### Glossary
Definitions of technical terms and acoustic analysis concepts.

---

*Hydrophone Analyzer User Manual - Version 2.3.4*  
*Document Last Updated: [Current Date]*

For additional support and updates, please refer to the project documentation or contact your system administrator.