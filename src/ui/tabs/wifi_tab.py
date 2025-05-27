#!/usr/bin/env python3

import traceback
import gi # type: ignore
import threading
import requests
from ui.tabs.settings_tab import SettingsTab
from utils.logger import LogLevel, Logger
import subprocess

from utils.settings import load_settings, save_settings
from utils.translations import Translation

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk  # type: ignore
from tools.globals import get_wifi_css

from tools.wifi import (
    get_wifi_status,
    set_wifi_power,
    get_wifi_networks,
    connect_network,
    disconnect_network,
    forget_network,
    get_network_speed,
    get_connection_info,
    generate_wifi_qrcode,
    wifi_supported,
    get_network_details
)

class WiFiTab(Gtk.Box):
    """WiFi settings tab"""

    def __init__(self, logging: Logger, txt: Translation):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        get_wifi_css()
        self.txt = txt
        self.logging = logging
        self.logging.log(LogLevel.Debug, "WiFi tab: Starting initialization")
        
        # Debug container visibility
        self._debug_containers = []
        self.set_margin_start(15)
        self.set_margin_end(15)
        self.set_margin_top(15)
        self.set_margin_bottom(15)
        self.set_hexpand(True)
        self.set_vexpand(True)
        
        # Load settings
        self.settings = load_settings(self.logging)
        
        # Get separator from settings and set default to false
        self.separator_enabled = self.settings.get("enable_separator", False)
         
        settings_tab = SettingsTab(self.logging, self.txt)        
        settings_tab.connect("enable-separator-changed", self.on_enable_separator_changed)
        # Track tab visibility status
        self.tab_visible = False

        if not wifi_supported:
            self.logging.log(LogLevel.Warn, "WiFi is not supported on this machine")

        # Create header box with title and refresh button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header_box.set_hexpand(True)

        # Create title box with icon and label
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Add wifi icon with hover animations
        wifi_icon = Gtk.Image.new_from_icon_name("network-wireless-symbolic", Gtk.IconSize.DIALOG)
        ctx = wifi_icon.get_style_context()
        ctx.add_class("wifi-icon")

        def on_enter(widget, event):
            ctx.add_class("wifi-icon-animate")

        def on_leave(widget, event):
            ctx.remove_class("wifi-icon-animate")

        # Wrap in event box for hover detection
        icon_event_box = Gtk.EventBox()
        icon_event_box.add(wifi_icon)
        icon_event_box.connect("enter-notify-event", on_enter)
        icon_event_box.connect("leave-notify-event", on_leave)

        title_box.pack_start(icon_event_box, False, False, 0)

        # Add title
        wifi_label = Gtk.Label()
        wifi_title = getattr(self.txt, "wifi_title", "WiFi")
        wifi_label.set_markup(f"<span weight='bold' size='large'>{wifi_title}</span>")
        wifi_label.set_halign(Gtk.Align.START)
        title_box.pack_start(wifi_label, False, False, 0)

        header_box.pack_start(title_box, True, True, 0)

        # Add refresh button with expandable animation
        self.refresh_button = Gtk.Button()
        self.refresh_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.refresh_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        self.refresh_label = Gtk.Label(label="Refresh")
        self.refresh_label.set_margin_start(5)
        self.refresh_btn_box.pack_start(self.refresh_icon, False, False, 0)
        
        # Animation controller
        self.refresh_revealer = Gtk.Revealer()
        self.refresh_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)
        self.refresh_revealer.set_transition_duration(150)
        self.refresh_revealer.add(self.refresh_label)
        self.refresh_revealer.set_reveal_child(False)
        self.refresh_btn_box.pack_start(self.refresh_revealer, False, False, 0)
        
        self.refresh_button.add(self.refresh_btn_box)
        refresh_tooltip = getattr(self.txt, "wifi_refresh_tooltip", "Refresh WiFi List")
        self.refresh_button.set_tooltip_text(refresh_tooltip)
        self.refresh_button.connect("clicked", self.on_refresh_clicked)
        
        # Hover behavior
        self.refresh_button.set_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.refresh_button.connect("enter-notify-event", self.on_refresh_enter)
        self.refresh_button.connect("leave-notify-event", self.on_refresh_leave)

        # Disable refresh button if WiFi is not supported
        if not wifi_supported:
            self.refresh_button.set_sensitive(False)

        header_box.pack_end(self.refresh_button, False, False, 0)

        self.pack_start(header_box, False, False, 0)

        # Create scrollable content
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_window.set_vexpand(True)

        # Create main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_box.set_margin_top(10)
        content_box.set_margin_bottom(10)
        content_box.set_margin_start(10)
        content_box.set_margin_end(10)

        # WiFi power switch
        power_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        wifi_power_text = getattr(self.txt, "wifi_power", "WiFi Power")
        power_label = Gtk.Label(label=wifi_power_text)
        power_label.set_markup(f"<b>{wifi_power_text}</b>")
        power_label.set_halign(Gtk.Align.START)
        self.power_switch = Gtk.Switch()

        if wifi_supported:
            self.power_switch.set_active(get_wifi_status(self.logging))
            self.power_switch.connect("notify::active", self.on_power_switched)
        else:
            self.power_switch.set_sensitive(False)

        power_box.pack_start(power_label, False, True, 0)
        power_box.pack_end(self.power_switch, False, True, 0)
        content_box.pack_start(power_box, False, True, 0)

        network_info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        network_info_box.set_halign(Gtk.Align.START)
        
        network_info_box_botton = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        network_info_box_botton.set_halign(Gtk.Align.START)

        self.ip_label = Gtk.Label(label="IP Address: N/A")
        self.ip_label.set_halign(Gtk.Align.START)

        network_info_box.pack_start(self.ip_label, False, True, 0)

        self.public_ip = self.get_public_ip()
        self.public_ip_visible = False

        content_box.pack_start(network_info_box, False, True, 0)
        content_box.pack_start(network_info_box_botton, False, True, 0)


        # Network speed
        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        speed_box.set_margin_top(10)
        speed_box.set_margin_bottom(5)
        speed_label = Gtk.Label()
        wifi_speed_text = getattr(self.txt, "wifi_speed", "WiFi Speed")
        speed_label.set_markup(f"<b>{wifi_speed_text}</b>")
        speed_label.set_halign(Gtk.Align.START)
        speed_box.pack_start(speed_label, True, True, 0)
        content_box.pack_start(speed_box, False, True, 0)
        speed_values_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        wifi_upload_text = getattr(self.txt, "wifi_upload", "Upload")
        wifi_download_text = getattr(self.txt, "wifi_download", "Download")
        self.upload_label = Gtk.Label(label=f"{wifi_upload_text}: 0 Mbps")
        self.upload_label.set_halign(Gtk.Align.START)
        self.download_label = Gtk.Label(label=f"{wifi_download_text}: 0 Mbps")
        self.download_label.set_halign(Gtk.Align.START)
        speed_values_box.pack_start(self.download_label, False, True, 0)
        speed_values_box.pack_start(self.upload_label, False, True, 0)
        content_box.pack_start(speed_values_box, False, True, 0)



        self.network_details = get_network_details(logging)

        self.ip_label.set_text(f"IP Address: {self.network_details['ip_address']}")        

        # Network list section
        networks_label = Gtk.Label()
        wifi_available_text = getattr(self.txt, "wifi_available", "Available Networks")
        networks_label.set_markup(f"<b>{wifi_available_text}</b>")
        networks_label.set_halign(Gtk.Align.START)
        networks_label.set_margin_top(15)
        content_box.pack_start(networks_label, False, True, 0)

        # Network list
        networks_frame = Gtk.Frame()
        networks_frame.set_shadow_type(Gtk.ShadowType.IN)
        self.networks_box = Gtk.ListBox()
        self.networks_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.networks_box.get_style_context().add_class("network-list")
        networks_frame.add(self.networks_box)
        content_box.pack_start(networks_frame, True, True, 0)

        # Add the content box to the scroll window
        scroll_window.add(content_box)
        self.pack_start(scroll_window, True, True, 0)

        # Action buttons - moved outside of the scrollable area
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_box.set_margin_top(10)
        connect_text = getattr(self.txt, "connect", "Connect")
        connect_button = Gtk.Button(label=connect_text)
        connect_button.connect("clicked", self.on_connect_clicked)
        action_box.pack_start(connect_button, True, True, 0)

        disconnect_text = getattr(self.txt, "disconnect", "Disconnect")
        disconnect_button = Gtk.Button(label=disconnect_text)
        disconnect_button.connect("clicked", self.on_disconnect_clicked)
        action_box.pack_start(disconnect_button, True, True, 0)

        wifi_forget_text = getattr(self.txt, "wifi_forget", "Forget")
        forget_button = Gtk.Button(label=wifi_forget_text)
        forget_button.connect("clicked", self.on_forget_clicked)
        action_box.pack_start(forget_button, True, True, 0)

        # Add action buttons directly to the main container (outside scroll window)
        self.pack_start(action_box, False, True, 0)

        # Initial network list population is now deferred
        # self.update_network_list()  <- This line is removed

        # Store network speed timer ID so we can stop it when tab is hidden
        self.network_speed_timer_id = None

        # Previous speed values for calculation
        self.prev_rx_bytes = 0
        self.prev_tx_bytes = 0

        self.connect('key-press-event', self.on_key_press)
        
        # Connect signals for tab visibility tracking
        self.connect("map", self.on_tab_shown)
        self.connect("unmap", self.on_tab_hidden)

    def update_network_details(self):
        details = get_network_details(self.logging)

        self.ip_label.set_text(f"IP Address: {details['ip_address']}")        
        # self.dns_label.set_text(f"• DNS: {details['dns']}")
        # self.gateway_label.set_text(f"• Gateway: {details['gateway']}")

    def get_public_ip(self):
        try:
            response = requests.get("https://ifconfig.me/ip", timeout=3)
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass
        return "N/A"
        
     # keybinds for wifi tab
    def on_key_press(self, widget, event):
        keyval = event.keyval
        
        if keyval in (114, 82):
            if self.power_switch.get_active():
                #  check if wifi is already loading or not
                for child in self.networks_box.get_children():
                    box = child.get_child()
                    if isinstance(box.get_children()[0], Gtk.Spinner):
                        self.logging.log(LogLevel.Info, "Already refreshing wifi, skipping")
                        return True
                    
                self.logging.log(LogLevel.Info, "Refreshing wifi networks via keybind")
                self.load_networks()
                return True
            else:
                self.logging.log(LogLevel.Info, "Unable to refresh, wifi is disabled")
                

    def on_tab_shown(self, widget):
        """Handle tab becoming visible"""
        self.logging.log(LogLevel.Debug, "WiFi tab: on_tab_shown triggered")
        self.tab_visible = True
        
        # Debug container visibility
        def check_visibility():
            self.logging.log(LogLevel.Debug, f"WiFi tab visible: {self.get_visible()}")
            for child in self.get_children():
                self.logging.log(LogLevel.Debug, f"Child {type(child).__name__} visible: {child.get_visible()}")
            return False
            
        GLib.idle_add(check_visibility)
        
        self.update_network_list()

        # Start network speed updates when tab becomes visible
        if self.network_speed_timer_id is None:
            self.network_speed_timer_id = GLib.timeout_add_seconds(1, self.update_network_speed)

        # Update network details (IP, DNS, Gateway)
        self.update_network_details()

        return False

    def on_tab_hidden(self, widget):
        """Handle tab becoming hidden"""
        self.logging.log(LogLevel.Info, "WiFi tab became hidden")
        self.tab_visible = False

        # Stop network speed updates when tab is hidden
        if self.network_speed_timer_id is not None:
            GLib.source_remove(self.network_speed_timer_id)
            self.network_speed_timer_id = None

        return False

    def load_networks(self):
        """Load WiFi networks list - to be called after all tabs are loaded"""
        self.logging.log(LogLevel.Info, "Loading WiFi networks after tabs initialization")

        # Only load networks if the tab is visible
        if not self.tab_visible:
            self.logging.log(LogLevel.Info, "WiFi tab not visible, skipping initial network loading")
            return

        # Add a loading indicator
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)

        spinner = Gtk.Spinner()
        spinner.start()
        box.pack_start(spinner, False, False, 0)

        label = Gtk.Label(label="Loading networks...")
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, True, True, 0)

        row.add(box)
        self.networks_box.add(row)
        self.networks_box.show_all()

        # Start network scan in background thread
        thread = threading.Thread(target=self._load_networks_thread)
        thread.daemon = True
        thread.start()

    def _load_networks_thread(self):
        """Background thread to load WiFi networks"""
        try:
            # Get networks
            networks = get_wifi_networks(self.logging)
            self.logging.log(LogLevel.Info, f"Found {len(networks)} WiFi networks")
            # Update UI in main thread
            GLib.idle_add(self._update_networks_in_ui, networks)
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed loading WiFi networks: {e}")
            # Show error in UI
            GLib.idle_add(self._show_network_error, str(e))

    def _update_networks_in_ui(self, networks):
        """Update UI with networks (called in main thread)"""
        try:
            # Clear existing networks
            for child in self.networks_box.get_children():
                self.networks_box.remove(child)

            if not networks:
                self._show_no_networks_info()
                return False

            sorted_networks = self._sort_networks(networks)

            for network in sorted_networks:
                self._add_network_row(network)

            self.networks_box.show_all()

        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed updating networks in UI: {e}")
            self._show_network_error(str(e))

        return False  # required for GLib.idle_add

    def _show_no_networks_info(self):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)

        result = subprocess.run(["nmcli", "-t", "-f", "DEVICE,TYPE", "device"], capture_output=True, text=True)
        wifi_interfaces = [line for line in result.stdout.split('\n') if "wifi" in line]

        if not wifi_interfaces:
            error_icon = Gtk.Image.new_from_icon_name("dialog-error-symbolic", Gtk.IconSize.MENU)
            box.pack_start(error_icon, False, False, 0)
            label = Gtk.Label(label="WiFi is not supported on this machine")
        else:
            label = Gtk.Label(label="No networks found")

        label.set_halign(Gtk.Align.START)
        box.pack_start(label, True, True, 0)

        row.add(box)
        self.networks_box.add(row)

        row.get_style_context().add_class("fade-in")

        def remove_animation_class(row_widget):
            if row_widget and row_widget.get_parent() is not None:
                row_widget.get_style_context().remove_class("fade-in")
            return False

        GLib.timeout_add(350, remove_animation_class, row)

        self.networks_box.show_all()

    def _sort_networks(self, networks):
        def get_sort_key(network):
            try:
                if network["in_use"]:
                    return -9999
                else:
                    return -int(network["signal"])
            except (ValueError, TypeError):
                return 0
        return sorted(networks, key=get_sort_key)

    def _add_network_row(self, network):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(6)
        box.set_margin_bottom(6)

        # Add signal icon
        signal_icon = self._create_signal_icon(network)
        box.pack_start(signal_icon, False, False, 0)

        info_box = self._create_network_info_box(network)
        box.pack_start(info_box, True, True, 0)

        # Connected indicator + QR button
        if network["in_use"]:
            self._add_connected_qr_widgets(box)

        # Lock icon if network is secure
        if network["security"].lower() != "none":
            lock_icon = Gtk.Image.new_from_icon_name("system-lock-screen-symbolic", Gtk.IconSize.MENU)
            box.pack_end(lock_icon, False, False, 0)
            
        # security type
        self.security_type = network["security"]

        row.add(box)
        self.networks_box.add(row)
        
        if network["in_use"] and self.separator_enabled:
            self.separator_row = Gtk.ListBoxRow()
            self.separator_row.set_selectable(False)
            self.separator_row.set_activatable(False)

            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            separator.get_style_context().add_class("network-separator")
            separator.set_margin_start(10)
            separator.set_margin_end(10)
            separator.set_margin_top(5)
            separator.set_margin_bottom(5)

            self.separator_row.add(separator)
            self.networks_box.add(self.separator_row)

        def add_animation_with_delay(row_widget, index):
            if row_widget and row_widget.get_parent() is not None:
                row_widget.get_style_context().add_class("fade-in")

                def remove_animation_class():
                    if row_widget and row_widget.get_parent() is not None:
                        row_widget.get_style_context().remove_class("fade-in")
                    return False

                GLib.timeout_add(350, remove_animation_class)
            return False

        index = len([child for child in self.networks_box.get_children() 
                if child.get_selectable()]) - 1  
        GLib.timeout_add(30 * index, add_animation_with_delay, row, index)

    def _create_signal_icon(self, network):
        try:
            signal_strength = int(network.get("signal", 0))
        except (ValueError, TypeError):
            signal_strength = 0
        if signal_strength >= 80:
            icon_name = "network-wireless-signal-excellent-symbolic"
        elif signal_strength >= 60:
            icon_name = "network-wireless-signal-good-symbolic"
        elif signal_strength >= 40:
            icon_name = "network-wireless-signal-ok-symbolic"
        elif signal_strength > 0:
            icon_name = "network-wireless-signal-weak-symbolic"
        else:
            icon_name = "network-wireless-signal-none-symbolic"
        signal_icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
        return signal_icon

    def _create_network_info_box(self, network):
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)

        name_label = Gtk.Label()
        name_label.set_halign(Gtk.Align.START)
        if network["in_use"]:
            name_label.set_markup(f"<b>{GLib.markup_escape_text(network['ssid'])}</b>")
        else:
            name_label.set_text(network["ssid"])
        info_box.pack_start(name_label, False, True, 0)

        security_text = network.get("security", "")
        signal_val = 0
        try:
            signal_val = int(network.get("signal", 0))
        except (ValueError, TypeError):
            signal_val = 0
        if security_text.lower() == "none":
            security_text_disp = "Open"
        else:
            security_text_disp = security_text
        details_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        details_label = Gtk.Label()
        details_label.set_markup(f'<small>{GLib.markup_escape_text(security_text_disp)} • Signal: {signal_val}%</small>')
        details_label.set_halign(Gtk.Align.START)
        details_box.pack_start(details_label, False, True, 0)
        info_box.pack_start(details_box, False, True, 0)

        return info_box

    def _add_connected_qr_widgets(self, container_box):
        connected_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic", Gtk.IconSize.MENU)
        connected_text = getattr(self.txt, "connected", "Connected")
        connected_label = Gtk.Label(label=connected_text)
        connected_label.get_style_context().add_class("dim-label")
        connected_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        connected_box.pack_start(connected_icon, False, False, 0)
        connected_box.pack_start(connected_label, False, False, 0)
        container_box.pack_start(connected_box, False, True, 0)
        
        # Network properties button
        properties_button = Gtk.Button()
        properties_button.set_tooltip_text("Properties")
        properties_button.get_style_context().add_class("properties-button")
        properties_button.connect("clicked", self.show_prop_dialog)
        properties_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.MENU)
        properties_icon.get_style_context().add_class("rotate-gear")
        properties_button.set_image(properties_icon)
        container_box.pack_start(properties_button, False, False, 0)


    def _show_network_error(self, error_message):
        """Show an error message in the networks list"""
        # Clear existing networks
        for child in self.networks_box.get_children():
            self.networks_box.remove(child)
        # Add error message
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)

        error_icon = Gtk.Image.new_from_icon_name("dialog-error-symbolic", Gtk.IconSize.MENU)
        box.pack_start(error_icon, False, False, 0)

        label = Gtk.Label(label=f"Failed loading networks: {error_message}")
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, True, True, 0)

        row.add(box)
        self.networks_box.add(row)
        self.networks_box.show_all()

        return False  # Required for GLib.idle_add

    def update_network_list(self):
        """Update the list of WiFi networks"""
        self.logging.log(LogLevel.Info, "Refreshing WiFi networks list")

        # Don't refresh if tab is not visible
        if not self.tab_visible:
            self.logging.log(LogLevel.Info, "WiFi tab not visible, skipping network refresh")
            return

        # Clear existing networks
        for child in self.networks_box.get_children():
            self.networks_box.remove(child)

        # Add loading indicator
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)

        spinner = Gtk.Spinner()
        spinner.start()
        box.pack_start(spinner, False, False, 0)

        loading_networks_text = getattr(self.txt, "wifi_loading_networks", "Loading networks...")
        label = Gtk.Label(label=loading_networks_text)
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, True, True, 0)

        row.add(box)
        self.networks_box.add(row)
        self.networks_box.show_all()

        # Start network scan in background thread
        thread = threading.Thread(target=self._load_networks_thread)
        thread.daemon = True
        thread.start()

    def update_network_speed(self):
        """Update network speed display"""
        speed = get_network_speed(self.logging)

        # Check if WiFi is supported
        if "wifi_supported" in speed and not speed["wifi_supported"]:
            self.download_label.set_text("Download: N/A")
            self.upload_label.set_text("Upload: N/A")
            return True  # Continue the timer

        rx_bytes = speed["rx_bytes"]
        tx_bytes = speed["tx_bytes"]

        if self.prev_rx_bytes > 0 and self.prev_tx_bytes > 0:
            rx_speed = ((rx_bytes - self.prev_rx_bytes) * 8) / (1024 * 1024) 
            tx_speed = ((tx_bytes - self.prev_tx_bytes) * 8) / (1024 * 1024)  
            self.download_label.set_text(f"Download: {rx_speed:.1f} Mbps")
            self.upload_label.set_text(f"Upload: {tx_speed:.1f} Mbps")
            while Gtk.events_pending():
                Gtk.main_iteration()

        self.prev_rx_bytes = rx_bytes
        self.prev_tx_bytes = tx_bytes

        return True  

    def on_power_switched(self, switch, gparam):
        """Handle WiFi power switch toggle"""
        state = switch.get_active()
        self.logging.log(LogLevel.Info, f"Setting WiFi power: {'ON' if state else 'OFF'}")
        # Run power toggle in a background thread to avoid UI freezing
        def power_toggle_thread():
            try:
                set_wifi_power(state, self.logging)
                if state and self.tab_visible:
                    # Only refresh network list if tab is visible
                    GLib.idle_add(self.update_network_list)
            except Exception as e:
                self.logging.log(LogLevel.Error, f"Failed setting WiFi power: {e}")
        # Start thread
        thread = threading.Thread(target=power_toggle_thread)
        thread.daemon = True
        thread.start()

    def on_refresh_enter(self, widget, event):
        alloc = widget.get_allocation()
        if (0 <= event.x <= alloc.width and 
            0 <= event.y <= alloc.height):
            self.refresh_revealer.set_reveal_child(True)
        return False
    
    def on_refresh_leave(self, widget, event):
        alloc = widget.get_allocation()
        if not (0 <= event.x <= alloc.width and 
               0 <= event.y <= alloc.height):
            self.refresh_revealer.set_reveal_child(False)
        return False

    def on_refresh_clicked(self, button):
        """Handle refresh button click"""
        self.logging.log(LogLevel.Info, "Manual refresh of WiFi networks requested")
        self.update_network_list()

    def on_connect_clicked(self, button):
        """Handle connect button click"""
        row = self.networks_box.get_selected_row()
        if row is None:
            return

        box = row.get_child()
        info_box = box.get_children()[1]
        name_label = info_box.get_children()[0]
        ssid = name_label.get_text()
        # If network name is formatted with markup, strip the markup
        if not ssid:
            ssid = name_label.get_label()
            ssid = ssid.replace("<b>", "").replace("</b>", "")

        self.logging.log(LogLevel.Info, f"Connecting to WiFi network: {ssid}")

        # Show connecting indicator in list
        for child in self.networks_box.get_children():
            if child == row:
                # Update the selected row to show connecting status
                old_box = child.get_child()
                child.remove(old_box)
                new_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                new_box.set_margin_start(10)
                new_box.set_margin_end(10)
                new_box.set_margin_top(6)
                new_box.set_margin_bottom(6)
                # Add spinner
                spinner = Gtk.Spinner()
                spinner.start()
                new_box.pack_start(spinner, False, False, 0)
                # Add label
                connecting_label = Gtk.Label(label=f"Connecting to {ssid}...")
                connecting_label.set_halign(Gtk.Align.START)
                new_box.pack_start(connecting_label, True, True, 0)

                child.add(new_box)
                child.show_all()
                break

        # Try connecting in background thread
        def connect_thread():
            try:
                # First try to connect with saved credentials
                if connect_network(ssid, self.logging):
                    GLib.idle_add(self.update_network_list)
                    return

                # If that fails, check if network requires password
                networks = get_wifi_networks(self.logging)
                network = next((n for n in networks if n["ssid"] == ssid), None)

                if network and network["security"].lower() != "none":
                    # Network requires password and saved credentials failed, show password dialog
                    GLib.idle_add(self._show_password_dialog, ssid)
                else:
                    # Failed to connect but no password needed, just refresh UI
                    GLib.idle_add(self.update_network_list)
            except Exception as e:
                self.logging.log(LogLevel.Error, f"Failed connecting to network: {e}")
                GLib.idle_add(self.update_network_list)

        thread = threading.Thread(target=connect_thread)
        thread.daemon = True
        thread.start()

    def _show_password_dialog(self, ssid):
        """Show password dialog for secured networks"""
        networks = get_wifi_networks(self.logging)
        network = next((n for n in networks if n["ssid"] == ssid), None)
        if network and network["security"].lower() != "none":
            dialog = Gtk.Dialog(
                title=f"Connect to {ssid}",
                parent=self.get_toplevel(),
                flags=0,
                buttons=(
                    Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_OK, Gtk.ResponseType.OK
                )
            )

            box = dialog.get_content_area()
            box.set_spacing(10)
            box.set_margin_start(10)
            box.set_margin_end(10)
            box.set_margin_top(10)
            box.set_margin_bottom(10)

            password_label = Gtk.Label(label="Password:")
            box.add(password_label)

            password_entry = Gtk.Entry()
            password_entry.set_visibility(False)
            password_entry.set_invisible_char("●")
            box.add(password_entry)

            remember_check = Gtk.CheckButton(label="Remember this network")
            remember_check.set_active(True)
            box.add(remember_check)

            dialog.show_all()
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                password = password_entry.get_text()
                remember = remember_check.get_active()
                dialog.destroy()
                # Connect with password in background thread
                def connect_with_password_thread():
                    try:
                        if connect_network(ssid, self.logging, password, remember):
                            GLib.idle_add(self.update_network_list)
                        else:
                            # Show error dialog
                            error_dialog = Gtk.MessageDialog(
                                transient_for=self.get_toplevel(),
                                flags=0,
                                message_type=Gtk.MessageType.ERROR,
                                buttons=Gtk.ButtonsType.OK,
                                text="Failed to connect"
                            )
                            error_dialog.format_secondary_text(
                                "Please check your password and try again."
                            )
                            error_dialog.run()
                            error_dialog.destroy()
                            # Refresh UI to clear status
                            GLib.idle_add(self.update_network_list)
                    except Exception as e:
                        self.logging.log(LogLevel.Error, f"Failed connecting to network with password: {e}")
                        GLib.idle_add(self.update_network_list)
                thread = threading.Thread(target=connect_with_password_thread)
                thread.daemon = True
                thread.start()
            else:
                dialog.destroy()
                # User cancelled, refresh UI to clear status
                self.update_network_list()
        else:
            # No security or network not found, just refresh UI
            self.update_network_list()
        return False  # Required for GLib.idle_add

    def on_disconnect_clicked(self, button):
        """Handle disconnect button click"""
        row = self.networks_box.get_selected_row()
        if row is None:
            return

        box = row.get_child()
        info_box = box.get_children()[1]
        name_label = info_box.get_children()[0]
        ssid = name_label.get_text()
        # If network name is formatted with markup, strip the markup
        if not ssid:
            ssid = name_label.get_label()
            ssid = ssid.replace("<b>", "").replace("</b>", "")

        self.logging.log(LogLevel.Info, f"Disconnecting from WiFi network: {ssid}")

        # Show disconnecting indicator
        for child in self.networks_box.get_children():
            if child == row:
                # Update the selected row to show disconnecting status
                old_box = child.get_child()
                child.remove(old_box)
                new_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                new_box.set_margin_start(10)
                new_box.set_margin_end(10)
                new_box.set_margin_top(6)
                new_box.set_margin_bottom(6)
                # Add spinner
                spinner = Gtk.Spinner()
                spinner.start()
                new_box.pack_start(spinner, False, False, 0)
                # Add label
                disconnecting_label = Gtk.Label(label=f"Disconnecting from {ssid}...")
                disconnecting_label.set_halign(Gtk.Align.START)
                new_box.pack_start(disconnecting_label, True, True, 0)

                child.add(new_box)
                child.show_all()
                break

        # Run disconnect in separate thread
        thread = threading.Thread(target=self._disconnect_thread, args=(ssid,))
        thread.daemon = True
        thread.start()

    def on_forget_clicked(self, button):
        """Handle forget button click"""
        row = self.networks_box.get_selected_row()
        if row is None:
            return

        box = row.get_child()
        info_box = box.get_children()[1]
        name_label = info_box.get_children()[0]
        ssid = name_label.get_text()
        # If network name is formatted with markup, strip the markup
        if not ssid:
            ssid = name_label.get_label()
            ssid = ssid.replace("<b>", "").replace("</b>", "")
        self.logging.log(LogLevel.Info, f"Forgetting WiFi network: {ssid}")

        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Forget network {ssid}?"
        )
        dialog.format_secondary_text(
            "This will remove all saved settings for this network."
        )

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            # Show forgetting indicator
            for child in self.networks_box.get_children():
                if child == row:
                    # Update the selected row to show forgetting status
                    old_box = child.get_child()
                    child.remove(old_box)
                    new_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                    new_box.set_margin_start(10)
                    new_box.set_margin_end(10)
                    new_box.set_margin_top(6)
                    new_box.set_margin_bottom(6)
                    # Add spinner
                    spinner = Gtk.Spinner()
                    spinner.start()
                    new_box.pack_start(spinner, False, False, 0)
                    # Add label
                    forgetting_label = Gtk.Label(label=f"Forgetting {ssid}...")
                    forgetting_label.set_halign(Gtk.Align.START)
                    new_box.pack_start(forgetting_label, True, True, 0)

                    child.add(new_box)
                    child.show_all()
                    break

            # Run forget in background thread
            def forget_thread():
                try:
                    if forget_network(ssid, self.logging):
                        GLib.idle_add(self.update_network_list)
                    else:
                        # Failed to forget, just refresh UI
                        GLib.idle_add(self.update_network_list)
                except Exception as e:
                    self.logging.log(LogLevel.Error, f"Failed forgetting network: {e}")
                    GLib.idle_add(self.update_network_list)
            thread = threading.Thread(target=forget_thread)
            thread.daemon = True
            thread.start()

    def _disconnect_thread(self, ssid):
        """Thread function to disconnect from a WiFi network"""
        try:
            if disconnect_network(ssid, self.logging):
                GLib.idle_add(self.update_network_list)
                self.logging.log(LogLevel.Info, f"Successfully disconnected from {ssid}")
            else:
                self.logging.log(LogLevel.Error, f"Failed to disconnect from {ssid}")
                GLib.idle_add(self.update_network_list)
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed disconnecting from network: {e}")
            GLib.idle_add(self.update_network_list)


    def get_current_network(self):
        """Get the currently connected network"""
        try:
            networks = get_wifi_networks(self.logging)
            current_network = next((network for network in networks if network["in_use"]), None)
            return current_network
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed to get current network: {e}")
            return None

    def show_prop_dialog(self, button):
            """Show a qr code dialog for current network"""
            # Get current network
            current_network = self.get_current_network()
            if current_network:
                # create a dialog
                try:
                    connection_info = get_connection_info(current_network["ssid"], self.logging)

                    # generate qr code for wifi
                    qr_path = generate_wifi_qrcode(
                        current_network["ssid"],
                        connection_info.get("password", ""),
                        current_network["security"],
                        self.logging
                    )

                    # use hardcoded fallback title text to avoid missing translation attribute diagnostics
                    # dialog_title = getattr(self.txt, "wifi_share_title", "Share WiFi")
                    dialog_title = "Network Properties"

                    prop_dialog = Gtk.Dialog(
                        title=dialog_title,
                        parent=self.get_toplevel(),
                        flags=0,
                    )
                    prop_dialog.set_size_request(380, 500)
                    prop_dialog.set_modal(True)
                    prop_dialog.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)

                    # header
                    header_bar = Gtk.HeaderBar()
                    header_bar.set_show_close_button(True)
                    header_bar.set_title(dialog_title)
                    prop_dialog.set_titlebar(header_bar)
                    
                    # scrolled window for content
                    scrolled_window = Gtk.ScrolledWindow()
                    scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
                    scrolled_window.set_vexpand(True)

                    # content area
                    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                    main_box.set_margin_top(10)
                    main_box.set_margin_bottom(10)
                    main_box.set_margin_start(10)
                    main_box.set_margin_end(10)

                    # create top box for qr code 
                    # create bottom box for network details 
                    top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                    bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

                    
                    # image holder
                    qr_button = Gtk.Button()
                    qr_button.set_size_request(124,124)
                    qr_button.set_relief(Gtk.ReliefStyle.NONE)
                    qr_button.get_style_context().add_class("qr_image_holder")

                    # fallback for wifi_share_scan
                    scan_text = getattr(self.txt, "wifi_share_scan", "Scan this QR code to join")
                    scan_label = Gtk.Label(label=scan_text)
                    scan_label.get_style_context().add_class("scan_label")

                    if qr_path:
                        qr_image = Gtk.Image()
                        qr_image.set_size_request(120, 120)
                        qr_image.set_margin_top(8)
                        qr_image.set_margin_bottom(8)
                        qr_image.set_from_file(qr_path)
                        qr_button.add(qr_image)
                    else:
                        error_label = Gtk.Label(label="Failed to generate QR code")
                        qr_button.add(error_label)

                    top_box.pack_start(scan_label, False, False, 0)
                    top_box.pack_start(qr_button, False, False, 0)

                    # network details
                    # bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
                    # bottom_box.set_margin_top(1)

                    # network name
                    ssid_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    ssid_box.set_size_request(320, 50)
                    ssid_box.get_style_context().add_class("ssid-box")

                    ssid_label_text = getattr(self.txt, "wifi_network_name", "Network name")
                    ssid_label = Gtk.Label(label=ssid_label_text)
                    ssid_label.get_style_context().add_class("dimmed-label")
                    ssid_label.set_markup(f"<b>{ssid_label_text}</b>")
                    ssid_label.set_halign(Gtk.Align.START)

                    ssid_name = Gtk.Label(label=current_network["ssid"])
                    ssid_name.get_style_context().add_class("dimmed-label")
                    ssid_name.set_halign(Gtk.Align.START)
                    ssid_box.pack_start(ssid_label, False, False, 0)
                    ssid_box.pack_start(ssid_name, False, False, 0)

                    # network password
                    security_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    security_box.set_size_request(320, 50)
                    security_box.get_style_context().add_class("secrity-box")

                    wifi_password_text = getattr(self.txt, "wifi_password", "Password")
                    security_label = Gtk.Label(label=wifi_password_text)
                    security_label.get_style_context().add_class("dimmed-label")
                    security_label.set_markup(f"<b>{wifi_password_text}</b>")
                    security_label.set_halign(Gtk.Align.START)

                    passwd = Gtk.Label(label=connection_info.get("password", "Hidden"))
                    passwd.get_style_context().add_class("dimmed-label")
                    passwd.set_halign(Gtk.Align.START)
                    
                    security_box.pack_start(security_label, False, False, 0)
                    security_box.pack_start(passwd, False, False, 0)
                    
                    top_box.pack_start(ssid_box, False, False, 0)
                    top_box.pack_start(security_box, False, False, 0)

                    main_box.pack_start(top_box, True, True, 0)
                    main_box.pack_end(bottom_box, True, True, 0)
                    
                    bottom_label = Gtk.Label(label="Network Details")
                    bottom_label.set_markup("<span weight='bold' size='large'>Network Details</span>")
                    
                    bottom_box.pack_start(bottom_label, False, False, 0)
                    
                    # Ip address and other details
                    details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
                    
                    ip_address_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                    ip_address_box.get_style_context().add_class("ip-address-box")
                    ip_address_label = Gtk.Label(label="IP Address")
                    ip_address_label.get_style_context().add_class("dimmed-label")
                    ip_address_label.set_halign(Gtk.Align.START)
                    
                    ip_address = Gtk.Label()
                    ip_address.set_text(f"{self.network_details['ip_address']}")
                    ip_address.get_style_context().add_class("dimmed-label")
                    ip_address.set_halign(Gtk.Align.START)
                    ip_address_box.pack_start(ip_address_label, False, False, 0)
                    ip_address_box.pack_start(ip_address, True, True, 0)
                    details_box.pack_start(ip_address_box, False, False, 0)
                    
                    dns_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                    dns_box.get_style_context().add_class("dns-box")
                    dns_label = Gtk.Label(label="DNS")
                    dns_label.get_style_context().add_class("dimmed-label")
                    dns_label.set_halign(Gtk.Align.START)
                    
                    dns = Gtk.Label()
                    dns.set_text(f"{self.network_details['dns']}")
                    dns.get_style_context().add_class("dimmed-label")
                    dns.set_halign(Gtk.Align.START)
                    dns_box.pack_start(dns_label, False, False, 0)
                    dns_box.pack_start(dns, True, True, 0)
                    details_box.pack_start(dns_box, False, False, 0)
                    
                    gateway_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                    gateway_box.get_style_context().add_class("gateway-box")
                    gateway_label = Gtk.Label(label="Gateway")
                    gateway_label.get_style_context().add_class("dimmed-label")
                    gateway_label.set_halign(Gtk.Align.START)
                    
                    gateway = Gtk.Label()
                    gateway.set_text(f"{self.network_details['gateway']}")
                    gateway.get_style_context().add_class("dimmed-label")
                    gateway.set_halign(Gtk.Align.START)
                    gateway_box.pack_start(gateway_label, False, False, 0)
                    gateway_box.pack_start(gateway, True, True, 0)
                    details_box.pack_start(gateway_box, False, False, 0)
                    
                    security_type_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                    security_type_box.get_style_context().add_class("security-type-box")
                    security_type_label = Gtk.Label(label="Security")
                    security_type_label.get_style_context().add_class("dimmed-label")
                    security_type_label.set_halign(Gtk.Align.START)
                    
                    security_type = Gtk.Label(label=self.security_type)
                    security_type.get_style_context().add_class("dimmed-label")
                    security_type.set_halign(Gtk.Align.START)
                    security_type_box.pack_start(security_type_label, False, False, 0)
                    security_type_box.pack_start(security_type, True, True, 0)
                    details_box.pack_start(security_type_box, False, False, 0)
                    
                    public_ip_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                    public_ip_box.get_style_context().add_class("public-ip-box")
                    
                    # For label and hide icon
                    public_ip_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                    public_ip_label = Gtk.Label(label="Public IP")
                    public_ip_label.get_style_context().add_class("dimmed-label")
                    public_ip_label.set_halign(Gtk.Align.START)
                    
                    self.eye_button = Gtk.Button()
                    self.eye_button.set_relief(Gtk.ReliefStyle.NONE)
                    self.eye_icon = Gtk.Image.new_from_icon_name("view-reveal-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
                    self.eye_button.add(self.eye_icon)
                    self.eye_button.set_tooltip_text("Show/Hide Public IP")
                    
                    public_ip_header.pack_start(public_ip_label, True, True, 0)
                    public_ip_header.pack_start(self.eye_button, False, False, 0)
                    
                    self.public_ip_value = Gtk.Label()
                    self.public_ip_value.set_text(f"hidden")
                    self.public_ip_value.get_style_context().add_class("dimmed-label")
                    self.public_ip_value.set_halign(Gtk.Align.START)
                        
                    self.eye_button.connect("clicked", self.toggle_public_ip)

                    public_ip_box.pack_start(public_ip_header, False, False, 0)
                    public_ip_box.pack_start(self.public_ip_value, True, True, 0)
                    details_box.pack_start(public_ip_box, False, False, 0)
                    
                    
                    bottom_box.pack_start(details_box, False, False, 0)
                    scrolled_window.add(main_box)
                    prop_dialog.get_content_area().pack_start(scrolled_window, True, True, 0)
                                                
                    prop_dialog.show_all()
                    prop_dialog.run()
                    prop_dialog.destroy()

                except Exception as e:
                    self.logging.log(LogLevel.Error, f"failed to open qr code dialog: {e}")
                    traceback.print_exc()

    def toggle_public_ip(self, button):
        if self.public_ip_visible:
            self.public_ip_value.set_text("hidden")
            self.eye_icon.set_from_icon_name("view-reveal-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
            self.eye_button.set_tooltip_text("Show Public IP")
            self.public_ip_visible = False
        else:
            if self.public_ip == "N/A":
                self.public_ip = self.get_public_ip()
                
            self.public_ip_value.set_text(self.public_ip)
            self.eye_icon.set_from_icon_name("view-conceal-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
            self.eye_button.set_tooltip_text("Hide Public IP")
            self.public_ip_visible = True
                    
    def on_enable_separator_changed(self, widget, active):
        """Handle connected seprarator toggled signal from settings tab"""
        self.settings["enable_separator"] = active
        save_settings(self.settings, self.logging)
        
        self.separator_enabled = active
        
        # TODO update on realtime
        
        self.logging.log(LogLevel.Info, f"WiFi separator visibility set to: {active}")
        self.logging.log(LogLevel.Info, f"Restart to see the changes")
