#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple

from models.wifi_network import WiFiNetwork
from utils.logger import Logger


class WiFiService(ABC):
    """Interface for WiFi operations."""
    
    @abstractmethod
    def get_power_state(self) -> bool:
        """Get the current power state of the WiFi adapter.
        
        Returns:
            bool: True if WiFi is powered on, False otherwise.
        """
        pass
        
    @abstractmethod
    def set_power_state(self, state: bool) -> bool:
        """Set the power state of the WiFi adapter.
        
        Args:
            state (bool): True to power on, False to power off.
            
        Returns:
            bool: True if operation was successful, False otherwise.
        """
        pass
        
    @abstractmethod
    def get_networks(self) -> List[WiFiNetwork]:
        """Get list of available WiFi networks.
        
        Returns:
            List[WiFiNetwork]: List of available networks.
        """
        pass
        
    @abstractmethod
    def get_network_info(self, ssid: str) -> Optional[WiFiNetwork]:
        """Get detailed information about a specific network.
        
        Args:
            ssid (str): SSID of the network.
            
        Returns:
            Optional[WiFiNetwork]: Network information if found, None otherwise.
        """
        pass
        
    @abstractmethod
    def connect_network(self, ssid: str, password: Optional[str] = None, save: bool = True) -> bool:
        """Connect to a WiFi network.
        
        Args:
            ssid (str): SSID of the network.
            password (Optional[str]): Password for secured networks.
            save (bool): Whether to save the network details.
            
        Returns:
            bool: True if connection was successful, False otherwise.
        """
        pass
        
    @abstractmethod
    def disconnect_network(self, ssid: str) -> bool:
        """Disconnect from a WiFi network.
        
        Args:
            ssid (str): SSID of the network.
            
        Returns:
            bool: True if disconnection was successful, False otherwise.
        """
        pass
        
    @abstractmethod
    def forget_network(self, ssid: str) -> bool:
        """Remove saved information about a WiFi network.
        
        Args:
            ssid (str): SSID of the network.
            
        Returns:
            bool: True if operation was successful, False otherwise.
        """
        pass
        
    @abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed information about the current WiFi connection.
        
        Returns:
            Dict[str, Any]: Connection details like speed, IP address, etc.
        """
        pass
        
    @abstractmethod
    def get_saved_networks(self) -> List[str]:
        """Get list of saved WiFi networks.
        
        Returns:
            List[str]: List of saved network SSIDs.
        """
        pass
    
    @abstractmethod
    def get_network_speed(self) -> Dict[str, int]:
        """Get current network upload and download speeds.
        
        Returns:
            Dict[str, int]: Dictionary containing 'rx_bytes' (download) and 'tx_bytes' (upload).
        """
        pass
    
    @abstractmethod
    def is_adapter_available(self) -> bool:
        """Check if WiFi adapter is available.
        
        Returns:
            bool: True if adapter is available, False otherwise.
        """
        pass