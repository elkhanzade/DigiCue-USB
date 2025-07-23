#!/usr/bin/env python3
"""
DigiCue Listening Daemon
Continuously listens for DigiCue devices and broadcasts scan requests every 5 seconds
"""

import sys
sys.path.insert(0, '/Users/sarkhan/Library/Python/3.13/lib/python/site-packages')

import serial
import struct
import time
import threading
import signal
from datetime import datetime

class DigiCueDaemon:
    def __init__(self, port='/dev/cu.usbmodem11'):
        self.port = port
        self.ser = None
        self.running = False
        self.connected_devices = {}
        self.last_broadcast = 0
        self.scan_active = False
        
    def connect(self):
        """Connect to BLED112"""
        try:
            self.ser = serial.Serial(self.port, 115200, timeout=0.1)
            print(f"[{self.timestamp()}] Connected to BLED112 on {self.port}")
            return True
        except Exception as e:
            print(f"[{self.timestamp()}] Failed to connect: {e}")
            return False
    
    def timestamp(self):
        """Get current timestamp"""
        return datetime.now().strftime("%H:%M:%S")
    
    def reset_module(self):
        """Reset BLE module"""
        print(f"[{self.timestamp()}] Resetting BLE module...")
        self.ser.write(b'\x00\x00\x01\x00\x00\x00')
        time.sleep(1)
        self.ser.flushInput()
    
    def start_scan(self):
        """Start BLE scanning"""
        if not self.scan_active:
            print(f"[{self.timestamp()}] Starting BLE scan...")
            # Set GAP mode
            self.ser.write(b'\x00\x00\x02\x06\x01\x00\x00')
            time.sleep(0.1)
            # Start discovery
            self.ser.write(b'\x00\x00\x01\x06\x02\x02')
            self.scan_active = True
            self.last_broadcast = time.time()
    
    def stop_scan(self):
        """Stop BLE scanning"""
        if self.scan_active:
            self.ser.write(b'\x00\x00\x00\x06\x04')
            self.scan_active = False
    
    def parse_packet(self):
        """Parse incoming BGAPI packets"""
        if self.ser.in_waiting < 4:
            return
        
        # Read header
        header = self.ser.read(4)
        if len(header) < 4:
            return
            
        msg_type, tech_type, payload_len, cls_id = struct.unpack('<BBBB', header)
        
        # Read command ID and payload
        if self.ser.in_waiting >= payload_len + 1:
            cmd_id = struct.unpack('<B', self.ser.read(1))[0]
            payload = self.ser.read(payload_len) if payload_len > 0 else b''
            
            # Handle scan response
            if msg_type == 0x80 and cls_id == 0x06 and cmd_id == 0x00:
                self.handle_scan_response(payload)
            # Handle connection status
            elif msg_type == 0x80 and cls_id == 0x03 and cmd_id == 0x00:
                self.handle_connection_status(payload)
            # Handle notifications
            elif msg_type == 0x80 and cls_id == 0x04 and cmd_id == 0x05:
                self.handle_notification(payload)
    
    def handle_scan_response(self, payload):
        """Handle scan response packets"""
        if len(payload) < 11:
            return
        
        rssi = struct.unpack('<b', payload[0:1])[0]
        address = payload[2:8]
        addr_hex = ':'.join(f'{b:02X}' for b in address[::-1])
        
        data_len = payload[10] if len(payload) > 10 else 0
        data = payload[11:11+data_len] if len(payload) > 11 and data_len > 0 else b''
        
        # Check if DigiCue
        if 'B7:76:8E' in addr_hex or b'DigiCue' in data:
            if addr_hex not in self.connected_devices:
                print(f"\n[{self.timestamp()}] 🎯 DigiCue found!")
                print(f"  Address: {addr_hex}")
                print(f"  RSSI: {rssi} dBm")
                if data:
                    try:
                        ascii_data = data.decode('ascii', errors='replace')
                        print(f"  Name: {ascii_data}")
                    except:
                        pass
                self.connected_devices[addr_hex] = {
                    'rssi': rssi,
                    'last_seen': time.time(),
                    'address': address
                }
            else:
                # Update RSSI and last seen
                self.connected_devices[addr_hex]['rssi'] = rssi
                self.connected_devices[addr_hex]['last_seen'] = time.time()
    
    def handle_connection_status(self, payload):
        """Handle connection status events"""
        if len(payload) >= 16:
            connection, flags, address = struct.unpack('<BB6s', payload[:8])
            addr_hex = ':'.join(f'{b:02X}' for b in address[::-1])
            
            if flags & 0x01:
                print(f"\n[{self.timestamp()}] ✓ Connected to {addr_hex}")
            else:
                print(f"\n[{self.timestamp()}] ✗ Disconnected from {addr_hex}")
    
    def handle_notification(self, payload):
        """Handle data notifications from DigiCue"""
        if len(payload) >= 5:
            connection, atthandle = struct.unpack('<BH', payload[:3])
            value_len = payload[3]
            value = payload[4:4+value_len] if len(payload) >= 4+value_len else b''
            
            print(f"\n[{self.timestamp()}] 📊 DigiCue Data:")
            print(f"  Handle: {atthandle}")
            print(f"  Raw: {' '.join(f'{b:02X}' for b in value)}")
            
            # Try to interpret the data (adjust based on actual protocol)
            if len(value) >= 2:
                val = struct.unpack('<H', value[:2])[0]
                print(f"  Value: {val}")
    
    def broadcast_loop(self):
        """Broadcast scan requests every 5 seconds"""
        while self.running:
            current_time = time.time()
            
            # Broadcast every 5 seconds
            if current_time - self.last_broadcast >= 5:
                self.stop_scan()
                time.sleep(0.1)
                self.start_scan()
                
                # Show status
                if self.connected_devices:
                    print(f"\n[{self.timestamp()}] 📡 Broadcasting... ({len(self.connected_devices)} DigiCue(s) tracked)")
                    for addr, info in self.connected_devices.items():
                        age = int(current_time - info['last_seen'])
                        print(f"  {addr}: RSSI {info['rssi']} dBm (last seen {age}s ago)")
                else:
                    print(f"\n[{self.timestamp()}] 📡 Broadcasting... (no devices found yet)")
            
            time.sleep(0.1)
    
    def listen_loop(self):
        """Main listening loop"""
        while self.running:
            try:
                self.parse_packet()
            except Exception as e:
                if self.running:
                    print(f"\n[{self.timestamp()}] Error: {e}")
            time.sleep(0.001)
    
    def run(self):
        """Run the daemon"""
        if not self.connect():
            return
        
        print(f"\n{'='*60}")
        print("DigiCue Listening Daemon Started")
        print(f"{'='*60}")
        print("Broadcasting every 5 seconds...")
        print("Press Ctrl+C to stop\n")
        
        self.running = True
        
        try:
            # Reset module
            self.reset_module()
            
            # Start initial scan
            self.start_scan()
            
            # Start threads
            broadcast_thread = threading.Thread(target=self.broadcast_loop)
            broadcast_thread.daemon = True
            broadcast_thread.start()
            
            listen_thread = threading.Thread(target=self.listen_loop)
            listen_thread.daemon = True
            listen_thread.start()
            
            # Wait for Ctrl+C
            while self.running:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print(f"\n[{self.timestamp()}] Shutting down...")
        finally:
            self.running = False
            self.stop_scan()
            time.sleep(0.5)
            if self.ser and self.ser.is_open:
                self.ser.close()
            print(f"[{self.timestamp()}] Daemon stopped")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    pass

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    daemon = DigiCueDaemon()
    daemon.run()