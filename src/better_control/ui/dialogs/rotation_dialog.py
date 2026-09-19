import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib # type:ignore
from better_control.tools.hyprland import set_hyprland_transform

class RotationConfirmDialog(Gtk.MessageDialog):
    def __init__(self, parent, display, previous_orientation, session, logging):
        super().__init__(
            transient_for=parent,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text="Keep display changes?"
        )
        
        self.display = display
        self.previous_orientation = previous_orientation
        self.session = session
        self.logging = logging
        self.countdown = 10
        self.timeout_id = None
        
        # Add buttons
        self.add_button("Revert back", Gtk.ResponseType.CANCEL)
        self.add_button("Keep changes", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.CANCEL)
        
        # Add countdown label
        self.countdown_label = Gtk.Label()
        self.countdown_label.set_text(f"Reverting in {self.countdown} seconds...")
        self.get_content_area().pack_end(self.countdown_label, True, True, 5)
        self.show_all()
        
        # Start countdown
        self.timeout_id = GLib.timeout_add(1000, self.update_countdown)
    
    def update_countdown(self):
        self.countdown -= 1
        if self.countdown <= 0:
            self.response(Gtk.ResponseType.CANCEL)
            return False
            
        self.countdown_label.set_text(f"Reverting in {self.countdown} seconds...")
        return True

    def do_response(self, response):
        # Clean up timer
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            
        # Handle revert
        if response == Gtk.ResponseType.CANCEL:
            if "Hyprland" in self.session:
                set_hyprland_transform(self.logging, self.display, self.previous_orientation)
