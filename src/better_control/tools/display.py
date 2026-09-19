#!/usr/bin/env python3

import subprocess
from typing import Dict, List

from better_control.utils.logger import LogLevel, Logger
from better_control.tools.globals import get_current_session
from better_control.tools.hyprland import get_hyprland_displays, set_hyprland_transform

def get_brightness(logging: Logger) -> int:
    """Get the current brightness level

    Returns:
        int: current brightness percentage
    """
    try:
        output = subprocess.getoutput("brightnessctl g")
        max_brightness = int(subprocess.getoutput("brightnessctl m"))
        current_brightness = int(output)
        return int((current_brightness / max_brightness) * 100)
    except Exception as e:
        logging.log(LogLevel.Error, f"Failed getting brightness: {e}")
        return 0


def set_brightness(value: int, logging: Logger) -> None:
    """Set the brightness level

    Args:
        value (int): brightness percentage to set
    """
    try:
        subprocess.run(["brightnessctl", "s", f"{value}%"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        logging.log(LogLevel.Error, f"Failed setting brightness: {e}")


def get_displays(logging: Logger) -> List[str]:
    """Get list of connected displays

    Returns:
        List[str]: List of display names
    """
    try:
        output = subprocess.getoutput("xrandr --query")
        displays = []
        for line in output.split("\n"):
            if " connected" in line:
                displays.append(line.split()[0])
        return displays
    except Exception as e:
        logging.log(LogLevel.Error, f"Failed getting displays: {e}")
        return []


def get_display_info(display: str, logging: Logger) -> Dict[str, str]:
    """Get information about a specific display

    Args:
        display (str): Display name

    Returns:
        Dict[str, str]: Dictionary containing display information
    """
    try:
        session = get_current_session()
        if session == "Hyprland":
            displays = get_hyprland_displays()
            transform_map = {
                0: "normal",
                1: "right",
                2: "inverted",
                3: "left"
            }
            if display in displays:
                return {"rotation": transform_map.get(displays[display], "normal")}
        
        output = subprocess.run(f"xrandr --query --verbose | grep -A10 {display}", capture_output=True,text=True)
        lines = output.stdout.split("\n")
        
        for i, line in enumerate(lines):
            if display in line and " connected" in line:
                parts = line.split()
                for idx, part in enumerate(parts):
                    if part.startswith("(") and part.endswith(")"):
                        orientation = parts[idx + 1]
                        return {"rotation": orientation}
        
        # Return default if no rotation information found
        return {"rotation": "normal"}
    except Exception as e:
        logging.log(LogLevel.Error, f"Failed getting display info: {e}")
        return {"rotation": "normal"}

def rotate_display(display: str, desktop_env: str, orientation: str, logging: Logger) -> bool:
    """Change the orientation of the display
    Args:
        display: Display name
        orientation: Orientation ('normal', 'left', 'right', 'inverted')
        desktop_env: Desktop environment ('hyprland', 'sway', 'gnome')
        logging: Logger
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        session = get_current_session()
        
        if session == "Hyprland":
            return set_hyprland_transform(logging, display, orientation)

        elif desktop_env.lower() == "gnome":
            rotation_map = {
                "normal": "normal",
                "left": "left",
                "right": "right",
                "inverted": "inverted"
            }
            rotation = rotation_map.get(orientation.lower(), "normal")
            # Use gsettings to rotate display in gnome
            cmd = [
                "gsettings", 
                "set", 
                "org.gnome.settings-daemon.plugins.orientation", 
                "active", 
                "true"
            ]
            subprocess.run(cmd, check=True)

            # Apply the rotation to the specific monitor
            cmd = [
                "xrandr",
                "--output",
                display,
                "--rotate",
                rotation
            ]
            subprocess.run(cmd, check=True)
        return True
    except Exception as err:
        logging.log(LogLevel.Error, f"Failed to change display orientation for {display}: {err}")
        return False
    
