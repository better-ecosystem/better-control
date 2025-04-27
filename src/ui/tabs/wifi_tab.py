#!/usr/bin/env python3

import traceback
import gi # type: ignore
import threading

from utils.logger import LogLevel, Logger
import subprocess

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
    wifi_supported
)

# Import the speedtest module
from tools.speedtest import (
    SpeedtestRunner, 
    SpeedtestResult,
    install_speedtest_cli
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

        # Track tab visibility status
        self.tab_visible = False

        # Initialize speedtest runner
        self.speedtest_runner = SpeedtestRunner(logging)
        
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
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)  # Increased from 10
        content_box.set_margin_top(16)    # Increased from 10
        content_box.set_margin_bottom(16) # Increased from 10
        content_box.set_margin_start(16)  # Increased from 10
        content_box.set_margin_end(16)    # Increased from 10
        content_box.get_style_context().add_class("content-container")  # Add our new CSS class

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

        # Speedtest section
        speedtest_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        speedtest_box.set_margin_top(15)
        speedtest_box.set_margin_bottom(5)
        
        # Speedtest header with button
        speedtest_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        speedtest_label = Gtk.Label()
        speedtest_text = getattr(self.txt, "speedtest_title", "Speed Test")
        speedtest_label.set_markup(f"<b>{speedtest_text}</b>")
        speedtest_label.set_halign(Gtk.Align.START)
        speedtest_header_box.pack_start(speedtest_label, True, True, 0)
        
        # Speedtest button
        self.speedtest_button = Gtk.Button()
        speedtest_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        speedtest_icon = Gtk.Image.new_from_icon_name("network-transmit-receive-symbolic", Gtk.IconSize.BUTTON)
        speedtest_button_label = Gtk.Label(label=getattr(self.txt, "run_test", "Run Test"))
        speedtest_button_box.pack_start(speedtest_icon, False, False, 0)
        speedtest_button_box.pack_start(speedtest_button_label, False, False, 0)
        self.speedtest_button.add(speedtest_button_box)
        self.speedtest_button.connect("clicked", self.on_speedtest_clicked)
        
        # Check if speedtest is available, disable button if not
        if not self.speedtest_runner.speedtest_available():
            self.speedtest_button.set_tooltip_text("Speedtest CLI not installed")
            self.speedtest_button.set_sensitive(False)
        
        speedtest_header_box.pack_end(self.speedtest_button, False, False, 0)
        speedtest_box.pack_start(speedtest_header_box, False, True, 0)
        
        # Speedtest progress and results
        self.speedtest_progress_bar = Gtk.ProgressBar()
        self.speedtest_progress_bar.set_text("Ready")
        self.speedtest_progress_bar.set_show_text(True)
        self.speedtest_progress_bar.set_margin_top(5)
        self.speedtest_progress_bar.set_margin_bottom(5)
        
        # Initially hide the progress bar
        self.speedtest_progress_revealer = Gtk.Revealer()
        self.speedtest_progress_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.speedtest_progress_revealer.set_transition_duration(300)
        self.speedtest_progress_revealer.add(self.speedtest_progress_bar)
        self.speedtest_progress_revealer.set_reveal_child(False)
        speedtest_box.pack_start(self.speedtest_progress_revealer, False, True, 0)
        
        # Results grid
        self.results_grid = Gtk.Grid()
        self.results_grid.set_column_spacing(15)
        self.results_grid.set_row_spacing(8)
        self.results_grid.set_margin_top(5)
        
        # Row 0: Download and Upload
        download_label = Gtk.Label(label=getattr(self.txt, "download", "Download"))
        download_label.set_halign(Gtk.Align.START)
        download_label.get_style_context().add_class("dim-label")
        self.results_grid.attach(download_label, 0, 0, 1, 1)
        
        self.download_result_label = Gtk.Label(label="--")
        self.download_result_label.set_halign(Gtk.Align.START)
        self.results_grid.attach(self.download_result_label, 1, 0, 1, 1)
        
        upload_label = Gtk.Label(label=getattr(self.txt, "upload", "Upload"))
        upload_label.set_halign(Gtk.Align.START)
        upload_label.get_style_context().add_class("dim-label")
        self.results_grid.attach(upload_label, 2, 0, 1, 1)
        
        self.upload_result_label = Gtk.Label(label="--")
        self.upload_result_label.set_halign(Gtk.Align.START)
        self.results_grid.attach(self.upload_result_label, 3, 0, 1, 1)
        
        # Row 1: Ping and Jitter
        ping_label = Gtk.Label(label=getattr(self.txt, "ping", "Ping"))
        ping_label.set_halign(Gtk.Align.START)
        ping_label.get_style_context().add_class("dim-label")
        self.results_grid.attach(ping_label, 0, 1, 1, 1)
        
        self.ping_result_label = Gtk.Label(label="--")
        self.ping_result_label.set_halign(Gtk.Align.START)
        self.results_grid.attach(self.ping_result_label, 1, 1, 1, 1)
        
        jitter_label = Gtk.Label(label=getattr(self.txt, "jitter", "Jitter"))
        jitter_label.set_halign(Gtk.Align.START)
        jitter_label.get_style_context().add_class("dim-label")
        self.results_grid.attach(jitter_label, 2, 1, 1, 1)
        
        self.jitter_result_label = Gtk.Label(label="--")
        self.jitter_result_label.set_halign(Gtk.Align.START)
        self.results_grid.attach(self.jitter_result_label, 3, 1, 1, 1)
        
        # Row 2: ISP and Server
        isp_label = Gtk.Label(label=getattr(self.txt, "isp", "ISP"))
        isp_label.set_halign(Gtk.Align.START)
        isp_label.get_style_context().add_class("dim-label")
        self.results_grid.attach(isp_label, 0, 2, 1, 1)
        
        self.isp_result_label = Gtk.Label(label="--")
        self.isp_result_label.set_halign(Gtk.Align.START)
        self.results_grid.attach(self.isp_result_label, 1, 2, 1, 1)
        
        server_label = Gtk.Label(label=getattr(self.txt, "server", "Server"))
        server_label.set_halign(Gtk.Align.START)
        server_label.get_style_context().add_class("dim-label")
        self.results_grid.attach(server_label, 2, 2, 1, 1)
        
        self.server_result_label = Gtk.Label(label="--")
        self.server_result_label.set_halign(Gtk.Align.START)
        self.results_grid.attach(self.server_result_label, 3, 2, 1, 1)
        
        # Initially hide the results grid
        self.results_revealer = Gtk.Revealer()
        self.results_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.results_revealer.set_transition_duration(300)
        self.results_revealer.add(self.results_grid)
        self.results_revealer.set_reveal_child(False)
        speedtest_box.pack_start(self.results_revealer, False, True, 0)
        
        # Add speedtest section to content
        content_box.pack_start(speedtest_box, False, True, 0)
        
        # Register callbacks for speedtest
        self.speedtest_runner.register_callback(self.on_speedtest_complete)
        self.speedtest_runner.register_progress_callback(self.on_speedtest_progress)

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

        # Store network speed timer ID so we can stop it when tab is hidden
        self.network_speed_timer_id = None

        # Previous speed values for calculation
        self.prev_rx_bytes = 0
        self.prev_tx_bytes = 0

        self.connect('key-press-event', self.on_key_press)
        
        # Connect signals for tab visibility tracking
        self.connect("map", self.on_tab_shown)
        self.connect("unmap", self.on_tab_hidden)
    
    def on_speedtest_clicked(self, button):
        """Handle speedtest button click"""
        # If speedtest-cli is not available, attempt to install it
        if not self.speedtest_runner.speedtest_available():
            self.logging.log(LogLevel.Info, "Speedtest CLI not installed, attempting to install")
            self.speedtest_button.set_sensitive(False)
            
            # Show installing message in progress bar
            self.speedtest_progress_bar.set_text("Installing speedtest-cli...")
            self.speedtest_progress_bar.set_fraction(0.1)
            self.speedtest_progress_revealer.set_reveal_child(True)
            
            def install_thread():
                success = install_speedtest_cli(self.logging)
                GLib.idle_add(self._handle_speedtest_install_result, success)
                
            threading.Thread(target=install_thread, daemon=True).start()
            return
            
        # If speedtest is already running, cancel it
        if self.speedtest_runner.is_running:
            self.logging.log(LogLevel.Info, "Cancelling speedtest")
            self.speedtest_runner.cancel_test()
            return
            
        # Start speedtest
        self.logging.log(LogLevel.Info, "Starting speedtest")
        
        # Update UI
        self.speedtest_button.get_children()[0].get_children()[1].set_text(getattr(self.txt, "cancel", "Cancel"))
        self.speedtest_progress_bar.set_text("Initializing...")
        self.speedtest_progress_bar.set_fraction(0)
        self.speedtest_progress_revealer.set_reveal_child(True)
        
        # Start the test
        self.speedtest_runner.run_test()
    
    def _handle_speedtest_install_result(self, success):
        """Handle the result of speedtest-cli installation"""
        if success:
            self.logging.log(LogLevel.Info, "Speedtest CLI installed successfully")
            self.speedtest_button.set_sensitive(True)
            self.speedtest_button.set_tooltip_text("")
            self.speedtest_progress_bar.set_text("Ready to run test")
            self.speedtest_progress_bar.set_fraction(1.0)
            
            # Hide progress bar after a delay
            def hide_progress_bar():
                self.speedtest_progress_revealer.set_reveal_child(False)
                return False
                
            GLib.timeout_add(2000, hide_progress_bar)
        else:
            self.logging.log(LogLevel.Error, "Failed to install speedtest-cli")
            self.speedtest_button.set_sensitive(False)
            self.speedtest_button.set_tooltip_text("Failed to install speedtest-cli")
            self.speedtest_progress_bar.set_text("Installation failed")
            self.speedtest_progress_bar.set_fraction(0)
            
        return False  # required for GLib.idle_add
    
    def on_speedtest_progress(self, progress, stage):
        """Handle speedtest progress updates"""
        GLib.idle_add(self._update_speedtest_progress, progress, stage)
    
    def _update_speedtest_progress(self, progress, stage):
        """Update the speedtest progress bar in the UI thread"""
        self.speedtest_progress_bar.set_text(stage)
        self.speedtest_progress_bar.set_fraction(progress / 100.0)
        return False  # required for GLib.idle_add
    
    def on_speedtest_complete(self, result):
        """Handle speedtest completion"""
        GLib.idle_add(self._update_speedtest_results, result)
    
    def _update_speedtest_results(self, result):
        """Update the UI with speedtest results in the UI thread"""
        # Update button text
        self.speedtest_button.get_children()[0].get_children()[1].set_text(getattr(self.txt, "run_test", "Run Test"))
        
        if result.error:
            self.logging.log(LogLevel.Error, f"Speedtest failed: {result.error}")
            self.speedtest_progress_bar.set_text(f"Test failed: {result.error}")
            return False
            
        # Update progress bar
        self.speedtest_progress_bar.set_text("Test completed")
        self.speedtest_progress_bar.set_fraction(1.0)
        
        # Update result labels
        self.download_result_label.set_text(f"{result.download:.2f} Mbps")
        self.upload_result_label.set_text(f"{result.upload:.2f} Mbps")
        self.ping_result_label.set_text(f"{result.ping:.2f} ms")
        self.jitter_result_label.set_text(f"{result.jitter:.2f} ms")
        self.isp_result_label.set_text(result.isp)
        
        server_text = result.server_name
        if result.server_location:
            server_text += f" ({result.server_location})"
        self.server_result_label.set_text(server_text)
        
        # Show results grid
        self.results_revealer.set_reveal_child(True)
        
        return False  # required for GLib.idle_add

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

        row.add(box)
        self.networks_box.add(row)

        def add_animation_with_delay(row_widget, index):
            if row_widget and row_widget.get_parent() is not None:
                row_widget.get_style_context().add_class("fade-in")

                def remove_animation_class():
                    if row_widget and row_widget.get_parent() is not None:
                        row_widget.get_style_context().remove_class("fade-in")
                    return False

                GLib.timeout_add(350, remove_animation_class)
            return False

        index = len(self.networks_box.get_children()) - 1
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

        qr_button = Gtk.Button()
        qr_button.set_tooltip_text("Show Qr code")
        qr_button.get_style_context().add_class("qr-button")
        qr_button.connect("clicked", self.show_qr_dialog)
        qr_icon = Gtk.Image.new_from_icon_name("qrscanner-symbolic", Gtk.IconSize.MENU)
        qr_button.set_image(qr_icon)
        container_box.pack_start(qr_button, False, False, 0)

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
            # Calculate byte difference
            rx_diff = rx_bytes - self.prev_rx_bytes
            tx_diff = tx_bytes - self.prev_tx_bytes
            
            # Convert bytes to bits (multiply by 8)
            # Then convert to megabits (divide by 1,000,000)
            # Since we poll every second, this gives us Mbps
            rx_speed = (rx_diff * 8) / 1000000
            tx_speed = (tx_diff * 8) / 1000000
            
            # Format based on speed ranges for more readable values
            if rx_speed < 0.1:
                download_text = f"Download: {rx_speed * 1000:.1f} Kbps"
            else:
                download_text = f"Download: {rx_speed:.1f} Mbps"
                
            if tx_speed < 0.1:
                upload_text = f"Upload: {tx_speed * 1000:.1f} Kbps"
            else:
                upload_text = f"Upload: {tx_speed:.1f} Mbps"
                
            self.download_label.set_text(download_text)
            self.upload_label.set_text(upload_text)

        self.prev_rx_bytes = rx_bytes
        self.prev_tx_bytes = tx_bytes

        return True  # Continue the timer

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

    def show_qr_dialog(self, button):
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
                    dialog_title = getattr(self.txt, "wifi_share_title", "Share WiFi")

                    qr_dialog = Gtk.Dialog(
                        title=dialog_title,
                        parent=self.get_toplevel(),
                        flags=Gtk.DialogFlags.MODAL,
                    )
                    qr_dialog.set_default_size(0,0)
                    qr_dialog.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)

                    # header
                    header_bar = Gtk.HeaderBar()
                    header_bar.set_show_close_button(True)
                    header_bar.set_title(dialog_title)
                    qr_dialog.set_titlebar(header_bar)

                    # content area
                    content_area = qr_dialog.get_content_area()
                    content_area.set_spacing(10)
                    content_area.set_margin_top(10)
                    content_area.set_margin_bottom(10)
                    content_area.set_margin_start(10)
                    content_area.set_margin_end(10)

                    # for qr code image
                    top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                    top_box.set_margin_bottom(20)

                    # image holder
                    qr_button = Gtk.Button()
                    qr_button.set_size_request(124,124)
                    qr_button.set_relief(Gtk.ReliefStyle.NONE)
                    qr_button.get_style_context().add_class("qr_image_holder")
                    top_box.pack_start(qr_button, False, False, 0)

                    # fallback for wifi_share_scan
                    scan_text = getattr(self.txt, "wifi_share_scan", "Scan this QR code to join")
                    scan_label = Gtk.Label(label=scan_text)
                    scan_label.get_style_context().add_class("scan_label")
                    top_box.pack_start(scan_label, False, False, 0)

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

                    content_area.pack_start(top_box, False, True, 0)

                    # network details
                    bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
                    bottom_box.set_margin_top(1)

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

                    # add to bottom box
                    bottom_box.pack_start(ssid_box, False, False, 0)
                    bottom_box.pack_start(security_box, False, False, 0)

                    content_area.pack_start(bottom_box, False, True, 0)

                    qr_dialog.show_all()
                    qr_dialog.run()
                    qr_dialog.destroy()

                except Exception as e:
                    self.logging.log(LogLevel.Error, f"failed to open qr code dialog: {e}")
                    traceback.print_exc()

    def on_key_press(self, widget, event):
        """Handle key press events in the WiFi tab"""
        keyval = event.keyval
        
        # Key code 114 is 'r', 82 is 'R'
        if keyval in (114, 82):  # r/R key for refresh
            if self.power_switch.get_active():
                # Check if wifi is already loading or not
                for child in self.networks_box.get_children():
                    box = child.get_child()
                    if isinstance(box.get_children()[0], Gtk.Spinner):
                        self.logging.log(LogLevel.Info, "Already refreshing wifi, skipping")
                        return True
                        
                self.logging.log(LogLevel.Info, "Refreshing wifi networks via keybind")
                self.update_network_list()
                return True
            else:
                self.logging.log(LogLevel.Info, "Unable to refresh, wifi is disabled")
                
        return False  # Allow event propagation for unhandled keys
