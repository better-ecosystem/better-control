#!/usr/bin/env python3

import gi

from utils.translations import English, Spanish  # type: ignore
gi.require_version('Gtk', '3.0')
import subprocess
import os
import threading
from datetime import datetime
from gi.repository import Gtk, GLib,Gdk  # type: ignore
from utils.logger import LogLevel, Logger


class BatteryTab(Gtk.Box):
    def __init__(self, logging: Logger, txt: English|Spanish, parent=None):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.txt = txt
        self.logging = logging

        self.last_refresh_time = datetime.now()
        # Dictionary to track expanded state of battery cards
        self.expanded_batteries = {}

        self.__load_gui(parent)

        self.power_mode_dropdown = Gtk.ComboBoxText()
        self.power_modes = {
            self.txt.battery_power_saving: "power-saver",
            self.txt.battery_balanced: "balanced",
            self.txt.battery_performance: "performance",
        }

        for mode in self.power_modes.keys():
            self.power_mode_dropdown.append_text(mode)

        # Get saved mode from settings
        saved_mode = ''
        try:
            # Get current power plan using powerprofilesctl
            result = subprocess.run(
                "powerprofilesctl get", shell=True, capture_output=True, text=True
            )
            if result.returncode == 0:
                current_plan = result.stdout.strip()

                plan_mapping = {
                    "power-saver": "Power Saving",
                    "balanced": "Balanced",
                    "performance": "Performance",
                }
                if current_plan in plan_mapping:
                    saved_mode = current_plan
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed to get current power plan: {e}")

        matching_label = next(
            (label for label, value in self.power_modes.items() if value == saved_mode),
            self.txt.battery_balanced,
        )
        if matching_label:
            self.power_mode_dropdown.set_active(
                list(self.power_modes.keys()).index(matching_label)
            )
        else:
            self.logging.log(
                LogLevel.Warn,
                f"Unknown power mode '{saved_mode}', defaulting to Balanced",
            )
            self.power_mode_dropdown.set_active(
                list(self.power_modes.keys()).index("Balanced")
            )

        # Add dropdown to the UI
        self.dropdown_box.pack_start(self.power_mode_dropdown, True, True, 0)
        self.power_mode_box.pack_start(self.dropdown_box, False, False, 0)

        self.scroll_window.add(self.content_box)
        self.pack_start(self.scroll_window, True, True, 0)

        self.power_mode_dropdown.connect("changed", self.set_power_mode)
        
        self.connect('key-press-event', self.on_key_press)

        self.refresh_battery_info()
        GLib.timeout_add_seconds(10, self.refresh_battery_info)
        
    # keybinds for battery tab
    def on_key_press(self, widget, event):
        keyval = event.keyval
        
        if keyval in (114, 82):
            self.logging.log(LogLevel.Info, "Refreshing battery info via keybind")
            self.refresh_battery_info()
            return True

    def set_power_mode(self, widget):
        """Handle power mode change using powerprofilesctl."""
        selected_mode = widget.get_active_text()
        if selected_mode in self.power_modes:
            mode_value = self.power_modes[selected_mode]

            # Disable dropdown while processing
            self.power_mode_dropdown.set_sensitive(False)

            # Create and start thread for async operation
            def run_power_change():
                try:
                    command = f"powerprofilesctl set {mode_value}"
                    result = subprocess.run(
                        command, shell=True, capture_output=True, text=True
                    )

                    # Use GLib.idle_add to update UI from the main thread
                    def update_ui():
                        self.power_mode_dropdown.set_sensitive(True)

                        if result.returncode != 0:
                            error_message = "powerprofilesctl is missing. Please check our GitHub page to see all dependencies and install them."
                            self.logging.log(LogLevel.Error, error_message)
                            if self.parent:
                                self.parent.show_error_dialog(error_message)
                        else:
                            self.logging.log(
                                LogLevel.Info,
                                f"Power mode changed to: {selected_mode} ({mode_value})",
                            )
                            # Refresh the UI to update button styles
                            self.refresh_battery_info()
                        return False

                    GLib.idle_add(update_ui)

                except Exception as e:
                    def handle_error(e=e):  # Capture the exception in the closure
                        self.power_mode_dropdown.set_sensitive(True)
                        error_message = f"Failed to set power mode: {e}"
                        self.logging.log(LogLevel.Error, error_message)
                        if self.parent:
                            self.parent.show_error_dialog(error_message)
                        return False

                    GLib.idle_add(handle_error)

            # Start the thread
            thread = threading.Thread(target=run_power_change, daemon=True)
            thread.start()

    def get_battery_devices(self):
        """Get list of battery devices from UPower."""
        devices = []
        try:
            # List all UPower devices
            result = subprocess.run(
                "upower -e", shell=True, capture_output=True, text=True
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    # Only include battery devices
                    if "battery" in line.lower():
                        devices.append(line)
            return devices
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed to get UPower devices: {e}")
            return []

    def parse_upower_output(self, output):
        """Parse the output of upower -i command into a dict."""
        info = {}

        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Check if this is a main property line (contains a colon)
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Skip empty values
                if not value:
                    continue

                # Map UPower keys to more user-friendly labels
                key_mapping = {
                    "vendor": "Manufacturer",
                    "model": "Model",
                    "serial": "Serial",  # Added serial mapping
                    "state": "State",
                    "warning-level": "Warning Level",
                    "energy": "Energy",
                    "energy-empty": "Energy Empty",
                    "energy-full": "Energy Full",
                    "energy-full-design": "Energy Full Design",
                    "energy-rate": "Energy Rate",
                    "voltage": "Voltage",
                    "time to empty": "Time to Empty",
                    "time to full": "Time to Full",
                    "percentage": "Charge",
                    "capacity": "Capacity",
                    "technology": "Technology",
                    "updated": "Updated",  # Added updated mapping
                }

                display_key = key_mapping.get(key, key.capitalize())
                info[display_key] = value

        return info

    def create_battery_card(self, battery_info, device_path):
        """Create a modern card-style widget for battery information."""
        # Extract basic info first to reduce complexity
        charge_percentage = self._get_charge_percentage(battery_info)
        state_text = battery_info.get("State", "Unknown")
        icon_name = self._get_battery_icon(charge_percentage, state_text)
        title = self._get_battery_title(battery_info, device_path)

        # Main card container
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        card.set_margin_top(10)
        card.set_margin_bottom(10)
        card.set_margin_start(10)
        card.set_margin_end(10)

        # Create header for expander
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Battery icon in header
        battery_icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        header_box.pack_start(battery_icon, False, False, 0)

        # Battery name & percentage
        header_label = Gtk.Label(xalign=0)
        header_label.set_markup(f"<b>{title}</b> - {charge_percentage}%")
        header_box.pack_start(header_label, True, True, 5)

        # Create the expander widget
        expander = Gtk.Expander()
        expander.set_label_widget(header_box)

        # Set expander state based on previous state
        device_id = os.path.basename(device_path)
        expander.set_expanded(self.expanded_batteries.get(device_id, False))

        expander.set_margin_top(10)
        expander.set_margin_bottom(5)
        expander.set_margin_start(15)
        expander.set_margin_end(15)

        # Container for expanded content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_box.set_margin_top(10)
        content_box.set_margin_bottom(10)
        content_box.set_margin_start(15)
        content_box.set_margin_end(15)

        # Manufacturer info
        manufacturer = battery_info.get("Manufacturer", "Unknown")
        manufacturer_label = Gtk.Label(xalign=0)
        manufacturer_label.set_markup(f"<span size='small'>Manufacturer: {manufacturer}</span>")
        content_box.pack_start(manufacturer_label, False, False, 0)

        # Battery detailed status
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        status_box.set_margin_top(10)

        # Detailed percentage
        charge_label = Gtk.Label()
        charge_label.set_markup(f"<span size='x-large'><b>{charge_percentage}%</b></span>")
        status_box.pack_start(charge_label, False, False, 0)

        # State label
        state_label = Gtk.Label()
        state_label.set_markup(f"<span size='large'>{state_text.capitalize()}</span>")
        status_box.pack_start(state_label, False, False, 15)

        # Time estimates
        if "Time to Empty" in battery_info and "discharging" in state_text.lower():
            time_label = Gtk.Label(xalign=0)
            time_label.set_markup(f"<span weight='bold'>Time remaining:</span> {battery_info['Time to Empty']}")
            status_box.pack_end(time_label, False, False, 0)
        elif "Time to Full" in battery_info and "charging" in state_text.lower():
            time_label = Gtk.Label(xalign=0)
            time_label.set_markup(f"<span weight='bold'>Full in:</span> {battery_info['Time to Full']}")
            status_box.pack_end(time_label, False, False, 0)

        content_box.pack_start(status_box, False, False, 0)

        # Battery level bar
        level_bar = Gtk.LevelBar()
        level_bar.set_min_value(0.0)
        level_bar.set_max_value(100.0)
        level_bar.set_value(charge_percentage)
        level_bar.set_size_request(-1, 15)
        level_bar.set_hexpand(True)

        # Set custom level bar colors
        level_bar.add_offset_value("low", 20.0)
        level_bar.add_offset_value("high", 50.0)
        level_bar.add_offset_value("full", 90.0)

        # Style the level bar based on state
        level_bar_context = level_bar.get_style_context()
        if "charging" in state_text.lower():
            level_bar_context.add_class("charging")
        elif "fully-charged" in state_text.lower():
            level_bar_context.add_class("full")
        elif charge_percentage <= 20:
            level_bar_context.add_class("critical")

        content_box.pack_start(level_bar, False, False, 10)

        # Add separator before detailed tabs
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(5)
        separator.set_margin_bottom(15)
        content_box.pack_start(separator, False, False, 0)

        # Notebook with tabs
        notebook = Gtk.Notebook()

        # Create tabs for different categories
        self.add_info_tab(notebook, self.txt.battery_overview, battery_info, [
            "Charge", "State", "Capacity", "Technology",
            "Energy Rate", "Voltage"
        ])

        # Add Serial and Updated to the Details tab
        self.add_info_tab(notebook, self.txt.battery_details, battery_info, [
            "Energy", "Energy Empty", "Energy Full",
            "Energy Full Design", "Warning Level",
            "Serial", "Updated"  # Added Serial and Updated fields
        ])

        content_box.pack_start(notebook, True, True, 0)

        # Add content to expander
        expander.add(content_box)

        # Log expand/collapse events
        def on_expander_toggled(widget, param):
            is_expanded = widget.get_expanded()
            # Store expanded state for this device
            device_id = os.path.basename(device_path)
            self.expanded_batteries[device_id] = is_expanded

            if is_expanded:
                self.logging.log(LogLevel.Info, f"Expanded details for {title}")
            else:
                self.logging.log(LogLevel.Info, f"Collapsed details for {title}")

        expander.connect("notify::expanded", on_expander_toggled)

        # Add the expander to the card
        card.pack_start(expander, True, True, 0)

        return card

    def _get_charge_percentage(self, battery_info):
        """Extract charge percentage from battery info."""
        if "Charge" in battery_info:
            try:
                charge_text = battery_info["Charge"]
                return int(charge_text.split("%")[0])
            except (ValueError, IndexError):
                pass
        return 0

    def _get_battery_icon(self, charge_percentage, state_text):
        """Get appropriate battery icon based on charge and state."""
        icon_name = "battery-empty-symbolic"
        if charge_percentage > 10:
            icon_name = "battery-low-symbolic"
        if charge_percentage > 30:
            icon_name = "battery-good-symbolic"
        if charge_percentage > 60:
            icon_name = "battery-full-symbolic"

        if "charging" in state_text.lower():
            icon_name = "battery-good-charging-symbolic"

        return icon_name

    def _get_battery_title(self, battery_info, device_path):
        """Generate title for battery card."""
        if "Model" in battery_info:
            return battery_info["Model"]
        return f"Battery {os.path.basename(device_path)}"

    def add_info_tab(self, notebook, title, battery_info, fields):
        """Add a tab with styled grid of battery information."""
        grid = Gtk.Grid()
        grid.set_column_spacing(20)
        grid.set_row_spacing(12)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_start(15)
        grid.set_margin_end(15)

        row = 0
        for key in fields:
            if key in battery_info:
                key_label = Gtk.Label(xalign=0)
                key_label.set_markup(f"<b>{key}:</b>")
                grid.attach(key_label, 0, row, 1, 1)

                value_label = Gtk.Label(xalign=0)
                value_label.set_text(battery_info[key])
                value_label.set_hexpand(True)
                grid.attach(value_label, 1, row, 1, 1)
                row += 1

        # If there are no fields with data, show a message
        if row == 0:
            no_data_label = Gtk.Label()
            no_data_label.set_text("No data available")
            no_data_label.set_margin_top(20)
            no_data_label.set_margin_bottom(20)
            grid.attach(no_data_label, 0, 0, 2, 1)

        # Add tab
        tab_label = Gtk.Label(title)
        notebook.append_page(grid, tab_label)

    def refresh_battery_info(self, button=None):
        """Refresh battery information using UPower with improved visual representation."""
        if button:
            self.logging.log(
                LogLevel.Info, "Manual refresh of battery information requested"
            )

        for child in self.content_box.get_children():
            self.content_box.remove(child)

        # Add power mode selector with simpler style suitable for dark themes
        mode_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        mode_container.set_margin_top(10)
        mode_container.set_margin_bottom(15)

        # Power mode selector with streamlined buttons
        mode_selector = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        mode_selector.set_homogeneous(True)  # Make all buttons equal width

        mode_icons = {
            self.txt.battery_power_saving: "power-profile-power-saver-symbolic",
            self.txt.battery_balanced: "power-profile-balanced-symbolic",
            self.txt.battery_performance: "power-profile-performance-symbolic"
        }

        # Get current active mode
        active_mode = self.power_mode_dropdown.get_active_text()

        for mode, profile in self.power_modes.items():
            mode_button = Gtk.Button()

            # Button content
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            button_box.set_margin_top(8)
            button_box.set_margin_bottom(8)

            # Icon
            icon = Gtk.Image.new_from_icon_name(mode_icons.get(mode, "dialog-question-symbolic"), Gtk.IconSize.BUTTON)
            button_box.pack_start(icon, False, False, 0)

            # Label - only show text when there's enough space
            label = Gtk.Label(mode)
            button_box.pack_start(label, True, False, 0)

            mode_button.add(button_box)
            mode_button.connect("clicked", self.on_power_mode_button_clicked, mode)

            # First remove all style classes related to selection
            context = mode_button.get_style_context()
            context.remove_class("suggested-action")

            # Style active button
            if mode == active_mode:
                context.add_class("suggested-action")

            mode_selector.pack_start(mode_button, True, True, 0)

        mode_container.pack_start(mode_selector, False, False, 0)

        # Add power mode to content
        self.content_box.pack_start(mode_container, False, False, 0)

        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.content_box.pack_start(separator, False, False, 0)

        # Get battery devices
        battery_devices = self.get_battery_devices()

        if not battery_devices:
            # Create styled "no battery" message
            no_battery_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            no_battery_box.set_halign(Gtk.Align.CENTER)
            no_battery_box.set_valign(Gtk.Align.CENTER)
            no_battery_box.set_margin_top(50)

            # Icon
            no_battery_icon = Gtk.Image.new_from_icon_name(
                "battery-missing-symbolic", Gtk.IconSize.DIALOG
            )
            no_battery_box.pack_start(no_battery_icon, False, False, 0)

            # Message
            no_battery_label = Gtk.Label()
            no_battery_label.set_markup(f"<span size='large'>{self.txt.battery_no_batteries}</span>")
            no_battery_box.pack_start(no_battery_label, False, False, 10)

            self.content_box.pack_start(no_battery_box, True, True, 0)
        else:
            # Create a container for battery cards
            batteries_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
            batteries_container.set_halign(Gtk.Align.FILL)
            batteries_container.set_hexpand(True)

            # Title for batteries section
            batteries_title = Gtk.Label(xalign=0)
            batteries_title.set_markup(f"<span weight='bold' size='large'>{self.txt.battery_batteries}</span>")
            batteries_title.set_margin_top(5)
            batteries_title.set_margin_bottom(5)
            batteries_container.pack_start(batteries_title, False, False, 0)

            # Process each battery
            for device_path in battery_devices:
                try:
                    # Run upower command for this battery
                    result = subprocess.run(
                        f"upower -i {device_path}",
                        shell=True,
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        battery_info = self.parse_upower_output(result.stdout)

                        # Create a styled card for this battery
                        battery_card = self.create_battery_card(battery_info, device_path)
                        batteries_container.pack_start(battery_card, False, False, 0)
                except Exception as e:
                    self.logging.log(
                        LogLevel.Error, f"Error processing battery {device_path}: {e}"
                    )

            # Add battery container to the main content
            self.content_box.pack_start(batteries_container, False, False, 0)

        # Show all widgets
        self.content_box.show_all()

        # Update refresh time
        self.last_refresh_time = datetime.now()

        return True

    def on_power_mode_button_clicked(self, button, mode):
        """Handle click on power mode button."""
        # Disable all mode buttons while processing
        for child in button.get_parent().get_children():
            child.set_sensitive(False)

        # Find index of the selected mode
        if mode in self.power_modes:
            index = list(self.power_modes.keys()).index(mode)
            # Set the dropdown to this index (will trigger the "changed" signal)
            self.power_mode_dropdown.set_active(index)

    def __load_gui(self, parent):
        self.set_margin_top(15)
        self.set_margin_bottom(15)
        self.set_margin_start(15)
        self.set_margin_end(15)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.parent = parent

        # Create header box with title and refresh button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header_box.set_hexpand(True)

        # Create title box with icon and label
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Add battery icon with hover animations
        battery_icon = Gtk.Image.new_from_icon_name(
            "battery-good-symbolic", Gtk.IconSize.DIALOG
        )
        ctx = battery_icon.get_style_context()
        ctx.add_class("battery-icon")

        def on_enter(widget, event):
            ctx.add_class("battery-icon-animate")

        def on_leave(widget, event):
            ctx.remove_class("battery-icon-animate")

        # Wrap in event box for hover detection
        icon_event_box = Gtk.EventBox()
        icon_event_box.add(battery_icon)
        icon_event_box.connect("enter-notify-event", on_enter)
        icon_event_box.connect("leave-notify-event", on_leave)

        title_box.pack_start(icon_event_box, False, False, 0)

        # Add title
        self.battery_label = Gtk.Label()
        self.battery_label.set_markup(
            f"<span weight='bold' size='large'>{self.txt.battery_title}</span>"
        )
        self.battery_label.set_halign(Gtk.Align.START)
        title_box.pack_start(self.battery_label, False, False, 0)

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
        refresh_tooltip = getattr(self.txt, "refresh_tooltip", "Refresh Info")
        self.refresh_button.set_tooltip_text(refresh_tooltip)
        self.refresh_button.connect("clicked", self.refresh_battery_info)
        
        # Hover behavior
        self.refresh_button.set_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.refresh_button.connect("enter-notify-event", self.on_refresh_enter)
        self.refresh_button.connect("leave-notify-event", self.on_refresh_leave)

        # Add refresh button to header
        header_box.pack_end(self.refresh_button, False, False, 0)
        self.pack_start(header_box, False, False, 0)


        # Create scrollable content
        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll_window.set_vexpand(True)

        # Create main content box - store as instance variable to update later
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.content_box.set_margin_top(10)
        self.content_box.set_margin_bottom(10)
        self.content_box.set_margin_start(10)
        self.content_box.set_margin_end(10)
        self.content_box.set_hexpand(True)
        self.content_box.set_vexpand(True)

        # Power mode section (hidden as we'll create this dynamically)
        self.power_mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.power_mode_label = Gtk.Label(label="Select Power Mode:")
        self.power_mode_label.set_halign(Gtk.Align.START)
        self.power_mode_label.set_markup("<b>Select Power Mode:</b>")
        self.power_mode_box.pack_start(self.power_mode_label, False, False, 0)

        # Mode selection dropdown (hidden but functional for logic)
        self.dropdown_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.dropdown_box.set_margin_top(5)
        # Note: The dropdown is not visible but set active in code to trigger mode change


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