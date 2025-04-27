from sys import stderr, stdout
from typing import Dict, List, Optional, TextIO, Tuple, Any

from tools.terminal import term_support_color


def sprint(file: Optional[TextIO], *args) -> None:
    """a 'print' statement macro with the 'file' parameter placed on the beggining

    Args:
        file (Optional[TextIO]): the file stream to output to
    """
    if file is None:
        file = stdout
    print(*args, file=file, flush=True)


def parse_args() -> Dict[str, Any]:
    """Parse command-line arguments and return a dictionary of parameters.
    
    Returns:
        Dict[str, Any]: Dictionary containing the parsed command-line arguments
    """
    import sys
    args = ArgParse(sys.argv)
    
    # Create a dictionary to store the parsed arguments
    parsed_args = {}
    
    # Help argument
    if args.find_arg(("-h", "--help")):
        args.print_help_msg(stdout)
    
    # Force argument
    parsed_args['force'] = args.find_arg(("-f", "--force"))
    
    # Window size
    size_option = args.option_arg(("-s", "--size"))
    if size_option:
        parsed_args['size'] = size_option
    
    # Language
    lang_option = args.option_arg(("-L", "--lang"))
    if lang_option:
        parsed_args['lang'] = lang_option
    
    # Minimal UI
    parsed_args['minimal'] = args.find_arg(("-m", "--minimal"))
    
    # Tab selection
    if args.find_arg(("-a", "--autostart")):
        parsed_args['start_tab'] = "autostart"
    elif args.find_arg(("-B", "--battery")):
        parsed_args['start_tab'] = "battery"
    elif args.find_arg(("-b", "--bluetooth")):
        parsed_args['start_tab'] = "bluetooth"
    elif args.find_arg(("-d", "--display")):
        parsed_args['start_tab'] = "display"
    elif args.find_arg(("-p", "--power")):
        parsed_args['start_tab'] = "power"
    elif args.find_arg(("-u", "--usbguard")):
        parsed_args['start_tab'] = "usbguard"
    elif args.find_arg(("-V", "--volume")) or args.find_arg(("-v", "")):
        parsed_args['start_tab'] = "volume"
    elif args.find_arg(("-w", "--wifi")):
        parsed_args['start_tab'] = "wifi"
    
    # Logging
    log_option = args.option_arg(("-l", "--log"))
    if log_option:
        parsed_args['log'] = log_option
    
    # Redact sensitive information
    parsed_args['redact'] = args.find_arg(("-r", "--redact"))
    
    return parsed_args


