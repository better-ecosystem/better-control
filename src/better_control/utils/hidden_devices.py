import json
import os
import tempfile

CONFIG_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "better-control"
)

HIDDEN_DEVICES_FILE = os.path.join(CONFIG_DIR, "hidden_devices.json")
PERMANENT_DEVICES_FILE = os.path.join(CONFIG_DIR, "permanent_devices.json")

class DeviceStorage:
    """Base class for device storage"""
    def __init__(self, storage_file, logging):
        self.storage_file = storage_file
        self.logging = logging
        self.devices = set()
        self._ensure_config_dir()
        self.load()

    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
        except Exception as e:
            self.logging.log_error(f"Error creating config dir: {e}")

    def load(self) -> bool:
        """Load devices from file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.devices = set(data)
                        return True
            return False
        except Exception as e:
            self.logging.log_error(f"Error loading devices: {e}")
            return False

    def save(self) -> bool:
        """Save devices to file atomically"""
        try:
            temp_path = tempfile.mktemp(dir=CONFIG_DIR)
            with open(temp_path, 'w') as f:
                json.dump(list(self.devices), f)

            # Verify the file is valid
            with open(temp_path, 'r') as f:
                json.load(f)

            # Atomic replace
            os.replace(temp_path, self.storage_file)
            return True
        except Exception as e:
            self.logging.log_error(f"Error saving devices: {e}")
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass
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
    def __init__(self, logging):
        super().__init__(HIDDEN_DEVICES_FILE, logging)

class PermanentDevices(DeviceStorage):
    """Class for managing permanently allowed USB devices"""
    def __init__(self, logging):
        super().__init__(PERMANENT_DEVICES_FILE, logging)


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
