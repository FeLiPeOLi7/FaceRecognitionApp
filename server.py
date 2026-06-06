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

@app.route("/recognize/start", methods=["POST"])
def recognize_video():
    db_info = database.init_db()
    print(f"Database initialized. sqlite-vec enabled: {db_info['vec_enabled']}")

    video_capture = cv2.VideoCapture(0)

    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True
    enroll_requested = False

    while True:
        ret, frame = video_capture.read()  # Pick up a frame of the video
        if process_this_frame and ret:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            # Handle enrollment if requested
            if enroll_requested:
                if face_encodings:
                    consent = input(
                        "Voce consente com armazenamento/processamento da biometria (LGPD)? (s/n): "
                    ).strip().lower()

                    if consent == "s":
                        name = input("Digite seu nome: ").strip()
                        if name:
                            user_id = database.save_face(name, face_encodings[0])
                            total = database.count_people()
                            print(f"Pessoa cadastrada. user_id={user_id}. total_pessoas={total}")
                        else:
                            print("Cadastro cancelado: nome vazio.")
                    else:
                        print("Cadastro cancelado: consentimento nao fornecido.")
                else:
                    print("Cadastro solicitado, mas nenhuma face foi detectada.")

                enroll_requested = False

            face_names = []
            # See the encodings for each face in the frame.
            for face_encoding in face_encodings:
                match = database.search_face(face_encoding, threshold=0.6, k=1)
                name = match["name"] if match else "Unknown"
                face_names.append(name)

        process_this_frame = not process_this_frame  # Only process every other frame, to save time
        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4


            font = cv2.FONT_HERSHEY_DUPLEX
            font_scale = 0.8
            thickness = 1
            padding = 10

            # Width available inside face rectangle
            max_width = (right - left) - padding

            # Reduce font size until text fits
            while font_scale > 0.3:
                (text_width, text_height), baseline = cv2.getTextSize(
                    name,
                    font,
                    font_scale,
                    thickness
                )

                if text_width <= max_width:
                    break

                font_scale -= 0.1

            # Adjust width of the rectangle
            box_left = max(0,left)
            box_right = max(right, left + text_width + padding)

            # Adjust height of the rectangle
            box_top = bottom - text_height - padding
            box_top = max(0, box_top)
            box_bottom = bottom

            #Draw a box around the face
            cv2.rectangle(frame, (box_left, max(0, top - 20)), (box_right, bottom), (0, 0, 255), 2)

            # Background of the label
            cv2.rectangle(
                frame,
                (box_left, box_top),
                (box_right, box_bottom),
                (0, 0, 255),
                cv2.FILLED
            )

            # Centralized text
            cv2.putText(
                frame,
                name,
                (left + padding // 2, bottom - padding // 2),
                font,
                font_scale,
                (255, 255, 255),
                thickness
            )

        cv2.putText(
            frame,
            "Pressione C para cadastrar 1 face | Q para sair",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

        # Display the resulting image
        cv2.imshow('Video', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('c'):
            enroll_requested = True
            print("Cadastro solicitado. Enquadre 1 rosto e aguarde o prompt no terminal.")

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()

    return "Video received"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
