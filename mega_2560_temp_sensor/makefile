# Makefile for compiling and uploading Arduino sketches using arduino-cli
#
# USAGE:
#   make           - Compiles and uploads the code (default action).
#   make upload    - Compiles and uploads the code.
#   make compile   - Compiles the code without uploading.
#   make monitor   - Opens the serial monitor.
#   make help      - Displays this help message.
#
#-----------------------------------------------------------------------------

# --- User-configurable variables ---
# Update these to match your setup if needed.

# The Fully Qualified Board Name. Find with `arduino-cli board listall`
BOARD_FQBN := arduino:avr:mega

# The serial port your Arduino is connected to.
# The `?=` means you can override it from the command line, e.g., `make upload PORT=/dev/ttyACM1`
PORT ?= /dev/ttyACM0

# The baud rate for the serial monitor. Must match Serial.begin() in your code.
BAUD_RATE := 9600

# The directory containing the .ino file to compile.
SKETCH_DIR := $(pwd)


# --- Automatic variables (should not need to be changed) ---

# The arduino-cli command
CLI := arduino-cli


# --- Makefile Targets ---

# Phony targets are actions that don't represent actual files.
.PHONY: all compile upload monitor help

# The default target, executed when you just run `make`.
all: upload

# Target to compile the sketch.
compile:
	@echo "--- Compiling sketch: $(SKETCH_DIR) for $(BOARD_FQBN) ---"
	@$(CLI) compile --fqbn $(BOARD_FQBN) $(SKETCH_DIR)
	@echo "--- Compilation successful ---"

# Target to compile and upload the sketch.
upload:
	@echo "--- Compiling and uploading sketch: $(SKETCH_DIR) ---"
	@$(CLI) compile --fqbn $(BOARD_FQBN) --upload -p $(PORT) $(SKETCH_DIR)
	@echo "--- Upload complete ---"

# Target to open the serial monitor.
monitor:
	@echo "--- Opening serial monitor on $(PORT) at $(BAUD_RATE) baud (Ctrl+C to exit) ---"
	@$(CLI) monitor -p $(PORT) --config baudrate=$(BAUD_RATE)

# Target to display help information.
help:
	@echo "Arduino CLI Makefile"
	@echo "--------------------"
	@echo "Available commands:"
	@echo "  make or make upload    - Compiles and uploads the sketch to $(BOARD_FQBN) on $(PORT)"
	@echo "  make compile           - Verifies and compiles the sketch without uploading"
	@echo "  make monitor           - Opens the serial monitor"
	@echo "  make help              - Shows this message"

