#!/usr/bin/env python3
"""Quick test to verify BLED112 connection and scanning"""

import sys
sys.path.append('/Users/sarkhan/Library/Python/3.13/lib/python/site-packages')

import serial
import time
import struct

# Try to connect to BLED112
port = '/dev/cu.usbmodem11'
print(f"Attempting to connect to BLED112 on {port}...")

try:
    ser = serial.Serial(port, 115200, timeout=1)
    print("✓ Successfully connected to BLED112")
    
    # Send reset command
    print("\nSending reset command...")
    reset_cmd = struct.pack('<BBBBB', 0x00, 0x00, 0x01, 0x00, 0x00) + b'\x00'
    ser.write(reset_cmd)
    print(f"Sent: {' '.join(f'{b:02X}' for b in reset_cmd)}")
    
    time.sleep(1)
    
    # Clear buffer
    ser.flushInput()
    
    # Send scan command
    print("\nStarting BLE scan...")
    # Set GAP mode
    gap_mode_cmd = struct.pack('<BBBBB', 0x00, 0x00, 0x02, 0x06, 0x01) + b'\x00\x00'
    ser.write(gap_mode_cmd)
    time.sleep(0.1)
    
    # Start discovery
    discover_cmd = struct.pack('<BBBBB', 0x00, 0x00, 0x01, 0x06, 0x02) + b'\x02'
    ser.write(discover_cmd)
    print(f"Sent scan command: {' '.join(f'{b:02X}' for b in discover_cmd)}")
    
    # Read responses for 10 seconds
    print("\nListening for devices (10 seconds)...")
    start_time = time.time()
    found_digicue = False
    
    while time.time() - start_time < 10:
        if ser.in_waiting > 0:
            # Read header
            header = ser.read(4)
            if len(header) == 4:
                msg_type, tech_type, payload_len, cls_id = struct.unpack('<BBBB', header)
                
                # Read rest of packet
                cmd_id_byte = ser.read(1)
                if cmd_id_byte:
                    cmd_id = struct.unpack('<B', cmd_id_byte)[0]
                    payload = ser.read(payload_len)
                    
                    # Check if it's a scan response event
                    if msg_type == 0x80 and cls_id == 0x06 and cmd_id == 0x00:
                        if len(payload) >= 11:
                            rssi = struct.unpack('<b', payload[0:1])[0]
                            address = payload[2:8]
                            addr_hex = ':'.join(f'{b:02X}' for b in address[::-1])
                            
                            data_len = payload[10] if len(payload) > 10 else 0
                            data = payload[11:11+data_len] if len(payload) > 11 else b''
                            
                            # Check for DigiCue
                            if b'DigiCue' in data or 'B7:76:8E' in addr_hex:
                                print(f"\n🎯 Found DigiCue device!")
                                print(f"   Address: {addr_hex}")
                                print(f"   RSSI: {rssi} dBm")
                                print(f"   Raw data: {' '.join(f'{b:02X}' for b in data)}")
                                if data:
                                    print(f"   ASCII: {data.decode('ascii', errors='replace')}")
                                found_digicue = True
    
    # Stop scanning
    print("\nStopping scan...")
    stop_cmd = struct.pack('<BBBBB', 0x00, 0x00, 0x00, 0x06, 0x04)
    ser.write(stop_cmd)
    
    ser.close()
    
    if found_digicue:
        print("\n✓ DigiCue detected! The BLED112 connection is working.")
    else:
        print("\n⚠️  DigiCue not found. Make sure the device is powered on and nearby.")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure BLED112 is connected to USB")
    print("2. Check if the correct port is being used")
    print("3. Ensure no other program is using the serial port")