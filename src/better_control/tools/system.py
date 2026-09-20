#!/usr/bin/env python3

import subprocess
import shutil
import psutil
from typing import List, Optional, Dict, Tuple

from better_control.logger import LogLevel, Logger


def check_dependency(
    command: str, name: str, install_instructions: str, logging: Logger
) -> Optional[str]:
    """Checks if a dependency is installed or not

    Args:
        command (str): command used to check for the dependency
        name (str): the package name of the dependency
        install_instructions (str): the instruction used to install the package

    Returns:
        Optional[str]: Error message if dependency is missing, None otherwise
    """
    if not shutil.which(command):
        error_msg = f"{name} is required but not installed!\n\nInstall it using:\n{install_instructions}"
        logging.log(LogLevel.Error, error_msg)
        return error_msg
    return None


def get_battery_devices(logging: Logger) -> List[str]:
    """Returns battery devices that are detected by upower

    Returns:
        List[str]: a list of devices
    """
    try:
        devices = subprocess.getoutput("upower -e").split("\n")
        return [device for device in devices if "battery" in device]
    except Exception as e:
        logging.log(LogLevel.Error, f"Error retrieving battery devices: {e}")
        return []


def get_battery_info(device: str, logging: Logger) -> str:
    """fetch the information of a battery

    Args:
        device (str): the name of the battery device

    Returns:
        str: the information of the device
    """
    try:
        info = subprocess.getoutput(f"upower -i {device}")
        return info
    except Exception as e:
        logging.log(LogLevel.Error, f"Error retrieving battery info for {device}: {e}")
        return ""


def get_system_battery_info() -> Optional[Dict[str, str]]:
    """fetch the systemwide battery information from psutil

    Returns:
        Optional[Dict[str, str]]: a dictionary containing charge, state, and time left. Or None
    """
    battery = psutil.sensors_battery()

    if not battery:
        return None

    # Get charging state
    state = "Charging" if battery.power_plugged else "Discharging"

    # Get the amount of time left for the battery
    if battery.secsleft == psutil.POWER_TIME_UNLIMITED:
        time_left = "Unlimited"
    else:
        hours, remainder = divmod(battery.secsleft, 3600)
        minutes = remainder // 60
        time_left = f"{hours}h {minutes}m"

    return {
        "Charge": f"{battery.percent}%",
        "State": state,
        "Time Left": time_left,
    }


def detect_peripheral_battery(logging: Logger) -> Tuple[Optional[str], Optional[str]]:
    """get the battery status of mices and keyboards

    Returns:
        Tuple: a tuple containing the device and the label
    """
    for device in get_battery_devices(logging):
        info = get_battery_info(device, logging)
        if "mouse" in info.lower():
            return (device, "Wireless Mouse Battery")
        elif "keyboard" in info.lower():
            return (device, "Wireless Keyboard Battery")
    return (None, None)


def get_battery_status(logging: Logger) -> Dict[Optional[str], Optional[str]]:
    """fetch the battery status of peripheral given from the "detect_peripheral_battery" function

    Example Usage:
    ```python
    battery_status = get_battery_status()
    ```

    Returns:
        Dict[str, str]: a dict containing the device label and battery charge
    """
    peripheral_battery, label = detect_peripheral_battery(logging)

    if peripheral_battery:
        info = get_battery_info(peripheral_battery, logging)
        percentage = next(
            (
                line.split(":")[1].strip()
                for line in info.split("\n")
                if "percentage" in line.lower()
            ),
            "Unknown",
        )
        return {"Device": label, "Charge": percentage}

    system_battery = get_system_battery_info()
    if system_battery:
        system_battery["Device"] = "System Battery"
        return system_battery  # type: ignore

    return {"Device": "No Battery Detected"}


def get_current_brightness(logging: Logger) -> int:
    """Get the current brightness level.

    Returns:
        int: Current brightness level (0-100)
    """
    if not shutil.which("brightnessctl"):
        logging.log(LogLevel.Error, "brightnessctl is not installed.")
        return 50

    output = subprocess.getoutput("brightnessctl get")
    max_brightness = subprocess.getoutput("brightnessctl max")

    try:
        return int((int(output) / int(max_brightness)) * 100)
    except ValueError:
        logging.log(
            LogLevel.Error,
            f"Unexpected output from brightnessctl: {output}, {max_brightness}",
        )
        return 50


def set_brightness_level(value: int, logging: Logger) -> None:
    """Set brightness to a specific level.

    Args:
        value (int): Brightness level to set (0-100)
    """
    if shutil.which("brightnessctl"):
        max_brightness = int(subprocess.getoutput("brightnessctl max"))
        # Convert percentage to actual brightness value
        actual_value = int((value / 100) * max_brightness)
        subprocess.run(
            ["brightnessctl", "s", f"{actual_value}"], stdout=subprocess.DEVNULL
        )
    else:
        logging.log(
            LogLevel.Error,
            "brightnessctl is missing. Please check our GitHub page to see all dependencies and install them",
        )
