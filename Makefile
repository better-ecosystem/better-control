PREFIX ?= /usr
BIN_DIR := $(PREFIX)/bin
DESKTOP_DIR := $(PREFIX)/share/applications
APP_NAME := control
SRC := src/control.py

install: build
	install -Dm755 $(SRC) $(BIN_DIR)/$(APP_NAME)
	install -Dm644 src/control.desktop $(DESKTOP_DIR)/control.desktop
	@echo "Better Control installed successfully!"

uninstall:
	rm -f $(BIN_DIR)/$(APP_NAME)
	rm -f $(DESKTOP_DIR)/control.desktop
	@echo "Better Control uninstalled successfully!"

build:
	@echo "No compilation needed for Python script."

.PHONY: install uninstall build
