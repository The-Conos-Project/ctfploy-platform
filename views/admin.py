import os
import json
import tarfile
import tempfile
import threading
import time
import uuid
import urllib.request
import queue
from flask import redirect, request, Response, url_for
from config import CHALLENGES_STORE
from data_store import load_data, save_data
from docker_ops import build_image_thread, terminate_instance
from page_templates.templates import (
    admin_challenges_page,
    admin_codes_page,
    admin_dashboard_page,
    admin_update_page,
    build_log_page,
)
from views.utils import admin_required, request_flash_messages


@admin_required
def admin_dashboard():
    data = load_data()
    return admin_dashboard_page(data["challenges"], data["instances"], flashes=request_flash_messages())


@admin_required
def admin_challenges():
    data = load_data()
    return admin_challenges_page(data["challenges"])


@admin_required
def import_url():
    url = request.form["url"].strip()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz") as tmp:
            urllib.request.urlretrieve(url, tmp.name)
            filepath = tmp.name

        build_dir = f"/tmp/ctf_build_{int(time.time())}"
        os.makedirs(build_dir, exist_ok=True)
        with tarfile.open(filepath, "r:gz") as tar:
            tar.extractall(build_dir)
        os.unlink(filepath)

        metadata_path = os.path.join(build_dir, "ctfploy.json")
        meta = {}
        if os.path.exists(metadata_path):
            with open(metadata_path) as f:
                meta = json.load(f)

        name = meta.get("name", os.path.basename(url).replace(".tar.gz", "").replace(" ", "-").lower())
        display_name = meta.get("display_name", name.replace("-", " ").title())
        internal_port = meta.get("internal_port", 22)
        connection_type = meta.get("connection_type", "ssh")
        flag_type = meta.get("flag_type", "static")
        flag = meta.get("flag", "flag{change_me}")
        hints = meta.get("hints", [])

        image_tag = f"ctf-{name}"
        challenge_id = str(uuid.uuid4())[:8]
        challenge = {
            "id": challenge_id,
            "name": name,
            "display_name": display_name,
            "image_tag": image_tag,
            "internal_port": internal_port,
            "connection_type": connection_type,
            "flag_type": flag_type,
            "flag": flag,
            "hints": hints,
            "build_status": "building",
        }
        data = load_data()
        data["challenges"].append(challenge)
        save_data(data)
        threading.Thread(target=build_image_thread, args=(name, build_dir, image_tag, challenge_id), daemon=True).start()
        return redirect(url_for("main.build_log_view", challenge_id=challenge_id))
    except Exception as e:
        return redirect(url_for("main.admin_challenges", error=f"Build failed: {str(e)}"))


@admin_required
def build_log_view(challenge_id: str):
    return build_log_page(challenge_id)


@admin_required
def build_log_stream(challenge_id: str):
    from docker_ops import build_logs
    q = build_logs.get(challenge_id)
    if not q:
        q = queue.Queue()
        build_logs[challenge_id] = q

    def generate():
        while True:
            line = q.get()
            if line is None:
                yield "data: END\n\n"
                break
            yield f"data: {line}\n\n"
            time.sleep(0.05)

    return Response(generate(), mimetype="text/event-stream")


@admin_required
def delete_challenge(challenge_id: str):
    data = load_data()
    data["challenges"] = [c for c in data["challenges"] if c["id"] != challenge_id]
    save_data(data)
    return redirect(url_for("main.admin_challenges"))


@admin_required
def admin_codes():
    data = load_data()

    def get_challenge(cid: str):
        return next((c for c in data["challenges"] if c["id"] == cid), None)

    return admin_codes_page(data["access_codes"], data["challenges"], get_challenge, flashes=request_flash_messages())


@admin_required
def generate_code():
    data = load_data()
    code_str = f"CTF-{uuid.uuid4().hex[:6].upper()}"
    data["access_codes"].append({
        "code": code_str,
        "challenges": [],
        "used_by": []
    })
    save_data(data)
    return redirect(url_for("main.admin_codes"))


@admin_required
def add_challenge_to_code():
    data = load_data()
    code = request.form["code"]
    challenge_id = request.form["challenge_id"]
    for c in data["access_codes"]:
        if c["code"] == code and challenge_id not in c["challenges"]:
            c["challenges"].append(challenge_id)
    save_data(data)
    return redirect(url_for("main.admin_codes"))


@admin_required
def delete_code(code: str):
    data = load_data()
    data["access_codes"] = [c for c in data["access_codes"] if c["code"] != code]
    save_data(data)
    return redirect(url_for("main.admin_codes"))


@admin_required
def admin_update():
    if request.method == "POST":
        try:
            import subprocess
            subprocess.run(["docker", "pull", "zohidjonmarufov/ctfploy-platform:main"], check=True)
            subprocess.run(["docker", "compose", "-f", "/etc/ctfploy/docker-compose.yml", "up", "-d", "platform"], check=True)
            return redirect(url_for("main.admin_update", success="Platform updated successfully!"))
        except Exception as e:
            return redirect(url_for("main.admin_update", error=f"Update failed: {str(e)}"))

    return admin_update_page(flashes=request_flash_messages())
