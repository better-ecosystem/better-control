#!/usr/bin/env python3

import gi

from utils.translations import English, Spanish  # type: ignore
from ui.view_models.wifi_network_view_model import WiFiNetworkViewModel
from models.wifi_network import WiFiNetwork

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # type: ignore


class WiFiNetworkRow(Gtk.ListBoxRow):
    def __init__(self, network: WiFiNetwork, txt: English|Spanish):
        super().__init__()
        self.txt = txt
        
        # Convert the pure model to a view model
        self.view_model = WiFiNetworkViewModel(network)
        
        # Configure row styling
        self.set_margin_top(5)
        self.set_margin_bottom(5)
        self.set_margin_start(10)
        self.set_margin_end(10)

        # Main horizontal container
        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.add(container)

        # Signal strength icon
        wifi_icon = Gtk.Image.new_from_icon_name(self.view_model.signal_icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        container.pack_start(wifi_icon, False, False, 0)

        # Left side with network name and details
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)

        # SSID with connected status if applicable
        ssid_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        ssid_label = Gtk.Label()
        ssid_label.set_markup(self.view_model.ssid)
        ssid_label.set_halign(Gtk.Align.START)
        ssid_box.pack_start(ssid_label, True, True, 0)

        # Show connected label if connected
        if self.view_model.connected:
            connected_label = Gtk.Label(label=f" ({self.txt.connected})")
            connected_label.get_style_context().add_class("success-label")
            ssid_box.pack_start(connected_label, False, False, 0)

        left_box.pack_start(ssid_box, False, False, 0)

        # Network details (security type, frequency)
        details_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        # Security icon
        security_image = Gtk.Image.new_from_icon_name(
            self.view_model.security_icon_name, Gtk.IconSize.SMALL_TOOLBAR
        )
        details_box.pack_start(security_image, False, False, 0)

        # Security type and other details
        details_label = Gtk.Label(label=self.view_model.details_label)
        details_label.set_halign(Gtk.Align.START)
        details_label.get_style_context().add_class("dim-label")
        details_box.pack_start(details_label, False, False, 0)

        left_box.pack_start(details_box, False, False, 0)
        
        # Show error message if any
        if self.view_model.has_error:
            error_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            error_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
            error_box.pack_start(error_icon, False, False, 0)
            
            error_label = Gtk.Label(label=self.view_model.error_message)
            error_label.get_style_context().add_class("error-text")
            error_box.pack_start(error_label, False, False, 0)
            
            left_box.pack_start(error_box, False, False, 3)

        container.pack_start(left_box, True, True, 0)

        # Right side with signal strength percentage
        signal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        signal_box.set_halign(Gtk.Align.END)

        signal_label = Gtk.Label(label=self.view_model.signal_strength_text)
        signal_box.pack_start(signal_label, False, False, 0)

        container.pack_end(signal_box, False, False, 0)
        
        # Add connect button for non-connected networks
        if not self.view_model.connected:
            self.connect_button = Gtk.Button(label=self.txt.connect)
            container.pack_end(self.connect_button, False, False, 0)
        else:
            self.disconnect_button = Gtk.Button(label=self.txt.disconnect)
            container.pack_end(self.disconnect_button, False, False, 0)

    def get_ssid(self) -> str:
        """Get network SSID."""
        return self.view_model.network.ssid

    def get_is_connected(self) -> bool:
        """Get connection status."""
        return self.view_model.connected
        
    def get_security_type(self) -> str:
        """Get security type."""
        return self.view_model.security_type
