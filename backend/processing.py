"""
Processamento de frames de video e reconhecimento facial.
Modulo reutilizavel que encapsula a logica de processamento.
"""

import face_recognition
import cv2
import numpy as np
import database
import io
from PIL import Image
import unicodedata


def normalize_text(texto):
    nfkd = unicodedata.normalize('NFKD', texto)

    return "".join([c for c in nfkd if not unicodedata.combining(c)])

RECOGNITION_INTERVAL = 5
client_cache = {}

def process_frame_bytes(image_bytes: bytes, sid: str, resize_scale: float = 0.25) -> bytes:
    """Processes a frame and returns marked JPEG bytes."""
    if sid not in client_cache:
        client_cache[sid] = {"frame_counter": 0, "locations": [], "names": []}

    cache = client_cache[sid]
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    small = cv2.resize(frame, (0, 0), fx=resize_scale, fy=resize_scale)
    rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    if cache["frame_counter"] == 0:
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

    scale = 1.0 / resize_scale
    for (top, right, bottom, left), name in zip(locations, names):
        top, right, bottom, left = int(top * scale), int(right * scale), int(bottom * scale), int(left * scale)
        
        normalized_name = normalize_text(name)
        font_size = 1.2
        max_size = 14

        if len(name) > max_size:
            parts = normalized_name.split()

            short_name = parts[0]

            for part in parts[1:]:
                if len(short_name) + len(part) + 1 <= max_size:
                    short_name += " " + part
                else:
                    break

            normalized_name = short_name

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 3)
        cv2.rectangle(frame, (left, bottom - 40), (right, bottom), (0, 0, 255), cv2.FILLED)
        cv2.putText(frame, normalized_name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, font_size, (255,255,255), 2)

    _, jpg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    return jpg.tobytes()

def register_face(img_path, name) -> bool:
    """Extracts encoding and saves to database."""
    img = face_recognition.load_image_file(img_path)
    encodings = face_recognition.face_encodings(img)

    if len(encodings) != 1:
        return False

    database.save_face(name, encodings[0])
    return True