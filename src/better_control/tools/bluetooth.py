#!/usr/bin/env python3

import dbus
import dbus.mainloop.glib
from gi.repository import GLib  # type: ignore
import subprocess
import threading
from typing import Dict, List, Optional, Callable
import time  # For proper sleep handling
import os

from better_control.utils.logger import LogLevel, Logger

BLUEZ_SERVICE_NAME = "org.bluez"
BLUEZ_ADAPTER_INTERFACE = "org.bluez.Adapter1"
BLUEZ_DEVICE_INTERFACE = "org.bluez.Device1"
DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
BLUEZ_SERVICE_NAME = 'org.bluez'
BLUEZ_ADAPTER_INTERFACE = 'org.bluez.Adapter1'
BLUEZ_DEVICE_INTERFACE = 'org.bluez.Device1'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'
DEFAULT_NOTIFY_SUBJECT='Better Control'


class BluetoothManager:
    def __init__(self, logging_instance: Logger):
        self.logging = logging_instance
        self.adapter = None
        self.adapter_path = None
        self.bus = None
        self.audio_routing_callbacks = []
        self.current_audio_sink = None
        self.signal_match = None

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
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error initializing Bluetooth: {e}")

    BATTERY_INTERFACE = "org.bluez.Battery1"

    def __del__(self):
        """Cleanup resources"""
        try:
            # Clean up any resources
            if self.signal_match:
                self.signal_match.remove()
                self.signal_match = None
            self.adapter = None
            self.bus = None
            self.audio_routing_callbacks.clear()
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
                threading.Thread(target=self._switch_to_bluetooth_audio, args=(path,), daemon=True).start()
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error handling device property change: {e}")

    def _switch_to_bluetooth_audio(self, device_path):
        """Switch both input and output audio to Bluetooth device with retries"""
        max_attempts = 2
        base_delay = 0.5  # seconds
        
        for attempt in range(max_attempts):
            try:
                # Get list of available sinks and sources
                sinks_output = subprocess.getoutput("pactl list sinks short")
                sources_output = subprocess.getoutput("pactl list sources short")
                
                bluez_sinks = [
                    line.split()[1] 
                    for line in sinks_output.splitlines() 
                    if "bluez" in line.lower()
                ]
                
                bluez_sources = [
                    line.split()[1] 
                    for line in sources_output.splitlines() 
                    if "bluez" in line.lower()
                ]
                
                if not bluez_sinks and not bluez_sources:
                    if attempt == max_attempts - 1:
                        self.logging.log(LogLevel.Warn, "No Bluetooth audio devices found after retries")
                        return
                    time.sleep(base_delay * (2 ** attempt))
                    continue
                    
                # Switch output if available
                if bluez_sinks:
                    sink_name = bluez_sinks[0]
                    verify_output = subprocess.run(["pactl", "list", "sinks", "short"], 
                                                 capture_output=True, text=True)
                    if sink_name in verify_output.stdout:
                        subprocess.run(["pactl", "set-default-sink", sink_name], check=True)
                        self.current_audio_sink = sink_name
                        self.logging.log(LogLevel.Info, f"Switched to Bluetooth output: {sink_name}")
                
                # Switch input if available
                if bluez_sources:
                    source_name = bluez_sources[0]
                    verify_output = subprocess.run(["pactl", "list", "sources", "short"],
                                                 capture_output=True, text=True)
                    if source_name in verify_output.stdout:
                        subprocess.run(["pactl", "set-default-source", source_name], check=True)
                        self.logging.log(LogLevel.Info, f"Switched to Bluetooth input: {source_name}")
                
                # Notify callbacks with the new sink name
                if self.current_audio_sink:
                    for cb in self.audio_routing_callbacks:
                        try:
                            cb(self.current_audio_sink)
                        except Exception as e:
                            self.logging.log(LogLevel.Error, f"Error in audio routing callback: {e}")
                else:
                    self.logging.log(LogLevel.Warn, "No audio sink available to notify callbacks")
                
                return
                
            except subprocess.CalledProcessError as e:
                self.logging.log(LogLevel.Error, f"Audio switch command failed (attempt {attempt+1}): {e}")
                if attempt == max_attempts - 1:
                    self.logging.log(LogLevel.Error, "Max retries reached for audio switching")
                    return
                time.sleep(base_delay * (2 ** attempt))
            except Exception as e:
                self.logging.log(LogLevel.Error, f"Unexpected error switching audio (attempt {attempt+1}): {e}")
                return

    def get_device_battery(self, device_path: str) -> Optional[int]:
        """Retrieve battery percentage for a Bluetooth device using busctl."""
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
            output = subprocess.run(
                cmd, capture_output=True, text=True
            )

            if output.returncode != 0:
                return None
            else:
                return int(output.stdout.strip().split()[-1])

        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed retrieving battery info: {e}")
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

    def set_bluetooth_power(self, enabled: bool) -> None:
        """Set Bluetooth power state"""
        try:
            if not self.adapter or self.bus is None:
                return
            self.adapter.Set(BLUEZ_ADAPTER_INTERFACE, "Powered", dbus.Boolean(enabled))
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed setting Bluetooth power: {e}")

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
                        "paired": properties.get("Paired", False),
                        "connected": properties.get("Connected", False),
                        "trusted": properties.get("Trusted", False),
                        "icon": properties.get("Icon", ""),
                        "path": path,
                    }
                )
            return devices
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed getting devices: {e}")
            return []

    def start_discovery(self) -> None:
        """Start scanning for Bluetooth devices"""
        try:
            if not self.adapter or self.bus is None or not self.adapter_path:
                return
            adapter = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, self.adapter_path),
                BLUEZ_ADAPTER_INTERFACE,
            )
            adapter.StartDiscovery()
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed starting discovery: {e}")

    def stop_discovery(self) -> None:
        """Stop scanning for Bluetooth devices"""
        try:
            if not self.adapter or self.bus is None or not self.adapter_path:
                return
            adapter = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, self.adapter_path),
                BLUEZ_ADAPTER_INTERFACE,
            )
            adapter.StopDiscovery()
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed stopping discovery: {e}")

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
            import time

            time.sleep(2)

            # Fetch device name
            properties = dbus.Interface(
                self.bus.get_object(BLUEZ_SERVICE_NAME, device_path), DBUS_PROP_IFACE
            )
            device_name = properties.Get(BLUEZ_DEVICE_INTERFACE, "Alias")

            battery_percentage: Optional[int] = self.get_device_battery(device_path)
            battery_info: str = ''

            if battery_percentage is None:
                battery_info = ""
            else:
                battery_info = f"Battery: {battery_percentage}%"

            subprocess.run(["notify-send", DEFAULT_NOTIFY_SUBJECT,
                            f"{device_name} connected.\n{battery_info}"])

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

                if battery_percentage is None:
                    battery_info = ""
                else:
                    battery_info = f"Battery: {battery_percentage}%"

                # Send notification
                subprocess.run(["notify-send", DEFAULT_NOTIFY_SUBJECT,
                                f"{device_name} connected.\n{battery_info}"])
                
                # Automatically switch to Bluetooth audio sink
                self._switch_to_bluetooth_audio(local_path)
                
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
            device_name = properties.Get(BLUEZ_DEVICE_INTERFACE, "Name")
            device.Disconnect()

            subprocess.run(["notify-send", DEFAULT_NOTIFY_SUBJECT, f"{device_name} disconnected."])

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
                subprocess.run(["notify-send", DEFAULT_NOTIFY_SUBJECT, f"{device_name} disconnected."])
                
                # Automatically switch back to default non-Bluetooth sink
                try:
                    # Get list of available sinks
                    sinks_output = subprocess.getoutput("pactl list sinks short")
                    for line in sinks_output.splitlines():
                        if "bluez" not in line.lower():
                            sink_name = line.split()[1]
                            subprocess.run(["pactl", "set-default-sink", sink_name], check=True)
                            self.current_audio_sink = sink_name
                            for cb in self.audio_routing_callbacks:
                                try:
                                    cb(sink_name)
                                except Exception as e:
                                    self.logging.log(LogLevel.Error, f"Error in audio routing callback: {e}")
                            break
                except Exception as e:
                    self.logging.log(LogLevel.Error, f"Failed switching to default audio: {e}")
                
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


