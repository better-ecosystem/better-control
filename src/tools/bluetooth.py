#!/usr/bin/env python3

import dbus
import dbus.mainloop.glib
from gi.repository import GLib  # type: ignore
import subprocess
import threading
from typing import Dict, List, Optional, Callable, Any, Union, TypeVar, cast, Tuple, NamedTuple
import time  # For proper sleep handling
import os
import functools
from pathlib import Path

from utils.logger import LogLevel, Logger

# D-Bus interfaces constants
BLUEZ_SERVICE_NAME = "org.bluez"
BLUEZ_ADAPTER_INTERFACE = "org.bluez.Adapter1"
BLUEZ_DEVICE_INTERFACE = "org.bluez.Device1"
BLUEZ_BATTERY_INTERFACE = "org.bluez.Battery1"
DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
DEFAULT_NOTIFY_SUBJECT = "Better Control"

# Timeouts and retry settings
DBUS_INIT_TIMEOUT = 10  # seconds
DBUS_CONNECT_RETRIES = 3
COMMAND_TIMEOUT = 3  # seconds
DEFAULT_MAX_RETRIES = 5
DEFAULT_BACKOFF_FACTOR = 0.5  # seconds

# Audio settings
PULSE_CONFIG_DIR = Path("~/.config/pulse").expanduser()
SINK_STATE_FILE = PULSE_CONFIG_DIR / "default-sink"

# Custom exception types for more specific error handling
class DBusInitError(Exception):
    """Raised when D-Bus initialization fails"""
    pass

class BluetoothCommandError(Exception):
    """Raised when a Bluetooth command fails"""
    pass

class AudioRoutingError(Exception):
    """Raised when audio routing fails"""
    pass

# Type alias for easier type hints
T = TypeVar('T')
ReturnType = TypeVar('ReturnType')
DBusPropertyType = Union[bool, str, int, float, List[Any], Dict[str, Any]]

# Helper for retry logic with exponential backoff
def with_retries(max_retries: int = DEFAULT_MAX_RETRIES, 
                 base_delay: float = DEFAULT_BACKOFF_FACTOR, 
                 timeout: float = DBUS_INIT_TIMEOUT,
                 exceptions_to_catch: tuple = (Exception,)):
    """Decorator for retrying functions with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds (will be multiplied by 2^attempt)
        timeout: Total timeout for all attempts in seconds
        exceptions_to_catch: Tuple of exception types to catch and retry
    """
    def decorator(func: Callable[..., ReturnType]) -> Callable[..., ReturnType]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> ReturnType:
            start_time = time.time()
            last_exception = None
            
            for attempt in range(max_retries):
                # Check if we've exceeded the timeout
                if time.time() - start_time > timeout:
                    if last_exception:
                        raise last_exception
                    raise TimeoutError(f"Function {func.__name__} timed out after {timeout}s")
                
                try:
                    return func(*args, **kwargs)
                except exceptions_to_catch as e:
                    last_exception = e
                    # Don't sleep on the last attempt
                    if attempt < max_retries - 1:
                        # Calculate delay with exponential backoff
                        delay = base_delay * (2 ** attempt)
                        # Make sure we don't exceed the timeout
                        if time.time() + delay - start_time > timeout:
                            delay = max(0, timeout - (time.time() - start_time))
                        time.sleep(delay)
            
            # If we get here, we've exhausted all retries
            if last_exception:
                raise last_exception
            # This should never happen if we catch all exceptions specified
            raise RuntimeError(f"Function {func.__name__} failed after {max_retries} attempts")
        
        return wrapper
    return decorator

