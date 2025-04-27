#!/usr/bin/env python3

import subprocess
import time
import threading
from typing import List, Optional, Tuple, Dict, Any

from models.bluetooth_device import BluetoothDevice
from tools.services.bluetooth_service import BluetoothService
from tools.parsers.bluetooth_parser import BluetoothParser
from utils.logger import Logger, LogLevel


class BluetoothctlService(BluetoothService):
    """Implementation of BluetoothService using bluetoothctl command-line utility."""
    
    def __init__(self, logging: Logger):
        self.logging = logging
        self.parser = BluetoothParser(logging)
        self._cache = {}
        self._cache_ttl = 5  # seconds
        self._cache_timestamps = {}
        self._lock = threading.RLock()
        
    def _run_command(self, command: str) -> str:
        """Run a bluetoothctl command and return its output.
        
        Args:
            command (str): Command to run in bluetoothctl.
            
        Returns:
            str: Command output.
        """
        try:
            full_command = f"bluetoothctl {command}"
            self.logging.log(LogLevel.Debug, f"Running command: {full_command}")
            output = subprocess.check_output(
                full_command, 
                shell=True, 
                stderr=subprocess.STDOUT,
                text=True
            )
            return output
        except subprocess.CalledProcessError as e:
            self.logging.log(LogLevel.Error, f"Command failed: {e.output}")
            return e.output if e.output else ""
            
    def _cached_run(self, command: str, cache_key: str = None, use_cache: bool = True) -> str:
        """Run a command with caching.
        
        Args:
            command (str): Command to run.
            cache_key (str, optional): Key to use for caching. Defaults to command.
            use_cache (bool, optional): Whether to use cache. Defaults to True.
            
        Returns:
            str: Command output.
        """
        if cache_key is None:
            cache_key = command
            
        with self._lock:
            now = time.time()
            
            # Return cached result if valid
            if use_cache and cache_key in self._cache:
                timestamp = self._cache_timestamps.get(cache_key, 0)
                if now - timestamp < self._cache_ttl:
                    self.logging.log(LogLevel.Debug, f"Using cached result for: {cache_key}")
                    return self._cache[cache_key]
            
            # Run command
            result = self._run_command(command)
            
            # Cache result
            if use_cache:
                self._cache[cache_key] = result
                self._cache_timestamps[cache_key] = now
                
            return result
    
    def invalidate_cache(self, key: Optional[str] = None) -> None:
        """Invalidate cache entries.
        
        Args:
            key (Optional[str], optional): Specific key to invalidate, or None for all. Defaults to None.
        """
        with self._lock:
            if key is None:
                self._cache.clear()
                self._cache_timestamps.clear()
            elif key in self._cache:
                del self._cache[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]
    
    def get_power_state(self) -> bool:
        """Get the current power state of the Bluetooth adapter."""
        output = self._cached_run("show")
        return self.parser.parse_power_state(output)
        
    def set_power_state(self, state: bool) -> bool:
        """Set the power state of the Bluetooth adapter using rfkill."""
        action = "unblock" if state else "block"
        command = f"rfkill {action} bluetooth"
        try:
            self.logging.log(LogLevel.Info, f"Attempting to set Bluetooth power state using: {command}")
            # Use subprocess.run for better error handling
            result = subprocess.run(
                command.split(), 
                check=True, 
                capture_output=True, 
                text=True
            )
            self.logging.log(LogLevel.Debug, f"rfkill command output: {result.stdout}")
            # Invalidate cache after potentially changing power state
            self.invalidate_cache("show") # Keep checking state via bluetoothctl for now
            return True
        except FileNotFoundError:
            self.logging.log(LogLevel.Error, "rfkill command not found. Cannot change Bluetooth power state.")
            return False
        except subprocess.CalledProcessError as e:
            self.logging.log(LogLevel.Error, f"rfkill command failed: {e.stderr}")
            # Attempt to provide a more helpful message based on common rfkill errors
            if "Operation not possible due to RF-kill" in e.stderr:
                 self.logging.log(LogLevel.Warning, "Bluetooth state might be blocked by hardware switch or airplane mode.")
            elif "Permission denied" in e.stderr:
                 self.logging.log(LogLevel.Error, "Permission denied for rfkill. User might need specific group membership (e.g., rfkill group).")
            return False
        except Exception as e:
            self.logging.log(LogLevel.Error, f"An unexpected error occurred while running rfkill: {e}")
            return False
        
    def get_devices(self) -> List[BluetoothDevice]:
        """Get list of known Bluetooth devices."""
        output = self._cached_run("devices")
        devices = self.parser.parse_device_listing(output)
        
        # Enrich basic device info with detailed info
        for device in devices:
            detailed_info = self.get_device_info(device.mac_address)
            if detailed_info:
                # Update this device with detailed info
                device.connected = detailed_info.connected
                device.paired = detailed_info.paired
                device.trusted = detailed_info.trusted
                device.device_type = detailed_info.device_type
                device.battery_percentage = detailed_info.battery_percentage
                device.rssi = detailed_info.rssi
                
        return devices
        
    def scan_for_devices(self, timeout_seconds: int = 10) -> List[BluetoothDevice]:
        """Scan for available Bluetooth devices."""
        # Start scan
        scan_command = f"scan on"
        self._run_command(scan_command)
        
        try:
            # Wait for the specified timeout
            time.sleep(timeout_seconds)
        finally:
            # Stop scan
            self._run_command("scan off")
            
        # Invalidate cache to get fresh device list
        self.invalidate_cache("devices")
        
        # Return updated device list
        return self.get_devices()
        
    def get_device_info(self, mac_address: str) -> Optional[BluetoothDevice]:
        """Get detailed information about a specific device."""
        cache_key = f"info_{mac_address}"
        output = self._cached_run(f"info {mac_address}", cache_key)
        return self.parser.parse_device_info(output)
        
    def connect_device(self, mac_address: str) -> bool:
        """Connect to a Bluetooth device."""
        output = self._run_command(f"connect {mac_address}")
        
        # Invalidate cache
        self.invalidate_cache(f"info_{mac_address}")
        
        return "Connection successful" in output
        
    def disconnect_device(self, mac_address: str) -> bool:
        """Disconnect from a Bluetooth device."""
        output = self._run_command(f"disconnect {mac_address}")
        
        # Invalidate cache
        self.invalidate_cache(f"info_{mac_address}")
        
        return "Successful disconnected" in output
        
    def pair_device(self, mac_address: str) -> Tuple[bool, Optional[str]]:
        """Pair with a Bluetooth device."""
        output = self._run_command(f"pair {mac_address}")
        
        # Invalidate cache
        self.invalidate_cache(f"info_{mac_address}")
        
        if "Pairing successful" in output:
            return True, None
        else:
            # Extract error message if any
            error = "Unknown pairing error"
            if "Failed to pair" in output:
                error_parts = output.split("Failed to pair:")
                if len(error_parts) > 1:
                    error = error_parts[1].strip()
            return False, error
        
    def unpair_device(self, mac_address: str) -> bool:
        """Unpair from a Bluetooth device."""
        output = self._run_command(f"remove {mac_address}")
        
        # Invalidate multiple caches
        self.invalidate_cache(f"info_{mac_address}")
        self.invalidate_cache("devices")
        
        return "Device has been removed" in output
        
    def trust_device(self, mac_address: str) -> bool:
        """Trust a Bluetooth device."""
        output = self._run_command(f"trust {mac_address}")
        
        # Invalidate cache
        self.invalidate_cache(f"info_{mac_address}")
        
        return "trust succeeded" in output
        
    def untrust_device(self, mac_address: str) -> bool:
        """Untrust a Bluetooth device."""
        output = self._run_command(f"untrust {mac_address}")
        
        # Invalidate cache
        self.invalidate_cache(f"info_{mac_address}")
        
        return "untrust succeeded" in output
        
    def is_adapter_available(self) -> bool:
        """Check if Bluetooth adapter is available."""
        output = self._cached_run("show")
        return self.parser.parse_controller_availability(output)