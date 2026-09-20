#!/usr/bin/env python3

import gi  # type: ignore
import subprocess
import threading
import time

from better_control.logger import LogLevel, Logger
from better_control.translations import English, Spanish

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # type: ignore

from better_control.tools.volume import (
    get_volume,
    set_volume,
    get_mute_state,
    toggle_mute,
    get_sinks,
    get_sources,
    get_applications,
    set_application_volume,
    move_application_to_sink,
    set_default_sink,
    set_default_source,
    get_mic_volume,
    set_mic_volume,
    get_mic_mute_state,
    toggle_mic_mute,
    get_sink_identifier_by_id,
    get_application_mute_state,
    toggle_application_mute,
    get_source_outputs,
    get_application_mic_mute_state,
    toggle_application_mic_mute,
    get_application_mic_volume,
    set_application_mic_volume,
)


class VolumeTab(Gtk.Box):
    """Volume settings tab"""

    def __init__(self, logging: Logger, txt: English|Spanish):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.txt = txt
        self.logging = logging
        self.set_margin_start(15)
        self.set_margin_end(15)
        self.set_margin_top(15)
        self.set_margin_bottom(15)
        self.set_hexpand(True)
        self.set_vexpand(True)

        # Critical - ensure this widget is fully visible in the parent application\'s notebook
        self.set_visible(True)
        self.set_no_show_all(False)

        # Create lock for thread safety
        self._lock = threading.RLock()
        self._output_changing_lock = threading.Lock() # Lock to prevent re-entrancy in on_output_changed

        self.is_visible = False  # Track tab visibility

        # Initialize flags and references to prevent segfaults
        self._volume_change_timeout_id = None
        self._mic_volume_change_timeout_id = None
        self._app_volume_timeouts = {}
        self._app_mic_volume_timeouts = {}
        self._pending_app_volumes = {}
        self._pending_app_mic_volumes = {}
        self.pulse_thread = None
        self._is_being_destroyed = False

        # Get the default icon theme
        self.icon_theme = Gtk.IconTheme.get_default()

        # Create header box with title
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header_box.set_hexpand(True)
        header_box.set_visible(True)  # Ensure header is visible

        # Create title box with icon and label
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_box.set_visible(True)  # Ensure title is visible

        # Add volume icon
        volume_icon = Gtk.Image.new_from_icon_name(
            "audio-volume-high-symbolic", Gtk.IconSize.DIALOG

        )

        self.animate_icon(volume_icon)

        title_box.pack_start(self.icon_event_box, False, False, 0)

        # Add title
        volume_label = Gtk.Label()
        volume_label.set_markup(
            f"<span weight='bold' size='large'>{self.txt.volume_title}</span>"
        )
        volume_label.set_halign(Gtk.Align.START)
        title_box.pack_start(volume_label, False, False, 0)

        header_box.pack_start(title_box, True, True, 0)

        self.pack_start(header_box, False, False, 0)

        # Create notebook for tabbed interface
        self.notebook = Gtk.Notebook()
        self.notebook.set_vexpand(True)
        self.notebook.set_visible(True)  # Ensure notebook is visible

        # Create tabs for different categories
        self.create_output_tab()
        self.create_input_tab()
        self.create_apps_output_tab()
        self.create_apps_input_tab()

        self.pack_start(self.notebook, True, True, 0)

        # Initialize pulse audio monitoring variables
        self.should_monitor = False  # Don't start monitoring until tab is visible

        # Initialize UI state
        self.update_device_lists()
        self.update_mute_buttons()

        # Start with initial data refresh
        self.update_volumes()

        # Always start monitoring on initialization to ensure the app works
        # even if map signal doesn't fire correctly
        self.should_monitor = True
        self.start_pulse_monitoring()

        # Connect map/unmap signals for smart monitoring when tab becomes visible/hidden
        self.connect("map", self.on_tab_shown)
        self.connect("unmap", self.on_tab_hidden)

        # Register for audio device change notifications
        from better_control.tools.bluetooth import add_audio_routing_callback
        self._audio_device_changed_cb = self._on_audio_device_changed
        self.last_bluetooth_device_update_time = 0
        self.update_interval_bluetooth = 1
        add_audio_routing_callback(self._audio_device_changed_cb, logging)

        # Connect destroy signal for proper cleanup
        self.connect_destroy_signal()

    def create_output_tab(self):
        """Create speaker/output device tab"""
        output_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        output_tab.set_margin_start(12)
        output_tab.set_margin_end(12)
        output_tab.set_margin_top(12)
        output_tab.set_margin_bottom(12)
        output_tab.set_visible(True)  # Ensure tab content is visible

        # Output device selection
        device_frame = Gtk.Frame()
        device_frame.set_shadow_type(Gtk.ShadowType.NONE)
        device_frame.set_visible(True)

        device_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        device_box.set_margin_start(12)
        device_box.set_margin_end(12)
        device_box.set_margin_top(12)
        device_box.set_margin_bottom(12)

        output_label = Gtk.Label()
        output_label.set_markup(f"<b>{self.txt.volume_output_device}</b>")
        output_label.set_halign(Gtk.Align.START)
        device_box.pack_start(output_label, False, True, 0)

        combo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        device_label = Gtk.Label(label=f"{self.txt.volume_device}:")
        self.output_combo = Gtk.ComboBoxText()
        self.output_combo.connect("changed", self.on_output_changed)
        combo_box.pack_start(device_label, False, True, 0)
        combo_box.pack_start(self.output_combo, True, True, 0)
        device_box.pack_start(combo_box, False, True, 0)

        device_frame.add(device_box)
        output_tab.pack_start(device_frame, False, False, 0)

        # Volume control
        volume_frame = Gtk.Frame()
        volume_frame.set_shadow_type(Gtk.ShadowType.IN)
        volume_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        volume_box.set_margin_start(12)
        volume_box.set_margin_end(12)
        volume_box.set_margin_top(12)
        volume_box.set_margin_bottom(12)

        # Volume title
        volume_title = Gtk.Label()
        volume_title.set_markup(f"<b>{self.txt.volume_speaker_volume}</b>")
        volume_title.set_halign(Gtk.Align.START)
        volume_box.pack_start(volume_title, False, True, 0)

        # Volume control (slider + mute button) in horizontal box
        volume_control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        # Volume slider
        self.volume_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 1
        )
        self.volume_scale.set_value(get_volume(self.logging))
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        # Improve slider responsiveness
        self._configure_slider(self.volume_scale)
        volume_control_box.pack_start(self.volume_scale, True, True, 0)

        # Mute button
        self.mute_button = Gtk.Button()
        self.update_mute_button()
        self.mute_button.connect("clicked", self.on_mute_clicked)
        volume_control_box.pack_start(self.mute_button, False, False, 0)

        volume_box.pack_start(volume_control_box, True, True, 0)

        # Quick volume presets
        quick_label = Gtk.Label()
        quick_label.set_markup(f"<small>{self.txt.volume_quick_presets}</small>")
        quick_label.set_halign(Gtk.Align.START)
        volume_box.pack_start(quick_label, False, True, 0)

        quick_volume_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        volumes = [0, 25, 50, 75, 100]
        for vol in volumes:
            button = Gtk.Button(label=f"{vol}%")
            button.set_relief(Gtk.ReliefStyle.NONE)  # Make buttons less prominent
            button.get_style_context().add_class("flat")
            button.connect("clicked", self.on_quick_volume_clicked, vol)
            quick_volume_box.pack_start(button, True, True, 0)
        volume_box.pack_start(quick_volume_box, False, True, 0)

        volume_frame.add(volume_box)
        output_tab.pack_start(volume_frame, False, True, 0)

        # Create tab label with icon and text
        tab_label = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        output_icon = Gtk.Image.new_from_icon_name("audio-speakers-symbolic", Gtk.IconSize.MENU)
        output_text = Gtk.Label(label=self.txt.volume_speakers)
        tab_label.pack_start(output_icon, False, False, 0)
        tab_label.pack_start(output_text, False, False, 0)
        tab_label.show_all()

        # Add the output tab to the notebook with combined label
        output_tab_index = self.notebook.append_page(output_tab, tab_label)

        # Set tooltip on the tab widget itself
        tab = self.notebook.get_nth_page(output_tab_index)
        if tab:
            tab.set_tooltip_text(self.txt.volume_tab_tooltip)

    def animate_icon(self, volume_icon):
        """Setup volume icon hover animations"""
        self.volume_icon = volume_icon

        # Wrap icon in event box for hover detection
        self.icon_event_box = Gtk.EventBox()
        self.icon_event_box.add(volume_icon)

        # Add CSS classes for hover effects
        ctx = volume_icon.get_style_context()
        ctx.add_class("volume-icon")

        def on_enter(widget, event):
            ctx.add_class("volume-icon-animate")

        def on_leave(widget, event):
            ctx.remove_class("volume-icon-animate")

        self.icon_event_box.connect("enter-notify-event", on_enter)
        self.icon_event_box.connect("leave-notify-event", on_leave)

        # Set initial state
        volume_icon.set_from_icon_name("audio-volume-high-symbolic", Gtk.IconSize.DIALOG)

    def create_input_tab(self):
        """Create microphone/input device tab"""
        input_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        input_tab.set_margin_start(12)
        input_tab.set_margin_end(12)
        input_tab.set_margin_top(12)
        input_tab.set_margin_bottom(12)

        # Input device selection
        device_frame = Gtk.Frame()
        device_frame.set_shadow_type(Gtk.ShadowType.NONE)

        device_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        device_box.set_margin_start(12)
        device_box.set_margin_end(12)
        device_box.set_margin_top(12)
        device_box.set_margin_bottom(12)

        input_label = Gtk.Label()
        input_label.set_markup(f"<b>{self.txt.microphone_tab_input_device}</b>")
        input_label.set_halign(Gtk.Align.START)
        device_box.pack_start(input_label, False, True, 0)

        combo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        device_label = Gtk.Label(label=f"{self.txt.volume_device}:")
        self.input_combo = Gtk.ComboBoxText()
        self.input_combo.connect("changed", self.on_input_changed)
        combo_box.pack_start(device_label, False, True, 0)
        combo_box.pack_start(self.input_combo, True, True, 0)
        device_box.pack_start(combo_box, False, True, 0)

        device_frame.add(device_box)
        input_tab.pack_start(device_frame, False, False, 0)

        # Microphone control
        mic_frame = Gtk.Frame()
        mic_frame.set_shadow_type(Gtk.ShadowType.IN)
        mic_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        mic_box.set_margin_start(12)
        mic_box.set_margin_end(12)
        mic_box.set_margin_top(12)
        mic_box.set_margin_bottom(12)

        # Mic title
        mic_title = Gtk.Label()
        mic_title.set_markup(f"<b>{self.txt.microphone_tab_volume}</b>")
        mic_title.set_halign(Gtk.Align.START)
        mic_box.pack_start(mic_title, False, True, 0)

        # Mic control (slider + mute button) in horizontal box
        mic_control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        # Mic slider
        self.mic_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.mic_scale.set_value(get_mic_volume(self.logging))
        self.mic_scale.connect("value-changed", self.on_mic_volume_changed)
        # Improve slider responsiveness
        self._configure_slider(self.mic_scale)
        mic_control_box.pack_start(self.mic_scale, True, True, 0)

        # Mic mute button
        self.mic_mute_button = Gtk.Button()
        self.update_mic_mute_button()
        self.mic_mute_button.connect("clicked", self.on_mic_mute_clicked)
        mic_control_box.pack_start(self.mic_mute_button, False, False, 0)

        mic_box.pack_start(mic_control_box, True, True, 0)

        # Quick mic volume presets
        quick_label = Gtk.Label()
        quick_label.set_markup(f"<small>{self.txt.volume_quick_presets}</small>")
        quick_label.set_halign(Gtk.Align.START)
        mic_box.pack_start(quick_label, False, True, 0)

        quick_mic_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        volumes = [0, 25, 50, 75, 100]
        for vol in volumes:
            button = Gtk.Button(label=f"{vol}%")
            button.set_relief(Gtk.ReliefStyle.NONE)  # Make buttons less prominent
            button.get_style_context().add_class("flat")
            button.connect("clicked", self.on_quick_mic_volume_clicked, vol)
            quick_mic_box.pack_start(button, True, True, 0)
        mic_box.pack_start(quick_mic_box, False, True, 0)

        mic_frame.add(mic_box)
        input_tab.pack_start(mic_frame, False, True, 0)

        # Create tab label with icon and text
        tab_label = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        input_icon = Gtk.Image.new_from_icon_name("audio-input-microphone-symbolic", Gtk.IconSize.MENU)
        input_text = Gtk.Label(label=self.txt.microphone_tab_microphone)
        tab_label.pack_start(input_icon, False, False, 0)
        tab_label.pack_start(input_text, False, False, 0)
        tab_label.show_all()

        # Add the input tab to the notebook with combined label
        input_tab_index = self.notebook.append_page(input_tab, tab_label)

        # Set tooltip on the tab widget itself
        tab = self.notebook.get_nth_page(input_tab_index)
        if tab:
            tab.set_tooltip_text(self.txt.microphone_tab_tooltip)

    def create_apps_output_tab(self):
        """Create application output volume tab"""
        apps_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        apps_tab.set_margin_start(12)
        apps_tab.set_margin_end(12)
        apps_tab.set_margin_top(12)
        apps_tab.set_margin_bottom(12)

        # Title
        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{self.txt.app_output_volume}</b>")
        title_label.set_halign(Gtk.Align.START)
        apps_tab.pack_start(title_label, False, False, 0)

        # Scrollable window for app list
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_window.set_vexpand(True)
        scroll_window.set_margin_top(6)

        # Container for app controls
        self.app_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.app_box.set_margin_start(6)
        self.app_box.set_margin_end(6)
        self.app_box.set_margin_top(6)
        self.app_box.set_margin_bottom(6)

        scroll_window.add(self.app_box)
        apps_tab.pack_start(scroll_window, True, True, 0)

        # Create tab label with icon and text
        tab_label = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        apps_icon = Gtk.Image.new_from_icon_name("multimedia-volume-control-symbolic", Gtk.IconSize.MENU)
        apps_text = Gtk.Label(label=self.txt.app_output_title)
        tab_label.pack_start(apps_icon, False, False, 0)
        tab_label.pack_start(apps_text, False, False, 0)
        tab_label.show_all()

        # Add the apps tab to the notebook with combined label
        apps_tab_index = self.notebook.append_page(apps_tab, tab_label)

        # Set tooltip on the tab widget itself
        tab = self.notebook.get_nth_page(apps_tab_index)
        if tab:
            tab.set_tooltip_text(self.txt.app_output_tab_tooltip)

    def create_apps_input_tab(self):
        """Create application input (microphone) volume tab"""
        mic_apps_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        mic_apps_tab.set_margin_start(12)
        mic_apps_tab.set_margin_end(12)
        mic_apps_tab.set_margin_top(12)
        mic_apps_tab.set_margin_bottom(12)

        # Title
        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{self.txt.app_input_volume}</b>")
        title_label.set_halign(Gtk.Align.START)
        mic_apps_tab.pack_start(title_label, False, False, 0)

        # Scrollable window for app list
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_window.set_vexpand(True)
        scroll_window.set_margin_top(6)

        # Container for app controls
        self.mic_app_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.mic_app_box.set_margin_start(6)
        self.mic_app_box.set_margin_end(6)
        self.mic_app_box.set_margin_top(6)
        self.mic_app_box.set_margin_bottom(6)

        scroll_window.add(self.mic_app_box)
        mic_apps_tab.pack_start(scroll_window, True, True, 0)

        # Create tab label with icon and text
        tab_label = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        mic_apps_icon = Gtk.Image.new_from_icon_name("microphone-sensitivity-medium-symbolic", Gtk.IconSize.MENU)
        mic_apps_text = Gtk.Label(label=self.txt.app_input_title)
        tab_label.pack_start(mic_apps_icon, False, False, 0)
        tab_label.pack_start(mic_apps_text, False, False, 0)
        tab_label.show_all()

        # Add the mic apps tab to the notebook with combined label
        mic_apps_tab_index = self.notebook.append_page(mic_apps_tab, tab_label)

        # Set tooltip on the tab widget itself
        tab = self.notebook.get_nth_page(mic_apps_tab_index)
        if tab:
            tab.set_tooltip_text(self.txt.app_input_tab_tooltip)

    def on_tab_shown(self, widget):
        """Called when the tab becomes visible"""
        self.is_visible = True

        # Make sure the tab and all its contents are visible
        self.set_visible(True)
        self.show_all()

        self.update_volumes()

        # Only start monitoring if not already active
        if (
            not self.should_monitor
            or not self.pulse_thread
            or not self.pulse_thread.is_alive()
        ):
            self.should_monitor = True
            self.start_pulse_monitoring()

    def on_tab_hidden(self, widget):
        """Called when the tab is hidden"""
        self.is_visible = False

    def start_pulse_monitoring(self):
        """Start the PulseAudio monitoring thread for real-time updates"""
        # Only start if not already monitoring
        if self.pulse_thread is None or not self.pulse_thread.is_alive():
            self.should_monitor = True
            self.pulse_thread = threading.Thread(
                target=self.monitor_pulse_events, daemon=True
            )
            self.pulse_thread.start()
            self.logging.log(LogLevel.Info, "Started periodic (500ms) audio monitoring")
        else:
            self.logging.log(LogLevel.Info, "Audio monitoring already active")

    def stop_pulse_monitoring(self):
        """Stop monitoring pulse events"""
        # Set flag to indicate we should stop
        self.should_monitor = False

        # Use lock to safely access thread data
        with self._lock:
            # Make sure thread terminates properly
            thread_ref = self.pulse_thread
            if thread_ref is not None and thread_ref.is_alive():
                try:
                    # Wait a short time for the thread to exit naturally
                    # Don't join in the main thread, as that could block UI
                    def join_thread_safe():
                        try:
                            thread_ref.join(timeout=0.3)
                        except Exception as e:
                            self.logging.log(LogLevel.Error, f"Error joining pulse thread: {e}")
                        return False  # Don't repeat

                    # Schedule joining the thread
                    GLib.timeout_add(100, join_thread_safe)
                except Exception as e:
                    self.logging.log(LogLevel.Error, f"Error stopping pulse thread: {e}")

            # Clear the reference regardless
            self.pulse_thread = None

    def monitor_pulse_events(self):
        """Background thread for monitoring pulse audio state"""
        counter = 0
        last_error_time = 0
        error_count = 0

        while self.should_monitor:
            try:
                # Check if we're being destroyed or monitoring should stop
                if not self.should_monitor or hasattr(self, '_is_being_destroyed') and self._is_being_destroyed:
                    break

                # Use locks to prevent race conditions with the main thread
                with self._lock:
                    # Every 10th iteration (roughly 1 second), do a deeper refresh
                    if counter % 10 == 0:
                        if self.is_visible:
                            # Use GLib.idle_add to ensure UI updates happen on the main thread
                            GLib.idle_add(self.refresh_audio_state, counter)

                # Sleep a bit to prevent high CPU usage
                # Use smaller sleep increments and check should_monitor regularly
                for _ in range(5):
                    if not self.should_monitor or hasattr(self, '_is_being_destroyed') and self._is_being_destroyed:
                        break
                    time.sleep(0.02)  # 20ms * 5 = 100ms

                counter += 1

            except RuntimeError as e:
                # Handle RuntimeError separately (often due to thread issues)
                self.logging.log(LogLevel.Error, f"Runtime error in pulse monitoring thread: {e}")
                # Exit the thread if we're having serious issues
                if "object at has been deleted" in str(e):
                    self.logging.log(LogLevel.Error, "Critical error in pulse thread - exiting")
                    break
                time.sleep(0.5)  # Sleep to prevent tight loop

            except Exception as e:
                current_time = time.time()
                # Limit error logging to prevent log spam
                if current_time - last_error_time > 5:  # Reset error count after 5 seconds
                    error_count = 0
                    last_error_time = current_time

                error_count += 1
                if error_count <= 3:  # Log only first 3 errors in a 5 second window
                    self.logging.log(LogLevel.Error, f"Error in pulse monitoring thread: {e}")

                # Sleep after error to prevent tight loop
                time.sleep(0.5)

        self.logging.log(LogLevel.Debug, "Pulse audio monitoring thread exited")

        # Clear thread reference when it exits
        with self._lock:
            if hasattr(self, 'pulse_thread') and self.pulse_thread is not None:
                self.pulse_thread = None

    def refresh_audio_state(self, counter):
        """Update audio state based on a counter (to distribute heavy operations)"""
        try:
            # Get current notebook page to optimize updates
            current_page = self.notebook.get_current_page()

            # Always update volume and mute states unless user is actively adjusting them
            updating_volume = hasattr(self, "_volume_change_timeout_id") and self._volume_change_timeout_id
            updating_mic = hasattr(self, "_mic_volume_change_timeout_id") and self._mic_volume_change_timeout_id

            # Update main volume if not being adjusted by user and on output tab
            if not updating_volume and (current_page == 0 or counter % 4 == 0):
                self.volume_scale.set_value(get_volume(self.logging))
                self.update_mute_button()

            # Update mic volume if not being adjusted by user and on input tab
            if not updating_mic and (current_page == 1 or counter % 4 == 0):
                self.mic_scale.set_value(get_mic_volume(self.logging))
                self.update_mic_mute_button()

            # Distribute heavier operations across different refresh cycles
            # Always update device lists on a 6-cycle interval (3 seconds)
            if counter % 6 == 0:
                self.update_device_lists()

            # Update application lists based on current tab
            if current_page == 2 or (counter % 4 == 0 and current_page != 3):
                self.update_application_list()

            if current_page == 3 or (counter % 4 == 2 and current_page != 2):
                self.update_mic_application_list()

        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error refreshing audio state: {e}")

        return False  # Don't repeat via GLib (we're manually scheduling)

    def update_device_lists(self):
        """Update output and input device lists and sync dropdown with the actual default sink."""
        try:
            self.logging.log(LogLevel.Info, "Updating audio device lists...")

            # Get the currently active sink
            current_sink = subprocess.getoutput("pactl get-default-sink").strip()
            self.logging.log(
                LogLevel.Info, f"Current active output sink: {current_sink}"
            )

            # Output devices (speakers/headphones)
            self.output_combo.remove_all()
            sinks = get_sinks(self.logging)

            if not sinks:
                self.logging.log(LogLevel.Warn, "No output sinks found!")
                self.output_combo.append("no-sink", "No Output Devices Found")
                self.output_combo.set_active(0)
            else:
                active_index = -1
                for i, sink in enumerate(sinks):
                    self.logging.log(
                        LogLevel.Info,
                        f"Adding output sink: {sink['identifier']} ({sink['description']})",
                    )
                    self.output_combo.append(sink["identifier"], sink["description"])
                    if sink["active"]:
                        active_index = i

                if active_index != -1:
                    self.output_combo.set_active(active_index)
                else:
                    self.output_combo.set_active(0)  # Default to first item

            # Get the currently active input source (microphone)
            current_source = subprocess.getoutput("pactl get-default-source").strip()
            self.logging.log(
                LogLevel.Info, f"Current active input source: {current_source}"
            )

            # Input devices (microphones)
            self.input_combo.remove_all()
            sources = get_sources(self.logging)

            if not sources:
                self.logging.log(LogLevel.Warn, "No input sources found!")
                self.input_combo.append("no-source", "No Input Devices Found")
                self.input_combo.set_active(0)
            else:
                active_index = -1
                source_count = 0  # Track actual position in dropdown
                for i, source in enumerate(sources):
                    if "monitor" not in source["name"].lower():  # Skip monitor sources
                        self.logging.log(
                            LogLevel.Info,
                            f"Adding input source: {source['name']} ({source['description']})",
                        )
                        self.input_combo.append(source["name"], source["description"])
                        if source["name"] == current_source:
                            active_index = source_count
                        source_count += 1

                if active_index != -1:
                    self.input_combo.set_active(active_index)
                else:
                    self.input_combo.set_active(0)  # Default to first item

        except Exception as e:
            self.logging.log(LogLevel.Error, f"Failed updating device lists: {e}")

    def update_mute_buttons(self):
        """Update mute button labels"""
        self.update_mute_button()

        # Update mic mute button
        self.update_mic_mute_button()

    def update_mute_button(self):
        """Update speaker mute button icon"""
        speaker_muted = get_mute_state(self.logging)
        if speaker_muted:
            mute_icon = Gtk.Image.new_from_icon_name(
                "audio-volume-muted-symbolic", Gtk.IconSize.BUTTON
            )
            self.mute_button.set_tooltip_text(self.txt.volume_unmute_speaker)
        else:
            mute_icon = Gtk.Image.new_from_icon_name(
                "audio-volume-high-symbolic", Gtk.IconSize.BUTTON
            )
            self.mute_button.set_tooltip_text(self.txt.volume_mute_speaker)
        self.mute_button.set_image(mute_icon)

    def _configure_slider(self, scale):
        """Configure a volume slider with common settings for better performance"""
        scale.set_draw_value(True)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.set_increments(1, 5)  # Small step, page increment
        scale.set_size_request(150, -1)  # Set minimum width
        scale.set_hexpand(True)  # Allow slider to expand horizontally
        return scale

    def update_application_list(self):
        """Update application volume controls"""
        # Remove existing controls
        for child in self.app_box.get_children():
            self.app_box.remove(child)

        apps = get_applications(self.logging)

        if not apps:
            # Show "No applications playing audio" message
            no_apps_label = Gtk.Label()
            no_apps_label.set_markup(f"<i>{self.txt.app_output_no_apps}</i>")
            no_apps_label.set_halign(Gtk.Align.START)
            no_apps_label.set_margin_top(5)
            no_apps_label.set_margin_bottom(5)
            self.app_box.pack_start(no_apps_label, False, True, 0)
            self.app_box.show_all()
            return

        # Get sinks once and prepare sink options
        sinks = get_sinks(self.logging)
        sink_options = [(s["identifier"], s["description"]) for s in sinks] if sinks else []

        for app in apps:
            card = self._create_app_output_card(app, sink_options)
            self.app_box.pack_start(card, False, True, 0)

        self.app_box.show_all()

    def _create_app_output_card(self, app, sink_options):
        """Create a UI card widget for a single application's output"""
        card = Gtk.Frame()
        card.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        card.set_margin_bottom(8)

        app_grid = Gtk.Grid()
        app_grid.set_margin_start(10)
        app_grid.set_margin_end(10)
        app_grid.set_margin_top(8)
        app_grid.set_margin_bottom(8)
        app_grid.set_column_spacing(12)
        app_grid.set_row_spacing(4)

        # Icon
        icon = self._resolve_app_icon(app)
        app_grid.attach(icon, 0, 0, 1, 2)

        # Name
        name_label = Gtk.Label()
        name_label.set_markup(f"<b>{app['name']}</b>")
        name_label.set_halign(Gtk.Align.START)
        name_label.set_hexpand(True)
        app_grid.attach(name_label, 1, 0, 1, 1)

        # Controls box
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self._configure_slider(scale)
        scale.set_value(app["volume"])
        scale.connect("value-changed", self.on_app_volume_changed, app["id"])
        controls_box.pack_start(scale, True, True, 0)

        app_muted = get_application_mute_state(app["id"], self.logging)
        app_mute_button = Gtk.Button()
        if app_muted:
            mute_icon = Gtk.Image.new_from_icon_name("audio-volume-muted-symbolic", Gtk.IconSize.BUTTON)
            app_mute_button.set_tooltip_text(self.txt.app_output_unmute)
        else:
            mute_icon = Gtk.Image.new_from_icon_name("audio-volume-high-symbolic", Gtk.IconSize.BUTTON)
            app_mute_button.set_tooltip_text(self.txt.app_output_mute)
        app_mute_button.set_image(mute_icon)
        app_mute_button.connect("clicked", self.on_app_mute_clicked, app["id"])
        controls_box.pack_start(app_mute_button, False, False, 0)

        app_grid.attach(controls_box, 1, 1, 1, 1)

        # Device selector box
        device_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        device_label = Gtk.Label(label=f"{self.txt.volume_output}:")
        device_label.set_halign(Gtk.Align.START)

        output_combo = Gtk.ComboBoxText()
        output_combo.set_tooltip_text(self.txt.volume_output_combo_tooltip)
        output_combo.set_hexpand(True)
        for sink_identifier, sink_desc in sink_options:
            output_combo.append(sink_identifier, sink_desc)

        current_sink_identifier = ""
        if "sink" in app:
            current_sink_identifier = get_sink_identifier_by_id(app["sink"], self.logging)

        # Set active sink
        active_found = False
        for idx, (sink_identifier, sink_desc) in enumerate(sink_options):
            if sink_identifier == current_sink_identifier:
                output_combo.set_active(idx)
                active_found = True
                self.logging.log(LogLevel.Debug, f"Active sink is {sink_identifier}")
                break
        if not active_found and sink_options:
            output_combo.set_active(0)

        output_combo.connect("changed", self.on_app_output_changed, app["id"])

        device_box.pack_start(device_label, False, False, 0)
        device_box.pack_start(output_combo, True, True, 0)

        app_grid.attach(device_box, 0, 2, 2, 1)

        card.add(app_grid)
        return card

    def _resolve_app_icon(self, app):
        """Resolve best available icon for app"""
        icon = None

        # App's own icon field
        if "icon" in app:
            icon_name = app["icon"]
            if self.is_visible:
                self.logging.log(LogLevel.Debug, f"Trying app icon: {icon_name}")
            if icon_name and self.icon_exists(icon_name):
                icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)

        # Binary name as icon
        if not icon and "binary" in app:
            binary_name = app["binary"].lower()
            if self.is_visible:
                self.logging.log(LogLevel.Debug, f"Trying binary icon: {binary_name}")
            if binary_name and self.icon_exists(binary_name):
                icon = Gtk.Image.new_from_icon_name(binary_name, Gtk.IconSize.LARGE_TOOLBAR)

        # Normalized app name as icon
        if not icon:
            app_icon_name = app.get("name", "").lower().replace(" ", "-")
            if self.is_visible:
                self.logging.log(LogLevel.Debug, f"Trying normalized name icon: {app_icon_name}")
            if app_icon_name and self.icon_exists(app_icon_name):
                icon = Gtk.Image.new_from_icon_name(app_icon_name, Gtk.IconSize.LARGE_TOOLBAR)

        # Known mappings
        if not icon:
            app_name = app.get("name", "").lower()
            icon_map = {
                "firefox": "firefox",
                "chrome": "google-chrome",
                "chromium": "chromium",
                "spotify": "spotify",
                "mpv": "mpv",
                "vlc": "vlc",
                "telegram": "telegram",
                "discord": "discord",
                "steam": "steam",
                "brave": "brave",
                "audacious": "audacious",
                "clementine": "clementine",
                "deadbeef": "deadbeef",
                "rhythmbox": "rhythmbox",
            }
            for key, candidate_icon in icon_map.items():
                if key in app_name and self.icon_exists(candidate_icon):
                    icon = Gtk.Image.new_from_icon_name(candidate_icon, Gtk.IconSize.LARGE_TOOLBAR)
                    break

        # Fallback
        if not icon:
            icon = Gtk.Image.new_from_icon_name("audio-x-generic-symbolic", Gtk.IconSize.LARGE_TOOLBAR)

        return icon

    def update_volumes(self):
        """Update volume displays"""
        try:
            # Update main volume
            self.volume_scale.set_value(get_volume(self.logging))

            # Update mic volume
            self.mic_scale.set_value(get_mic_volume(self.logging))

            # Update mute buttons
            self.update_mute_buttons()

            # Update all application lists
            self.update_application_list()
            self.update_mic_application_list()

        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error updating volumes: {e}")

    def on_volume_changed(self, scale):
        """Handle volume scale changes"""
        value = int(scale.get_value())

        # Use debounce mechanism to avoid excessive updates
        if hasattr(self, "_volume_change_timeout_id") and self._volume_change_timeout_id:
            GLib.source_remove(self._volume_change_timeout_id)

        # Set a small timeout to aggregate rapid changes
        # Store the current value for the delayed handler
        self._pending_volume = value
        self._volume_change_timeout_id = GLib.timeout_add(50, self._apply_volume_change)

    def _apply_volume_change(self):
        """Apply the volume change after debouncing"""
        if hasattr(self, "_pending_volume"):
            value = self._pending_volume
            # Update the volume immediately when user changes slider
            set_volume(value, self.logging)
            # Force update of mute button to ensure it's in sync when unmuting via volume change
            if value > 0 and get_mute_state(self.logging):
                GLib.idle_add(self.update_mute_button)

        # Reset the timeout ID
        self._volume_change_timeout_id = None
        return False  # Don't repeat

    def on_mute_clicked(self, button):
        """Handle mute button clicks"""
        toggle_mute(self.logging)
        self.update_mute_buttons()

    def on_quick_volume_clicked(self, button, volume):
        """Handle quick volume button clicks"""
        set_volume(volume, self.logging)
        self.volume_scale.set_value(volume)

    def on_mic_volume_changed(self, scale):
        """Handle microphone volume scale changes"""
        value = int(scale.get_value())

        # Use debounce mechanism to avoid excessive updates
        if hasattr(self, "_mic_volume_change_timeout_id") and self._mic_volume_change_timeout_id:
            GLib.source_remove(self._mic_volume_change_timeout_id)

        # Set a small timeout to aggregate rapid changes
        # Store the current value for the delayed handler
        self._pending_mic_volume = value
        self._mic_volume_change_timeout_id = GLib.timeout_add(50, self._apply_mic_volume_change)

    def _apply_mic_volume_change(self):
        """Apply the microphone volume change after debouncing"""
        if hasattr(self, "_pending_mic_volume"):
            value = self._pending_mic_volume
            # Update the volume with the aggregated value
            set_mic_volume(value, self.logging)

        # Reset the timeout ID
        self._mic_volume_change_timeout_id = None
        return False  # Don't repeat

    def on_mic_mute_clicked(self, button):
        """Handle microphone mute button clicks"""
        toggle_mic_mute(self.logging)
        self.update_mic_mute_button()

    def on_quick_mic_volume_clicked(self, button, volume):
        """Handle quick microphone volume button clicks"""
        set_mic_volume(volume, self.logging)
        self.mic_scale.set_value(volume)

    def on_output_changed(self, combo):
        """Handle output device selection changes"""
        self.logging.log(LogLevel.Info, "Output device audio changed")

        # Prevent re-entrancy if already processing a change
        if not self._output_changing_lock.acquire(blocking=False):
            self.logging.log(LogLevel.Debug, "on_output_changed is already active, skipping.")
            return

        try:
            active_id = combo.get_active_id()
            if active_id is None or active_id == "no-sink":
                self.logging.log(LogLevel.Debug, "No valid sink selected.")
                return

            device_id, port_name = active_id.split("####")
            if not device_id:
                self.logging.log(LogLevel.Warn, "Invalid device_id after split.")
                return

            current_index = combo.get_active()
            self.logging.log(LogLevel.Debug, f"Attempting to set sink to: {device_id} with port {port_name}")

            # Run the sink change in a separate thread to avoid blocking the UI thread
            def do_set_sink():
                try:
                    success = set_default_sink(device_id, port_name, self.logging)

                    def update_ui_after_set_sink():
                        if not success:
                            self.logging.log(LogLevel.Error, f"Failed to switch to device {device_id}")
                            if combo.get_active() != current_index: # Check if user hasn't changed it again
                                combo.set_active(current_index)
                            return

                        # Verify the change took effect
                        # This check should also be non-blocking or handled carefully
                        new_sink_check_output = subprocess.getoutput("pactl get-default-sink").strip()
                        if new_sink_check_output != device_id:
                            self.logging.log(
                                LogLevel.Error,
                                f"Device switch verification failed (expected: {device_id}, got: {new_sink_check_output})",
                            )
                            if combo.get_active() != current_index:
                                combo.set_active(current_index)
                            return

                        self.logging.log(LogLevel.Info, f"Successfully switched to sink: {device_id}")
                        # Force refresh of application outputs on the main thread
                        self.update_application_list() # This itself should use GLib.idle_add for its UI parts

                    GLib.idle_add(update_ui_after_set_sink)

                except Exception as e_thread:
                    self.logging.log(LogLevel.Error, f"Error in do_set_sink thread: {e_thread}")
                    # Ensure UI reversion happens on the main thread
                    def revert_ui_on_error():
                        if combo.get_active() != current_index:
                             combo.set_active(current_index)
                    GLib.idle_add(revert_ui_on_error)
                finally:
                    # Release lock in the thread that acquired it, after all operations
                    # However, the primary lock is released in the main path.
                    # This secondary lock management needs careful thought if do_set_sink is complex.
                    # For now, the main lock is released outside this thread.
                    pass
            
            # Offload the potentially blocking operation
            thread = threading.Thread(target=do_set_sink)
            thread.daemon = True
            thread.start()

        except Exception as e:
            self.logging.log(LogLevel.Error, f"Error in on_output_changed: {e}")
            # Fallback: ensure lock is released if an error occurs before thread start
            # self._output_changing_lock.release() # Releasing here might be too early if thread is started
        finally:
            # Release the lock after initiating the process
            # The actual sink change and UI updates are now threaded or scheduled via GLib.idle_add
            # Consider if lock should be released by the thread or GLib.idle_add callback
            GLib.timeout_add(100, self._release_output_changing_lock) # Release after a short delay

    def _release_output_changing_lock(self):
        if self._output_changing_lock.locked():
            self._output_changing_lock.release()
        return False # Do not repeat

    def on_input_changed(self, combo):
        """Handle input device selection changes"""
        device_id = combo.get_active_id()
        if device_id:
            set_default_source(device_id, self.logging)

    def on_app_volume_changed(self, scale, app_id):
        """Handle application volume changes"""
        value = int(scale.get_value())

        # Use per-app debouncing mechanism with a dictionary
        # Create the tracking dictionary if it doesn't exist
        if not hasattr(self, "_app_volume_timeouts"):
            self._app_volume_timeouts = {}
            self._pending_app_volumes = {}

        # Cancel previous timeout if exists
        if app_id in self._app_volume_timeouts and self._app_volume_timeouts[app_id]:
            GLib.source_remove(self._app_volume_timeouts[app_id])

        # Store the pending value and create a new timeout
        self._pending_app_volumes[app_id] = value
        self._app_volume_timeouts[app_id] = GLib.timeout_add(
            50,
            lambda: self._apply_app_volume_change(app_id)
        )

    def _apply_app_volume_change(self, app_id):
        """Apply the application volume change after debouncing"""
        if hasattr(self, "_pending_app_volumes") and app_id in self._pending_app_volumes:
            value = self._pending_app_volumes[app_id]
            # Apply the volume change
            set_application_volume(app_id, value, self.logging)

        # Reset the timeout ID
        if hasattr(self, "_app_volume_timeouts"):
            self._app_volume_timeouts[app_id] = None

        return False  # Don't repeat

    def on_app_output_changed(self, combo, app_id):
        """Handle application output device changes"""

        if combo.get_active_id() is None or combo.get_active_id() == "no-sink":
            return

        device_id, port_name = combo.get_active_id().split("####")

        if device_id:
            try:
                # First check if the application still exists
                app_exists = False
                apps = get_applications(self.logging)
                for app in apps:
                    if app["id"] == app_id:
                        app_exists = True
                        break

                if app_exists:
                    move_application_to_sink(app_id, device_id, port_name, self.logging)
                    self.logging.log(
                        LogLevel.Info,
                        f"Moving application {app_id} to sink {device_id}",
                    )
                else:
                    self.logging.log(
                        LogLevel.Warn,
                        f"Cannot move application {app_id}, it no longer exists",
                    )
                    # Force refresh to remove stale apps
                    self.update_application_list()
            except Exception as e:
                self.logging.log(
                    LogLevel.Error, f"Failed moving application to sink: {e}"
                )
                # Force refresh to ensure UI is in sync with actual state
                self.update_application_list()

    def on_app_mute_clicked(self, button, app_id):
        """Handle application mute button clicks"""
        toggle_application_mute(app_id, self.logging)
        self.update_application_list()

    def on_app_mic_volume_changed(self, scale, app_id):
        """Handle application microphone volume changes"""
        value = int(scale.get_value())

        # Use per-app debouncing mechanism with a dictionary
        # Create the tracking dictionary if it doesn't exist
        if not hasattr(self, "_app_mic_volume_timeouts"):
            self._app_mic_volume_timeouts = {}
            self._pending_app_mic_volumes = {}

        # Cancel previous timeout if exists
        if app_id in self._app_mic_volume_timeouts and self._app_mic_volume_timeouts[app_id]:
            GLib.source_remove(self._app_mic_volume_timeouts[app_id])

        # Store the pending value and create a new timeout
        self._pending_app_mic_volumes[app_id] = value
        self._app_mic_volume_timeouts[app_id] = GLib.timeout_add(
            50,
            lambda: self._apply_app_mic_volume_change(app_id)
        )

    def _apply_app_mic_volume_change(self, app_id):
        """Apply the application microphone volume change after debouncing"""
        if hasattr(self, "_pending_app_mic_volumes") and app_id in self._pending_app_mic_volumes:
            value = self._pending_app_mic_volumes[app_id]
            # Apply the volume change
            set_application_mic_volume(app_id, value, self.logging)

        # Reset the timeout ID
        if hasattr(self, "_app_mic_volume_timeouts"):
            self._app_mic_volume_timeouts[app_id] = None

        return False  # Don't repeat

    def on_app_mic_mute_clicked(self, button, app_id):
        """Handle application microphone mute button clicks"""
        toggle_application_mic_mute(app_id, self.logging)
        self.update_mic_application_list()

    def icon_exists(self, icon_name):
        """Check if an icon exists in the icon theme"""
        return self.icon_theme.has_icon(icon_name)

    def update_mic_mute_button(self):
        """Update microphone mute button"""
        mic_muted = get_mic_mute_state(self.logging)
        if mic_muted:
            mute_icon = Gtk.Image.new_from_icon_name(
                "microphone-disabled-symbolic", Gtk.IconSize.BUTTON
            )
            self.mic_mute_button.set_tooltip_text(self.txt.microphone_tab_unmute_microphone)
        else:
            mute_icon = Gtk.Image.new_from_icon_name(
                "microphone-sensitivity-high-symbolic", Gtk.IconSize.BUTTON
            )
            self.mic_mute_button.set_tooltip_text(self.txt.microphone_tab_mute_microphone)
        self.mic_mute_button.set_image(mute_icon)

    def update_mic_application_list(self):
        """Update microphone application list"""
        # Remove existing controls
        for child in self.mic_app_box.get_children():
            self.mic_app_box.remove(child)

        # Add controls for each application using microphone
        mic_apps = get_source_outputs(self.logging)
        if not mic_apps:
            # Show "No applications using microphone" message
            no_mic_apps_label = Gtk.Label()
            no_mic_apps_label.set_markup(f"<i>{self.txt.app_input_no_apps}</i>")
            no_mic_apps_label.set_halign(Gtk.Align.START)
            no_mic_apps_label.set_margin_top(5)
            no_mic_apps_label.set_margin_bottom(5)
            self.mic_app_box.pack_start(no_mic_apps_label, False, True, 0)
        else:
            for app in mic_apps:
                # Create a card-like container for each app
                card = Gtk.Frame()
                card.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
                card.set_margin_bottom(8)

                # Main container within card
                app_grid = Gtk.Grid()
                app_grid.set_margin_start(10)
                app_grid.set_margin_end(10)
                app_grid.set_margin_top(8)
                app_grid.set_margin_bottom(8)
                app_grid.set_column_spacing(12)
                app_grid.set_row_spacing(4)

                # App icon
                icon = None

                # Try icon from app info first
                if "icon" in app:
                    icon_name = app["icon"]
                    if self.is_visible:
                        self.logging.log(LogLevel.Debug, f"Trying app icon: {icon_name}")
                    if self.icon_exists(icon_name):
                        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)

                # If icon is not valid or not found, try binary name as icon
                if not icon and "binary" in app:
                    binary_name = app["binary"].lower()
                    if self.is_visible:
                        self.logging.log(LogLevel.Debug, f"Trying binary icon: {binary_name}")
                    if self.icon_exists(binary_name):
                        icon = Gtk.Image.new_from_icon_name(binary_name, Gtk.IconSize.LARGE_TOOLBAR)

                # Last resort: fallback to generic audio icon
                if not icon:
                    icon = Gtk.Image.new_from_icon_name("audio-input-microphone-symbolic", Gtk.IconSize.LARGE_TOOLBAR)

                # Position icon at top
                app_grid.attach(icon, 0, 0, 1, 2)

                # App name with bold styling
                name_label = Gtk.Label()
                name_label.set_markup(f"<b>{app['name']}</b>")
                name_label.set_halign(Gtk.Align.START)
                name_label.set_hexpand(True)
                app_grid.attach(name_label, 1, 0, 1, 1)

                # Volume controls in second row
                controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

                # Volume slider
                volume = get_application_mic_volume(app["id"], self.logging)
                scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
                self._configure_slider(scale)
                scale.set_value(volume)
                scale.connect("value-changed", self.on_app_mic_volume_changed, app["id"])
                controls_box.pack_start(scale, True, True, 0)

                # Mic mute button
                app_mic_muted = get_application_mic_mute_state(app["id"], self.logging)
                app_mic_mute_button = Gtk.Button()
                if app_mic_muted:
                    mute_icon = Gtk.Image.new_from_icon_name("microphone-disabled-symbolic", Gtk.IconSize.BUTTON)
                    app_mic_mute_button.set_tooltip_text(self.txt.app_input_unmute)
                else:
                    mute_icon = Gtk.Image.new_from_icon_name("microphone-sensitivity-high-symbolic", Gtk.IconSize.BUTTON)
                    app_mic_mute_button.set_tooltip_text(self.txt.app_input_mute)
                app_mic_mute_button.set_image(mute_icon)
                app_mic_mute_button.connect("clicked", self.on_app_mic_mute_clicked, app["id"])
                controls_box.pack_start(app_mic_mute_button, False, False, 0)

                app_grid.attach(controls_box, 1, 1, 1, 1)

                card.add(app_grid)
                self.mic_app_box.pack_start(card, False, True, 0)

        self.mic_app_box.show_all()

    def connect_destroy_signal(self):
        """Connect to the destroy signal to clean up resources when the widget is destroyed"""

        def on_destroy(*args):
            self.logging.log(
                LogLevel.Info, "Volume tab is being destroyed, cleaning up resources"
            )
            self.stop_pulse_monitoring()

        self.connect("destroy", on_destroy)

    def _on_audio_device_changed(self, sink_name):
        """Callback when audio routing changes"""
        current_time = time.time()
        if current_time > self.last_bluetooth_device_update_time + self.update_interval_bluetooth:
            return

        self.last_bluetooth_device_update_time = current_time
        GLib.idle_add(self.update_device_lists)
        if sink_name:
            self.logging.log(LogLevel.Info,
                f"Audio device changed to: {sink_name}")

    def __del__(self):
        """Clean up resources when tab is destroyed"""
        self.stop_pulse_monitoring()
        # Clean up any other resources
        self.logging.log(LogLevel.Debug, "Volume tab resources cleaned up")

    def on_destroy(self, widget):
        """Clean up resources when tab is destroyed"""
        self.stop_pulse_monitoring()

        # Remove audio device change callback
        if hasattr(self, '_audio_device_changed_cb'):
            from better_control.tools.bluetooth import remove_audio_routing_callback
            remove_audio_routing_callback(self._audio_device_changed_cb, self.logging)
            del self._audio_device_changed_cb

        # Cancel any pending timeouts
        if hasattr(self, "_volume_change_timeout_id") and self._volume_change_timeout_id:
            GLib.source_remove(self._volume_change_timeout_id)
            self._volume_change_timeout_id = None
        if hasattr(self, "_mic_volume_change_timeout_id") and self._mic_volume_change_timeout_id:
            GLib.source_remove(self._mic_volume_change_timeout_id)
            self._mic_volume_change_timeout_id = None

        # Clean up application volume timeouts
        if hasattr(self, "_app_volume_timeouts"):
            for app_id, timeout_id in self._app_volume_timeouts.items():
                if timeout_id:
                    GLib.source_remove(timeout_id)
            self._app_volume_timeouts = {}

        # Clean up application mic volume timeouts
        if hasattr(self, "_app_mic_volume_timeouts"):
            for app_id, timeout_id in self._app_mic_volume_timeouts.items():
                if timeout_id:
                    GLib.source_remove(timeout_id)
            self._app_mic_volume_timeouts = {}

    def show_all(self):
        """Ensure tab and all its contents are shown correctly"""
        # Make sure the notebook and all its tabs are shown
        self.notebook.show_all()

        # Make sure all children are visible
        for child in self.get_children():
            child.show_all()

        # Make sure we are visible
        super().show_all()
