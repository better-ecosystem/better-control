#!/usr/bin/env python3

import gi  # type: ignore

from utils.logger import LogLevel, Logger
from utils.translations import English, Spanish

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk # type: ignore

from tools.bluetooth import (
    get_bluetooth_status,
    set_bluetooth_power,
    get_devices,
    start_discovery,
    stop_discovery,
    connect_device_async,
    disconnect_device_async,
)
from ui.widgets.bluetooth_device_row import BluetoothDeviceRow


class BluetoothTab(Gtk.Box):
    """Bluetooth settings tab"""

    def __init__(self, logging: Logger, txt: English|Spanish):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.txt = txt
        self.logging = logging

        self.set_margin_start(15)
        self.set_margin_end(15)
        self.set_margin_top(15)
        self.set_margin_bottom(15)
        self.set_hexpand(True)
        self.set_vexpand(True)

        # State tracking
        self.is_discovering = False
        self.discovery_timeout_id = None
        self.discovery_check_id = None

        # Create header box with title and refresh button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header_box.set_hexpand(True)

        # Create title box with icon and label
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Add bluetooth icon with hover animations
        bluetooth_icon = Gtk.Image.new_from_icon_name(
            "bluetooth-symbolic", Gtk.IconSize.DIALOG
        )
        ctx = bluetooth_icon.get_style_context()
        ctx.add_class("bluetooth-icon")

        def on_enter(widget, event):
            ctx.add_class("bluetooth-icon-animate")

        def on_leave(widget, event):
            ctx.remove_class("bluetooth-icon-animate")

        # Wrap in event box for hover detection
        icon_event_box = Gtk.EventBox()
        icon_event_box.add(bluetooth_icon)
        icon_event_box.connect("enter-notify-event", on_enter)
        icon_event_box.connect("leave-notify-event", on_leave)

        title_box.pack_start(icon_event_box, False, False, 0)

        # Add title
        bluetooth_label = Gtk.Label()
        bluetooth_label.set_markup(
            f"<span weight='bold' size='large'>{self.txt.bluetooth_title}</span>"
        )
        bluetooth_label.set_halign(Gtk.Align.START)
        title_box.pack_start(bluetooth_label, False, False, 0)

        header_box.pack_start(title_box, True, True, 0)

        # Add combined refresh/scan button with expandable animation
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
        refresh_tooltip = getattr(self.txt, "refresh_tooltip", "Refresh and Scan for Devices")
        self.refresh_button.set_tooltip_text(refresh_tooltip)
        self.refresh_button.connect("clicked", self.on_scan_clicked)
        
        # Hover behavior
        self.refresh_button.set_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.refresh_button.connect("enter-notify-event", self.on_refresh_enter)
        self.refresh_button.connect("leave-notify-event", self.on_refresh_leave)

        # Add refresh button to header
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

        # Bluetooth power switch
        power_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        power_label = Gtk.Label(label=self.txt.bluetooth_power)
        power_label.set_markup(f"<b>{self.txt.bluetooth_power}</b>")
        power_label.set_halign(Gtk.Align.START)
        self.power_switch = Gtk.Switch()
        self.power_switch.set_active(get_bluetooth_status(self.logging))
        self.power_switch.connect("notify::active", self.on_power_switched)
        power_box.pack_start(power_label, False, True, 0)
        power_box.pack_end(self.power_switch, False, True, 0)
        content_box.pack_start(power_box, False, True, 0)

        # Device list section
        devices_label = Gtk.Label()
        devices_label.set_markup(f"<b>{self.txt.bluetooth_available_devices}</b>")
        devices_label.set_halign(Gtk.Align.START)
        devices_label.set_margin_top(15)
        content_box.pack_start(devices_label, False, True, 0)

        # Device list
        devices_frame = Gtk.Frame()
        devices_frame.set_shadow_type(Gtk.ShadowType.IN)
        self.devices_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.devices_box.set_margin_start(10)
        self.devices_box.set_margin_end(10)
        self.devices_box.set_margin_top(10)
        self.devices_box.set_margin_bottom(10)

        devices_frame.add(self.devices_box)
        content_box.pack_start(devices_frame, True, True, 0)

        scroll_window.add(content_box)
        self.pack_start(scroll_window, True, True, 0)

        # Check for connected Bluetooth devices and switch audio if necessary
        devices = get_devices(self.logging)
        for device in devices:
            if device['connected']:
                from tools.bluetooth import get_bluetooth_manager
                manager = get_bluetooth_manager(self.logging)
                manager._switch_to_bluetooth_audio(device['path'])
                break

        # Initial device list population
        self.update_device_list()
        
        self.connect('key-press-event', self.on_key_press)

        # Set up periodic device list updates
        GLib.timeout_add(2000, self.periodic_update)


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
        
    # keybinds for bluetooth tab
    def on_key_press(self, widget, event):
        keyval = event.keyval
        
        if keyval in (114, 82):
            if self.power_switch.get_active():
                self.logging.log(LogLevel.Info, "Refreshing bluetooth list via keybind")
                self.update_device_list()
                return True
            else:
                self.logging.log(LogLevel.Info, "Unable to refresh devices, bluetooth is off")
                

    def update_device_list(self):
        """Update the list of Bluetooth devices"""
        # Clear existing devices
        try:
            for child in self.devices_box.get_children():
                self.devices_box.remove(child)
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error clearing device list: {e}")

        # Only add devices if Bluetooth is enabled
        if get_bluetooth_status(self.logging):
            # Add devices
            try:
                devices = get_devices(self.logging)
                for device in devices:
                    # Get battery info for connected devices
                    if device['connected']:
                        from tools.bluetooth import get_bluetooth_manager
                        manager = get_bluetooth_manager(self.logging)
                        battery = manager.get_device_battery(device['path'])
                        if battery is not None:
                            device['battery'] = battery
                    device_row = BluetoothDeviceRow(device, self.txt)
                    device_row.connect_button.connect(
                        "clicked", self.on_connect_clicked, device["path"]
                    )
                    device_row.disconnect_button.connect(
                        "clicked", self.on_disconnect_clicked, device["path"]
                    )
                    self.devices_box.pack_start(device_row, False, True, 0)
            except Exception as e:
                self.logging.log(LogLevel.Error, f"Error populating device list: {e}")

        self.devices_box.show_all()

    def periodic_update(self):
        """Update the device list periodically"""
        try:
            # Skip update if tab is being destroyed
            if hasattr(self, 'is_being_destroyed') and self.is_being_destroyed:
                return False

            self.update_device_list()
            return True  # Keep the timer active
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error in periodic update: {e}")
            return True  # Keep trying

    def __del__(self):
        """Clean up resources when tab is destroyed"""
        try:
            self.cleanup_resources()
        except Exception:
            pass  # Can't log during __del__

    def on_destroy(self, widget):
        """Clean up resources when tab is destroyed"""
        self.is_being_destroyed = True
        self.cleanup_resources()

    def cleanup_resources(self):
        """Clean up all resources used by the tab"""
        # Stop discovery if active
        if self.is_discovering:
            try:
                stop_discovery(self.logging)
                self.is_discovering = False
            except Exception as e:
                self.logging.log(LogLevel.Error, f"Error stopping discovery: {e}")

        # Remove timers
        if self.discovery_timeout_id is not None:
            try:
                GLib.source_remove(self.discovery_timeout_id)
                self.discovery_timeout_id = None
            except Exception as e:
                self.logging.log(LogLevel.Error, f"Error removing discovery timeout: {e}")

        if self.discovery_check_id is not None:
            try:
                GLib.source_remove(self.discovery_check_id)
                self.discovery_check_id = None
            except Exception as e:
                self.logging.log(LogLevel.Error, f"Error removing discovery check: {e}")

        self.logging.log(LogLevel.Debug, "Bluetooth tab resources cleaned up")

    def on_power_switched(self, switch, gparam):
        """Handle Bluetooth power switch changes

        Args:
            switch (Gtk.Switch): The power switch widget
            gparam: GObject parameter
        """
        is_enabled = switch.get_active()
        # Store the original state in case we need to revert
        original_state = not is_enabled 
        
        success = set_bluetooth_power(is_enabled, self.logging)

        if not success:
            self.logging.log(LogLevel.Error, "Failed to change Bluetooth power state.")
            # Revert the switch state visually
            # Use idle_add to ensure UI updates happen on the main thread
            # and avoid potential signal loop issues
            def revert_switch():
                switch.handler_block_by_func(self.on_power_switched)
                switch.set_active(original_state)
                switch.handler_unblock_by_func(self.on_power_switched)
                
                # Show an error message
                dialog = Gtk.MessageDialog(
                    transient_for=self.get_toplevel(),
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text=getattr(self.txt, 'bluetooth_power_failed_title', "Bluetooth Power Error") # Added default
                )
                # Add secondary text if available in translations
                secondary_text = getattr(self.txt, 'bluetooth_power_failed_message', 
                                         "Could not change Bluetooth power state. Check system logs or permissions.")
                dialog.format_secondary_text(secondary_text)
                dialog.run()
                dialog.destroy()
                return False # Important for GLib.idle_add

            GLib.idle_add(revert_switch)
            return # Stop further processing

        # Update UI based on Bluetooth state (only if successful)
        if is_enabled:
            # Bluetooth enabled - refresh button should be active
            self.refresh_button.set_sensitive(True)
            # Update device list
            self.update_device_list()
        else:
            # Bluetooth disabled - refresh button should be disabled
            self.refresh_button.set_sensitive(False)
            # Clear all devices from the list
            try: # Add try-except for safety
                for child in self.devices_box.get_children():
                    self.devices_box.remove(child)
                self.devices_box.show_all()
            except Exception as e:
                 self.logging.log(LogLevel.Error, f"Error clearing devices after power off: {e}")
            # If we're discovering, stop it
            if self.is_discovering:
                self.stop_scan(self.refresh_button)

    def on_scan_clicked(self, button):
        """Handle scan button clicks

        Args:
            button (Gtk.Button): The scan button widget
        """
        # If already scanning, stop the scan
        if self.is_discovering:
            self.stop_scan(button)
            return

        self.logging.log(LogLevel.Info, "Starting Bluetooth device scan")
        # Update button during scan
        button.set_sensitive(False)
        self.refresh_label.set_label(self.txt.bluetooth_scanning)
        self.refresh_revealer.set_reveal_child(True)

        # Start discovery
        try:
            start_discovery(self.logging)
            self.is_discovering = True
        except Exception as e:
            self.logging.log(
                LogLevel.Error, f"Failed to start Bluetooth discovery: {e}"
            )
            button.set_label(self.txt.bluetooth_scan_devices)
            button.set_sensitive(True)
            return

        # Store the start time
        self.scan_start_time = GLib.get_monotonic_time()

        # Schedule periodic checks
        def check_scan_status():
            if not self.is_discovering:
                return False

            current_time = GLib.get_monotonic_time()
            elapsed_seconds = (
                current_time - self.scan_start_time
            ) / 1000000  # Convert to seconds
            # If scan has been running for more than 30 seconds, force stop
            if elapsed_seconds > 30:
                self.logging.log(
                    LogLevel.Warn, "Bluetooth scan timeout reached. Forcing stop."
                )
                self.stop_scan(button)
                return False
            return True

        # Add periodic check every 5 seconds
        if self.discovery_check_id:
            GLib.source_remove(self.discovery_check_id)
        self.discovery_check_id = GLib.timeout_add_seconds(5, check_scan_status)

        # Schedule stopping discovery after 10 seconds
        def stop_scan():
            if self.is_discovering:
                self.stop_scan(button)
            return False

        if self.discovery_timeout_id:
            GLib.source_remove(self.discovery_timeout_id)
        self.discovery_timeout_id = GLib.timeout_add_seconds(10, stop_scan)

    def stop_scan(self, button):
        """Stop the Bluetooth discovery process

        Args:
            button (Gtk.Button): The scan button widget
        """
        self.logging.log(LogLevel.Info, "Stopping Bluetooth device scan")
        if not self.is_discovering:
            button.set_sensitive(True)
            button.set_label(self.txt.bluetooth_scan_devices)
            return

        try:
            stop_discovery(self.logging)
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed to stop Bluetooth discovery: {e}")
        finally:
            self.is_discovering = False
            if self.discovery_timeout_id:
                GLib.source_remove(self.discovery_timeout_id)
                self.discovery_timeout_id = None
            if self.discovery_check_id:
                GLib.source_remove(self.discovery_check_id)
                self.discovery_check_id = None
            # Restore original button appearance with hover behavior
            button.set_sensitive(True)
            self.refresh_label.set_label("Refresh")
            self.refresh_revealer.set_reveal_child(False)
            # Force update the button appearance
            self.refresh_btn_box.queue_draw()
            self.update_device_list()

    def on_connect_clicked(self, button, device_path):
        """Handle device connect button clicks

        Args:
            button (Gtk.Button): The connect button widget
            device_path (str): DBus path of the device
        """
        # Store button reference in a dictionary keyed by device path
        if not hasattr(self, '_processing_buttons'):
            self._processing_buttons = {}
        self._processing_buttons[device_path] = button

        # Disable the button and show a spinner to indicate connection in progress
        button.set_sensitive(False)
        button.set_label(self.txt.connecting)

        # Create a spinner and add it to the button
        spinner = Gtk.Spinner()
        spinner.start()
        button.set_image(spinner)

        # Connect asynchronously
        def on_connect_complete(success):
            # Use GLib.idle_add to ensure we're on the main thread
            def update_ui():
                # Check if the button still exists and is valid
                if device_path not in self._processing_buttons:
                    return False

                stored_button = self._processing_buttons[device_path]
                # Make sure the button is still a valid GTK widget
                if not isinstance(stored_button, Gtk.Button) or not stored_button.get_parent():
                    # Button was removed from UI
                    del self._processing_buttons[device_path]
                    self.update_device_list()
                    return False

                # Button is still valid, update it
                stored_button.set_label(self.txt.connect)
                stored_button.set_image(None)
                stored_button.set_sensitive(True)

                # Clean up our reference
                del self._processing_buttons[device_path]

                if success:
                    # Just update the list
                    self.update_device_list()
                else:
                    # Show error in a dialog
                    dialog = Gtk.MessageDialog(
                        transient_for=self.get_toplevel(),
                        modal=True,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text=self.txt.bluetooth_connect_failed
                    )
                    dialog.format_secondary_text(self.txt.bluetooth_try_again)
                    dialog.run()
                    dialog.destroy()
                return False

            GLib.idle_add(update_ui)

        # Start the async connection
        connect_device_async(device_path, on_connect_complete, self.logging)

    def on_disconnect_clicked(self, button, device_path):
        """Handle device disconnect button clicks

        Args:
            button (Gtk.Button): The disconnect button widget
            device_path (str): DBus path of the device
        """
        # Store button reference in a dictionary keyed by device path
        if not hasattr(self, '_processing_buttons'):
            self._processing_buttons = {}
        self._processing_buttons[device_path] = button

        # Disable the button and show a spinner to indicate disconnection in progress
        button.set_sensitive(False)
        button.set_label(self.txt.disconnecting)

        # Create a spinner and add it to the button
        spinner = Gtk.Spinner()
        spinner.start()
        button.set_image(spinner)

        # Disconnect asynchronously
        def on_disconnect_complete(success):
            # Use GLib.idle_add to ensure we're on the main thread
            def update_ui():
                # Check if the button still exists and is valid
                if device_path not in self._processing_buttons:
                    return False

                stored_button = self._processing_buttons[device_path]
                # Make sure the button is still a valid GTK widget
                if not isinstance(stored_button, Gtk.Button) or not stored_button.get_parent():
                    # Button was removed from UI
                    del self._processing_buttons[device_path]
                    self.update_device_list()
                    return False

                # Button is still valid, update it
                stored_button.set_label(self.txt.disconnect)
                stored_button.set_image(None)
                stored_button.set_sensitive(True)

                # Clean up our reference
                del self._processing_buttons[device_path]

                if success:
                    # Just update the list
                    self.update_device_list()
                else:
                    # Show error in a dialog
                    dialog = Gtk.MessageDialog(
                        transient_for=self.get_toplevel(),
                        modal=True,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text=self.txt.bluetooth_disconnect_failed
                    )
                    dialog.format_secondary_text(self.txt.bluetooth_try_again)
                    dialog.run()
                    dialog.destroy()
                return False

            GLib.idle_add(update_ui)

        # Start the async disconnection
        disconnect_device_async(device_path, on_disconnect_complete, self.logging)
