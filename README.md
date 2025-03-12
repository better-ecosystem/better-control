# Better-Control
A gtk themed control panel for linux

This project is still under development , contriubutions such as ideas and feature requests towards project and testers are welcome.

# How to Install?
before install make sure u have `git` and `base-devel` installed
```
git clone https://github.com/quantumvoid0/better-control
cd better-control
sudo make install

```
# How to uninstall?
```
git clone https://github.com/quantumvoid0/better-control
cd better-control
sudo make uninstall

```
# Compatability
I have only tested this on Arch Linux with Hyprland so testers are welcome to test it out and share their review in discussions/issues. This should work on all arch based, fedora based and debian based distros (if u tested it pls leave a comment for any issues)

Probably will work on the stuff below 
| **Category**         | **Requirements**                                                                 |
|-----------------------|----------------------------------------------------------------------------------|
| **Operating System**  | Linux                                                                            |
| **Distributions**     | Arch based,Fedora Based,Debian Based                                                               |
| **Desktop Environments** (might work) | GNOME, XFCE, KDE Plasma (with GTK support), LXDE/LXQT, etc.                  |
| **Window Managers** (might work)   | Hyprland (def works), Sway, i3, Openbox, Fluxbox, etc.                             |
| **Display Protocol**     | Wayland (recommended), X11 (partial functionality)                               |

# Requirements
All these are installed during the installation process so dont worry abt it (except the hardware)

| **Category**             | **Requirements**                                                                 |
|--------------------------|----------------------------------------------------------------------------------|
| **Packages**             | `networkmanager` `bluez` `bluez-utils` `brightnessctl` `gtk4` `pipewire-pulse` `python-gobject` `python-pydbus`     |
| **Hardware**             | Wi-Fi adapter, Bluetooth adapter, audio hardware, backlight control device       |

# For WM users
make it so that `control` runs as a floating window to make it look cool if u want

hyprwm example
```
windowrulev2 = float, class:control
windowrulev2 = opacity 0.5 0.5,class:control
```
