#!/usr/bin/env python3
"""
Test script for BLED112 USB dongle to connect to DigiCue device
Uses BGAPI binary protocol to communicate with BLED112
"""

import sys
# Add path for user-installed packages
sys.path.insert(0, '/Users/sarkhan/Library/Python/3.13/lib/python/site-packages')

import serial
import struct
import time
import threading

# BGAPI Protocol Constants
BGAPI_HEADER_LENGTH = 4

# Message Types
BGAPI_MSG_TYPE_COMMAND = 0x00
BGAPI_MSG_TYPE_RESPONSE = 0x00
BGAPI_MSG_TYPE_EVENT = 0x80

# Technology Types
BGAPI_TECH_TYPE_BLUETOOTH = 0x00

# Class IDs
BGAPI_CLASS_SYSTEM = 0x00
BGAPI_CLASS_GAP = 0x06
BGAPI_CLASS_CONNECTION = 0x03
BGAPI_CLASS_ATTCLIENT = 0x04

# Command IDs
BGAPI_CMD_SYSTEM_RESET = 0x00
BGAPI_CMD_GAP_SET_MODE = 0x01
BGAPI_CMD_GAP_DISCOVER = 0x02
BGAPI_CMD_GAP_END_PROCEDURE = 0x04
BGAPI_CMD_GAP_CONNECT_DIRECT = 0x03
BGAPI_CMD_CONNECTION_DISCONNECT = 0x00
BGAPI_CMD_ATTCLIENT_FIND_INFORMATION = 0x03
BGAPI_CMD_ATTCLIENT_READ_BY_TYPE = 0x02

# Event IDs
BGAPI_EVT_GAP_SCAN_RESPONSE = 0x00
BGAPI_EVT_CONNECTION_STATUS = 0x00
BGAPI_EVT_CONNECTION_DISCONNECTED = 0x04
BGAPI_EVT_ATTCLIENT_PROCEDURE_COMPLETED = 0x01
BGAPI_EVT_ATTCLIENT_VALUE_INDICATION = 0x05
BGAPI_EVT_ATTCLIENT_VALUE_NOTIFICATION = 0x05

