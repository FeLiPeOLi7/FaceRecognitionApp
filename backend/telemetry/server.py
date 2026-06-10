#!/usr/bin/env python3
"""
Hybrid Face Recognition Server with Telemetry & Enhanced Security.
- Flask (Port 5000): Handles biometric registration (Rest/HTTP).
- Raw Sockets (Port 5001): Handles real-time frame processing with Telemetry.
"""

import socket
import threading
import json
import base64
import os
import io
import re
import time
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
MAX_PAYLOAD_SIZE = 3 * 1024 * 1024
SOCKET_TIMEOUT = 2.0

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Telemetry Engine ---
class ServerTelemetry:
    def __init__(self):
        self._lock = threading.Lock()
        self.active_clients = 0
        self.total_processed_frames = 0
        self.total_bytes_sent = 0
        self.inference_times = []
        self.timeouts_and_drops = 0
        self.rate_limit_blocks = 0
        
        # Rate Limiting Tracker (IP -> List of timestamps)
        self.ip_request_history: Dict[str, list] = {}
        self.RATE_LIMIT_MAX_FPS = 12

    def client_connected(self):
        with self._lock:
            self.active_clients += 1

    def client_disconnected(self):
        with self._lock:
            if self.active_clients > 0:
                self.active_clients -= 1

    def record_frame(self, bytes_sent: int, inference_time: float):
        with self._lock:
            self.total_processed_frames += 1
            self.total_bytes_sent += bytes_sent
            self.inference_times.append(inference_time)
            if len(self.inference_times) > 100:
                self.inference_times.pop(0)

    def record_drop(self):
        with self._lock:
            self.timeouts_and_drops += 1

    def record_rate_limit(self):
        with self._lock:
            self.rate_limit_blocks += 1

    def is_rate_limited(self, ip: str) -> bool:
        """Security: Aplica controle de taxa na Camada de Aplicação."""
        with self._lock:
            now = time.time()
            if ip not in self.ip_request_history:
                self.ip_request_history[ip] = []
            
            # Limpa histórico antigo (> 1 segundo)
            self.ip_request_history[ip] = [t for t in self.ip_request_history[ip] if now - t < 1.0]
            
            if len(self.ip_request_history[ip]) >= self.RATE_LIMIT_MAX_FPS:
                return True
            
            self.ip_request_history[ip].append(now)
            return False

    def print_metrics_loop(self):
        """Exibe o Dashboard de telemetria no terminal a cada 3 segundos."""
        while True:
            time.sleep(3.0)
            with self._lock:
                avg_inference = (sum(self.inference_times) / len(self.inference_times) * 1000) if self.inference_times else 0
                throughput_mb = (self.total_bytes_sent / (1024 * 1024))
                
                print("\n" + "="*25 + " TELEMETRIA DE REDE " + "="*25)
                print(f" Capacidade Concorrente Estável : {self.active_clients} Clientes Ativos")
                print(f" Vazão de Saída Acumulada       : {throughput_mb:.2f} MB Trafegados")
                print(f" Latência Média do Pipeline IA : {avg_inference:.2f} ms / frame")
                print(f" Total de Frames Processados   : {self.total_processed_frames} unidades")
                print(f" Perda de Conexão / Timeouts   : {self.timeouts_and_drops} falhas de link")
                print(f" Bloqueios de Rate Limit (DoS) : {self.rate_limit_blocks} requisições barradas")
                print("="*72 + "\n")

telemetry = ServerTelemetry()

# Inicializa thread de exibição de métricas
threading.Thread(target=telemetry.print_metrics_loop, daemon=True).start()


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
    try:
        request_str = raw_request.decode('utf-8', errors='ignore')
        parts = request_str.split('\r\n\r\n', 1)
        headers_part = parts[0]
        header_lines = headers_part.split('\r\n')
        
        request_line = header_lines[0].split()
        method = request_line[0] if len(request_line) > 0 else "UNKNOWN"
        path = request_line[1] if len(request_line) > 1 else "/"
        
        headers = {}
        for line in header_lines[1:]:
            if ':' in line:
                k, v = line.split(':', 1)
                headers[k.strip().lower()] = v.strip()
        
        body = raw_request[len(headers_part) + 4:]
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

