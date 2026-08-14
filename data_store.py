import json
import os
import sqlite3
import hashlib
import hmac
import secrets
from typing import Optional

from config import DATA_DB, DATA_JSON, HASH_ITERATIONS, HASH_SALT_BYTES


def _connect():
    os.makedirs(os.path.dirname(DATA_DB), exist_ok=True)
    conn = sqlite3.connect(DATA_DB, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS challenges (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                display_name TEXT,
                description TEXT,
                image_tag TEXT,
                flags TEXT,
                build_status TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS instances (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                challenge_id TEXT,
                container_id TEXT,
                container_name TEXT,
                host_port INTEGER,
                connection_type TEXT,
                status TEXT,
                created_at TEXT,
                expires_at TEXT,
                dynamic_flag TEXT,
                flag TEXT,
                submitted_flags TEXT,
                username TEXT,
                password TEXT
            )
            """
        )
        _ensure_column(cursor, "challenges", "flags", "TEXT")
        _ensure_column(cursor, "challenges", "description", "TEXT")
        _ensure_column(cursor, "instances", "submitted_flags", "TEXT")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS classes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                join_code TEXT UNIQUE NOT NULL,
                challenge_ids TEXT NOT NULL,
                member_ids TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _ensure_column(cursor, table: str, column: str, definition: str) -> None:
    """Add a column for deployments created before a schema change."""
    columns = {row["name"] for row in cursor.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _serialize(value):
    return json.dumps(value, separators=(",", ":"), default=str)


def _deserialize(value):
    return json.loads(value) if value else []


def _migrate_json():
    """Import the legacy JSON store once, even though SQLite has been initialized."""
    if not os.path.exists(DATA_JSON):
        return
    _init_db()
    with _connect() as conn:
        migrated = conn.execute(
            "SELECT 1 FROM settings WHERE key = 'json_migration_complete'"
        ).fetchone()
    if migrated:
        return
    with open(DATA_JSON, encoding="utf-8") as f:
        data = json.load(f)
    save_data(data)
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("json_migration_complete", "1"),
        )
        conn.commit()


def load_data() -> dict:
    _init_db()
    _migrate_json()
    with _connect() as conn:
        cursor = conn.cursor()
        users = [
            {
                **dict(row)
            }
            for row in cursor.execute("SELECT * FROM users")
        ]
        challenges = [
            {
                **dict(row),
                "flags": _deserialize(row["flags"]),
            }
            for row in cursor.execute("SELECT * FROM challenges")
        ]
        instances = [
            {**dict(row), "submitted_flags": _deserialize(row["submitted_flags"])}
            for row in cursor.execute("SELECT * FROM instances")
        ]
        classes = [
            {**dict(row), "challenge_ids": _deserialize(row["challenge_ids"]), "member_ids": _deserialize(row["member_ids"])}
            for row in cursor.execute("SELECT * FROM classes")
        ]
        return {
            "users": users,
            "challenges": challenges,
            "instances": instances,
            "classes": classes,
        }


def save_data(data: dict) -> None:
    _init_db()
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM challenges")
        cursor.execute("DELETE FROM instances")
        cursor.execute("DELETE FROM classes")

        for user in data.get("users", []):
            cursor.execute(
                "INSERT OR REPLACE INTO users (id, username, password_hash) VALUES (?, ?, ?)",
                (
                    user["id"],
                    user["username"],
                    user["password_hash"],
                ),
            )

        for challenge in data.get("challenges", []):
            cursor.execute(
                "INSERT OR REPLACE INTO challenges (id, name, display_name, description, image_tag, flags, build_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    challenge["id"],
                    challenge["name"],
                    challenge.get("display_name"),
                    challenge.get("description", ""),
                    challenge.get("image_tag"),
                    _serialize(challenge.get("flags", [])),
                    challenge.get("build_status"),
                ),
            )

        for instance in data.get("instances", []):
            cursor.execute(
                "INSERT OR REPLACE INTO instances (id, user_id, challenge_id, container_id, container_name, host_port, status, created_at, expires_at, dynamic_flag, flag, submitted_flags, username, password) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    instance["id"],
                    instance.get("user_id"),
                    instance.get("challenge_id"),
                    instance.get("container_id"),
                    instance.get("container_name"),
                    instance.get("host_port"),
                    instance.get("status"),
                    instance.get("created_at"),
                    instance.get("expires_at"),
                    instance.get("dynamic_flag"),
                    instance.get("flag"),
                    _serialize(instance.get("submitted_flags", [])),
                    instance.get("username"),
                    instance.get("password"),
                ),
            )
        for classroom in data.get("classes", []):
            cursor.execute(
                "INSERT OR REPLACE INTO classes (id, name, join_code, challenge_ids, member_ids, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (classroom["id"], classroom["name"], classroom["join_code"], _serialize(classroom.get("challenge_ids", [])), _serialize(classroom.get("member_ids", [])), classroom["created_at"]),
            )
        conn.commit()


def hash_password(pw: str, salt: Optional[str] = None) -> str:
    if salt is None:
        salt = secrets.token_hex(HASH_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), HASH_ITERATIONS)
    return f"{salt}${HASH_ITERATIONS}${dk.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        salt, iterations, digest = stored.split("$")
        derived = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), int(iterations)).hex()
        return hmac.compare_digest(derived, digest)
    except Exception:
        return False


def get_user(username: str) -> Optional[dict]:
    _init_db()
    _migrate_json()
    with _connect() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            return None
        user = dict(row)
        return user


def get_user_by_id(uid: str, data: Optional[dict] = None) -> Optional[dict]:
    if data is not None:
        return next((u for u in data.get("users", []) if u["id"] == uid), None)
    _init_db()
    with _connect() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
        if not row:
            return None
        user = dict(row)
        return user
