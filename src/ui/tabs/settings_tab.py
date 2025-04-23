#!/usr/bin/env python3

import gi

from utils.logger import LogLevel, Logger
from utils.translations import English, Spanish, Portuguese, French  # type: ignore

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject  # type: ignore

from utils.settings import load_settings, save_settings


class SettingsTab(Gtk.Box):
    """Tab for application settings"""
    __gsignals__ = {
        'tab-visibility-changed': (GObject.SignalFlags.RUN_LAST, None, (str, bool,)),
        'tab-order-changed': (GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,)),
        'vertical-tabs-changed': (GObject.SignalFlags.RUN_LAST, None, (bool,)),
    }

    def __init__(self, logging: Logger, txt: English | Spanish | Portuguese | French):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.txt = txt
        self.logging = logging

        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)
        self.set_hexpand(True)
        self.set_vexpand(True)

        # Load settings
        self.settings = load_settings(logging)

        # Header with Settings title and icon
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_margin_bottom(10)
        header_box.set_halign(Gtk.Align.START)
        header_box.set_hexpand(True)

        settings_icon = Gtk.Image.new_from_icon_name(
            "preferences-system-symbolic", Gtk.IconSize.DIALOG
        )
        ctx = settings_icon.get_style_context()
        ctx.add_class("settings-icon")

        def on_enter(widget, event):
            ctx.add_class("settings-icon-animate")

        def on_leave(widget, event):
            ctx.remove_class("settings-icon-animate")

        icon_event_box = Gtk.EventBox()
        icon_event_box.add(settings_icon)
        icon_event_box.connect("enter-notify-event", on_enter)
        icon_event_box.connect("leave-notify-event", on_leave)

        header_box.pack_start(icon_event_box, False, False, 0)

        settings_label = Gtk.Label(label=self.txt.settings_title)
        settings_label.set_markup(f"<span size='x-large' weight='bold'>{self.txt.settings_title}</span>")
        header_box.pack_start(settings_label, False, False, 0)

        self.pack_start(header_box, False, False, 0)

        # Wrap content in a scrolled window
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        self.pack_start(scrolled_window, True, True, 0)

        # Create notebook for tabs
        self.notebook = Gtk.Notebook()
        self.notebook.set_hexpand(True)
        self.notebook.set_vexpand(True)
        scrolled_window.add(self.notebook)

        # Create Tabs Reordering tab
        self.create_tabs_reordering_tab()

        # Create Language tab
        self.create_language_tab()

        self.show_all()

        self.logging.log(LogLevel.Info, "Settings UI with tabs has been created")

    def create_tabs_reordering_tab(self):
        tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tab_box.set_margin_top(10)
        tab_box.set_margin_bottom(10)
        tab_box.set_margin_start(10)
        tab_box.set_margin_end(10)
        tab_box.set_hexpand(True)
        tab_box.set_vexpand(True)

        # Frame for tab settings
        settings_frame = Gtk.Frame()
        settings_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        settings_frame.set_hexpand(True)
        settings_frame.set_vexpand(True)
        tab_box.pack_start(settings_frame, True, True, 0)

        self.tab_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.tab_section.set_margin_top(10)
        self.tab_section.set_margin_bottom(10)
        self.tab_section.set_margin_start(10)
        self.tab_section.set_margin_end(10)
        self.tab_section.set_hexpand(True)
        self.tab_section.set_vexpand(True)
        settings_frame.add(self.tab_section)

        section_label = Gtk.Label(label=self.txt.settings_tab_settings)
        section_label.set_markup(f"<span weight='bold'>{self.txt.settings_tab_settings}</span>")
        section_label.set_halign(Gtk.Align.START)
        self.tab_section.pack_start(section_label, False, False, 0)

        tabs = ["Volume", "Wi-Fi", "Bluetooth", "Battery", "Display", "Power", "Autostart", "USBGuard"]
        self.tab_switches = {}
        self.tab_rows = {}

        for tab_name in tabs:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            row.set_hexpand(True)
            row.set_margin_top(2)
            row.set_margin_bottom(2)

            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            button_box.set_valign(Gtk.Align.CENTER)

            up_button = Gtk.Button()
            up_button.set_image(Gtk.Image.new_from_icon_name("go-up-symbolic", Gtk.IconSize.BUTTON))
            up_button.set_relief(Gtk.ReliefStyle.NONE)
            up_button.connect("clicked", self.on_move_up_clicked, tab_name)
            button_box.pack_start(up_button, False, False, 0)

            down_button = Gtk.Button()
            down_button.set_image(Gtk.Image.new_from_icon_name("go-down-symbolic", Gtk.IconSize.BUTTON))
            down_button.set_relief(Gtk.ReliefStyle.NONE)
            down_button.connect("clicked", self.on_move_down_clicked, tab_name)
            button_box.pack_start(down_button, False, False, 0)

            up_button.set_size_request(24, 24)
            down_button.set_size_request(24, 24)

            row.pack_start(button_box, False, False, 0)

            label = Gtk.Label(label=f"{self.txt.show} {tab_name} tab")
            label.set_halign(Gtk.Align.START)
            row.pack_start(label, True, True, 0)

            switch = Gtk.Switch()
            visible = self.settings.get("visibility", {}).get(tab_name, True)
            switch.set_active(visible)
            switch.connect("notify::active", self.on_tab_visibility_changed, tab_name)
            switch.set_size_request(40, 20)
            switch.set_valign(Gtk.Align.CENTER)

            switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            switch_box.set_size_request(50, 24)
            switch_box.set_valign(Gtk.Align.CENTER)
            switch_box.pack_start(switch, True, False, 0)

            row.pack_end(switch_box, False, False, 0)

            self.tab_switches[tab_name] = switch
            self.tab_rows[tab_name] = row

        self.update_ui_order()

        # Add vertical tabs toggle
        vertical_tabs_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        vertical_tabs_row.set_hexpand(True)
        vertical_tabs_row.set_margin_top(10)
        vertical_tabs_row.set_margin_bottom(10)

        vertical_tabs_label = Gtk.Label(label=self.txt.settings_vertical_tabs_label if hasattr(self.txt, 'settings_vertical_tabs_label') else "Enable Vertical Tabs")
        vertical_tabs_label.set_halign(Gtk.Align.START)
        vertical_tabs_row.pack_start(vertical_tabs_label, True, True, 0)

        self.vertical_tabs_switch = Gtk.Switch()
        vertical_tabs_enabled = self.settings.get("vertical_tabs", False)
        self.vertical_tabs_switch.set_active(vertical_tabs_enabled)
        self.vertical_tabs_switch.set_size_request(40, 20)
        self.vertical_tabs_switch.set_valign(Gtk.Align.CENTER)
        self.vertical_tabs_switch.connect("notify::active", self.on_vertical_tabs_toggled)

        vertical_tabs_switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        vertical_tabs_switch_box.set_size_request(50, 24)
        vertical_tabs_switch_box.set_valign(Gtk.Align.CENTER)
        vertical_tabs_switch_box.pack_start(self.vertical_tabs_switch, True, False, 0)

        vertical_tabs_row.pack_end(vertical_tabs_switch_box, False, False, 0)

        self.tab_section.pack_start(vertical_tabs_row, False, False, 0)

        tab_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.MENU)
        tab_text = Gtk.Label(label="Tab Settings")
        tab_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        tab_label_box.pack_start(tab_icon, False, False, 0)
        tab_label_box.pack_start(tab_text, False, False, 0)
        tab_label_box.show_all()
        self.notebook.append_page(tab_box, tab_label_box)

    def create_language_tab(self):
        lang_box_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        lang_box_outer.set_margin_top(10)
        lang_box_outer.set_margin_bottom(10)
        lang_box_outer.set_margin_start(10)
        lang_box_outer.set_margin_end(10)
        lang_box_outer.set_hexpand(True)
        lang_box_outer.set_vexpand(True)

        lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        lang_box.set_margin_top(10)
        lang_box.set_margin_bottom(10)

        lang_label = Gtk.Label(label=self.txt.settings_language)
        lang_label.set_halign(Gtk.Align.START)

        lang_combo = Gtk.ComboBoxText()
        lang_combo.append("default", "Default (System)")
        lang_combo.append("en", "English")
        lang_combo.append("es", "Español")
        lang_combo.append("pt", "Português")
        lang_combo.append("fr", "Français")
        lang_combo.append("id", "Bahasa Indonesia")
        lang_combo.set_active_id(self.settings.get("language"))
        lang_combo.connect("changed", self.on_language_changed)

        lang_box.pack_start(lang_label, True, True, 0)
        lang_box.pack_end(lang_combo, False, False, 0)

        lang_box_outer.pack_start(lang_box, False, False, 0)

        lang_icon = Gtk.Image.new_from_icon_name("preferences-desktop-locale-symbolic", Gtk.IconSize.MENU)
        lang_text = Gtk.Label(label="Language")
        lang_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        lang_label_box.pack_start(lang_icon, False, False, 0)
        lang_label_box.pack_start(lang_text, False, False, 0)
        lang_label_box.show_all()
        self.notebook.append_page(lang_box_outer, lang_label_box)

    def update_ui_order(self):
        tab_order = self.settings.get("tab_order", ["Volume", "Wi-Fi", "Bluetooth", "Battery", "Display", "Power", "Autostart", "USBGuard"])
        all_tabs = ["Volume", "Wi-Fi", "Bluetooth", "Battery", "Display", "Power", "Autostart", "USBGuard"]
        for tab in all_tabs:
            if tab not in tab_order:
                if tab == "Autostart":
                    if "USBGuard" in tab_order:
                        autostart_index = tab_order.index("USBGuard")
                        tab_order.insert(autostart_index, tab)
                    else:
                        tab_order.append(tab)
                elif tab == "USBGuard":
                    tab_order.append(tab)
                else:
                    tab_order.append(tab)

        self.settings["tab_order"] = tab_order
        save_settings(self.settings, self.logging)

        for row in self.tab_section.get_children():
            if isinstance(row, Gtk.Box) and row != self.tab_section.get_children()[0]:
                self.tab_section.remove(row)

        for tab_name in tab_order:
            if tab_name in self.tab_rows:
                self.tab_rows[tab_name].set_hexpand(True)
                self.tab_rows[tab_name].set_margin_top(4)
                self.tab_rows[tab_name].set_margin_bottom(4)
                self.tab_section.pack_start(self.tab_rows[tab_name], False, False, 2)

    def on_tab_visibility_changed(self, switch, gparam, tab_name):
        active = switch.get_active()
        if "visibility" not in self.settings:
            self.settings["visibility"] = {}
        self.settings["visibility"][tab_name] = active
        save_settings(self.settings, self.logging)
        self.emit("tab-visibility-changed", tab_name, active)

    def on_vertical_tabs_toggled(self, switch, gparam):
        active = switch.get_active()
        self.settings["vertical_tabs"] = active
        save_settings(self.settings, self.logging)
        # Emit a custom signal if needed to notify main window
        self.emit("vertical-tabs-changed", active)

    def on_move_up_clicked(self, button, tab_name):
        tab_order = self.settings.get("tab_order", ["Volume", "Wi-Fi", "Bluetooth", "Battery", "Display", "Power", "Autostart", "USBGuard"])
        current_index = tab_order.index(tab_name)
        if current_index > 0:
            tab_order[current_index], tab_order[current_index - 1] = tab_order[current_index - 1], tab_order[current_index]
            self.settings["tab_order"] = tab_order
            save_settings(self.settings, self.logging)
            self.update_ui_order()
            self.emit("tab-order-changed", tab_order)

    def on_move_down_clicked(self, button, tab_name):
        tab_order = self.settings.get("tab_order", ["Volume", "Wi-Fi", "Bluetooth", "Battery", "Display", "Power", "Autostart", "USBGuard"])
        current_index = tab_order.index(tab_name)
        if current_index >= len(tab_order) - 1:
            return
        tab_order[current_index], tab_order[current_index + 1] = tab_order[current_index + 1], tab_order[current_index]
        self.settings["tab_order"] = tab_order
        save_settings(self.settings, self.logging)
        self.update_ui_order()
        self.emit("tab-order-changed", tab_order)

    def save_window_size(self, width: int, height: int):
        if "window_size" not in self.settings:
            self.settings["window_size"] = {}
        self.settings["window_size"]["settings_width"] = width
        self.settings["window_size"]["settings_height"] = height
        save_settings(self.settings, self.logging)
        self.logging.log(LogLevel.Info, f"Saved reference window size: {width}x{height}")

    def on_language_changed(self, combo):
        lang = combo.get_active_id()
        self.settings["language"] = lang
        self.logging.log(LogLevel.Info, f"Language changed to {lang}, saving settings")

        if "language" not in self.settings:
            self.logging.log(LogLevel.Warn, "Language key not in settings, adding it")

        save_settings(self.settings, self.logging)

        saved_settings = load_settings(self.logging)
        if saved_settings.get("language") == lang:
            self.logging.log(LogLevel.Info, f"Language setting verified: {saved_settings.get('language')}")
        else:
            self.logging.log(LogLevel.Error, f"Language setting not saved correctly. Expected: {lang}, Got: {saved_settings.get('language')}")
            self.logging.log(LogLevel.Info, "Forcing language setting in configuration file")
            saved_settings["language"] = lang
            save_settings(saved_settings, self.logging)

        parent_window = self.get_toplevel()
        if hasattr(parent_window, 'settings'):
            parent_window.settings["language"] = lang
            self.logging.log(LogLevel.Info, f"Updated main window's language setting to {lang}")

        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=self.txt.settings_language_changed
        )
        dialog.format_secondary_text(
            self.txt.settings_language_changed_restart
        )
        dialog.run()
        dialog.destroy()