# Helper for sending desktop notifications
def send_notification(title: str, message: str, logging: Logger) -> bool:
    """Send a desktop notification and log any errors
    
    Args:
        title: Notification title
        message: Notification message
        logging: Logger instance
    
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    try:
        result = subprocess.run(
            ["notify-send", title, message],
            capture_output=True,
            text=True,
            check=False,
            timeout=COMMAND_TIMEOUT
        )
        if result.returncode != 0:
            logging.log(LogLevel.Warn, 
                        f"Failed to send notification: {result.stderr.strip()}")
            return False
        return True
    except subprocess.SubprocessError as e:
        logging.log(LogLevel.Error, f"Error sending notification: {e}")
        return False
    except Exception as e:
        logging.log(LogLevel.Error, f"Unexpected error sending notification: {e}")
        return False


class AudioSink(NamedTuple):
    """Represents a PulseAudio sink"""
    id: int
    name: str
    description: str
    is_bluetooth: bool = False
    
class AudioSource(NamedTuple):
    """Represents a PulseAudio source"""
    id: int
    name: str
    description: str
    is_bluetooth: bool = False


class AudioRouter:
    """Manages audio routing between devices, especially for Bluetooth"""
    
    def __init__(self, logging: Logger):
        """Initialize the audio router
        
        Args:
            logging: Logger instance for recording events
        """
        self.logging = logging
        self.callbacks: List[Callable[[str], None]] = []
        self.current_sink: Optional[str] = None
        
        # Ensure the PulseAudio config directory exists
        PULSE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
    def register_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback to be notified when audio routing changes
        
        Args:
            callback: Function to call with the new sink name when routing changes
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)
            
    def unregister_callback(self, callback: Callable[[str], None]) -> None:
        """Remove an audio routing callback
        
        Args:
            callback: Callback function to remove
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    @with_retries(max_retries=3, base_delay=0.5, timeout=5)
    def list_sinks(self) -> List[AudioSink]:
        """Get list of available audio sinks
        
        Returns:
            List of AudioSink objects
        
        Raises:
            AudioRoutingError: If listing sinks fails
        """
        try:
            result = subprocess.run(
                ["pactl", "list", "sinks", "short"],
                capture_output=True,
                text=True,
                check=True,
                timeout=COMMAND_TIMEOUT
            )
            
            sinks = []
            for line in result.stdout.strip().splitlines():
                if not line:
                    continue
                    
                parts = line.split()
                if len(parts) < 2:
                    continue
                    
                sink_id = int(parts[0])
                name = parts[1]
                description = " ".join(parts[2:]) if len(parts) > 2 else name
                is_bluetooth = "bluez" in name.lower()
                
                sinks.append(AudioSink(
                    id=sink_id,
                    name=name,
                    description=description,
                    is_bluetooth=is_bluetooth
                ))
                
            return sinks
        except subprocess.SubprocessError as e:
            self.logging.log(LogLevel.Error, f"Failed to list audio sinks: {e}")
            raise AudioRoutingError(f"Failed to list audio sinks: {e}")
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Unexpected error listing audio sinks: {e}")
            raise AudioRoutingError(f"Unexpected error listing audio sinks: {e}")
    
    @with_retries(max_retries=3, base_delay=0.5, timeout=5)
    def list_sources(self) -> List[AudioSource]:
        """Get list of available audio sources
        
        Returns:
            List of AudioSource objects
        
        Raises:
            AudioRoutingError: If listing sources fails
        """
        try:
            result = subprocess.run(
                ["pactl", "list", "sources", "short"],
                capture_output=True,
                text=True,
                check=True,
                timeout=COMMAND_TIMEOUT
            )
            
            sources = []
            for line in result.stdout.strip().splitlines():
                if not line:
                    continue
                    
                parts = line.split()
                if len(parts) < 2:
                    continue
                    
                source_id = int(parts[0])
                name = parts[1]
                description = " ".join(parts[2:]) if len(parts) > 2 else name
                is_bluetooth = "bluez" in name.lower()
                
                sources.append(AudioSource(
                    id=source_id,
                    name=name,
                    description=description,
                    is_bluetooth=is_bluetooth
                ))
                
            return sources
        except subprocess.SubprocessError as e:
            self.logging.log(LogLevel.Error, f"Failed to list audio sources: {e}")
            raise AudioRoutingError(f"Failed to list audio sources: {e}")
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Unexpected error listing audio sources: {e}")
            raise AudioRoutingError(f"Unexpected error listing audio sources: {e}")
            
    def get_current_sink(self) -> Optional[str]:
        """Get the currently active audio sink name
        
        Returns:
            Name of current audio sink or None if not available
        """
        try:
            result = subprocess.run(
                ["pactl", "get-default-sink"],
                capture_output=True,
                text=True,
                check=True,
                timeout=COMMAND_TIMEOUT
            )
            sink_name = result.stdout.strip()
            return sink_name if sink_name else None
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed getting current audio sink: {e}")
            return None
            
    def get_current_source(self) -> Optional[str]:
        """Get the currently active audio source name
        
        Returns:
            Name of current audio source or None if not available
        """
        try:
            result = subprocess.run(
                ["pactl", "get-default-source"],
                capture_output=True,
                text=True,
                check=True,
                timeout=COMMAND_TIMEOUT
            )
            source_name = result.stdout.strip()
            return source_name if source_name else None
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed getting current audio source: {e}")
            return None
    
    @with_retries(max_retries=3, base_delay=0.5, timeout=5)
    def set_default_sink(self, sink_name: str) -> bool:
        """Set the default audio sink
        
        Args:
            sink_name: Name of the sink to set as default
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            AudioRoutingError: If setting the default sink fails
        """
        try:
            # Verify sink exists before setting it
            sinks = self.list_sinks()
            sink_exists = any(sink.name == sink_name for sink in sinks)
            
            if not sink_exists:
                self.logging.log(LogLevel.Warn, f"Audio sink '{sink_name}' not found")
                raise AudioRoutingError(f"Audio sink '{sink_name}' not found")
                
            result = subprocess.run(
                ["pactl", "set-default-sink", sink_name],
                capture_output=True,
                text=True,
                check=True,
                timeout=COMMAND_TIMEOUT
            )
            
            # Update current sink and save to file
            self.current_sink = sink_name
            self._save_sink_state(sink_name)
            
            # Notify callbacks
            for callback in self.callbacks:
                try:
                    callback(sink_name)
                except Exception as e:
                    self.logging.log(LogLevel.Error, f"Error in audio routing callback: {e}")
                    
            self.logging.log(LogLevel.Info, f"Set default sink to: {sink_name}")
            return True
        except subprocess.SubprocessError as e:
            self.logging.log(LogLevel.Error, f"Failed to set default sink: {e}")
            raise AudioRoutingError(f"Failed to set default sink: {e}")
        except AudioRoutingError:
            # Re-raise AudioRoutingError without wrapping it
            raise
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Unexpected error setting default sink: {e}")
            raise AudioRoutingError(f"Unexpected error setting default sink: {e}")
            
    @with_retries(max_retries=3, base_delay=0.5, timeout=5)
    def set_default_source(self, source_name: str) -> bool:
        """Set the default audio source
        
        Args:
            source_name: Name of the source to set as default
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            AudioRoutingError: If setting the default source fails
        """
        try:
            # Verify source exists before setting it
            sources = self.list_sources()
            source_exists = any(source.name == source_name for source in sources)
            
            if not source_exists:
                self.logging.log(LogLevel.Warn, f"Audio source '{source_name}' not found")
                raise AudioRoutingError(f"Audio source '{source_name}' not found")
                
            result = subprocess.run(
                ["pactl", "set-default-source", source_name],
                capture_output=True,
                text=True,
                check=True,
                timeout=COMMAND_TIMEOUT
            )
            
            self.logging.log(LogLevel.Info, f"Set default source to: {source_name}")
            return True
        except subprocess.SubprocessError as e:
            self.logging.log(LogLevel.Error, f"Failed to set default source: {e}")
            raise AudioRoutingError(f"Failed to set default source: {e}")
        except AudioRoutingError:
            # Re-raise AudioRoutingError without wrapping it
            raise
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Unexpected error setting default source: {e}")
            raise AudioRoutingError(f"Unexpected error setting default source: {e}")
    
    def _save_sink_state(self, sink_name: str) -> None:
        """Save the current sink name to a file for later restoration
        
        Args:
            sink_name: Name of sink to save
        """
        try:
            with open(SINK_STATE_FILE, 'w') as f:
                f.write(sink_name)
            self.logging.log(LogLevel.Debug, f"Saved sink state: {sink_name}")
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed to save sink state: {e}")
            
    def restore_saved_sink(self) -> bool:
        """Restore the previously saved audio sink
        
        Returns:
            True if restoration was successful, False otherwise
        """
        try:
            if not SINK_STATE_FILE.exists():
                self.logging.log(LogLevel.Debug, "No saved sink state file found")
                return False
                
            with open(SINK_STATE_FILE, 'r') as f:
                saved_sink = f.read().strip()
                
            if not saved_sink:
                self.logging.log(LogLevel.Debug, "Saved sink state file is empty")
                return False
                
            # Get current sinks and check if saved sink is available
            sinks = self.list_sinks()
            if not any(sink.name == saved_sink for sink in sinks):
                self.logging.log(LogLevel.Info, f"Saved sink '{saved_sink}' is not currently available")
                return False
                
            # Restore the sink
            self.logging.log(LogLevel.Info, f"Restoring saved sink: {saved_sink}")
            return self.set_default_sink(saved_sink)
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error restoring saved sink: {e}")
            return False
            
    def switch_to_bluetooth_audio(self, device_path: str) -> bool:
        """Switch both input and output audio to a Bluetooth device
        
        Args:
            device_path: D-Bus path of the Bluetooth device
            
        Returns:
            True if at least one audio endpoint was switched, False otherwise
        """
        success = False
        
        try:
            # Wait a short time for the audio device to register
            time.sleep(1)
            
            # Get available sinks and sources
            sinks = self.list_sinks()
            sources = self.list_sources()
            
            # Find Bluetooth sinks and sources
            bluetooth_sinks = [sink for sink in sinks if sink.is_bluetooth]
            bluetooth_sources = [source for source in sources if source.is_bluetooth]
            
            if not bluetooth_sinks and not bluetooth_sources:
                self.logging.log(LogLevel.Debug, "No Bluetooth audio devices found, retrying...")
                # Wait and retry once more
                time.sleep(2)
                sinks = self.list_sinks()
                sources = self.list_sources()
                bluetooth_sinks = [sink for sink in sinks if sink.is_bluetooth]
                bluetooth_sources = [source for source in sources if source.is_bluetooth]
                
                if not bluetooth_sinks and not bluetooth_sources:
                    self.logging.log(LogLevel.Warn, "No Bluetooth audio devices found after retry")
                    return False
            
            # Switch output if available
            if bluetooth_sinks:
                sink = bluetooth_sinks[0]
                self.set_default_sink(sink.name)
                self.logging.log(LogLevel.Info, f"Switched to Bluetooth output: {sink.name}")
                success = True
            
            # Switch input if available
            if bluetooth_sources:
                source = bluetooth_sources[0]
                self.set_default_source(source.name)
                self.logging.log(LogLevel.Info, f"Switched to Bluetooth input: {source.name}")
                success = True
                
            return success
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed to switch to Bluetooth audio: {e}")
            return False
            
    def switch_to_default_audio(self) -> bool:
        """Switch back to default (non-Bluetooth) audio devices
        
        Returns:
            True if at least one audio endpoint was switched, False otherwise
        """
        success = False
        
        try:
            # Get available sinks and sources
            sinks = self.list_sinks()
            sources = self.list_sources()
            
            # Find non-Bluetooth sinks and sources
            regular_sinks = [sink for sink in sinks if not sink.is_bluetooth]
            regular_sources = [source for source in sources if not source.is_bluetooth]
            
            # Switch output if available
            if regular_sinks:
                sink = regular_sinks[0]
                self.set_default_sink(sink.name)
                self.logging.log(LogLevel.Info, f"Switched to default output: {sink.name}")
                success = True
            
            # Switch input if available
            if regular_sources:
                source = regular_sources[0]
                self.set_default_source(source.name)
                self.logging.log(LogLevel.Info, f"Switched to default input: {source.name}")
                success = True
                
            return success
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed to switch to default audio: {e}")
            return False


