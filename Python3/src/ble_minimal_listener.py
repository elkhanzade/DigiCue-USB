#!/usr/bin/env python3
"""Ultra-minimal BLE listener for BLED112 on RPi"""

import serial
import time
from datetime import datetime

PORT = '/dev/ttyACM0'

try:
    ser = serial.Serial(PORT, 115200, timeout=0.1)
    print(f"Connected to {PORT}")
except Exception as e:
    print(f"Failed to open {PORT}: {e}")
    exit(1)

# System reset
print("Sending system reset...")
ser.write(bytes.fromhex('00 01 00 00'))
time.sleep(2)
ser.flushInput()

# Start BLE observation
print("Starting BLE observation...")
ser.write(bytes.fromhex('00 01 06 02 01'))
print("\nListening (Ctrl+C to stop)...\n")

try:
    while True:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            hex_str = ' '.join(f'{b:02X}' for b in data)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)
            
            print(f"[{ts}] {hex_str}")
            print(f"{'':>12} ASCII: {ascii_str}\n")
            
except KeyboardInterrupt:
    print("\nStopping...")
    ser.write(bytes.fromhex('00 00 06 04'))
    time.sleep(0.5)
    ser.close()
    print("Closed")