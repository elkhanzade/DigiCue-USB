#!/usr/bin/env python3
"""Run the test script with controlled output"""

import subprocess
import time
import signal

# Run the test script for 20 seconds
print("Running BLED112-DigiCue test for 20 seconds...")
print("Make sure your DigiCue is powered on!\n")

proc = subprocess.Popen(['python3', 'test_bled112_digicue.py'], 
                       stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE,
                       text=True)

try:
    # Wait for 20 seconds
    stdout, stderr = proc.communicate(timeout=20)
    print("STDOUT:")
    print(stdout)
    if stderr:
        print("\nSTDERR:")
        print(stderr)
except subprocess.TimeoutExpired:
    print("\nStopping after 20 seconds...")
    proc.terminate()
    time.sleep(1)
    if proc.poll() is None:
        proc.kill()
    stdout, stderr = proc.communicate()
    print("STDOUT:")
    print(stdout)
    if stderr:
        print("\nSTDERR:")
        print(stderr)