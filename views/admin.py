import os
import json
import tarfile
import tempfile
import threading
import time
import uuid
import urllib.request
import shutil
import re
from flask import redirect, request, Response, url_for
from config import BUILD_LOGS_STORE, CHALLENGES_STORE
from data_store import load_data, save_data
from docker_ops import build_image_thread, build_log_path, terminate_instance
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
    url = request.form.get("url", "").strip()
    if not url.startswith(("https://", "http://")):
        return redirect(url_for("main.admin_challenges", error="Use an http:// or https:// archive URL"))
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz") as tmp:
            filepath = tmp.name
            req = urllib.request.Request(url, headers={"User-Agent": "CTFploy/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > 100 * 1024 * 1024:
                        raise ValueError("Archive is larger than the 100 MB limit")
                    tmp.write(chunk)

        build_dir = tempfile.mkdtemp(prefix="ctf_build_")
        with tarfile.open(filepath, "r:gz") as tar:
            members = tar.getmembers()
            if len(members) > 5_000:
                raise ValueError("Archive contains too many files")
            for member in members:
                destination = os.path.realpath(os.path.join(build_dir, member.name))
                if not destination.startswith(os.path.realpath(build_dir) + os.sep):
                    raise ValueError("Archive contains an unsafe file path")
                if member.issym() or member.islnk() or member.isdev():
                    raise ValueError("Archive links and device files are not allowed")
            tar.extractall(build_dir, members=members, filter="data")
        os.unlink(filepath)

        if not os.path.exists(os.path.join(build_dir, "Dockerfile")):
            dockerfile_dirs = [
                root
                for root, _, files in os.walk(build_dir)
                if "Dockerfile" in files
            ]
            if len(dockerfile_dirs) == 0:
                return redirect(url_for("main.admin_challenges", error="Archive must include a Dockerfile"))
            if len(dockerfile_dirs) > 1:
                return redirect(url_for("main.admin_challenges", error="Archive contains multiple Dockerfiles; use a single challenge package."))
            build_dir = dockerfile_dirs[0]

        metadata_path = os.path.join(build_dir, "ctfploy.json")
        meta = {}
        if os.path.exists(metadata_path):
            with open(metadata_path) as f:
                meta = json.load(f)

        name = str(meta.get("name", os.path.basename(url).replace(".tar.gz", "").replace(" ", "-").lower()))
        if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,62}", name):
            raise ValueError("Challenge name must use lowercase letters, numbers, dots, underscores, or hyphens")
        display_name = meta.get("display_name", name.replace("-", " ").title())
        internal_port = int(meta.get("internal_port", 22))
        if not 1 <= internal_port <= 65535:
            raise ValueError("internal_port must be between 1 and 65535")
        connection_type = meta.get("connection_type", "ssh")
        if connection_type not in {"ssh", "web", "nc"}:
            raise ValueError("connection_type must be ssh, web, or nc")
        flag_type = meta.get("flag_type", "static")
        if flag_type not in {"static", "dynamic"}:
            raise ValueError("flag_type must be static or dynamic")
        flag = meta.get("flag", "flag{change_me}")
        hints = meta.get("hints", [])
        if not isinstance(hints, list) or not all(isinstance(hint, str) for hint in hints):
            raise ValueError("hints must be a list of strings")

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
        os.makedirs(BUILD_LOGS_STORE, exist_ok=True)
        with open(build_log_path(challenge_id), "w", encoding="utf-8") as log:
            log.write("Build queued...\n")
        threading.Thread(target=build_image_thread, args=(name, build_dir, image_tag, challenge_id), daemon=True).start()
        return redirect(url_for("main.build_log_view", challenge_id=challenge_id))
    except Exception as e:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.unlink(filepath)
        if 'build_dir' in locals() and os.path.isdir(build_dir):
            shutil.rmtree(build_dir, ignore_errors=True)
        return redirect(url_for("main.admin_challenges", error=f"Build failed: {str(e)}"))


@admin_required
def build_log_view(challenge_id: str):
    return build_log_page(challenge_id)


@admin_required
def build_log_stream(challenge_id: str):
    log_path = build_log_path(challenge_id)

    def generate():
        offset = 0
        idle_polls = 0
        while idle_polls < 3_600:  # One hour keeps an abandoned tab from leaking a worker.
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="replace") as log:
                    log.seek(offset)
                    chunk = log.read()
                    offset = log.tell()
                if chunk:
                    idle_polls = 0
                    for line in chunk.splitlines():
                        yield f"data: {json.dumps(line)}\n\n"
                    continue
                data = load_data()
                challenge = next((c for c in data["challenges"] if c["id"] == challenge_id), None)
                if challenge and challenge.get("build_status") in {"success", "failed"}:
                    yield "event: complete\ndata: done\n\n"
                    return
            idle_polls += 1
            yield ": keep-alive\n\n"
            time.sleep(1)

    return Response(generate(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


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
