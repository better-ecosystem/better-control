#!/usr/bin/env sh
# This script is run when user presses "give permission" button on the usbguard tab

set -eu

echo "=== USBGuard Permission Setup ==="
echo "This will configure your system to allow USBGuard access."

if [ "$(id -u)" -ne 0 ]; then
    echo "Please run this script with sudo or as root."
    exit 1
fi

# Determine invoking user
USER_NAME="${SUDO_USER:-$(logname)}"
echo "Configuring USBGuard for user: $USER_NAME"

# Create usbguard group if it doesn't exist
if ! getent group usbguard >/dev/null; then
    echo "Creating usbguard group..."
    groupadd usbguard
else
    echo "usbguard group already exists."
fi

# Add user to usbguard group
echo "Adding $USER_NAME to usbguard group..."
usermod -aG usbguard "$USER_NAME"

# Create or update udev rule
UDEV_RULE_FILE="/etc/udev/rules.d/99-usbguard.rules"
RULE='SUBSYSTEM=="usb", MODE="0660", TAG+="uaccess"'

if [ -f "$UDEV_RULE_FILE" ]; then
    if grep -Fxq "$RULE" "$UDEV_RULE_FILE"; then
        echo "udev rule already present."
    else
        echo "Appending udev rule to $UDEV_RULE_FILE..."
        echo "$RULE" >> "$UDEV_RULE_FILE"
    fi
else
    echo "Creating udev rule at $UDEV_RULE_FILE..."
    echo "$RULE" > "$UDEV_RULE_FILE"
fi

# Modify usbguard-daemon.conf safely
CONF_FILE="/etc/usbguard/usbguard-daemon.conf"

modify_conf_entry() {
    local key="$1"
    local value="$2"
    if grep -q "^$key=" "$CONF_FILE"; then
        if grep -q "^$key=.*\b$value\b" "$CONF_FILE"; then
            echo "$key already includes $value."
        else
            echo "Appending $value to $key..."
            sed -i "s/^$key=/&$value /" "$CONF_FILE"
        fi
    else
        echo "$key=$value" >> "$CONF_FILE"
    fi
}

modify_conf_entry "IPCAllowedUsers" "$USER_NAME"
modify_conf_entry "IPCAllowedGroups" "usbguard"

# Reload udev and restart usbguard
echo "Reloading udev rules..."
udevadm control --reload-rules

echo "Restarting USBGuard service..."
systemctl restart usbguard

echo
echo "USBGuard setup complete for user '$USER_NAME'."
echo "Please log out and back in for group changes to take effect."
echo "Note: You may need to reconnect USB devices after setup."
