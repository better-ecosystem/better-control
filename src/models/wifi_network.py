#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class WiFiNetwork:
    """Pure data model representing a WiFi network."""
    ssid: str
    signal_strength: int = 0  # 0-100%
    security_type: str = "unknown"  # "WPA2", "WPA3", "WPA", "WEP", "Open"
    connected: bool = False
    frequency: Optional[float] = None  # in GHz (2.4, 5.0)
    channel: Optional[int] = None
    rate: Optional[str] = None  # e.g. "54 Mb/s"
    bssid: Optional[str] = None  # MAC address of access point
    mode: Optional[str] = None  # "Infrastructure", "Ad-Hoc", etc.
    error: Optional[str] = None
    raw_data: Optional[str] = None  # Original data for debugging
    
    @property
    def is_secured(self) -> bool:
        """Return True if the network uses encryption."""
        return self.security_type != "Open"
    
    @property
    def signal_icon_name(self) -> str:
        """Return appropriate signal strength icon name."""
        if self.signal_strength >= 80:
            return "network-wireless-signal-excellent-symbolic"
        elif self.signal_strength >= 60:
            return "network-wireless-signal-good-symbolic"
        elif self.signal_strength >= 40:
            return "network-wireless-signal-ok-symbolic"
        elif self.signal_strength > 0:
            return "network-wireless-signal-weak-symbolic"
        else:
            return "network-wireless-signal-none-symbolic"
    
    @property
    def security_icon_name(self) -> str:
        """Return appropriate security icon name."""
        if self.is_secured:
            return "network-wireless-encrypted-symbolic"
        else:
            return "network-wireless-symbolic"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert network to dictionary for serialization."""
        return {
            "ssid": self.ssid,
            "signal": self.signal_strength,
            "security": self.security_type,
            "in_use": self.connected,
            "frequency": self.frequency,
            "channel": self.channel,
            "rate": self.rate,
            "bssid": self.bssid,
            "mode": self.mode,
            "raw_data": self.raw_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WiFiNetwork':
        """Create network from dictionary representation."""
        return cls(
            ssid=data.get('ssid', 'Unknown Network'),
            signal_strength=int(data.get('signal', 0)),
            security_type=data.get('security', 'unknown'),
            connected=data.get('in_use', False),
            frequency=data.get('frequency'),
            channel=data.get('channel'),
            rate=data.get('rate'),
            bssid=data.get('bssid'),
            mode=data.get('mode'),
            raw_data=data.get('raw_data')
        )
