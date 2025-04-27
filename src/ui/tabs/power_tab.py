#!/usr/bin/env python3

import gi # type: ignore

from utils.translations import Translation  # type: ignore
gi.require_version('Gtk', '3.0')
import subprocess
import json
import os
from gi.repository import Gtk, GLib, Gdk  # type: ignore
from utils.logger import LogLevel, Logger

class PowerTab(Gtk.Box):
    """Power management tab with suspend, shutdown and reboot options"""

    def __init__(self, logging: Logger, txt: Translation):
            super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            self.txt = txt

            self.logging = logging

            # Initialize visibility flag
            self.is_visible = False
            self.minimal_mode = False

            # Set default button visibility
            self.config_file = os.path.expanduser("~/.config/better-control/power_settings.json")
            self.active_buttons = self._load_settings()
            self.custom_commands = self.active_buttons.get("commands", {})
            self.custom_colors = self.active_buttons.get("colors", {})
            self.custom_shortcuts = self.active_buttons.get("shortcuts", {})
            self.show_keybinds = self.active_buttons.get("show_keybinds", True)

            # Connect visibility signals
            self.connect("map", self.on_mapped)
            self.connect("unmap", self.on_unmapped)

            # Log loaded shortcuts for debugging
            self.logging.log(LogLevel.Debug, f"Loaded shortcuts: {self.custom_shortcuts}")

            # Set margins to match other tabs
            self.set_margin_start(15)
            self.set_margin_end(15)
            self.set_margin_top(15)
            self.set_margin_bottom(15)
            self.set_hexpand(True)
            self.set_vexpand(True)

            # Create header box with title
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            header_box.set_hexpand(True)
            header_box.set_margin_bottom(20)

            # Create title box with icon and label
            title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

            # Add power icon with hover animations
            power_icon = Gtk.Image.new_from_icon_name(
                "system-shutdown-symbolic", Gtk.IconSize.DIALOG
            )
            ctx = power_icon.get_style_context()
            ctx.add_class("power-icon")

            def on_enter(widget, event):
                ctx.add_class("power-icon-animate")

            def on_leave(widget, event):
                ctx.remove_class("power-icon-animate")

            # Wrap in event box for hover detection
            icon_event_box = Gtk.EventBox()
            icon_event_box.add(power_icon)
            icon_event_box.connect("enter-notify-event", on_enter)
            icon_event_box.connect("leave-notify-event", on_leave)

            title_box.pack_start(icon_event_box, False, False, 0)

            # Add title with better styling
            title_label = Gtk.Label()
            title_label.set_markup(
                f"<span weight='bold' size='x-large'>{getattr(self.txt, 'power_title', 'Power')}</span>"
            )
            title_label.get_style_context().add_class("header-title")
            title_label.set_halign(Gtk.Align.START)
            title_box.pack_start(title_label, False, False, 0)

            header_box.pack_start(title_box, True, True, 0)

            # Create settings button
            settings_button = Gtk.Button()
            settings_button.set_tooltip_text(getattr(self.txt, 'power_tooltip_menu', 'Power Options'))
            self.settings_icon = Gtk.Image.new_from_icon_name(
                "emblem-system-symbolic", Gtk.IconSize.MENU
            )
            self.settings_icon.get_style_context().add_class("rotate-gear")
            settings_button.add(self.settings_icon)
            settings_button.get_style_context().add_class("flat")
            settings_button.connect("clicked", self.on_settings_clicked)
            header_box.pack_end(settings_button, False, False, 0)

            self.pack_start(header_box, False, False, 0)

            # Grid container
            self.grid_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            self.grid_container.set_hexpand(True)
            self.grid_container.set_vexpand(True)

            # Define power options with metadata
            self.power_options = [
                {
                    "id": "lock",
                    "label": getattr(self.txt, 'power_menu_lock', 'Lock'),
                    "icon": "system-lock-screen-symbolic",
                    "tooltip": getattr(self.txt, 'power_menu_tooltip_lock', 'Lock the session'),
                    "callback": self.on_lock_clicked,
                    "color": "#4A90D9",
                    "default_shortcut": "l"
                },
                {
                    "id": "logout",
                    "label": getattr(self.txt, 'power_menu_logout', 'Logout'),
                    "icon": "system-log-out-symbolic",
                    "tooltip": getattr(self.txt, 'power_menu_tooltip_logout', 'Logout current user'),
                    "callback": self.on_logout_clicked,
                    "color": "#729FCF",
                    "default_shortcut": "o"
                },
                {
                    "id": "suspend",
                    "label": getattr(self.txt, 'power_menu_suspend', 'Suspend'),
                    "icon": "system-suspend-symbolic",
                    "tooltip": getattr(self.txt, 'power_menu_tooltip_suspend', 'Suspend the system'),
                    "callback": self.on_suspend_clicked,
                    "color": "#8DB67A",
                    "default_shortcut": "s"
                },
                {
                    "id": "hibernate",
                    "label": getattr(self.txt, 'power_menu_hibernate', 'Hibernate'),
                    "icon": "document-save-symbolic",
                    "tooltip": getattr(self.txt, 'power_menu_tooltip_hibernate', 'Hibernate the system'),
                    "callback": self.on_hibernate_clicked,
                    "color": "#AD7FA8",
                    "default_shortcut": "h"
                },
                {
                    "id": "reboot",
                    "label": getattr(self.txt, 'power_menu_reboot', 'Reboot'),
                    "icon": "system-reboot-symbolic",
                    "tooltip": getattr(self.txt, 'power_menu_tooltip_reboot', 'Restart the computer'),
                    "callback": self.on_reboot_clicked,
                    "color": "#F8C146",
                    "default_shortcut": "r"
                },
                {
                    "id": "shutdown",
                    "label": getattr(self.txt, 'power_menu_shutdown', 'Shutdown'),
                    "icon": "system-shutdown-symbolic",
                    "tooltip": getattr(self.txt, 'power_menu_tooltip_shutdown', 'Power off the computer'),
                    "callback": self.on_shutdown_clicked,
                    "color": "#EF5350",
                    "default_shortcut": "p"
                }
            ]

            # Update power options with custom shortcuts
            self._update_power_options_shortcuts()

            # Build the grid with active buttons
            self._build_power_grid()
            self.pack_start(self.grid_container, True, True, 0)

            # Create settings popover
            self.settings_popover = Gtk.Popover()
            self.settings_popover.set_position(Gtk.PositionType.BOTTOM)
            self.settings_popover.set_relative_to(settings_button)

            # Create content for settings popover
            self._create_settings_content()

            # Add CSS for styling
            self._add_css()

            # Setup key event handling
            self.set_can_focus(True)
            self.grab_focus()

            # Connect to key-press-event at window level to ensure it works
            # We need to get the toplevel window to attach the event
            GLib.timeout_add(200, self._setup_key_handler)

    def _setup_key_handler(self):
        """Set up keyboard handler with a small delay to ensure window is ready"""
        # Get the toplevel window
        toplevel = self.get_toplevel()
        if toplevel and isinstance(toplevel, Gtk.Window):
            self.logging.log(LogLevel.Debug, "Setting up key handler on window")

            # Connect to key-press-event at window level
            handler_id = toplevel.connect("key-press-event", self.on_key_press)
            self.logging.log(LogLevel.Info, f"Connected key handler with ID: {handler_id}")

            # Try to grab focus
            self.grab_focus()

            # Check if we're in minimal mode
            if hasattr(toplevel, 'arg_parser') and hasattr(toplevel.arg_parser, 'find_arg'):
                self.minimal_mode = toplevel.arg_parser.find_arg(("-m", "--minimal"))
                if self.minimal_mode:
                    self.is_visible = True
                    self.logging.log(LogLevel.Info, "Power tab in minimal mode, keybindings always active")
        return False  # Don't call again

    def on_mapped(self, widget):
        """Called when the widget becomes visible"""
        self.is_visible = True
        self.logging.log(LogLevel.Info, "Power tab became visible, activating its keybindings")

    def on_unmapped(self, widget):
        """Called when the widget is hidden"""
        # Don't change visibility in minimal mode
        if not self.minimal_mode:
            self.is_visible = False
            self.logging.log(LogLevel.Info, "Power tab became hidden, deactivating its keybindings")

    def _update_power_options_shortcuts(self):
        """Update power options with custom shortcuts"""
        for option in self.power_options:
            option_id = option["id"]
            shortcut = self.custom_shortcuts.get(option_id, option["default_shortcut"])
            option["shortcut"] = shortcut
            self.logging.log(LogLevel.Debug, f"Set shortcut for {option_id}: {shortcut}")

    def on_key_press(self, widget, event):
        """Handle key press events to trigger power actions"""
        # Skip processing if not visible and not minimal mode
        if not self.minimal_mode and not self.is_visible:
            return False

        keyval = event.keyval
        keychar = chr(keyval).lower()

        for option in self.power_options:
            option_id = option["id"]
            if not self.active_buttons.get(option_id, True):
                continue

            shortcut = self.custom_shortcuts.get(option_id, option["default_shortcut"]).lower()

            if keychar == shortcut:
                self.logging.log(LogLevel.Info, f"Shortcut triggered for {option['label']}")
                option["callback"](None)
                self._close_application()
                return True

        return False

    def _load_settings(self):
        """Load power menu button settings"""
        default_shortcuts = {}
        for option in [
            {"id": "lock", "default_shortcut": "l"},
            {"id": "logout", "default_shortcut": "o"},
            {"id": "suspend", "default_shortcut": "s"},
            {"id": "hibernate", "default_shortcut": "h"},
            {"id": "reboot", "default_shortcut": "r"},
            {"id": "shutdown", "default_shortcut": "p"}
        ]:
            default_shortcuts[option["id"]] = option["default_shortcut"]

        default_settings = {
            "lock": True,
            "logout": True,
            "suspend": True,
            "hibernate": True,
            "reboot": True,
            "shutdown": True,
            "commands": {
                "lock": "loginctl lock-session",
                "logout": "loginctl terminate-user $USER",
                "suspend": "loginctl suspend",  # Changed from systemctl
                "hibernate": "loginctl hibernate", # Changed from systemctl
                "reboot": "loginctl reboot",   # Changed from systemctl
                "shutdown": "loginctl poweroff" # Changed from systemctl
            },
            "colors": {
                "lock": "#4A90D9",
                "logout": "#729FCF",
                "suspend": "#8DB67A",
                "hibernate": "#AD7FA8",
                "reboot": "#F8C146",
                "shutdown": "#EF5350"
            },
            "shortcuts": default_shortcuts,
            "show_keybinds": True
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge loaded settings with defaults, ensuring all keys exist
                    for key, default_value in default_settings.items():
                        if key not in loaded_settings:
                            loaded_settings[key] = default_value
                        elif isinstance(default_value, dict):
                            # Merge dictionaries (commands, colors, shortcuts)
                            for sub_key, sub_default_value in default_value.items():
                                if sub_key not in loaded_settings[key]:
                                    loaded_settings[key][sub_key] = sub_default_value
                    return loaded_settings
            else:
                # Ensure config directory exists
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                # Save default settings if file doesn't exist
                with open(self.config_file, 'w') as f:
                    json.dump(default_settings, f, indent=4)
                return default_settings
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error loading power settings: {e}")
            return default_settings

    def _save_settings(self):
        """Save power menu button settings"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.active_buttons, f, indent=2)
            self.logging.log(LogLevel.Info, "Power menu settings saved")
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed to save power settings: {e}")

    def _build_power_grid(self):
        """Build the power buttons grid based on active buttons"""
        # Clear existing children
        for child in self.grid_container.get_children():
            self.grid_container.remove(child)

        # Create new grid
        grid = Gtk.Grid()
        grid.set_row_spacing(20)
        grid.set_column_spacing(20)
        grid.set_row_homogeneous(True)
        grid.set_column_homogeneous(True)
        grid.set_halign(Gtk.Align.FILL)
        grid.set_valign(Gtk.Align.FILL)
        grid.set_hexpand(True)
        grid.set_vexpand(True)

        # Filter and add only active buttons
        active_options = [option for option in self.power_options
                          if self.active_buttons.get(option["id"], True)]

        # Calculate optimal grid dimensions to make it as square as possible
        num_buttons = len(active_options)

        # Determine best grid dimensions based on number of buttons
        if num_buttons <= 1:
            columns = 1
        elif num_buttons == 2:
            columns = 2  # 2 in a row
        elif num_buttons <= 4:
            columns = 2  # 2x2 grid
        elif num_buttons <= 6:
            columns = 3  # 3x2 grid
        elif num_buttons <= 9:
            columns = 3  # 3x3 grid
        elif num_buttons <= 12:
            columns = 4  # 3x4 grid
        else:
            columns = 4  # Default for larger numbers

        # Adjust button size based on grid dimensions
        button_size = 140 if columns <= 2 else 120

        # Create and arrange buttons in a grid
        for i, option in enumerate(active_options):
            # Get custom color if available
            color = self.custom_colors.get(option["id"], option["color"])

            # Get current shortcut for this option
            shortcut = self.custom_shortcuts.get(option["id"], option["default_shortcut"])

            # Add shortcut to label if enabled
            label_with_shortcut = option['label']
            if self.show_keybinds:
                label_with_shortcut = f"{option['label']} [{shortcut}]"

            button = self._create_power_button(
                label_with_shortcut,
                option["icon"],
                option["tooltip"],
                option["callback"],
                color,
                button_size
            )

            row = i // columns
            col = i % columns

            grid.attach(button, col, row, 1, 1)

        self.grid_container.pack_start(grid, True, True, 0)
        self.grid_container.show_all()

    def _create_settings_content(self):
            """Create content for settings popover"""
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            box.set_margin_start(12)
            box.set_margin_end(12)
            box.set_margin_top(12)
            box.set_margin_bottom(12)

            def build_visibility_tab():
                tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                tab.set_margin_start(10)
                tab.set_margin_end(10)
                tab.set_margin_top(10)
                tab.set_margin_bottom(10)

                lbl = Gtk.Label()
                lbl.set_markup(
                    f"<b>{getattr(self.txt, 'power_menu_show_hide_buttons', 'Show/hide buttons')}</b>"
                )
                lbl.set_halign(Gtk.Align.START)
                tab.pack_start(lbl, False, False, 0)

                tab.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)

                # Toggle for keybind visibility
                keybinds_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                keybinds_label = Gtk.Label(
                    label=getattr(self.txt, 'power_menu_show_keyboard_shortcut', 'Show keyboard shortcut labels')
                )
                keybinds_label.set_halign(Gtk.Align.START)
                keybinds_box.pack_start(keybinds_label, True, True, 0)

                self.keybinds_switch = Gtk.Switch()
                self.keybinds_switch.set_active(self.show_keybinds)
                self.keybinds_switch.connect("notify::active", self.on_keybinds_toggled)
                keybinds_box.pack_end(self.keybinds_switch, False, False, 0)
                tab.pack_start(keybinds_box, False, False, 5)

                tab.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)

                self.option_switches = {}
                for option in self.power_options:
                    option_id = option["id"]
                    container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

                    icon = Gtk.Image.new_from_icon_name(option["icon"], Gtk.IconSize.MENU)
                    container.pack_start(icon, False, False, 0)

                    label = Gtk.Label(label=option["label"])
                    label.set_halign(Gtk.Align.START)
                    container.pack_start(label, True, True, 0)

                    switch = Gtk.Switch()
                    switch.set_active(self.active_buttons.get(option_id, True))
                    switch.connect("notify::active", self.on_option_toggled, option_id)
                    self.option_switches[option_id] = switch
                    container.pack_end(switch, False, False, 0)

                    tab.pack_start(container, False, False, 5)

                vis_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic", Gtk.IconSize.MENU)
                vis_text = Gtk.Label(label=getattr(self.txt, 'power_menu_visibility', 'Visibility'))
                vis_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                vis_label_box.pack_start(vis_icon, False, False, 0)
                vis_label_box.pack_start(vis_text, False, False, 0)
                vis_label_box.show_all()
                return tab, vis_label_box

            def build_shortcuts_tab():
                tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                tab.set_margin_start(10)
                tab.set_margin_end(10)
                tab.set_margin_top(10)
                tab.set_margin_bottom(10)

                lbl = Gtk.Label()
                lbl.set_markup(
                    f"<b>{getattr(self.txt, 'power_menu_keyboard_shortcut', 'Keyboard Shortcuts')}</b>"
                )
                lbl.set_halign(Gtk.Align.START)
                tab.pack_start(lbl, False, False, 0)

                info = Gtk.Label()
                info.set_markup("<small>Press a single key to set the shortcut for each action</small>")
                info.set_halign(Gtk.Align.START)
                tab.pack_start(info, False, False, 5)

                tab.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)

                shortcuts_scrolled = Gtk.ScrolledWindow()
                shortcuts_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
                shortcuts_scrolled.set_vexpand(True)

                container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                self.shortcut_entries = {}

                for idx, option in enumerate(self.power_options):
                    option_id = option["id"]
                    current_shortcut = self.custom_shortcuts.get(option_id, option["default_shortcut"])

                    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

                    icon = Gtk.Image.new_from_icon_name(option["icon"], Gtk.IconSize.MENU)
                    row.pack_start(icon, False, False, 0)

                    label = Gtk.Label(label=f"{option['label']} Shortcut:")
                    label.set_halign(Gtk.Align.START)
                    row.pack_start(label, True, True, 0)

                    entry = Gtk.Entry()
                    entry.set_text(current_shortcut)
                    entry.set_width_chars(1)
                    entry.set_max_length(1)
                    entry.set_alignment(0.5)
                    entry.set_tooltip_text(f"Press a key to set the shortcut for {option['label']}")
                    entry.connect("key-press-event", self.on_shortcut_key_press, option_id)
                    self.shortcut_entries[option_id] = entry
                    row.pack_end(entry, False, False, 0)

                    reset_button = Gtk.Button()
                    reset_button.set_tooltip_text("Reset to default shortcut")
                    reset_icon = Gtk.Image.new_from_icon_name("edit-undo-symbolic", Gtk.IconSize.MENU)
                    reset_button.add(reset_icon)
                    reset_button.connect("clicked", self.on_reset_shortcut, option_id, entry, option["default_shortcut"])
                    row.pack_end(reset_button, False, False, 5)

                    container.pack_start(row, False, False, 5)

                    if idx < len(self.power_options) - 1:
                        container.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)

                shortcuts_scrolled.add(container)
                tab.pack_start(shortcuts_scrolled, True, True, 0)

                shortcuts_icon = Gtk.Image.new_from_icon_name("input-keyboard-symbolic", Gtk.IconSize.MENU)
                shortcuts_text = Gtk.Label(label=getattr(self.txt, 'power_menu_shortcuts_tab_label', 'Shortcuts'))
                shortcuts_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                shortcuts_label_box.pack_start(shortcuts_icon, False, False, 0)
                shortcuts_label_box.pack_start(shortcuts_text, False, False, 0)
                shortcuts_label_box.show_all()
                return tab, shortcuts_label_box

            def build_commands_tab():
                tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                tab.set_margin_start(10)
                tab.set_margin_end(10)
                tab.set_margin_top(10)
                tab.set_margin_bottom(10)

                lbl = Gtk.Label()
                lbl.set_markup("<b>Customize Commands</b>")
                lbl.set_halign(Gtk.Align.START)
                tab.pack_start(lbl, False, False, 0)

                tab.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)

                scrolled = Gtk.ScrolledWindow()
                scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
                scrolled.set_vexpand(True)

                container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                self.command_entries = {}

                for idx, option in enumerate(self.power_options):
                    option_id = option["id"]

                    # determine default
                    defaults_map = {
                        "lock": "loginctl lock-session",
                        "logout": "loginctl terminate-user $USER",
                        "suspend": "loginctl suspend",
                        "hibernate": "loginctl hibernate",
                        "reboot": "loginctl reboot",
                        "shutdown": "loginctl poweroff",
                    }
                    default_cmd = defaults_map.get(option_id, "")

                    current_cmd = self.active_buttons.get("commands", {}).get(option_id, default_cmd)

                    label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                    icon = Gtk.Image.new_from_icon_name(option["icon"], Gtk.IconSize.MENU)
                    label_box.pack_start(icon, False, False, 0)

                    label = Gtk.Label(label=f"{option['label']} Command:")
                    label.set_halign(Gtk.Align.START)
                    label_box.pack_start(label, True, True, 0)
                    container.pack_start(label_box, False, False, 0)

                    entry = Gtk.Entry()
                    entry.set_text(current_cmd)
                    entry.set_tooltip_text(f"Command to execute when {option['label']} button is clicked")
                    self.command_entries[option_id] = entry
                    container.pack_start(entry, False, False, 0)

                    reset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                    reset_box.set_halign(Gtk.Align.END)

                    reset_button = Gtk.Button()
                    reset_button.set_tooltip_text("Reset to default command")
                    reset_icon = Gtk.Image.new_from_icon_name("edit-undo-symbolic", Gtk.IconSize.MENU)
                    reset_button.add(reset_icon)
                    reset_button.connect("clicked", self.on_reset_command, option_id, entry, default_cmd)
                    reset_box.pack_end(reset_button, False, False, 0)

                    container.pack_start(reset_box, False, False, 0)

                    if idx < len(self.power_options) - 1:
                        container.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)

                scrolled.add(container)
                tab.pack_start(scrolled, True, True, 0)

                commands_icon = Gtk.Image.new_from_icon_name("utilities-terminal-symbolic", Gtk.IconSize.MENU)
                commands_text = Gtk.Label(label=getattr(self.txt, 'power_menu_commands', 'Commands'))
                commands_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                commands_label_box.pack_start(commands_icon, False, False, 0)
                commands_label_box.pack_start(commands_text, False, False, 0)
                commands_label_box.show_all()
                return tab, commands_label_box

            def build_colors_tab():
                tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                tab.set_margin_start(10)
                tab.set_margin_end(10)
                tab.set_margin_top(10)
                tab.set_margin_bottom(10)

                lbl = Gtk.Label()
                lbl.set_markup("<b>Customize Button Colors</b>")
                lbl.set_halign(Gtk.Align.START)
                tab.pack_start(lbl, False, False, 0)

                tab.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)

                scrolled = Gtk.ScrolledWindow()
                scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
                scrolled.set_vexpand(True)

                container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                self.color_buttons = {}

                for idx, option in enumerate(self.power_options):
                    option_id = option["id"]

                    defaults_map = {
                        "lock": "#4A90D9",
                        "logout": "#729FCF",
                        "suspend": "#8DB67A",
                        "hibernate": "#AD7FA8",
                        "reboot": "#F8C146",
                        "shutdown": "#EF5350",
                    }
                    default_color = defaults_map.get(option_id, "#888888")
                    current_color = self.custom_colors.get(option_id, default_color)

                    label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                    icon = Gtk.Image.new_from_icon_name(option["icon"], Gtk.IconSize.MENU)
                    label_box.pack_start(icon, False, False, 0)

                    label = Gtk.Label(label=f"{option['label']} Color:")
                    label.set_halign(Gtk.Align.START)
                    label_box.pack_start(label, True, True, 0)
                    container.pack_start(label_box, False, False, 0)

                    color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

                    color_button = Gtk.ColorButton()
                    color_button.set_tooltip_text(f"Select color for {option['label']} button")
                    rgba = self._hex_to_rgba(current_color)
                    color_button.set_rgba(rgba)

                    color_button.connect("color-set", self.on_color_selected, option_id)
                    self.color_buttons[option_id] = color_button

                    color_box.pack_start(color_button, False, False, 0)

                    color_entry = Gtk.Entry()
                    color_entry.set_text(current_color)
                    color_entry.set_width_chars(9)
                    color_entry.set_max_length(7)
                    color_entry.set_editable(False)
                    color_box.pack_start(color_entry, False, False, 0)

                    color_button.connect("color-set", self.on_update_color_entry, color_entry)

                    reset_button = Gtk.Button()
                    reset_button.set_tooltip_text("Reset to default color")
                    reset_icon = Gtk.Image.new_from_icon_name("edit-undo-symbolic", Gtk.IconSize.MENU)
                    reset_button.add(reset_icon)
                    reset_button.connect("clicked", self.on_reset_color, option_id, color_button, color_entry, default_color)
                    color_box.pack_end(reset_button, False, False, 0)

                    preview_button = Gtk.Button(label=option["label"])
                    preview_button.set_size_request(120, 30)

                    style_provider = Gtk.CssProvider()
                    css = f".preview-button {{ background-color: {current_color}; color: white; font-weight: bold; border-radius: 6px; }}"
                    style_provider.load_from_data(css.encode())
                    preview_button.get_style_context().add_class("preview-button")
                    preview_button.get_style_context().add_provider(
                        style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                    )

                    setattr(color_button, "preview_button", preview_button)
                    setattr(color_button, "preview_color", current_color)

                    color_box.pack_end(preview_button, True, True, 0)

                    container.pack_start(color_box, False, False, 0)

                    if idx < len(self.power_options) - 1:
                        container.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 10)

                scrolled.add(container)
                tab.pack_start(scrolled, True, True, 0)

                colors_icon = Gtk.Image.new_from_icon_name("applications-graphics-symbolic", Gtk.IconSize.MENU)
                colors_text = Gtk.Label(label=getattr(self.txt, 'power_menu_colors', 'Colors'))
                colors_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                colors_label_box.pack_start(colors_icon, False, False, 0)
                colors_label_box.pack_start(colors_text, False, False, 0)
                colors_label_box.show_all()
                return tab, colors_label_box

            notebook = Gtk.Notebook()
            notebook.set_size_request(400, 300)

            visibility_tab, visibility_label = build_visibility_tab()
            notebook.append_page(visibility_tab, visibility_label)

            shortcuts_tab, shortcuts_label = build_shortcuts_tab()
            notebook.append_page(shortcuts_tab, shortcuts_label)

            commands_tab, commands_label = build_commands_tab()
            notebook.append_page(commands_tab, commands_label)

            colors_tab, colors_label = build_colors_tab()
            notebook.append_page(colors_tab, colors_label)

            box.pack_start(notebook, True, True, 0)

            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            btn_box.set_halign(Gtk.Align.END)
            btn_box.set_margin_top(10)

            apply_button = Gtk.Button(label=getattr(self.txt, 'power_menu_apply', 'Apply'))
            apply_button.connect("clicked", self.on_apply_settings)
            btn_box.pack_end(apply_button, False, False, 0)

            box.pack_start(btn_box, False, False, 0)

            box.show_all()
            self.settings_popover.add(box)

    def on_option_toggled(self, switch, gparam, option_id):
        """Handle option switch toggle"""
        self.active_buttons[option_id] = switch.get_active()

    def on_keybinds_toggled(self, switch, gparam):
        """Handle keybinds visibility toggle"""
        self.show_keybinds = switch.get_active()
        self.active_buttons["show_keybinds"] = self.show_keybinds

    def on_reset_command(self, button, option_id, entry, default_cmd):
        """Reset command to default value"""
        entry.set_text(default_cmd)

    def on_apply_settings(self, button):
        """Handle apply button click"""
        # Get current commands from entries
        commands = {}
        for option_id, entry in self.command_entries.items():
            commands[option_id] = entry.get_text()

        # Get current colors from color buttons
        colors = {}
        for option_id, color_button in self.color_buttons.items():
            hex_color = getattr(color_button, "preview_color")
            colors[option_id] = hex_color

        # Get current shortcuts from entries
        shortcuts = {}
        for option_id, entry in self.shortcut_entries.items():
            shortcuts[option_id] = entry.get_text()

        # Save settings
        self.active_buttons["commands"] = commands
        self.active_buttons["colors"] = colors
        self.active_buttons["shortcuts"] = shortcuts
        self.active_buttons["show_keybinds"] = self.show_keybinds

        # Update custom values
        self.custom_commands = commands
        self.custom_colors = colors
        self.custom_shortcuts = shortcuts
        self.show_keybinds = self.active_buttons["show_keybinds"]

        # Update power options with new shortcuts
        self._update_power_options_shortcuts()

        self._save_settings()

        # Rebuild the grid to show updated shortcut labels
        self._build_power_grid()
        self.settings_popover.popdown()

    def on_settings_clicked(self, button):
        """Handle settings button click"""
        self.settings_icon.get_style_context().add_class("rotate-gear-active")
        self.settings_icon.get_style_context().remove_class("rotate-gear")

        def on_popover_close(popover):
            self.settings_icon.get_style_context().remove_class("rotate-gear-active")
            self.settings_icon.get_style_context().add_class("rotate-gear")
            popover.disconnect(closed_handler)
        closed_handler = self.settings_popover.connect("closed", on_popover_close)

        self.settings_popover.popup()

    def _add_css(self):
        """Add CSS styling for power buttons"""
        css_provider = Gtk.CssProvider()
        css = """
        .power-button {
            border-radius: 12px;
            transition: all 200ms ease;
        }

        .power-button:hover {
            opacity: 0.9;
        }

        .power-button-label {
            color: white;
            font-weight: bold;
            font-size: 14px;
            text-shadow: 0px 1px 2px rgba(0, 0, 0, 0.5);
        }

        .power-button-icon {
            color: white;
            -gtk-icon-shadow: 0px 1px 2px rgba(0, 0, 0, 0.5);
        }
        """
        css_provider.load_from_data(css.encode())

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _create_power_button(self, label_text, icon_name, tooltip, callback, color, size=120):
        """Create a styled power button with icon and label"""
        button = Gtk.Button()
        button.set_tooltip_text(tooltip)
        button.connect("clicked", callback)
        button.set_size_request(size, size)

        # Apply CSS class
        button.get_style_context().add_class("power-button")

        # Add custom background color
        button_style = f".power-button {{ background-color: {color}; }}"
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(button_style.encode())
        button.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Set up button contents
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_valign(Gtk.Align.CENTER)

        # Create larger icon
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        icon.get_style_context().add_class("power-button-icon")
        content_box.pack_start(icon, False, False, 0)

        # Create label
        label = Gtk.Label(label=label_text)
        label.get_style_context().add_class("power-button-label")
        content_box.pack_start(label, False, False, 0)

        button.add(content_box)

        return button

    def _execute_command(self, command):
        """Execute a custom command"""
        try:
            # Handle special case for USER substitution
            if "$USER" in command:
                import os
                username = os.environ.get('USER', os.environ.get('USERNAME', ''))
                command = command.replace("$USER", username)

            self.logging.log(LogLevel.Info, f"Executing command: {command}")
            subprocess.Popen(command.split())
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed to execute command: {e}")

    def _close_application(self):
        """Close the application"""
        window = self.get_toplevel()
        if isinstance(window, Gtk.Window):
            self.logging.log(LogLevel.Info, "Closing application after power action")
            GLib.timeout_add(100, window.close)

    def on_lock_clicked(self, widget):
        """Handle lock button click"""
        command = self.custom_commands.get("lock", "loginctl lock-session")
        self.logging.log(LogLevel.Info, f"Lock button clicked, running: {command}")
        self._execute_command(command)
        # Close application after executing command
        self._close_application()

    def on_logout_clicked(self, widget):
        """Handle logout button click"""
        command = self.custom_commands.get("logout", "loginctl terminate-user $USER")
        self.logging.log(LogLevel.Info, f"Logout button clicked, running: {command}")
        self._execute_command(command)
        # Close application after executing command
        self._close_application()

    def on_suspend_clicked(self, widget):
        """Handle suspend button click"""
        command = self.custom_commands.get("suspend", "loginctl suspend")
        self.logging.log(LogLevel.Info, f"Suspend button clicked, running: {command}")
        self._execute_command(command)
        # Close application after executing command
        self._close_application()

    def on_hibernate_clicked(self, widget):
        """Handle hibernate button click"""
        command = self.custom_commands.get("hibernate", "loginctl hibernate")
        self.logging.log(LogLevel.Info, f"Hibernate button clicked, running: {command}")
        self._execute_command(command)
        # Close application after executing command
        self._close_application()

    def on_reboot_clicked(self, widget):
        """Handle reboot button click"""
        command = self.custom_commands.get("reboot", "loginctl reboot")
        self.logging.log(LogLevel.Info, f"Reboot button clicked, running: {command}")
        self._execute_command(command)
        # Close application after executing command
        self._close_application()

    def on_shutdown_clicked(self, widget):
        """Handle shutdown button click"""
        command = self.custom_commands.get("shutdown", "loginctl poweroff")
        self.logging.log(LogLevel.Info, f"Shutdown button clicked, running: {command}")
        self._execute_command(command)
        # Close application after executing command
        self._close_application()

    def _hex_to_rgba(self, hex_color):
        """Convert hex color to RGBA color"""
        rgba = Gdk.RGBA()

        # Handle both formats: #RRGGBB and RRGGBB
        if hex_color.startswith("#"):
            hex_color = hex_color[1:]

        # Parse the hex color
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            rgba.red = r
            rgba.green = g
            rgba.blue = b
            rgba.alpha = 1.0

        return rgba

    def _rgba_to_hex(self, rgba):
        """Convert RGBA color to hex color"""
        r = int(rgba.red * 255)
        g = int(rgba.green * 255)
        b = int(rgba.blue * 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def on_color_selected(self, color_button, option_id):
        """Handle color selection"""
        rgba = color_button.get_rgba()
        hex_color = self._rgba_to_hex(rgba)
        setattr(color_button, "preview_color", hex_color)

        # Update preview button style
        preview_button = getattr(color_button, "preview_button")
        style_provider = Gtk.CssProvider()
        css = f".preview-button {{ background-color: {hex_color}; color: white; font-weight: bold; border-radius: 6px; }}"
        style_provider.load_from_data(css.encode())

        # Remove old provider and add new one
        style_context = preview_button.get_style_context()
        for provider in style_context.list_providers():
            style_context.remove_provider(provider)

        style_context.add_provider(
            style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_update_color_entry(self, color_button, entry):
        """Update color entry when color button changes"""
        rgba = color_button.get_rgba()
        hex_color = self._rgba_to_hex(rgba)
        entry.set_text(hex_color)

    def on_reset_color(self, button, option_id, color_button, entry, default_color):
        """Reset color to default"""
        rgba = self._hex_to_rgba(default_color)
        color_button.set_rgba(rgba)
        entry.set_text(default_color)

        # Update preview button
        setattr(color_button, "preview_color", default_color)
        preview_button = getattr(color_button, "preview_button")
        style_provider = Gtk.CssProvider()
        css = f".preview-button {{ background-color: {default_color}; color: white; font-weight: bold; border-radius: 6px; }}"
        style_provider.load_from_data(css.encode())

        # Remove old provider and add new one
        style_context = preview_button.get_style_context()
        for provider in style_context.list_providers():
            style_context.remove_provider(provider)

        style_context.add_provider(
            style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_shortcut_key_press(self, entry, event, option_id):
        """Handle key press in shortcut entry"""
        keyval = event.keyval

        # Ignore modifier keys
        if keyval in (Gdk.KEY_Control_L, Gdk.KEY_Control_R,
                      Gdk.KEY_Shift_L, Gdk.KEY_Shift_R,
                      Gdk.KEY_Alt_L, Gdk.KEY_Alt_R):
            return True

        # Get the character
        keychar = chr(keyval).lower()

        # Update the entry
        entry.set_text(keychar)

        # Prevent further processing
        return True

    def on_reset_shortcut(self, button, option_id, entry, default_shortcut):
        """Reset shortcut to default"""
        entry.set_text(default_shortcut)

        # Update the active_buttons dictionary
        self.active_buttons[option_id] = True