def handle_options_request() -> bytes:
    response = f"HTTP/1.1 204 No Content\r\n"
    response += f"Access-Control-Allow-Origin: *\r\n"
    response += f"Access-Control-Allow-Methods: POST, OPTIONS\r\n"
    response += "Access-Control-Allow-Headers: Content-Type\r\n"
    response += "Access-Control-Max-Age: 86400\r\n"
    response += "Content-Length: 0\r\n\r\n"
    return response.encode()

def handle_socket_client(client_socket, client_address):
    client_ip = client_address[0]
    telemetry.client_connected()
    
    try:
        # Security Guard: Aplica timeout de socket para evitar travamento por conexões fantasmas
        client_socket.settimeout(SOCKET_TIMEOUT)
        
        # Security Guard: Rate Limiting Preventivo antes de alocar processamento
        if telemetry.is_rate_limited(client_ip):
            telemetry.record_rate_limit()
            resp = build_http_response(425, "Too Early", "application/json", b'{"error": "Rate limit exceeded"}')
            client_socket.sendall(resp)
            return

        raw_data = b""
        while True:
            chunk = client_socket.recv(4096)
            if not chunk: 
                break
            raw_data += chunk
            
            # Security Guard: Evita estouro de pilha alocada na memória
            if len(raw_data) > MAX_PAYLOAD_SIZE:
                raise ValueError("Payload excede o limite máximo de segurança.")

            if b'\r\n\r\n' in raw_data:
                headers_str = raw_data.split(b'\r\n\r\n')[0].decode('utf-8', errors='ignore')
                cl_match = re.search(r'content-length:\s*(\d+)', headers_str, re.I)
                if cl_match:
                    cl = int(cl_match.group(1))
                    if len(raw_data) >= raw_data.find(b'\r\n\r\n') + 4 + cl:
                        break
                else: 
                    break

        method, path, headers, body = parse_http_request(raw_data)

        if method == 'OPTIONS':
            response = handle_options_request()
            client_socket.sendall(response)
            return
            
        elif method == "POST" and path == "/frame":
            image_bytes = body
            if 'application/json' in headers.get('content-type', ''):
                data = json.loads(body.decode())
                image_bytes = base64.b64decode(data['image_b64'])
            
            sid = f"{client_address[0]}:{client_address[1]}"
            
            # Medição de Tempo de Inferência (IA + OpenCV)
            start_time = time.perf_counter()
            processed_jpeg = process_frame_bytes(image_bytes, sid)
            end_time = time.perf_counter()
            
            inference_time = end_time - start_time
            
            response = build_http_response(200, "OK", "image/jpeg", processed_jpeg)
            client_socket.sendall(response)
            
            # Registra sucesso e vazão na telemetria
            telemetry.record_frame(len(response), inference_time)
        else:
            resp = build_http_response(404, "Not Found", "application/json", b'{"error": "Route not found"}')
            client_socket.sendall(resp)
            
    except (socket.timeout, socket.error, ValueError) as e:
        # Conta a perda de pacotes ou desconexões por timeout de rede
        telemetry.record_drop()
    except Exception as e:
        telemetry.record_drop()
    finally:
        telemetry.client_disconnected()
        client_socket.close()

def start_socket_server(use_ssl: bool = False):   
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    protocol = "HTTP"
    ssl_context = None

    if use_ssl:
        script_dir = Path(__file__).parent
        cert_file = script_dir / "cert.pem"
        key_file = script_dir / "key.pem"

        if cert_file.exists() and key_file.exists():
            try:
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(str(cert_file), str(key_file))
                protocol = "HTTPS"
            except Exception as e:
                print(f"[WARNING] SSL error: {e}")

    try:
        server_socket.bind((HOST, SOCKET_PORT))
        server_socket.listen(10) # Fila de escuta estendida para mitigar picos de conexões

        print("\n" + "="*60)
        print(f" SERVIDOR {protocol} SOCKET ATIVO COLETANDO TELEMETRIA")
        print(f" Endereço: {HOST}:{SOCKET_PORT}")
        print("="*60 + "\n")

        while True:
            try:
                client_socket, client_address = server_socket.accept()

                if ssl_context:
                    try:
                        client_socket = ssl_context.wrap_socket(client_socket, server_side=True)
                    except Exception as e:
                        telemetry.record_drop()
                        client_socket.close()
                        continue

                client_thread = threading.Thread(
                    target=handle_socket_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()

            except KeyboardInterrupt:
                break
    except Exception as e:
        print(f"[ERROR] Server error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    database.init_db()
    threading.Thread(target=start_socket_server, args=(True,), daemon=True).start()
    run_flask()
