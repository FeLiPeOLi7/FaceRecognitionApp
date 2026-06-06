import face_recognition
import cv2
import numpy as np
import database
from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
import os
from typing import Any
import io
import base64
from PIL import Image


def process_frame_bytes(image_bytes: bytes, resize_scale: float = 0.6) -> bytes:
    """Processa um frame (JPEG/PNG bytes) e retorna JPEG anotado.
    Implementado inline para manter módulo único `server.py`.
    """

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # Prepare scaled frame for faster recognition
    small = cv2.resize(frame, (0, 0), fx=resize_scale, fy=resize_scale)
    rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    locations = face_recognition.face_locations(rgb_small)
    encodings = face_recognition.face_encodings(rgb_small, locations)

    names = []
    for enc in encodings:
        match = database.search_face(enc, threshold=0.6, k=1)
        names.append(match["name"] if match else "Unknown")

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
    return jpg.tobytes()

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev"
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def register_face(img_path, name) -> None:
    img = face_recognition.load_image_file(img_path)
    encodings = face_recognition.face_encodings(img)

    if len(encodings) == 0:
        print("Não foi detectado nenhuma cara para cadastro.")
        return
    elif len(encodings) > 1:
        print("Foi detectado mais de uma face para o cadastro.")
        return

    face_encoding = encodings[0]

    user_id = database.save_face(name, face_encoding)
    total = database.count_people()
    print(f"Pessoa cadastrada. user_id={user_id}. total_pessoas={total}")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/registered", methods=["POST"])
def registered():
    name = request.form["name"]

    if name is None:
        return "Name required", 400

    image = request.files["image"]

    if image is None:
        return "Image required", 400

    consent = request.form.get("consent")

    if consent is None:
        return "Consent required", 400

    filepath = os.path.join(UPLOAD_FOLDER, image.filename)

    image.save(filepath)

    print(f"Name: {name}")

    print(f"Saved: {filepath}")

    # Register the face
    register_face(filepath, name)

    if os.path.exists(filepath):
        os.remove(filepath)

    return f"Image received: {image.filename}"


@app.route("/recognize")
def recognize():
    return render_template("recognize.html")


@app.route('/scripts/<path:filename>')
def serve_scripts(filename: str):
    return send_from_directory('scripts', filename)


@socketio.on('frame')
def handle_frame(data):
    try:
        if isinstance(data, dict) and 'image_b64' in data:
            image_bytes = base64.b64decode(data['image_b64'])
        elif isinstance(data, (bytes, bytearray)):
            image_bytes = bytes(data)
        else:
            raise ValueError(f'Unsupported frame payload type: {type(data)}')

        processed = process_frame_bytes(image_bytes)
        emit('processed', processed)
    except Exception as e:
        print('Error processing frame:', e)


if __name__ == "__main__":
    database.init_db()
    print("Starting Flask+SocketIO server on http://0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000)