class BluetoothManager:
    def __init__(self, logging_instance: Logger):
        self.logging = logging_instance
        self.adapter = None
        self.adapter_path = None
        self.bus = None
        self.audio_router = AudioRouter(logging_instance)
        self.signal_match = None

        # Initialize D-Bus with retries
        self._init_dbus()
        
    @with_retries(max_retries=DBUS_CONNECT_RETRIES, timeout=DBUS_INIT_TIMEOUT, 
                  exceptions_to_catch=(dbus.DBusException,))
    def _init_dbus(self) -> None:
        """Initialize D-Bus connection with retries
        
        Raises:
            DBusInitError: If D-Bus initialization fails after retries
        """
        try:
            # Initialize DBus with mainloop
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()
            self.mainloop = GLib.MainLoop()

            # Find the adapter
            self.adapter_path = self.find_adapter()

            # Set up signal handler for device property changes
            if self.bus:
                self.signal_match = self.bus.add_signal_receiver(
                    self._on_device_property_changed,
                    signal_name="PropertiesChanged",
                    dbus_interface=DBUS_PROP_IFACE,
                    path_keyword="path"
                )
            if self.adapter_path:
                self.adapter = dbus.Interface(
                    self.bus.get_object(BLUEZ_SERVICE_NAME, self.adapter_path),
                    DBUS_PROP_IFACE,
                )
                self.logging.log(LogLevel.Info, f"Bluetooth adapter found: {self.adapter_path}")
            else:
                self.logging.log(LogLevel.Warn, "No Bluetooth adapter found")
        except dbus.DBusException as e:
            self.logging.log(LogLevel.Error, f"DBus error initializing Bluetooth: {e}")
            raise DBusInitError(f"DBus error initializing Bluetooth: {e}")
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error initializing Bluetooth: {e}")
            raise DBusInitError(f"Error initializing Bluetooth: {e}")

    def __del__(self):
        """Cleanup resources"""
        try:
            # Clean up any resources
            if hasattr(self, 'signal_match') and self.signal_match:
                self.signal_match.remove()
                self.signal_match = None
                
            # Explicitly remove signal receiver if possible
            if hasattr(self, 'bus') and self.bus:
                try:
                    self.bus.remove_signal_receiver(
                        self._on_device_property_changed,
                        signal_name="PropertiesChanged",
                        dbus_interface=DBUS_PROP_IFACE
                    )
                except Exception:
                    pass  # Ignore errors removing signal receiver

            # Stop any running mainloop
            if hasattr(self, 'mainloop') and self.mainloop and hasattr(self.mainloop, 'is_running') and self.mainloop.is_running():
                self.mainloop.quit()
                
            self.adapter = None
            self.bus = None
        except Exception:
            pass  # Ignore errors during cleanup

    def _on_device_property_changed(self, interface, changed_properties, invalidated_properties, path):
        """Handle DBus property change signals for Bluetooth devices"""
        try:
            if interface != BLUEZ_DEVICE_INTERFACE:
                return

            # Check if this is a connection state change
            if "Connected" in changed_properties and changed_properties["Connected"]:
                # Device connected - switch audio
                self.audio_router.switch_to_bluetooth_audio(path)
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error handling device property change: {e}")

    def get_device_battery(self, device_path: str) -> Optional[int]:
        """Retrieve battery percentage for a Bluetooth device
        
        First tries to use D-Bus Properties interface directly,
        then falls back to busctl command.
        
        Args:
            device_path: D-Bus path of the device
            
        Returns:
            Battery percentage as integer, None if not available, or -1 on error
        """
        # First try using D-Bus directly
        try:
            if self.bus is None:
                raise RuntimeError("D-Bus connection not initialized")
                
            battery_props = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, device_path),
                DBUS_PROP_IFACE
            )
            
            # Check if device has Battery interface
            managed_objects = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, "/"),
                DBUS_OM_IFACE
            ).GetManagedObjects()
            
            if device_path in managed_objects and BLUEZ_BATTERY_INTERFACE in managed_objects[device_path]:
                percentage = battery_props.Get(BLUEZ_BATTERY_INTERFACE, "Percentage")
                return int(percentage)
            
            # No Battery interface, fall back to busctl
            return self._get_device_battery_busctl(device_path)
            
        except dbus.DBusException as e:
            if "org.freedesktop.DBus.Error.UnknownInterface" in str(e):
                # Battery interface not available, try busctl
                return self._get_device_battery_busctl(device_path)
            
            self.logging.log(LogLevel.Debug, f"D-Bus error getting battery info: {e}")
            return self._get_device_battery_busctl(device_path)
            
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error getting battery info: {e}")
            return -1

    def _get_device_battery_busctl(self, device_path: str) -> Optional[int]:
        """Fallback method to get battery using busctl command
        
        Args:
            device_path: D-Bus path of the device
            
        Returns:
            Battery percentage as integer, None if not available, or -1 on error
        """
        try:
            cmd = [
                "busctl",
                "get-property",
                "org.bluez",
                device_path,
                "org.bluez.Battery1",
                "Percentage",
            ]

            # Run the command and capture the output
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=COMMAND_TIMEOUT
            )

            if result.returncode != 0:
                return None
            else:
                # Parse the output - should be something like "y 85"
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    return int(parts[-1])
                return None

        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed retrieving battery info with busctl: {e}")
            return -1  # Indicate battery info is unavailable

    def find_adapter(self) -> str:
        """Find the first available Bluetooth adapter"""
        try:
            if self.bus is None:
                self.logging.log(LogLevel.Error, "D-Bus connection not initialized")
                return ""

            remote_om = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, "/"), DBUS_OM_IFACE
            )
            objects = remote_om.GetManagedObjects()

            for o, props in objects.items():
                if BLUEZ_ADAPTER_INTERFACE in props:
                    return o

            self.logging.log(LogLevel.Warn, "No Bluetooth adapter found")
            return ""
        except dbus.DBusException as e:
            self.logging.log(LogLevel.Error, f"DBus error finding Bluetooth adapter: {e}")
            return ""
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error finding Bluetooth adapter: {e}")
            return ""

    def get_bluetooth_status(self) -> bool:
        """Get Bluetooth power status"""
        try:
            if not self.adapter or self.bus is None:
                return False
            powered = self.adapter.Get(BLUEZ_ADAPTER_INTERFACE, "Powered")
            return bool(powered)
        except dbus.DBusException as e:
            self.logging.log(LogLevel.Error, f"DBus error getting Bluetooth status: {e}")
            return False
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed getting Bluetooth status: {e}")
            return False

    def set_bluetooth_power(self, enabled: bool) -> bool:
        """Set Bluetooth power state
        
        Args:
            enabled: True to power on, False to power off
            
        Returns:
            True if operation was successful, False otherwise
        """
        try:
            if not self.adapter or self.bus is None:
                self.logging.log(LogLevel.Error, "Bluetooth adapter not initialized")
                return False
                
            self.adapter.Set(BLUEZ_ADAPTER_INTERFACE, "Powered", dbus.Boolean(enabled))
            return True
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed setting Bluetooth power: {e}")
            return False

    def get_devices(self) -> List[Dict[str, str]]:
        """Get list of all known Bluetooth devices"""
        try:
            if not self.adapter or self.bus is None:
                return []

            remote_om = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, "/"), DBUS_OM_IFACE
            )
            objects = remote_om.GetManagedObjects()
            devices = []
            for path, interfaces in objects.items():
                if BLUEZ_DEVICE_INTERFACE not in interfaces:
                    continue

                properties = interfaces[BLUEZ_DEVICE_INTERFACE]
                if not properties.get("Name", None):
                    continue

                devices.append(
                    {
                        "mac": properties.get("Address", ""),
                        "name": properties.get("Name", ""),
                        "paired": bool(properties.get("Paired", False)),
                        "connected": bool(properties.get("Connected", False)),
                        "trusted": bool(properties.get("Trusted", False)),
                        "icon": properties.get("Icon", ""),
                        "path": path,
                    }
                )
            return devices
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed getting devices: {e}")
            return []

    def start_discovery(self) -> bool:
        """Start scanning for Bluetooth devices
        
        Returns:
            True if discovery started successfully, False otherwise
        """
        try:
            if not self.adapter or self.bus is None or not self.adapter_path:
                self.logging.log(LogLevel.Error, "Bluetooth adapter not initialized")
                return False
                
            adapter = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, self.adapter_path),
                BLUEZ_ADAPTER_INTERFACE,
            )
            adapter.StartDiscovery()
            return True
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed starting discovery: {e}")
            return False

    def stop_discovery(self) -> bool:
        """Stop scanning for Bluetooth devices
        
        Returns:
            True if discovery stopped successfully, False otherwise
        """
        try:
            if not self.adapter or self.bus is None or not self.adapter_path:
                self.logging.log(LogLevel.Error, "Bluetooth adapter not initialized")
                return False
                
            adapter = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, self.adapter_path),
                BLUEZ_ADAPTER_INTERFACE,
            )
            adapter.StopDiscovery()
            return True
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed stopping discovery: {e}")
            return False

    def connect_device(self, device_path: str) -> bool:
        """Connect to a Bluetooth device, set it as the default audio sink, and fetch battery info."""
        try:
            if self.bus is None:
                self.logging.log(LogLevel.Error, "D-Bus connection not initialized")
                return False

            device = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, device_path),
                BLUEZ_DEVICE_INTERFACE,
            )
            device.Connect()

            # Wait for the device to register
            time.sleep(2)

            # Fetch device name
            properties = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, device_path), DBUS_PROP_IFACE
            )
            device_name = properties.Get(BLUEZ_DEVICE_INTERFACE, "Alias")

            battery_percentage: Optional[int] = self.get_device_battery(device_path)
            battery_info: str = ''

            if battery_percentage is None or battery_percentage < 0:
                battery_info = ""
            else:
                battery_info = f"Battery: {battery_percentage}%"

            send_notification(DEFAULT_NOTIFY_SUBJECT, 
                            f"{device_name} connected.\n{battery_info}", 
                            self.logging)

            # Switch to Bluetooth audio
            self.audio_router.switch_to_bluetooth_audio(device_path)
            
            return True
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed connecting to device: {e}")
            return False

    def connect_device_async(self, device_path: str, callback: Callable[[bool], None]) -> None:
        """Connect to a Bluetooth device asynchronously

        Args:
            device_path: DBus path of the device
            callback: Function to call when connection attempt completes with a boolean success parameter
        """
        def run_connect():
            success = False
            device_name = "Unknown Device"
            try:
                if self.bus is None:
                    self.logging.log(LogLevel.Error, "D-Bus connection not initialized")
                    GLib.idle_add(lambda: callback(False))
                    return

                # Make a copy of the device_path to avoid any potential threading issues
                local_path = str(device_path)

                # Get DBus interfaces
                device = dbus.Interface(
                    self.bus.get_object(BLUEZ_SERVICE_NAME, local_path),
                    BLUEZ_DEVICE_INTERFACE,
                )
                properties = dbus.Interface(
                    self.bus.get_object(BLUEZ_SERVICE_NAME, local_path),
                    DBUS_PROP_IFACE
                )

                # Get device name before connecting
                try:
                    device_name = str(properties.Get(BLUEZ_DEVICE_INTERFACE, "Alias"))
                except Exception:
                    device_name = "Bluetooth Device"

                # Connect to the device
                self.logging.log(LogLevel.Info, f"Connecting to {device_name}...")
                device.Connect()

                # Wait to ensure connection is established
                time.sleep(1)

                # Verify connection status
                try:
                    is_connected = bool(properties.Get(BLUEZ_DEVICE_INTERFACE, "Connected"))
                    if not is_connected:
                        self.logging.log(LogLevel.Warn, f"Connection to {device_name} reported as failed, but no exception thrown")
                        GLib.idle_add(lambda: callback(False))
                        return
                except Exception as e:
                    self.logging.log(LogLevel.Error, f"Failed to verify connection status: {e}")

                # Get battery information
                battery_percentage: Optional[int] = self.get_device_battery(local_path)
                battery_info: str = ''

                if battery_percentage is None or battery_percentage < 0:
                    battery_info = ""
                else:
                    battery_info = f"Battery: {battery_percentage}%"

                # Send notification
                send_notification(DEFAULT_NOTIFY_SUBJECT,
                                  f"{device_name} connected.\n{battery_info}",
                                  self.logging)
                
                # Automatically switch to Bluetooth audio sink
                self.audio_router.switch_to_bluetooth_audio(local_path)
                
                success = True

            except Exception as e:
                self.logging.log(LogLevel.Error, f"Failed connecting to device {device_name}: {e}")
                success = False

            # Call the callback in the main thread
            GLib.idle_add(lambda: callback(success))

        # Start the connection process in a separate real thread
        thread = threading.Thread(target=run_connect, daemon=True)
        thread.start()

    def disconnect_device(self, device_path: str) -> bool:
        """Disconnect from a Bluetooth device"""
        try:
            if self.bus is None:
                self.logging.log(LogLevel.Error, "D-Bus connection not initialized")
                return False

            device = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, device_path),
                BLUEZ_DEVICE_INTERFACE,
            )
            properties = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, device_path), DBUS_PROP_IFACE
            )
            # Fetch device name
            device_name = "Bluetooth Device"
            try:
                device_name = properties.Get(BLUEZ_DEVICE_INTERFACE, "Name")
            except Exception:
                try:
                    device_name = properties.Get(BLUEZ_DEVICE_INTERFACE, "Alias")
                except Exception:
                    pass
                    
            device.Disconnect()

            send_notification(DEFAULT_NOTIFY_SUBJECT, 
                             f"{device_name} disconnected.", 
                             self.logging)
            
            # Switch back to default audio
            self.audio_router.switch_to_default_audio()

            return True
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed disconnecting from device: {e}")
            return False

    def disconnect_device_async(self, device_path: str, callback: Callable[[bool], None]) -> None:
        """Disconnect from a Bluetooth device asynchronously

        Args:
            device_path: DBus path of the device
            callback: Function to call when disconnection attempt completes with a boolean success parameter
        """
        def run_disconnect():
            success = False
            device_name = "Unknown Device"
            try:
                if self.bus is None:
                    self.logging.log(LogLevel.Error, "D-Bus connection not initialized")
                    GLib.idle_add(lambda: callback(False))
                    return

                # Make a copy of the device_path to avoid any potential threading issues
                local_path = str(device_path)

                # Get DBus interfaces
                device = dbus.Interface(
                    self.bus.get_object(BLUEZ_SERVICE_NAME, local_path),
                    BLUEZ_DEVICE_INTERFACE,
                )
                properties = dbus.Interface(
                    self.bus.get_object(BLUEZ_SERVICE_NAME, local_path),
                    DBUS_PROP_IFACE
                )

                # Get device name before disconnecting
                try:
                    device_name = str(properties.Get(BLUEZ_DEVICE_INTERFACE, "Name"))
                except Exception:
                    try:
                        device_name = str(properties.Get(BLUEZ_DEVICE_INTERFACE, "Alias"))
                    except Exception:
                        device_name = "Bluetooth Device"

                # Disconnect the device
                self.logging.log(LogLevel.Info, f"Disconnecting from {device_name}...")
                device.Disconnect()

                # Wait to ensure disconnection is completed
                time.sleep(1)

                # Send notification
                send_notification(DEFAULT_NOTIFY_SUBJECT, 
                                 f"{device_name} disconnected.", 
                                 self.logging)
                
                # Automatically switch back to default non-Bluetooth sink
                self.audio_router.switch_to_default_audio()
                
                success = True

            except Exception as e:
                self.logging.log(LogLevel.Error, f"Failed disconnecting from device {device_name}: {e}")
                success = False

            # Call the callback in the main thread
            GLib.idle_add(lambda: callback(success))

        # Start the disconnection process in a separate real thread
        thread = threading.Thread(target=run_disconnect, daemon=True)
        thread.start()
        
    def bluetooth_supported(self) -> bool:
        return bool(self.adapter_path)
    
    def add_audio_routing_callback(self, callback: Callable[[str], None]) -> None:
        """Add a callback to be notified when audio routing changes
        
        Args:
            callback: Function to call with the new sink name when routing changes
        """
        self.audio_router.register_callback(callback)
        
    def remove_audio_routing_callback(self, callback: Callable[[str], None]) -> None:
        """Remove an audio routing callback
        
        Args:
            callback: Callback function to remove
        """
        self.audio_router.unregister_callback(callback)
    
    def get_current_audio_sink(self) -> Optional[str]:
        """Get the currently active audio sink name
        
        Returns:
            Name of current audio sink or None if not available
        """
        return self.audio_router.get_current_sink()
        
    def restore_last_sink(self) -> bool:
        """Restore the last used audio sink
        
        Returns:
            True if restoration was successful, False otherwise
        """
        return self.audio_router.restore_saved_sink()