class BLED112:
    def __init__(self, port='/dev/cu.usbmodem11', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connection_handle = None
        self.target_address = None
        self.running = True
        
    def connect(self):
        """Connect to BLED112 dongle"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"Connected to BLED112 on {self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from BLED112"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Disconnected from BLED112")
    
    def send_command(self, msg_type, tech_type, cls_id, cmd_id, payload=b''):
        """Send BGAPI command"""
        header = struct.pack('<BBBB', msg_type, tech_type, len(payload), cls_id)
        packet = header + struct.pack('<B', cmd_id) + payload
        
        print(f"Sending: {' '.join(f'{b:02X}' for b in packet)}")
        self.ser.write(packet)
    
    def read_packet(self):
        """Read BGAPI packet"""
        # Read header
        header = self.ser.read(BGAPI_HEADER_LENGTH)
        if len(header) < BGAPI_HEADER_LENGTH:
            return None
        
        msg_type, tech_type, payload_length, cls_id = struct.unpack('<BBBB', header)
        
        # Read command/event ID
        cmd_id_byte = self.ser.read(1)
        if not cmd_id_byte:
            return None
        cmd_id = struct.unpack('<B', cmd_id_byte)[0]
        
        # Read payload
        payload = self.ser.read(payload_length)
        
        return {
            'msg_type': msg_type,
            'tech_type': tech_type,
            'cls_id': cls_id,
            'cmd_id': cmd_id,
            'payload': payload
        }
    
    def reset_ble_module(self):
        """Reset BLE module"""
        print("\nResetting BLE module...")
        self.send_command(BGAPI_MSG_TYPE_COMMAND, BGAPI_TECH_TYPE_BLUETOOTH, 
                         BGAPI_CLASS_SYSTEM, BGAPI_CMD_SYSTEM_RESET, b'\x00')
        time.sleep(1)
        # Clear any pending data
        self.ser.flushInput()
    
    def start_scanning(self):
        """Start BLE scanning"""
        print("\nStarting BLE scan...")
        # Set GAP mode to non-discoverable, non-connectable
        self.send_command(BGAPI_MSG_TYPE_COMMAND, BGAPI_TECH_TYPE_BLUETOOTH,
                         BGAPI_CLASS_GAP, BGAPI_CMD_GAP_SET_MODE, b'\x00\x00')
        time.sleep(0.1)
        
        # Start discovery (active scanning)
        self.send_command(BGAPI_MSG_TYPE_COMMAND, BGAPI_TECH_TYPE_BLUETOOTH,
                         BGAPI_CLASS_GAP, BGAPI_CMD_GAP_DISCOVER, b'\x02')
    
    def stop_scanning(self):
        """Stop BLE scanning"""
        print("\nStopping BLE scan...")
        self.send_command(BGAPI_MSG_TYPE_COMMAND, BGAPI_TECH_TYPE_BLUETOOTH,
                         BGAPI_CLASS_GAP, BGAPI_CMD_GAP_END_PROCEDURE)
    
    def connect_to_device(self, address, address_type):
        """Connect to BLE device"""
        print(f"\nConnecting to device {':'.join(f'{b:02X}' for b in address)}...")
        # address (6 bytes) + address_type (1 byte) + conn_interval_min (2) + conn_interval_max (2) + timeout (2) + latency (2)
        payload = address + struct.pack('<BHHHHH', address_type, 60, 76, 100, 0, 0)
        self.send_command(BGAPI_MSG_TYPE_COMMAND, BGAPI_TECH_TYPE_BLUETOOTH,
                         BGAPI_CLASS_GAP, BGAPI_CMD_GAP_CONNECT_DIRECT, payload)
    
    def parse_scan_response(self, packet):
        """Parse scan response event"""
        if len(packet['payload']) < 11:
            return
        
        rssi, packet_type, address = struct.unpack('<bB6s', packet['payload'][:8])
        address_type, bond = struct.unpack('<BB', packet['payload'][8:10])
        data_len = packet['payload'][10]
        data = packet['payload'][11:11+data_len] if len(packet['payload']) > 11 else b''
        
        # Convert address to hex string
        addr_hex = ':'.join(f'{b:02X}' for b in address[::-1])
        
        # Check if this is a DigiCue device
        if b'DigiCue' in data or 'B7:76:8E' in addr_hex:
            print(f"\nFound DigiCue device!")
            print(f"  Address: {addr_hex}")
            print(f"  RSSI: {rssi} dBm")
            print(f"  Data: {data}")
            
            # Store the address for connection
            self.target_address = address
            self.target_address_type = address_type
            
            # Stop scanning and connect
            self.stop_scanning()
            time.sleep(0.5)
            self.connect_to_device(address, address_type)
    
    def handle_connection_status(self, packet):
        """Handle connection status event"""
        if len(packet['payload']) < 16:
            return
        
        connection, flags, address, address_type = struct.unpack('<BB6sB', packet['payload'][:9])
        conn_interval, timeout, latency, bonding = struct.unpack('<HHHB', packet['payload'][9:16])
        
        addr_hex = ':'.join(f'{b:02X}' for b in address[::-1])
        print(f"\nConnection status:")
        print(f"  Handle: {connection}")
        print(f"  Address: {addr_hex}")
        print(f"  Flags: {flags}")
        
        if flags & 0x01:  # Connected
            print("  Status: CONNECTED")
            self.connection_handle = connection
            # Now we can start listening for notifications
            print("\nListening for DigiCue data...")
        else:
            print("  Status: Not connected")
    
    def handle_notification(self, packet):
        """Handle attribute value notification"""
        if len(packet['payload']) < 5:
            return
        
        connection, atthandle = struct.unpack('<BH', packet['payload'][:3])
        value_len = packet['payload'][3]
        value = packet['payload'][4:4+value_len] if len(packet['payload']) >= 4+value_len else b''
        
        print(f"\nReceived data from DigiCue:")
        print(f"  Handle: {atthandle}")
        print(f"  Length: {value_len}")
        print(f"  Raw data: {' '.join(f'{b:02X}' for b in value)}")
        
        # Try to interpret the data
        if value_len >= 2:
            # This is a guess - adjust based on actual DigiCue protocol
            print(f"  Data interpretation: {struct.unpack('<H', value[:2])[0]}")
    
    def process_events(self):
        """Process incoming BGAPI events"""
        while self.running:
            try:
                packet = self.read_packet()
                if not packet:
                    continue
                
                # Check if it's an event
                if packet['msg_type'] & BGAPI_MSG_TYPE_EVENT:
                    if packet['cls_id'] == BGAPI_CLASS_GAP and packet['cmd_id'] == BGAPI_EVT_GAP_SCAN_RESPONSE:
                        self.parse_scan_response(packet)
                    elif packet['cls_id'] == BGAPI_CLASS_CONNECTION:
                        if packet['cmd_id'] == BGAPI_EVT_CONNECTION_STATUS:
                            self.handle_connection_status(packet)
                        elif packet['cmd_id'] == BGAPI_EVT_CONNECTION_DISCONNECTED:
                            print("\nDevice disconnected")
                            self.connection_handle = None
                    elif packet['cls_id'] == BGAPI_CLASS_ATTCLIENT:
                        if packet['cmd_id'] == BGAPI_EVT_ATTCLIENT_VALUE_NOTIFICATION:
                            self.handle_notification(packet)
                
            except Exception as e:
                if self.running:
                    print(f"Error processing events: {e}")
    
    def run_test(self):
        """Run the test sequence"""
        if not self.connect():
            return
        
        try:
            # Start event processing thread
            event_thread = threading.Thread(target=self.process_events)
            event_thread.daemon = True
            event_thread.start()
            
            # Reset and start scanning
            self.reset_ble_module()
            self.start_scanning()
            
            # Wait for user to stop
            print("\nScanning for DigiCue device...")
            print("Make practice strokes with your cue once connected.")
            print("Press Ctrl+C to stop.\n")
            
            while self.running:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nStopping...")
            self.running = False
            if self.connection_handle is not None:
                # Disconnect if connected
                self.send_command(BGAPI_MSG_TYPE_COMMAND, BGAPI_TECH_TYPE_BLUETOOTH,
                                BGAPI_CLASS_CONNECTION, BGAPI_CMD_CONNECTION_DISCONNECT,
                                struct.pack('<B', self.connection_handle))
                time.sleep(0.5)
            self.stop_scanning()
            time.sleep(0.5)
        finally:
            self.disconnect()

if __name__ == "__main__":
    bled = BLED112()
    bled.run_test()