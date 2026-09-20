#!/usr/bin/env python3

from pathlib import Path
import subprocess

from better_control.logger import LogLevel, Logger

CONFIG_FILES = [
    Path.home() / ".config/hypr/hyprland.conf",
    Path.home() / ".config/hypr/autostart.conf"
        ]

def get_hyprland_startup_apps():
    """Retrieve apps started using exec-once in Hyprland"""
    startup_apps = {}
    for hypr_config in CONFIG_FILES:
        if hypr_config.exists():
            with open(hypr_config, "r") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                stripped = line.strip()
                if "exec-once" in stripped:
                    enabled = not stripped.startswith("#")
                    
                    cleared_line = stripped.lstrip("#").strip()
                    if "=" in cleared_line:
                        parts = cleared_line.split("=", 1)
                        command = parts[1].strip().strip('"')
                    else:
                        parts = cleared_line.split(None, 1)
                        if len(parts) > 1:
                            command = parts[1].strip().strip('"')
                        else:
                            continue
                    startup_apps[command] = {
                        "name": command,
                        "type": "hyprland",
                        "path": hypr_config,
                        "line_index": i,
                        "enabled": enabled
                    }
    return startup_apps

def toggle_hyprland_startup(command):
    """Toggle the startup state of command in Hyprland config"""
    apps = get_hyprland_startup_apps()
    if command not in apps:
        print(f"Command '{command}' not found in Hyprland autostart apps.")
        return
    
    app_info = apps[command]
    config_path = app_info["path"]
    
    with open(config_path, "r") as f:
        lines = f.readlines()
    
    if app_info["enabled"]:
        # Comment out the line to disable the app
        lines[app_info["line_index"]] = f"# {lines[app_info['line_index']].lstrip('# ').strip()}\n"
        print(f"Disabled startup for: {command}")
    else:
        # Uncomment the line to enable the app
        lines[app_info["line_index"]] = lines[app_info["line_index"]].lstrip("# ").strip() + "\n"
        print(f"Enabled startup for: {command}")
    
    with open(config_path, "w") as f:
        f.writelines(lines)
    
    # Reload hyprland
    subprocess.run(["hyprctl", "reload"])
    
def get_hyprland_displays() -> dict:
    """Get current displays and their transforms from hyprctl monitors
    Returns:
        dict: Dictionary with display names as keys and transforms as values for each display
    """
    try:
        result = subprocess.run(["hyprctl", "monitors"], capture_output=True, text=True)
        if result.returncode != 0:
            return {}
            
        displays = {}
        current_display = None

        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith('Monitor'):
                current_display = line.split()[1]
                displays[current_display] = {}

            elif current_display:
                if 'transform:' in line:
                    transform = int(line.split(':')[1].strip())
                    displays[current_display]['transform'] = transform
                elif 'scale:' in line:
                    scale = float(line.split(':')[1].strip())
                    displays[current_display]['scale'] = scale
                elif '@' in line and 'x' in line and 'at ' in line:
                    res_part = line.split('@')[0].strip()
                    width, height = map(int, res_part.split('x'))
                    displays[current_display]['resolution'] = {'width': width, 'height': height}

                    # Get refresh rate
                    refresh_part = line.split('@')[1].split(' at ')[0].strip()
                    refresh = int(float(refresh_part))
                    displays[current_display]['refresh_rate'] = refresh

                if ' at ' in line:
                        pos_part = line.split(' at ')[1].strip()
                        pos_x, pos_y = map(int, pos_part.split('x'))
                        displays[current_display]['position'] = {'x': pos_x, 'y': pos_y}

        return displays
    except Exception as e:
        print(f"Error getting Hyprland displays: {e}")
        return {}
    
def set_hyprland_transform(logging: Logger, display: str, orientation: str) -> bool:
    """Set display transform in Hyprland

    Args:
        display: Display name (e.g. 'eDP-1')
        orientation: Desired orientation ('normal: 0', 'right:1 ', 'inverted: 2', 'left: 3')
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        displays = get_hyprland_displays()
        if display not in displays:
            logging.log(LogLevel.Error, f"Display '{display}' not found")
            return False

        info = displays[display]
        
        resolution = info['resolution']
        refresh = info['refresh_rate']
        scale = info.get('scale', 1.0)
        if 'position' not in info:
            position = {'x': 0, 'y': 0}  # Default position
            logging.log(LogLevel.Warn, f"Position information missing for display '{display}', using (0,0)")
        else:
            position = info['position']
        current_transform = info.get('transform', 0)
        transform_map = {
            "normal": 0,
            "90°": 1,
            "180°": 2,
            "270°": 3,
            "flip": 4,
            "flip-vertical": 5,
            "flip-90°": 6,
            "flip-270°": 7,
            "rotate-ccw": (current_transform + 1) % 4,
            "rotate-cw": (current_transform - 1) % 4,
            "flip-ccw": ((current_transform + 1) % 4) + 4 if current_transform >= 4 else current_transform,
            "flip-cw": ((current_transform - 1) % 4) + 4 if current_transform >= 4 else current_transform
        }
        
        if orientation.lower() in ["rotate-cw", "rotate-ccw", "flip-cw", "flip-ccw"]:
            transform = transform_map[orientation.lower()]
        else:
            transform = transform_map.get(orientation.lower(), 0)

        pos_str = f"{position['x']}x{position['y']}"
        # hyprctl command to transform display 
        cmd = [
            "hyprctl",
            "keyword",
            f"monitor {display},{resolution['width']}x{resolution['height']}@{refresh},"
            f"{pos_str},{scale},transform,{transform}"
        ]        
        
        logging.log(LogLevel.Info, f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        
        if result.returncode != 0:
            logging.log(LogLevel.Error, f"Command failed with: {result.stderr}")
            return False
        return True

    except Exception as e:
        print(f"Error setting Hyprland transform: {e}")
        return False


def get_hyprland_rotation():
    try:
        result = subprocess.run(["hyprctl", "monitors"], capture_output=True, text=True)
        output = result.stdout

        for line in output.splitlines():
            if "transform:" in line:
                transform_value = int(line.strip().split(":")[1].strip())
                transform_map = {
                    0: "normal",
                    1: "90°",
                    2: "180°",
                    3: "270°",
                    4: "flip",
                    5: "flip-vertical",
                    6: "flip-90°",
                    7: "flip-270°"
                }
                return transform_map.get(transform_value, f"unknown ({transform_value})")
    except Exception as e:
        return f"Error: {e}"