# Makefile for ESP8266 projects using arduino-cli

# --- Include and Configuration ---
# Include credentials from an untracked file, if it exists.
# Create a file named 'credentials.mk' with:
# WIFI_SSID := "your_ssid"
# WIFI_PASS := "your_password"
-include credentials.mk

# Default credentials. These are used if 'credentials.mk' is not found.
# They can be overridden from the command line, e.g., make WIFI_SSID="other_ssid"
WIFI_SSID ?= "your_default_ssid"
WIFI_PASS ?= "your_default_password"

# Board's Fully Qualified Board Name (FQBN).
BOARD_FQBN := esp8266:esp8266:nodemcuv2

# Serial port your board is connected to.
PORT ?= /dev/ttyUSB0

# Baud rate for the serial monitor.
BAUD_RATE := 115200

# --- Automatic Variables ---
CLI := arduino-cli
SKETCH_DIR := $(shell pwd)

# Define the build flags to pass to the compiler.
# The quoting is important to ensure the values are treated as strings.
BUILD_FLAGS := -DWIFI_SSID="\"$(WIFI_SSID)\"" -DWIFI_PASS="\"$(WIFI_PASS)\""

# --- Commands ---
.PHONY: all compile upload monitor clean help

# Default target: compile and upload the sketch.
all: upload

# Compile the sketch with the injected credentials.
compile:
	@echo "--- Compiling Sketch with SSID: $(WIFI_SSID) ---"
	$(CLI) compile --fqbn $(BOARD_FQBN) \
		--build-property "build.extra_flags=$(BUILD_FLAGS)" \
		$(SKETCH_DIR)

# Upload the compiled sketch to the board.
upload: compile
	@echo "--- Uploading Sketch to $(PORT) ---"
	$(CLI) upload -p $(PORT) --fqbn $(BOARD_FQBN) $(SKETCH_DIR)

# Open a serial monitor to view output from the board.
monitor:
	@echo "--- Starting Serial Monitor on $(PORT) (Press Ctrl+C to exit) ---"
	$(CLI) monitor -p $(PORT) --config baudrate=$(BAUD_RATE)

# Clean the build cache and remove build artifacts.
clean:
	@echo "--- Cleaning Build Artifacts ---"
	$(CLI) cache clean
	@rm -rf $(SKETCH_DIR)/build

