import paho.mqtt.client as mqtt
import serial
import time
import json

# --- Configuration ---
# IMPORTANT: Change this to the IP address of your Mac Mini.
BROKER_ADDRESS = "10.147.18.165" 
BROKER_PORT = 1883
TOPIC = "lab/battery_station_1/temperature"

# This is the typical serial port for an Arduino on a Raspberry Pi.
# You might need to change it. Check with 'ls /dev/tty*'
SERIAL_PORT = '/dev/ttyACM0' 
BAUD_RATE = 9600

def on_connect(client, userdata, flags, rc, properties=None):
    """Callback function for when the client connects to the broker."""
    if rc == 0:
        print("Connected successfully to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}\n")

def setup_serial():
    """Sets up and returns a serial connection object."""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        # Wait for the serial connection to initialize
        time.sleep(2) 
        print(f"Connected to Arduino on {SERIAL_PORT}")
        return ser
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {SERIAL_PORT}.")
        print(f"Details: {e}")
        print("Is the Arduino plugged in? Is the port correct?")
        return None

def main():
    """Main function to connect to MQTT and publish serial data."""
    # 1. Create MQTT client and assign callbacks
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pi_temp_sensor")
    client.on_connect = on_connect

    # 2. Connect to the MQTT broker
    try:
        client.connect(BROKER_ADDRESS, BROKER_PORT, 60)
    except ConnectionRefusedError:
        print("Connection refused. Is the broker running on the Mac Mini?")
        print(f"Is the IP address '{BROKER_ADDRESS}' correct?")
        return
    except OSError as e:
        print(f"Network error: {e}. Is the Mac Mini reachable?")
        return
        
    # 3. Set up the serial connection
    arduino_serial = setup_serial()
    if not arduino_serial:
        return # Exit if serial connection failed

    client.loop_start() # Start the network loop in the background

    # 4. Main loop to read from serial and publish
    try:
        while True:
            if arduino_serial.in_waiting > 0:
                line = arduino_serial.readline().decode('utf-8').strip()
                if line:
                    try:
                        # Best practice: Send data as a JSON object
                        f, c, hum = map(float, line.split(','))

                        payload = json.dumps({
                            "celcius": c,
                            "fahrenheit": f,
                            "humidity": hum
                        })
                        
                        result = client.publish(TOPIC, payload)
                        if result[0] == 0:
                            print(f"Published: {payload} to topic '{TOPIC}'")
                        else:
                            print(f"Failed to publish message.")
                    except ValueError:
                        print(f"Warning: Could not convert serial data '{line}' to a number. Skipping.")
            
            time.sleep(3) # Wait a second between readings

    except KeyboardInterrupt:
        print("Stopping publisher...")
    finally:
        client.loop_stop()
        client.disconnect()
        if arduino_serial and arduino_serial.is_open:
            arduino_serial.close()
        print("Disconnected and serial port closed.")

if __name__ == '__main__':
    main()
