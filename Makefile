# Makefile for Better Control
# This Makefile installs the application to /usr/share/better-control
# and creates launcher scripts in /usr/bin

PREFIX ?= /usr
INSTALL_DIR = $(DESTDIR)$(PREFIX)/share/better-control
BIN_DIR = $(DESTDIR)$(PREFIX)/bin

.PHONY: all install uninstall clean

all:
	@echo "Run 'make install' to install Better Control"

install:
	@echo "Installing Better Control..."
	# Create installation directories
	mkdir -p $(INSTALL_DIR)
	mkdir -p $(BIN_DIR)
	# Copy all project files to installation directory
	cp -r src/* $(INSTALL_DIR)/

	# Create and install the better-control executable script
	@echo "#!/usr/bin/env sh" > better-control
	@echo "python3 $(PREFIX)/share/better-control/better_control.py \$$@" >> better-control
	chmod +x better-control
	cp better-control $(BIN_DIR)/better-control

	# Create and install the control executable script
	cp better-control control
	cp control $(BIN_DIR)/control
	cp betterctl.sh $(BIN_DIR)/betterctl
	chmod +x $(BIN_DIR)/betterctl

	# Cleanup temporary files
	rm better-control control

	# Install desktop file
	mkdir -p $(DESTDIR)$(PREFIX)/share/applications
	sed 's|Exec=/usr/bin/control|Exec=/usr/bin/better-control|' \
		src/control.desktop > $(DESTDIR)$(PREFIX)/share/applications/better-control.desktop

	@echo "Installation complete!"

uninstall:
	@echo "Uninstalling Better Control..."
	rm -rf $(INSTALL_DIR)
	rm -f $(BIN_DIR)/better-control
	rm -f $(BIN_DIR)/control
	rm -f $(BIN_DIR)/betterctl
	rm -f $(DESTDIR)$(PREFIX)/share/applications/better-control.desktop
	@echo "Uninstallation complete!"

clean:
	@echo "Nothing to clean."