# Create a global instance of the BluetoothManager
_manager = None


def get_bluetooth_manager(logging: Logger) -> BluetoothManager:
    """Get or create the global BluetoothManager instance"""
    global _manager
    if _manager is None:
        try:
            _manager = BluetoothManager(logging)
        except DBusInitError as e:
            logging.log(LogLevel.Error, f"Failed to initialize BluetoothManager: {e}")
            # Create a minimal manager that reports no support
            _manager = BluetoothManager.__new__(BluetoothManager)
            _manager.logging = logging
            _manager.adapter = None
            _manager.adapter_path = None
            _manager.bus = None
            _manager.audio_router = AudioRouter(logging)
    return _manager

def add_audio_routing_callback(callback: Callable[[str], None], logging: Logger) -> None:
    """Add a callback to be notified when audio routing changes
    
    Args:
        callback: Function to call with the new sink name when routng changes
        logging: Logger instance
    """
    manager = get_bluetooth_manager(logging)
    manager.add_audio_routing_callback(callback)

def remove_audio_routing_callback(callback: Callable[[str], None], logging: Logger) -> None:
    """Remove an audio routng callback
    
    Args:
        callback: Callback function to remove
        logging: Logger instance
    """
    manager = get_bluetooth_manager(logging)
    manager.remove_audio_routing_callback(callback)

