#!/usr/bin/env python3
"""Find BLED112 device on Linux"""

import glob
import os

print("Searching for BLED112 device...")

# Check common device paths
devices = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')

if devices:
    print(f"\nFound {len(devices)} possible device(s):")
    for dev in devices:
        print(f"  {dev}")
    print("\nThe BLED112 is likely one of these.")
else:
    print("\nNo ttyACM* or ttyUSB* devices found.")
    
print("\nYou can also check with:")
print("  dmesg | grep -i 'tty'")
print("  ls -la /dev/tty* | grep -E '(ACM|USB)'")