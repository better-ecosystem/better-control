#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any

from models.bluetooth_device import BluetoothDevice
from utils.logger import Logger


class BluetoothService(ABC):
    """Interface for Bluetooth operations."""
    
    @abstractmethod
    def get_power_state(self) -> bool:
        """Get the current power state of the Bluetooth adapter.
        
        Returns:
            bool: True if Bluetooth is powered on, False otherwise.
        """
        pass
        
    @abstractmethod
    def set_power_state(self, state: bool) -> bool:
        """Set the power state of the Bluetooth adapter.
        
        Args:
            state (bool): True to power on, False to power off.
            
        Returns:
            bool: True if operation was successful, False otherwise.
        """
        pass
        
    @abstractmethod
    def get_devices(self) -> List[BluetoothDevice]:
        """Get list of known Bluetooth devices.
        
        Returns:
            List[BluetoothDevice]: List of known devices.
        """
        pass
        
    @abstractmethod
    def scan_for_devices(self, timeout_seconds: int = 10) -> List[BluetoothDevice]:
        """Scan for available Bluetooth devices.
        
        Args:
            timeout_seconds (int): Duration of scan in seconds.
            
        Returns:
            List[BluetoothDevice]: List of discovered devices.
        """
        pass
        
    @abstractmethod
    def get_device_info(self, mac_address: str) -> Optional[BluetoothDevice]:
        """Get detailed information about a specific device.
        
        Args:
            mac_address (str): MAC address of the device.
            
        Returns:
            Optional[BluetoothDevice]: Device information if found, None otherwise.
        """
        pass
        
    @abstractmethod
    def connect_device(self, mac_address: str) -> bool:
        """Connect to a Bluetooth device.
        
        Args:
            mac_address (str): MAC address of the device.
            
        Returns:
            bool: True if connection was successful, False otherwise.
        """
        pass
        
    @abstractmethod
    def disconnect_device(self, mac_address: str) -> bool:
        """Disconnect from a Bluetooth device.
        
        Args:
            mac_address (str): MAC address of the device.
            
        Returns:
            bool: True if disconnection was successful, False otherwise.
        """
        pass
        
    @abstractmethod
    def pair_device(self, mac_address: str) -> Tuple[bool, Optional[str]]:
        """Pair with a Bluetooth device.
        
        Args:
            mac_address (str): MAC address of the device.
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        pass
        
    @abstractmethod
    def unpair_device(self, mac_address: str) -> bool:
        """Unpair from a Bluetooth device.
        
        Args:
            mac_address (str): MAC address of the device.
            
        Returns:
            bool: True if unpairing was successful, False otherwise.
        """
        pass
        
    @abstractmethod
    def trust_device(self, mac_address: str) -> bool:
        """Trust a Bluetooth device.
        
        Args:
            mac_address (str): MAC address of the device.
            
        Returns:
            bool: True if operation was successful, False otherwise.
        """
        pass
        
    @abstractmethod
    def untrust_device(self, mac_address: str) -> bool:
        """Untrust a Bluetooth device.
        
        Args:
            mac_address (str): MAC address of the device.
            
        Returns:
            bool: True if operation was successful, False otherwise.
        """
        pass
        
    @abstractmethod
    def is_adapter_available(self) -> bool:
        """Check if Bluetooth adapter is available.
        
        Returns:
            bool: True if adapter is available, False otherwise.
        """
        pass