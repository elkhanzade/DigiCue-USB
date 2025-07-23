#!/usr/bin/env python3
"""Verbose test for DigiCue connection"""

import sys
sys.path.insert(0, '/Users/sarkhan/Library/Python/3.13/lib/python/site-packages')

import serial
import struct
import time

print("DigiCue Connection Test")
print("=" * 50)

# Connect to BLED112
port = '/dev/cu.usbmodem11'
ser = serial.Serial(port, 115200, timeout=1)
print(f"✓ Connected to BLED112 on {port}")

# Reset
print("\nResetting BLE module...")
ser.write(b'\x00\x00\x01\x00\x00\x00')
time.sleep(1)
ser.flushInput()

# Start scanning
print("Starting BLE scan...")
# Set GAP mode
ser.write(b'\x00\x00\x02\x06\x01\x00\x00')
time.sleep(0.1)
# Start discovery
ser.write(b'\x00\x00\x01\x06\x02\x02')

print("\nScanning for 15 seconds...")
print("Looking for DigiCue device (B7:76:8E)...")
print("-" * 50)

start_time = time.time()
devices_found = 0
digicue_found = False

while time.time() - start_time < 15:
    if ser.in_waiting >= 4:
        # Read header
        header = ser.read(4)
        msg_type, tech_type, payload_len, cls_id = struct.unpack('<BBBB', header)
        
        # Read rest
        if ser.in_waiting >= payload_len + 1:
            cmd_id = struct.unpack('<B', ser.read(1))[0]
            payload = ser.read(payload_len)
            
            # Scan response event
            if msg_type == 0x80 and cls_id == 0x06 and cmd_id == 0x00 and len(payload) >= 11:
                devices_found += 1
                rssi = struct.unpack('<b', payload[0:1])[0]
                address = payload[2:8]
                addr_hex = ':'.join(f'{b:02X}' for b in address[::-1])
                
                data_len = payload[10] if len(payload) > 10 else 0
                data = payload[11:11+data_len] if len(payload) > 11 and data_len > 0 else b''
                
                # Always print device info
                print(f"\nDevice #{devices_found}:")
                print(f"  Address: {addr_hex}")
                print(f"  RSSI: {rssi} dBm")
                if data:
                    print(f"  Data ({len(data)} bytes): {' '.join(f'{b:02X}' for b in data)}")
                    # Try to decode as ASCII
                    try:
                        ascii_data = data.decode('ascii', errors='replace')
                        print(f"  ASCII: '{ascii_data}'")
                    except:
                        pass
                
                # Check if DigiCue
                if 'B7:76:8E' in addr_hex or b'DigiCue' in data:
                    print("  *** This is the DigiCue! ***")
                    digicue_found = True

# Stop scanning
print("\n" + "-" * 50)
print("Stopping scan...")
ser.write(b'\x00\x00\x00\x06\x04')
time.sleep(0.5)

ser.close()

print(f"\nScan complete. Found {devices_found} devices.")
if digicue_found:
    print("✓ DigiCue was detected!")
else:
    print("⚠️  DigiCue not found. Make sure it's powered on and in range.")