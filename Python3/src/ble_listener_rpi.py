#!/usr/bin/env python3
"""Minimal BLE listener for Raspberry Pi 3 with BLED112"""

import sys
import time
import argparse
from datetime import datetime

# Try to import pyserial
try:
    import serial
except ImportError:
    print("Error: pyserial not installed")
    print("Install with: pip install pyserial")
    sys.exit(1)

# Parse arguments
parser = argparse.ArgumentParser(description='BLE traffic listener for BLED112')
parser.add_argument('-o', '--output', help='Output file to capture data')
parser.add_argument('-p', '--port', default='/dev/ttyACM0', help='Serial port (default: /dev/ttyACM0)')
args = parser.parse_args()

PORT = args.port
capture_file = None

try:
    ser = serial.Serial(PORT, 115200, timeout=0.1)
    print(f"Connected to BLED112 on {PORT}")
except Exception as e:
    print(f"Failed to open {PORT}: {e}")
    print("Check if BLED112 is connected to Raspberry Pi")
    print("\nTry running: ls /dev/tty* | grep -E '(ACM|USB)'")
    print("to find the correct device")
    sys.exit(1)

# Open capture file if specified
if args.output:
    try:
        capture_file = open(args.output, 'w')
        print(f"Capturing to: {args.output}")
    except Exception as e:
        print(f"Failed to open capture file: {e}")
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
            
            # Print to console
            print(f"[{timestamp}] {hex_str}")
            print(f"            ASCII: {ascii_str}")
            print()
            
            # Write to capture file if specified
            if capture_file:
                capture_file.write(f"[{timestamp}] {hex_str}\n")
                capture_file.write(f"            ASCII: {ascii_str}\n")
                capture_file.write("\n")
                capture_file.flush()  # Ensure data is written immediately
            
except KeyboardInterrupt:
    print("\nStopping BLE observation...")
    ser.write(bytes.fromhex('00 00 06 04'))
    time.sleep(0.5)
    ser.close()
    if capture_file:
        capture_file.close()
        print(f"Capture saved to: {args.output}")
    print("Closed.")