# Create a global instance of the BluetoothManager
_manager = None


def get_bluetooth_manager(logging: Logger) -> BluetoothManager:
    """Get or create the global BluetoothManager instance"""
    global _manager
    if _manager is None:
        _manager = BluetoothManager(logging)
    return _manager

def add_audio_routing_callback(callback: Callable[[str], None], logging: Logger) -> None:
    """Add a callback to be notified when audio routing changes
    
    Args:
        callback: Function to call with the new sink name when routng changes
        logging: Logger instance
    """
    manager = get_bluetooth_manager(logging)
    if callback not in manager.audio_routing_callbacks:
        manager.audio_routing_callbacks.append(callback)

def remove_audio_routing_callback(callback: Callable[[str], None], logging: Logger) -> None:
    """Remove an audio routng callback
    
    Args:
        callback: Callback function to remove
        logging: Logger instance
    """
    manager = get_bluetooth_manager(logging)
    if callback in manager.audio_routing_callbacks:
        manager.audio_routing_callbacks.remove(callback)

def get_current_audio_sink(logging: Logger) -> Optional[str]:
    """Get the currently active audio sink name
    
    Returns:
        str :Name of current audio sink or None if not available
    """
    try:
        output = subprocess.getoutput("pactl get-default-sink")
        return output.strip() if output else None
    except Exception as e:
        logging.log(LogLevel.Error, f"Failed getting current audio sink: {e}")
        return None

