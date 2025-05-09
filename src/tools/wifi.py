#!/usr/bin/env python3

from pathlib import Path
import qrcode
import subprocess
from typing import List, Dict

import qrcode.constants
from utils.logger import LogLevel, Logger
import time
import threading


def get_wifi_status(logging: Logger) -> bool:
    """Get WiFi power status

    Returns:
        bool: True if WiFi is enabled, False otherwise
    """
    try:
        result = subprocess.run(
            ["nmcli", "radio", "wifi"], capture_output=True, text=True
        )
        return result.stdout.strip().lower() == "enabled"
    except Exception as e:
        logging.log(LogLevel.Error, f"Failed getting WiFi status: {e}")
        return False


def set_wifi_power(enabled: bool, logging: Logger) -> None:
    """Set WiFi power state

    Args:
        enabled (bool): True to enable, False to disable
    """
    try:
        state = "on" if enabled else "off"
        subprocess.run(["nmcli", "radio", "wifi", state], check=True)
    except subprocess.CalledProcessError as e:
        logging.log(LogLevel.Error, f"Failed setting WiFi power: {e}")


def get_wifi_networks(logging: Logger) -> List[Dict[str, str]]:
    """Get list of available WiFi networks

    Returns:
        List[Dict[str, str]]: List of network dictionaries
    """
    try:
        # Check if WiFi is supported on this system
        result = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,TYPE", "device"],
            capture_output=True,
            text=True,
        )
        wifi_interfaces = [line for line in result.stdout.split("\n") if "wifi" in line]
        if not wifi_interfaces:
            logging.log(LogLevel.Warn, "WiFi is not supported on this machine")
            return []

        # Use --terse mode and specific fields for more reliable parsing
        result = subprocess.run(
            [
                "nmcli",
                "-t",
                "-f",
                "IN-USE,SSID,SIGNAL,SECURITY",
                "device",
                "wifi",
                "list",
            ],
            capture_output=True,
            text=True,
        )
        output = result.stdout
        networks = []
        for line in output.split("\n"):
            if not line.strip():
                continue
            # Split by ':' since we're using terse mode
            parts = line.split(":")
            if len(parts) >= 4:
                in_use = "*" in parts[0]
                ssid = parts[1]
                signal = parts[2] if parts[2].strip() else "0"
                security = parts[3] if parts[3].strip() != "" else "none"
                # Only add networks with valid SSIDs
                if ssid and ssid.strip():
                    networks.append(
                        {
                            "in_use": in_use,
                            "ssid": ssid.strip(),
                            "signal": signal.strip(),
                            "security": security.strip(),
                        }
                    )
        return networks
    except Exception as e:
        logging.log(LogLevel.Error, f"Failed getting WiFi networks: {e}")
        return []


def get_connection_info(ssid: str, logging: Logger) -> Dict[str, str]:
    """Get information about a WiFi connection

    Args:
        ssid (str): Network SSID

    Returns:
        Dict[str, str]: Dictionary containing connection information
    """
    try:
        result = subprocess.run(
            ["nmcli", "-t", "--show-secrets", "connection", "show", ssid], capture_output=True, text=True
        )
        output = result.stdout
        info = {}
        for line in output.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                info[key.strip()] = value.strip()
        password = info.get("802-11-wireless-security.psk", "Hidden")
        info["password"] = password
        return info
    except Exception as e:
        logging.log(LogLevel.Error, f"Failed getting connection info: {e}")
        return {}


def connect_network(
    ssid: str, logging: Logger, password: str = "", remember: bool = True
) -> bool:
    """Connect to a WiFi network

    Args:
        ssid (str): Network SSID
        password (str, optional): Network password. Defaults to "".
        remember (bool, optional): Whether to save the connection. Defaults to True.

    Returns:
        bool: True if connection successful, False otherwise
    """
    # Handle connection with password
    if password:
        return _connect_with_password(ssid, password, remember, logging)
    else:
        return _connect_without_password(ssid, remember, logging)


