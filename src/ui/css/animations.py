import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib #type: ignore
import logging

def get_animations_css_path():
    """Returns the absolute path to the animations CSS file"""
    return os.path.join(os.path.dirname(__file__), "animations.css")

def get_spacing_css_path():
    """Returns the absolute path to the spacing CSS file"""
    return os.path.join(os.path.dirname(__file__), "spacing.css")

def animate_widget_show(widget, duration=250):
    """
    Animate widget appearance using CSS transitions with fade-in effect
    
    Args:
        widget: The GTK widget to animate
        duration: Animation duration in milliseconds (default: 250ms)
    """
    if widget is None:
        return
        
    try:
        style_context = widget.get_style_context()
        style_context.add_class("animate-show")
        
        # Remove animation class after animation completes
        GLib.timeout_add(duration, lambda: _safe_remove_class(style_context, "animate-show"))
        
        # Make sure widget is visible
        widget.show_all()
    except Exception as e:
        logging.warning(f"Animation error: {str(e)}")

def animate_fade_in(widget, duration=250):
    """
    Apply fade-in animation to widget with smooth transitions
    
    Args:
        widget: The GTK widget to animate
        duration: Animation duration in milliseconds (default: 250ms)
    """
    if widget is None:
        return
        
    try:
        style_context = widget.get_style_context()
        style_context.add_class("fade-in")
        
        # Remove animation class after animation completes
        GLib.timeout_add(duration, lambda: _safe_remove_class(style_context, "fade-in"))
        
        # Make sure widget is visible
        widget.show_all()
    except Exception as e:
        logging.warning(f"Animation error: {str(e)}")

def animate_slide_in_right(widget, duration=200):
    """
    Apply slide-in-from-right animation to widget
    
    Args:
        widget: The GTK widget to animate
        duration: Animation duration in milliseconds (default: 200ms)
    """
    if widget is None:
        return
        
    try:
        style_context = widget.get_style_context()
        style_context.add_class("slide-in-right")
        
        # Remove animation class after animation completes
        GLib.timeout_add(duration, lambda: _safe_remove_class(style_context, "slide-in-right"))
        
        # Make sure widget is visible
        widget.show_all()
    except Exception as e:
        logging.warning(f"Animation error: {str(e)}")

def animate_slide_in_left(widget, duration=200):
    """
    Apply slide-in-from-left animation to widget
    
    Args:
        widget: The GTK widget to animate
        duration: Animation duration in milliseconds (default: 200ms)
    """
    if widget is None:
        return
        
    try:
        style_context = widget.get_style_context()
        style_context.add_class("slide-in-left")
        
        # Remove animation class after animation completes
        GLib.timeout_add(duration, lambda: _safe_remove_class(style_context, "slide-in-left"))
        
        # Make sure widget is visible
        widget.show_all()
    except Exception as e:
        logging.warning(f"Animation error: {str(e)}")

def animate_icon_pulse(widget, icon_class, duration=500):
    """
    Apply pulse animation to an icon widget
    
    Args:
        widget: The GTK widget to animate
        icon_class: Type of icon (e.g., 'volume', 'wifi', 'bluetooth')
        duration: Animation duration in milliseconds (default: 500ms)
    """
    if widget is None:
        return
        
    try:
        style_context = widget.get_style_context()
        animation_class = f"{icon_class}-icon-animate"
        style_context.add_class(animation_class)
        
        # Remove animation class after animation completes
        GLib.timeout_add(duration, lambda: _safe_remove_class(style_context, animation_class))
    except Exception as e:
        logging.warning(f"Animation error: {str(e)}")

def animate_settings_gear(widget, active=True, duration=600):
    """
    Animate settings gear icon (rotation)
    
    Args:
        widget: The GTK image widget containing the gear icon
        active: Whether to activate or deactivate the animation
        duration: Animation duration in milliseconds (default: 600ms)
    """
    if widget is None:
        return
        
    try:
        style_context = widget.get_style_context()
        
        if active:
            style_context.remove_class("rotate-gear")
            style_context.add_class("rotate-gear-active")
        else:
            style_context.remove_class("rotate-gear-active")
            style_context.add_class("rotate-gear")
    except Exception as e:
        logging.warning(f"Animation error: {str(e)}")

def _safe_remove_class(style_context, class_name):
    """
    Safely remove a CSS class from a style context with error handling
    
    Args:
        style_context: The GTK style context
        class_name: CSS class name to remove
    
    Returns:
        False to ensure GLib.timeout_add doesn't repeat
    """
    if style_context is None:
        return False
    
    try:
        if style_context.has_class(class_name):
            style_context.remove_class(class_name)
    except Exception as e:
        logging.warning(f"Failed to remove style class {class_name}: {str(e)}")
    
    return False  # Don't repeat the timeout

def load_animations_css():
    """
    Load the animations CSS file into GTK
    
    Returns:
        The CSS provider object or None on failure
    """
    try:
        # Load animations CSS
        css_provider_animations = Gtk.CssProvider()
        css_path_animations = get_animations_css_path()
        
        if not os.path.exists(css_path_animations):
            logging.error(f"CSS file not found: {css_path_animations}")
            return None
            
        css_provider_animations.load_from_path(css_path_animations)

        # Load spacing CSS
        css_provider_spacing = Gtk.CssProvider()
        css_path_spacing = get_spacing_css_path()
        
        if not os.path.exists(css_path_spacing):
            logging.warning(f"Spacing CSS file not found: {css_path_spacing}")
        else:
            css_provider_spacing.load_from_path(css_path_spacing)

        screen = Gdk.Screen.get_default()
        if screen is not None:
            # Add animations CSS
            Gtk.StyleContext.add_provider_for_screen(
                screen,
                css_provider_animations,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            
            # Add spacing CSS with higher priority
            if os.path.exists(css_path_spacing):
                Gtk.StyleContext.add_provider_for_screen(
                    screen,
                    css_provider_spacing,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 10  # Higher priority
                )
        else:
            logging.warning("No display available for CSS animations")
            return None
            
        return css_provider_animations
    except Exception as e:
        logging.error(f"Could not load CSS animations: {str(e)}")
        return None
