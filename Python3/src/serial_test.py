#!/usr/bin/env python3
"""Test basic serial connection"""

import serial
import sys

port = '/dev/cu.usbmodem11'

try:
    print(f"Testing serial port {port}...")
    
    # Try to open the port
    ser = serial.Serial(port, 115200, timeout=0.5)
    print(f"✓ Port opened successfully")
    print(f"  Port: {ser.port}")
    print(f"  Baudrate: {ser.baudrate}")
    print(f"  Is open: {ser.is_open}")
    
    # Send a simple command and read response
    print("\nSending test data...")
    test_data = b'\x00\x00\x01\x00\x00\x00'  # Reset command
    ser.write(test_data)
    print(f"✓ Sent {len(test_data)} bytes")
    
    # Try to read response
    print("\nReading response (waiting up to 2 seconds)...")
    ser.timeout = 2
    response = ser.read(100)
    
    if response:
        print(f"✓ Received {len(response)} bytes:")
        print(f"  Hex: {' '.join(f'{b:02X}' for b in response)}")
    else:
        print("⚠️  No response received")
    
    ser.close()
    print("\n✓ Port closed successfully")
    
except serial.SerialException as e:
    print(f"❌ Serial error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()