def _connect_with_password(ssid: str, password: str, remember: bool, logging: Logger) -> bool:
    """Helper function to connect to a network with a password"""
    try:
        # Get networks but don't use the unused variable
        get_wifi_networks(logging)

        # Default to creating a new connection with explicit security settings
        logging.log(LogLevel.Info, f"Creating connection for network: {ssid}")

        # First, try to delete any existing connection with this name to avoid conflicts
        try:
            delete_cmd = f'nmcli connection delete "{ssid}"'
            subprocess.run(delete_cmd, shell=True, capture_output=True, text=True)
            logging.log(LogLevel.Debug, f"Removed any existing connection named '{ssid}'")
        except Exception as e:
            # It's fine if this fails - might not exist yet
            logging.log(LogLevel.Debug, f"No existing connection to delete or other error: {e}")

        # Create a new connection with the right security settings
        conn_name = f"{ssid}-temp" if not remember else ssid

        # Create new connection with explicit security settings
        cmd_str = f'nmcli connection add con-name "{conn_name}" type wifi ssid "{ssid}" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "{password}"'
        logging.log(LogLevel.Debug, f"Creating connection with command (password masked): nmcli connection add con-name \"{conn_name}\" type wifi ssid \"{ssid}\" wifi-sec.key-mgmt wpa-psk wifi-sec.psk ********")

        result = subprocess.run(cmd_str, capture_output=True, text=True, shell=True)

        # Log the result
        if result.stdout:
            logging.log(LogLevel.Debug, f"Connection creation output: {result.stdout}")
        if result.stderr:
            logging.log(LogLevel.Debug, f"Connection creation error: {result.stderr}")

        # Now activate the connection
        if result.returncode == 0:
            return _activate_connection(conn_name, ssid, remember, logging)
        else:
            logging.log(LogLevel.Error, f"Failed to create connection profile: {result.stderr or 'Unknown error'}")
            return _try_fallback_connection(ssid, password, remember, logging)

    except Exception as e:
        logging.log(LogLevel.Error, f"Error during connection process: {e}")
        return False


def _activate_connection(conn_name: str, ssid: str, remember: bool, logging: Logger) -> bool:
    """Activate a created connection profile"""
    logging.log(LogLevel.Info, f"Created connection profile for {ssid}, now connecting...")

    # Connect to the newly created connection
    up_cmd = f'nmcli connection up "{conn_name}"'
    up_result = subprocess.run(up_cmd, capture_output=True, text=True, shell=True)

    # Log the connection result
    if up_result.stdout:
        logging.log(LogLevel.Debug, f"Connection activation output: {up_result.stdout}")
    if up_result.stderr:
        logging.log(LogLevel.Debug, f"Connection activation error: {up_result.stderr}")

    # Clean up if temporary
    if not remember and up_result.returncode == 0:
        _schedule_connection_cleanup(conn_name, logging)

    if up_result.returncode == 0:
        logging.log(LogLevel.Info, f"Successfully connected to {ssid}")
        return True
    else:
        logging.log(LogLevel.Error, f"Failed to activate connection: {up_result.stderr or 'Unknown error'}")
        return False


def _schedule_connection_cleanup(conn_name: str, logging: Logger) -> None:
    """Schedule the deletion of a temporary connection"""
    def delete_later():
        try:
            time.sleep(2)  # Give it a moment to connect fully
            delete_cmd = f'nmcli connection delete "{conn_name}"'
            subprocess.run(delete_cmd, shell=True)
            logging.log(LogLevel.Debug, f"Removed temporary connection {conn_name}")
        except Exception as e:
            logging.log(LogLevel.Error, f"Failed to remove temporary connection: {e}")

    cleanup = threading.Thread(target=delete_later)
    cleanup.daemon = True
    cleanup.start()


