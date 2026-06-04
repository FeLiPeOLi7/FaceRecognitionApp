import hashlib
import hmac
import os
import sqlite3
from pathlib import Path
from typing import Any
from cryptography.fernet import Fernet
import numpy as np


DB_PATH = Path("faces.db")
KEY_PATH = Path("db_key.key")
ENCODING_SIZE = 128

def _get_or_create_key(key_path: Path = KEY_PATH) -> bytes:
    '''
    Get or create the encription key for the database. 
    The key is used to encrypt the user names and stored in a db_key.key file.
    '''
    
    # Check if the key already exists
    if key_path.exists():
        key = key_path.read_bytes()
        
        return key

    # Else, it creates the key
    key = Fernet.generate_key()
    key_path.write_bytes(key)
    os.chmod(key_path, 0o600)

    return key


def _encrypt_name(name: str, key: bytes) -> bytes:
    cipher = Fernet(key)
    
    return cipher.encrypt(name.encode("utf-8"))


def _decrypt_name(payload: bytes, key: bytes) -> str:
    cipher = Fernet(key)

    return cipher.decrypt(payload).decode("utf-8")


def _vector_to_blob(vector: np.ndarray) -> bytes:
    arr = np.asarray(vector, dtype=np.float32).reshape(-1)
    if arr.shape[0] != ENCODING_SIZE:
        raise ValueError(f"Expected vector with {ENCODING_SIZE} values, got {arr.shape[0]}")
    return arr.tobytes()


def _blob_to_vector(blob: bytes) -> np.ndarray:
    arr = np.frombuffer(blob, dtype=np.float32)
    if arr.shape[0] != ENCODING_SIZE:
        raise ValueError("Stored encoding has invalid size")
    return arr


def _open_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _load_sqlite_vec(conn: sqlite3.Connection) -> bool:
    try:
        import sqlite_vec  # type: ignore
    except Exception:
        return False

    try:
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        return True
    except Exception:
        return False


