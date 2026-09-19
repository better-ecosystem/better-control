import subprocess
import gi

from better_control.utils.logger import LogLevel, Logger  # type: ignore

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # type: ignore


class WiFiNetworkRow(Gtk.ListBoxRow):
    def __init__(self, network_info, logging: Logger):
        super().__init__()
        self.logging = logging
        self.set_margin_top(5)
        self.set_margin_bottom(5)
        self.set_margin_start(10)
        self.set_margin_end(10)

        parts = network_info.split()
        self.is_connected = "*" in parts[0]

        self.ssid = self._extract_ssid(parts, network_info)
        self.security = self._extract_security(network_info)
        signal_value = self._extract_signal_strength(parts)

        if signal_value >= 80:
            icon_name = "network-wireless-signal-excellent-symbolic"
        elif signal_value >= 60:
            icon_name = "network-wireless-signal-good-symbolic"
        elif signal_value >= 40:
            icon_name = "network-wireless-signal-ok-symbolic"
        elif signal_value > 0:
            icon_name = "network-wireless-signal-weak-symbolic"
        else:
            icon_name = "network-wireless-signal-none-symbolic"

        if self.security != "Open":
            security_icon = "network-wireless-encrypted-symbolic"
        else:
            security_icon = "network-wireless-symbolic"

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

        container.pack_end(signal_box, False, False, 0)

        self.original_network_info = network_info

    def _extract_ssid(self, parts, network_info):
        if len(parts) > 1:
            if self.is_connected:
                try:
                    active_connections = subprocess.getoutput(
                        "nmcli -t -f NAME,DEVICE connection show --active"
                    ).split("\n")
                    for conn in active_connections:
                        if ":" in conn:
                            conn_name = conn.split(":")[0]
                            conn_type = subprocess.getoutput(
                                f"nmcli -t -f TYPE connection show '{conn_name}'"
                            )
                            if "wifi" in conn_type:
                                return conn_name
                    else:
                        return parts[1]
                except Exception as e:
                    self.logging.log(
                        LogLevel.Error, f"Failed getting active connection name: {e}"
                    )
                    return parts[1]
            else:
                return parts[1]
        else:
            return "Unknown"

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

    def _extract_signal_strength(self, parts):
        signal_value = 0
        try:
            if len(parts) > 6 and parts[6].isdigit():
                signal_value = int(parts[6])
                self.signal_strength = f"{signal_value}%"
            else:
                for i, p in enumerate(parts):
                    if p.isdigit() and 0 <= int(p) <= 100:
                        if i != 4:
                            signal_value = int(p)
                            self.signal_strength = f"{signal_value}%"
                            break
                else:
                    self.signal_strength = "0%"
        except (IndexError, ValueError) as e:
            self.logging.log(
                LogLevel.Error, f"Failed parsing signal strength from {parts}: {e}"
            )
            self.signal_strength = "0%"
            signal_value = 0
        return signal_value

    def get_ssid(self):
        return self.ssid

    def get_security(self):
        return self.security

    def get_original_network_info(self):
        return self.original_network_info

    def is_secured(self):
        return self.security != "Open"
