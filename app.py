#!/usr/bin/env python3
"""
Conos CTFploy Platform – Flask Application
"""
from flask import Flask
from config import SECRET_KEY
from routes import bp


app = Flask(__name__)
app.secret_key = SECRET_KEY
app.register_blueprint(bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
