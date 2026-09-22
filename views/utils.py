from functools import wraps
from flask import flash, get_flashed_messages, redirect, request, session, url_for


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


def toast_success(message: str) -> None:
    flash(message, "success")


def toast_error(message: str) -> None:
    flash(message, "error")


def request_toast_messages():
    """Session flashes — shown once, then cleared (no URL query params)."""
    return list(get_flashed_messages(with_categories=True))


# Back-compat alias
request_flash_messages = request_toast_messages
