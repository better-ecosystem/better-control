import json
import os
from pathlib import Path
from typing import Any

from better_control.utils.atomic_write import atomic_write
from better_control.utils.logger import LogLevel, Logger
from better_control.utils.settings import Config


class DeviceStorage:
    """Base class for device storage"""

    def __init__(self, logger: Logger, config: Config, storage_file: Path):
        self.__logger = logger
        self.__config = config

        self.storage_file = storage_file
        self.devices: set[Any] = set()
        self.load()

    def load(self) -> bool:
        """Load devices from file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, "r") as f:
                    data = json.load(f)

                    if isinstance(data, list):
                        self.devices = set(data)  # type: ignore
                        return True
            return False
        except Exception as e:
            self.__logger.log(LogLevel.Error, f"Error loading devices: {e}")
            return False

    def save(self) -> bool:
        """Save devices to file atomically"""
        try:
            atomic_write(
                self.storage_file,
                lambda f: json.dump(list(self.devices), f),  # type: ignore
            )
            return True
        except Exception as e:
            self.__logger.log(
                LogLevel.Error,
                f"Error saving devices: {e}",
            )
            return False

    def add(self, device_id: str) -> bool:
        """Add a device"""
        self.devices.add(device_id)
        return self.save()

    def remove(self, device_id: str) -> bool:
        """Remove a device"""
        self.devices.discard(device_id)
        return self.save()

    def contains(self, device_id: str) -> bool:
        """Check if device exists"""
        return device_id in self.devices

    def __iter__(self):
        """Allow iteration over device IDs"""
        return iter(self.devices)


class HiddenDevices(DeviceStorage):
    """Class for managing hidden USB devices"""

    def __init__(self, config: Config, logger: Logger):
        super().__init__(
            logger, config, Path(os.path.join(config.config_dir, "hidden_devices.json"))
        )

    def add(self, device_id: str) -> bool:
        """Add a device to hidden set"""
        self.devices.add(device_id)
        return self.save()

    def remove(self, device_id: str) -> bool:
        """Remove a device from hidden set"""
        self.devices.discard(device_id)
        return self.save()

    def contains(self, device_id: str) -> bool:
        """Check if device is hidden"""
        return device_id in self.devices

    def __iter__(self):
        """Allow iteration over hidden device IDs"""
        return iter(self.devices)


class PermanentDevices(DeviceStorage):
    """Class for managing permanently allowed USB devices"""

    def __init__(self, config: Config, logger: Logger):
        super().__init__(
            logger,
            config,
            Path(os.path.join(config.config_dir, "permanent_devices.json")),
        )

    def add(self, device_id: str) -> bool:
        """Add a device to hidden set"""
        self.devices.add(device_id)
        return self.save()

    def remove(self, device_id: str) -> bool:
        """Remove a device from hidden set"""
        self.devices.discard(device_id)
        return self.save()

    def contains(self, device_id: str) -> bool:
        """Check if device is hidden"""
        return device_id in self.devices

    def __iter__(self):
        """Allow iteration over hidden device IDs"""
        return iter(self.devices)