def init_db(db_path: Path = DB_PATH, key_path: Path = KEY_PATH) -> dict[str, Any]:
    _get_or_create_key(key_path)

    with _open_connection(db_path) as conn:
        vec_enabled = _load_sqlite_vec(conn)

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_encrypted BLOB NOT NULL
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS face_encodings (
                user_id INTEGER PRIMARY KEY,
                encoding BLOB NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )

        if vec_enabled:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_face_encodings USING vec0(
                    encoding FLOAT[128]
                );
                """
            )

    return {"vec_enabled": vec_enabled}


def save_face(name: str, encoding_vector: np.ndarray, db_path: Path = DB_PATH, key_path: Path = KEY_PATH) -> int:
    key = _get_or_create_key(key_path)
    encrypted_name = _encrypt_name(name, key)
    encoding_blob = _vector_to_blob(encoding_vector)

    with _open_connection(db_path) as conn:
        vec_enabled = _load_sqlite_vec(conn)
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute("INSERT INTO users(name_encrypted) VALUES (?)", (encrypted_name,))
        user_id = int(cur.lastrowid)
        cur.execute("INSERT INTO face_encodings(user_id, encoding) VALUES (?, ?)", (user_id, encoding_blob))

        if vec_enabled:
            cur.execute(
                "INSERT OR REPLACE INTO vec_face_encodings(rowid, encoding) VALUES (?, ?)",
                (user_id, encoding_blob),
            )

        conn.commit()
        return user_id


def search_face(
    query_vector: np.ndarray,
    threshold: float = 0.6,
    k: int = 1,
    db_path: Path = DB_PATH,
    key_path: Path = KEY_PATH,
) -> dict[str, Any] | None:
    key = _get_or_create_key(key_path)
    query_blob = _vector_to_blob(query_vector)

    with _open_connection(db_path) as conn:
        vec_enabled = _load_sqlite_vec(conn)
        user_id = None
        distance = None

        if vec_enabled:
            try:
                row = conn.execute(
                    """
                    SELECT rowid, distance
                    FROM vec_face_encodings
                    WHERE encoding MATCH ? AND k = ?
                    ORDER BY distance ASC
                    LIMIT 1
                    """,
                    (query_blob, int(k)),
                ).fetchone()

                if row is not None:
                    user_id = int(row[0])
                    distance = float(row[1])
            except sqlite3.DatabaseError:
                user_id = None
                distance = None

        if user_id is None:
            candidates = conn.execute("SELECT user_id, encoding FROM face_encodings").fetchall()
            if not candidates:
                return None

            q = np.frombuffer(query_blob, dtype=np.float32)
            best_user = None
            best_distance = None

            for cand_user_id, cand_blob in candidates:
                cand_vec = _blob_to_vector(cand_blob)
                d = float(np.linalg.norm(q - cand_vec))
                if best_distance is None or d < best_distance:
                    best_distance = d
                    best_user = int(cand_user_id)

            user_id = best_user
            distance = best_distance

        if user_id is None or distance is None or distance > threshold:
            return None

        row = conn.execute("SELECT name_encrypted FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            return None

        name = _decrypt_name(row[0], key)
        return {"user_id": user_id, "name": name, "distance": distance}


def delete_person(user_id: int, db_path: Path = DB_PATH) -> bool:
    with _open_connection(db_path) as conn:
        vec_enabled = _load_sqlite_vec(conn)
        cur = conn.cursor()
        cur.execute("BEGIN")

        if vec_enabled:
            cur.execute("DELETE FROM vec_face_encodings WHERE rowid = ?", (int(user_id),))

        cur.execute("DELETE FROM users WHERE id = ?", (int(user_id),))
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted


def count_people(db_path: Path = DB_PATH) -> int:
    with _open_connection(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return int(row[0]) if row else 0

def print_all_people(db_path: Path = DB_PATH, key_path: Path = KEY_PATH) -> None:
    key = _get_or_create_key(key_path)

    with _open_connection(db_path) as conn:
        rows = conn.execute("SELECT id, name_encrypted FROM users").fetchall()
        print("Registered people:")
        for user_id, name_encrypted in rows:
            name = _decrypt_name(name_encrypted, key)
            print(f"ID: {user_id}, Name: {name}, Encrypted: {name_encrypted}")



# def _get_or_create_key(key_path: Path = KEY_PATH) -> bytes:
#     '''
#     Get or create the encription key for the database. 
#     The key is used to encrypt the user names and stored in a db_key.key file.
#     '''
#     if key_path.exists():
#         key = key_path.read_bytes()
#         if len(key) != 32:
#             raise ValueError("Invalid key length in db_key.key")
#         return key

#     key = os.urandom(32)
#     key_path.write_bytes(key)
#     os.chmod(key_path, 0o600)
#     return key


# def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
#     '''
#     Generate a keystream of the given length using HMAC-SHA256 with the provided key and nonce.
#     '''
#     out = bytearray()
#     counter = 0
#     while len(out) < length:
#         block = hmac.new(key, nonce + counter.to_bytes(8, "little"), hashlib.sha256).digest()
#         out.extend(block)
#         counter += 1
#     return bytes(out[:length])


# def _encrypt_name(name: str, key: bytes) -> bytes:
#     plaintext = name.encode("utf-8")
#     nonce = os.urandom(16)
#     stream = _keystream(key, nonce, len(plaintext))
#     ciphertext = bytes(p ^ s for p, s in zip(plaintext, stream))
#     tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
#     return nonce + ciphertext + tag


# def _decrypt_name(payload: bytes, key: bytes) -> str:
#     if len(payload) < 48:
#         raise ValueError("Corrupted encrypted payload")

#     nonce = payload[:16]
#     tag = payload[-32:]
#     ciphertext = payload[16:-32]
#     expected = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
#     if not hmac.compare_digest(tag, expected):
#         raise ValueError("Encrypted payload integrity check failed")

#     stream = _keystream(key, nonce, len(ciphertext))
#     plaintext = bytes(c ^ s for c, s in zip(ciphertext, stream))
#     return plaintext.decode("utf-8")