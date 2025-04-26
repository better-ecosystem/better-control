"""
English language translation for Better Control
"""

from translations.translation_manager import TranslationManager

class English:
    """English language translation for the application"""
    def __init__(self):
        # app description
        self.msg_desc = "A sleek GTK-themed control panel for Linux."

        # USB notifications
        self.usb_connected = "{device} connected."
        self.usb_disconnected = "{device} disconnected."
        self.permission_allowed = "USB permission granted"
        self.permission_blocked = "USB permission blocked"
        self.msg_app_url = "https://github.com/quantumvoid0/better-control"
        self.msg_usage = "Usage"

        # for args
        self.msg_args_help = "Prints this message"
        self.msg_args_autostart = "Starts with the autostart tab open"
        self.msg_args_battery = "Starts with the battery tab open"
        self.msg_args_bluetooth = "Starts with the bluetooth tab open"
        self.msg_args_display = "Starts with the display tab open"
        self.msg_args_force = "Makes the app force to have all dependencies installed"
        self.msg_args_power = "Starts with the power tab open"
        self.msg_args_volume = "Starts with the volume tab open"
        self.msg_args_volume_v = "Also starts with the volume tab open"
        self.msg_args_wifi = "Starts with the wifi tab open"

        self.msg_args_log = "The program will either log to a file if given a file path,\n or output to stdout based on the log level if given a value between 0, and 3."
        self.msg_args_redact = "Redact sensitive information from logs (network names, device IDs, etc.)"
        self.msg_args_size = "Sets a custom window size"

        # commonly used
        self.connect = "Connect"
        self.connected = "Connected"
        self.connecting = "Connecting..."
        self.disconnect = "Disconnect"
        self.disconnected = "Disconnected"
        self.disconnecting = "Disconnecting..."
        self.enable = "Enable"
        self.disable = "Disable"
        self.close = "Close"
        self.show = "Show"
        self.loading = "Loading..."
        self.loading_tabs = "Loading tabs..."

        # for tabs
        self.msg_tab_autostart = "Autostart"
        self.msg_tab_usbguard = "USBGuard"
        self.usbguard_title = "USB Device Control"
        self.refresh = "Refresh"
        self.allow = "Allow"
        self.block = "Block"
        self.allowed = "Allowed"
        self.blocked = "Blocked"
        self.rejected = "Rejected"
        self.policy = "View Policy"
        self.usbguard_error = "Error accessing USBGuard"
        self.usbguard_not_installed = "USBGuard not installed"
        self.usbguard_not_running = "USBGuard service not running"
        self.no_devices = "No USB devices connected"
        self.operation_failed = "Operation failed"
        self.policy_error = "Failed to load policy"
        self.permanent_allow = "Permanently Allow"
        self.permanent_allow_tooltip = "Permanently allow this device (adds to policy)"
        self.msg_tab_battery = "Battery"
        self.msg_tab_bluetooth = "Bluetooth"
        self.msg_tab_display = "Display"
        self.msg_tab_power = "Power"
        self.msg_tab_volume = "Volume"
        self.msg_tab_wifi = "Wi-Fi"

        # Autostart tab translations
        self.autostart_title = "Autostart Applications"
        self.autostart_session = "Session"
        self.autostart_show_system_apps = "Show system autostart applications"
        self.autostart_configured_applications = "Configured Applications"
        self.autostart_tooltip_rescan = "Rescan autostart apps"

        # Battery tab translations
        self.battery_title = "Battery Dashboard"
        self.battery_power_saving = "Power Saving"
        self.battery_balanced = "Balanced"
        self.battery_performance = "Performance"
        self.battery_batteries = "Batteries"
        self.battery_overview = "Overview"
        self.battery_details = "Details"
        self.battery_tooltip_refresh = "Refresh Battery Information"
        self.battery_no_batteries = "No battery detected"

        # Bluetooth tab translations
        self.bluetooth_title = "Bluetooth Devices"
        self.bluetooth_scan_devices = "Scan for Devices"
        self.bluetooth_scanning = "Scanning..."
        self.bluetooth_power = "Bluetooth"
        self.bluetooth_available_devices = "Available Devices"
        self.bluetooth_tooltip_refresh = "Scan for Devices"
        self.bluetooth_connect_failed = "Failed to connect to device"
        self.bluetooth_disconnect_failed = "Failed to disconnect from device"
        self.bluetooth_try_again = "Please try again later."

        # Display tab translations
        self.display_title = "Display Settings"
        self.display_brightness = "Screen Brightness"
        self.display_blue_light = "Blue Light"
        self.display_orientation = "Orientation"
        self.display_default = "Default"
        self.display_left = "Left"
        self.display_right = "Right"
        self.display_inverted = "Inverted"
        
        self.display_rotation = "Rotation Options"
        self.display_simple_rotation = "Quick Rotation"
        self.display_specific_orientation = "Specific Orientation"
        self.display_flip_controls = "Display Flipping"
        self.display_rotate_cw = "Rotate Clockwise"
        self.display_rotate_ccw = "Rotate Counter-clockwise"
        self.display_rotation_help = "Rotation applies right away. It’ll reset if you don’t confirm in 10 seconds."

        # Power tab translations
        self.power_title = "Power Management"
        self.power_tooltip_menu = "Configure Power Menu"
        self.power_menu_buttons = "Buttons"
        self.power_menu_commands = "Commands"
        self.power_menu_colors = "Colors"
        self.power_menu_show_hide_buttons = "Show/Hide Buttons"
        self.power_menu_shortcuts_tab_label = "Shortcuts"
        self.power_menu_visibility = "Buttons"
        self.power_menu_keyboard_shortcut = "Keyboard Shortcuts"
        self.power_menu_show_keyboard_shortcut = "Show Keyboard Shortcuts"
        self.power_menu_lock = "Lock"
        self.power_menu_logout = "Logout"
        self.power_menu_suspend = "Suspend"
        self.power_menu_hibernate = "Hibernate"
        self.power_menu_reboot = "Reboot"
        self.power_menu_shutdown = "Shutdown"
        self.power_menu_apply = "Apply"
        self.power_menu_tooltip_lock = "Lock the screen"
        self.power_menu_tooltip_logout = "Log out of the current session"
        self.power_menu_tooltip_suspend = "Suspend the system (sleep)"
        self.power_menu_tooltip_hibernate = "Hibernate the system"
        self.power_menu_tooltip_reboot = "Restart the screen"
        self.power_menu_tooltip_shutdown = "Power off the screen"


        # Volume tab translations
        self.volume_title = "Volume Settings"
        self.volume_speakers = "Speakers"
        self.volume_tab_tooltip = "Speakers Settings"
        self.volume_output_device = "Output Device"
        self.volume_device = "Device"
        self.volume_output = "Output"
        self.volume_speaker_volume = "Speaker Volume"
        self.volume_mute_speaker = "Mute Speakers"
        self.volume_unmute_speaker = "Unmute Speakers"
        self.volume_quick_presets = "Quick Presets"
        self.volume_output_combo_tooltip = "Select output device for this application"

        # Volume tab microphone translations
        self.microphone_tab_microphone = "Microphone"
        self.microphone_tab_input_device = "Input Device"
        self.microphone_tab_volume = "Microphone Volume"
        self.microphone_tab_mute_microphone = "Mute Microphone"
        self.microphone_tab_unmute_microphone = "Unmute Microphone"
        self.microphone_tab_tooltip = "Microphone Settings"

        # Volume tab App output translations
        self.app_output_title = "App Output"
        self.app_output_volume = "Application Output Volume"
        self.app_output_mute = "Mute"
        self.app_output_unmute = "Unmute"
        self.app_output_tab_tooltip = "Application Output Settings"
        self.app_output_no_apps = "No applications playing audio"
        self.app_output_dropdown_tooltip = "Select output device for this application"

        # Volume tab App input translations
        self.app_input_title = "App Input"
        self.app_input_volume = "Application Input Volume"
        self.app_input_mute = "Mute Microphone for this application"
        self.app_input_unmute = "Unmute Microphone for this application"
        self.app_input_tab_tooltip = "Application Microphone Settings"
        self.app_input_no_apps = "No applications using microphone"

        # WiFi tab translations
        self.wifi_title = "Wi-Fi Networks"
        self.wifi_refresh_tooltip = "Refresh Networks"
        self.wifi_power = "Wi-Fi"
        self.wifi_speed = "Connection Speed"
        self.wifi_download = "Download"
        self.wifi_upload = "Upload"
        self.wifi_available = "Available Networks"
        self.wifi_forget = "Forget"
        self.wifi_share_title = "Share Network"
        self.wifi_share_scan = "Scan to connect"
        self.wifi_network_name = "Network Name"
        self.wifi_password = "Password"
        self.wifi_loading_networks = "Loading Networks..."

        # Settings tab translations
        self.settings_title = "Settings"
        self.settings_tab_settings = "Tab Settings"
        self.settings_language = "Language"
        self.settings_language_changed_restart = "Please restart the application for the language change to take effect."
        self.settings_language_changed = "Language changed"

# Register the language with the TranslationManager
TranslationManager.register_language("en", English)