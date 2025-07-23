#!/usr/bin/env python3
"""Minimal BLE listener - dumps raw traffic from BLED112"""

import serial
import serial.tools.list_ports
import time
import sys
from datetime import datetime

# Find BLED112 port
import glob
ports = glob.glob('/dev/cu.usbmodem*') + glob.glob('/dev/tty.usbmodem*')
port = ports[0] if ports else None

if not port:
    print("Error: No BLED112 found (no usbmodem device)")
    sys.exit(1)

print(f"Found BLED112 at: {port}")

# Open serial connection
ser = serial.Serial(port, 115200, timeout=0.1)
print("Connected at 115200 baud\n")

# System reset
print("Sending system reset...")
ser.write(bytes.fromhex('00 01 00 00'))
time.sleep(2)
ser.flushInput()

# Start BLE observation
print("Starting BLE observation...")
ser.write(bytes.fromhex('00 01 06 02 01'))
print("Listening for raw BLE traffic (Ctrl+C to stop)\n")
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