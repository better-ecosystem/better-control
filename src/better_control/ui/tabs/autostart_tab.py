#!/usr/bin/env python3

import threading
import gi

from better_control.utils.translations import Translation  # type: ignore
gi.require_version('Gtk', '3.0')
import glob
import os
from pathlib import Path
from gi.repository import Gtk, GLib, Gdk, Pango # type: ignore
from better_control.utils.logger import LogLevel, Logger
from better_control.tools.hyprland import get_hyprland_startup_apps, toggle_hyprland_startup
from better_control.tools.globals import get_current_session
from better_control.tools.swaywm import get_sway_startup_apps, toggle_sway_startup

class AutostartTab(Gtk.Box):
    """Autostart settings tab"""

    def __init__(self, logging: Logger, txt: Translation):
                super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                self.txt = txt
                self.logging = logging
                self.startup_apps = {}

                self.update_timeout_id = None
                self.update_interval = 100  # in ms
                self.is_visible = False

                # Set margins to match other tabs
                self.set_margin_start(15)
                self.set_margin_end(15)
                self.set_margin_top(15)
                self.set_margin_bottom(15)
                self.set_hexpand(True)
                self.set_vexpand(True)

                hypr_apps = get_hyprland_startup_apps()
                if not hypr_apps:
                    logging.log(LogLevel.Warn, "failed to get hyprland config")

                # Create header box with title
                header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                header_box.set_hexpand(True)
                header_box.set_margin_bottom(10)

                # Create title box with icon and label
                title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

                # Add display icon with hover animations
                display_icon = Gtk.Image.new_from_icon_name(
                    "system-run-symbolic", Gtk.IconSize.DIALOG
                )
                ctx = display_icon.get_style_context()
                ctx.add_class("autostart-icon")

                def on_enter(widget, event):
                    ctx.add_class("autostart-icon-animate")

                def on_leave(widget, event):
                    ctx.remove_class("autostart-icon-animate")

                # Wrap in event box for hover detection
                icon_event_box = Gtk.EventBox()
                icon_event_box.add(display_icon)
                icon_event_box.connect("enter-notify-event", on_enter)
                icon_event_box.connect("leave-notify-event", on_leave)

                title_box.pack_start(icon_event_box, False, False, 0)

                # Add title with better styling
                display_label = Gtk.Label()
                display_label.set_markup(
                    f"<span weight='bold' size='large'>{getattr(self.txt, 'autostart_title', 'Autostart')}</span>"
                )
                display_label.get_style_context().add_class("header-title")
                display_label.set_halign(Gtk.Align.START)
                title_box.pack_start(display_label, False, False, 0)

                header_box.pack_start(title_box, True, True, 0)

                # Add scan button with better styling
                self.refresh_button = Gtk.Button()
                self.refresh_button.set_valign(Gtk.Align.CENTER)
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
                refresh_tooltip = getattr(self.txt, "refresh_tooltip", "Refresh and Scan for Services")
                self.refresh_button.set_tooltip_text(refresh_tooltip)
                self.refresh_button.connect("clicked", self.refresh_list)
                
                # Hover behavior
                self.refresh_button.set_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
                self.refresh_button.connect("enter-notify-event", self.on_refresh_enter)
                self.refresh_button.connect("leave-notify-event", self.on_refresh_leave)

                # Add refresh button to header
                header_box.pack_end(self.refresh_button, False, False, 0)
                self.pack_start(header_box, False, False, 0)


                # Add session info with badge styling
                current_session = get_current_session()
                if current_session in ["Hyprland", "sway"]:
                    session_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                    session_box.set_margin_bottom(5)

                    session_label = Gtk.Label(label=f"{getattr(self.txt, 'autostart_session', 'Session')}: {current_session}")
                    session_label.get_style_context().add_class("session-label")
                    session_box.pack_start(session_label, False, False, 0)

                    self.pack_start(session_box, False, False, 0)

                # Add toggle switches box with better layout
                toggles_frame = Gtk.Frame()
                toggles_frame.set_shadow_type(Gtk.ShadowType.IN)
                toggles_frame.set_margin_top(5)
                toggles_frame.set_margin_bottom(15)

                toggles_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
                toggles_box.set_margin_start(10)
                toggles_box.set_margin_end(10)
                toggles_box.set_margin_top(10)
                toggles_box.set_margin_bottom(10)

                # System autostart apps toggle with better layout
                toggle1_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                toggle1_label = Gtk.Label(label=getattr(self.txt, 'autostart_show_system_apps', 'Show system apps'))
                toggle1_label.get_style_context().add_class("toggle-label")
                toggle1_label.set_halign(Gtk.Align.START)
                self.toggle1_switch = Gtk.Switch()
                self.toggle1_switch.set_active(False)
                self.toggle1_switch.connect("notify::active", self.on_toggle1_changed)
                toggle1_box.pack_start(toggle1_label, True, True, 0)
                toggle1_box.pack_end(self.toggle1_switch, False, False, 0)

                toggles_box.pack_start(toggle1_box, False, False, 0)
                toggles_frame.add(toggles_box)

                self.pack_start(toggles_frame, False, False, 0)

                # Add separator line with styling
                separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
                separator.get_style_context().add_class("separator")
                self.pack_start(separator, False, False, 0)

                # Section title for apps list
                apps_section_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                apps_section_box.set_margin_top(5)
                apps_section_box.set_margin_bottom(8)

                apps_icon = Gtk.Image.new_from_icon_name(
                    "application-x-executable-symbolic", Gtk.IconSize.MENU
                )
                apps_section_box.pack_start(apps_icon, False, False, 0)

                apps_title = Gtk.Label()
                apps_title.set_markup(f"<span weight='bold'>{getattr(self.txt, 'autostart_configured_applications', 'Configured Applications')}</span>")
                apps_title.set_halign(Gtk.Align.START)
                apps_section_box.pack_start(apps_title, False, False, 0)

                self.pack_start(apps_section_box, False, False, 0)

                # Add listbox for autostart apps with better styling
                scrolled_window = Gtk.ScrolledWindow()
                scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
                scrolled_window.set_vexpand(True)
                scrolled_window.set_margin_top(5)
                scrolled_window.set_shadow_type(Gtk.ShadowType.IN)

                self.listbox = Gtk.ListBox()
                self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                self.listbox.set_margin_start(5)
                self.listbox.set_margin_end(5)
                self.listbox.set_margin_top(5)
                self.listbox.set_margin_bottom(5)
                # Make listbox background transparent
                self.listbox.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 0))
                scrolled_window.add(self.listbox)
                self.pack_start(scrolled_window, True, True, 0)

                # Initial population
                self.refresh_list()
                
                self.connect('key-press-event', self.on_key_press)

                # Set up timer check for external changes
                GLib.timeout_add(4000, self.check_external_changes)

                self.connect("realize", self.on_realize)

    def on_realize(self, widget):
        GLib.idle_add(self.refresh_list)

    # keybinds for autostart tab
    def on_key_press(self, widget, event):
        keyval = event.keyval
        
        if keyval in (114, 82):
            self.logging.log(LogLevel.Info, "Refreshing list using keybind")
            self.refresh_list()
            return True
            
    def on_toggle1_changed(self, switch, gparam):
        """Handle toggle for system autostart apps"""
        show_system = switch.get_active()
        self.logging.log(LogLevel.Info, f"Show system autostart : {show_system}")
        self.refresh_list()

    def get_startup_apps(self):
            autostart_dirs = [
                Path.home() / ".config/autostart"
            ]

            # Add system directories
            if hasattr(self, 'toggle1_switch') and self.toggle1_switch.get_active():
                autostart_dirs.extend([
                    Path("/etc/xdg/autostart"),
                ])

            startup_apps = {}

            for autostart_dir in autostart_dirs:
                if autostart_dir.exists():
                    for desktop_file in glob.glob(str(autostart_dir / "*.desktop")):
                        if desktop_file.endswith(".desktop.disabled"):
                            continue

                        app_name = os.path.basename(desktop_file).replace(".desktop", "")

                        is_hidden = False
                        try:
                            with open(desktop_file, 'r') as f:
                                for line in f:
                                    if line.strip() == "Hidden=true":
                                        is_hidden = True
                                        break
                        except Exception as e:
                            self.logging.log(LogLevel.Warn, f"Could not read desktop file {desktop_file}: {e}")

                        if is_hidden and hasattr(self, 'toggle2_switch') and not self.toggle2_switch.get_active():
                            continue
                        startup_apps[app_name] = {
                            "type": "desktop",
                            "path": desktop_file,
                            "name": app_name,
                            "enabled": True,
                            "hidden": is_hidden
                            }

                    for desktop_file in glob.glob(str(autostart_dir / "*.desktop.disabled")):
                        app_name = os.path.basename(desktop_file).replace(".desktop.disabled", "")
                        startup_apps[app_name] = {
                            "type": "desktop",
                            "path": desktop_file,
                            "name": app_name,
                            "enabled": False,
                            "hidden": False
                            }

            # Add hyprland and sway apps according to session
            if get_current_session() == "Hyprland":
                hypr_apps = get_hyprland_startup_apps()
                startup_apps.update(hypr_apps)
            if get_current_session() == "sway":
                sway_apps = get_sway_startup_apps()
                startup_apps.update(sway_apps)

            self.logging.log(LogLevel.Debug, f"Found {len(startup_apps)} autostart apps")
            return startup_apps

    def refresh_list(self, widget=None):
        """Clear and repopulate the list of autostart apps
        Args:
            widget: Optional widget that triggered the refresh (from GTK signals)
        """
        # Run on a separate thread to avoid blocking the ui
        if hasattr(self, '_refresh_thread') and self._refresh_thread.is_alive():
            self.logging.log(LogLevel.Debug, "Refresh thread is already running")
        thread = threading.Thread(target=self.populate_list)
        thread.daemon = True
        thread.start()

    def populate_list(self):
        # Get apps first
        apps = self.get_startup_apps()
        self.startup_apps = apps

        # Clear list in main thread
        GLib.idle_add(self.clear_list)

        # Add each app in main thread
        for app_name, app in apps.items():
            GLib.idle_add(self.add_app_to_list, app_name, app)

    def clear_list(self):
        """Clear all items from the listbox"""
        children = self.listbox.get_children()
        for child in children:
            self.listbox.remove(child)

    def add_app_to_list(self, app_name, app):
        """Add a single app to the listbox"""
        self.logging.log(LogLevel.Debug, f"Adding app to list: {app_name}, enabled: {app['enabled']}")

        row = Gtk.ListBoxRow()
        row.get_style_context().add_class("app-row")

        # Create main container for the row
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox.set_margin_start(8)
        hbox.set_margin_end(8)
        hbox.set_margin_top(8)
        hbox.set_margin_bottom(8)
        row.add(hbox)

        # Status indicator icon container
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        # Try to get application icon if available
        app_icon = Gtk.Image.new_from_icon_name(
            app.get("name", app_name).lower(), Gtk.IconSize.LARGE_TOOLBAR
        )
        # Fallback to generic icon
        if not app_icon.get_pixbuf():
            app_icon = Gtk.Image.new_from_icon_name(
                "application-x-executable", Gtk.IconSize.LARGE_TOOLBAR
            )
        app_icon.get_style_context().add_class("app-icon")
        status_box.pack_start(app_icon, False, False, 0)

        if app.get("hidden", False):
            hidden_icon = Gtk.Image.new_from_icon_name(
                "view-hidden-symbolic", Gtk.IconSize.MENU
            )
            hidden_icon.set_tooltip_text("Hidden entry")
            hidden_icon.get_style_context().add_class("status-icon")
            status_box.pack_start(hidden_icon, False, False, 0)

        if not app.get("enabled", True):
            disabled_icon = Gtk.Image.new_from_icon_name(
                "window-close-symbolic", Gtk.IconSize.MENU
            )
            disabled_icon.set_tooltip_text("Disabled")
            disabled_icon.get_style_context().add_class("status-icon")
            status_box.pack_start(disabled_icon, False, False, 0)

        hbox.pack_start(status_box, False, False, 0)

        # App info container (name and path)
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)

        # App name
        label = Gtk.Label(label=app.get("name", app_name), xalign=0)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD)
        label.set_max_width_chars(40)
        label.get_style_context().add_class("app-label")
        info_box.pack_start(label, False, False, 0)

        # App path (if available)
        if "path" in app and app["path"]:
            path_label = Gtk.Label(label=str(app["path"]), xalign=0)
            path_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
            path_label.get_style_context().add_class(Gtk.STYLE_CLASS_DIM_LABEL)
            info_box.pack_start(path_label, False, False, 0)

        hbox.pack_start(info_box, True, True, 0)

        # Toggle button with better styling
        button_label = self.txt.disable if app["enabled"] else self.txt.enable
        button = Gtk.Button(label=button_label)
        button.get_style_context().add_class("toggle-button")
        button.get_style_context().add_class("enabled" if app["enabled"] else "disabled")
        button.connect("clicked", self.toggle_startup, app_name)
        hbox.pack_end(button, False, False, 0)

        row.app_name = app_name
        row.button = button
        self.listbox.add(row)
        row.show_all()

    def toggle_startup(self, button, app_name):
        app = self.startup_apps.get(app_name)

        if not app:
            self.logging.log(LogLevel.Warn, f"App not found : {app_name}")
            return

        self.logging.log(LogLevel.Info, f"Toggling app: {app_name}, current enabled: {app.get('enabled')}, type: {app.get('type')}")

        # for both .desktop and hyprland apps
        if app["type"] == "desktop" :
            new_path = app["path"] + ".disabled" if app["enabled"] else app["path"].replace(".disabled", "")
            try:
                os.rename(app["path"], new_path)
                app["path"] = new_path
                app["enabled"] = not app["enabled"]
                button.set_label("Disable" if app["enabled"] else "Enable")

                style_context = button.get_style_context()
                if app["enabled"]:
                    style_context.remove_class("destructive-action")
                    style_context.add_class("suggested-action")
                else:
                    style_context.remove_class("suggested-action")
                    style_context.add_class("destructive-action")

            except OSError as error:
                self.logging.log(LogLevel.Error, f"Failed to toggle startup app: {error}")

        elif app["type"] == "hyprland":
            # hyprland specific case
            toggle_hyprland_startup(app_name)

            app["enabled"] = not app["enabled"]
            button.set_label(self.txt.disable if app["enabled"] else self.txt.enable)

            style_context = button.get_style_context()
            if app["enabled"]:
                style_context.remove_class("destructive-action")
                style_context.add_class("suggested-action")
            else:
                style_context.remove_class("suggested-action")
                style_context.add_class("destructive-action")

            self.logging.log(LogLevel.Info, f"App toggled: {app_name}, enabled: {app['enabled']}")
        # for sway
        elif app["type"] == "sway":
            # sway specific case
            toggle_sway_startup(app_name)

            app["enabled"] = not app["enabled"]
            button.set_label(self.txt.disable if app["enabled"] else self.txt.enable)

            style_context = button.get_style_context()
            if app["enabled"]:
                style_context.remove_class("destructive-action")
                style_context.add_class("suggested-action")
            else:
                style_context.remove_class("suggested-action")
                style_context.add_class("destructive-action")

            self.logging.log(LogLevel.Info, f"App toggled: {app_name}, enabled: {app['enabled']}")
        self.refresh_list()


    def on_scan_clicked(self, widget):
        self.logging.log(LogLevel.Info, "Manually refreshing autostart apps...")
        self.refresh_list()

    def check_external_changes(self):
        """Check for external changes and update the UI"""
        current_apps = self.get_startup_apps()

        # check if there's any difference between current and stored apps
        if self.has_changes(current_apps, self.startup_apps):
            self.logging.log(LogLevel.Info, "Detected external changes in autostart apps, updating UI")
            self.refresh_list()

        return True

    def has_changes(self, new_apps, old_apps):
        """Check if there are differences between two app dictionaries"""
        if set(new_apps.keys()) != set(old_apps.keys()):
            return True

        for app_name, app_info in new_apps.items():
            if app_name not in old_apps:
                return True
            if app_info["enabled"] != old_apps[app_name]["enabled"]:
                return True
            if app_info["path"] != old_apps[app_name]["path"]:
                return True

        return False

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