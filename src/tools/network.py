#!/usr/bin/env python3

import subprocess
from typing import Tuple, List

from utils.logger import LogLevel, Logger


def get_network_speed(logging: Logger) -> Tuple[float, float]:
    """Measure current network speed

    Returns:
        Tuple[float, float]: Upload and download speeds in Mbps
    """
    try:
        # Get network interfaces for wifi and ethernet
        interfaces_output = subprocess.getoutput(
            "nmcli -t -f DEVICE,TYPE device | grep -E 'wifi|ethernet'"
        ).split("\n")
        logging.log(LogLevel.Debug, f"Interfaces output: {interfaces_output}")
        wifi_interfaces = [line.split(":")[0] for line in interfaces_output if "wifi" in line and ":" in line]
        ethernet_interfaces = [line.split(":")[0] for line in interfaces_output if "ethernet" in line and ":" in line]
        logging.log(LogLevel.Debug, f"WiFi interfaces: {wifi_interfaces}")
        logging.log(LogLevel.Debug, f"Ethernet interfaces: {ethernet_interfaces}")

        if wifi_interfaces:
            interface = wifi_interfaces[0]
        elif ethernet_interfaces:
            interface = ethernet_interfaces[0]
        else:
            logging.log(LogLevel.Debug, "No wifi or ethernet interfaces found")
            return 0.0, 0.0

        logging.log(LogLevel.Debug, f"Using interface: {interface}")

        operstate = subprocess.getoutput(f"cat /sys/class/net/{interface}/operstate").strip()
        logging.log(LogLevel.Debug, f"Interface {interface} operstate: {operstate}")
        if operstate != "up":
            logging.log(LogLevel.Debug, f"Interface {interface} is not up")
            return 0.0, 0.0

        rx_bytes = int(
            subprocess.getoutput(f"cat /sys/class/net/{interface}/statistics/rx_bytes")
        )
        tx_bytes = int(
            subprocess.getoutput(f"cat /sys/class/net/{interface}/statistics/tx_bytes")
        )
        logging.log(LogLevel.Debug, f"rx_bytes: {rx_bytes}, tx_bytes: {tx_bytes}")

        # Store current values
        if not hasattr(get_network_speed, "prev_rx_bytes"):
            get_network_speed.prev_rx_bytes = rx_bytes  # type: ignore
            get_network_speed.prev_tx_bytes = tx_bytes  # type: ignore
            return 0.0, 0.0

        # Calculate speed
        rx_speed = rx_bytes - get_network_speed.prev_rx_bytes  # type: ignore
        tx_speed = tx_bytes - get_network_speed.prev_tx_bytes  # type: ignore

        # Update previous values
        get_network_speed.prev_rx_bytes = rx_bytes  # type: ignore
        get_network_speed.prev_tx_bytes = tx_bytes  # type: ignore

        # Convert to Mbps
        rx_speed_mbps = (rx_speed * 8) / (1024 * 1024)  # Convert to Mbps
        tx_speed_mbps = (tx_speed * 8) / (1024 * 1024)  # Convert to Mbps

        return tx_speed_mbps, rx_speed_mbps

    except Exception as e:
        logging.log(LogLevel.Error, f"Failed measuring network speed: {e}")
        return 0.0, 0.0


def get_wifi_networks(logging: Logger) -> List[str]:
    """Get list of available WiFi networks

    Returns:
        List[str]: List of network information strings
    """
    try:
        # Use fields parameter to get a more consistent format, including SIGNAL explicitly
        output = subprocess.getoutput(
            "nmcli -f IN-USE,BSSID,SSID,MODE,CHAN,RATE,SIGNAL,BARS,SECURITY dev wifi list"
        )
        networks = output.split("\n")[1:]  # Skip header row
        return networks
    except Exception as e:
        logging.log(LogLevel.Error, f"Failed getting WiFi networks: {e}")
        return []


