#!/usr/bin/env python3

import re
from typing import Dict, List, Optional, Any

from models.wifi_network import WiFiNetwork
from utils.logger import Logger, LogLevel


class WiFiParser:
    """Parser for WiFi command outputs from nmcli and other tools."""
    
    def __init__(self, logging: Logger):
        self.logging = logging
    
    def parse_network_list(self, output: str) -> List[WiFiNetwork]:
        """Parse the output of 'nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE dev wifi list' command.
        
        Args:
            output (str): Command output from nmcli device wifi list.
            
        Returns:
            List[WiFiNetwork]: List of parsed WiFi networks.
        """
        networks = []
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            try:
                # Split by colon which is the delimiter in tab mode (-t)
                parts = line.split(':')
                if len(parts) < 3:
                    continue
                
                ssid = parts[0]
                if not ssid:
                    continue  # Skip networks with empty SSIDs
                
                # Parse signal strength
                signal_strength = 0
                if len(parts) > 1 and parts[1].isdigit():
                    signal_strength = int(parts[1])
                
                # Parse security
                security_type = "Open"
                if len(parts) > 2 and parts[2]:
                    if "WPA2" in parts[2]:
                        security_type = "WPA2"
                    elif "WPA3" in parts[2]:
                        security_type = "WPA3"
                    elif "WPA" in parts[2]:
                        security_type = "WPA"
                    elif "WEP" in parts[2]:
                        security_type = "WEP"
                
                # Check if network is in use
                connected = False
                if len(parts) > 3:
                    connected = parts[3] == "*"
                
                network = WiFiNetwork(
                    ssid=ssid,
                    signal_strength=signal_strength,
                    security_type=security_type,
                    connected=connected,
                    raw_data=line
                )
                networks.append(network)
                
            except Exception as e:
                self.logging.log(LogLevel.Error, f"Failed to parse network line: {line}, Error: {e}")
        
        return networks
    
    def parse_detailed_network_info(self, output: str, ssid: str) -> Optional[WiFiNetwork]:
        """Parse detailed information about a specific network.
        
        Args:
            output (str): Command output from nmcli connection show or similar command.
            ssid (str): SSID of the network.
            
        Returns:
            Optional[WiFiNetwork]: Parsed network or None if parsing failed.
        """
        if not output:
            return None
            
        try:
            # Base network object
            network = WiFiNetwork(ssid=ssid)
            
            # Extract connection status
            network.connected = "GENERAL.STATE: activated" in output
            
            # Extract frequency if available
            freq_match = re.search(r'GENERAL\.FREQUENCY:\s*(\d+)\s*MHz', output)
            if freq_match:
                try:
                    # Convert MHz to GHz for display
                    freq_mhz = int(freq_match.group(1))
                    network.frequency = round(freq_mhz / 1000.0, 1)
                except ValueError:
                    pass
            
            # Extract channel if available
            channel_match = re.search(r'GENERAL\.CHAN:\s*(\d+)', output)
            if channel_match:
                try:
                    network.channel = int(channel_match.group(1))
                except ValueError:
                    pass
            
            # Extract rate if available
            rate_match = re.search(r'GENERAL\.RATE:\s*([\d.]+)\s*Mb/s', output)
            if rate_match:
                network.rate = f"{rate_match.group(1)} Mb/s"
            
            # Extract BSSID (MAC address of access point) if available
            bssid_match = re.search(r'GENERAL\.HWADDR:\s*([0-9A-F:]{17})', output, re.IGNORECASE)
            if bssid_match:
                network.bssid = bssid_match.group(1)
            
            # Extract security settings
            if "802-11-wireless-security" in output:
                security_lines = re.findall(r'802-11-wireless-security\.key-mgmt:\s*(\S+)', output)
                if security_lines:
                    security_type = security_lines[0]
                    if "wpa-psk" in security_type.lower():
                        network.security_type = "WPA"
                    elif "sae" in security_type.lower():
                        network.security_type = "WPA3"
                    elif "wep" in security_type.lower():
                        network.security_type = "WEP"
                    elif "none" in security_type.lower():
                        network.security_type = "Open"
            
            # Store raw data for debugging
            network.raw_data = output
            
            return network
            
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed to parse detailed network info: {e}")
            return None
    
    def parse_power_state(self, output: str) -> bool:
        """Parse the output of nmcli radio wifi command.
        
        Args:
            output (str): Command output from nmcli radio wifi.
            
        Returns:
            bool: True if WiFi is enabled, False otherwise.
        """
        return output.strip().lower() == "enabled"
    
    def parse_connection_info(self, output: str) -> Dict[str, Any]:
        """Parse connection info from various command outputs.
        
        Args:
            output (str): Command output with connection details.
            
        Returns:
            Dict[str, Any]: Dictionary with connection details.
        """
        result = {}
        
        # Parse IP address
        ip_match = re.search(r'IP4\.ADDRESS\[1\]:\s*([0-9.]+)/\d+', output)
        if ip_match:
            result["ip_address"] = ip_match.group(1)
        
        # Parse gateway
        gw_match = re.search(r'IP4\.GATEWAY:\s*([0-9.]+)', output)
        if gw_match:
            result["gateway"] = gw_match.group(1)
        
        # Parse DNS servers
        dns_matches = re.finditer(r'IP4\.DNS\[\d+\]:\s*([0-9.]+)', output)
        dns_servers = [m.group(1) for m in dns_matches]
        if dns_servers:
            result["dns_servers"] = dns_servers
        
        return result
    
    def parse_network_device_status(self, output: str) -> Dict[str, bool]:
        """Parse the output of 'nmcli device' command to check WiFi device status.
        
        Args:
            output (str): Command output from nmcli device.
            
        Returns:
            Dict[str, bool]: Dictionary with device status ('available', 'connected').
        """
        result = {
            "available": False,
            "connected": False
        }
        
        lines = output.strip().split('\n')
        for line in lines:
            if "wifi" in line.lower():
                result["available"] = True
                if "connected" in line.lower():
                    result["connected"] = True
                    
        return result