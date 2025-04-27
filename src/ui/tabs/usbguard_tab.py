#!/usr/bin/env python3

import gi
import logging
import subprocess
import threading
from gi.repository import Gtk, GLib , Gdk # type: ignore
from utils.logger import LogLevel
from utils.translations import get_translations

class USBGuardTab(Gtk.Box):
    def __init__(self, logging, txt):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.logging = logging
        self.txt = txt
        self.previous_devices = None  # Initialize as None to skip first refresh
        from utils.hidden_devices import HiddenDevices
        self.hidden_devices = HiddenDevices(logging)
        self.manual_operations = set()  # Track devices being manually allowed/blocked
        self.set_margin_start(10)
        self.set_margin_end(10)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        
        # Main header container
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        # Top row: Icon, title and refresh button
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        usb_icon = Gtk.Image.new_from_icon_name("drive-removable-media-symbolic", Gtk.IconSize.DIALOG)
        ctx = usb_icon.get_style_context()
        ctx.add_class("usb-icon")
        
        def on_enter(widget, event):
            ctx.add_class("usb-icon-animate")
        
        def on_leave(widget, event):
            ctx.remove_class("usb-icon-animate")
        
        icon_event_box = Gtk.EventBox()
        icon_event_box.add(usb_icon)
        icon_event_box.connect("enter-notify-event", on_enter)
        icon_event_box.connect("leave-notify-event", on_leave)
        
        top_row.pack_start(icon_event_box, False, False, 0)

        usb_label = Gtk.Label()
        usb_label.set_markup(f"<span weight='bold' size='large'>USBGuard</span>")
        usb_label.set_halign(Gtk.Align.START)
        top_row.pack_start(usb_label, False, False, 0)
        
        # Status indicator
        self.status_indicator = Gtk.Label()
        self.status_indicator.set_margin_start(10)
        top_row.pack_start(self.status_indicator, False, False, 0)
        
        # Spacer
        top_row.pack_start(Gtk.Box(), True, True, 0)
        
        # Refresh button
        self.refresh_button = Gtk.Button()
        self.refresh_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.refresh_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        self.refresh_label = Gtk.Label(label="Refresh")
        self.refresh_label.set_margin_start(5)
        self.refresh_btn_box.pack_start(self.refresh_icon, False, False, 0)
        
        # Animation controller
        self.refresh_revealer = Gtk.Revealer()
        self.refresh_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)
        self.refresh_revealer.set_transition_duration(150)
        self.refresh_revealer.add(self.refresh_label)
        self.refresh_revealer.set_reveal_child(False)
        self.refresh_btn_box.pack_start(self.refresh_revealer, False, False, 0)
        
        self.refresh_button.add(self.refresh_btn_box)
        refresh_tooltip = getattr(self.txt, "refresh_tooltip", "Refresh and Scan for Devices")
        self.refresh_button.set_tooltip_text(refresh_tooltip)
        self.refresh_button.connect("clicked", self.refresh_devices)
        
        # Hover behavior
        self.refresh_button.set_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.refresh_button.connect("enter-notify-event", self.on_refresh_enter)
        self.refresh_button.connect("leave-notify-event", self.on_refresh_leave)

        # Add refresh button to header
        top_row.pack_end(self.refresh_button, False, False, 0)
        
        header_box.pack_start(top_row, False, False, 0)
        
        # Bottom row: Status label and toggle switch with spacing
        bottom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        bottom_row.set_margin_top(14)  
        bottom_row.set_margin_start(3)  
        bottom_row.set_margin_end(3)  
        
        # Status label aligned left
        status_label = Gtk.Label()
        status_label.set_markup("<b>USBGuard Status</b>")
        status_label.set_halign(Gtk.Align.START)
        status_label.set_margin_start(10)  # Additional left margin
        bottom_row.pack_start(status_label, False, False, 0)
        
        # Spacer to push switch to right
        bottom_row.pack_start(Gtk.Box(), True, True, 0)
        
        # Power switch
        self.power_switch = Gtk.Switch()
        self.power_switch.set_margin_end(10)  # Additional right margin
        self.power_switch.connect("notify::active", self.on_power_switched)
        bottom_row.pack_end(self.power_switch, False, False, 0)
        
        header_box.pack_start(bottom_row, False, False, 0)
        self.pack_start(header_box, False, False, 0)
        
        # Initial service status check
        self.check_service_status()
        
        # Status label
        self.status_label = Gtk.Label()
        self.pack_start(self.status_label, False, False, 0)
        
        # Device list
        self.device_list = Gtk.ListBox()
        self.device_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.device_list)
        self.pack_start(scrolled, True, True, 0)
        
        # Control buttons
        button_box = Gtk.Box(spacing=10)
        self.manage_button = Gtk.Button(label="Manage Devices")
        self.manage_button.connect("clicked", self.show_manage_dialog)
        button_box.pack_start(self.manage_button, False, False, 0)
        
        self.policy_button = Gtk.Button(label=get_translations().policy)
        self.policy_button.connect("clicked", self.show_policy_dialog)
        button_box.pack_start(self.policy_button, False, False, 0)
        
        self.pack_end(button_box, False, False, 0)
        
        self.connect('key-press-event', self.on_key_press)
        
        # Initial refresh
        self.refresh_devices(None)
        
        # Auto-refresh thread
        self.refresh_thread_running = True
        threading.Thread(target=self.auto_refresh_devices, daemon=True).start()
        
     # keybinds for usbguard tab
    def on_key_press(self, widget, event):
        keyval = event.keyval
        
        if keyval in (114, 82):
            if self.power_switch.get_active():
                self.logging.log(LogLevel.Info, "Refreshing devices via keybind")
                self.refresh_devices(None)
                return True
            else:
                self.logging.log(LogLevel.Info, "Unable to refresh, USBGuard service is not running")
                return True

    
    def auto_refresh_devices(self):
        while self.refresh_thread_running:
            GLib.idle_add(self.refresh_devices, None)
            threading.Event().wait(5)  # Refresh every 5 seconds
    
    def refresh_devices(self, widget):
        try:
            # First check if USBGuard is installed
            try:
                subprocess.run(["which", "usbguard"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
                self.status_label.set_markup(
                    "<span foreground='red'>"
                    "USBGuard is not installed. Please install it first."
                    "</span>"
                )
                return
                
            # Then check service status
            self.check_service_status()
            
            if not self.power_switch.get_active():
                self.status_label.set_markup(
                    "<span foreground='orange'>"
                    "USBGuard service is not running. Enable it to manage devices."
                    "</span>"
                )
                return
                
            # Get device list excluding hidden devices
            result = subprocess.run(["usbguard", "list-devices"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 check=True)
            current_devices = "\n".join(
                line for line in result.stdout.decode('utf-8').splitlines()
                if line.strip() and not self.hidden_devices.contains(line.split()[0].split(':')[0])
            )
            
            # Force state update on manual refresh
            if widget:
                self.previous_devices = None
                self.manual_operations.clear()
                
            self.check_device_changes(current_devices)
            self.update_device_list(current_devices)
            self.status_label.set_text("")
            
            # Show loading spinner on refresh button
            if widget:
                spinner = Gtk.Spinner()
                spinner.start()
                widget.set_image(spinner)
                GLib.timeout_add(1000, self.reset_refresh_button, widget)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else "Unknown error"
            
            # Handle specific permission denied error
            if "Operation not permitted" in error_msg:
                error_display = (
                    "<b>USBGuard Permission Required</b>\n\n"
                    "- USBGuard requires your user to have access to it to avoid running Better Control with sudo.\n\n"
                    '- To grant permission, please check this script:\n'
                    '   <a href="https://github.com/quantumvoid0/better-control/blob/main/src/utils/usbguard_permissions.sh">'
                    'https://github.com/qunatumvoid0/better-control/blob/main/src/utils/usbguard_permissions.sh</a>\n\n'
                    "- You can run the script or manually apply the commands. Check the source if you're skeptical - we got nothing to hide."
                )

            else:
                error_display = get_translations().usbguard_error
            
            if hasattr(self.logging, 'log_error'):
                self.logging.log_error(f"USBGuard error: {error_msg}")
            else:
                print(f"USBGuard error: {error_msg}")
            self.show_error(error_display)
        except FileNotFoundError:
            if hasattr(self.logging, 'log_error'):
                self.logging.log_error("USBGuard not installed")
            else:
                print("USBGuard not installed")
            self.show_error(get_translations().usbguard_not_installed)

    # Common vendor and product mappings
    VENDOR_MAP = {
        "0x8086": "Intel",
        "0x8087": "Intel",
        "0x045e": "Microsoft",
        "0x046d": "Logitech",
        "0x04f2": "Chicony",
        "0x05ac": "Apple",
        "0x093a": "Pixart",
        "0x0b05": "ASUS",
        "0x0cf3": "Qualcomm",
        "0x1532": "Razer",
        "0x2109": "VIA Labs"
    }

    PRODUCT_TYPE_MAP = {
        "0x0001": "Keyboard",
        "0x0002": "Mouse",
        "0x0003": "Combo Keyboard/Mouse",
        "0x0004": "Game Controller",
        "0x0005": "Pen Tablet",
        "0x0006": "Scanner",
        "0x0007": "Camera",
        "0x0008": "Printer",
        "0x0009": "Storage",
        "0x000a": "Audio",
        "0x000b": "Network"
    }

    def update_device_list(self, devices_str):
        # Clear existing devices
        for child in self.device_list.get_children():
            self.device_list.remove(child)
        
        # Filter out hidden devices
        visible_devices = []
        for line in devices_str.splitlines():
            if not line.strip():
                continue
            device_id = line.split()[0].split(':')[0]
            if not self.hidden_devices.contains(device_id):
                visible_devices.append(line)
            else:
                self.logging.log_info(f"Filtering out hidden device: {device_id}")
        
        if not visible_devices:
            self.show_error(get_translations().no_devices)
            return
        
        # Add new devices (only non-hidden ones)
        for line in visible_devices:
            if not line.strip():
                continue
                
            parts = line.split()
            if len(parts) < 3:
                continue
                
            device_id = parts[0].split(":")[0]
            status = parts[1]
            device_info = " ".join(parts[2:])
            
            # Parse device info for displa
            try:
                device_name = "Device name cannot be retrieved"
                
                
                name_start = device_info.find('name "')
                if name_start != -1:
                    name_end = device_info.find('"', name_start + 6)
                    if name_end != -1:
                        device_name = device_info[name_start+6:name_end].strip()
                        if not device_name:  # If name is empty
                            device_name = "Device name cannot be retrieved"
                
                # get gud looking stuff
                status_text = {
                    "allow": "✅ Allowed",
                    "block": "❌ Blocked",
                    "reject": "🚫 Rejected"
                }.get(status.lower(), f"({status})")
                
                # Create formatted display text with device name as primary identfier
                display_text = f"""
<b>{device_name}</b>
ID: {device_id}
Status: {status_text}
"""
                if "serial=" in device_info:
                    serial = device_info.split("serial=")[1].split()[0]
                    display_text += f"Serial: {serial}\n"
                
                # Add any additional info with proper line wrapping
                display_text += f"\n<small>{device_info.replace(' ', '&#160;')}</small>"
                
            except Exception as e:
                display_text = f"{device_info} ({status})"
                if hasattr(self.logging, 'log_error'):
                    self.logging.log_error(f"Failed to parse device info: {e}")
            
            # Create device row with compact layout
            row = Gtk.ListBoxRow()
            row.set_margin_start(5)
            row.set_margin_end(5)
            row.set_margin_top(2)
            row.set_margin_bottom(2)
            
            # Main container box
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.set_margin_start(10)
            box.set_margin_end(10)
            box.set_margin_top(5)
            box.set_margin_bottom(5)
            
            # Simple icon selection based on device name
            icon_name = "drive-removable-media-symbolic"
            if "keyboard" in device_name.lower():
                icon_name = "input-keyboard-symbolic"
            elif "mouse" in device_name.lower():
                icon_name = "input-mouse-symbolic"
            elif "storage" in device_name.lower() or "disk" in device_name.lower():
                icon_name = "drive-harddisk-symbolic"
            elif "audio" in device_name.lower() or "headphone" in device_name.lower():
                icon_name = "audio-headphones-symbolic"
            elif "network" in device_name.lower():
                icon_name = "network-wired-symbolic"
            elif "printer" in device_name.lower():
                icon_name = "printer-symbolic"
            elif "camera" in device_name.lower():
                icon_name = "camera-web-symbolic"
            
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.SMALL_TOOLBAR)
            icon.set_margin_end(10)
            box.pack_start(icon, False, False, 0)
            
            # Device info in vertical box
            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            
            # Device name and status
            name_label = Gtk.Label()
            name_label.set_markup(f"<b>{device_name}</b>")
            name_label.set_halign(Gtk.Align.START)
            name_label.set_xalign(0)
            info_box.pack_start(name_label, False, False, 0)
            
            # Status indicator
            status_label = Gtk.Label()
            status_label.set_markup({
                "allow": f"<span foreground='green'>✓ {get_translations().allowed}</span>",
                "block": f"<span foreground='red'>✗ {get_translations().blocked}</span>",
                "reject": f"<span foreground='orange'>⚠ {get_translations().rejected}</span>"
            }.get(status.lower(), status))
            status_label.set_halign(Gtk.Align.START)
            status_label.set_xalign(0)
            info_box.pack_start(status_label, False, False, 0)
            
            box.pack_start(info_box, True, True, 0)
            
            # Action buttons with icons
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            
            if status == "block":
                # Temporary allow button with internal label animation
                allow_btn = Gtk.Button()
                allow_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                allow_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic", Gtk.IconSize.BUTTON)
                allow_btn_box.pack_start(allow_icon, False, False, 0)
                allow_label = Gtk.Label(label=get_translations().allow)
                allow_revealer = Gtk.Revealer()
                allow_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)
                allow_revealer.set_transition_duration(150)
                allow_revealer.add(allow_label)
                allow_revealer.set_reveal_child(False)
                allow_btn_box.pack_start(allow_revealer, False, False, 0)
                allow_btn.add(allow_btn_box)
                allow_btn.set_tooltip_text(get_translations().allow)
                allow_btn.connect("clicked", self.on_allow_device, device_id)
                
                allow_btn.set_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
                allow_btn.connect("enter-notify-event", self.on_button_hover_enter, allow_revealer)
                allow_btn.connect("leave-notify-event", self.on_button_hover_leave, allow_revealer)
                btn_box.pack_start(allow_btn, False, False, 0)
                
                # Permanent allow button with internal label animation
                perm_allow_btn = Gtk.Button()
                perm_allow_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                perm_allow_icon = Gtk.Image.new_from_icon_name("emblem-default-symbolic", Gtk.IconSize.BUTTON)
                perm_allow_btn_box.pack_start(perm_allow_icon, False, False, 0)
                perm_allow_label = Gtk.Label(label=get_translations().permanent_allow)
                perm_allow_revealer = Gtk.Revealer()
                perm_allow_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)
                perm_allow_revealer.set_transition_duration(150)
                perm_allow_revealer.add(perm_allow_label)
                perm_allow_revealer.set_reveal_child(False)
                perm_allow_btn_box.pack_start(perm_allow_revealer, False, False, 0)
                perm_allow_btn.add(perm_allow_btn_box)
                perm_allow_btn.set_tooltip_text(get_translations().permanent_allow_tooltip)
                perm_allow_btn.connect("clicked", self.on_permanent_allow_device, device_id)
                
                perm_allow_btn.set_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
                perm_allow_btn.connect("enter-notify-event", self.on_button_hover_enter, perm_allow_revealer)
                perm_allow_btn.connect("leave-notify-event", self.on_button_hover_leave, perm_allow_revealer)
                btn_box.pack_start(perm_allow_btn, False, False, 0)
            else:
                # Block button with internal label animation
                block_btn = Gtk.Button()
                block_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                block_icon = Gtk.Image.new_from_icon_name("action-unavailable-symbolic", Gtk.IconSize.BUTTON)
                block_btn_box.pack_start(block_icon, False, False, 0)
                block_label = Gtk.Label(label=get_translations().block)
                block_revealer = Gtk.Revealer()
                block_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)
                block_revealer.set_transition_duration(150)
                block_revealer.add(block_label)
                block_revealer.set_reveal_child(False)
                block_btn_box.pack_start(block_revealer, False, False, 0)
                block_btn.add(block_btn_box)
                block_btn.set_tooltip_text(get_translations().block)
                block_btn.connect("clicked", self.on_block_device, device_id)
                
                block_btn.set_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
                block_btn.connect("enter-notify-event", self.on_button_hover_enter, block_revealer)
                block_btn.connect("leave-notify-event", self.on_button_hover_leave, block_revealer)
                btn_box.pack_start(block_btn, False, False, 0)
            
            box.pack_end(btn_box, False, False, 0)
            row.add(box)
            self.device_list.add(row)
        
        self.device_list.show_all()
    
    def on_allow_device(self, widget, device_id):
        try:
            self.manual_operations.add(device_id)
            # Temporary allow (won't persist after unplug/restart)
            subprocess.run(["usbguard", "allow-device", device_id], check=True)
            
            result = subprocess.run(["usbguard", "list-devices"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 check=True)
            devices = result.stdout.decode('utf-8').splitlines()
            device_info = next((d for d in devices if d.startswith(device_id)), "")
            device_name = self.get_device_name(device_info)
            
            #subprocess.run([
                #"notify-send",
                #"-i", "emblem-ok-symbolic",
                #f"Better Control",
                #f"{device_name} has been temporarily allowed (will block after unplug)"
            #])
            
            self.refresh_devices(None)
            self.manual_operations.discard(device_id)
            
        except subprocess.CalledProcessError as e:
            if hasattr(self.logging, 'log_error'):
                self.logging.log_error(f"Failed to allow device: {e}")
            else:
                print(f"Failed to allow device: {e}")
            self.show_error(get_translations().operation_failed)

    def on_permanent_allow_device(self, widget, device_id):
        """Handle permanently allowing a USB device by adding to policy"""
        try:
            self.manual_operations.add(device_id)
            
            subprocess.run(["usbguard", "allow-device", "-p", device_id], check=True)
            
            result = subprocess.run(["usbguard", "list-devices"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 check=True)
            devices = result.stdout.decode('utf-8').splitlines()
            device_info = next((d for d in devices if d.startswith(device_id)), "")
            device_name = self.get_device_name(device_info)
            
            #subprocess.run([
#                "notify-send",
                #"-i", "emblem-default-symbolic",
                #f"Better Control",
                #f"{device_name} has been permanently allowed (added to policy)."
            #])
            
            self.refresh_devices(None)
            self.manual_operations.discard(device_id)
            
        except subprocess.CalledProcessError as e:
            if hasattr(self.logging, 'log_error'):
                self.logging.log_error(f"Failed to permanently allow device: {e}")
            else:
                print(f"Failed to permanently allow device: {e}")
            self.show_error(get_translations().operation_failed)
    
    def on_block_device(self, widget, device_id):
        try:
            self.manual_operations.add(device_id)
            
            # Block permanently with -p flag
            subprocess.run(["usbguard", "block-device", "-p", device_id], check=True)
            
            # Also remove from hidden devices if present
            self.hidden_devices.remove(device_id)
            
            # Get device info for notification
            result = subprocess.run(["usbguard", "list-devices"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 check=True)
            devices = result.stdout.decode('utf-8').splitlines()
            device_info = next((d for d in devices if d.startswith(device_id)), "")
            device_name = self.get_device_name(device_info)
            
            #subprocess.run([
                #"notify-send",
                #"-i", "action-unavailable-symbolic",
                #f"Better Control",
                #f"{device_name} has been permanently blocked"
            #])
            
            self.refresh_devices(None)
            self.manual_operations.discard(device_id)
            
        except subprocess.CalledProcessError as e:
            if hasattr(self.logging, 'log_error'):
                self.logging.log_error(f"Failed to block device: {e}")
            else:
                print(f"Failed to block device: {e}")
            self.show_error(get_translations().operation_failed)
        

    def show_manage_dialog(self, widget):
        """Show dialog to manage hidden devices"""
        dialog = None
        try:
            # Get ALL devices (including hidden ones) for management dialog
            result = subprocess.run(["usbguard", "list-devices"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 check=True)
            devices = result.stdout.decode('utf-8').splitlines()
            # Also include any hidden devices that might be currently disconnected
            for device_id in self.hidden_devices:
                if not any(d.startswith(device_id) for d in devices):
                    devices.append(f"{device_id}: hidden (disconnected)")
            
            if not devices:
                self.show_error("No USB devices found")
                return
            
            dialog = Gtk.Dialog(title="Manage Visibility Of Devices",
                            parent=self.get_toplevel(),
                            flags=Gtk.DialogFlags.MODAL)
            dialog.add_button("Done", Gtk.ResponseType.OK)
            
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            header_box.set_margin_start(10)
            header_box.set_margin_end(10)
            header_box.set_margin_top(10)
            header_box.set_margin_bottom(10)
            
            
            icon = Gtk.Image.new_from_icon_name("preferences-other-symbolic", Gtk.IconSize.DIALOG)
            header_box.pack_start(icon, False, False, 0)
            
            title = Gtk.Label(label="<b>Manage Visibility Of Devices</b>")
            title.set_use_markup(True)
            header_box.pack_start(title, False, False, 0)
            
            dialog.get_content_area().pack_start(header_box, False, False, 0)
                        
            spacer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            spacer.set_size_request(-1, 10)  # height = 10px
            dialog.get_content_area().pack_start(spacer, False, False, 0)

 
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            
            # Create list box for devices
            listbox = Gtk.ListBox()
            listbox.set_selection_mode(Gtk.SelectionMode.NONE)

            for device in devices:
                if not device.strip():
                    continue
                    
                device_id = device.split()[0].split(':')[0]
                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                box.set_margin_start(10)
                box.set_margin_end(10)
                box.set_margin_top(5)
                box.set_margin_bottom(5)
                
                check = Gtk.CheckButton()
                # Initialize as checked (hidden) so unchecking will hide
                check.set_active(not self.hidden_devices.contains(device_id))
                check.connect("toggled", lambda b, d=device_id: self.on_device_toggled(b, not b.get_active(), d))
                box.pack_start(check, False, False, 0)
                
                label = Gtk.Label(label=self.get_device_name(device))
                label.set_halign(Gtk.Align.START)
                box.pack_start(label, True, True, 0)
                
                row.add(box)
                listbox.add(row)
            
            scrolled.add(listbox)
            dialog.get_content_area().pack_start(scrolled, True, True, 0)
            dialog.set_default_size(500, 400)  
            dialog.show_all()
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                self.refresh_devices(None)
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            self.show_error(f"Failed to get device list:\n{error_msg}")
        finally:
            if dialog:
                dialog.destroy()

    def on_device_toggled(self, button, should_hide, device_id):
        """Handle device checkbox toggles
        Args:
            button: The checkbox widget
            should_hide: True if device should be hidden, False to show
            device_id: The device ID to toggle
        """
        try:
            if should_hide:
                if self.hidden_devices.add(device_id):
                    self.logging.log(LogLevel.Info, f"Hiding device: {device_id}")
                else:
                    self.logging.log(LogLevel.Error, f"Failed to hide device: {device_id}")
            else:
                if self.hidden_devices.remove(device_id):
                    self.logging.log(LogLevel.Info, f"Unhiding device: {device_id}")
                else:
                    self.logging.log(LogLevel.Error, f"Failed to unhide device: {device_id}")
        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error in device toggle handler: {e}")

    def show_policy_dialog(self, widget):
        # Store current selection
        current_selection = self.device_list.get_selected_row()
        
        dialog = Gtk.Dialog(title="USBGuard Policy", 
                        parent=self.get_toplevel(),
                        flags=Gtk.DialogFlags.MODAL)
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        
        try:
            # Get policy with timeout
            policy = subprocess.check_output(
                ["usbguard", "list-rules"],
                timeout=5
            ).decode('utf-8').strip()

            # Insert this block to show instructions if no rules exist
            if not policy:
                policy = (
                    "⚠️⚠️ No USBGuard policy rules found ⚠️⚠️.\n\n"
                    "please run this to generate policy rules\n\n"
                    "sudo usbguard generate-policy > rules.conf\n"
                    "sudo cp rules.conf /etc/usbguard/rules.conf\n"
                    "sudo systemctl restart usbguard"

                )

            # Create text view with monospace font
            textview = Gtk.TextView()
            textview.set_editable(False)
            textview.set_cursor_visible(False)
            textview.set_monospace(True)
            textview.get_buffer().set_text(policy)

            # Configure scrolling
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled.add(textview)

            # Add to dialog
            content = dialog.get_content_area()
            content.pack_start(scrolled, True, True, 0)
            content.set_margin_start(10)
            content.set_margin_end(10)
            content.set_margin_top(10)
            content.set_margin_bottom(10)

            dialog.set_default_size(600, 400)
            dialog.show_all()

            # Run dialog and restore selection
            dialog.run()
            dialog.destroy()

            if current_selection:
                self.device_list.select_row(current_selection)

        except subprocess.TimeoutExpired:
            self.show_error("Policy retrieval timed out")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            self.show_error(f"Failed to get policy:\n{error_msg}")
            if hasattr(self.logging, 'log_error'):
                self.logging.log_error(f"Policy error: {error_msg}")


            # Create text view with monospace font
            textview = Gtk.TextView()
            textview.set_editable(False)
            textview.set_cursor_visible(False)
            textview.set_monospace(True)
            textview.get_buffer().set_text(policy)

            # Configure scrolling
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled.add(textview)

            # Add to dialog
            content = dialog.get_content_area()
            content.pack_start(scrolled, True, True, 0)
            content.set_margin_start(10)
            content.set_margin_end(10)
            content.set_margin_top(10)
            content.set_margin_bottom(10)

            dialog.set_default_size(600, 400)
            dialog.show_all()

            # Run dialog and restore selection
            dialog.run()
            dialog.destroy()

            if current_selection:
                self.device_list.select_row(current_selection)

        except subprocess.TimeoutExpired:
            self.show_error("Policy retrieval timed out")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            self.show_error(f"Failed to get policy:\n{error_msg}")
            if hasattr(self.logging, 'log_error'):
                self.logging.log_error(f"Policy error: {error_msg}")


    
    def show_error(self, message):
        for child in self.device_list.get_children():
            self.device_list.remove(child)

        label = Gtk.Label()
        label.set_markup(message)
        label.set_line_wrap(True)
        label.set_selectable(True)
        label.set_use_markup(True)
        label.set_halign(Gtk.Align.START)
        label.set_valign(Gtk.Align.START)
        label.set_xalign(0)
        label.set_yalign(0)
        label.set_margin_top(10)
        label.set_margin_bottom(10)
        label.set_margin_start(10)
        label.set_margin_end(10)
        label.set_max_width_chars(80)
        label.set_track_visited_links(True)

        self.device_list.add(label)
        self.device_list.show_all()

        
    def get_device_name(self, device_info):
        """Helper method to extract device name from info string"""
        if not device_info:
            return "Unknown Device"
            
        # If we got just a device ID, try to get full info
        if len(device_info.split()) == 1 and ':' in device_info:
            try:
                result = subprocess.run(["usbguard", "list-devices", device_info],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     check=True)
                device_info = result.stdout.decode('utf-8').strip()
            except subprocess.CalledProcessError:
                pass

        try:
            parts = device_info.split()
            if len(parts) < 3:
                return "Unknown Device"
                
            device_info = " ".join(parts[2:])
            name_start = device_info.find('name "')
            if name_start != -1:
                name_end = device_info.find('"', name_start + 6)
                if name_end != -1:
                    device_name = device_info[name_start+6:name_end].strip()
                    if device_name:  # Only return if name is not empty
                        return device_name
            
            # Fallback to device ID if name can't be determined
            return parts[0].split(":")[0]
            
        except Exception:
            return "Unknown Device"

    def check_device_changes(self, current_devices):
        """Block new devices unless permanently allowed"""
        current_set = set(device.strip() for device in current_devices.splitlines() if device.strip())
        
        # Skip first refresh (initial device list)
        if self.previous_devices is None:
            self.previous_devices = current_set
            return
            
        # Handle reconnected devices
        for device in current_set:
            device_id = device.split()[0].split(":")[0]
            if device_id in self.manual_operations:
                # Skip recently modified devices
                continue
            
        # Get permanent allow rules
        try:
            policy_check = subprocess.run(
                ["usbguard", "list-rules"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            policy_rules = policy_check.stdout.decode('utf-8')
        except subprocess.CalledProcessError:
            policy_rules = ""
            
        # Handle new devices
        for device in current_set - self.previous_devices:
            device_id = device.split()[0].split(":")[0]
            if device_id not in self.manual_operations:
                # Check if device is in permanent allow policy
                try:
                    allow_check = subprocess.run(
                        ["usbguard", "list-rules"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True
                    )
                    allow_rules = allow_check.stdout.decode('utf-8')
                    
                    # Skip if device is permanently allowed
                    if f"allow id {device_id}" in allow_rules.lower():
                        continue
                        
                    # Block permanently if not allowed
                    subprocess.run(["usbguard", "block-device", "-p", device_id], check=True)
                    device_name = self.get_device_name(device)
                    #subprocess.run([
                        #"notify-send",
                        #"-i", "action-unavailable-symbolic",
                        ##f"{device_name} was permanently blocked"
                    #])
                    # Log the blocking
                    if hasattr(self.logging, 'info'):
                        self.logging.info(f"Permanently blocked device {device_id} ({device_name})")
                except subprocess.CalledProcessError as e:
                    if hasattr(self.logging, 'error'):
                        self.logging.error(f"Failed to block device {device_id}: {e}")
                    # Retry blocking if first attempt failed
                    try:
                        subprocess.run(["usbguard", "block-device", device_id], check=True)
                    except subprocess.CalledProcessError as e:
                        if hasattr(self.logging, 'error'):
                            self.logging.error(f"Failed to block device {device_id} on retry: {e}")
        
        # Removed devices
        for device in self.previous_devices - current_set:
            device_id = device.split()[0].split(":")[0]
            if device_id not in self.manual_operations:
                device_name = self.get_device_name(device)
        
        self.previous_devices = current_set

    def check_service_status(self):
        """Check and update USBGuard service status"""
        try:
            output = subprocess.check_output(["systemctl", "is-active", "usbguard"]).decode('utf-8').strip()
            is_active = output == "active"

            # Temporarily block signal so we don’t trigger on_power_switched
            self.power_switch.handler_block_by_func(self.on_power_switched)
            self.power_switch.set_active(is_active)
            self.power_switch.handler_unblock_by_func(self.on_power_switched)

            self.status_indicator.set_markup(
                f"<span foreground='{'green' if is_active else 'red'}'>"
                f"{'● Active' if is_active else '○ Inactive'}"
                f"</span>"
            )
        except subprocess.CalledProcessError:
            self.power_switch.handler_block_by_func(self.on_power_switched)
            self.power_switch.set_active(False)
            self.power_switch.handler_unblock_by_func(self.on_power_switched)

            self.status_indicator.set_markup("<span foreground='red'>○ Service Error</span>")

    def on_power_switched(self, switch, gparam):
        """Handle USBGuard service power switch changes"""
        try:
            if switch.get_active():
                subprocess.run(["pkexec", "systemctl", "start", "usbguard"], check=True)
            else:
                subprocess.run(["pkexec", "systemctl", "stop", "usbguard"], check=True)
            GLib.timeout_add(500, self.check_service_status)
        except subprocess.CalledProcessError as e:
            self.logging.log_error(f"Failed to change USBGuard service state: {e}")
            self.check_service_status()


    def reset_refresh_button(self, button):
        """Reset refresh button after operation"""
        button.set_image(Gtk.Image.new_from_icon_name(
            "view-refresh-symbolic", 
            Gtk.IconSize.BUTTON
        ))
        return False  

    def on_button_hover_enter(self, widget, event, revealer):
        """Handle button hover enter event"""
        alloc = widget.get_allocation()
        if (0 <= event.x <= alloc.width and 
            0 <= event.y <= alloc.height):
            revealer.set_reveal_child(True)
        return False
    
    def on_button_hover_leave(self, widget, event, revealer):
        """Handle button hover leave event"""
        alloc = widget.get_allocation()
        if not (0 <= event.x <= alloc.width and 
               0 <= event.y <= alloc.height):
            revealer.set_reveal_child(False) 
        return False

    def on_destroy(self, widget):
        self.refresh_thread_running = False

    def on_refresh_enter(self, widget, event):
        alloc = widget.get_allocation()
        if (0 <= event.x <= alloc.width and 
            0 <= event.y <= alloc.height):
            self.refresh_revealer.set_reveal_child(True)
        return False
    
    def on_refresh_leave(self, widget, event):
        alloc = widget.get_allocation()
        if not (0 <= event.x <= alloc.width and 
               0 <= event.y <= alloc.height):
            self.refresh_revealer.set_reveal_child(False) 
        return False