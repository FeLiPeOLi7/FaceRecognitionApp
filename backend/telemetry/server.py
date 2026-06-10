#!/usr/bin/env python3
"""
Hybrid Face Recognition Server with Advanced Telemetry & Enhanced Security.
- Flask (Port 5000): Handles biometric registration (Rest/HTTP).
- Raw Sockets (Port 5001): Handles real-time frame processing with Advanced Telemetry.
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
MAX_PAYLOAD_SIZE = 3 * 1024 * 1024  # Máximo 3MB por frame (Proteção Buffer Overflow)
SOCKET_TIMEOUT = 2.0                 # Timeout de E/S para conexões lentas ou mortas
MAX_LISTEN_BACKLOG = 10              # Limite da fila de escuta do Socket a nível de SO

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Advanced Telemetry Engine ---
class ServerTelemetry:
    def __init__(self):
        self._lock = threading.Lock()
        
        # Conexões e Capacidade
        self.active_clients = 0
        self.peak_clients = 0  # Maior número de usuários simultâneos registrados
        
        # Métricas de Volume e Vazão
        self.total_processed_frames = 0
        self.total_bytes_sent = 0
        self.last_bytes_count = 0
        self.current_bandwidth_bps = 0.0  # Vazão instantânea em bits por segundo
        self.last_bandwidth_update = time.time()
        
        # Métricas de Tamanho de Pacote
        self.last_packet_size_bytes = 0
        self.packet_sizes = []
        
        # Desempenho e Inferência
        self.inference_times = []
        self.timeouts_and_drops = 0
        self.rate_limit_blocks = 0
        
        # Controle de Taxa por IP
        self.ip_request_history: Dict[str, list] = {}
        self.RATE_LIMIT_MAX_FPS = 12

    def client_connected(self):
        with self._lock:
            self.active_clients += 1
            if self.active_clients > self.peak_clients:
                self.peak_clients = self.active_clients

    def client_disconnected(self):
        with self._lock:
            if self.active_clients > 0:
                self.active_clients -= 1

    def record_frame(self, bytes_sent: int, inference_time: float):
        with self._lock:
            self.total_processed_frames += 1
            self.total_bytes_sent += bytes_sent
            self.last_packet_size_bytes = bytes_sent
            
            # Histórico dos tamanhos de pacotes para média móvel
            self.packet_sizes.append(bytes_sent)
            if len(self.packet_sizes) > 100:
                self.packet_sizes.pop(0)
                
            # Histórico de tempos de inferência
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
        with self._lock:
            now = time.time()
            if ip not in self.ip_request_history:
                self.ip_request_history[ip] = []
            self.ip_request_history[ip] = [t for t in self.ip_request_history[ip] if now - t < 1.0]
            if len(self.ip_request_history[ip]) >= self.RATE_LIMIT_MAX_FPS:
                return True
            self.ip_request_history[ip].append(now)
            return False

    def update_instant_bandwidth(self):
        """Calcula a largura de banda consumida no último intervalo."""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_bandwidth_update
            if elapsed >= 1.0:
                bytes_diff = self.total_bytes_sent - self.last_bytes_count
                # Converte bytes para Bits por Segundo (bps)
                self.current_bandwidth_bps = (bytes_diff * 8) / elapsed
                self.last_bytes_count = self.total_bytes_sent
                self.last_bandwidth_update = now

    def calculate_theoretical_capacity(self, avg_inference_ms: float) -> str:
        """
        Estima a capacidade máxima do servidor com base na latência de processamento
        da CPU e nas restrições de concorrência (threads e backlog).
        """
        if avg_inference_ms == 0:
            return "Indefinida (Aguardando tráfego)"
        
        # Cada cliente envia 5 frames por segundo (um frame a cada 200ms)
        # Se um frame demora 'avg_inference_ms' para processar, um único núcleo processa (1000 / avg_inference_ms) f/s.
        # Considerando o modelo multithread cooperativo e a fila do SO (Backlog):
        max_frames_per_second = 1000.0 / avg_inference_ms
        estimated_users = max_frames_per_second / 5.0  # Cada usuário consome 5 FPS do pool
        
        # Teto físico baseado no Backlog máximo de escuta do socket
        capacity_ceiling = estimated_users + MAX_LISTEN_BACKLOG
        return f"~{int(capacity_ceiling)} usuários simultâneos (limite físico por CPU)"

    def print_metrics_loop(self):
        """Exibe o Dashboard expandido de telemetria no terminal a cada 3 segundos."""
        while True:
            time.sleep(3.0)
            self.update_instant_bandwidth()
            
            with self._lock:
                avg_inference = (sum(self.inference_times) / len(self.inference_times) * 1000) if self.inference_times else 0
                avg_packet_size = (sum(self.packet_sizes) / len(self.packet_sizes) / 1024) if self.packet_sizes else 0
                last_packet_kb = self.last_packet_size_bytes / 1024
                
                throughput_mb = (self.total_bytes_sent / (1024 * 1024))
                bandwidth_kbps = self.current_bandwidth_bps / 1024
                
                capacity_estimation = self.calculate_theoretical_capacity(avg_inference)
                
                print("\n" + "="*23 + " ADVANCED NETWORK TELEMETRY " + "="*23)
                print(f" Concurrent Connections        : {self.active_clients} Active | [Peak: {self.peak_clients}]")
                print(f" Estimated Max Capacity        : {capacity_estimation}")
                print(f" Instant Bandwidth             : {bandwidth_kbps:.2f} Kbps")
                print(f" Accumulated Output Volume     : {throughput_mb:.2f} MB")
                print(f" Last Packet Size              : {last_packet_kb:.2f} KB")
                print(f" Average Packet Size           : {avg_packet_size:.2f} KB")
                print(f" Average Inference Latency     : {avg_inference:.2f} ms / frame")
                print(f" Total Processed Frames        : {self.total_processed_frames} units")
                print(f" Connection Drops / Timeouts   : {self.timeouts_and_drops} failures")
                print(f" Rate Limit Blocks (DoS)       : {self.rate_limit_blocks} rejected requests")
                print("="*74 + "\n")

telemetry = ServerTelemetry()
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
        client_socket.settimeout(SOCKET_TIMEOUT)
        
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
            sid = f"{client_address[0]}:{client_address[1]}"
            if 'application/json' in headers.get('content-type', ''):
                data = json.loads(body.decode())
                image_bytes = base64.b64decode(data['image_b64'])
                sid = data['client_id']
            
            start_time = time.perf_counter()
            processed_jpeg = process_frame_bytes(image_bytes, sid)
            end_time = time.perf_counter()
            
            inference_time = end_time - start_time
            
            response = build_http_response(200, "OK", "image/jpeg", processed_jpeg)
            client_socket.sendall(response)
            
            telemetry.record_frame(len(response), inference_time)
        else:
            resp = build_http_response(404, "Not Found", "application/json", b'{"error": "Route not found"}')
            client_socket.sendall(resp)
            
    except (socket.timeout, socket.error, ValueError):
        telemetry.record_drop()
    except Exception:
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
        server_socket.listen(MAX_LISTEN_BACKLOG)

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
                    except Exception:
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
