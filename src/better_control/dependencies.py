import shutil
from typing import Dict, List, NamedTuple, Optional
from result import Result, Ok, Err


class Dependency(NamedTuple):
    command: str
    name: str
    instructions: str


class DependencyChecker:
    dependencies: Dict[str, Dependency] = {
        "powerprofilesctl": Dependency(
            "powerprofilesctl",
            "Power Profiles Control",
            "- Debian/Ubuntu: sudo apt install power-profiles-daemon\n- Arch Linux: sudo pacman -S power-profiles-daemon\n- Fedora: sudo dnf install power-profiles-daemon",
        ),
        "nmcli": Dependency(
            "nmcli",
            "Network Manager CLI",
            "- Install NetworkManager package for your distro",
        ),
        "bluetoothctl": Dependency(
            "bluetoothctl",
            "Bluetooth Control",
            "- Debian/Ubuntu: sudo apt install bluez\n- Arch Linux: sudo pacman -S bluez bluez-utils\n- Fedora: sudo dnf install bluez",
        ),
        "pactl": Dependency(
            "pactl",
            "PulseAudio Control",
            "- Install PulseAudio or PipeWire depending on your distro",
        ),
        "brightnessctl": Dependency(
            "brightnessctl",
            "Brightness Control",
            "- Debian/Ubuntu: sudo apt install brightnessctl\n- Arch Linux: sudo pacman -S brightnessctl\n- Fedora: sudo dnf install brightnessctl",
        ),
        "gammastep": Dependency(
            "gammastep",
            "Blue Light Filter",
            "- Debian/Ubuntu: sudo apt install gammastep\n- Arch Linux: sudo pacman -S gammastep\n- Fedora: sudo dnf install gammastep",
        ),
        "upower": Dependency(
            "upower",
            "Battery Information",
            "- Debian/Ubuntu: sudo apt install upower\n- Arch Linux: sudo pacman -S upower\n- Fedora: sudo dnf install upower",
        ),
    }

    @staticmethod
    def check(command: str) -> Result[None, Optional[Dependency]]:
        """Check whether a command is an available dependency.

        Args:
            command: The command to check.

        Returns:
            - `Ok(None)` if the command is an available dependency.
            - `Err(Dependency)` if the command is a known dependency but is unavailable.
            - `Err(None)` if the command is not a known dependency.
        """

        if command not in DependencyChecker.dependencies:
            return Err(None)
        if not shutil.which(command):
            return Err(DependencyChecker.dependencies[command])
        return Ok(None)

    @staticmethod
    def check_all() -> Result[None, List[Dependency]]:
        """Checks if all dependencies exist or not.

        Returns:
            - `Ok(None)` if all dependencies exists.
            - `Err(...)` a list of all missing dependencies.
        """

        missing: List[Dependency] = []
        for cmd, dep in DependencyChecker.dependencies.items():
            if not shutil.which(cmd):
                missing.append(dep)
        if not missing:  # ? list is empty
            return Ok(None)
        return Err(missing)
