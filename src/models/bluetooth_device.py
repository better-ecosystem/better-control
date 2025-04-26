#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class BluetoothDevice:
    """Pure data model representing a Bluetooth device."""
    mac_address: str
    name: str
    connected: bool = False
    paired: bool = False
    trusted: bool = False
    device_type: str = "unknown"
    device_path: Optional[str] = None
    battery_percentage: Optional[int] = None
    rssi: Optional[int] = None
    error: Optional[str] = None
    
    @property
    def friendly_device_type(self) -> str:
        """Return user-friendly device type name."""
        type_names = {
            "audio-headset": "Headset",
            "audio-headphones": "Headphones",
            "audio-card": "Speaker",
            "input-keyboard": "Keyboard",
            "input-mouse": "Mouse",
            "input-gaming": "Game Controller",
            "phone": "Phone",
            "unknown": "Device",
        }
        return type_names.get(self.device_type, "Bluetooth Device")
    
    @property
    def icon_name(self) -> str:
        """Return appropriate icon based on device type."""
        if self.device_type == "audio-headset" or self.device_type == "audio-headphones":
            return "audio-headset-symbolic"
        elif self.device_type == "audio-card":
            return "audio-speakers-symbolic"
        elif self.device_type == "input-keyboard":
            return "input-keyboard-symbolic"
        elif self.device_type == "input-mouse":
            return "input-mouse-symbolic"
        elif self.device_type == "input-gaming":
            return "input-gaming-symbolic"
        elif self.device_type == "phone":
            return "phone-symbolic"
        else:
            return "bluetooth-symbolic"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert device to dictionary for serialization."""
        return {
            "mac": self.mac_address,
            "name": self.name,
            "connected": self.connected,
            "paired": self.paired,
            "trusted": self.trusted,
            "icon": self.device_type,
            "path": self.device_path,
            "battery": self.battery_percentage,
            "rssi": self.rssi
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BluetoothDevice':
        """Create device from dictionary representation."""
        return cls(
            mac_address=data.get('mac', ''),
            name=data.get('name', 'Unknown Device'),
            connected=data.get('connected', False),
            paired=data.get('paired', False),
            trusted=data.get('trusted', False),
            device_type=data.get('icon', 'unknown'),
            device_path=data.get('path'),
            battery_percentage=data.get('battery'),
            rssi=data.get('rssi')
        )
