import json, os, hashlib
from typing import Optional

DATA_FILE = "/data/data.json"


def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"challenges": [], "access_codes": [], "instances": [], "users": []}
    with open(DATA_FILE) as f:
        data = json.load(f)
        for key in ["challenges", "access_codes", "instances", "users"]:
            if key not in data:
                data[key] = []
        return data


def save_data(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def get_user(username: str) -> Optional[dict]:
    data = load_data()
    for u in data["users"]:
        if u["username"] == username:
            return u
    return None


def get_user_by_id(uid: str, data: Optional[dict] = None) -> Optional[dict]:
    if data is None:
        data = load_data()
    for u in data["users"]:
        if u["id"] == uid:
            return u
    return None
