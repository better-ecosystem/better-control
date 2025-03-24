#!/usr/bin/env python3

# Copyright (C) 2025 quantumvoid0 and FelipeFMA 
#
# This program is licensed under the terms of the GNU General Public License v3 + Attribution.
# See the full license text in the LICENSE file or at:
# https://github.com/quantumvoid0/better-control/blob/main/LICENSE
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.


import gi
import os
import psutil
import logging
import shutil
import time
import json
from pydbus import SystemBus
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib, Gdk
import subprocess
gi.require_version('Pango', '1.0')
from gi.repository import Gtk, Pango
import threading

import argparse

# Add this at the beginning of the file, before the bettercontrol class definition
def parse_arguments():
    parser = argparse.ArgumentParser(description="Better Control - A system control center.")
    parser.add_argument('--volume', action='store_true', help='Start with the Volume tab open.')
    parser.add_argument('--wifi', action='store_true', help='Start with the Wi-Fi tab open.')
    parser.add_argument('--bluetooth', action='store_true', help='Start with the Bluetooth tab open.')
    parser.add_argument('--battery', action='store_true', help='Start with the Battery tab open.')
    parser.add_argument('--display', action='store_true', help='Start with the Display tab open.')
    return parser.parse_args()

# Get configuration directory from XDG standard or fallback to ~/.config
CONFIG_DIR = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
CONFIG_PATH = os.path.join(CONFIG_DIR, 'better-control')
SETTINGS_FILE = os.path.join(CONFIG_PATH, 'settings.json')


def get_battery_devices():
    try:
        devices = subprocess.getoutput("upower -e").split("\n")
        return [d for d in devices if "battery" in d]
    except Exception as e:
        print(f"Error retrieving battery devices: {e}")
        return []

def get_battery_info(device):
    try:
        info = subprocess.getoutput(f"upower -i {device}")
        return info
    except Exception as e:
        print(f"Error retrieving battery info for {device}: {e}")
        return ""



def get_system_battery_info():
    battery = psutil.sensors_battery()
    if battery:
        return {
            "Charge": f"{battery.percent}%",
            "State": "Charging" if battery.power_plugged else "Discharging",
            "Time Left": "Unlimited" if battery.secsleft == psutil.POWER_TIME_UNLIMITED else f"{battery.secsleft // 3600}h {battery.secsleft % 3600 // 60}m"
        }
    return None

def detect_peripheral_battery():
    for device in get_battery_devices():
        info = get_battery_info(device)
        if "mouse" in info.lower():
            return device, "Wireless Mouse Battery"
        elif "keyboard" in info.lower():
            return device, "Wireless Keyboard Battery"
    return None, None

def get_battery_status():
    peripheral_battery, label = detect_peripheral_battery()
    if peripheral_battery:
        info = get_battery_info(peripheral_battery)
        percentage = next((line.split(":")[1].strip() for line in info.split("\n") if "percentage" in line.lower()), "Unknown")
        return {"Device": label, "Charge": percentage}

    system_battery = get_system_battery_info()
    if system_battery:
        system_battery["Device"] = "System Battery"
        return system_battery

    return {"Device": "No Battery Detected"}


# Example usage
battery_status = get_battery_status()




def check_dependency(command, name, install_instructions):
    if not shutil.which(command):
        logging.error(f"{name} is required but not installed!\n\nInstall it using:\n{install_instructions}")
        return f"{name} is required but not installed!\n\nInstall it using:\n{install_instructions}"
    return None

dependencies = [
    ("powerprofilesctl", "Power Profiles Control", "- Debian/Ubuntu: sudo apt install power-profiles-daemon\n- Arch Linux: sudo pacman -S power-profiles-daemon\n- Fedora: sudo dnf install power-profiles-daemon"),
    ("nmcli", "Network Manager CLI", "- Install NetworkManager package for your distro"),
    ("bluetoothctl", "Bluetooth Control", "- Debian/Ubuntu: sudo apt install bluez\n- Arch Linux: sudo pacman -S bluez bluez-utils\n- Fedora: sudo dnf install bluez"),
    ("pactl", "PulseAudio Control", "- Install PulseAudio or PipeWire depending on your distro"),
    ("brightnessctl", "Brightness Control", "- Debian/Ubuntu: sudo apt install brightnessctl\n- Arch Linux: sudo pacman -S brightnessctl\n- Fedora: sudo dnf install brightnessctl")
]

def check_all_dependencies(parent):
    missing = [check_dependency(cmd, name, inst) for cmd, name, inst in dependencies]
    missing = [msg for msg in missing if msg]
    if missing:
        show_error_dialog(parent, "\n\n".join(missing))
        return False  
    return True

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading settings: {e}")
    return {}

def save_settings(settings):
    try:
        # Ensure the config directory exists
        os.makedirs(CONFIG_PATH, exist_ok=True)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f)
    except Exception as e:
        logging.error(f"Error saving settings: {e}")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Better Control is running.")

class WiFiNetworkRow(Gtk.ListBoxRow):
    def __init__(self, network_info):
        super().__init__()
        self.set_margin_top(5)
        self.set_margin_bottom(5)
        self.set_margin_start(10)
        self.set_margin_end(10)
        
        # Parse network information
        parts = network_info.split()
        self.is_connected = '*' in parts[0]
        
        # More reliable SSID extraction
        if len(parts) > 1:
            # Find SSID - sometimes it's after the * mark in different positions
            # For connected networks, using a more reliable method to extract SSID
            if self.is_connected:
                # Try to get the proper SSID from nmcli connection show --active
                try:
                    active_connections = subprocess.getoutput("nmcli -t -f NAME,DEVICE connection show --active").split('\n')
                    for conn in active_connections:
                        if ':' in conn and 'wifi' in subprocess.getoutput(f"nmcli -t -f TYPE connection show '{conn.split(':')[0]}'"):
                            self.ssid = conn.split(':')[0]
                            break
                    else:
                        # Fallback to position-based extraction
                        self.ssid = parts[1]
                except Exception as e:
                    print(f"Error getting active connection name: {e}")
                    self.ssid = parts[1]
            else:
                # For non-connected networks, use the second column
                self.ssid = parts[1]
        else:
            self.ssid = "Unknown"
            
        # Determine security type more precisely
        if "WPA2" in network_info:
            self.security = "WPA2"
        elif "WPA3" in network_info:
            self.security = "WPA3"
        elif "WPA" in network_info:
            self.security = "WPA"
        elif "WEP" in network_info:
            self.security = "WEP"
        else:
            self.security = "Open"
        
        # Improved signal strength extraction
        # Signal is displayed in the "SIGNAL" column of nmcli output (index 6 with our new command)
        signal_value = 0
        try:
            # Now that we use a consistent format with -f, SIGNAL should be in column 7 (index 6)
            if len(parts) > 6 and parts[6].isdigit():
                signal_value = int(parts[6])
                self.signal_strength = f"{signal_value}%"
            else:
                # Fallback: scan through values for something that looks like signal strength
                for i, p in enumerate(parts):
                    # Look for a number between 0-100 that's likely the signal strength
                    if p.isdigit() and 0 <= int(p) <= 100:
                        # Skip if this is likely to be the channel number (typically at index 4)
                        if i != 4:  # Skip CHAN column
                            signal_value = int(p)
                            self.signal_strength = f"{signal_value}%"
                            break
                else:
                    # No valid signal found
                    self.signal_strength = "0%"
        except (IndexError, ValueError) as e:
            print(f"Error parsing signal strength from {parts}: {e}")
            self.signal_strength = "0%"
            signal_value = 0
        
        # Determine signal icon based on signal strength percentage
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
            
        # Determine security icon
        if self.security != "Open":
            security_icon = "network-wireless-encrypted-symbolic"
        else:
            security_icon = "network-wireless-symbolic"
        
        # Main container for the row
        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.add(container)
        
        # Network icon
        wifi_icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        container.pack_start(wifi_icon, False, False, 0)
        
        # Left side with SSID and security
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
        
        security_image = Gtk.Image.new_from_icon_name(security_icon, Gtk.IconSize.SMALL_TOOLBAR)
        details_box.pack_start(security_image, False, False, 0)
        
        security_label = Gtk.Label(label=self.security)
        security_label.set_halign(Gtk.Align.START)
        security_label.get_style_context().add_class("dim-label")
        details_box.pack_start(security_label, False, False, 0)
        
        left_box.pack_start(details_box, False, False, 0)
        
        container.pack_start(left_box, True, True, 0)
        
        # Right side with signal strength
        signal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        signal_box.set_halign(Gtk.Align.END)
        
        signal_label = Gtk.Label(label=self.signal_strength)
        signal_box.pack_start(signal_label, False, False, 0)
        
        container.pack_end(signal_box, False, False, 0)
        
        # Store original network info for connection handling
        self.original_network_info = network_info
        
    def get_ssid(self):
        return self.ssid
    
    def get_security(self):
        return self.security
    
    def get_original_network_info(self):
        return self.original_network_info
    
    def is_secured(self):
        return self.security != "Open"

