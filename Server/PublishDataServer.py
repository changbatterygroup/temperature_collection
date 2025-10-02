import os
from flask import Flask, request, jsonify, Response
import json
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

SECRET_API_KEY = os.getenv("CLIENT_API_KEY")
if not SECRET_API_KEY:
    raise ValueError("No CLIENT_API_KEY set in .env file")

HOST = os.getenv("HOST")
if not HOST:
    raise ValueError("No HOST set in .env file")

PORT = int(os.getenv("PORT"))
if not PORT:
    raise ValueError("No PORT set in .env file")

app = Flask(__name__)

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
    data = request.get_json(force=True)
    print(f"Received JSON data: {data}")

    response_data = json.dumps({"success": "true"})

    return Response(response_data, mimetype='application/json', status=200)



if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)