def get_current_audio_sink(logging: Logger) -> Optional[str]:
    """Get the currently active audio sink name
    
    Returns:
        str: Name of current audio sink or None if not available
    """
    return get_bluetooth_manager(logging).get_current_audio_sink()

def restore_last_sink(logging: Logger) -> bool:
    """Restore the last used audio sink device after startup.
    
    Returns:
        bool: True if restoration was successful, False otherwise
    """
    return get_bluetooth_manager(logging).restore_last_sink()


# Convenience functions using the global manager
def get_bluetooth_status(logging: Logger) -> bool:
    """Get Bluetooth power status
    
    Args:
        logging: Logger instance
    
    Returns:
        bool: True if Bluetooth is powered on, False otherwise
    """
    return get_bluetooth_manager(logging).get_bluetooth_status()


def set_bluetooth_power(enabled: bool, logging: Logger) -> bool:
    """Set Bluetooth power state
    
    Args:
        enabled: True to power on, False to power off
        logging: Logger instance
        
    Returns:
        bool: True if operation was successful, False otherwise
    """
    return get_bluetooth_manager(logging).set_bluetooth_power(enabled)


def get_devices(logging: Logger) -> List[Dict[str, str]]:
    """Get list of all known Bluetooth devices
    
    Args:
        logging: Logger instance
    
    Returns:
        List of dictionaries with device information
    """
    return get_bluetooth_manager(logging).get_devices()


