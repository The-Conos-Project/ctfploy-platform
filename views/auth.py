import uuid
from flask import redirect, request, session, url_for
from config import ADMIN_PASSWORD
from data_store import get_user, get_user_by_id, load_data, save_data, hash_password, verify_password
from page_templates.auth import register_page, sign_in_page, admin_sign_in_page
from page_templates.home import landing_page


def index():
    return landing_page()


def sign_in():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        user = get_user(username)
        if user and verify_password(password, user["password_hash"]):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("main.dashboard"))
        return sign_in_page(error=True)
    return sign_in_page()


def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        if get_user(username):
            return register_page(error=True)
        data = load_data()
        new_user = {
            "id": str(uuid.uuid4())[:8],
            "username": username,
            "password_hash": hash_password(password)
        }
        data["users"].append(new_user)
        save_data(data)
        session["user_id"] = new_user["id"]
        session["username"] = new_user["username"]
        return redirect(url_for("main.dashboard"))
    return register_page()


def logout():
    session.clear()
    return redirect(url_for("main.sign_in"))


def admin_sign_in():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"].strip()
        if username == "root" and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("main.admin_dashboard"))
        return admin_sign_in_page(error=True)
    return admin_sign_in_page()


def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("main.admin_sign_in"))
