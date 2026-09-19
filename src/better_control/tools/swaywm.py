#!/usr/bin/env python3

from pathlib import Path
import subprocess

CONFIG_FILES = [
    Path.home() / ".config/sway/config",
    Path.home() / ".config/sway/autostart"
]

def get_sway_startup_apps():
    """Get apps started using exec  in Sway"""
    startup_apps = {}
    for sway_config in CONFIG_FILES:
        if sway_config.exists():
            with open(sway_config, "r") as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                stripped = line.strip()
                # this is a workaround for sway files
                if (stripped.startswith("exec") or
                    stripped.startswith("# exec") or
                    stripped.startswith("#exec") or
                    stripped.startswith("exec_always") or
                    stripped.startswith("#exec_always") or
                    stripped.startswith("# exec_always")):
                    
                    enabled = not stripped.startswith("#")
                    cleared_line = stripped.lstrip("#").strip()
                    
                    parts = cleared_line.split(None, 1)
                    if len(parts) <= 1:
                        continue
                    command = parts[1].strip().strip('"')
                    if command:
                        startup_apps[command] = {
                            "name": command,
                            "type": "sway",
                            "path": sway_config,
                            "line_index": i,
                            "enabled": enabled
                        }
    return startup_apps

def toggle_sway_startup(command):
    """Toggle the startup app in sway"""
    apps  = get_sway_startup_apps()
    if command not in apps:
        (f"Command '{command}' not found in Sway autostart apps.")
        return
    
    app_info = apps[command]
    config_path = app_info["path"]
    
    with open(config_path, "r") as f:
        lines = f.readlines()
        
    # comment and uncomment the line
    if app_info["enabled"]:
        lines[app_info["line_index"]] = f"# {lines[app_info['line_index']].lstrip('# ').strip()}\n"
        print(f"Disabled startup for: {command}")
    else:
        lines[app_info["line_index"]] = lines[app_info["line_index"]].lstrip("# ").strip() + "\n"
        print(f"Enabled startup for: {command}")
    
    with open(config_path, "w") as f:
        f.writelines(lines)
    
    subprocess.run(["swaymsg", "reload"], check=True)