def get_wifi_status(logging: Logger) -> bool:
    """Check if WiFi is enabled

    Returns:
        bool: True if WiFi is enabled, False otherwise
    """
    try:
        wifi_status = subprocess.getoutput("nmcli radio wifi").strip()
        return wifi_status.lower() == "enabled"
    except Exception as e:
        logging.log(LogLevel.Error, f"Failed getting WiFi status: {e}")
        return False


def set_wifi_status(enabled: bool, logging: Logger) -> bool:
    """Enable or disable WiFi

    Args:
        enabled (bool): True to enable WiFi, False to disable

    Returns:
        bool: True if operation was successful, False otherwise
    """
    try:
        command = "on" if enabled else "off"
        subprocess.run(["nmcli", "radio", "wifi", command], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.log(
            LogLevel.Error, f"Failed to {'enable' if enabled else 'disable'} WiFi: {e}"
        )
        return False


def connect_to_wifi(
    ssid: str, logging: Logger, password: str = "", remember: bool = True
) -> bool:
    """Connect to a WiFi network

    Args:
        ssid (str): Network SSID
        password (str, optional): Network password. Defaults to None.
        remember (bool, optional): Whether to remember the network. Defaults to True.

    Returns:
        bool: True if connection was successful, False otherwise
    """
    try:
        if password:
            # Create connection profile
            add_command = [
                "nmcli",
                "con",
                "add",  
                "type",
                "wifi",
                "con-name",
                "ssid",
                "wifi-sec.key-mgmt",
                "wpa-psk",
                "wifi-sec.psk",
                password,
            ]

            if not remember:
                add_command.extend(["connection.autoconnect", "no"])

            subprocess.run(add_command, check=True)
        else:
            # For open networks
            add_command = [
                "nmcli",
                "con",
                "add",
                "type",
                "wifi",
                "con-name",
                "ssid",
            ]
            subprocess.run(add_command, check=True)

        # Activate the connection
        subprocess.run(["nmcli", "con", "up", "ssid"], check=True)
        return True

    except subprocess.CalledProcessError as e:
        logging.log(LogLevel.Error, f"Failed to connect to network {ssid}: {e}")
        return False


def disconnect_wifi(logging: Logger) -> bool:
    """Disconnect from current WiFi network

    Returns:
        bool: True if disconnection was successful, False otherwise
    """
    try:
        # First approach: Try to find WiFi device that's connected
        connected_wifi_device = subprocess.getoutput(
            "nmcli -t -f DEVICE,STATE dev | grep wifi.*:connected"
        )

        if connected_wifi_device:
            # Extract device name
            wifi_device = connected_wifi_device.split(":")[0]

            # Get connection name for this device
            device_connection = subprocess.getoutput(
                f"nmcli -t -f NAME,DEVICE con show --active | grep {wifi_device}"
            )

            if device_connection and ":" in device_connection:
                connection_name = device_connection.split(":")[0]
                subprocess.run(["nmcli", "con", "down", connection_name], check=True)
                return True

        # Second approach: Try checking all active WiFi connections
        active_connections = subprocess.getoutput(
            "nmcli -t -f NAME,TYPE con show --active"
        ).split("\n")
        for conn in active_connections:
            if ":" in conn and (
                "wifi" in conn.lower() or "802-11-wireless" in conn.lower()
            ):
                connection_name = conn.split(":")[0]
                subprocess.run(["nmcli", "con", "down", connection_name], check=True)
                return True

        return False

    except subprocess.CalledProcessError as e:
        logging.log(LogLevel.Error, f"Failed to disconnect: {e}")
        return False


def forget_wifi_network(ssid: str, logging: Logger) -> bool:
    """Remove a saved WiFi network

    Args:
        ssid (str): Network SSID to forget

    Returns:
        bool: True if operation was successful, False otherwise
    """
    try:
        subprocess.run(["nmcli", "connection", "delete", ssid], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.log(LogLevel.Error, f"Failed to forget network: {e}")
        return False
