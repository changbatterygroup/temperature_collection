-include credentials.mk

ifndef WIFI_SSID
    $(error WIFI_SSID is not defined. Please set it in credentials.mk)
endif
ifndef WIFI_PASS
    $(error WIFI_PASS is not defined. Please set it in credentials.mk)
endif
ifndef OTA_HOSTNAME
    $(error OTA_HOSTNAME is not defined. Please set it in credentials.mk)
endif
ifndef OTA_PASSWORD
    $(error OTA_PASSWORD is not defined. Please set it in credentials.mk)
endif
ifndef LOCAL_ESP_IP
    $(error LOCAL_ESP_IP is not defined. Please set it in credentials.mk)
endif
ifndef SERVER_IP
    $(error SERVER_IP is not defined. Please set it in credentials.mk)
endif
ifndef API_KEY
    $(error API_KEY is not defined. Please set it in credentials.mk)
endif
ifndef TOPIC
    $(error TOPIC is not defined. Please set it in credentials.mk)
endif

BOARD_FQBN := esp8266:esp8266:nodemcuv2

PORT ?= /dev/ttyUSB0

BAUD_RATE := 115200

CLI := arduino-cli
SKETCH_DIR := $(shell pwd)

BUILD_FLAGS := \
    -DWIFI_SSID="\"$(WIFI_SSID)\"" \
    -DWIFI_PASS="\"$(WIFI_PASS)\"" \
    -DOTA_HOSTNAME="\"$(OTA_HOSTNAME)\"" \
    -DOTA_PASSWORD="\"$(OTA_PASSWORD)\"" \
    -DSERVER_IP="\"$(SERVER_IP)\"" \
    -DAPI_KEY="\"$(API_KEY)\"" \
    -DTOPIC="\"$(TOPIC)\""

.PHONY: all compile upload upload-ota monitor clean help

all: upload-ota

help:
	@echo "------------------------------------------------------------------"
	@echo " ESP8266 Makefile with OTA Support"
	@echo "------------------------------------------------------------------"
	@echo "  make help          - Show this help message."
	@echo "  make compile       - Compiles the sketch."
	@echo "  make upload        - Compiles and uploads via USB."
	@echo "  make upload-ota    - (Default) Compiles and uploads wirelessly (OTA)."
	@echo "  make monitor       - Open the serial monitor."
	@echo "  make monitor-ota   - monitor over the network using telnet."
	@echo "  make clean         - Clean build artifacts."
	@echo "------------------------------------------------------------------"

compile:
	@echo "--- Compiling Sketch with SSID: $(WIFI_SSID) ---"
	$(CLI) compile --fqbn $(BOARD_FQBN) \
		--build-property "build.extra_flags=$(BUILD_FLAGS)" \
		$(SKETCH_DIR)

upload: compile
	@echo "--- Uploading Sketch to $(PORT) via USB ---"
	@if [ -z "$(PORT)" ]; then echo "Error: Serial port not found. Please specify with PORT="; exit 1; fi
	$(CLI) upload -p $(PORT) --fqbn $(BOARD_FQBN) $(SKETCH_DIR)

upload-ota: compile
	@echo "--- Uploading Sketch to $(LOCAL_ESP_IP) via OTA ---"
	$(CLI) upload --port $(LOCAL_ESP_IP) \
		--fqbn $(BOARD_FQBN) \
		--upload-field password=$(OTA_PASSWORD) \
		$(SKETCH_DIR)

monitor:
	@echo "--- Starting Serial Monitor on $(PORT) (Press Ctrl+A, K, then X to exit) ---"
	@if [ -z "$(PORT)" ]; then echo "Error: Serial port not found. Please specify with PORT="; exit 1; fi
	$(CLI) monitor -p $(PORT) --config baudrate=$(BAUD_RATE)

clean:
	@echo "--- Cleaning Build Artifacts ---"
	$(CLI) cache clean
	@rm -rf $(SKETCH_DIR)/build