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
    '''
    Encrypt the user name with Fernet symetric encryption.
    '''
    cipher = Fernet(key)
    
    return cipher.encrypt(name.encode("utf-8"))


def _decrypt_name(payload: bytes, key: bytes) -> str:
    '''
    Decrypt the user name with Fernet symetric encryption.
    '''
    cipher = Fernet(key)

    return cipher.decrypt(payload).decode("utf-8")


def _vector_to_blob(vector: np.ndarray) -> bytes:
    '''
    Convert a NumPy array to a Binary Large Object (BLOB) for storage in SQLite.
    The vector is expected to be a 128-dimensional float32 array.
    '''
    arr = np.asarray(vector, dtype=np.float32).reshape(-1)
    if arr.shape[0] != ENCODING_SIZE:
        raise ValueError(f"Expected vector with {ENCODING_SIZE} values, got {arr.shape[0]}")
    return arr.tobytes()


def _blob_to_vector(blob: bytes) -> np.ndarray:
    '''
    Convert a Binary Large Object (BLOB) to a NumPy array.
    The vector is expected to be a 128-dimensional float32 array.
    '''
    arr = np.frombuffer(blob, dtype=np.float32)
    if arr.shape[0] != ENCODING_SIZE:
        raise ValueError("Stored encoding has invalid size")
    return arr


def _open_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    '''
    Open a connection to the SQLite database.

    Enable foreign key (i.e. a column (or group of columns) in one table that references the primary key of another table.)
    '''
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _load_sqlite_vec(conn: sqlite3.Connection) -> bool:
    '''
    Loads the sqlite-vec extension

    So we can search the database using vector similarity, much faster than doing it in Python.
    '''
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
    '''
    Create the key to the database if it does not exist

    Create the database and tables if they do not exist
        - users: stores the user_id and the encrypted name
        - face_encodings: stores the user_id and the face encoding as a BLOB
        - vec_face_encodings: virtual table for vector search (if sqlite-vec is available)
    '''
    
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
    '''
    Register a new face in the database. 
    
    Returns the user_id of the new entry.
    '''
    
    key = _get_or_create_key(key_path)
    encrypted_name = _encrypt_name(name, key)
    encoding_blob = _vector_to_blob(encoding_vector)

    with _open_connection(db_path) as conn:
        vec_enabled = _load_sqlite_vec(conn)
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute("INSERT INTO users(name_encrypted) VALUES (?)", (encrypted_name,))
        user_id = int(cur.lastrowid) # The foreign key in face_encodings and vec_face_encodings tables
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
    '''
    Try to use vectorial search to find the most similar user

    If it is not possible, fallback to calculate the distance of all users with NumPy

    Returns a dict if we have a match, else returns None
    '''
    key = _get_or_create_key(key_path)
    query_blob = _vector_to_blob(query_vector)

    with _open_connection(db_path) as conn:
        vec_enabled = _load_sqlite_vec(conn)
        user_id = None
        distance = None

        # Vectorial search
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

        # Fallback when we don't have sqlite-vec our SQL didn't return any candidate
        if user_id is None:
            # WARNING: This brings all users to memory...maybe it can overflow (but the encodes are small, it should suffice for a good number os users)
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
    '''
    Atomic deletion of a user by user_id. (LGPD - Right to be forgotten)
    
    Returns True if a user was deleted, False if no such user_id exists.
    '''
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
    '''
    Returns the total number of registered people in the database.
    '''
    with _open_connection(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return int(row[0]) if row else 0

def print_all_people(db_path: Path = DB_PATH, key_path: Path = KEY_PATH) -> None:
    '''
    Prints all registered users.
    '''
    key = _get_or_create_key(key_path)

    with _open_connection(db_path) as conn:
        rows = conn.execute("SELECT id, name_encrypted FROM users").fetchall()
        print("Registered people:")
        for user_id, name_encrypted in rows:
            name = _decrypt_name(name_encrypted, key)
            print(f"ID: {user_id}, Name: {name}, Encrypted: {name_encrypted}")