def start_discovery(logging: Logger) -> bool:
    """Start scanning for Bluetooth devices
    
    Args:
        logging: Logger instance
    
    Returns:
        bool: True if discovery started successfully, False otherwise
    """
    return get_bluetooth_manager(logging).start_discovery()


def stop_discovery(logging: Logger) -> bool:
    """Stop scanning for Bluetooth devices
    
    Args:
        logging: Logger instance
    
    Returns:
        bool: True if discovery stopped successfully, False otherwise
    """
    return get_bluetooth_manager(logging).stop_discovery()


def connect_device(device_path: str, logging: Logger) -> bool:
    """Connect to a Bluetooth device
    
    Args:
        device_path: D-Bus path of the device
        logging: Logger instance
        
    Returns:
        bool: True if connection was successful, False otherwise
    """
    return get_bluetooth_manager(logging).connect_device(device_path)


def disconnect_device(device_path: str, logging: Logger) -> bool:
    """Disconnect from a Bluetooth device
    
    Args:
        device_path: D-Bus path of the device
        logging: Logger instance
        
    Returns:
        bool: True if disconnection was successful, False otherwise
    """
    return get_bluetooth_manager(logging).disconnect_device(device_path)


# Add async versions to the convenience functions
def connect_device_async(device_path: str, callback: Callable[[bool], None], logging: Logger) -> None:
    """Connect to a Bluetooth device asynchronously
    
    Args:
        device_path: D-Bus path of the device
        callback: Function to call when connection attempt completes with a boolean success parameter
        logging: Logger instance
    """
    get_bluetooth_manager(logging).connect_device_async(device_path, callback)

def disconnect_device_async(device_path: str, callback: Callable[[bool], None], logging: Logger) -> None:
    """Disconnect from a Bluetooth device asynchronously
    
    Args:
        device_path: D-Bus path of the device
        callback: Function to call when disconnection attempt completes with a boolean success parameter
        logging: Logger instance
    """
    get_bluetooth_manager(logging).disconnect_device_async(device_path, callback)

# Check if Bluetooth is supported on this system
def bluetooth_supported(logging: Logger) -> bool:
    """Check if Bluetooth is supported on this system
    
    Args:
        logging: Logger instance
        
    Returns:
        bool: True if Bluetooth is supported, False otherwise
    """
    return get_bluetooth_manager(logging).bluetooth_supported()
