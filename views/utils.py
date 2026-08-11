from functools import wraps
from flask import redirect, request, session, url_for


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("main.sign_in"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("main.admin_sign_in"))
        return f(*args, **kwargs)
    return decorated


def request_flash_messages():
    flashes = []
    success = request.args.get("success")
    error = request.args.get("error")
    if success:
        flashes.append(("success", success))
    if error:
        flashes.append(("error", error))
    return flashes
