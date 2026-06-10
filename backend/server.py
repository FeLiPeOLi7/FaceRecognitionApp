#!/usr/bin/env python3
"""
Hybrid Face Recognition Server.
- Flask (Port 5000): Handles biometric registration (Rest/HTTP).
- Raw Sockets (Port 5001): Handles real-time frame processing for low-latency.
"""

import socket
import threading
import json
import base64
import os
import io
import re
from typing import Tuple, Dict, Any
import ssl
from pathlib import Path

import cv2
import numpy as np
import face_recognition
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image

import database

# Constants
HOST = "0.0.0.0"
FLASK_PORT = 5000
SOCKET_PORT = 5001
MAX_LISTEN_BACKLOG = 10

# --- Creates temp upload folder ---
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Recognition Logic ---
from processing import process_frame_bytes, register_face

# --- Flask Server (Port 5000) ---
app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "hybrid_server_online", "flask_port": FLASK_PORT, "socket_port": SOCKET_PORT})

@app.route("/registered", methods=["POST"])
def registered():
    name = request.form.get("name")
    consent = request.form.get("consent")

    if not name or consent != "true":
        return jsonify({"error": "Name and consent are required."}), 400

    if "image" not in request.files:
        return jsonify({"error": "Image file required."}), 400

    image = request.files["image"]
    filepath = os.path.join(UPLOAD_FOLDER, f"reg_{os.urandom(4).hex()}.png")
    image.save(filepath)

    success = register_face(filepath, name)
    if os.path.exists(filepath):
        os.remove(filepath)

    if success:
        return jsonify({"status": "success", "message": f"{name} registered."}), 200
    return jsonify({"status": "error", "message": "Failed to extract face."}), 422

def run_flask():
    print(f"[*] Flask server starting on port {FLASK_PORT}...")
    app.run(host=HOST, port=FLASK_PORT, debug=False, use_reloader=False)

# --- Raw Socket Server (Port 5001) ---

def parse_http_request(raw_request: bytes):
    """Simple parser for the frame route."""
    try:
        request_str = raw_request.decode('utf-8', errors='ignore') #Binary to string
        parts = request_str.split('\r\n\r\n', 1)
        headers_part = parts[0]
        header_lines = headers_part.split('\r\n')
        
        # Method and Path
        request_line = header_lines[0].split()
        method = request_line[0] if len(request_line) > 0 else "UNKNOWN"
        path = request_line[1] if len(request_line) > 1 else "/"
        
        # Headers
        headers = {}
        for line in header_lines[1:]:
            if ':' in line:
                k, v = line.split(':', 1)
                headers[k.strip().lower()] = v.strip()
        
        # Body
        body = raw_request[len(headers_part) + 4:] #+4 because of \r\n\r\n (gets everything after the header [i.e. the body])
        return method, path, headers, body
    except:
        return None, None, {}, b""

def build_http_response(status_code, status_text, content_type, body):
    response = f"HTTP/1.1 {status_code} {status_text}\r\n"
    response += f"Content-Type: {content_type}\r\n"
    response += f"Content-Length: {len(body)}\r\n"
    response += "Access-Control-Allow-Origin: *\r\n"
    response += "Connection: close\r\n\r\n"
    return response.encode() + body

def handle_options_request() -> Tuple[int, str, bytes]:
    """Handler para OPTIONS requests (CORS pre-flight)."""
    response = f"HTTP/1.1 204 No Content\r\n"
    response += f"Access-Control-Allow-Origin: *\r\n"
    response += f"Access-Control-Allow-Methods: POST, OPTIONS\r\n"
    response += "Access-Control-Allow-Headers: Content-Type\r\n"
    response += "Access-Control-Max-Age: 86400\r\n"
    response += "Content-Length: 0\r\n\r\n"

    return response.encode()

def handle_socket_client(client_socket, client_address):
    try:
        raw_data = b""

        '''
        While you dont have all the data, continue getting 4KB chunks. Ensuring that we will have all the packet in the final loop
        '''
        while True:
            chunk = client_socket.recv(4096)
            if not chunk: break
            raw_data += chunk
            if b'\r\n\r\n' in raw_data: # Do we have all the headers?
                # Basic check for content-length to ensure full read
                headers_str = raw_data.split(b'\r\n\r\n')[0].decode('utf-8', errors='ignore')
                cl_match = re.search(r'content-length:\s*(\d+)', headers_str, re.I)
                if cl_match:
                    cl = int(cl_match.group(1)) #Content-Length
                    if len(raw_data) >= raw_data.find(b'\r\n\r\n') + 4 + cl: #Do we have all the body + header?
                        break
                else: break 

        method, path, headers, body = parse_http_request(raw_data)
        

        if method == 'OPTIONS':
            # Pre-flight CORS request
            response = handle_options_request()

            client_socket.sendall(response)
            return
        elif method == "POST" and path == "/frame":
            # Extract image (could be JSON or raw)
            image_bytes = body
            sid = f"{client_address[0]}:{client_address[1]}"
            if 'application/json' in headers.get('content-type', ''):
                data = json.loads(body.decode())
                image_bytes = base64.b64decode(data['image_b64'])
                sid = data["client_id"]
            processed_jpeg = process_frame_bytes(image_bytes, sid)
            
            response = build_http_response(200, "OK", "image/jpeg", processed_jpeg)
            client_socket.sendall(response)
        else:
            resp = build_http_response(404, "Not Found", "application/json", b'{"error": "Route not found"}')
            client_socket.sendall(resp)
    except Exception as e:
        print(f"[Socket Error] {e}")
    finally:
        client_socket.close()

def start_socket_server():    
    """Inicia o servidor HTTP (com ou sem TLS/SSL)."""

    #Creates our SOCKET (SOCK_STREAM enables TCP connection)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #Re-uses the socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    protocol = "HTTP"

    try:
        #Estabilishs the sockets addr
        server_socket.bind((HOST, SOCKET_PORT))
        server_socket.listen(MAX_LISTEN_BACKLOG)

        print("\n" + "="*60)
        print(f" SERVIDOR {protocol} SOCKET ATIVO")
        print(f" Endereço: {HOST}:{SOCKET_PORT}")
        print("="*60 + "\n")

        # Server is eternally waiting and accepting clients
        while True:
            try:
                #accept() is a blocking function, so it waits the client accept to continue running the code
                client_socket, client_address = server_socket.accept()

                client_thread = threading.Thread(
                    target=handle_socket_client,
                    args=(
                        client_socket,
                        client_address
                    ),
                    daemon=True
                )

                client_thread.start()

            except KeyboardInterrupt:
                break

    except Exception as e:
        print(f"[ERROR] Server error: {e}")

    finally:
        print("\n[SHUTDOWN] Encerrando servidor...")
        server_socket.close()

if __name__ == "__main__":
    database.init_db()
    
    # Start Socket Server in thread
    threading.Thread(target=start_socket_server, daemon=True).start()
    
    # Start Flask Server in main thread
    run_flask()
