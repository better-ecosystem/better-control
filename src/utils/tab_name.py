from utils.arg_parser import ArgParse


def tab_name_from_arguments(arg_parser: ArgParse):
    active_tab = None

    if arg_parser.find_arg(("-V", "--volume")) or arg_parser.find_arg(("-v", "")):
        active_tab = "Volume"
    elif arg_parser.find_arg(("-w", "--wifi")):
        active_tab = "Wi-Fi"
    elif arg_parser.find_arg(("-a", "--autostart")):
        active_tab = "Autostart"
    elif arg_parser.find_arg(("-b", "--bluetooth")):
        active_tab = "Bluetooth"
    elif arg_parser.find_arg(("-B", "--battery")):
        active_tab = "Battery"
    elif arg_parser.find_arg(("-d", "--display")):
        active_tab = "Display"
    elif arg_parser.find_arg(("-p", "--power")):
        active_tab = "Power"
    elif arg_parser.find_arg(("-u", "--usbguard")):
        active_tab = "USBGuard"

    return active_tab
