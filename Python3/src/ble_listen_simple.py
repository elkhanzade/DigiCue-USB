#!/usr/bin/env python3
"""Ultra-simple BLE listener"""

import serial
import time
from datetime import datetime

# Hardcode the port - change this if needed
PORT = '/dev/cu.usbmodem11'

try:
    ser = serial.Serial(PORT, 115200, timeout=0.1)
    print(f"Connected to {PORT}")
except Exception as e:
    print(f"Failed to open {PORT}: {e}")
    print("Check if BLED112 is connected and try again")
    exit(1)

# Reset
ser.write(b'\x00\x01\x00\x00')
time.sleep(2)
ser.flushInput()

# Start observation
ser.write(b'\x00\x01\x06\x02\x01')
print("\nListening... (Ctrl+C to stop)\n")

try:
    while True:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{ts}] {' '.join(f'{b:02X}' for b in data)}")
except KeyboardInterrupt:
    ser.write(b'\x00\x00\x06\x04')  # Stop
    ser.close()
    print("\nStopped")