import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib #type: ignore

def get_animations_css_path():
    return os.path.join(os.path.dirname(__file__), "animations.css")

def animate_widget_show(widget, duration=200):
    """Animate widget appearance using CSS transitions"""
    style_context = widget.get_style_context()
    style_context.add_class("animate-show")
    GLib.timeout_add(duration, lambda: style_context.remove_class("animate-show"))

def load_animations_css():
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(get_animations_css_path())

    try:
        screen = Gdk.Screen.get_default()
        if screen is not None:
            Gtk.StyleContext.add_provider_for_screen(
                screen,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        else:
            print("Warning: No display available for CSS animations")
    except Exception as e:
        print(f"Warning: Could not load CSS animations: {str(e)}")
