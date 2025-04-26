#!/usr/bin/env python3

import argparse
import sys
import os


def parse_args():
    """
    Parse command line arguments using Python's built-in argparse.
    Returns a dictionary of arguments for compatibility with existing code.
    """
    parser = argparse.ArgumentParser(
        description="Better Control - A GTK control panel for Linux",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Basic arguments
    parser.add_argument("-v", "--verbose", action="store_true", 
                      help="Enable verbose logging")
    parser.add_argument("-d", "--debug", action="store_true", 
                      help="Enable debug mode")
    parser.add_argument("-q", "--quiet", action="store_true", 
                      help="Quiet mode - suppress all output")
    parser.add_argument("-f", "--force", action="store_true", 
                      help="Force start, bypassing dependency checks")
    
    # Configuration
    parser.add_argument("-c", "--config", type=str, metavar="FILE",
                      help="Use alternative config file")
    parser.add_argument("-l", "--lang", type=str, metavar="LANG",
                      help="Set language (en, es, pt, fr, id, hi)")
    
    # UI options
    parser.add_argument("-s", "--size", type=str, metavar="WIDTHxHEIGHT",
                      help="Set window size (e.g., 900x600)")
    
    # Version info
    parser.add_argument("--version", action="store_true",
                      help="Show version information and exit")
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Handle version specially
    if args.version:
        print("Better Control 1.0.0")
        sys.exit(0)
    
    # Convert namespace to dictionary for compatibility with existing code
    args_dict = vars(args)
    
    return args_dict


if __name__ == "__main__":
    # Example usage
    args = parse_args()
    print(args)
