#!/usr/bin/env python3

import subprocess
import time
import re
import threading
from typing import List, Optional, Dict, Any

from models.wifi_network import WiFiNetwork
from tools.services.wifi_service import WiFiService
from tools.parsers.wifi_parser import WiFiParser
from utils.logger import Logger, LogLevel


class NetworkManagerService(WiFiService):
    """Implementation of WiFiService using NetworkManager command-line interface (nmcli)."""
    
    def __init__(self, logging: Logger):
        self.logging = logging
        self.parser = WiFiParser(logging)
        self._cache = {}
        self._cache_ttl = 5  # seconds
        self._cache_timestamps = {}
        self._lock = threading.RLock()
        
    def _run_command(self, command: str) -> str:
        """Run a shell command and return its output.
        
        Args:
            command (str): Command to run.
            
        Returns:
            str: Command output.
        """
        try:
            self.logging.log(LogLevel.Debug, f"Running command: {command}")
            output = subprocess.check_output(
                command, 
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
        """Get the current power state of the WiFi adapter."""
        output = self._cached_run("nmcli radio wifi")
        return self.parser.parse_power_state(output)
        
    def set_power_state(self, state: bool) -> bool:
        """Set the power state of the WiFi adapter."""
        state_str = "on" if state else "off"
        output = self._run_command(f"nmcli radio wifi {state_str}")
        
        # Invalidate cache after changing power state
        self.invalidate_cache("nmcli radio wifi")
        
        # Check if command succeeded (empty output typically means success)
        # Also invalidate networks cache if turning on
        if state:
            self.invalidate_cache("nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE dev wifi list")
        
        return output.strip() == ""
        
    def get_networks(self) -> List[WiFiNetwork]:
        """Get list of available WiFi networks."""
        # Rescan networks first to ensure we have up-to-date list
        self._run_command("nmcli device wifi rescan")
        
        # Wait a moment for scan to complete
        time.sleep(1)
        
        # Get network list with specific fields
        output = self._cached_run("nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE dev wifi list")
        return self.parser.parse_network_list(output)
        
    def get_network_info(self, ssid: str) -> Optional[WiFiNetwork]:
        """Get detailed information about a specific network."""
        # Escape single quotes in SSID for shell command
        escaped_ssid = ssid.replace("'", "'\\''")
        
        # First check if this is a saved connection
        conn_info = self._cached_run(f"nmcli -t connection show '{escaped_ssid}'", f"conn_info_{ssid}")
        
        if "Error: " not in conn_info:
            # It's a saved connection
            return self.parser.parse_detailed_network_info(conn_info, ssid)
        
        # Try to get info from available networks
        networks = self.get_networks()
        network = next((n for n in networks if n.ssid == ssid), None)
        
        return network
        
    def connect_network(self, ssid: str, password: Optional[str] = None, save: bool = True) -> bool:
        """Connect to a WiFi network."""
        # Escape single quotes in SSID for shell command
        escaped_ssid = ssid.replace("'", "'\\''")
        
        if password is None:
            # Try to connect to a saved network
            output = self._run_command(f"nmcli connection up '{escaped_ssid}'")
            success = "successfully activated" in output.lower()
        else:
            # Connect with password
            escaped_password = password.replace("'", "'\\''")
            if save:
                output = self._run_command(
                    f"nmcli device wifi connect '{escaped_ssid}' password '{escaped_password}'"
                )
            else:
                output = self._run_command(
                    f"nmcli --ask device wifi connect '{escaped_ssid}' password '{escaped_password}' name '{escaped_ssid}-temp'"
                )
            success = "successfully activated" in output.lower()
        
        # Invalidate caches
        self.invalidate_cache(f"conn_info_{ssid}")
        self.invalidate_cache("nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE dev wifi list")
        
        return success
        
    def disconnect_network(self, ssid: str) -> bool:
        """Disconnect from a WiFi network."""
        # First check if the network is actually connected
        networks = self.get_networks()
        connected_network = next((n for n in networks if n.connected), None)
        
        if not connected_network or connected_network.ssid != ssid:
            # Not connected to this network
            return False
        
        # Find the connection UUID or interface
        conn_info = self._cached_run("nmcli -t -f NAME,UUID,DEVICE connection show --active", "active_connections")
        
        # Look for the connection with this SSID
        for line in conn_info.split('\n'):
            if line.startswith(f"{ssid}:"):
                parts = line.split(':')
                if len(parts) >= 3:
                    uuid = parts[1]
                    device = parts[2]
                    
                    # Try disconnecting by UUID
                    output = self._run_command(f"nmcli connection down '{uuid}'")
                    
                    # If that fails, try disconnecting the device
                    if "successfully deactivated" not in output.lower():
                        output = self._run_command(f"nmcli device disconnect {device}")
                    
                    success = "successfully deactivated" in output.lower()
                    
                    # Invalidate caches
                    self.invalidate_cache(f"conn_info_{ssid}")
                    self.invalidate_cache("nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE dev wifi list")
                    self.invalidate_cache("active_connections")
                    
                    return success
        
        # If we got here, couldn't find the connection to disconnect
        return False
        
    def forget_network(self, ssid: str) -> bool:
        """Remove saved information about a WiFi network."""
        # Escape single quotes in SSID for shell command
        escaped_ssid = ssid.replace("'", "'\\''")
        
        # Delete the connection profile
        output = self._run_command(f"nmcli connection delete '{escaped_ssid}'")
        
        # Invalidate caches
        self.invalidate_cache(f"conn_info_{ssid}")
        self.invalidate_cache("nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE dev wifi list")
        self.invalidate_cache("nmcli connection show")
        
        return "successfully deleted" in output.lower()
        
    def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed information about the current WiFi connection."""
        result = {}
        
        # Get active connections
        conn_output = self._cached_run("nmcli -t connection show --active", "active_connection_list")
        
        # Find WiFi connection
        wifi_conn = None
        for line in conn_output.split('\n'):
            if not line:
                continue
                
            # Check connection type by getting details
            conn_name = line.split(':')[0] if ':' in line else line.strip()
            if not conn_name:
                continue
                
            # Escape connection name
            escaped_conn_name = conn_name.replace("'", "'\\''")
            
            # Get connection details
            conn_details = self._cached_run(
                f"nmcli -t connection show '{escaped_conn_name}'", 
                f"conn_details_{conn_name}"
            )
            
            if "802-11-wireless" in conn_details:
                wifi_conn = conn_name
                result = self.parser.parse_connection_info(conn_details)
                break
                
        # Add device statistics
        if wifi_conn:
            # Get active device
            device_match = re.search(r'GENERAL\.DEVICES:\s*(\S+)', 
                self._cached_run(f"nmcli -t connection show '{wifi_conn}'", f"conn_device_{wifi_conn}")
            )
            
            if device_match:
                device = device_match.group(1)
                result["device"] = device
                
                # Get device information
                device_info = self._cached_run(f"nmcli -t device show {device}", f"device_info_{device}")
                
                # Parse IP information from device info if not already present
                if "ip_address" not in result:
                    ip_match = re.search(r'IP4\.ADDRESS\[1\]:\s*([0-9.]+)/\d+', device_info)
                    if ip_match:
                        result["ip_address"] = ip_match.group(1)
        
        return result
        
    def get_saved_networks(self) -> List[str]:
        """Get list of saved WiFi networks."""
        saved_networks = []
        
        conn_output = self._cached_run("nmcli -t -f NAME,TYPE connection show", "saved_connections")
        
        for line in conn_output.split('\n'):
            if not line or ':' not in line:
                continue
                
            parts = line.split(':')
            if len(parts) >= 2 and parts[1].strip() == "802-11-wireless":
                saved_networks.append(parts[0].strip())
                
        return saved_networks
    
    def get_network_speed(self) -> Dict[str, int]:
        """Get current network upload and download speeds."""
        result = {"rx_bytes": 0, "tx_bytes": 0, "wifi_supported": False}
        
        try:
            # Get active WiFi interface
            device_output = self._cached_run("nmcli -t -f DEVICE,TYPE device status", "wifi_device")
            
            wifi_device = None
            for line in device_output.split('\n'):
                if ':wifi' in line:
                    wifi_device = line.split(':')[0]
                    result["wifi_supported"] = True
                    break
            
            if not wifi_device:
                return result
                
            # Get rx/tx bytes from /proc/net/dev
            net_dev = self._cached_run("cat /proc/net/dev", "net_dev", use_cache=False)
            
            for line in net_dev.split('\n'):
                if wifi_device in line:
                    # Format: Interface: rx_bytes ... tx_bytes ...
                    fields = line.split()
                    if len(fields) >= 10:
                        result["rx_bytes"] = int(fields[1])
                        result["tx_bytes"] = int(fields[9])
                    break
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error getting network speed: {e}")
            
        return result
    
    def is_adapter_available(self) -> bool:
        """Check if WiFi adapter is available."""
        device_output = self._cached_run("nmcli -t -f DEVICE,TYPE device", "device_check")
        
        for line in device_output.split('\n'):
            if ':wifi' in line:
                return True
                
        return False