#!/usr/bin/env python3

import subprocess
import gi  # type: ignore
from better_control.utils.logger import LogLevel, Logger
from pathlib import Path
from better_control.tools.wifi import generate_wifi_qrcode, get_connection_info

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # type: ignore


class QRCodeDialog(Gtk.Dialog):
    def __init__(self, parent, qr_code_path):
        super().__init__(title="WiFi QR Code", transient_for=parent, flags=0)
        self.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        box = self.get_content_area()
        box.set_spacing(10)
        
        if Path(qr_code_path).name == "error.png":
            error_label = Gtk.Label(label="Failed to generate QR code")
            box.add(error_label)
        else:
            image = Gtk.Image.new_from_file(qr_code_path)
            box.add(image)
        
        self.show_all()


class WiFiNetworkRow(Gtk.ListBoxRow):
    def __init__(self, network_info, logging: Logger, parent_window=None):
        super().__init__()
        self.set_margin_top(5)
        self.set_margin_bottom(5)
        self.set_margin_start(10)
        self.set_margin_end(10)
        self.parent_window = parent_window
        self.logging = logging

        parts = network_info.split()
        self.is_connected = "*" in parts[0]

        self.ssid = self._extract_ssid(parts, logging)
        self.security = self._extract_security(network_info)
        self.qr_button = Gtk.Button.new_from_icon_name("insert-image-symbolic", Gtk.IconSize.BUTTON)
        self.qr_button.connect("clicked", self._on_qr_button_clicked)
        self.qr_button.set_tooltip_text("Generate QR Code")
        signal_value = self._extract_signal(parts, logging)
        self.signal_strength = f"{signal_value}%" if signal_value > 0 else "0%"

        icon_name = self._determine_signal_icon(signal_value)
        security_icon = self._determine_security_icon()

        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.add(container)

        wifi_icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        container.pack_start(wifi_icon, False, False, 0)

        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)

        ssid_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        ssid_label = Gtk.Label(label=self.ssid)
        ssid_label.set_halign(Gtk.Align.START)
        if self.is_connected:
            ssid_label.set_markup(f"<b>{self.ssid}</b>")
        ssid_box.pack_start(ssid_label, True, True, 0)

        if self.is_connected:
            connected_label = Gtk.Label(label=" (Connected)")
            connected_label.get_style_context().add_class("success-label")
            ssid_box.pack_start(connected_label, False, False, 0)

        left_box.pack_start(ssid_box, False, False, 0)

        details_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        security_image = Gtk.Image.new_from_icon_name(
            security_icon, Gtk.IconSize.SMALL_TOOLBAR
        )
        details_box.pack_start(security_image, False, False, 0)

        security_label = Gtk.Label(label=self.security)
        security_label.set_halign(Gtk.Align.START)
        security_label.get_style_context().add_class("dim-label")
        details_box.pack_start(security_label, False, False, 0)

        left_box.pack_start(details_box, False, False, 0)

        container.pack_start(left_box, True, True, 0)

        signal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        signal_box.set_halign(Gtk.Align.END)

        signal_label = Gtk.Label(label=self.signal_strength)
        signal_box.pack_start(signal_label, False, False, 0)

        if self.is_connected:
            container.pack_end(self.qr_button, False, False, 0)
        container.pack_end(signal_box, False, False, 0)

        self.original_network_info = network_info

    def _on_qr_button_clicked(self, button):
        """Handle QR code button click"""
        if not self.is_connected:
            return

        conn_info = get_connection_info(self.ssid, self.logging)
        password = conn_info.get("password", "")
        security = conn_info.get("802-11-wireless-security.key-mgmt", "none").upper()

        qr_path = generate_wifi_qrcode(self.ssid, password, security, self.logging)
        QRCodeDialog(self.parent_window, qr_path)

    def _extract_ssid(self, parts, logging):
        if len(parts) <= 1:
            return "Unknown"

        if self.is_connected:
            try:
                active_connections = subprocess.getoutput(
                    "nmcli -t -f NAME,DEVICE connection show --active"
                ).split("\n")
                for conn in active_connections:
                    if ":" in conn:
                        name = conn.split(":")[0]
                        conn_type = subprocess.getoutput(
                            f"nmcli -t -f TYPE connection show '{name}'"
                        )
                        if "wifi" in conn_type:
                            return name
                return parts[1]
            except Exception as e:
                logging.log(
                    LogLevel.Error, f"Error getting active connection name: {e}"
                )
                return parts[1]
        else:
            return parts[1]

    def _extract_security(self, network_info):
        if "WPA2" in network_info:
            return "WPA2"
        elif "WPA3" in network_info:
            return "WPA3"
        elif "WPA" in network_info:
            return "WPA"
        elif "WEP" in network_info:
            return "WEP"
        else:
            return "Open"

    def _extract_signal(self, parts, logging):
        signal_value = 0
        try:
            if len(parts) > 6 and parts[6].isdigit():
                signal_value = int(parts[6])
            else:
                for i, p in enumerate(parts):
                    if p.isdigit() and 0 <= int(p) <= 100 and i != 4:
                        signal_value = int(p)
                        break
        except (IndexError, ValueError) as e:
            logging.log(LogLevel.Error, f"Error parsing signal strength from {parts}: {e}")
            signal_value = 0
        return signal_value

    def _determine_signal_icon(self, signal_value):
        if signal_value >= 80:
            return "network-wireless-signal-excellent-symbolic"
        elif signal_value >= 60:
            return "network-wireless-signal-good-symbolic"
        elif signal_value >= 40:
            return "network-wireless-signal-ok-symbolic"
        elif signal_value > 0:
            return "network-wireless-signal-weak-symbolic"
        else:
            return "network-wireless-signal-none-symbolic"

    def _determine_security_icon(self):
        return "network-wireless-encrypted-symbolic" if self.security != "Open" else "network-wireless-symbolic"

    def get_ssid(self):
        return self.ssid

    def get_security(self):
        return self.security

    def get_original_network_info(self):
        return self.original_network_info

    def is_secured(self):
        return self.security != "Open"
