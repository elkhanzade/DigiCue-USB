# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DigiCue-USB is a Python desktop GUI application that interfaces with the DigiCue Blue pool/billiards training device via a BLED112 Bluetooth USB dongle. The application monitors stroke metrics in real-time and logs shot data for analysis.

## Key Commands

### Running the Application
```bash
# Install dependencies (use virtualenv as recommended in README)
pip install -r requirements.txt

# Run the main application
python Python3/src/main.py

# On Windows, alternatively use:
python Python3/src/run.bat
```

### Testing BLED112 Connectivity
```bash
# Test scripts for BLED112-DigiCue communication
python Python3/src/test_bled112_digicue.py
python Python3/src/ble_listener_rpi.py -o capture.txt  # For Raspberry Pi
python Python3/src/digicue_daemon.py  # Continuous monitoring daemon
```

## Architecture

### Core Components

1. **GUI Layer** (`gui.py`): Tkinter-based interface with tabs for monitoring and configuration
   - Real-time stroke metrics visualization
   - Device configuration interface
   - CSV data logging

2. **Device Communication** (`digicueblue.py`): Handles DigiCue Blue protocol
   - Parses 8 stroke metrics: Jab, Follow Through, Finish, Tip Steer, Straightness, Finesse, Shot Interval, Backstroke Pause
   - Configuration packet encoding/decoding
   - Alert and data packet processing

3. **Bluetooth Layer** (`bgapi.py`, `bglib.py`): Implements Bluegiga BGAPI protocol
   - BLED112 dongle communication via serial port
   - BLE scanning, connection, and data handling
   - Binary protocol implementation for BGAPI commands

4. **Threading Model** (`main.py`): Manages concurrent operations
   - GUI thread (main)
   - Bluetooth communication thread
   - Inter-thread communication via shared `DigicueBlue` object

### Data Flow

1. BLED112 dongle receives BLE packets from DigiCue Blue
2. `bgapi.py` processes BGAPI events and extracts data
3. `digicueblue.py` parses DigiCue-specific protocol
4. GUI updates in real-time and logs to `data.csv`

### Key Protocol Details

- DigiCue Blue advertises with MAC pattern containing "B7:76:8E"
- Uses BLE notifications for real-time stroke data
- Configuration requires double-press of device button
- Data packets contain encoded stroke metrics and timestamps

## Important Files

- `comport.cfg`: Stores selected serial port (auto-created, gitignored)
- `data.csv`: Shot data log with comma-delimited metrics
- Test scripts in `Python3/src/`: Various utilities for debugging BLED112 communication

## Notes

- Supports both Python 2 and 3, with Python 3 being current focus
- Windows executable can be built with py2exe (setup in Python2 folder)
- License discrepancy: README mentions MIT but LICENSE file is GPL v3