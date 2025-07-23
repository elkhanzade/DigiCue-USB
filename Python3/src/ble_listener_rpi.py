#!/usr/bin/env python3
"""Minimal BLE listener for Raspberry Pi 3 with BLED112"""

import sys
import time
from datetime import datetime

# Try to import pyserial
try:
    import serial
except ImportError:
    print("Error: pyserial not installed")
    print("Install with: pip install pyserial")
    sys.exit(1)

# BLED112 on Raspberry Pi 3
PORT = '/dev/ttyACM0'

try:
    ser = serial.Serial(PORT, 115200, timeout=0.1)
    print(f"Connected to BLED112 on {PORT}")
except Exception as e:
    print(f"Failed to open {PORT}: {e}")
    print("Check if BLED112 is connected to Raspberry Pi")
    print("\nTry running: ls /dev/tty* | grep -E '(ACM|USB)'")
    print("to find the correct device")
    sys.exit(1)

# System reset
print("Sending system reset...")
ser.write(bytes.fromhex('00 01 00 00'))
time.sleep(2)
ser.flushInput()

# Start BLE observation
print("Starting BLE observation...")
ser.write(bytes.fromhex('00 01 06 02 01'))
print("\nListening for raw BLE traffic (Ctrl+C to stop)\n")
print("-" * 70)

try:
    while True:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            hex_str = ' '.join(f'{b:02X}' for b in data)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)
            
            print(f"[{timestamp}] {hex_str}")
            print(f"            ASCII: {ascii_str}")
            print()
            
except KeyboardInterrupt:
    print("\nStopping BLE observation...")
    ser.write(bytes.fromhex('00 00 06 04'))
    time.sleep(0.5)
    ser.close()
    print("Closed.")