#!/usr/bin/env python3
"""
Conos CTFploy Platform – Flask Application
"""
import os

from flask import Flask
from config import SECRET_KEY, CHALLENGES_STORE
from docker_ops import ensure_network
from routes import bp


app = Flask(__name__)
app.secret_key = SECRET_KEY
app.register_blueprint(bp)

ensure_network()
os.makedirs(CHALLENGES_STORE, exist_ok=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
