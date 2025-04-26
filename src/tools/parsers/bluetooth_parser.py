#!/usr/bin/env python3

import re
from typing import Dict, List, Optional, Any

from models.bluetooth_device import BluetoothDevice
from utils.logger import Logger, LogLevel


class BluetoothParser:
    """Parser for Bluetooth command outputs."""
    
    def __init__(self, logging: Logger):
        self.logging = logging
    
    def parse_device_listing(self, output: str) -> List[BluetoothDevice]:
        """Parse the output of 'bluetoothctl devices' command.
        
        Args:
            output (str): Command output from bluetoothctl devices.
            
        Returns:
            List[BluetoothDevice]: List of parsed devices.
        """
        devices = []
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            try:
                # Format: "Device XX:XX:XX:XX:XX:XX DeviceName"
                parts = line.split(' ', 2)
                if len(parts) < 2:
                    continue
                
                mac_address = parts[1]
                name = parts[2] if len(parts) > 2 else "Unknown Device"
                
                # Create basic device, more details can be added with parse_device_info
                device = BluetoothDevice(
                    mac_address=mac_address,
                    name=name
                )
                devices.append(device)
                
            except Exception as e:
                self.logging.log(LogLevel.Error, f"Failed to parse device line: {line}, Error: {e}")
        
        return devices
    
    def parse_device_info(self, output: str) -> Optional[BluetoothDevice]:
        """Parse the output of 'bluetoothctl info XX:XX:XX:XX:XX:XX' command.
        
        Args:
            output (str): Command output from bluetoothctl info.
            
        Returns:
            Optional[BluetoothDevice]: Parsed device or None if parsing failed.
        """
        if not output or "No default controller available" in output:
            return None
            
        try:
            # Extract MAC address
            mac_match = re.search(r'Device ([0-9A-F:]{17})', output)
            if not mac_match:
                return None
                
            mac_address = mac_match.group(1)
            
            # Extract name
            name_match = re.search(r'Name: (.+)', output)
            name = name_match.group(1) if name_match else "Unknown Device"
            
            # Extract connection status
            connected = "Connected: yes" in output
            
            # Extract pairing status
            paired = "Paired: yes" in output
            
            # Extract trusted status
            trusted = "Trusted: yes" in output
            
            # Extract device type/icon
            device_type = "unknown"
            icon_match = re.search(r'Icon: (.+)', output)
            if icon_match:
                device_type = icon_match.group(1)
                
            # Extract battery level if available
            battery_percentage = None
            battery_match = re.search(r'Battery Percentage: \((\d+)\)', output)
            if battery_match:
                try:
                    battery_percentage = int(battery_match.group(1))
                except ValueError:
                    pass
            
            # Extract RSSI if available
            rssi = None
            rssi_match = re.search(r'RSSI: (-?\d+)', output)
            if rssi_match:
                try:
                    rssi = int(rssi_match.group(1))
                except ValueError:
                    pass
            
            return BluetoothDevice(
                mac_address=mac_address,
                name=name,
                connected=connected,
                paired=paired,
                trusted=trusted,
                device_type=device_type,
                battery_percentage=battery_percentage,
                rssi=rssi
            )
            
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed to parse device info: {e}")
            return None
    
    def parse_power_state(self, output: str) -> bool:
        """Parse the output of 'bluetoothctl show' command for power state.
        
        Args:
            output (str): Command output from bluetoothctl show.
            
        Returns:
            bool: True if powered on, False otherwise.
        """
        return "Powered: yes" in output
    
    def parse_controller_availability(self, output: str) -> bool:
        """Parse the output to check if a Bluetooth controller is available.
        
        Args:
            output (str): Command output from bluetoothctl show.
            
        Returns:
            bool: True if controller is available, False otherwise.
        """
        return "No default controller available" not in output