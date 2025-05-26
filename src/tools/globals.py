#!/usr/bin/env python3
import os
import subprocess
import gi

from tools.bluetooth import get_bluetooth_manager
from tools.wifi import wifi_supported
from utils.logger import LogLevel
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk # type: ignore

def get_current_session():  
    if "hyprland" in os.environ.get("XDG_CURRENT_DESKTOP", "").lower():
        return "Hyprland"
    elif "sway" in os.environ.get("XDG_CURRENT_DESKTOP", "").lower():
        return "sway"
    else:
        return False
    
    
# css for wifi_tab
def get_wifi_css():
    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(b"""
        .qr-button{
            background-color: transparent;
        }
        .qr_image_holder{
            border-radius: 12px;
        }
        .scan_label{
            font-size: 18px;
            font-weight: bold;
        }
        .ssid-box{
            background: @wm_button_unfocused_bg;
            border-radius: 6px;
            border-bottom-right-radius: 0px;
            border-bottom-left-radius: 0px;
            padding: 10px;
        }
        .dimmed-label{
            opacity: 0.5;
        }
        .secrity-box{
            background: @wm_button_unfocused_bg;
            border-radius: 6px;
            border-top-right-radius: 0px;
            border-top-left-radius: 0px;
            padding: 10px;
        }
        .ip-address-box, .dns-box, .gateway-box, .security-type-box, .public-ip-box {
            background: @wm_button_unfocused_bg;
            border-radius: 6px;
            border-bottom-right-radius: 0px;
            border-bottom-left-radius: 0px;
            padding: 10px;
        }
        .dns-box {
            border-top-right-radius: 0px;
            border-top-left-radius: 0px;
        }
        .gateway-box {
            border-top-right-radius: 0px;
            border-top-left-radius: 0px;
        }
        .public-ip-box {
            border-top-right-radius: 0px;
            border-top-left-radius: 0px;
            border-bottom-right-radius: 6px;
            border-bottom-left-radius: 6px;
        }
    """)
    
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_USER
    )

# check for battery suppoert 
def battery_supported() -> bool:
    try:
        result = subprocess.run(
            "upower -e", shell=True, capture_output=True, text=True
        )
        if result.returncode == 0 and "/battery_" in result.stdout:
            return True
    except Exception:
        return False
    
def check_hardware_support(self, visibility, logging):
    """Check if wifi, bluetooth, battery is supported or not"""
    
    bluetooth_manager = get_bluetooth_manager(logging)
    hardware_checks = {
        "Wi-Fi": {
            "check": wifi_supported,
            "log_message": "No Wi-Fi adapter found, skipping Wi-Fi tab",
        },
        "Battery": {
            "check": battery_supported,
            "log_message": "No battery found, skipping Battery tab",
        },
        "Bluetooth": {
            "check": bluetooth_manager.bluetooth_supported,
            "log_message": "No Bluetooth adapter found, skipping Bluetooth tab",
        },
    }
    for tab_name, check_info in hardware_checks.items():
        try:
            if not check_info["check"]():
                logging.log(LogLevel.Warn, check_info["log_message"])
                visibility[tab_name] = False
        except Exception as e:
            logging.log(LogLevel.Error, f"Error checking {tab_name} support: {e}")