class BatteryTab(Gtk.Box):
    def __init__(self, parent):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=10)
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
        
        # Add battery icon - increase size to match other tabs
        battery_icon = Gtk.Image.new_from_icon_name("battery-good-symbolic", Gtk.IconSize.DIALOG)
        title_box.pack_start(battery_icon, False, False, 0)
        
        # Add title
        self.battery_label = Gtk.Label()
        self.battery_label.set_markup("<span weight='bold' size='large'>Battery Metrics</span>")
        self.battery_label.set_halign(Gtk.Align.START)
        title_box.pack_start(self.battery_label, False, False, 0)
        
        header_box.pack_start(title_box, True, True, 0)
        
        # Add refresh button
        refresh_button = Gtk.Button()
        refresh_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        refresh_button.set_image(refresh_icon)
        refresh_button.set_tooltip_text("Refresh Battery Information")
        refresh_button.connect("clicked", self.refresh_battery_info)
        header_box.pack_end(refresh_button, False, False, 0)
        
        self.pack_start(header_box, False, False, 0)
        
        # Create scrollable content
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_window.set_vexpand(True)
        
        # Create main content box - store as instance variable to update later
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.content_box.set_margin_top(10)
        self.content_box.set_margin_bottom(10)
        self.content_box.set_margin_start(10)
        self.content_box.set_margin_end(10)
        
        # Power mode section (will be added at the bottom after battery info)
        self.power_mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        self.power_mode_label = Gtk.Label(label="Select Power Mode:")
        self.power_mode_label.set_halign(Gtk.Align.START)
        self.power_mode_label.set_markup("<b>Select Power Mode:</b>")
        self.power_mode_box.pack_start(self.power_mode_label, False, False, 0)
        
        # Mode selection dropdown
        dropdown_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        dropdown_box.set_margin_top(5)
        
        self.power_mode_dropdown = Gtk.ComboBoxText()
        self.power_modes = {
            "Power Saving": "power-saver",
            "Balanced": "balanced",
            "Performance": "performance"
        }

        for mode in self.power_modes.keys():
            self.power_mode_dropdown.append_text(mode)

        settings = load_settings()
        saved_mode = settings.get("power_mode", "balanced")

        matching_label = next((label for label, value in self.power_modes.items() if value == saved_mode), "Balanced")
        if matching_label:
            self.power_mode_dropdown.set_active(list(self.power_modes.keys()).index(matching_label))
        else:
            print(f"Warning: Unknown power mode '{saved_mode}', defaulting to Balanced")
            self.power_mode_dropdown.set_active(list(self.power_modes.keys()).index("Balanced"))

        dropdown_box.pack_start(self.power_mode_dropdown, True, True, 0)
        self.power_mode_box.pack_start(dropdown_box, False, False, 0)
        
        # We'll add batteries and power mode in refresh_battery_info()
        
        scroll_window.add(self.content_box)
        self.pack_start(scroll_window, True, True, 0)

        self.power_mode_dropdown.connect("changed", self.set_power_mode)
        
        # Initial refresh
        self.refresh_battery_info()
        GLib.timeout_add_seconds(10, self.refresh_battery_info)

    

    def set_power_mode_from_string(self, mode_string):
        """
        Set the power mode based on the string passed.
        :param mode_string: The power mode string (e.g., "powersave", "ondemand", "performance")
        """
        if mode_string in self.power_modes.values():
            for key, value in self.power_modes.items():
                if value == mode_string:
                    self.power_mode_dropdown.set_active(list(self.power_modes.keys()).index(key))
                    break
        else:
            self.power_mode_dropdown.set_active(list(self.power_modes.keys()).index("Balanced"))

    def show_password_dialog(self):
        """
        Show a password entry dialog and return the entered password.
        """
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Authentication Required",
        )
        dialog.format_secondary_text("Enter your password to change power mode:")

        entry = Gtk.Entry()
        entry.set_visibility(False)  
        entry.set_invisible_char("*")
        entry.set_activates_default(True)  

        box = dialog.get_content_area()
        box.pack_end(entry, False, False, 10)
        entry.show()

        dialog.set_default_response(Gtk.ResponseType.OK)
        response = dialog.run()
        password = entry.get_text() if response == Gtk.ResponseType.OK else None
        dialog.destroy()

        return password

    def set_power_mode(self, widget):
        """Handle power mode change using powerprofilesctl."""
        selected_mode = widget.get_active_text()
        if selected_mode in self.power_modes:
            mode_value = self.power_modes[selected_mode]

            try:
                command = f"powerprofilesctl set {mode_value}"
                result = subprocess.run(command, shell=True, capture_output=True, text=True)

                if result.returncode != 0:
                    error_message = "powerprofilesctl is missing. Please check our GitHub page to see all dependencies and install them."
                    logging.error(error_message)
                    self.parent.show_error_dialog(error_message)  
                else:
                    logging.info(f"Power mode changed to: {selected_mode} ({mode_value})")

                    settings = load_settings()
                    settings["power_mode"] = self.power_modes[selected_mode]  
                    save_settings(settings)

            except subprocess.CalledProcessError as e:
                self.parent.show_error_dialog(f"Failed to set power mode: {e}")

            except FileNotFoundError:
                self.parent.show_error_dialog("powerprofilesctl is not installed or not found in PATH.")

    def refresh_battery_info(self, button=None):
        """Refresh battery information. Can be triggered by button press."""
        # Clear content box
        for child in self.content_box.get_children():
            self.content_box.remove(child)
        
        # Create a grid to hold the batteries in a 2x2 layout
        batteries_grid = Gtk.Grid()
        batteries_grid.set_column_spacing(20)
        batteries_grid.set_row_spacing(20)
        batteries_grid.set_halign(Gtk.Align.CENTER)
        self.content_box.pack_start(batteries_grid, False, False, 0)
        
        # Counter for batteries found and position tracking
        batteries_found = 0
        
        # First check if we can get battery info from /sys/class/power_supply
        battery_paths = []
        for root, dirs, files in os.walk('/sys/class/power_supply/', topdown=False):
          for name in dirs:
              path = os.path.join(root, name)
              if os.path.exists(path):
                battery_paths.append(path)
        
        # Create battery sections
        for path in battery_paths:
            batteries_found += 1
            battery_id = os.path.basename(path)
            
            # Calculate grid position (2x2 layout)
            grid_x = (batteries_found - 1) % 2
            grid_y = (batteries_found - 1) // 2
            
            # Create a grid for this battery
            battery_grid = Gtk.Grid()
            battery_grid.set_column_spacing(15)
            battery_grid.set_row_spacing(10)
            battery_grid.set_margin_bottom(15)
            
            # Add battery title
            title = f"Battery {battery_id}"
            # Try to get model name for a better title
            if os.path.exists(f"{path}/model_name"):
                try:
                    with open(f"{path}/model_name", "r") as f:
                        model = f.read().strip()
                        if model:
                            title = f"{model} ({battery_id})"
                except:
                    pass
            
            title_label = Gtk.Label(xalign=0)
            title_label.set_markup(f"<span weight='bold'>{title}</span>")
            battery_grid.attach(title_label, 0, 0, 2, 1)
            
            row = 1
            battery_info = {}
            
            # Charge percentage
            try:
                if os.path.exists(f"{path}/capacity"):
                    with open(f"{path}/capacity", "r") as f:
                        capacity = f.read().strip()
                        battery_info["Charge"] = f"{capacity}%"
            except Exception as e:
                logging.error(f"Failed to read capacity: {e}")
                battery_info["Charge"] = "Error"
            
            # Battery status
            try:
                if os.path.exists(f"{path}/status"):
                    with open(f"{path}/status", "r") as f:
                        status = f.read().strip()
                        battery_info["State"] = status
            except Exception as e:
                logging.error(f"Failed to read status: {e}")
                battery_info["State"] = "Unknown"
            
            # Capacity health
            try:
                if os.path.exists(f"{path}/energy_full") and os.path.exists(f"{path}/energy_full_design"):
                    with open(f"{path}/energy_full", "r") as f:
                        energy_full = float(f.read().strip())
                    with open(f"{path}/energy_full_design", "r") as f:
                        energy_full_design = float(f.read().strip())
                    capacity_health = (energy_full / energy_full_design) * 100
                    battery_info["Capacity"] = f"{capacity_health:.1f}%"
            except Exception as e:
                logging.error(f"Failed to read capacity health: {e}")
                battery_info["Capacity"] = "Unknown"
                
            # Power consumption
            try:
                if os.path.exists(f"{path}/power_now"):
                    with open(f"{path}/power_now", "r") as f:
                        power_now = float(f.read().strip()) / 1000000  # Convert to W
                        battery_info["Power"] = f"{power_now:.2f} W"
            except Exception as e:
                logging.error(f"Failed to read power: {e}")
                battery_info["Power"] = "Unknown"
                
            # Voltage
            try:
                if os.path.exists(f"{path}/voltage_now"):
                    with open(f"{path}/voltage_now", "r") as f:
                        voltage_now = float(f.read().strip()) / 1000000  # Convert to V
                        battery_info["Voltage"] = f"{voltage_now:.2f} V"
            except Exception as e:
                logging.error(f"Failed to read voltage: {e}")
                battery_info["Voltage"] = "Unknown"
                
            # Cycle count
            try:
                if os.path.exists(f"{path}/cycle_count"):
                    with open(f"{path}/cycle_count", "r") as f:
                        cycle_count = f.read().strip()
                        battery_info["Cycles"] = cycle_count
            except Exception as e:
                logging.error(f"Failed to read cycle count: {e}")
                
            # Technology
            try:
                if os.path.exists(f"{path}/technology"):
                    with open(f"{path}/technology", "r") as f:
                        technology = f.read().strip()
                        battery_info["Technology"] = technology
            except Exception as e:
                logging.error(f"Failed to read technology: {e}")
                
            # Manufacturer
            try:
                if os.path.exists(f"{path}/manufacturer"):
                    with open(f"{path}/manufacturer", "r") as f:
                        manufacturer = f.read().strip()
                        battery_info["Manufacturer"] = manufacturer
            except Exception as e:
                logging.error(f"Failed to read manufacturer: {e}")
            
            # Serial number
            try:
                if os.path.exists(f"{path}/serial_number"):
                    with open(f"{path}/serial_number", "r") as f:
                        serial = f.read().strip()
                        battery_info["Serial"] = serial
            except Exception as e:
                logging.error(f"Failed to read serial number: {e}")
            
            # Time remaining (energy_now / power_now) if discharging
            try:
                if (os.path.exists(f"{path}/energy_now") and 
                    os.path.exists(f"{path}/power_now") and 
                    battery_info.get("State") == "Discharging"):
                    
                    with open(f"{path}/energy_now", "r") as f:
                        energy_now = float(f.read().strip())
                    with open(f"{path}/power_now", "r") as f:
                        power_now = float(f.read().strip())
                    
                    if power_now > 0:
                        # Time in hours
                        time_left = energy_now / power_now
                        hours = int(time_left)
                        minutes = int((time_left - hours) * 60)
                        battery_info["Time Left"] = f"{hours:02d}:{minutes:02d}"
            except Exception as e:
                logging.error(f"Failed to calculate time left: {e}")
            
            # Add all available information to grid
            for key, value in battery_info.items():
                key_label = Gtk.Label(xalign=0)
                key_label.set_markup(f"<b>{key}:</b>")
                battery_grid.attach(key_label, 0, row, 1, 1)
                
                value_label = Gtk.Label(xalign=0)
                value_label.set_text(value)
                battery_grid.attach(value_label, 1, row, 1, 1)
                row += 1
            
            # Add this battery grid to the main batteries grid in a 2x2 layout
            batteries_grid.attach(battery_grid, grid_x, grid_y, 1, 1)
        
        # If no battery files were found, try using psutil
        if not batteries_found:
            try:
                battery = psutil.sensors_battery()
                if battery:
                    batteries_found += 1
                    # Create a grid for system battery info
                    battery_grid = Gtk.Grid()
                    battery_grid.set_column_spacing(15)
                    battery_grid.set_row_spacing(10)
                    
                    title_label = Gtk.Label(xalign=0)
                    title_label.set_markup("<span weight='bold'>Battery</span>")
                    battery_grid.attach(title_label, 0, 0, 2, 1)
                    
                    # Charge percentage
                    percent = battery.percent
                    power_plugged = battery.power_plugged
                    state = "Charging" if power_plugged else "Discharging"
                    
                    # Format seconds remaining
                    secs_left = battery.secsleft
                    if secs_left == psutil.POWER_TIME_UNLIMITED:
                        time_left = "Unlimited"
                    elif secs_left == psutil.POWER_TIME_UNKNOWN:
                        time_left = "Unknown"
                    else:
                        hours, remainder = divmod(secs_left, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        time_left = f"{int(hours):02d}:{int(minutes):02d}"
                    
                    # Add information to grid
                    row = 1
                    infos = [
                        ("Charge", f"{percent:.1f}%"),
                        ("State", state),
                        ("Time Left", time_left)
                    ]
                    
                    for key, value in infos:
                        key_label = Gtk.Label(xalign=0)
                        key_label.set_markup(f"<b>{key}:</b>")
                        battery_grid.attach(key_label, 0, row, 1, 1)
                        
                        value_label = Gtk.Label(xalign=0)
                        value_label.set_text(value)
                        battery_grid.attach(value_label, 1, row, 1, 1)
                        row += 1
                    
                    # Add to batteries grid
                    batteries_grid.attach(battery_grid, 0, 0, 1, 1)
            except Exception as e:
                logging.error(f"Failed to get battery info via psutil: {e}")
        
        # If still no batteries found, show "No battery detected" message
        if not batteries_found:
            no_battery_label = Gtk.Label(xalign=0)
            no_battery_label.set_text("No battery detected")
            no_battery_label.set_margin_top(10)
            no_battery_label.set_margin_bottom(10)
            self.content_box.pack_start(no_battery_label, False, False, 0)
        
        # Add separator and power mode section
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.content_box.pack_start(separator, False, False, 10)
        
        # Add the power mode box at the bottom
        self.content_box.pack_start(self.power_mode_box, False, False, 0)
        
        # Show all updated widgets
        self.content_box.show_all()
        return True  # Keep the timer active

class bettercontrol(Gtk.Window):
    def __init__(self, args):
        Gtk.Window.__init__(self, title="Control Center")
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_default_size(900, 600)
        self.set_resizable(True)

        self._tabs_initialized = {}

        if "hyprland" in os.environ.get("XDG_CURRENT_DESKTOP", "").lower():
            subprocess.run(["hyprctl", "keyword", "windowrulev2", "float,class:^(control)$"])

        self.tabs = {}  
        self.tab_visibility = self.load_settings()
        
        # Override tab visibility based on command-line arguments
        if args.volume:
            self.tab_visibility["Volume"] = True
        if args.wifi:
            self.tab_visibility["Wi-Fi"] = True
        if args.bluetooth:
            self.tab_visibility["Bluetooth"] = True
        if args.battery:
            self.tab_visibility["Battery"] = True
        if args.display:
            self.tab_visibility["Display"] = True

        # Dictionary to store original tab positions
        self.original_tab_positions = self.original_tab_positions if hasattr(self, 'original_tab_positions') else {}
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(self.main_container)
    
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.main_container.pack_start(self.notebook, True, True, 0)
        self.notebook.connect("switch-page", self.on_tab_switch)
        
        # Create Settings button in the tab bar action area (right side)
        settings_button = Gtk.Button()
        settings_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.BUTTON)
        settings_button.set_image(settings_icon)
        settings_button.set_tooltip_text("Settings")
        settings_button.connect("clicked", self.toggle_settings_panel)
        self.notebook.set_action_widget(settings_button, Gtk.PackType.END)
        settings_button.show()

        # Create custom CSS for our UI
        css_provider = Gtk.CssProvider()
        css_data = """
            .success-label {
                color: #2ecc71;
                font-weight: bold;
            }
            .warning-label {
                color: #e67e22;
            }
            .error-label {
                color: #e74c3c;
            }
            .wifi-header {
                font-weight: bold;
                font-size: 16px;
            }
            .wifi-button {
                border-radius: 20px;
                padding: 8px 16px;
            }
            .info-notification {
                background-color: #3498db;
                color: white;
            }
        """
        css_provider.load_from_data(css_data.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Create the Wi-Fi tab
        wifi_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        wifi_box.set_margin_top(15)
        wifi_box.set_margin_bottom(15)
        wifi_box.set_margin_start(15)
        wifi_box.set_margin_end(15)
        wifi_box.set_hexpand(True)
        wifi_box.set_vexpand(True)
        
        # Header with Wi-Fi title and status
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_margin_bottom(10)
        
        wifi_icon = Gtk.Image.new_from_icon_name("network-wireless-symbolic", Gtk.IconSize.DIALOG)
        header_box.pack_start(wifi_icon, False, False, 0)
        
        wifi_label = Gtk.Label(label="Wi-Fi Networks")
        wifi_label.get_style_context().add_class("wifi-header")
        header_box.pack_start(wifi_label, False, False, 0)
        
        self.wifi_status_switch = Gtk.Switch()
        self.wifi_status_switch.set_active(True)
        self.wifi_status_switch.connect("notify::active", self.on_wifi_switch_toggled)
        self.wifi_status_switch.set_valign(Gtk.Align.CENTER)
        header_box.pack_end(self.wifi_status_switch, False, False, 0)
        
        wifi_status_label = Gtk.Label(label="Enable Wi-Fi")
        wifi_status_label.set_valign(Gtk.Align.CENTER)
        header_box.pack_end(wifi_status_label, False, False, 5)
        
        wifi_box.pack_start(header_box, False, False, 0)
        
        # Network speed indicators
        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        speed_box.set_margin_bottom(10)
        
        # Upload speed
        upload_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        upload_icon = Gtk.Image.new_from_icon_name("go-up-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        upload_box.pack_start(upload_icon, False, False, 0)
        
        self.upload_label = Gtk.Label(label="0 KB/s")
        upload_box.pack_start(self.upload_label, False, False, 0)
        
        speed_box.pack_start(upload_box, False, False, 0)
        
        # Download speed
        download_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        download_icon = Gtk.Image.new_from_icon_name("go-down-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        download_box.pack_start(download_icon, False, False, 0)
        
        self.download_label = Gtk.Label(label="0 KB/s")
        download_box.pack_start(self.download_label, False, False, 0)
        
        speed_box.pack_start(download_box, False, False, 0)
        
        # Add right-aligned refresh button
        refresh_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        refresh_button = Gtk.Button()
        refresh_button.set_tooltip_text("Refresh Networks")
        refresh_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        refresh_button.add(refresh_icon)
        refresh_button.connect("clicked", self.refresh_wifi)
        refresh_box.pack_end(refresh_button, False, False, 0)
        
        speed_box.pack_end(refresh_box, True, True, 0)
        
        wifi_box.pack_start(speed_box, False, False, 0)
        
        # Network list with scrolling
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_window.set_vexpand(True)
        
        self.wifi_listbox = Gtk.ListBox()
        self.wifi_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.wifi_listbox.set_activate_on_single_click(False)
        self.wifi_listbox.connect("row-activated", self.on_network_row_activated)
        
        scroll_window.add(self.wifi_listbox)
        wifi_box.pack_start(scroll_window, True, True, 0)
        
        # Action buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_box.set_margin_top(10)
        
        connect_button = Gtk.Button(label="Connect")
        connect_button.get_style_context().add_class("suggested-action")
        connect_button.connect("clicked", self.connect_wifi)
        action_box.pack_start(connect_button, True, True, 0)
        
        disconnect_button = Gtk.Button(label="Disconnect")
        disconnect_button.connect("clicked", self.disconnect_wifi)
        action_box.pack_start(disconnect_button, True, True, 0)
        
        forget_button = Gtk.Button(label="Forget Network")
        forget_button.connect("clicked", self.forget_wifi)
        action_box.pack_start(forget_button, True, True, 0)
        
        wifi_box.pack_start(action_box, False, False, 0)
        
        GLib.timeout_add_seconds(1, self.update_network_speed)
        
        scrolled_wifi = Gtk.ScrolledWindow()
        scrolled_wifi.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.tabs["Wi-Fi"] = wifi_box
        if self.tab_visibility.get("Wi-Fi", True):
            self.notebook.append_page(wifi_box, self.create_tab_label_with_icon("Wi-Fi"))
            # Don't scan WiFi on startup - will be scanned when tab is selected
            self._tabs_initialized = {}  # Initialize dictionary before using it
            self._tabs_initialized["Wi-Fi"] = False
            
            # Add signal for tab change to refresh WiFi when tab is selected
            self.notebook.connect("switch-page", self.on_tab_switched)
        
        # Replace the old bluetooth_box implementation
        bluetooth_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        bluetooth_box.set_margin_top(15)
        bluetooth_box.set_margin_bottom(15)
        bluetooth_box.set_margin_start(15)
        bluetooth_box.set_margin_end(15)
        bluetooth_box.set_hexpand(True)
        bluetooth_box.set_vexpand(True)
        
        # Header with Bluetooth title and status
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_margin_bottom(10)
        
        bt_icon = Gtk.Image.new_from_icon_name("bluetooth-symbolic", Gtk.IconSize.DIALOG)
        header_box.pack_start(bt_icon, False, False, 0)
        
        bt_label = Gtk.Label(label="Bluetooth Devices")
        bt_label.get_style_context().add_class("wifi-header")
        header_box.pack_start(bt_label, False, False, 0)
        
        # Add an initialization flag for Bluetooth
        self._bt_initialized = False
        self._tabs_initialized["Bluetooth"] = False
        
        # Set up the Bluetooth switch
        self.bt_status_switch = Gtk.Switch()
        self.bt_status_switch.set_valign(Gtk.Align.CENTER)
        
        # Don't check Bluetooth status at startup - will be checked when tab is selected
        self.bt_status_switch.set_active(False)
        
        # Connect the signal handler
        self.bt_status_switch.connect("notify::active", self.on_bluetooth_switch_toggled)
        
        header_box.pack_end(self.bt_status_switch, False, False, 0)
        
        bt_status_label = Gtk.Label(label="Enable Bluetooth")
        bt_status_label.set_valign(Gtk.Align.CENTER)
        header_box.pack_end(bt_status_label, False, False, 5)
        
        bluetooth_box.pack_start(header_box, False, False, 0)
        
        # Status and refresh area
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_box.set_margin_bottom(10)
        
        self.bt_status_label = Gtk.Label(label="Bluetooth is ready")
        status_box.pack_start(self.bt_status_label, False, False, 0)
        
        # Add right-aligned refresh button
        refresh_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        refresh_button = Gtk.Button()
        refresh_button.set_tooltip_text("Scan for Devices")
        refresh_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        refresh_button.add(refresh_icon)
        refresh_button.connect("clicked", self.refresh_bluetooth)
        refresh_box.pack_end(refresh_button, False, False, 0)
        
        status_box.pack_end(refresh_box, True, True, 0)
        
        bluetooth_box.pack_start(status_box, False, False, 0)
        
        # Device list with scrolling
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_window.set_vexpand(True)
        
        self.bt_listbox = Gtk.ListBox()
        self.bt_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.bt_listbox.set_activate_on_single_click(False)
        self.bt_listbox.connect("row-activated", self.on_device_row_activated)
        
        scroll_window.add(self.bt_listbox)
        bluetooth_box.pack_start(scroll_window, True, True, 0)
        
        # Action buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_box.set_margin_top(10)
        
        connect_button = Gtk.Button(label="Connect")
        connect_button.get_style_context().add_class("suggested-action")
        connect_button.connect("clicked", self.connect_bluetooth_device_selected)
        action_box.pack_start(connect_button, True, True, 0)
        
        disconnect_button = Gtk.Button(label="Disconnect")
        disconnect_button.connect("clicked", self.disconnect_bluetooth_device_selected)
        action_box.pack_start(disconnect_button, True, True, 0)
        
        forget_button = Gtk.Button(label="Forget Device")
        forget_button.connect("clicked", self.forget_bluetooth_device_selected)
        action_box.pack_start(forget_button, True, True, 0)
        
        bluetooth_box.pack_start(action_box, False, False, 0)
        
        # Replace the old scrolled_bt with our new implementation
        scrolled_bt = Gtk.ScrolledWindow()
        scrolled_bt.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_bt.add(bluetooth_box)

        self.tabs["Bluetooth"] = scrolled_bt
        if self.tab_visibility.get("Bluetooth", True):
            self.notebook.append_page(scrolled_bt, self.create_tab_label_with_icon("Bluetooth"))

        # Updated Volume tab with new UI matching Bluetooth and WiFi tabs
        volume_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        volume_box.set_margin_top(15)
        volume_box.set_margin_bottom(15)
        volume_box.set_margin_start(15)
        volume_box.set_margin_end(15)
        volume_box.set_hexpand(True)
        volume_box.set_vexpand(True)
        
        # Header with Volume title and status
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_margin_bottom(10)
        
        volume_icon = Gtk.Image.new_from_icon_name("audio-volume-high-symbolic", Gtk.IconSize.DIALOG)
        header_box.pack_start(volume_icon, False, False, 0)
        
        volume_title = Gtk.Label(label="Volume Control")
        volume_title.get_style_context().add_class("wifi-header")
        header_box.pack_start(volume_title, False, False, 0)
        
        volume_box.pack_start(header_box, False, False, 0)
        
        # Status area with output device selection
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_box.set_margin_bottom(10)
        
        output_label = Gtk.Label(label="Output Device:")
        output_label.set_size_request(120, -1)  # Set fixed width for the label
        status_box.pack_start(output_label, False, False, 0)
        
        # Replace ComboBoxText with ComboBox for icons
        self.sink_store = Gtk.ListStore(str, str, str)  # Device ID, Display Name, Icon Name
        self.sink_dropdown = Gtk.ComboBox.new_with_model(self.sink_store)
        
        # Add icon renderer
        icon_renderer = Gtk.CellRendererPixbuf()
        self.sink_dropdown.pack_start(icon_renderer, False)
        self.sink_dropdown.add_attribute(icon_renderer, "icon_name", 2)
        
        # Add text renderer
        text_renderer = Gtk.CellRendererText()
        self.sink_dropdown.pack_start(text_renderer, True)
        self.sink_dropdown.add_attribute(text_renderer, "text", 1)
        
        self.sink_dropdown.connect("changed", self.on_sink_selected)
        self.sink_dropdown.set_size_request(200, 30)
        status_box.pack_start(self.sink_dropdown, True, True, 0)
        
        # Refresh button
        refresh_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        refresh_button = Gtk.Button()
        refresh_button.set_tooltip_text("Refresh Audio Devices")
        refresh_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        refresh_button.add(refresh_icon)
        refresh_button.connect("clicked", self.update_sink_list)
        refresh_box.pack_end(refresh_button, False, False, 0)
        
        status_box.pack_end(refresh_box, False, False, 0)
        
        volume_box.pack_start(status_box, False, False, 0)
        
        # Add input device selection
        input_status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        input_status_box.set_margin_bottom(10)
        
        input_label = Gtk.Label(label="Input Device:")
        input_label.set_size_request(120, -1)  # Set fixed width for the label
        input_status_box.pack_start(input_label, False, False, 0)
        
        # Replace ComboBoxText with ComboBox for icons
        self.source_store = Gtk.ListStore(str, str, str)  # Device ID, Display Name, Icon Name
        self.source_dropdown = Gtk.ComboBox.new_with_model(self.source_store)
        
        # Add icon renderer
        source_icon_renderer = Gtk.CellRendererPixbuf()
        self.source_dropdown.pack_start(source_icon_renderer, False)
        self.source_dropdown.add_attribute(source_icon_renderer, "icon_name", 2)
        
        # Add text renderer
        source_text_renderer = Gtk.CellRendererText()
        self.source_dropdown.pack_start(source_text_renderer, True)
        self.source_dropdown.add_attribute(source_text_renderer, "text", 1)
        
        self.source_dropdown.connect("changed", self.on_source_selected)
        self.source_dropdown.set_size_request(200, 30)
        input_status_box.pack_start(self.source_dropdown, True, True, 0)
        
        # Input refresh button
        input_refresh_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        input_refresh_button = Gtk.Button()
        input_refresh_button.set_tooltip_text("Refresh Input Devices")
        input_refresh_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        input_refresh_button.add(input_refresh_icon)
        input_refresh_button.connect("clicked", self.update_source_list)
        input_refresh_box.pack_end(input_refresh_button, False, False, 0)
        
        input_status_box.pack_end(input_refresh_box, False, False, 0)
        
        volume_box.pack_start(input_status_box, False, False, 0)
        
        # Initialize the sink list
        self.update_sink_list()
        self.update_source_list()
        GLib.timeout_add_seconds(3, self.update_sink_list_repeated)
        
        # Volume controls in scrollable area
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_window.set_vexpand(True)
        
        controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        controls_box.set_margin_top(10)
        
        # Speaker volume section
        speaker_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        speaker_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        volume_label = Gtk.Label(label="Speaker Volume")
        volume_label.set_xalign(0)
        speaker_header.pack_start(volume_label, True, True, 0)
        
        self.volume_button = Gtk.Button(label="Mute/Unmute")
        self.volume_button.connect("clicked", self.mute)
        speaker_header.pack_end(self.volume_button, False, False, 0)
        
        speaker_section.pack_start(speaker_header, False, False, 0)
        
        # Volume slider
        self.volume_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.volume_scale.set_hexpand(True)
        self.volume_scale.set_value(self.get_current_volume())
        self.volume_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.volume_scale.connect("value-changed", self.set_volume)
        speaker_section.pack_start(self.volume_scale, False, False, 0)
        
        # Quick volume buttons
        volume_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.volume_zero = Gtk.Button(label="0%")
        self.volume_zero.connect("clicked", self.vzero)
        volume_buttons.pack_start(self.volume_zero, True, True, 0)
        
        self.volume_tfive = Gtk.Button(label="25%")
        self.volume_tfive.connect("clicked", self.vtfive)
        volume_buttons.pack_start(self.volume_tfive, True, True, 0)
        
        self.volume_fifty = Gtk.Button(label="50%")
        self.volume_fifty.connect("clicked", self.vfifty)
        volume_buttons.pack_start(self.volume_fifty, True, True, 0)
        
        self.volume_sfive = Gtk.Button(label="75%")
        self.volume_sfive.connect("clicked", self.vsfive)
        volume_buttons.pack_start(self.volume_sfive, True, True, 0)
        
        self.volume_hund = Gtk.Button(label="100%")
        self.volume_hund.connect("clicked", self.vhund)
        volume_buttons.pack_start(self.volume_hund, True, True, 0)
        
        speaker_section.pack_start(volume_buttons, False, False, 0)
        controls_box.pack_start(speaker_section, False, False, 0)
        
        # Mic volume section
        mic_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        mic_section.set_margin_top(15)
        
        mic_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        mic_label = Gtk.Label(label="Microphone Volume")
        mic_label.set_xalign(0)
        mic_header.pack_start(mic_label, True, True, 0)
        
        self.volume_mic = Gtk.Button(label="Mute/Unmute Mic")
        self.volume_mic.connect("clicked", self.micmute)
        mic_header.pack_end(self.volume_mic, False, False, 0)
        
        mic_section.pack_start(mic_header, False, False, 0)
        
        # Mic slider
        self.mic_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.mic_scale.set_hexpand(True)
        self.mic_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.mic_scale.set_value(self.get_current_mic_volume())
        self.mic_scale.connect("value-changed", self.set_mic_volume)
        mic_section.pack_start(self.mic_scale, False, False, 0)
        
        # Quick mic buttons
        mic_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.mic_zero = Gtk.Button(label="0%")
        self.mic_zero.connect("clicked", self.mzero)
        mic_buttons.pack_start(self.mic_zero, True, True, 0)
        
        self.mic_tfive = Gtk.Button(label="25%")
        self.mic_tfive.connect("clicked", self.mtfive)
        mic_buttons.pack_start(self.mic_tfive, True, True, 0)
        
        self.mic_fifty = Gtk.Button(label="50%")
        self.mic_fifty.connect("clicked", self.mfifty)
        mic_buttons.pack_start(self.mic_fifty, True, True, 0)
        
        self.mic_sfive = Gtk.Button(label="75%")
        self.mic_sfive.connect("clicked", self.msfive)
        mic_buttons.pack_start(self.mic_sfive, True, True, 0)
        
        self.mic_hund = Gtk.Button(label="100%")
        self.mic_hund.connect("clicked", self.mhund)
        mic_buttons.pack_start(self.mic_hund, True, True, 0)
        
        mic_section.pack_start(mic_buttons, False, False, 0)
        controls_box.pack_start(mic_section, False, False, 0)
        
        # Application volume section
        app_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        app_section.set_margin_top(15)
        
        app_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        app_label = Gtk.Label(label="Application Volume")
        app_label.set_xalign(0)
        app_header.pack_start(app_label, True, True, 0)
        
        refresh_app_volume_button = Gtk.Button(label="Refresh Applications")
        refresh_app_volume_button.get_style_context().add_class("suggested-action")
        refresh_app_volume_button.connect("clicked", self.refresh_app_volume)
        app_header.pack_end(refresh_app_volume_button, False, False, 0)
        
        app_section.pack_start(app_header, False, False, 0)
        
        # Application volume list
        self.app_volume_listbox = Gtk.ListBox()
        self.app_volume_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        app_section.pack_start(self.app_volume_listbox, True, True, 0)
        
        controls_box.pack_start(app_section, False, False, 0)
        
        # Initialize app volume list and set up auto-refresh
        GLib.timeout_add_seconds(1, self.refresh_app_volume_realtime)
        
        scroll_window.add(controls_box)
        volume_box.pack_start(scroll_window, True, True, 0)
        
        scrolled_volume = Gtk.ScrolledWindow()
        scrolled_volume.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_volume.add(volume_box)

        self.tabs["Volume"] = scrolled_volume
        if self.tab_visibility.get("Volume", True):
            self.notebook.append_page(scrolled_volume, self.create_tab_label_with_icon("Volume"))

        # Create a placeholder for the Display tab to be initialized later
        display_placeholder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.tabs["Display"] = display_placeholder
        if self.tab_visibility.get("Display", True):
            self.notebook.append_page(display_placeholder, self.create_tab_label_with_icon("Display"))

        self.battery_tab = BatteryTab(self)
        self.tabs["Battery"] = self.battery_tab
        if self.tab_visibility.get("Battery", True):  
            self.notebook.append_page(self.battery_tab, self.create_tab_label_with_icon("Battery"))


        # Create the settings box but don't add it to the notebook
        settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        settings_box.set_margin_top(10)
        settings_box.set_margin_bottom(10)
        settings_box.set_margin_start(10)
        settings_box.set_margin_end(10)
        settings_box.set_hexpand(True)
        settings_box.set_vexpand(True)

        self.tabs["Settings"] = settings_box  
        
        # Initialize the settings box content
        self.populate_settings_tab()

        # Apply the saved tab order if available
        self.apply_saved_tab_order()

        # Set the initial tab based on the command-line arguments
        if args.volume:
            initial_tab = "Volume"
        elif args.wifi:
            initial_tab = "Wi-Fi"
        elif args.bluetooth:
            initial_tab = "Bluetooth"
        elif args.battery:
            initial_tab = "Battery"
        elif args.display:
            initial_tab = "Display"
        else:
             initial_tab = next(iter(self.tabs))  # Default to Volume if no argument is provided

        # Find the index of the initial tab
        for index, (tab_name, tab) in enumerate(self.tabs.items()):
            if tab_name == initial_tab:
                GLib.idle_add(self.notebook.set_current_page, index)
                break


        self.update_button_labels()
        
        # The original_tab_positions dictionary is already initialized earlier

    def apply_css(self, widget):
        css = """
        label {
            font-size: 18px; 
        }
        """

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode())

        context = widget.get_style_context()
        context.add_provider(
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # Helper methods to reduce code duplication
    def set_blue_light(self, value):
        """Set blue light filter to a specific value"""
        if shutil.which("gammastep"):
            self.blue_light_slider.set_value(value)
        else:
            self.show_error_dialog("gammastep is missing. please check our github page to see all dependencies and install them")
    
    def set_mic_level(self, value):
        """Set microphone volume to a specific level"""
        if shutil.which("pactl"):
            subprocess.run(["pactl", "set-source-volume", "@DEFAULT_SOURCE@", f"{value}%"])
            self.mic_scale.set_value(value)
        else:
            self.show_error_dialog("pactl is missing. Please check our GitHub page to see all dependencies and install them.")
    
    def set_volume_level(self, value):
        """Set speaker volume to a specific level"""
        if shutil.which("pactl"):
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{value}%"])
            self.volume_scale.set_value(value)
        else:
            self.show_error_dialog("pactl is missing. please check our github page to see all dependencies and install them")
    
    def set_brightness_level(self, value):
        """Set brightness to a specific level"""
        if shutil.which("brightnessctl"):
            max_brightness = int(subprocess.getoutput("brightnessctl max"))
            # Convert percentage to actual brightness value
            actual_value = int((value / 100) * max_brightness)
            subprocess.run(['brightnessctl', 's', f'{actual_value}'])
            self.brightness_scale.set_value(value)
        else:
            self.show_error_dialog("brightnessctl is missing. please check our github page to see all dependencies and install them")
    
    # Blue light filter button handlers
    def bzero(self, button):
        self.set_blue_light(2500)
        
    def btfive(self, button):
        self.set_blue_light(3500)
        
    def bfifty(self, button):
        self.set_blue_light(4500)
        
    def bsfive(self, button):
        self.set_blue_light(5500)
        
    def bhund(self, button):
        self.set_blue_light(6500)

    def set_bluelight_filter(self, scale):
        self.temperature = int(scale.get_value())

        settings = load_settings()
        settings["gamma"] = self.temperature
        save_settings(settings)

        subprocess.run(["pkill", "-f", "gammastep"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["gammastep", "-O", str(self.temperature)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def update_network_speed(self):
        """Measure and update the network speed."""
        try:
            net_io = psutil.net_io_counters()
            bytes_sent = net_io.bytes_sent
            bytes_recv = net_io.bytes_recv

            if not hasattr(self, 'prev_bytes_sent'):
                self.prev_bytes_sent = bytes_sent
                self.prev_bytes_recv = bytes_recv
                return True

            upload_speed_kb = (bytes_sent - self.prev_bytes_sent) / 1024  
            download_speed_kb = (bytes_recv - self.prev_bytes_recv) / 1024  

            upload_speed_mbps = (upload_speed_kb * 8) / 1024  
            download_speed_mbps = (download_speed_kb * 8) / 1024  

            self.prev_bytes_sent = bytes_sent
            self.prev_bytes_recv = bytes_recv

            self.download_label.set_text(f"Download: {download_speed_mbps:.2f} Mbps")
            self.upload_label.set_text(f"Upload: {upload_speed_mbps:.2f} Mbps | ")

        except Exception as e:
            print(f"Error updating network speed: {e}")

        return True  # Continue the timer

    def show_error_dialog(self, message):
        """Display an error dialog instead of crashing."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error: Missing Dependency"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def switch_audio_sink(self, button):
        """Cycle through available audio sinks."""
        try:
            # First, update the sink list to ensure we have the latest data
            # and friendly name mappings
            self.update_sink_list()
            
            output = subprocess.getoutput("pactl list short sinks")
            sinks = output.split("\n")
            if not sinks:
                print("No available sinks found.")
                return

            current_sink = subprocess.getoutput("pactl get-default-sink").strip()
            sink_list = [sink.split("\t")[1] for sink in sinks if sink]

            if current_sink in sink_list:
                next_index = (sink_list.index(current_sink) + 1) % len(sink_list)
                next_sink = sink_list[next_index]
            else:
                next_sink = sink_list[0]

            subprocess.run(["pactl", "set-default-sink", next_sink])
            
            # Get the friendly name for display
            friendly_name = self.friendly_sink_names.get(next_sink, next_sink)
            
            if friendly_name == next_sink:
                # If we still don't have a friendly name, try to create one
                if next_sink.startswith("alsa_output."):
                    friendly_name = next_sink.replace("alsa_output.", "").replace("_", " ").replace(".", " ").title()
                elif next_sink.startswith("bluez_sink."):
                    friendly_name = next_sink.replace("bluez_sink.", "").replace("_", " ").replace(".", " ").title()
            
            print(f"Switched to sink: {friendly_name} ({next_sink})")
            
            # Also update the dropdown to show the current selection
            if hasattr(self, 'sink_dropdown'):
                self.update_sink_list()

        except Exception as e:
            print(f"Error switching sinks: {e}")

    def update_sink_list_repeated(self):
        """Update the dropdown list with available sinks and keep refreshing."""
        self.update_sink_list()
        self.update_source_list()
        return True  

    def update_sink_list(self, button=None):
        """Update the dropdown list with available sinks."""
        try:
            # Get detailed sink information
            detailed_output = subprocess.getoutput("pactl list sinks")
            sink_sections = detailed_output.split("Sink #")
            
            # Get the short list for sink IDs
            output = subprocess.getoutput("pactl list short sinks")
            sinks = output.split("\n")
            self.sink_list = [sink.split("\t")[1] for sink in sinks if sink]
            
            # First pass: Extract sink IDs and their indices
            sink_indices = {}
            for idx, section in enumerate(sink_sections[1:], 0):
                lines = section.split("\n")
                if lines and lines[0].strip():
                    sink_id = lines[0].strip().split(':')[0].strip()
                    sink_indices[sink_id] = idx
            
            # Create a mapping of sink IDs to friendly names
            friendly_names = {}
            
            # Direct method: Use pactl list short sinks for proper matching
            short_sinks_output = subprocess.getoutput("pactl list short sinks")
            short_sinks = short_sinks_output.split("\n")
            
            for sink_line in short_sinks:
                if not sink_line.strip():
                    continue
                    
                parts = sink_line.split("\t")
                if len(parts) >= 2:
                    sink_id = parts[0].strip()
                    sink_name = parts[1].strip()
                    
                    # Get the corresponding section from the detailed output
                    if sink_id in sink_indices:
                        section_idx = sink_indices[sink_id]
                        section = sink_sections[section_idx + 1]  # +1 because we skipped the first empty section
                        lines = section.split("\n")
                        
                        # Look for the description
                        description = None
                        
                        # Try multiple potential description fields
                        for line in lines:
                            line = line.strip()
                            
                            # Primary pattern: Description field
                            if line.startswith("Description:"):
                                description = line.split("Description:")[1].strip()
                                break
                                
                            # Properties patterns
                            elif "device.description" in line and "=" in line:
                                description = line.split("=")[1].strip().strip('"')
                                break
                            elif "alsa.card_name" in line and "=" in line:
                                description = line.split("=")[1].strip().strip('"')
                                break
                            elif "device.product.name" in line and "=" in line:
                                description = line.split("=")[1].strip().strip('"')
                                break
                            elif "bluez.alias" in line and "=" in line:
                                description = line.split("=")[1].strip().strip('"')
                                break
                        
                        # If we found a description, use it; otherwise fall back to the name
                        if description:
                            friendly_names[sink_name] = description
                        else:
                            # Fall back to a humanized version of the sink name
                            if sink_name.startswith("alsa_output."):
                                humanized = sink_name.replace("alsa_output.", "").replace("_", " ").replace(".", " ").title()
                                friendly_names[sink_name] = humanized
            
            # Second fallback: direct mapping by index if no match was found
            if not friendly_names:
                for section in sink_sections[1:]:
                    lines = section.split("\n")
                    sink_id = None
                    description = None
                    
                    if lines and lines[0].strip():
                        sink_id = lines[0].strip().split(':')[0].strip()
                    
                    for line in lines:
                        if "Description:" in line:
                            description = line.split("Description:")[1].strip()
                            break
                    
                    if sink_id is not None and description and len(self.sink_list) > int(sink_id):
                        friendly_names[self.sink_list[int(sink_id)]] = description
            
            # Store the global mapping between sink IDs and friendly names for use elsewhere
            self.friendly_sink_names = friendly_names
            
            # Populate the dropdown with friendly names
            self.sink_store.clear()
            
            # Store the mapping between display name and actual sink ID
            self.sink_display_map = {}
            
            for sink in self.sink_list:
                display_name = friendly_names.get(sink, sink)
                self.sink_display_map[display_name] = sink
                
                # Determine the appropriate icon
                icon_name = self.get_sink_icon_name(sink, display_name)
                
                # Add to the store: ID, Display Name, Icon Name
                self.sink_store.append([sink, display_name, icon_name])
            
            # Select the current default sink
            current_sink = subprocess.getoutput("pactl get-default-sink").strip()
            if current_sink in self.sink_list:
                current_display_name = friendly_names.get(current_sink, current_sink)
                for i, row in enumerate(self.sink_store):
                    if row[1] == current_display_name:
                        self.sink_dropdown.set_active(i)
                        break
                        
        except Exception as e:
            print(f"Error updating sink list: {e}")

    def update_source_list(self, button=None):
        """Update the dropdown list with available input sources."""
        try:
            # Get detailed source information
            detailed_output = subprocess.getoutput("pactl list sources")
            source_sections = detailed_output.split("Source #")
            
            # Get the short list for source IDs
            output = subprocess.getoutput("pactl list short sources")
            sources = output.split("\n")
            self.source_list = [source.split("\t")[1] for source in sources if source]
            
            # First pass: Extract source IDs and their indices
            source_indices = {}
            for idx, section in enumerate(source_sections[1:], 0):
                lines = section.split("\n")
                if lines and lines[0].strip():
                    source_id = lines[0].strip().split(':')[0].strip()
                    source_indices[source_id] = idx
            
            # Create a mapping of source IDs to friendly names
            friendly_names = {}
            
            # Direct method: Use pactl list short sources for proper matching
            short_sources_output = subprocess.getoutput("pactl list short sources")
            short_sources = short_sources_output.split("\n")
            
            for source_line in short_sources:
                if not source_line.strip():
                    continue
                    
                parts = source_line.split("\t")
                if len(parts) >= 2:
                    source_id = parts[0].strip()
                    source_name = parts[1].strip()
                    
                    # Get the corresponding section from the detailed output
                    if source_id in source_indices:
                        section_idx = source_indices[source_id]
                        section = source_sections[section_idx + 1]  # +1 because we skipped the first empty section
                        lines = section.split("\n")
                        
                        # Look for the description
                        description = None
                        
                        # Try multiple potential description fields
                        for line in lines:
                            line = line.strip()
                            
                            # Primary pattern: Description field
                            if line.startswith("Description:"):
                                description = line.split("Description:")[1].strip()
                                break
                                
                            # Properties patterns
                            elif "device.description" in line and "=" in line:
                                description = line.split("=")[1].strip().strip('"')
                                break
                            elif "alsa.card_name" in line and "=" in line:
                                description = line.split("=")[1].strip().strip('"')
                                break
                            elif "device.product.name" in line and "=" in line:
                                description = line.split("=")[1].strip().strip('"')
                                break
                            elif "bluez.alias" in line and "=" in line:
                                description = line.split("=")[1].strip().strip('"')
                                break
                        
                        # Ignore monitor sources
                        if "monitor" in source_name.lower() and not source_name.lower().startswith("monitor"):
                            continue
                            
                        # If we found a description, use it; otherwise fall back to the name
                        if description:
                            # Add "Microphone: " prefix to distinguish if it's an input source
                            if not "monitor" in description.lower():
                                friendly_names[source_name] = description
                            else:
                                continue  # Skip monitor sources
                        else:
                            # Fall back to a humanized version of the source name
                            if source_name.startswith("alsa_input."):
                                humanized = source_name.replace("alsa_input.", "").replace("_", " ").replace(".", " ").title()
                                friendly_names[source_name] = humanized
            
            # Store the global mapping between source IDs and friendly names for use elsewhere
            self.friendly_source_names = friendly_names
            
            # Populate the dropdown with friendly names
            self.source_store.clear()
            
            # Store the mapping between display name and actual source ID
            self.source_display_map = {}
            
            for source in self.source_list:
                # Skip monitor sources
                if "monitor" in source.lower() and not source.lower().startswith("monitor"):
                    continue
                    
                display_name = friendly_names.get(source, source)
                if display_name in friendly_names.values():  # Only add if we have a friendly name
                    self.source_display_map[display_name] = source
                    
                    # Determine the appropriate icon
                    icon_name = self.get_source_icon_name(source, display_name)
                    
                    # Add to the store: ID, Display Name, Icon Name
                    self.source_store.append([source, display_name, icon_name])
            
            # Select the current default source
            current_source = subprocess.getoutput("pactl get-default-source").strip()
            if current_source in self.source_list:
                current_display_name = friendly_names.get(current_source, current_source)
                for i, row in enumerate(self.source_store):
                    if row[1] == current_display_name:
                        self.source_dropdown.set_active(i)
                        break
                        
        except Exception as e:
            print(f"Error updating source list: {e}")

    def add_tabs(self):
        # Define tab names and their corresponding initialization methods
        tab_definitions = {
            "Wi-Fi": self.initialize_wifi_tab,
            "Bluetooth": self.initialize_bluetooth_tab,
            "Volume": self.initialize_volume_tab,
            "Battery": self.initialize_battery_tab,
            "Display": self.initialize_display_tab,
        }

        # Add tabs to the notebook but don't initialize them yet
        for tab_name, init_method in tab_definitions.items():
            if self.tab_visibility.get(tab_name, True):
                placeholder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                self.tabs[tab_name] = placeholder
                self.notebook.append_page(placeholder, self.create_tab_label_with_icon(tab_name))

    def initialize_wifi_tab(self):
        if not self._tabs_initialized.get("Wi-Fi", False):
            print("Initializing Wi-Fi tab...")
            self.refresh_wifi(None)  # Load Wi-Fi content
            self._tabs_initialized["Wi-Fi"] = True

    def initialize_bluetooth_tab(self):
        if not self._tabs_initialized.get("Bluetooth", False):
            print("Initializing Bluetooth tab...")
            self.refresh_bluetooth(None)  # Load Bluetooth content
            self._tabs_initialized["Bluetooth"] = True

    def initialize_volume_tab(self):
        if not self._tabs_initialized.get("Volume", False):
            print("Initializing Volume tab...")
            self.refresh_app_volume(None)  # Load Volume content
            self._tabs_initialized["Volume"] = True

    def initialize_battery_tab(self):
        if not self._tabs_initialized.get("Battery", False):
            print("Initializing Battery tab...")
            self.battery_tab = BatteryTab(self)  # Initialize Battery tab
            self.tabs["Battery"] = self.battery_tab
            self._tabs_initialized["Battery"] = True

    def initialize_display_tab(self):
        if not self._tabs_initialized.get("Display", False):
            print("Initializing Display tab...")
            # Set a flag to indicate initialization is in progress to prevent infinite loops
            self._tabs_initialized["Display"] = True
            # Call refresh_display to load the content
            GLib.idle_add(self.refresh_display, None)  # Schedule refresh on the main thread

    def refresh_display(self, button=None):
        # Create a new scroll container for the display tab
        display_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        display_container.set_margin_start(10)
        display_container.set_margin_end(10)
        display_container.set_margin_top(10)
        display_container.set_margin_bottom(10)
        
        # Create content for the display tab
        brightness_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        brightness_box.set_vexpand(True)
        
        # Header with Display title and icon
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_margin_bottom(10)
        
        display_icon = Gtk.Image.new_from_icon_name("video-display-symbolic", Gtk.IconSize.DIALOG)
        header_box.pack_start(display_icon, False, False, 0)
        
        display_title = Gtk.Label(label="Display Settings")
        display_title.get_style_context().add_class("wifi-header")
        header_box.pack_start(display_title, False, False, 0)
        
        brightness_box.pack_start(header_box, False, False, 0)
        
        # Content area with scrolling
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_window.set_vexpand(True)
        
        display_controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        display_controls.set_margin_top(10)
        
        # Brightness section
        brightness_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        brightness_label = Gtk.Label(label="Brightness")
        brightness_label.set_xalign(0)
        brightness_section.pack_start(brightness_label, False, False, 0)
        
        # Brightness slider
        self.brightness_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.brightness_scale.set_hexpand(True)
        self.brightness_scale.set_value(self.get_current_brightness())
        self.brightness_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.brightness_scale.connect("value-changed", self.set_brightness)
        brightness_section.pack_start(self.brightness_scale, False, False, 0)
        
        # Quick brightness buttons
        brightness_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.brightness_zero = Gtk.Button(label="0%")
        self.brightness_zero.connect("clicked", self.zero)
        brightness_buttons.pack_start(self.brightness_zero, True, True, 0)
        
        self.brightness_tfive = Gtk.Button(label="25%")
        self.brightness_tfive.connect("clicked", self.tfive)
        brightness_buttons.pack_start(self.brightness_tfive, True, True, 0)
        
        self.brightness_fifty = Gtk.Button(label="50%")
        self.brightness_fifty.connect("clicked", self.fifty)
        brightness_buttons.pack_start(self.brightness_fifty, True, True, 0)
        
        self.brightness_sfive = Gtk.Button(label="75%")
        self.brightness_sfive.connect("clicked", self.sfive)
        brightness_buttons.pack_start(self.brightness_sfive, True, True, 0)
        
        self.brightness_hund = Gtk.Button(label="100%")
        self.brightness_hund.connect("clicked", self.hund)
        brightness_buttons.pack_start(self.brightness_hund, True, True, 0)
        
        brightness_section.pack_start(brightness_buttons, False, False, 0)
        display_controls.pack_start(brightness_section, False, False, 0)
        
        # Blue light filter section
        bluelight_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        bluelight_section.set_margin_top(15)
        
        blue_light_label = Gtk.Label(label="Blue Light Filter")
        blue_light_label.set_xalign(0)
        bluelight_section.pack_start(blue_light_label, False, False, 0)
        
        # Blue light slider
        self.blue_light_slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 2500, 6500, 100)
        self.blue_light_slider.set_hexpand(True)
        self.blue_light_slider.set_value_pos(Gtk.PositionType.RIGHT)
        
        # Set initial value from settings
        settings = load_settings()
        saved_gamma = settings.get("gamma", 6500)
        self.blue_light_slider.set_value(saved_gamma)
        self.blue_light_slider.connect("value-changed", self.set_bluelight_filter)
        bluelight_section.pack_start(self.blue_light_slider, False, False, 0)
        
        # Quick blue light buttons
        bluelight_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.blue_zero = Gtk.Button(label="0%")
        self.blue_zero.connect("clicked", self.bzero)
        bluelight_buttons.pack_start(self.blue_zero, True, True, 0)
        
        self.blue_tfive = Gtk.Button(label="25%")
        self.blue_tfive.connect("clicked", self.btfive)
        bluelight_buttons.pack_start(self.blue_tfive, True, True, 0)
        
        self.blue_fifty = Gtk.Button(label="50%")
        self.blue_fifty.connect("clicked", self.bfifty)
        bluelight_buttons.pack_start(self.blue_fifty, True, True, 0)
        
        self.blue_sfive = Gtk.Button(label="75%")
        self.blue_sfive.connect("clicked", self.bsfive)
        bluelight_buttons.pack_start(self.blue_sfive, True, True, 0)
        
        self.blue_hund = Gtk.Button(label="100%")
        self.blue_hund.connect("clicked", self.bhund)
        bluelight_buttons.pack_start(self.blue_hund, True, True, 0)
        
        bluelight_section.pack_start(bluelight_buttons, False, False, 0)
        display_controls.pack_start(bluelight_section, False, False, 0)
        
        scroll_window.add(display_controls)
        brightness_box.pack_start(scroll_window, True, True, 0)
        
        display_container.pack_start(brightness_box, True, True, 0)
        
        # Find the Display tab and replace its content
        for i in range(self.notebook.get_n_pages()):
            page = self.notebook.get_nth_page(i)
            if self.get_tab_name_from_label(page) == "Display":
                # Remove old widgets
                for child in page.get_children():
                    page.remove(child)
                # Add new content
                page.pack_start(display_container, True, True, 0)
                break
        
        # Store reference for future access
        self.tabs["Display"] = display_container
        
        # Don't auto-switch to this tab as it causes an infinite loop
        # self.notebook.set_current_page(self.notebook.page_num(display_container))
        
        display_container.show_all()
        # Make sure the parent page shows all children
        for i in range(self.notebook.get_n_pages()):
            page = self.notebook.get_nth_page(i)
            if self.get_tab_name_from_label(page) == "Display":
                page.show_all()
                break

    def on_sink_selected(self, combo):
        """Change the default sink when a new one is selected."""
        active_iter = combo.get_active_iter()
        if active_iter is not None:
            # Get data from model
            sink_id = self.sink_store[active_iter][0]
            display_name = self.sink_store[active_iter][1]
            
            current_sink = subprocess.getoutput("pactl get-default-sink").strip()
            if sink_id != current_sink:
                subprocess.run(["pactl", "set-default-sink", sink_id])
                print(f"Switched to sink: {display_name} ({sink_id})")

    def on_source_selected(self, combo):
        """Change the default source when a new one is selected."""
        active_iter = combo.get_active_iter()
        if active_iter is not None:
            # Get data from model
            source_id = self.source_store[active_iter][0]
            display_name = self.source_store[active_iter][1]
            
            current_source = subprocess.getoutput("pactl get-default-source").strip()
            if source_id != current_source:
                subprocess.run(["pactl", "set-default-source", source_id])
                print(f"Switched to source: {display_name} ({source_id})")

    def populate_settings_tab(self):
        """Populate the settings tab with tabs management options."""
        if not hasattr(self, 'settings_box'):
            return
            
        # Clear any existing content
        for child in self.settings_box.get_children():
            self.settings_box.remove(child)

        # Header with Settings title and icon
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_margin_bottom(20)
        
        settings_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.DIALOG)
        header_box.pack_start(settings_icon, False, False, 0)
        
        settings_label = Gtk.Label(label="Settings")
        settings_label.get_style_context().add_class("wifi-header")
        header_box.pack_start(settings_label, False, False, 0)
        
        self.settings_box.pack_start(header_box, False, False, 0)
        
        # Tab visibility and order section
        tab_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tab_section.set_margin_bottom(15)
        
        section_label = Gtk.Label()
        section_label.set_markup("<b>Tab Visibility and Order</b>")
        section_label.set_halign(Gtk.Align.START)
        section_label.set_margin_bottom(5)
        tab_section.pack_start(section_label, False, False, 0)
        
        instruction_label = Gtk.Label(label="Use the checkboxes to show/hide tabs and the arrows to change tab order.")
        instruction_label.set_halign(Gtk.Align.START)
        instruction_label.set_margin_bottom(10)
        tab_section.pack_start(instruction_label, False, False, 0)

        # Create a list of tab names sorted by their current positions
        tab_list = list(self.tabs.keys())
        tab_list.sort(key=lambda tab_name: 
            self.notebook.page_num(self.tabs[tab_name]) 
            if self.notebook.page_num(self.tabs[tab_name]) != -1 
            else float('inf')
        )
        
        # Remove Settings from the tab list since it's now a button, not a tab
        if "Settings" in tab_list:
            tab_list.remove("Settings")
        
        # Map tab names to appropriate icons
        tab_icons = {
            "Wi-Fi": "network-wireless-symbolic",
            "Bluetooth": "bluetooth-symbolic",
            "Volume": "audio-volume-high-symbolic",
            "Application Volume": "audio-speakers-symbolic",
            "Display": "video-display-symbolic",
            "Battery": "battery-good-symbolic",
            "Brightness": "display-brightness-symbolic"
        }
        
        self.check_buttons = {}
        for tab_name in tab_list:
            # Create a stylized container for each tab
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row_box.set_margin_bottom(5)
            
            # Checkbox for visibility
            check_button = Gtk.CheckButton()
            check_button.set_active(self.tab_visibility.get(tab_name, True))
            check_button.connect("toggled", self.toggle_tab, tab_name)
            row_box.pack_start(check_button, False, False, 0)
            self.check_buttons[tab_name] = check_button
            
            # Add icon for the tab
            icon_name = tab_icons.get(tab_name, "applications-system-symbolic")  # Default icon if not found
            tab_icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.SMALL_TOOLBAR)
            row_box.pack_start(tab_icon, False, False, 0)
            
            # Tab label
            tab_label = Gtk.Label(label=tab_name)
            tab_label.set_halign(Gtk.Align.START)
            row_box.pack_start(tab_label, True, True, 0)
            
            # Button container for movement controls
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            
            # Up button for moving tab up in order
            up_button = Gtk.Button()
            up_button.set_tooltip_text(f"Move {tab_name} tab up")
            up_image = Gtk.Image.new_from_icon_name("go-up-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
            up_button.set_image(up_image)
            up_button.connect("clicked", self.move_tab_up, tab_name)
            button_box.pack_start(up_button, False, False, 0)
            
            # Down button for moving tab down in order
            down_button = Gtk.Button()
            down_button.set_tooltip_text(f"Move {tab_name} tab down")
            down_image = Gtk.Image.new_from_icon_name("go-down-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
            down_button.set_image(down_image)
            down_button.connect("clicked", self.move_tab_down, tab_name)
            button_box.pack_start(down_button, False, False, 0)
            
            row_box.pack_end(button_box, False, False, 0)
            
            tab_section.pack_start(row_box, False, False, 0)
        
        self.settings_box.pack_start(tab_section, False, False, 0)
        
        # Add a separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(5)
        separator.set_margin_bottom(15)
        self.settings_box.pack_start(separator, False, False, 0)

    def toggle_tab(self, button, tab_name):
        """ Show or hide a tab based on checkbox state """
        tab_widget = self.tabs[tab_name]
        page_num = self.notebook.page_num(tab_widget)

        if button.get_active():
            if page_num == -1:  
                # Create a tab label with an icon
                tab_label_box = self.create_tab_label_with_icon(tab_name)
                
                if tab_name in self.original_tab_positions:
                    # Insert at original position
                    position = min(self.original_tab_positions[tab_name], self.notebook.get_n_pages())
                    self.notebook.insert_page(tab_widget, tab_label_box, position)
                else:
                    # If no original position known, just append
                    self.notebook.append_page(tab_widget, tab_label_box)
                self.notebook.show_all()  
                self.tab_visibility[tab_name] = True
        else:
            if page_num != -1:
                # Store the position
                self.original_tab_positions[tab_name] = page_num
                self.notebook.remove_page(page_num)
                tab_widget.hide()  
                self.tab_visibility[tab_name] = False

        self.save_settings()

    def save_settings(self):
        """ Save tab visibility states and positions to a file """
        try:
            # Save tab visibility and positions
            settings_data = {
                "visibility": self.tab_visibility,
                "positions": {}
            }
            
            # Store current positions of all tabs
            for tab_name in self.tabs.keys():
                tab_widget = self.tabs[tab_name]
                page_num = self.notebook.page_num(tab_widget)
                if page_num != -1:
                    settings_data["positions"][tab_name] = page_num
                elif tab_name in self.original_tab_positions:
                    settings_data["positions"][tab_name] = self.original_tab_positions[tab_name]
            
            # Ensure the config directory exists
            os.makedirs(CONFIG_PATH, exist_ok=True)
            with open(SETTINGS_FILE, "w") as f:
                json.dump(settings_data, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        """ Load tab visibility states and positions from a file """
        settings = {"visibility": {}, "positions": {}}
        if os.path.exists(SETTINGS_FILE):
            try:
                # Use a thread to avoid blocking UI during file I/O
                def load_settings_thread():
                    nonlocal settings
                    try:
                        with open(SETTINGS_FILE, "r") as f:
                            data = json.load(f)
                            # Handle legacy format (just visibility settings)
                            if isinstance(data, dict) and not ("visibility" in data and "positions" in data):
                                settings["visibility"] = data
                            else:
                                settings = data
                            
                            # Initialize original_tab_positions from saved positions
                            GLib.idle_add(lambda: setattr(self, 'original_tab_positions', settings.get("positions", {})))
                    except json.JSONDecodeError:
                        settings = {"visibility": {}, "positions": {}}
                
                # Start in a thread but wait for it to complete since we need the settings
                thread = threading.Thread(target=load_settings_thread)
                thread.start()
                thread.join(0.1)  # Short timeout to not block UI too long
                
                return settings["visibility"]
            except Exception as e:
                print(f"Error loading settings: {e}")
                return {}
        return {}

    def enable_bluetooth(self, button):
        if not shutil.which("bluetoothctl"):
            error_msg = "BlueZ is not installed. Install it with:\n\nsudo pacman -S bluez bluez-utils"
            self.show_error(error_msg)
            print(error_msg)
            return False

        print("===== Attempting to enable Bluetooth =====")
        
        # Try using bluetoothctl directly first - this has better user permissions
        try:
            print("Attempting to enable using bluetoothctl power on...")
            # This is a more direct way that works for regular users
            result = subprocess.run(
                ["bluetoothctl", "power", "on"],
                capture_output=True,
                text=True
            )
            
            print(f"bluetoothctl power on result: {result.returncode}")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            
            if result.returncode == 0:
                print("Bluetooth enabled via bluetoothctl")
                # Check if it's really on
                check_result = subprocess.run(
                    ["bluetoothctl", "show"],
                    capture_output=True,
                    text=True
                )
                if "Powered: yes" in check_result.stdout:
                    print("Confirmed Bluetooth is powered on")
                    return True
                else:
                    print("Warning: Bluetooth power on command succeeded but Bluetooth is not powered on")
        except Exception as e:
            print(f"Error using bluetoothctl to enable: {e}")
        
        # Try using rfkill which doesn't require root permissions
        try:
            print("Attempting to enable using rfkill...")
            rfkill_status = subprocess.run(
                ["rfkill", "list", "bluetooth"], 
                capture_output=True, 
                text=True
            )
            
            print(f"rfkill status output: {rfkill_status.stdout}")
            
            if "bluetooth" not in rfkill_status.stdout:
                print("No Bluetooth adapter found in rfkill")
            elif "blocked: yes" in rfkill_status.stdout:
                # Unblock Bluetooth if it's blocked
                print("Bluetooth is blocked, attempting to unblock...")
                result = subprocess.run(
                    ["rfkill", "unblock", "bluetooth"], 
                    capture_output=True,
                    text=True
                )
                
                print(f"rfkill unblock result: {result.returncode}")
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
                
                if result.returncode == 0:
                    print("Bluetooth unblocked via rfkill.")
                    
                    # Check if service needs to be started too
                    service_status = subprocess.run(
                        ["systemctl", "is-active", "bluetooth"], 
                        capture_output=True, 
                        text=True
                    ).stdout.strip()
                    
                    print(f"Bluetooth service status: {service_status}")
                    
                    if service_status != "active":
                        # Try to start the service, but it's not critical if it fails
                        # since we've already unblocked through rfkill
                        try:
                            print("Starting bluetooth service...")
                            subprocess.run(["systemctl", "start", "bluetooth"])
                        except Exception as e:
                            print(f"Failed to start bluetooth service: {e}")
                            pass
                    
                    # Now check if Bluetooth is really active
                    for _ in range(3):
                        bt_status = subprocess.run(
                            ["systemctl", "is-active", "bluetooth"], 
                            capture_output=True, 
                            text=True
                        ).stdout.strip()
                        
                        print(f"Checking if bluetooth is active: {bt_status}")
                        
                        if bt_status == "active":
                            print("Bluetooth service is active.")
                            
                            # Also verify with bluetoothctl
                            check_result = subprocess.run(
                                ["bluetoothctl", "show"],
                                capture_output=True,
                                text=True
                            )
                            if "Powered: yes" in check_result.stdout:
                                print("Confirmed Bluetooth is powered on")
                                return True
                            else:
                                print("Warning: Service is active but Bluetooth is not powered on")
                                # Try one more time to power on explicitly
                                subprocess.run(["bluetoothctl", "power", "on"])
                                return True
                        time.sleep(0.5)
            else:
                # Not blocked, just check service
                print("Bluetooth is not blocked in rfkill")
                service_status = subprocess.run(
                    ["systemctl", "is-active", "bluetooth"], 
                    capture_output=True, 
                    text=True
                ).stdout.strip()
                
                print(f"Bluetooth service status: {service_status}")
                
                if service_status == "active":
                    print("Bluetooth service is already active.")
                    # Also verify with bluetoothctl
                    check_result = subprocess.run(
                        ["bluetoothctl", "show"],
                        capture_output=True,
                        text=True
                    )
                    if "Powered: yes" in check_result.stdout:
                        print("Confirmed Bluetooth is powered on")
                        return True
                    else:
                        print("Warning: Service is active but Bluetooth is not powered on")
                        # Try to power on explicitly
                        subprocess.run(["bluetoothctl", "power", "on"])
                        return True
        except FileNotFoundError as e:
            print(f"Command not found: {e}")
            print("rfkill not found, trying systemctl")
        except Exception as e:
            print(f"Error using rfkill: {e}")
        
        # Fallback to systemctl method
        try:
            print("Attempting to enable using systemctl...")
            # Check if we're running with sufficient privileges
            test_result = subprocess.run(
                ["systemctl", "status", "bluetooth"],
                capture_output=True,
                text=True
            )
            
            print(f"systemctl status result: {test_result.returncode}")
            print(f"stdout: {test_result.stdout}")
            print(f"stderr: {test_result.stderr}")
            
            if "Access denied" in test_result.stderr:
                # Show error message but continue (bluez might already be running)
                print("Insufficient privileges to control Bluetooth service")
            else:
                # We have privileges, try to start Bluetooth
                print("Starting bluetooth service...")
                start_result = subprocess.run(
                    ["systemctl", "start", "bluetooth"],
                    capture_output=True,
                    text=True
                )
                print(f"systemctl start result: {start_result.returncode}")
                print(f"stdout: {start_result.stdout}")
                print(f"stderr: {start_result.stderr}")

            # Check if bluetooth is active
            for _ in range(5):
                bt_status = subprocess.run(
                    ["systemctl", "is-active", "bluetooth"], 
                    capture_output=True, 
                    text=True
                ).stdout.strip()
                
                print(f"Checking if bluetooth is active: {bt_status}")
                
                if bt_status == "active":
                    print("Bluetooth enabled via systemctl.")
                    # Also verify with bluetoothctl
                    check_result = subprocess.run(
                        ["bluetoothctl", "show"],
                        capture_output=True,
                        text=True
                    )
                    if "Powered: yes" in check_result.stdout:
                        print("Confirmed Bluetooth is powered on")
                        return True
                    else:
                        print("Warning: Service is active but Bluetooth is not powered on")
                        # Try to power on explicitly
                        subprocess.run(["bluetoothctl", "power", "on"])
                        return True
                time.sleep(1)
                
            error_msg = "Failed to enable Bluetooth. Make sure BlueZ is installed."
            self.show_error(error_msg)
            print(error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Failed to enable Bluetooth: {str(e)}"
            self.show_error(error_msg)
            print(error_msg)
            return False
        
        print("===== Finished enable Bluetooth attempt =====")
        return False

    def disable_bluetooth(self, button):
        print("===== Attempting to disable Bluetooth =====")
        
        # Try using bluetoothctl directly first - this has better user permissions
        try:
            print("Attempting to disable using bluetoothctl power off...")
            # This is a more direct way that works for regular users
            result = subprocess.run(
                ["bluetoothctl", "power", "off"],
                capture_output=True,
                text=True
            )
            
            print(f"bluetoothctl power off result: {result.returncode}")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            
            if result.returncode == 0:
                print("Bluetooth disabled via bluetoothctl")
                # Update UI
                self.bt_status_label.set_text("Bluetooth is disabled")
                # Clear the device list
                self.bt_listbox.foreach(lambda row: self.bt_listbox.remove(row))
                return
        except Exception as e:
            print(f"Error using bluetoothctl to disable: {e}")
            
        # Try rfkill next
        try:
            print("Attempting to disable using rfkill...")
            # Get bluetooth block status
            rfkill_status = subprocess.run(
                ["rfkill", "list", "bluetooth"], 
                capture_output=True, 
                text=True
            )
            
            print(f"rfkill status output: {rfkill_status.stdout}")
            
            if "bluetooth" not in rfkill_status.stdout:
                print("No Bluetooth adapter found in rfkill")
            elif "blocked: no" in rfkill_status.stdout:
                # Only block if not already blocked
                print("Bluetooth is not blocked, attempting to block...")
                result = subprocess.run(
                    ["rfkill", "block", "bluetooth"], 
                    capture_output=True,
                    text=True
                )
                
                print(f"rfkill block result: {result.returncode}")
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
                
                if result.returncode == 0:
                    print("Bluetooth disabled via rfkill.")
                    
                    # Update UI
                    self.bt_status_label.set_text("Bluetooth is disabled")
                    # Clear the device list
                    self.bt_listbox.foreach(lambda row: self.bt_listbox.remove(row))
                    return
                else:
                    print(f"rfkill failed: {result.stderr}")
            else:
                print("Bluetooth already blocked according to rfkill")
                # Update UI for consistency
                self.bt_status_label.set_text("Bluetooth is disabled")
                # Clear the device list
                self.bt_listbox.foreach(lambda row: self.bt_listbox.remove(row))
                return
                
        except FileNotFoundError:
            print("rfkill not found, trying systemctl")
        except Exception as e:
            print(f"Error using rfkill: {e}")
        
        # Fallback to systemctl method that requires root
        try:
            print("Attempting to disable using systemctl...")
            # Check if we're running with sufficient privileges
            test_result = subprocess.run(
                ["systemctl", "status", "bluetooth"],
                capture_output=True,
                text=True
            )
            
            print(f"systemctl status result: {test_result.returncode}")
            print(f"stdout: {test_result.stdout}")
            print(f"stderr: {test_result.stderr}")
            
            if "Access denied" in test_result.stderr:
                # Show error message about insufficient privileges
                error_msg = "Cannot disable Bluetooth via system service: insufficient privileges"
                print(error_msg)
                self.show_error(error_msg)
            else:
                # We have privileges, try to stop Bluetooth
                print("Attempting to stop bluetooth service...")
                stop_result = subprocess.run(
                    ["systemctl", "stop", "bluetooth"],
                    capture_output=True,
                    text=True
                )
                print(f"systemctl stop result: {stop_result.returncode}")
                print(f"stdout: {stop_result.stdout}")
                print(f"stderr: {stop_result.stderr}")
                
                if stop_result.returncode == 0:
                    print("Bluetooth disabled via systemctl.")
                else:
                    print(f"Failed to stop Bluetooth service: {stop_result.stderr}")
        except Exception as e:
            error_msg = f"Failed to disable Bluetooth: {str(e)}"
            self.show_error(error_msg)
            print(error_msg)
        
        # Update UI regardless of success (user will see if it worked)
        self.bt_status_label.set_text("Bluetooth is disabled")
        # Clear the device list
        self.bt_listbox.foreach(lambda row: self.bt_listbox.remove(row))
        print("===== Finished disable Bluetooth attempt =====")

    def on_bluetooth_switch_toggled(self, switch, gparam):        
        # Get the current state    
        active = switch.get_active()
        print(f"User toggled Bluetooth switch to {'ON' if active else 'OFF'}")
        
        # Block signal handling to prevent recursive events
        switch.handler_block_by_func(self.on_bluetooth_switch_toggled)
        
        try:
            if active:
                # Attempt to enable Bluetooth
                self.bt_status_label.set_text("Enabling Bluetooth...")
                success = self.enable_bluetooth(None)
                
                if success:
                    self.bt_status_label.set_text("Scanning for devices...")
                    # Automatically scan when enabled
                    GLib.timeout_add(1000, self.refresh_bluetooth, None)
                else:
                    # If enabling failed, revert the switch to off
                    print("Failed to enable Bluetooth, reverting switch")
                    switch.set_active(False)
                    self.bt_status_label.set_text("Failed to enable Bluetooth")
            else:
                # Attempt to disable Bluetooth
                self.bt_status_label.set_text("Disabling Bluetooth...")
                self.disable_bluetooth(None)
                # UI updates are handled in the disable_bluetooth method
        except Exception as e:
            print(f"Exception in bluetooth switch handler: {e}")
            # Make sure the switch reflects the actual bluetooth state
            self.update_bluetooth_switch_state()
        finally:
            # Unblock signal handlers when done
            switch.handler_unblock_by_func(self.on_bluetooth_switch_toggled)
    
    def update_bluetooth_switch_state(self):
        """Update the Bluetooth switch to match the actual Bluetooth state."""
        # Run this in a thread to avoid blocking the UI
        def check_bt_status():
            try:
                # Check if bluetooth is actually on using bluetoothctl
                check_result = subprocess.run(
                    ["bluetoothctl", "show"],
                    capture_output=True,
                    text=True
                )
                powered_on = "Powered: yes" in check_result.stdout
                
                # Update UI in main thread
                GLib.idle_add(lambda: self._update_bt_switch(powered_on))
            except Exception as e:
                print(f"Error updating bluetooth switch state: {e}")
                
                # In case of error, use systemctl as fallback
                try:
                    bt_status = subprocess.run(
                        ["systemctl", "is-active", "bluetooth"], 
                        capture_output=True, 
                        text=True
                    ).stdout.strip()
                    
                    # Update UI in main thread
                    GLib.idle_add(lambda: self._update_bt_switch(bt_status == "active"))
                    
                    print(f"Bluetooth service is {bt_status}")
                except Exception as e2:
                    print(f"Error using systemctl fallback: {e2}")
                    # If all else fails, don't change the switch state
                    
            return False  # To stop GLib.idle_add
        
        # Start the thread to check bluetooth status
        thread = threading.Thread(target=check_bt_status)
        thread.daemon = True
        thread.start()
        
    def _update_bt_switch(self, is_active):
        """Helper to update the bluetooth switch from the main thread."""
        # Block signals during update
        self.bt_status_switch.handler_block_by_func(self.on_bluetooth_switch_toggled)
        
        # Set the switch state
        self.bt_status_switch.set_active(is_active)
        
        # Unblock signals
        self.bt_status_switch.handler_unblock_by_func(self.on_bluetooth_switch_toggled)
        
        return False  # To stop GLib.idle_add

    def refresh_bluetooth(self, button):
        """Refreshes the list of Bluetooth devices with improved UI feedback."""
        # Update status
        self.bt_status_label.set_text("Scanning for devices...")
        
        # Clear existing devices
        self.bt_listbox.foreach(lambda row: self.bt_listbox.remove(row))
        
        # Check if bluetooth is active
        bt_status = subprocess.run(
            ["systemctl", "is-active", "bluetooth"], capture_output=True, text=True
        ).stdout.strip()
        
        if bt_status != "active":
            self.bt_status_label.set_text("Bluetooth is disabled.")
            return
        
        # Start a thread to handle scanning
        thread = threading.Thread(target=self._refresh_bluetooth_thread)
        thread.daemon = True
        thread.start()

    def _refresh_bluetooth_thread(self):
        """Performs Bluetooth scanning in a background thread."""
        # Run scan for 5 seconds
        try:
            subprocess.run(["bluetoothctl", "scan", "on"], timeout=5, 
                           capture_output=True, text=True)
        except subprocess.TimeoutExpired:
            # This is normal - we're just scanning for a fixed duration
            pass
        
        # Turn off scanning
        subprocess.run(["bluetoothctl", "scan", "off"], capture_output=True, text=True)
        
        # Get all devices
        output = subprocess.run(["bluetoothctl", "devices"], 
                                capture_output=True, text=True).stdout.strip()
        devices = output.split('\n')
        
        # Update the UI from the main thread
        GLib.idle_add(self._update_bluetooth_list_with_rows, devices)

    def _update_bluetooth_list_with_rows(self, devices):
        """Updates the Bluetooth listbox with the provided devices using our new row class."""
        # Clear any existing devices
        self.bt_listbox.foreach(lambda row: self.bt_listbox.remove(row))
        
        if not devices or devices == [""]:
            self.bt_status_label.set_text("No Bluetooth devices found.")
            return
        
        # Add each device
        for device in devices:
            if device.strip():  # Skip empty lines
                row = BluetoothDeviceRow(device)
                self.bt_listbox.add(row)
        
        self.bt_listbox.show_all()
        self.bt_status_label.set_text("Scan complete")
        return False  # Don't repeat the timeout

    def show_error(self, message):
        """ Displays an error message in a popup """
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            destroy_with_parent=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

    def connect_bluetooth_device_selected(self, button):
        """Connect to the selected Bluetooth device."""
        selected_row = self.bt_listbox.get_selected_row()
        if not selected_row:
            return
        
        mac_address = selected_row.get_mac_address()
        device_name = selected_row.get_device_name()
        
        # Show connecting status
        self.bt_status_label.set_text(f"Connecting to {device_name}...")
        
        # Use a thread to not block the UI
        def connect_thread():
            try:
                subprocess.run(["bluetoothctl", "pair", mac_address], capture_output=True, text=True)
                subprocess.run(["bluetoothctl", "connect", mac_address], capture_output=True, text=True)
                
                # Update UI from main thread
                GLib.idle_add(lambda: self.bt_status_label.set_text(f"Connected to {device_name}"))
                GLib.idle_add(self.refresh_bluetooth, None)
            except Exception as e:
                GLib.idle_add(lambda: self.bt_status_label.set_text(f"Connection failed: {str(e)}"))
        
        thread = threading.Thread(target=connect_thread)
        thread.daemon = True
        thread.start()

    def disconnect_bluetooth_device_selected(self, button):
        """Disconnect the selected Bluetooth device."""
        selected_row = self.bt_listbox.get_selected_row()
        if not selected_row:
            return
        
        mac_address = selected_row.get_mac_address()
        device_name = selected_row.get_device_name()
        
        self.bt_status_label.set_text(f"Disconnecting from {device_name}...")
        
        def disconnect_thread():
            try:
                subprocess.run(["bluetoothctl", "disconnect", mac_address], capture_output=True, text=True)
                
                GLib.idle_add(lambda: self.bt_status_label.set_text(f"Disconnected from {device_name}"))
                GLib.idle_add(self.refresh_bluetooth, None)
            except Exception as e:
                GLib.idle_add(lambda: self.bt_status_label.set_text(f"Disconnection failed: {str(e)}"))
        
        thread = threading.Thread(target=disconnect_thread)
        thread.daemon = True
        thread.start()

    def on_device_row_activated(self, listbox, row):
        """Handle activation of a device row by connecting to it."""
        if row:
            self.connect_bluetooth_device_selected(None)

    def forget_bluetooth_device_selected(self, button):
        """Remove the selected Bluetooth device."""
        selected_row = self.bt_listbox.get_selected_row()
        if not selected_row:
            return
        
        mac_address = selected_row.get_mac_address()
        device_name = selected_row.get_device_name()
        
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            destroy_with_parent=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Forget Bluetooth Device"
        )
        dialog.format_secondary_text(f"Are you sure you want to forget the device '{device_name}'?")
        response = dialog.run()
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        self.bt_status_label.set_text(f"Removing {device_name}...")
        
        def forget_thread():
            try:
                subprocess.run(["bluetoothctl", "remove", mac_address], capture_output=True, text=True)
                
                GLib.idle_add(lambda: self.bt_status_label.set_text(f"Removed {device_name}"))
                GLib.idle_add(self.refresh_bluetooth, None)
            except Exception as e:
                GLib.idle_add(lambda: self.bt_status_label.set_text(f"Removal failed: {str(e)}"))
        
        thread = threading.Thread(target=forget_thread)
        thread.daemon = True
        thread.start()

    def mzero(self, button):
        self.set_mic_level(0)

    def mtfive(self, button):
        self.set_mic_level(25)

    def mfifty(self, button):
        self.set_mic_level(50)

    def msfive(self, button):
        self.set_mic_level(75)

    def mhund(self, button):
        self.set_mic_level(100)

    def vzero(self, button):
        self.set_volume_level(0)

    def vtfive(self, button):
        self.set_volume_level(25)

    def vfifty(self, button):
        self.set_volume_level(50)

    def vsfive(self, button):
        self.set_volume_level(75)

    def vhund(self, button):
        self.set_volume_level(100)

    def zero(self, button):
        self.set_brightness_level(0)

    def tfive(self, button):
        self.set_brightness_level(25)

    def fifty(self, button):
        self.set_brightness_level(50)

    def sfive(self, button):
        self.set_brightness_level(75)

    def hund(self, button):
        self.set_brightness_level(100)

    def set_mic_volume(self, scale):
        new_volume = int(scale.get_value())
        self.set_mic_level(new_volume)

    def get_current_mic_volume(self):
        try:
            output = subprocess.getoutput("pactl get-source-volume @DEFAULT_SOURCE@")
            volume = int(output.split("/")[1].strip().strip("%"))
            return volume
        except Exception as e:
            print("Error getting mic volume:", e)
            return 50  

    def refresh_wifi(self, button):
        # Prevent multiple simultaneous refreshes
        if getattr(self, '_is_refreshing', False):
            return
            
        self._is_refreshing = True
        
        # Get current tab to check if WiFi tab is active
        current_page = self.notebook.get_current_page()
        current_tab = self.notebook.get_nth_page(current_page)
        current_tab_name = self.get_tab_name_from_label(current_tab)
        
        # If we're not on the WiFi tab, just mark as not refreshing and return
        # This prevents unnecessary scans when the WiFi tab isn't visible
        if current_tab_name != "Wi-Fi" and button is not None:  # Allow forced refresh
            self._is_refreshing = False
            return
            
        thread = threading.Thread(target=self._refresh_wifi_thread)
        thread.daemon = True
        thread.start()

    def _refresh_wifi_thread(self):
        # We don't need the tabular format anymore as we'll use the standard output format
        # directly for all operations
        try:
            # Use rescan to make it faster for subsequent calls
            if hasattr(self, '_wifi_scanned_once') and self._wifi_scanned_once:
                # Just update the list without rescanning - much faster
                pass
            else:
                # On first scan, try to be quicker by using a short timeout
                try:
                    subprocess.run(["nmcli", "device", "wifi", "rescan"], timeout=1)
                except subprocess.TimeoutExpired:
                    # This is normal, it might take longer than our timeout
                    pass
                self._wifi_scanned_once = True
                
            GLib.idle_add(self._update_wifi_list)
        except Exception as e:
            print(f"Error in refresh WiFi thread: {e}")
            self._is_refreshing = False

    def _update_wifi_list(self, networks=None):
        # First store the selected row's SSID if any
        selected_row = self.wifi_listbox.get_selected_row()
        selected_ssid = selected_row.get_ssid() if selected_row else None
        
        # Clear the existing list
        self.wifi_listbox.foreach(lambda row: self.wifi_listbox.remove(row))
        
        # Get the full information once for display in the UI
        try:
            # Use fields parameter to get a more consistent format, including SIGNAL explicitly
            full_networks = subprocess.getoutput("nmcli -f IN-USE,BSSID,SSID,MODE,CHAN,RATE,SIGNAL,BARS,SECURITY dev wifi list").split("\n")[1:]  # Skip header row
            
            # Add networks and keep track of the previously selected one
            previously_selected_row = None
            
            for network in full_networks:
                row = WiFiNetworkRow(network)
                self.wifi_listbox.add(row)
                
                # If this was the previously selected network, remember it
                if selected_ssid and row.get_ssid() == selected_ssid:
                    previously_selected_row = row
            
            self.wifi_listbox.show_all()
            
            # Reselect the previously selected network if it still exists
            if previously_selected_row:
                self.wifi_listbox.select_row(previously_selected_row)
            
            # Update the Wi-Fi status switch based on actual Wi-Fi state
            try:
                wifi_status = subprocess.getoutput("nmcli radio wifi").strip()
                self.wifi_status_switch.set_active(wifi_status.lower() == "enabled")
            except Exception as e:
                print(f"Error getting Wi-Fi status: {e}")
        except Exception as e:
            print(f"Error updating WiFi list: {e}")
        
        # Reset the flag
        self._is_refreshing = False
        
        return False  # Stop the timeout

    def on_wifi_switch_toggled(self, switch, gparam):
        active = switch.get_active()
        print(f"User toggled Wi-Fi switch to {'ON' if active else 'OFF'}")
        
        if active:
            try:
                subprocess.run(["nmcli", "radio", "wifi", "on"], check=True)
                self.refresh_wifi(None)
            except subprocess.CalledProcessError as e:
                print(f"Failed to enable Wi-Fi: {e}")
        else:
            try:
                subprocess.run(["nmcli", "radio", "wifi", "off"], check=True)
                self.wifi_listbox.foreach(lambda row: self.wifi_listbox.remove(row))
            except subprocess.CalledProcessError as e:
                print(f"Failed to disable Wi-Fi: {e}")
    
    def forget_wifi(self, button):
        selected_row = self.wifi_listbox.get_selected_row()
        if not selected_row:
            return
        
        ssid = selected_row.get_ssid()
        
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            destroy_with_parent=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Forget Wi-Fi Network"
        )
        dialog.format_secondary_text(f"Are you sure you want to forget the network '{ssid}'?")
        response = dialog.run()
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
            
        try:
            # With our new approach, we can delete the connection directly by its name (SSID)
            subprocess.run(["nmcli", "connection", "delete", ssid], check=True)
            print(f"Successfully forgot network '{ssid}'")
            self.refresh_wifi(None)
        except subprocess.CalledProcessError as e:
            print(f"Failed to forget network: {e}")

    def disconnect_wifi(self, button):
        try:
            # First approach: Try to find WiFi device that's connected
            connected_wifi_device = subprocess.getoutput("nmcli -t -f DEVICE,STATE dev | grep wifi.*:connected")
            print(f"Debug - connected wifi device: {connected_wifi_device}")
            
            if connected_wifi_device:
                # Extract device name
                wifi_device = connected_wifi_device.split(':')[0]
                print(f"Debug - Found connected wifi device: {wifi_device}")
                
                # Get connection name for this device
                device_connection = subprocess.getoutput(f"nmcli -t -f NAME,DEVICE con show --active | grep {wifi_device}")
                print(f"Debug - device connection: {device_connection}")
                
                if device_connection and ':' in device_connection:
                    connection_name = device_connection.split(':')[0]
                    print(f"Debug - Found connection name: {connection_name}")
                    
                    # Disconnect this connection
                    print(f"Disconnecting from WiFi connection: {connection_name}")
                    subprocess.run(["nmcli", "con", "down", connection_name], check=True)
                    print(f"Disconnected from WiFi network: {connection_name}")
                    self.refresh_wifi(None)
                    return
            
            # Second approach: Try checking all active WiFi connections
            active_connections = subprocess.getoutput("nmcli -t -f NAME,TYPE con show --active").split('\n')
            print(f"Debug - all active connections: {active_connections}")
            
            for conn in active_connections:
                if ':' in conn and ('wifi' in conn.lower() or '802-11-wireless' in conn.lower()):
                    connection_name = conn.split(':')[0]
                    print(f"Debug - Found WiFi connection from active list: {connection_name}")
                    subprocess.run(["nmcli", "con", "down", connection_name], check=True)
                    print(f"Disconnected from WiFi network: {connection_name}")
                    self.refresh_wifi(None)
                    return
            
            # If we got here, no WiFi connection was found
            print("No active Wi-Fi connection found")
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to disconnect: {e}")
        except Exception as e:
            print(f"General error during disconnect: {e}")

    def update_network_speed(self):
        """Measure and update the network speed."""
        try:
            # Get network interfaces
            interfaces = subprocess.getoutput("nmcli -t -f DEVICE,TYPE device | grep wifi").split("\n")
            wifi_interfaces = [line.split(":")[0] for line in interfaces if ":" in line]
            
            if not wifi_interfaces:
                self.upload_label.set_text("0 KB/s")
                self.download_label.set_text("0 KB/s")
                return True
                
            # Use the first Wi-Fi interface for simplicity
            interface = wifi_interfaces[0]
            
            # Get current transmit and receive bytes
            rx_bytes = int(subprocess.getoutput(f"cat /sys/class/net/{interface}/statistics/rx_bytes"))
            tx_bytes = int(subprocess.getoutput(f"cat /sys/class/net/{interface}/statistics/tx_bytes"))
            
            # Store current values
            if not hasattr(self, 'prev_rx_bytes'):
                self.prev_rx_bytes = rx_bytes
                self.prev_tx_bytes = tx_bytes
                return True
                
            # Calculate speed
            rx_speed = rx_bytes - self.prev_rx_bytes
            tx_speed = tx_bytes - self.prev_tx_bytes
            
            # Update previous values
            self.prev_rx_bytes = rx_bytes
            self.prev_tx_bytes = tx_bytes
            
            # Format for display
            def format_speed(bytes_per_sec):
                if bytes_per_sec > 1048576:  # 1 MB
                    return f"{bytes_per_sec/1048576:.1f} MB/s"
                elif bytes_per_sec > 1024:  # 1 KB
                    return f"{bytes_per_sec/1024:.1f} KB/s"
                else:
                    return f"{bytes_per_sec} B/s"
                    
            self.download_label.set_text(format_speed(rx_speed))
            self.upload_label.set_text(format_speed(tx_speed))
        except Exception as e:
            print(f"Error updating network speed: {e}")
            
        return True  # Continue the timer

    def get_current_volume(self):
        output = subprocess.getoutput("pactl get-sink-volume @DEFAULT_SINK@")
        volume = int(output.split("/")[1].strip().strip("%"))
        return volume

    def set_volume(self, scale):
        value = int(scale.get_value())
        self.set_volume_level(value)

    def get_current_brightness(self):
        if not shutil.which("brightnessctl"):
            logging.error("brightnessctl is not installed.")
            return 50  

        output = subprocess.getoutput("brightnessctl get")
        max_brightness = subprocess.getoutput("brightnessctl max")

        try:
            return int((int(output) / int(max_brightness)) * 100)
        except ValueError:
            logging.error(f"Unexpected output from brightnessctl: {output}, {max_brightness}")
            return 50  

    def set_brightness(self, scale):
        value = int(scale.get_value())
        self.set_brightness_level(value)

    def is_muted(self, audio_type="sink"):
        """
        Check if the audio sink or source is currently muted.
        :param audio_type: "sink" for speaker, "source" for microphone
        :return: True if muted, False otherwise
        """
        try:
            if audio_type == "sink":
                output = subprocess.getoutput("pactl get-sink-mute @DEFAULT_SINK@")
            elif audio_type == "source":
                output = subprocess.getoutput("pactl get-source-mute @DEFAULT_SOURCE@")
            else:
                raise ValueError("Invalid audio_type. Use 'sink' or 'source'.")

            return "yes" in output.lower()
        except Exception as e:
            print(f"Error checking mute state: {e}")
            return False

    def update_button_labels(self):
        """
        Update the labels of the mute/unmute buttons based on the current mute state.
        """
        try:

            if self.is_muted("sink"):
                self.volume_button.set_label("Unmute Speaker")
            else:
                self.volume_button.set_label("Mute Speaker")

            if self.is_muted("source"):
                self.volume_mic.set_label("Unmute Mic")
            else:
                self.volume_mic.set_label("Mute Mic")
        except Exception as e:
            print(f"Error updating button labels: {e}")

    def mute(self, button):
        if shutil.which("pactl"):
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
            self.update_button_labels()
        else:
            self.show_error_dialog("pactl is missing. please check our github page to see all dependencies and install them")

    def micmute(self, button):
        if shutil.which("pactl"):
            subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"])
            self.update_button_labels()
        else:
            self.show_error_dialog("pactl is missing. please check our github page to see all dependencies and install them")

    def on_network_row_activated(self, listbox, row):
        """Handle activation of a network row by connecting to it."""
        if row:
            self.connect_wifi(None)

    def show_wifi_password_dialog(self, ssid, security_type="WPA"):
        """Display a polished dialog for entering WiFi password."""
        dialog = Gtk.Dialog(
            title=f"Connect to {ssid}",
            transient_for=self,
            modal=True,
            destroy_with_parent=True
        )
        
        # Make the dialog look nice
        dialog.set_default_size(400, -1)
        dialog.set_border_width(10)
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        
        # Add header with network icon and name
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_margin_bottom(15)
        
        # Network icon based on signal strength
        network_icon = Gtk.Image.new_from_icon_name("network-wireless-signal-excellent-symbolic", Gtk.IconSize.DIALOG)
        header_box.pack_start(network_icon, False, False, 0)
        
        # Network name with security info
        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        network_name = Gtk.Label()
        network_name.set_markup(f"<b>{ssid}</b>")
        network_name.set_halign(Gtk.Align.START)
        name_box.pack_start(network_name, False, False, 0)
        
        # Security type
        security_label = Gtk.Label(label=f"Security: {security_type}")
        security_label.set_halign(Gtk.Align.START)
        security_label.get_style_context().add_class("dim-label")
        name_box.pack_start(security_label, False, False, 0)
        
        header_box.pack_start(name_box, True, True, 0)
        content_area.pack_start(header_box, False, False, 0)
        
        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_area.pack_start(separator, False, False, 0)
        
        # Add message
        message = Gtk.Label()
        message.set_markup("<span size='medium'>This network is password-protected. Please enter the password to connect.</span>")
        message.set_line_wrap(True)
        message.set_max_width_chars(50)
        message.set_margin_top(10)
        message.set_margin_bottom(10)
        content_area.pack_start(message, False, False, 0)
        
        # Add password entry
        password_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        password_box.set_margin_top(5)
        password_box.set_margin_bottom(15)
        
        password_label = Gtk.Label(label="Password:")
        password_box.pack_start(password_label, False, False, 0)
        
        password_entry = Gtk.Entry()
        password_entry.set_visibility(False)  
        password_entry.set_width_chars(25)
        password_entry.set_placeholder_text("Enter network password")
        
        # Add show/hide password button
        password_entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "view-conceal-symbolic")
        password_entry.connect("icon-press", self._on_password_dialog_icon_pressed)
        
        password_box.pack_start(password_entry, True, True, 0)
        content_area.pack_start(password_box, False, False, 0)
        
        # Remember checkbox
        remember_check = Gtk.CheckButton(label="Remember this network")
        remember_check.set_active(True)
        content_area.pack_start(remember_check, False, False, 0)
        
        # Add custom styled buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(10)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda w: dialog.response(Gtk.ResponseType.CANCEL))
        button_box.pack_start(cancel_button, False, False, 0)
        
        connect_button = Gtk.Button(label="Connect")
        connect_button.get_style_context().add_class("suggested-action")
        connect_button.connect("clicked", lambda w: dialog.response(Gtk.ResponseType.OK))
        button_box.pack_start(connect_button, False, False, 0)
        content_area.pack_start(button_box, False, False, 0)
        
        # Set the default button (respond to Enter key)
        connect_button.set_can_default(True)
        dialog.set_default(connect_button)
        
        # Set focus to password entry
        password_entry.grab_focus()
        
        # Make sure the dialog is fully displayed
        dialog.show_all()
        
        # Run the dialog and get the response
        response = dialog.run()
        
        # Get entered password if dialog was not canceled
        password = password_entry.get_text() if response == Gtk.ResponseType.OK else None
        remember = remember_check.get_active() if response == Gtk.ResponseType.OK else False
        
        # Destroy the dialog
        dialog.destroy()
        
        return password, remember, response == Gtk.ResponseType.OK
    
    def _on_password_dialog_icon_pressed(self, entry, icon_pos, event):
        """Toggle password visibility in the password dialog."""
        current_visibility = entry.get_visibility()
        entry.set_visibility(not current_visibility)
        
        if current_visibility:
            entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "view-conceal-symbolic")
        else:
            entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "view-reveal-symbolic")

    def connect_wifi(self, button):
        # Prevent multiple connection attempts at the same time
        if getattr(self, '_is_connecting', False):
            return
            
        selected_row = self.wifi_listbox.get_selected_row()
        if not selected_row:
            return
        
        ssid = selected_row.get_ssid()
        is_secured = selected_row.is_secured()
        
        # Set connecting flag
        self._is_connecting = True
        
        # Get password if needed
        password = None
        remember = True
        success = True
        
        if is_secured:
            # Check if the network already has a saved connection profile
            try:
                check_saved = subprocess.run(
                    ["nmcli", "-t", "-f", "name", "connection", "show"],
                    capture_output=True,
                    text=True
                )
                saved_connections = check_saved.stdout.strip().split('\n')
                has_saved_profile = ssid in saved_connections
            except Exception as e:
                print(f"Error checking saved connections: {e}")
                has_saved_profile = False
            
            # Only show password dialog if the network doesn't have a saved profile
            if not has_saved_profile:
                security_type = selected_row.get_security() or "WPA"
                password, remember, success = self.show_wifi_password_dialog(ssid, security_type)
                
                # If user canceled, abort connection
                if not success:
                    GLib.idle_add(self.hide_connecting_overlay)
                    GLib.idle_add(lambda: setattr(self, '_is_connecting', False))
                    return
        
        # Show connecting overlay
        self.show_connecting_overlay(ssid)
        
        def connect_thread():
            try:
                if is_secured:
                    # Check if we have a saved profile
                    has_saved_profile = False
                    try:
                        check_saved = subprocess.run(
                            ["nmcli", "-t", "-f", "name", "connection", "show"],
                            capture_output=True,
                            text=True
                        )
                        saved_connections = check_saved.stdout.strip().split('\n')
                        has_saved_profile = ssid in saved_connections
                    except Exception as e:
                        print(f"Error checking saved connections in thread: {e}")
                    
                    if has_saved_profile:
                        # If we have a saved profile, just activate it
                        print(f"Connecting to saved network: {ssid}")
                        up_command = ["nmcli", "con", "up", ssid]
                        up_result = subprocess.run(
                            up_command,
                            capture_output=True,
                            text=True
                        )
                        
                        if up_result.returncode == 0:
                            print(f"Connection activated: {up_result.stdout}")
                            # Wait longer to make sure the network changes
                            time.sleep(2)
                            GLib.idle_add(lambda: print(f"Successfully connected to {ssid}"))
                        else:
                            print(f"Error activating connection: {up_result.stderr}")
                            error_msg = up_result.stderr if up_result.stderr else f"Error code: {up_result.returncode}"
                            GLib.idle_add(lambda: print(f"Failed to activate connection: {error_msg}"))
                    else:
                        # No saved profile and no password provided
                        if not password:
                            GLib.idle_add(self.hide_connecting_overlay)
                            GLib.idle_add(lambda: print("Password required for secured network"))
                            GLib.idle_add(lambda: setattr(self, '_is_connecting', False))
                            return
                            
                        print(f"Connecting to secured network: {ssid}")
                        
                        # New approach: First create the connection
                        add_command = [
                            "nmcli", "con", "add", 
                            "type", "wifi", 
                            "con-name", ssid, 
                            "ssid", ssid, 
                            "wifi-sec.key-mgmt", "wpa-psk", 
                            "wifi-sec.psk", password
                        ]
                        
                        # If user unchecked "Remember this network"
                        if not remember:
                            add_command.extend(["connection.autoconnect", "no"])
                        
                        print(f"Running command: {' '.join(add_command)}")
                        
                        try:
                            # Create the connection profile
                            add_result = subprocess.run(
                                add_command,
                                capture_output=True,
                                text=True
                            )
                            
                            if add_result.returncode == 0:
                                print(f"Connection profile created: {add_result.stdout}")
                                
                                # Now activate the connection
                                up_command = ["nmcli", "con", "up", ssid]
                                up_result = subprocess.run(
                                    up_command,
                                    capture_output=True,
                                    text=True
                                )
                                
                                if up_result.returncode == 0:
                                    print(f"Connection activated: {up_result.stdout}")
                                    # Wait longer to make sure the network changes
                                    time.sleep(2)
                                    GLib.idle_add(lambda: print(f"Successfully connected to {ssid}"))
                                else:
                                    print(f"Error activating connection: {up_result.stderr}")
                                    error_msg = up_result.stderr if up_result.stderr else f"Error code: {up_result.returncode}"
                                    GLib.idle_add(lambda: print(f"Failed to activate connection: {error_msg}"))
                            else:
                                print(f"Error creating connection: {add_result.stderr}")
                                error_msg = add_result.stderr if add_result.stderr else f"Error code: {add_result.returncode}"
                                GLib.idle_add(lambda: print(f"Failed to create connection: {error_msg}"))
                                
                        except Exception as e:
                            print(f"Exception connecting to network: {e}")
                            GLib.idle_add(lambda: print(f"Error connecting: {str(e)}"))
                else:
                    print(f"Connecting to open network: {ssid}")
                    try:
                        # For open networks, create connection without security
                        add_command = [
                            "nmcli", "con", "add", 
                            "type", "wifi", 
                            "con-name", ssid, 
                            "ssid", ssid
                        ]
                        
                        # Create the connection profile for open network
                        add_result = subprocess.run(
                            add_command,
                            capture_output=True,
                            text=True
                        )
                        
                        if add_result.returncode == 0:
                            print(f"Open connection profile created: {add_result.stdout}")
                            
                            # Activate the connection
                            up_result = subprocess.run(
                                ["nmcli", "con", "up", ssid],
                                capture_output=True,
                                text=True
                            )
                            
                            if up_result.returncode == 0:
                                print(f"Open connection activated: {up_result.stdout}")
                                # Wait longer to make sure the network changes
                                time.sleep(2)
                                GLib.idle_add(lambda: print(f"Successfully connected to {ssid}"))
                            else:
                                print(f"Error activating open connection: {up_result.stderr}")
                                error_msg = up_result.stderr if up_result.stderr else f"Error code: {up_result.returncode}"
                                GLib.idle_add(lambda: print(f"Failed to activate connection: {error_msg}"))
                        else:
                            print(f"Error creating open connection: {add_result.stderr}")
                            error_msg = add_result.stderr if add_result.stderr else f"Error code: {add_result.returncode}"
                            GLib.idle_add(lambda: print(f"Failed to create connection: {error_msg}"))
                    except Exception as e:
                        print(f"Exception connecting to open network: {e}")
                        GLib.idle_add(lambda: print(f"Error connecting: {str(e)}"))
            finally:
                # Always update the network list after attempting connection
                # Wait a bit longer before refreshing to give the connection time to establish
                time.sleep(1)
                
                # Reset connecting flag and hide overlay
                GLib.idle_add(lambda: setattr(self, '_is_connecting', False))
                GLib.idle_add(self.hide_connecting_overlay)
                
                # Finally refresh the network list
                GLib.idle_add(self.refresh_wifi, None)
        
        thread = threading.Thread(target=connect_thread)
        thread.daemon = True
        thread.start()

    def show_connecting_overlay(self, ssid):
        """Show overlay with spinner during connection."""
        # First, make sure we don't already have an overlay
        if hasattr(self, 'overlay') and self.overlay:
            self.hide_connecting_overlay()
        
        # Store original parent of main_container
        self.original_parent = self.main_container.get_parent()
        if self.original_parent:
            self.original_parent.remove(self.main_container)
        
        # Create our overlay
        self.overlay = Gtk.Overlay()
        self.overlay.add(self.main_container)
        
        # Create a semi-transparent background
        bg = Gtk.EventBox()
        bg_style_provider = Gtk.CssProvider()
        bg_style_provider.load_from_data(b"""
            eventbox {
                background-color: rgba(0, 0, 0, 0.5);
            }
        """)
        bg_context = bg.get_style_context()
        bg_context.add_provider(bg_style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # Create a box for the spinner and message
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        
        # Add spinner
        spinner = Gtk.Spinner()
        spinner.set_size_request(50, 50)
        spinner.start()
        box.pack_start(spinner, False, False, 0)
        
        # Add message
        message = Gtk.Label()
        message.set_markup(f"<span color='white' size='large'>Connecting to <b>{ssid}</b>...</span>")
        box.pack_start(message, False, False, 0)
        
        bg.add(box)
        self.overlay.add_overlay(bg)
        
        # Add the overlay to our window
        self.add(self.overlay)
        self.show_all()
    
    def hide_connecting_overlay(self):
        """Hide the connection overlay and restore original layout."""
        if hasattr(self, 'overlay') and self.overlay:
            # Remove main_container from overlay
            self.overlay.remove(self.main_container)
            
            # Remove overlay from window
            self.remove(self.overlay)
            
            # Restore main_container to its original parent
            if hasattr(self, 'original_parent') and self.original_parent:
                self.original_parent.add(self.main_container)
            else:
                self.add(self.main_container)
            
            # Clean up
            self.overlay = None
            self.show_all()
        return False

    def on_tab_switch(self, notebook, tab, page_num):
        """Check dependencies when switching to a tab."""
        tab_label = self.get_tab_name_from_label(tab)

        if tab_label == "Bluetooth":
            if not shutil.which("bluetoothctl"):
                self.show_error_dialog("bluetoothctl is missing. Please check our GitHub page to see all dependencies and install them.")
            else:
                # Update the switch to reflect the actual Bluetooth state only if not initialized
                if not self._tabs_initialized.get("Bluetooth", False):
                    self.update_bluetooth_switch_state()
                    self._tabs_initialized["Bluetooth"] = True
                
                # Only initialize Bluetooth when the tab is selected and if Bluetooth is on
                if not self._bt_initialized and self.bt_status_switch.get_active():
                    self._bt_initialized = True
                    self.refresh_bluetooth(None)

        elif tab_label == "Wi-Fi":
            if not shutil.which("nmcli"):
                self.show_error_dialog("NetworkManager (nmcli) is missing. Please check our GitHub page to see all dependencies and install them.")
            elif not self._tabs_initialized.get("Wi-Fi", False):
                self._tabs_initialized["Wi-Fi"] = True
                self.refresh_wifi(None)

        elif tab_label == "Brightness" and not shutil.which("brightnessctl"):
            self.show_error_dialog("brightnessctl is missing. Please check our GitHub page to see all dependencies and install them.")

        elif tab_label in ["Volume", "Application Volume"] and not shutil.which("pactl"):
            self.show_error_dialog("pactl is missing. Please check our GitHub page to see all dependencies and install them.")

        elif tab_label in ["Battery"] and not shutil.which("powerprofilesctl"):
            self.show_error_dialog("powerprofilesctl is missing. Please check our GitHub page to see all dependencies and install them.")

        if tab_label == "Wi-Fi":
            self.refresh_wifi(None)
    
    def on_tab_switched(self, notebook, page, page_num):
        """Handle tab switching to refresh data when a tab is selected."""
        tab_page = notebook.get_nth_page(page_num)
        tab_label = self.get_tab_name_from_label(tab_page)

        # Initialize the tab if it hasn't been initialized yet
        if tab_label == "Wi-Fi" and not self._tabs_initialized.get("Wi-Fi", False):
            self.initialize_wifi_tab()
        elif tab_label == "Bluetooth" and not self._tabs_initialized.get("Bluetooth", False):
            self.initialize_bluetooth_tab()
        elif tab_label == "Volume" and not self._tabs_initialized.get("Volume", False):
            self.initialize_volume_tab()
        elif tab_label == "Battery" and not self._tabs_initialized.get("Battery", False):
            self.initialize_battery_tab()
        elif tab_label == "Display" and not self._tabs_initialized.get("Display", False):
            self.initialize_display_tab()

    def refresh_app_volume(self, button=None):
        """Refresh the list of applications playing audio and create sliders for them."""

        if not shutil.which("pactl"):
            self.show_error_dialog("pactl is missing. Please check our GitHub page to see all dependencies and install them.")
            return  

        self.app_volume_listbox.foreach(lambda row: self.app_volume_listbox.remove(row))

        try:
            output = subprocess.getoutput("pactl list sink-inputs")
            sink_inputs = output.split("Sink Input #")[1:]  

            for sink_input in sink_inputs:
                lines = sink_input.split("\n")
                sink_input_id = lines[0].strip()  

                app_name = "Unknown Application"
                media_name = "Unknown Media"
                volume_percent = 50
                icon_name = ""  # Default empty

                for line in lines:
                    if "application.name" in line:
                        app_name = line.split("=")[1].strip().strip('"')
                    if "application.icon_name" in line:
                        icon_name = line.split("=")[1].strip().strip('"')
                    if "media.name" in line:
                        media_name = line.split("=")[1].strip().strip('"')
                    if "Volume:" in line:
                        volume_parts = line.split("/")
                        if len(volume_parts) >= 2:
                            volume_percent = int(volume_parts[1].strip().strip("%"))

                # Get the appropriate icon name
                final_icon_name = self.get_app_icon_name(app_name, icon_name)

                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                box.set_margin_start(10)
                box.set_margin_end(10)
                box.set_margin_top(5)
                box.set_margin_bottom(5)

                # Add application icon
                app_icon = Gtk.Image.new_from_icon_name(final_icon_name, Gtk.IconSize.LARGE_TOOLBAR)
                box.pack_start(app_icon, False, False, 0)

                label = Gtk.Label(label=f"{app_name} - {media_name}")
                label.set_xalign(0)
                box.pack_start(label, True, True, 0)

                scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
                scale.set_hexpand(True)
                scale.set_value(volume_percent)  
                scale.connect("value-changed", self.set_app_volume, app_name, media_name)  
                box.pack_start(scale, True, True, 0)

                row.add(box)
                self.app_volume_listbox.add(row)

            self.app_volume_listbox.show_all()

        except Exception as e:
            print(f"Error refreshing application volume list: {e}")

    def get_app_volume(self, sink_input_id):
        """Get the current volume of an application."""
        try:
            output = subprocess.getoutput(f"pactl get-sink-input-volume {sink_input_id}")
            if "No such entity" in output or "No valid command specified" in output:
                raise ValueError(f"Sink input {sink_input_id} no longer exists or is invalid.")

            volume_parts = output.split("/")
            if len(volume_parts) < 2:  
                raise ValueError(f"Unexpected output format for sink input {sink_input_id}: {output}")

            volume = int(volume_parts[1].strip().strip("%"))
            return volume
        except ValueError as e:

            raise e
        except Exception as e:
            print(f"Error getting volume for sink input {sink_input_id}: {e}")
            return 50  

    def set_app_volume(self, scale, app_name, media_name):
        """Set the volume of an application by its name and media name."""
        try:
            new_volume = int(scale.get_value())

            output = subprocess.getoutput("pactl list sink-inputs")
            sink_inputs = output.split("Sink Input #")[1:]  

            for sink_input in sink_inputs:
                lines = sink_input.split("\n")
                sink_input_id = lines[0].strip()  

                current_app_name = None
                current_media_name = None
                for line in lines:
                    if "application.name" in line:
                        current_app_name = line.split("=")[1].strip().strip('"')
                    if "media.name" in line:
                        current_media_name = line.split("=")[1].strip().strip('"')

                if current_app_name == app_name and current_media_name == media_name:

                    result = subprocess.run(
                        ["pactl", "set-sink-input-volume", sink_input_id, f"{new_volume}%"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        print(f"Failed to set volume for sink input {sink_input_id}: {result.stderr}")
                    else:
                        print(f"Volume set to {new_volume}% for {app_name} - {media_name} (sink input {sink_input_id})")
                    return  

            print(f"Failed to find sink input for application: {app_name} - {media_name}")

        except Exception as e:
            print(f"Error setting volume for {app_name} - {media_name}: {e}")

    def refresh_app_volume_realtime(self):
        """Refresh the list of applications playing audio in real-time."""
        try:

            output = subprocess.getoutput("pactl list sink-inputs")
            sink_inputs = output.split("Sink Input #")[1:]  

            current_sink_inputs = []
            for sink_input in sink_inputs:
                lines = sink_input.split("\n")
                sink_input_id = lines[0].strip()  
                current_sink_inputs.append(sink_input_id)

            if hasattr(self, "previous_sink_inputs") and self.previous_sink_inputs == current_sink_inputs:
                return True  

            self.previous_sink_inputs = current_sink_inputs

            self.refresh_app_volume(None)

        except Exception as e:
            print(f"Error refreshing application volume list in real-time: {e}")

        return True

    def move_tab_up(self, button, tab_name):
        """Move a tab up in the order (lower position number)"""
        tab_widget = self.tabs[tab_name]
        current_position = self.notebook.page_num(tab_widget)

        if current_position <= 0 or current_position == -1:
            return

        tab_label = self.notebook.get_tab_label(tab_widget)
        current_active_tab = self.notebook.get_current_page()

        self.notebook.remove_page(current_position)
        new_position = current_position - 1
        self.notebook.insert_page(tab_widget, tab_label, new_position)

        self.notebook.set_current_page(current_active_tab if current_active_tab != current_position else new_position)

        for name, pos in self.original_tab_positions.items():
            if pos == new_position:
                self.original_tab_positions[name] = current_position
        self.original_tab_positions[tab_name] = new_position

        self.save_settings()
        self.populate_settings_tab()

        self.settings_box.show_all()
        self.queue_draw()

    def move_tab_down(self, button, tab_name):
        """Move a tab down in the order (higher position number)"""
        tab_widget = self.tabs[tab_name]
        current_position = self.notebook.page_num(tab_widget)
        last_position = self.notebook.get_n_pages() - 1

        if current_position == last_position or current_position == -1:
            return

        tab_label = self.notebook.get_tab_label(tab_widget)
        current_active_tab = self.notebook.get_current_page()

        self.notebook.remove_page(current_position)
        new_position = current_position + 1
        self.notebook.insert_page(tab_widget, tab_label, new_position)

        self.notebook.set_current_page(current_active_tab if current_active_tab != current_position else new_position)

        for name, pos in self.original_tab_positions.items():
            if pos == new_position:
                self.original_tab_positions[name] = current_position
        self.original_tab_positions[tab_name] = new_position

        self.save_settings()
        self.populate_settings_tab()

        self.settings_box.show_all()
        self.queue_draw()


    def apply_saved_tab_order(self):
        """Apply the saved tab order from settings"""
        # Create a list of tabs sorted by their saved positions
        if not self.original_tab_positions:
            return
            
        # Get all currently visible tabs
        visible_tabs = []
        for i in range(self.notebook.get_n_pages()):
            page = self.notebook.get_nth_page(i)
            label_text = self.get_tab_name_from_label(page)
            visible_tabs.append((label_text, page))
            
        # Remove all tabs
        while self.notebook.get_n_pages() > 0:
            self.notebook.remove_page(0)
            
        # Sort tabs by saved positions
        visible_tabs.sort(key=lambda x: self.original_tab_positions.get(x[0], 999))
        
        # Add tabs back in the sorted order
        for label_text, page in visible_tabs:
            self.notebook.append_page(page, self.create_tab_label_with_icon(label_text))
            
        self.notebook.show_all()
        
        # Make sure the notebook selects the first page
        if self.notebook.get_n_pages() > 0:
            self.notebook.set_current_page(0)

    def get_app_icon_name(self, app_name, provided_icon_name):
        """Map application names to appropriate icon names if needed"""
        # First check if the provided icon name exists
        if provided_icon_name and provided_icon_name != "":
            return provided_icon_name
            
        # Map common application names to icons
        icon_map = {
            "Firefox": "firefox",
            "firefox": "firefox",
            "Brave": "brave-browser",
            "brave": "brave-browser",
            "Chromium": "chromium",
            "chromium": "chromium",
            "Google Chrome": "google-chrome",
            "chrome": "google-chrome",
            "Spotify": "spotify",
            "spotify": "spotify",
            "VLC": "vlc",
            "vlc": "vlc",
            "mpv": "mpv",
            "MPV": "mpv",
            "Discord": "discord",
            "discord": "discord",
            "Telegram": "telegram",
            "telegram": "telegram",
            "Zoom": "zoom",
            "zoom": "zoom"
        }
        
        # Check if the app name is in our mapping
        for key in icon_map:
            if key in app_name:
                return icon_map[key]
        
        # Return a generic audio icon as fallback
        return "audio-x-generic-symbolic"

    def toggle_settings_panel(self, button):
        """Toggle the visibility of the settings panel"""
        if hasattr(self, 'settings_window') and self.settings_window.get_visible():
            self.settings_window.hide()
        else:
            self.show_settings_panel()
    
    def show_settings_panel(self):
        """Show the settings panel in a separate window"""
        if not hasattr(self, 'settings_window') or self.settings_window is None:
            # Create settings window
            self.settings_window = Gtk.Window(title="Settings")
            self.settings_window.set_transient_for(self)
            self.settings_window.set_modal(True)
            self.settings_window.set_default_size(400, 500)
            self.settings_window.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
            
            # Create a scrolled window for content
            scrolled_window = Gtk.ScrolledWindow()
            scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            
            # Create settings container
            settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            settings_box.set_margin_top(20)
            settings_box.set_margin_bottom(20)
            settings_box.set_margin_start(20)
            settings_box.set_margin_end(20)
            settings_box.set_hexpand(True)
            settings_box.set_vexpand(True)
            
            # Add settings box to scrolled window
            scrolled_window.add(settings_box)
            
            # Add scrolled window to the settings window
            self.settings_window.add(scrolled_window)
            
            # Store the settings box for later use
            self.settings_box = settings_box
            
            # Populate settings content
            self.populate_settings_tab()
            
            # Connect the close event
            self.settings_window.connect("delete-event", lambda w, e: w.hide() or True)
        
        self.settings_window.show_all()

    def create_tab_label_with_icon(self, tab_name):
        """Create a tab label with an icon and text"""
        # Map tab names to appropriate icons
        tab_icons = {
            "Wi-Fi": "network-wireless-symbolic",
            "Bluetooth": "bluetooth-symbolic",
            "Volume": "audio-volume-high-symbolic",
            "Application Volume": "audio-speakers-symbolic",
            "Display": "video-display-symbolic",
            "Battery": "battery-good-symbolic",
            "Brightness": "display-brightness-symbolic"
        }
        
        # Create a box for the tab label with icon and text
        tab_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Add icon
        icon_name = tab_icons.get(tab_name, "applications-system-symbolic")  # Default icon if not found
        tab_icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
        tab_label_box.pack_start(tab_icon, False, False, 0)
        
        # Add text label
        label = Gtk.Label(label=tab_name)
        tab_label_box.pack_start(label, False, False, 0)
        
        tab_label_box.show_all()
        return tab_label_box

    def get_tab_name_from_label(self, tab):
        """Get the tab name from a tab label which could be a box with icon and text"""
        tab_label = self.notebook.get_tab_label(tab)
        
        # If the tab label is a box (our custom label with icon)
        if isinstance(tab_label, Gtk.Box):
            # Get the label from the second child (first is icon, second is label)
            for child in tab_label.get_children():
                if isinstance(child, Gtk.Label):
                    return child.get_text()
            
        # Fallback to the standard method for text-only labels
        return self.notebook.get_tab_label_text(tab)

    def get_sink_icon_name(self, sink_name, description):
        """Determine the appropriate icon for an audio output device."""
        sink_name_lower = sink_name.lower()
        description_lower = description.lower() if description else ""
        
        # Check for headphones
        if any(term in sink_name_lower or term in description_lower for term in ["headphone", "headset", "earphone", "earbud"]):
            return "audio-headphones-symbolic"
        
        # Check for Bluetooth devices
        if "bluetooth" in sink_name_lower or "bluez" in sink_name_lower or "bt" in description_lower:
            return "bluetooth-symbolic"
            
        # Check for HDMI/DisplayPort outputs (typically TV or monitors)
        if any(term in sink_name_lower or term in description_lower for term in ["hdmi", "displayport", "dp", "tv"]):
            return "video-display-symbolic"
            
        # Check for USB audio interfaces
        if "usb" in sink_name_lower or "usb" in description_lower:
            return "audio-card-symbolic"
            
        # Default to speaker
        return "audio-speakers-symbolic"
        
    def get_source_icon_name(self, source_name, description):
        """Determine the appropriate icon for an audio input device."""
        source_name_lower = source_name.lower()
        description_lower = description.lower() if description else ""
        
        # Check for webcam microphones
        if "cam" in source_name_lower or "cam" in description_lower or "webcam" in description_lower:
            return "camera-web-symbolic"
            
        # Check for headset microphones
        if any(term in source_name_lower or term in description_lower for term in ["headset", "headphone"]):
            return "audio-headset-symbolic"
            
        # Check for Bluetooth microphones
        if "bluetooth" in source_name_lower or "bluez" in source_name_lower or "bt" in description_lower:
            return "bluetooth-symbolic"
            
        # Check for USB microphones
        if "usb" in source_name_lower or "usb" in description_lower:
            return "audio-input-microphone-symbolic"
            
        # Default to generic microphone
        return "audio-input-microphone-symbolic"

class BluetoothDeviceRow(Gtk.ListBoxRow):
    def __init__(self, device_info):
        super().__init__()
        self.set_margin_top(5)
        self.set_margin_bottom(5)
        self.set_margin_start(10)
        self.set_margin_end(10)
        
        # Parse device information
        parts = device_info.split(" ", 2)
        self.mac_address = parts[1] if len(parts) > 1 else ""
        self.device_name = parts[2] if len(parts) > 2 else self.mac_address
        
        # Get connection status
        self.is_connected = False
        try:
            status_output = subprocess.getoutput(f"bluetoothctl info {self.mac_address}")
            self.is_connected = "Connected: yes" in status_output
            
            # Get device type if available
            if "Icon: " in status_output:
                icon_line = [line for line in status_output.split('\n') if "Icon: " in line]
                self.device_type = icon_line[0].split("Icon: ")[1].strip() if icon_line else "unknown"
            else:
                self.device_type = "unknown"
        except Exception as e:
            print(f"Error checking status for {self.mac_address}: {e}")
            self.device_type = "unknown"
        
        # Main container for the row
        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.add(container)
        
        # Device icon based on type
        icon_name = self.get_icon_name_for_device()
        device_icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        container.pack_start(device_icon, False, False, 0)
        
        # Left side with device name and type
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        name_label = Gtk.Label(label=self.device_name)
        name_label.set_halign(Gtk.Align.START)
        if self.is_connected:
            name_label.set_markup(f"<b>{self.device_name}</b>")
        name_box.pack_start(name_label, True, True, 0)
        
        if self.is_connected:
            connected_label = Gtk.Label(label=" (Connected)")
            connected_label.get_style_context().add_class("success-label")
            name_box.pack_start(connected_label, False, False, 0)
        
        left_box.pack_start(name_box, False, False, 0)
        
        # Device details box
        details_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        type_label = Gtk.Label(label=self.get_friendly_device_type())
        type_label.set_halign(Gtk.Align.START)
        type_label.get_style_context().add_class("dim-label")
        details_box.pack_start(type_label, False, False, 0)
        
        mac_label = Gtk.Label(label=self.mac_address)
        mac_label.set_halign(Gtk.Align.START)
        mac_label.get_style_context().add_class("dim-label")
        details_box.pack_start(mac_label, False, False, 10)
        
        left_box.pack_start(details_box, False, False, 0)
        
        container.pack_start(left_box, True, True, 0)
    
    def get_icon_name_for_device(self):
        """Return appropriate icon based on device type"""
        if self.device_type == "audio-headset" or self.device_type == "audio-headphones":
            return "audio-headset-symbolic"
        elif self.device_type == "audio-card":
            return "audio-speakers-symbolic"
        elif self.device_type == "input-keyboard":
            return "input-keyboard-symbolic"
        elif self.device_type == "input-mouse":
            return "input-mouse-symbolic"
        elif self.device_type == "input-gaming":
            return "input-gaming-symbolic"
        elif self.device_type == "phone":
            return "phone-symbolic"
        else:
            return "bluetooth-symbolic"
    
    def get_friendly_device_type(self):
        """Return user-friendly device type name"""
        type_names = {
            "audio-headset": "Headset",
            "audio-headphones": "Headphones",
            "audio-card": "Speaker",
            "input-keyboard": "Keyboard",
            "input-mouse": "Mouse",
            "input-gaming": "Game Controller",
            "phone": "Phone",
            "unknown": "Device"
        }
        return type_names.get(self.device_type, "Bluetooth Device")
    
    def get_mac_address(self):
        return self.mac_address
    
    def get_device_name(self):
        return self.device_name
    
    def get_is_connected(self):
        return self.is_connected

if __name__ == "__main__":
    args = parse_arguments()
    win = bettercontrol(args)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

# Hey there!
# 
# First of all, thank you for checking out this project. We truly hope
# that Better Control is useful to you and that it helps you in your
# work or personal projects. If you have any suggestions,
# issues, or want to collaborate, don't hesitate to reach out. - quantumvoid0 and FelipeFMA
#
# Stay awesome! - reach out to us on
# "quantumvoid._"         <-- discord
# "quantumvoid_"          <-- reddit
# "nekrooo_"              <-- discord
# "BasedPenguinsEnjoyer"  <-- reddit
#