def _try_fallback_connection(ssid: str, password: str, remember: bool, logging: Logger) -> bool:
    """Try the simpler device wifi connect approach as fallback"""
    fallback_cmd = f'nmcli device wifi connect "{ssid}" password "{password}"'
    if not remember:
        fallback_cmd += " --temporary"

    logging.log(LogLevel.Debug, f"Trying fallback connection method (password masked): nmcli device wifi connect \"{ssid}\" password ********")
    fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True, shell=True)

    if fallback_result.returncode == 0:
        logging.log(LogLevel.Info, f"Connected to {ssid} using fallback method")
        return True
    else:
        logging.log(LogLevel.Error, f"Fallback connection failed: {fallback_result.stderr or 'Unknown error'}")
        return False


def _connect_without_password(ssid: str, remember: bool, logging: Logger) -> bool:
    """Connect to a network without providing a password (using saved credentials)"""
    try:
        # Use shell=True with quoted SSID
        cmd_str = f'nmcli con up "{ssid}"'
        result = subprocess.run(cmd_str, capture_output=True, text=True, shell=True)

        # Log all output
        if result.stdout:
            logging.log(LogLevel.Debug, f"Saved connection output: {result.stdout}")
        if result.stderr:
            logging.log(LogLevel.Debug, f"Saved connection error: {result.stderr}")

        # Check result code
        if result.returncode == 0:
            logging.log(LogLevel.Info, f"Connected to {ssid} using saved connection")
            return True
        else:
            # Log the error details for debugging
            logging.log(LogLevel.Debug, f"Failed to connect using saved connection: {result.stderr}")

            # Check if the error is about missing password
            if "Secrets were required, but not provided" in (result.stderr or ""):
                logging.log(LogLevel.Debug, "Connection requires password which wasn't provided")
                # Return false to trigger the password dialog in the UI
                return False

            return _try_direct_connection(ssid, remember, logging)
    except Exception as e:
        logging.log(LogLevel.Error, f"Exception during connection attempt: {e}")
        return False


def _try_direct_connection(ssid: str, remember: bool, logging: Logger) -> bool:
    """Try connecting directly to a network"""
    cmd_str = f'nmcli device wifi connect "{ssid}"'
    if not remember:
        cmd_str += " --temporary"

    logging.log(LogLevel.Debug, f"Attempting direct connection using command: {cmd_str}")
    result = subprocess.run(cmd_str, capture_output=True, text=True, shell=True)

    # Log all output
    if result.stdout:
        logging.log(LogLevel.Debug, f"Direct connection output: {result.stdout}")
    if result.stderr:
        logging.log(LogLevel.Debug, f"Direct connection error: {result.stderr}")

    # Check result code
    if result.returncode == 0:
        logging.log(LogLevel.Info, f"Connected to {ssid} using direct connection")
        return True
    else:
        logging.log(LogLevel.Error, f"Failed direct connection: {result.stderr or 'Unknown error'}")
        return False


