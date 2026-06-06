import face_recognition
import cv2
import numpy as np
import database
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
from typing import Any
import io
import base64
from PIL import Image
#import time

client_cache = {}

RECOGNITION_INTERVAL = 5

def process_frame_bytes(image_bytes: bytes, sid: str, resize_scale: float = 0.20) -> bytes:
    """Processa um frame (JPEG/PNG bytes) e retorna JPEG anotado.
    Implementado inline para manter módulo único `server.py`.
    """

    # simple cache for multiple users
    if sid not in client_cache:
        client_cache[sid] = {
            "frame_counter": 0,
            "locations": [],
            "names": []
        }

    cache = client_cache[sid]

    #start = time.perf_counter()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # Prepare scaled frame for faster recognition
    small = cv2.resize(frame, (0, 0), fx=resize_scale, fy=resize_scale)
    rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    if(cache["frame_counter"] == 0):
        locations = face_recognition.face_locations(rgb_small)
        encodings = face_recognition.face_encodings(rgb_small, locations)

        names = []
        for enc in encodings:
            match = database.search_face(enc, threshold=0.6, k=1)
            names.append(match["name"] if match else "Desconhecido")

        cache["locations"] = locations
        cache["names"] = names
    else:
        locations = cache["locations"]
        names = cache["names"]

    cache["frame_counter"] = (cache["frame_counter"] + 1) % RECOGNITION_INTERVAL

    # Scale coordinates back to original frame size
    scale = 1.0 / resize_scale
    for (top, right, bottom, left), name in zip(locations, names):
        top = int(top * scale)
        right = int(right * scale)
        bottom = int(bottom * scale)
        left = int(left * scale)

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.rectangle(frame, (left, bottom - 20), (right, bottom), (0, 0, 255), cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    _, jpg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    #end = time.perf_counter()
    #print(f"Frame: {(end-start)*1000:.2f} ms")
    return jpg.tobytes()

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev"

# Enable CORS for frontend cross-origin requests
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def register_face(img_path, name) -> bool:
    """Extracts encodings and persists them to the Ground-Truth database. Returns success/failure."""
    img = face_recognition.load_image_file(img_path)
    encodings = face_recognition.face_encodings(img)

    if len(encodings) == 0:
        print("[ENROLLMENT ERROR] No faces detected in the provided image.")
        return False
    elif len(encodings) > 1:
        print("[ENROLLMENT ERROR] Multiple faces detected. Please provide an isolated portrait.")
        return False

    face_encoding = encodings[0]
    user_id = database.save_face(name, face_encoding)
    total = database.count_people()
    print(f"[ENROLLMENT SUCCESS] {name} registered. ID={user_id}. Database total={total}")
    return True


@app.route("/registered", methods=["POST"])
def registered():
    """REST endpoint for biometric enrollment (Upload or Camera Capture)"""
    name = request.form.get("name")
    consent = request.form.get("consent")

    if not name:
        return jsonify({"error": "The 'name' field is required."}), 400

    if not consent or consent.lower() != 'true':
        return jsonify({"error": "Legal biometric consent (LGPD) was not provided."}), 400

    if "image" not in request.files:
        return jsonify({"error": "Binary image file was not uploaded."}), 400

    image = request.files["image"]
    if image.filename == '':
        return jsonify({"error": "Invalid filename."}), 400

    # Fallback name for React canvas webcam blobs
    filename = image.filename if image.filename else "capture.png"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    image.save(filepath)

    print(f"[REGISTRATION REQUEST] Name: {name} | Temporary file: {filepath}")

    # Process face vectorization
    success = register_face(filepath, name)

    # Garbage collection
    if os.path.exists(filepath):
        os.remove(filepath)

    if success:
        return jsonify({"status": "success", "message": f"Biometric profile for {name} saved successfully."}), 200
    else:
        return jsonify({"status": "error", "message": "Could not extract a clean biometric template."}), 422


@socketio.on('frame')
def handle_frame(data):
    """Continuous low-latency WebSockets processing loop (5 FPS)"""
    try:
        sid = request.sid

        if isinstance(data, dict) and 'image_b64' in data:
            image_bytes = base64.b64decode(data['image_b64'])
        elif isinstance(data, (bytes, bytearray)):
            image_bytes = bytes(data)
        else:
            raise ValueError(f'Unsupported payload structure: {type(data)}')

        processed = process_frame_bytes(image_bytes, sid=sid)
        emit('processed', processed)
    except Exception as e:
        print('[SOCKET ERROR] Failure in video loop cycle:', e)


if __name__ == "__main__":
    database.init_db()
    print("\n" + "="*60)
    print(" BACKEND SERVER ACTIVE (Flask + SocketIO + Eventlet)")
    print(" REST Endpoint: http://localhost:5000/registered")
    print(" WebSocket Channel active listening to event: 'frame'")
    print("="*60 + "\n")
    socketio.run(app, host="0.0.0.0", port=5000, log_output=False)
