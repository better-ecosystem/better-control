#!/usr/bin/env python3

import gi

from utils.translations import English, Spanish # type: ignore
from ui.view_models.bluetooth_device_view_model import BluetoothDeviceViewModel
from models.bluetooth_device import BluetoothDevice

gi.require_version("Gtk", "3.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk, Pango # type: ignore

class BluetoothDeviceRow(Gtk.ListBoxRow):
    def __init__(self, device: BluetoothDevice, txt: English|Spanish):
        super().__init__()
        self.txt = txt
        
        # Convert the pure model to a view model
        self.view_model = BluetoothDeviceViewModel(device)
        
        # Configure row styling
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(16)  # Increased from 10
        self.set_margin_end(16)    # Increased from 10
        
        # Add CSS class for styling
        context = self.get_style_context()
        context.add_class("device-row")

        # Main container for the row with increased spacing
        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)  # Increased from 10
        container.set_margin_top(6)     # Added internal padding
        container.set_margin_bottom(6)  # Added internal padding
        self.add(container)

        # Device icon based on type - make it slightly larger
        device_icon = Gtk.Image.new_from_icon_name(self.view_model.icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        container.pack_start(device_icon, False, False, 0)

        # Left side with device name and type
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)  # Increased from 3
        left_box.set_margin_start(4)  # Add a bit of margin after icon

        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)  # Increased from 5
        name_label = Gtk.Label()
        name_label.set_markup(self.view_model.name)
        name_label.set_halign(Gtk.Align.START)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_label.set_max_width_chars(20)
        
        name_status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)  # Added spacing
        name_status_box.pack_start(name_label, False, True, 0)

        # Show connection status if connected
        if self.view_model.connected:
            status_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)  # Increased from 3
            status_container.get_style_context().add_class("device-status-container")
            
            # Connection indicator
            connection_indicator = Gtk.DrawingArea()
            connection_indicator.set_size_request(14, 14)  # Increased from 12,12
            connection_indicator.get_style_context().add_class("connection-indicator")
            connection_indicator.get_style_context().add_class("connected")
            status_container.pack_start(connection_indicator, False, False, 0)
            
            # Status text with battery if available
            status_text = self.txt.connected
            if self.view_model.battery_percentage is not None:
                status_text += f" • {self.view_model.battery_percentage}%"
            status_label = Gtk.Label(label=status_text)
            status_label.get_style_context().add_class("status-label")
            status_container.pack_start(status_label, False, False, 0)
            
            name_status_box.pack_start(status_container, False, False, 6)  # Increased from 4
        
        name_box.pack_start(name_status_box, True, True, 0)
        left_box.pack_start(name_box, False, False, 0)

        # Device details box
        details_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)  # Increased from 5

        # Device type label
        type_label = Gtk.Label(label=self.view_model.friendly_device_type)
        type_label.set_halign(Gtk.Align.START)
        type_label.get_style_context().add_class("dim-label")
        details_box.pack_start(type_label, False, False, 0)

        # MAC address label
        mac_label = Gtk.Label(label=self.view_model.mac_address)
        mac_label.set_halign(Gtk.Align.START)
        mac_label.get_style_context().add_class("dim-label")
        details_box.pack_start(mac_label, False, False, 10)

        left_box.pack_start(details_box, False, False, 0)
        
        # Show error message if any
        if self.view_model.has_error:
            error_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)  # Increased from 5
            error_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
            error_box.pack_start(error_icon, False, False, 0)
            
            error_label = Gtk.Label(label=self.view_model.error_message)
            error_label.get_style_context().add_class("error-text")
            error_box.pack_start(error_label, False, False, 0)
            
            left_box.pack_start(error_box, False, False, 4)  # Increased from 3

        container.pack_start(left_box, True, True, 0)

        # Add connect/disconnect buttons with improved spacing
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)  # Increased from 5
        button_box.set_margin_start(8)  # Add margin before buttons

        self.connect_button = Gtk.Button(label=self.txt.connect)
        self.connect_button.set_sensitive(not self.view_model.connected)
        if not self.view_model.connected:
            self.connect_button.get_style_context().add_class("suggested-action")  # Highlight connect button
        button_box.pack_end(self.connect_button, False, False, 0)

        self.disconnect_button = Gtk.Button(label=self.txt.disconnect)
        self.disconnect_button.set_sensitive(self.view_model.connected)
        button_box.pack_end(self.disconnect_button, False, False, 0)

        container.pack_end(button_box, False, False, 0)
        
    def get_mac_address(self) -> str:
        """Get device MAC address."""
        return self.view_model.mac_address

    def get_device_name(self) -> str:
        """Get device name."""
        return self.view_model.device.name

    def get_is_connected(self) -> bool:
        """Get connection status."""
        return self.view_model.connected
