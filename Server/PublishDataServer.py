import os
import json
import logging
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='../logs/PublishDataServer.log')

load_dotenv()

SECRET_API_KEY = os.getenv("CLIENT_API_KEY")
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))

MQTT_BROKER_ADDRESS = os.getenv("BROKER_ADDRESS")
MQTT_BROKER_PORT = int(os.getenv("BROKER_PORT"))
MQTT_CLIENT_ID = os.getenv("CLIENT_ID")

required_vars = {
    "CLIENT_API_KEY": SECRET_API_KEY,
    "HOST": HOST,
    "PORT": PORT,
    "MQTT_BROKER_ADDRESS": MQTT_BROKER_ADDRESS,
    "MQTT_BROKER_PORT": MQTT_BROKER_PORT,
    "MQTT_CLIENT_ID": MQTT_CLIENT_ID
}

for var, val in required_vars.items():
    if not val:
        logging.critical(f"CRITICAL: Environment variable '{var}' is not set. Exiting.")
        raise ValueError(f"No {var} set in .env file or environment")

app = Flask(__name__)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logging.info("Successfully connected to MQTT Broker.")
    else:
        logging.error(f"Failed to connect to MQTT Broker, return code {rc}")

def on_disconnect(client, userdata, rc, properties=None):
    logging.warning(f"Disconnected from MQTT Broker with result code {rc}. Will attempt to auto-reconnect.")

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect

try:
    logging.info(f"Connecting to MQTT Broker at {MQTT_BROKER_ADDRESS}:{MQTT_BROKER_PORT}...")
    mqtt_client.connect(MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, 60)
except Exception as e:
    logging.error(f"Could not connect to MQTT Broker on startup: {e}")

mqtt_client.loop_start()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-API-Key')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        if token != SECRET_API_KEY:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/log', methods=['POST'])
@token_required
def log_data():
    try:
        data = request.get_json(force=True)
        
        topic = data.pop('topic', None)

        if not topic:
            logging.warning("Received request with missing 'topic' key.")
            return jsonify({'message': 'Error: "topic" key is required in JSON payload'}), 400

        payload = json.dumps(data)

        if not mqtt_client.is_connected():
            logging.error("MQTT client is not connected. Cannot publish message.")
            return jsonify({'message': 'Error: Internal service cannot connect to message broker'}), 503

        result = mqtt_client.publish(topic, payload)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logging.info(f"Published to topic '{topic}': {payload}")
            response_data = json.dumps({"success": True, "topic": topic})
            return Response(response_data, mimetype='application/json', status=200)
        else:
            logging.error(f"Failed to publish message to topic '{topic}'. MQTT-RC: {result.rc}")
            return jsonify({"success": False, "message": "Failed to publish message to broker"}), 500

    except json.JSONDecodeError:
        return jsonify({'message': 'Error: Request body must be valid JSON.'}), 400
    except Exception as e:
        logging.error(f"An unexpected error occurred in /log endpoint: {e}")
        return jsonify({'message': 'An internal server error occurred'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "mqtt_connected": mqtt_client.is_connected()
    }), 200

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=False)
