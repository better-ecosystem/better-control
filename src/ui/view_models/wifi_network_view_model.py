#!/usr/bin/env python3

from typing import Optional, Dict, Any
from models.wifi_network import WiFiNetwork


class WiFiNetworkViewModel:
    """View model for converting WiFiNetwork models to UI-ready data."""
    
    def __init__(self, network: WiFiNetwork):
        self.network = network
        
    @property
    def ssid(self) -> str:
        """Get network SSID, possibly with markup."""
        if self.network.connected:
            return f"<b>{self.network.ssid}</b>"
        return self.network.ssid
        
    @property
    def connected(self) -> bool:
        """Get connection status."""
        return self.network.connected
        
    @property
    def security_type(self) -> str:
        """Get security type."""
        return self.network.security_type
        
    @property
    def is_secured(self) -> bool:
        """Check if network uses encryption."""
        return self.network.is_secured
        
    @property
    def signal_strength(self) -> int:
        """Get signal strength percentage."""
        return self.network.signal_strength
        
    @property
    def signal_strength_text(self) -> str:
        """Get signal strength as text."""
        return f"{self.network.signal_strength}%"
        
    @property
    def signal_icon_name(self) -> str:
        """Get icon name for signal strength."""
        return self.network.signal_icon_name
        
    @property
    def security_icon_name(self) -> str:
        """Get icon name for security type."""
        return self.network.security_icon_name
        
    @property
    def frequency(self) -> Optional[float]:
        """Get network frequency in GHz."""
        return self.network.frequency
        
    @property
    def frequency_text(self) -> Optional[str]:
        """Get formatted frequency text."""
        if self.network.frequency is not None:
            return f"{self.network.frequency} GHz"
        return None
        
    @property
    def channel(self) -> Optional[int]:
        """Get network channel."""
        return self.network.channel
        
    @property
    def status_label(self) -> str:
        """Get a status label for the network."""
        if self.network.connected:
            return "Connected"
        return ""
        
    @property
    def details_label(self) -> str:
        """Generate a details label with security and frequency if available."""
        parts = [self.network.security_type]
        
        if self.network.frequency is not None:
            parts.append(f"{self.network.frequency} GHz")
            
        if self.network.channel is not None:
            parts.append(f"Ch {self.network.channel}")
            
        return " • ".join(parts)
        
    @property
    def has_error(self) -> bool:
        """Check if network has an error."""
        return self.network.error is not None
        
    @property
    def error_message(self) -> Optional[str]:
        """Get error message if any."""
        return self.network.error
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert view model to dictionary for UI templates."""
        return {
            "ssid": self.ssid,
            "connected": self.connected,
            "security_type": self.security_type,
            "is_secured": self.is_secured,
            "signal_strength": self.signal_strength,
            "signal_text": self.signal_strength_text,
            "signal_icon": self.signal_icon_name,
            "security_icon": self.security_icon_name,
            "frequency": self.frequency,
            "frequency_text": self.frequency_text,
            "channel": self.channel,
            "status": self.status_label,
            "details": self.details_label,
            "has_error": self.has_error,
            "error": self.error_message
        }