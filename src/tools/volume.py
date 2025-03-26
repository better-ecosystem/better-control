#!/usr/bin/env python3

import subprocess
from typing import List, Dict
import logging
import re

def get_volume() -> int:
    """Get current volume level

    Returns:
        int: Volume percentage
    """
    try:
        output = subprocess.getoutput("pactl get-sink-volume @DEFAULT_SINK@")
        volume = int(output.split("/")[1].strip().strip("%"))
        return volume
    except Exception as e:
        logging.error(f"Error getting volume: {e}")
        return 0

def set_volume(value: int) -> None:
    """Set volume level

    Args:
        value (int): Volume percentage
    """
    try:
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{value}%"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error setting volume: {e}")

def get_mute_state() -> bool:
    """Get mute state

    Returns:
        bool: True if muted, False otherwise
    """
    try:
        output = subprocess.getoutput("pactl get-sink-mute @DEFAULT_SINK@")
        return "yes" in output.lower()
    except Exception as e:
        logging.error(f"Error getting mute state: {e}")
        return False

def toggle_mute() -> None:
    """Toggle mute state"""
    try:
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error toggling mute: {e}")

def get_sinks() -> List[Dict[str, str]]:
    """Get list of audio sinks (output devices)

    Returns:
        List[Dict[str, str]]: List of sink dictionaries
    """
    try:
        output = subprocess.getoutput("pactl list sinks")
        sinks = []
        current_sink = {}
        for line in output.split("\n"):
            if line.startswith("Sink #"):
                if current_sink:
                    sinks.append(current_sink)
                current_sink = {"id": line.split("#")[1].strip()}
            elif ":" in line and current_sink:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key == "Name":
                    current_sink["name"] = value
                elif key == "Description":
                    current_sink["description"] = value

        if current_sink:
            sinks.append(current_sink)

        return sinks
    except Exception as e:
        logging.error(f"Error getting sinks: {e}")
        return []

def get_sources() -> List[Dict[str, str]]:
    """Get list of audio sources (input devices)

    Returns:
        List[Dict[str, str]]: List of source dictionaries
    """
    try:
        output = subprocess.getoutput("pactl list sources")
        sources = []
        current_source = {}
        for line in output.split("\n"):
            if line.startswith("Source #"):
                if current_source:
                    sources.append(current_source)
                current_source = {"id": line.split("#")[1].strip()}
            elif ":" in line and current_source:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key == "Name":
                    current_source["name"] = value
                elif key == "Description":
                    current_source["description"] = value

        if current_source:
            sources.append(current_source)

        return sources
    except Exception as e:
        logging.error(f"Error getting sources: {e}")
        return []

def get_applications() -> List[Dict[str, str]]:
    output = subprocess.getoutput("pactl list sink-inputs")
    apps = []
    current_app = {}

    for line in output.split("\n"):
        line = line.strip()
        print(f"Parsing Line: {line}")  # Debugging

        if line.startswith("Sink Input #"):
            if current_app:  # Finalize previous app before moving to a new one
                print("Finalizing previous app:", current_app)  
                if "name" in current_app and "volume" in current_app:
                    apps.append(current_app)  
                else:
                    print("Skipping app due to missing name or volume!", current_app)
            
            current_app = {"id": line.split("#")[1].strip()}  # New app entry
            print("New app detected with ID:", current_app["id"])

        elif "application.name" in line:
            current_app["name"] = line.split("=", 1)[1].strip().strip('"')
            print("Detected & Stored App Name:", current_app["name"])

        elif "media.name" in line and "name" not in current_app:
            current_app["name"] = line.split("=", 1)[1].strip().strip('"')
            print("Using Media Name:", current_app["name"])

        elif "application.process.binary" in line and "name" not in current_app:
            current_app["name"] = line.split("=", 1)[1].strip().strip('"')
            print("Using Process Binary Name:", current_app["name"])

        elif "Volume:" in line:
            print("Found Volume Line:", line)
            match = re.search(r"(\d+)%", line)
            if match:
                current_app["volume"] = int(match.group(1))
                print("Detected & Stored Volume:", current_app["volume"])
            else:
                print("Failed to parse volume from:", line)

    # Final app processing
    if current_app:
        print("Finalizing last app:", current_app)
        if "name" in current_app and "volume" in current_app:
            apps.append(current_app)
        else:
            print("Skipping last app due to missing name or volume!", current_app)

    print("Parsed Applications:", apps)
    return apps

def set_application_volume(app_id: str, value: int) -> None:
    """Set volume for a specific application

    Args:
        app_id (str): Application sink input ID
        value (int): Volume percentage
    """
    try:
        subprocess.run(["pactl", "set-sink-input-volume", app_id, f"{value}%"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error setting application volume: {e}")

def set_default_sink(sink_name: str) -> None:
    """Set default audio output device

    Args:
        sink_name (str): Sink name
    """
    try:
        subprocess.run(["pactl", "set-default-sink", sink_name], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error setting default sink: {e}")

def set_default_source(source_name: str) -> None:
    """Set default audio input device

    Args:
        source_name (str): Source name
    """
    try:
        subprocess.run(["pactl", "set-default-source", source_name], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error setting default source: {e}")

def get_mic_volume() -> int:
    """Get microphone volume level

    Returns:
        int: Volume percentage
    """
    try:
        output = subprocess.getoutput("pactl get-source-volume @DEFAULT_SOURCE@")
        volume = int(output.split("/")[1].strip().strip("%"))
        return volume
    except Exception as e:
        logging.error(f"Error getting mic volume: {e}")
        return 0

def set_mic_volume(value: int) -> None:
    """Set microphone volume level

    Args:
        value (int): Volume percentage
    """
    try:
        subprocess.run(["pactl", "set-source-volume", "@DEFAULT_SOURCE@", f"{value}%"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error setting mic volume: {e}")

def get_mic_mute_state() -> bool:
    """Get microphone mute state

    Returns:
        bool: True if muted, False otherwise
    """
    try:
        output = subprocess.getoutput("pactl get-source-mute @DEFAULT_SOURCE@")
        return "yes" in output.lower()
    except Exception as e:
        logging.error(f"Error getting mic mute state: {e}")
        return False

def toggle_mic_mute() -> None:
    """Toggle microphone mute state"""
    try:
        subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error toggling mic mute: {e}")
