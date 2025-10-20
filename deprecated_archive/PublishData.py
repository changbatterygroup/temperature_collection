#!/usr/bin/python3

import paho.mqtt.client as mqtt
import serial
import time
import json
import logging
import sys

# --- Configuration ---
BROKER_ADDRESS = "FILL IN"
BROKER_PORT = "FILL IN"
TOPIC = "lab/battery_station_1/temperature"
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
CLIENT_ID = "pi_temp_sensor_1"
LOG_FILE = "mqtt_publisher.log"
RECONNECT_DELAY = 5

def setup_logging():
    """Configures logging to a file."""
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(log_formatter)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(file_handler)

def on_connect(client, userdata, flags, rc, properties=None):
    """Callback for when the client connects to the MQTT broker."""
    if rc == 0:
        logging.info("Successfully connected to MQTT Broker.")
    else:
        logging.error(f"Failed to connect to MQTT Broker, return code {rc}")

def on_disconnect(client, userdata, rc, properties=None):
    """Callback for when the client disconnects from the MQTT broker."""
    logging.warning(f"Disconnected from MQTT Broker with result code {rc}. Will attempt to reconnect.")

def setup_serial():
    """Initializes and returns a serial connection object, or None on failure."""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) # Allow time for the connection to establish
        logging.info(f"Successfully connected to Arduino on {SERIAL_PORT}")
        return ser
    except serial.SerialException as e:
        logging.error(f"Could not open serial port {SERIAL_PORT}: {e}")
        return None

def main():
    """Main execution loop."""
    setup_logging()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    try:
        client.connect(BROKER_ADDRESS, BROKER_PORT, 60)
    except Exception as e:
        logging.error(f"Initial MQTT connection failed: {e}. The script will still attempt to connect in the loop.")

    client.loop_start()
    
    arduino_serial = None

    try:
        while True:
            if not client.is_connected():
                try:
                    logging.info("Attempting to reconnect to MQTT broker...")
                    client.reconnect()
                except Exception as e:
                    logging.error(f"MQTT reconnection failed: {e}")
                time.sleep(RECONNECT_DELAY)
                continue

            if arduino_serial is None or not arduino_serial.is_open:
                arduino_serial = setup_serial()
                if not arduino_serial:
                    time.sleep(RECONNECT_DELAY)
                    continue
            
            try:
                if arduino_serial.in_waiting > 0:
                    line = arduino_serial.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue

                    parts = line.split(',')
                    if len(parts) != 3:
                        logging.warning(f"Received malformed data, skipping: '{line}'")
                        continue

                    try:
                        f_temp, c_temp, humidity = map(float, parts)
                        payload = json.dumps({
                            "celcius": c_temp,
                            "fahrenheit": f_temp,
                            "humidity": humidity
                        })
                        
                        result = client.publish(TOPIC, payload)
                        if result.rc == mqtt.MQTT_ERR_SUCCESS:
                            logging.info(f"Published: {payload}")
                        else:
                            logging.warning(f"Failed to publish message. MQTT-RC: {result.rc}")

                    except (ValueError, TypeError) as e:
                        logging.warning(f"Could not parse data '{line}', skipping. Error: {e}")
            
            except serial.SerialException as e:
                logging.error(f"Serial communication error: {e}. Closing port and will attempt to reconnect.")
                if arduino_serial:
                    arduino_serial.close()
                arduino_serial = None
            
            time.sleep(2)

    except KeyboardInterrupt:
        logging.info("Shutdown signal received.")
    finally:
        logging.info("Cleaning up and shutting down.")
        client.loop_stop()
        client.disconnect()
        if arduino_serial and arduino_serial.is_open:
            arduino_serial.close()
        logging.info("Disconnected and serial port closed.")

if __name__ == '__main__':
    main()

