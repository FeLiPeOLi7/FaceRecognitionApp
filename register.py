import face_recognition
import cv2
import numpy as np
import database
from flask import Flask, render_template, request
import os

app = Flask(__name__)

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
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)