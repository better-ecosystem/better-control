import shutil
from typing import Optional
from better_control.utils.logger import LogLevel, Logger

DEPENDENCIES = [
    (
        "powerprofilesctl",
        "Power Profiles Control",
        "- Debian/Ubuntu: sudo apt install power-profiles-daemon\n- Arch Linux: sudo pacman -S power-profiles-daemon\n- Fedora: sudo dnf install power-profiles-daemon",
    ),
    (
        "nmcli",
        "Network Manager CLI",
        "- Install NetworkManager package for your distro",
    ),
    (
        "bluetoothctl",
        "Bluetooth Control",
        "- Debian/Ubuntu: sudo apt install bluez\n- Arch Linux: sudo pacman -S bluez bluez-utils\n- Fedora: sudo dnf install bluez",
    ),
    (
        "pactl",
        "PulseAudio Control",
        "- Install PulseAudio or PipeWire depending on your distro",
    ),
    (
        "brightnessctl",
        "Brightness Control",
        "- Debian/Ubuntu: sudo apt install brightnessctl\n- Arch Linux: sudo pacman -S brightnessctl\n- Fedora: sudo dnf install brightnessctl",
    ),
    (
        "gammastep",
        "Blue Light Filter",
        "- Debian/Ubuntu: sudo apt install gammastep\n- Arch Linux: sudo pacman -S gammastep\n- Fedora: sudo dnf install gammastep",
    ),
    (
        "upower",
        "Battery Information",
        "- Debian/Ubuntu: sudo apt install upower\n- Arch Linux: sudo pacman -S upower\n- Fedora: sudo dnf install upower"
    )
]


def check_dependency(
    command: str, name: str, install_instructions: str, logging: Logger
) -> Optional[str]:
    """Checks if a dependency is installed or not.

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


def check_all_dependencies(logging: Logger) -> bool:
    """Checks if all dependencies exist or not.

    Returns:
        bool: returns false if there are dependencies missing, or return true
    """
    missing = [
        check_dependency(cmd, name, inst, logging) for cmd, name, inst in DEPENDENCIES
    ]
    missing = [msg for msg in missing if msg]
    return not missing
