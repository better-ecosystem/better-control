PREFIX ?= /usr/local
BIN_DIR := $(PREFIX)/bin
DESKTOP_DIR := $(PREFIX)/share/applications
CONFIG_DIR := $(HOME)/.config
SUDO ?= sudo

install: check_deps
	install -Dm755 src/control $(BIN_DIR)/control
	install -Dm644 src/control.desktop $(DESKTOP_DIR)/control.desktop
	rm -rf $(shell pwd)
	@echo "Better Control installed successfully!"

uninstall:
	rm -f $(BIN_DIR)/control
	rm -f $(DESKTOP_DIR)/control.desktop
	rm -rf $(shell pwd)  
	@echo "Better Control uninstalled successfully!"


check_deps:
	@if command -v pacman >/dev/null; then \
		$(SUDO) pacman -S --noconfirm --needed gtk4 networkmanager bluez bluez-utils pipewire-pulse brightnessctl python-gobject python-pydbus; \
	elif command -v apt >/dev/null; then \
		$(SUDO) apt update && $(SUDO) apt install -y libgtk-4-dev network-manager bluez bluez-utils pipewire-pulse brightnessctl python3-gi python3-dbus; \
	elif command -v dnf >/dev/null; then \
		$(SUDO) dnf install -y gtk4 NetworkManager bluez bluez-utils pipewire-pulse brightnessctl python3-gobject python3-dbus; \
	else \
		echo "Unsupported package manager. Please install dependencies manually." >&2; exit 1; \
	fi

.PHONY: install uninstall check_deps
