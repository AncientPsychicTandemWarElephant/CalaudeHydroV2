# ClaudeHydro - Hydrophone Data Visualization Program

A Python-based visualization tool for hydrophone data, with FFT analysis and audio playback capabilities.

## Features

- Spectrogram visualization of hydrophone data
- FFT frequency analysis with adjustable Y-axis range
- Audio playback with waveform visualization
- Time-synchronized navigation with zoom controls
- Volume control and VU meter display
- Timestamp and timezone support
- Project saving and loading

## Recent Improvements

- Enhanced FFT Y-axis controls with +Max, -Max, +Min, -Min, and Auto Y buttons
- Fixed audio playback with improved UI feedback
- Enhanced waveform visualization for better display of low-amplitude signals
- Robust tracking of playback position on spectrograms
- Improved error handling and state management

## Usage

1. Use right-click to select time ranges on the spectrogram
2. Use the Play Audio button to play the selected range
3. Use the FFT Y-axis controls to adjust visualization
4. Navigate with zoom controls and pan buttons
5. Save your work using the Project menu

## Requirements

- Python 3.8+
- NumPy
- Matplotlib
- Sounddevice
- PyTZ
- tkinter

## License

This project is licensed under the MIT License - see the LICENSE file for details.