class ArgParse:
    def __init__(self, args: List[str]) -> None:
        self.__bin: str = ""
        self.__args: Dict[str, List[str | Dict[str, str]]] = {"long": [], "short": []}
        previous_arg_type: str = ""

        # ? This makes sure that detecting -ai as -a -i works
        # ? and also makes it not dependant on a lot of string operations
        for i, arg in enumerate(args):
            if i == 0:
                self.__bin = arg

            elif arg.startswith("--"):
                self.__args["long"].append(arg[2:])
                previous_arg_type = "long"

            elif arg.startswith("-"):
                self.__args["short"].append(arg[1:])
                previous_arg_type = "short"

            # ? If an arg reaches this statement,
            # ? that means the arg doesnt have a prefix of '-'.
            # ? Which would mean that it is an option
            elif previous_arg_type == "short":
                self.__args["short"].append({"option": arg})
            elif previous_arg_type == "long":
                self.__args["long"].append({"option": arg})

    def find_arg(self, __arg: Tuple[str, str]) -> bool:
        """tries to find 'arg' inside the argument list

        Args:
            arg (Tuple[str, str]): a tuple containing a short form of the arg, and long form

        Returns:
            bool: true if one of the arg is found, or false
        """
        # ? Check for short arg
        for arg in self.__args["short"]:
            if not isinstance(arg, Dict) and __arg[0][1:] in arg:
                return True

        # ? Check for long arg
        for arg in self.__args["long"]:
            if not isinstance(arg, Dict) and __arg[1][2:] == arg:
                return True
        return False

    def option_arg(self, __arg: Tuple[str, str]) -> Optional[str]:
        """tries to find and return an option from a given argument

        Args:
            arg (Tuple[str, str]): a tuple containing a short form of the arg, and long form

        Returns:
            Optional[str]: the option given or None
        """
        # ? Check for short arg
        for i, arg in enumerate(self.__args["short"]):
            if isinstance(arg, Dict):
                continue

            # ? Checks for equal signs, which allow us to check for -lo=a and -o=a
            if "=" in arg:
                eq_index: int = arg.index("=")
                split_arg: Tuple[str, str] = (arg[:eq_index], arg[eq_index + 1 :])

                # ? Check for -lo=a and -o=a
                if (len(split_arg[0]) > 1 and split_arg[0][-1] == __arg[0][1:]) or (
                    len(split_arg[0]) == 1 and split_arg[0][0] == __arg[0][1:]
                ):
                    return split_arg[1]

            # ? Check for -oa
            if len(arg) > 1 and arg[0] == __arg[0][1:]:
                return arg[1:]

            # ? Check for -lo a
            if len(arg) > 1:
                for _, c in enumerate(arg):
                    if c == __arg[0][1:] and i + 1 < len(self.__args["short"]):
                        next_arg = self.__args["short"][i + 1]
                        if isinstance(next_arg, Dict):
                            return next_arg["option"]

            # ? Check for -o a
            if arg == __arg[0][1:] and i + 1 < len(self.__args["short"]):
                next_arg = self.__args["short"][i + 1]

                if isinstance(next_arg, Dict):
                    return next_arg["option"]

        # ? Check for long arg
        for i, arg in enumerate(self.__args["long"]):
            if isinstance(arg, Dict):
                continue

            if "=" in arg:
                eq_index: int = arg.index("=")
                split_arg: Tuple[str, str] = (arg[:eq_index], arg[eq_index + 1 :])

                # ? Check for --option=a
                if split_arg[0] == __arg[1][2:]:
                    return split_arg[1]

            # ? Check for --option a
            if arg == __arg[1][2:] and i + 1 < len(self.__args["long"]):
                next_arg = self.__args["long"][i + 1]

                if isinstance(next_arg, Dict):
                    return next_arg["option"]
        return None

    def arg_print(self, msg: str) -> None:
        sprint(self.__help_stream, msg)

    def print_help_msg(self, stream: Optional[TextIO]):
        self.__help_stream = stream
        use_colors = term_support_color()

        # Define colors if terminal supports them
        if use_colors:
            # Color definitions
            RESET = "\033[0m"
            BOLD = "\033[1m"
            UNDERLINE = "\033[4m"
            CYAN = "\033[36m"
            GREEN = "\033[32m"
            YELLOW = "\033[33m"
            BLUE = "\033[34m"
            MAGENTA = "\033[35m"
            GRAY = "\033[90m"
            WHITE = "\033[97m"
        else:
            # No colors if terminal doesn't support them
            RESET = BOLD = UNDERLINE = CYAN = GREEN = YELLOW = BLUE = MAGENTA = GRAY = WHITE = ""

        # Header
        self.arg_print(f"\n{BOLD}{CYAN}╭────────────────────────────────────────────────────────────────╮{RESET}")
        self.arg_print(f"{BOLD}{CYAN}│                         BETTER CONTROL                         │{RESET}")
        self.arg_print(f"{BOLD}{CYAN}╰────────────────────────────────────────────────────────────────╯{RESET}\n")

        # Usage
        self.arg_print(f"{BOLD}USAGE:{RESET}")
        self.arg_print(f"  {WHITE}better-control {GRAY}[options]{RESET} \n  {WHITE}control {GRAY}[options]\n")

        # Options header
        self.arg_print(f"{BOLD}OPTIONS:{RESET}")

        # General options
        self.arg_print(f"{BOLD}{UNDERLINE}General:{RESET}")
        self.arg_print(f"  {GREEN}-h, --help{RESET}                      Prints this help message")
        self.arg_print(f"  {GREEN}-f, --force{RESET}                     Makes the app force to have all dependencies installed")
        self.arg_print(f"  {GREEN}-s, --size{RESET} {YELLOW}<intxint>{RESET}            Sets a custom window size")
        self.arg_print(f"  {GREEN}-L, --lang{RESET}                      Sets the language of the app (en,es,pt)")
        self.arg_print(f"  {GREEN}-m, --minimal{RESET}                   Hides the notebook tabs and only shows the selected tab content\n")

        # Tab selection options
        self.arg_print(f"{BOLD}{UNDERLINE}Tab Selection:{RESET}")
        self.arg_print(f"  {BLUE}-a, --autostart{RESET}                 Starts with the autostart tab open")
        self.arg_print(f"  {BLUE}-B, --battery{RESET}                   Starts with the battery tab open")
        self.arg_print(f"  {BLUE}-b, --bluetooth{RESET}                 Starts with the bluetooth tab open")
        self.arg_print(f"  {BLUE}-d, --display{RESET}                   Starts with the display tab open")
        self.arg_print(f"  {BLUE}-p, --power{RESET}                     Starts with the power tab open")
        self.arg_print(f"  {BLUE}-u, --usbguard{RESET}                  Starts with the usbguard tab open")
        self.arg_print(f"  {BLUE}-V, --volume{RESET}                    Starts with the volume tab open")
        self.arg_print(f"  {BLUE}-v{RESET}                              Also starts with the volume tab open")
        self.arg_print(f"  {BLUE}-w, --wifi{RESET}                      Starts with the wifi tab open\n")

        # Logging options
        self.arg_print(f"{BOLD}{UNDERLINE}Logging:{RESET}")
        self.arg_print(f"  {MAGENTA}-l, --log{RESET} {YELLOW}<lvl/file>{RESET}            The program will either log to a file if given a file path,")
        self.arg_print(f"                                  or output to stdout based on the log level if given")
        self.arg_print(f"                                  a value between 0 and 3.")
        self.arg_print(f"  {MAGENTA}-r, --redact{RESET}                    Redact sensitive information from logs\n")

        # Footer
        self.arg_print(f"{BOLD}{CYAN}╭────────────────────────────────────────────────────────────────╮{RESET}")
        self.arg_print(f"{BOLD}{CYAN}│         https://github.com/quantumvoid0/better-control         │{RESET}")
        self.arg_print(f"{BOLD}{CYAN}╰────────────────────────────────────────────────────────────────╯{RESET}\n")

        if stream == stderr:
            exit(1)
        else:
            exit(0)