def restore_last_sink(logging: Logger):
    """Restore the last used audio sink device after startup.

    This function attempts to restore the last used audio sink, typically
    a Bluetooth device, if one was previously connected.
    """
    try:
        # Wait for PA to fully initialize
        time.sleep(1.0)

        # Get PulseAudio settings directory
        pa_dir = os.path.expanduser("~/.config/pulse")

        # If the pulse config directory doesn't exist, exit early
        if not os.path.exists(pa_dir):
            logging.log(LogLevel.Debug, "No PulseAudio config directory found")
            return

        # Look for connection config files (specifically the default sink file)
        default_sink_file = os.path.join(pa_dir, "default-sink")

        if not os.path.exists(default_sink_file):
            logging.log(LogLevel.Debug, "No default sink file found to restore")
            return

        try:
            # Read the saved sink
            with open(default_sink_file, "r") as f:
                saved_sink = f.read().strip()

            if not saved_sink:
                logging.log(LogLevel.Debug, "No saved sink found")
                return

            # Check if it's a Bluetooth device by name convention
            if not "bluez" in saved_sink.lower():
                logging.log(LogLevel.Debug, "Saved sink is not a Bluetooth device")
                return

            # Get current sinks
            process = subprocess.run(
                ["pactl", "list", "sinks", "short"],
                capture_output=True,
                text=True,
                check=False
            )

            # Check for the presence of the saved device in currently available devices
            current_sinks = process.stdout.splitlines()
            device_found = False

            for sink in current_sinks:
                if saved_sink in sink:
                    device_found = True
                    break

            if not device_found:
                logging.log(LogLevel.Info, f"Saved Bluetooth sink '{saved_sink}' not currently available")
                return

            # Set the sink as default if it was found
            logging.log(LogLevel.Info, f"Restoring Bluetooth sink: {saved_sink}")
            subprocess.run(
                ["pactl", "set-default-sink", saved_sink],
                check=False
            )
            
            # Update current sink and notify callbacks
            manager = get_bluetooth_manager(logging)
            manager.current_audio_sink = saved_sink
            for callback in manager.audio_routing_callbacks:
                try:
                    callback(saved_sink)
                except Exception as e:
                    logging.log(LogLevel.Error, f"Error in audio routing callback: {e}")

        except Exception as e:
            logging.log(LogLevel.Error, f"Error restoring Bluetooth sink: {e}")
    except Exception as e:
        # Handle any unexpected errors without crashing
        logging.log(LogLevel.Error, f"Unexpected error in restore_last_sink: {e}")
    finally:
        # Always log completion to help with debugging
        logging.log(LogLevel.Debug, "Audio sink restoration process completed")


# Convenience functions using the global manager
def get_bluetooth_status(logging: Logger) -> bool:
    return get_bluetooth_manager(logging).get_bluetooth_status()


def set_bluetooth_power(enabled: bool, logging: Logger) -> None:
    get_bluetooth_manager(logging).set_bluetooth_power(enabled)


def get_devices(logging: Logger) -> List[Dict[str, str]]:
    return get_bluetooth_manager(logging).get_devices()


def start_discovery(logging: Logger) -> None:
    get_bluetooth_manager(logging).start_discovery()


def stop_discovery(logging: Logger) -> None:
    get_bluetooth_manager(logging).stop_discovery()


def connect_device(device_path: str, logging: Logger) -> bool:
    return get_bluetooth_manager(logging).connect_device(device_path)


def disconnect_device(device_path: str, logging: Logger) -> bool:
    return get_bluetooth_manager(logging).disconnect_device(device_path)


# Add async versions to the convenience functions
def connect_device_async(device_path: str, callback: Callable[[bool], None], logging: Logger) -> None:
    get_bluetooth_manager(logging).connect_device_async(device_path, callback)

def disconnect_device_async(device_path: str, callback: Callable[[bool], None], logging: Logger) -> None:
    get_bluetooth_manager(logging).disconnect_device_async(device_path, callback)

def forget_device(device_path: str, logging: Logger) -> bool:
    """Forget/unpair a Bluetooth device by removing it from the adapter"""
    manager = get_bluetooth_manager(logging)
    try:
        if manager.bus is None:
            logging.log(LogLevel.Error, "D-Bus connection not initialized")
            return False

        device = dbus.Interface(
            manager.bus.get_object(BLUEZ_SERVICE_NAME, device_path),
            BLUEZ_DEVICE_INTERFACE,
        )
        adapter = dbus.Interface(
            manager.bus.get_object(BLUEZ_SERVICE_NAME, manager.adapter_path),
            BLUEZ_ADAPTER_INTERFACE,
        )
        adapter.RemoveDevice(device_path)
        logging.log(LogLevel.Info, f"Device {device_path} forgotten successfully")
        return True
    except Exception as e:
        logging.log(LogLevel.Error, f"Failed to forget device {device_path}: {e}")
        return False

def forget_device_async(device_path: str, callback: Callable[[bool], None], logging: Logger) -> None:
    """Forget/unpair a Bluetooth device asynchronously

    Args:
        device_path: DBus path of the device
        callback: Function to call when forget attempt completes with a boolean success parameter
    """
    def run_forget():
        success = forget_device(device_path, logging)
        GLib.idle_add(lambda: callback(success))

    thread = threading.Thread(target=run_forget, daemon=True)
    thread.start()