def disconnect_network(ssid: str, logging: Logger) -> bool:
    """Disconnect from a WiFi network

    Args:
        ssid (str): Network SSID

    Returns:
        bool: True if disconnection successful, False otherwise
    """
    try:
        subprocess.run(["nmcli", "connection", "down", ssid], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.log(LogLevel.Error, f"Failed disconnecting from network: {e}")
        return False


def forget_network(ssid: str, logging: Logger) -> bool:
    """Remove a saved WiFi network

    Args:
        ssid (str): Network SSID

    Returns:
        bool: True if removal successful, False otherwise
    """
    try:
        subprocess.run(["nmcli", "connection", "delete", ssid], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.log(LogLevel.Error, f"Failed removing network: {e}")
        return False


def get_network_speed(logging: Logger) -> Dict[str, float]:
    try:
        # Get network interfaces for wifi and ethernett
        interfaces_output = subprocess.getoutput(
            "nmcli -t -f DEVICE,TYPE device | grep -E 'wifi|ethernet'"
        ).split("\n")
        wifi_interfaces = [line.split(":")[0] for line in interfaces_output if "wifi" in line and ":" in line]
        ethernet_interfaces = [line.split(":")[0] for line in interfaces_output if "ethernet" in line and ":" in line]


        def is_interface_up(interface: str) -> bool:
            operstate = subprocess.getoutput(f"cat /sys/class/net/{interface}/operstate").strip()
            return operstate == "up"

        interface = None
        for iface in wifi_interfaces:
            if is_interface_up(iface):
                interface = iface
                break

        if interface is None:
            for iface in ethernet_interfaces:
                if is_interface_up(iface):
                    interface = iface
                    break

        if interface is None:
            return {"rx_bytes": 0, "tx_bytes": 0, "wifi_supported": False}


        rx_bytes = int(
            subprocess.getoutput(f"cat /sys/class/net/{interface}/statistics/rx_bytes")
        )
        tx_bytes = int(
            subprocess.getoutput(f"cat /sys/class/net/{interface}/statistics/tx_bytes")
        )

        return {"rx_bytes": rx_bytes, "tx_bytes": tx_bytes, "wifi_supported": True}
    except Exception as e:
        logging.log(LogLevel.Error, f"Failed getting network speed: {e}")
        return {"rx_bytes": 0, "tx_bytes": 0, "wifi_supported": False}

def get_pillow_install_instructions():
    """Returns installation instructions for Pillow on various distros"""
    instructions = (
        "Pillow (Python Imaging Library) is required for QR code generation.\n"
        "Install it for your distribution:\n\n"
        "Alpine: sudo apk add py3-pillow\n"
        "Fedora: sudo dnf install python3-pillow\n"
        "Debian/Ubuntu: sudo apt install python3-pillow\n"
        "Arch: sudo pacman -S python-pillow\n"
        "Void: sudo xbps-install python3-pillow\n\n"
        "After installing, restart the application."
    )
    print(instructions)

def generate_wifi_qrcode(ssid: str, password: str, security: str, logging:Logger) -> str:
    """Generate qr_code for the wifi

    Returns:
        str: path to generated qr code image or installation instructions
    """
    # First check if Pillow is available
    try:
        import qrcode
    except ImportError:
        get_pillow_install_instructions()

    # Define temp_dir at the beginning to avoid 'possibly unbound' error
    temp_dir = Path("/tmp/better-control")

    try:
        temp_dir.mkdir(parents=True, exist_ok=True)

        qr_code_path = temp_dir / f"{ssid}.png"
        if qr_code_path.exists():
            logging.log(LogLevel.Info, f"found qr code for {ssid} at {qr_code_path}")
            return str(qr_code_path)

        security_type = "WPA" if security.lower() != "none" else "nopass"
        wifi_string = f"WIFI:T:{security_type};S:{ssid};P:{password};;"

        # generate the qr code
        qr_code = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=6,
            border=2,
        )
        qr_code.add_data(wifi_string)
        qr_code.make(fit=True)

        # create qr code image
        qr_code_image = qr_code.make_image(fill_color="black", back_color="white")
        # Open the file in binary write mode instead of passing a string
        with open(qr_code_path, "wb") as f:
            qr_code_image.save(f)

        logging.log(LogLevel.Info, f"generated qr code for {ssid} at {qr_code_path}")
        return str(qr_code_path)

    except Exception as e:
        logging.log(LogLevel.Error, f"Failed to generate qr code for {ssid} : {e}")
        # Fix: create an error.png path using correct Path object usage
        error_path = temp_dir / "error.png"
        return str(error_path)

def wifi_supported() -> bool:
    try:
        result = subprocess.run(["nmcli", "-t", "-f", "DEVICE,TYPE", "device"], capture_output=True, text=True)
        wifi_interfaces = [line for line in result.stdout.split('\n') if "wifi" in line]
        return bool(wifi_interfaces)
    except Exception:
        return False