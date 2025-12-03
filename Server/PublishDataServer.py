import os
import sys
import json
import logging
import time
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response
import paho.mqtt.client as mqtt

from FailureManager import FailureManager

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    filename='../logs/PublishDataServer.log'
)

load_dotenv()

SECRET_API_KEY = os.getenv("CLIENT_API_KEY")
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))
MQTT_BROKER_ADDRESS = os.getenv("BROKER_ADDRESS")
MQTT_BROKER_PORT = int(os.getenv("BROKER_PORT"))
MQTT_CLIENT_ID = os.getenv("CLIENT_ID")

DB_PATH = os.getenv("DB_PATH")
FAILURE_THRESHOLD = 5

required_vars = ["CLIENT_API_KEY", "HOST", "BROKER_ADDRESS", "CLIENT_ID"]
for var in required_vars:
    if not os.getenv(var):
        logging.critical(f"CRITICAL: {var} is missing. Exiting.")
        sys.exit(1)

app = Flask(__name__)

fail_manager = FailureManager(DB_PATH, FAILURE_THRESHOLD)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logging.info("Connected to MQTT Broker.")
        fail_manager.recover_data(client)
    else:
        logging.error(f"Failed to connect to MQTT Broker, return code {rc}")

def on_disconnect(client, userdata, rc, properties=None):
    logging.warning(f"Disconnected from MQTT Broker (rc={rc}).")

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect

try:
    logging.info(f"Connecting to MQTT Broker at {MQTT_BROKER_ADDRESS}:{MQTT_BROKER_PORT}...")
    mqtt_client.connect(MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    logging.critical(f"Could not connect to MQTT Broker on startup: {e}")

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
            return jsonify({'message': 'Error: "topic" key is required'}), 400

        if 'timestamp' not in data: # shouldn't be in the data normally
            data['timestamp'] = int(time.time())

        payload = json.dumps(data)

        if not mqtt_client.is_connected():
            logging.error("Broker disconnected. Buffering to SQLite.")
            fail_manager.buffer_data(topic, payload)
            return jsonify({'message': 'Buffered locally due to connection failure'}), 503

        result = mqtt_client.publish(topic, payload)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logging.info(f"Published to '{topic}'")
            return Response(json.dumps({"success": True, "topic": topic}), mimetype='application/json', status=200)
        else:
            logging.error(f"Publish failed (RC: {result.rc}). Buffering.")
            fail_manager.buffer_data(topic, payload)
            return jsonify({"success": False, "message": "Buffered locally"}), 500

    except json.JSONDecodeError:
        return jsonify({'message': 'Error: Invalid JSON'}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({'message': 'Internal error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "mqtt_connected": mqtt_client.is_connected(),
        "failures_since_start": fail_manager.fail_count
    }), 200

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=False)