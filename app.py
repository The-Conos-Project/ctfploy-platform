#!/usr/bin/env python3
"""
Conos CTFploy Platform – Flask Application
"""
import os

from flask import Flask
from config import SECRET_KEY, CHALLENGES_STORE, SESSION_COOKIE_SECURE
from data_store import _init_db
from docker_ops import ensure_network
from routes import bp


app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=SESSION_COOKIE_SECURE,
)
app.register_blueprint(bp)

_init_db()
os.makedirs(CHALLENGES_STORE, exist_ok=True)
try:
    ensure_network()
except RuntimeError as exc:
    # Keep the UI available so an administrator can see and correct a missing
    # Docker socket rather than making the entire service return 502.
    app.logger.warning("Docker is unavailable during startup: %s", exc)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
