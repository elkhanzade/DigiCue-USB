#!/usr/bin/env python3
"""BLE scanner that summarizes non-Apple devices"""

import serial
import time
from datetime import datetime
from collections import defaultdict

PORT = '/dev/ttyACM0'  # Change to /dev/cu.usbmodem11 for macOS

try:
    ser = serial.Serial(PORT, 115200, timeout=0.1)
    print(f"Connected to {PORT}")
except Exception as e:
    print(f"Failed to open {PORT}: {e}")
    exit(1)

# System reset
print("Resetting...")
ser.write(bytes.fromhex('00 01 00 00'))
time.sleep(2)
ser.flushInput()

# Start BLE observation
print("Starting scan...")
ser.write(bytes.fromhex('00 01 06 02 01'))
print("\nScanning for non-Apple BLE devices (Ctrl+C to stop)...\n")

devices = defaultdict(lambda: {'count': 0, 'rssi': [], 'last_seen': None, 'name': ''})
apple_count = 0

try:
    while True:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            hex_str = ' '.join(f'{b:02X}' for b in data)
            
            # Skip Apple devices
            if 'FF 4C 00' in hex_str:
                apple_count += 1
                continue
            
            # Parse BLE scan responses (80 = event, 06 00 = GAP scan response)
            if len(data) >= 11 and data[0] == 0x80 and data[2] == 0x06 and data[3] == 0x00:
                rssi = int.from_bytes(data[4:5], 'little', signed=True)
                mac = ':'.join(f'{b:02X}' for b in data[7:13][::-1])  # Reverse for correct order
                
                # Extract device name if present
                name = ''
                if len(data) > 14:
                    ad_len = data[13]
                    if len(data) >= 14 + ad_len:
                        ad_data = data[14:14+ad_len]
                        # Try to extract ASCII name
                        name = ''.join(chr(b) if 32 <= b < 127 else '' for b in ad_data).strip()
                
                # Update device info
                devices[mac]['count'] += 1
                devices[mac]['rssi'].append(rssi)
                devices[mac]['last_seen'] = datetime.now()
                if name and not devices[mac]['name']:
                    devices[mac]['name'] = name
                
                # Print summary every 10 detections
                total_detections = sum(d['count'] for d in devices.values())
                if total_detections % 10 == 0:
                    print(f"\n=== Found {len(devices)} non-Apple devices ({apple_count} Apple filtered) ===")
                    for mac, info in sorted(devices.items(), key=lambda x: x[1]['count'], reverse=True):
                        avg_rssi = sum(info['rssi']) / len(info['rssi'])
                        name_str = f" '{info['name']}'" if info['name'] else ""
                        print(f"{mac}{name_str}: {info['count']} detections, avg RSSI: {avg_rssi:.1f} dBm")
                    print("=" * 50 + "\n")
            
except KeyboardInterrupt:
    print(f"\n\nFinal Summary:")
    print(f"Total Apple devices filtered: {apple_count}")
    print(f"\nNon-Apple devices found:")
    for mac, info in sorted(devices.items(), key=lambda x: x[1]['count'], reverse=True):
        avg_rssi = sum(info['rssi']) / len(info['rssi'])
        name_str = f" '{info['name']}'" if info['name'] else ""
        print(f"  {mac}{name_str}: {info['count']} detections, avg RSSI: {avg_rssi:.1f} dBm")
    
    ser.write(bytes.fromhex('00 00 06 04'))
    time.sleep(0.5)
    ser.close()
    print("\nClosed")