#!/usr/bin/env python3

from typing import Optional, Dict, Any, Callable
from models.bluetooth_device import BluetoothDevice


class BluetoothDeviceViewModel:
    """View model for converting BluetoothDevice models to UI-ready data."""
    
    def __init__(self, device: BluetoothDevice):
        self.device = device
        
    @property
    def mac_address(self) -> str:
        """Get device MAC address."""
        return self.device.mac_address
        
    @property
    def name(self) -> str:
        """Get device name, possibly with markup."""
        if self.device.connected:
            return f"<b>{self.device.name}</b>"
        return self.device.name
        
    @property
    def connected(self) -> bool:
        """Get connection status."""
        return self.device.connected
        
    @property
    def paired(self) -> bool:
        """Get pairing status."""
        return self.device.paired
        
    @property
    def trusted(self) -> bool:
        """Get trusted status."""
        return self.device.trusted
        
    @property
    def device_type(self) -> str:
        """Get device type."""
        return self.device.device_type
        
    @property
    def friendly_device_type(self) -> str:
        """Get user-friendly device type name."""
        return self.device.friendly_device_type
        
    @property
    def icon_name(self) -> str:
        """Get icon name for the device type."""
        return self.device.icon_name
        
    @property
    def battery_percentage(self) -> Optional[int]:
        """Get battery percentage if available."""
        return self.device.battery_percentage
        
    @property
    def battery_level_icon(self) -> str:
        """Get battery level icon suffix based on percentage."""
        if not self.device.battery_percentage:
            return "missing"
        if self.device.battery_percentage >= 90:
            return "100"
        elif self.device.battery_percentage >= 70:
            return "080"
        elif self.device.battery_percentage >= 50:
            return "060"
        elif self.device.battery_percentage >= 30:
            return "040"
        elif self.device.battery_percentage >= 10:
            return "020"
        else:
            return "000"
            
    @property
    def status_label(self) -> str:
        """Get a status label for the device."""
        if self.device.connected:
            status = "Connected"
            if self.device.battery_percentage is not None:
                status += f" • {self.device.battery_percentage}%"
            return status
        elif self.device.paired:
            return "Paired"
        return "Not connected"
        
    @property
    def has_error(self) -> bool:
        """Check if device has an error."""
        return self.device.error is not None
        
    @property
    def error_message(self) -> Optional[str]:
        """Get error message if any."""
        return self.device.error
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert view model to dictionary for UI templates."""
        return {
            "mac_address": self.mac_address,
            "name": self.name,
            "connected": self.connected,
            "paired": self.paired,
            "trusted": self.trusted,
            "device_type": self.device_type,
            "friendly_type": self.friendly_device_type,
            "icon_name": self.icon_name,
            "battery": self.battery_percentage,
            "battery_icon": self.battery_level_icon,
            "status": self.status_label,
            "has_error": self.has_error,
            "error": self.error_message
        }