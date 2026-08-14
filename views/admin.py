import os
import json
import tarfile
import tempfile
import threading
import time
import uuid
from datetime import datetime
import urllib.request
import shutil
import re
from flask import redirect, request, Response, url_for
from config import BUILD_LOGS_STORE, CHALLENGES_STORE
from data_store import load_data, save_data
from docker_ops import build_image_thread, build_log_path, terminate_instance
from page_templates.templates import (
    admin_challenges_page,
    admin_dashboard_page,
    admin_update_page,
    build_log_page,
    admin_classes_page,
    admin_class_detail_page,
)
from views.utils import admin_required, request_toast_messages


def _normalize_flag(item):
    if isinstance(item, str) and item.strip():
        return {"flag": item.strip(), "description": "", "hints": []}
    if isinstance(item, dict):
        flag = str(item.get("flag", "")).strip()
        if not flag:
            raise ValueError("each flag must include a non-empty flag property")
        description = str(item.get("description", ""))
        hints = item.get("hints", [])
        if not isinstance(hints, list) or not all(isinstance(hint, str) for hint in hints):
            raise ValueError("each flag hints must be a list of strings")
        return {"flag": flag, "description": description, "hints": hints}
    raise ValueError("each flag must be a string or an object with a flag property")


def _normalize_flags(raw):
    if not isinstance(raw, list) or not raw:
        raise ValueError("flags must be a non-empty list")
    normalized = [_normalize_flag(item) for item in raw]
    if len({item["flag"] for item in normalized}) != len(normalized):
        raise ValueError("flags must not contain duplicates")
    return normalized


@admin_required
def admin_dashboard():
    data = load_data()
    return admin_dashboard_page(data["challenges"], data["instances"], toasts=request_toast_messages())


@admin_required
def admin_challenges():
    data = load_data()
    return admin_challenges_page(data["challenges"], toasts=request_toast_messages())


@admin_required
def import_url():
    url = request.form.get("url", "").strip()
    class_id = request.form.get("class_id", "").strip() or None
    if not url.startswith(("https://", "http://")):
        return redirect(url_for("main.admin_challenges", error="Use an http:// or https:// archive URL"))
    try:
        data = load_data()
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
                # Archives created with tar commonly contain a root `.` entry.
                # It resolves to build_dir itself and is safe to extract.
                if member.name in {"", ".", "./"}:
                    continue
                destination = os.path.realpath(os.path.join(build_dir, member.name))
                build_root = os.path.realpath(build_dir)
                if destination != build_root and not destination.startswith(build_root + os.sep):
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
        description = meta.get("description", "")
        if not isinstance(description, str):
            raise ValueError("description must be a string")

        challenges_meta = meta.get("challenges", [])
        if challenges_meta:
            challenge_ids = []
            for ch_meta in challenges_meta:
                ch_name = str(ch_meta.get("name", ""))
                if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,62}", ch_name):
                    raise ValueError(f"Challenge name must use lowercase letters, numbers, dots, underscores, or hyphens: {ch_name}")
                ch_display_name = ch_meta.get("display_name", ch_name.replace("-", " ").title())
                ch_description = ch_meta.get("description", "")
                if not isinstance(ch_description, str):
                    raise ValueError("each challenge description must be a string")
                ch_flags = ch_meta.get("flags")
                normalized_flags = _normalize_flags(ch_flags)

                challenge_id = str(uuid.uuid4())[:8]
                challenge_ids.append(challenge_id)
                challenge = {
                    "id": challenge_id,
                    "name": ch_name,
                    "display_name": ch_display_name,
                    "image_tag": f"ctf-{name}",
                    "description": ch_description,
                    "flags": normalized_flags,
                    "build_status": "building",
                }
                data["challenges"].append(challenge)
        else:
            flags = meta.get("flags")
            normalized_flags = _normalize_flags(flags)

            image_tag = f"ctf-{name}"
            challenge_id = str(uuid.uuid4())[:8]
            challenge_ids = [challenge_id]
            challenge = {
                "id": challenge_id,
                "name": name,
                "display_name": display_name,
                "image_tag": image_tag,
                "description": description,
                "flags": normalized_flags,
                "build_status": "building",
            }
            data["challenges"].append(challenge)

        save_data(data)
        os.makedirs(BUILD_LOGS_STORE, exist_ok=True)
        log_path = build_log_path(f"ctf-{name}")
        with open(log_path, "w", encoding="utf-8") as log:
            log.write("Build queued...\n")
        image_tag = f"ctf-{name}"
        threading.Thread(target=build_image_thread, args=(name, build_dir, image_tag, challenge_ids, class_id), daemon=True).start()
        if class_id:
            return redirect(url_for("main.build_log_view", challenge_id=challenge_ids[0], class_id=class_id))
        return redirect(url_for("main.build_log_view", challenge_id=challenge_ids[0]))
    except Exception as e:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.unlink(filepath)
        if 'build_dir' in locals() and os.path.isdir(build_dir):
            shutil.rmtree(build_dir, ignore_errors=True)
        class_id_err = request.form.get("class_id", "").strip()
        if class_id_err:
            return redirect(url_for("main.admin_class_detail", class_id=class_id_err, error=f"Build failed: {str(e)}"))
        return redirect(url_for("main.admin_challenges", error=f"Build failed: {str(e)}"))


@admin_required
def build_log_view(challenge_id: str):
    class_id = request.args.get("class_id")
    return build_log_page(challenge_id, class_id=class_id)


@admin_required
def build_log_stream(challenge_id: str):
    data = load_data()
    challenge = next((c for c in data["challenges"] if c["id"] == challenge_id), None)
    if not challenge:
        return Response("", mimetype="text/event-stream")
    image_tag = challenge.get("image_tag", challenge_id)
    log_path = build_log_path(image_tag)

    def generate():
        offset = 0
        idle_polls = 0
        while idle_polls < 3_600:
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
                related = [c for c in data["challenges"] if c.get("image_tag") == image_tag]
                if any(c.get("build_status") in {"ready", "failed"} for c in related):
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
def admin_classes():
    data = load_data()
    return admin_classes_page(data["classes"], data["challenges"], data["users"], toasts=request_toast_messages())


@admin_required
def admin_class_detail(class_id: str):
    data = load_data()
    classroom = next((c for c in data["classes"] if c["id"] == class_id), None)
    if not classroom:
        return redirect(url_for("main.admin_classes", error="Class not found"))
    return admin_class_detail_page(classroom, data["challenges"], data["users"], toasts=request_toast_messages())


@admin_required
def create_class():
    name = request.form.get("name", "").strip()
    if not name or len(name) > 80:
        return redirect(url_for("main.admin_classes", error="Enter a class name up to 80 characters"))
    data = load_data()
    data["classes"].append({
        "id": uuid.uuid4().hex[:8], "name": name,
        "join_code": f"CLASS-{uuid.uuid4().hex[:6].upper()}",
        "challenge_ids": [], "member_ids": [], "created_at": datetime.now().isoformat(),
    })
    save_data(data)
    return redirect(url_for("main.admin_classes", success="Class created"))


@admin_required
def assign_challenge_to_class():
    class_id, challenge_id = request.form.get("class_id"), request.form.get("challenge_id")
    data = load_data()
    classroom = next((c for c in data["classes"] if c["id"] == class_id), None)
    challenge = next((c for c in data["challenges"] if c["id"] == challenge_id and c["build_status"] == "ready"), None)
    if not classroom or not challenge:
        return redirect(url_for("main.admin_classes", error="Choose a valid ready challenge and class"))
    if challenge_id not in classroom["challenge_ids"]:
        classroom["challenge_ids"].append(challenge_id)
        save_data(data)
    return redirect(url_for("main.admin_class_detail", class_id=class_id, success="Challenge assigned"))


@admin_required
def delete_class(class_id):
    data = load_data()
    data["classes"] = [c for c in data["classes"] if c["id"] != class_id]
    save_data(data)
    return redirect(url_for("main.admin_classes", success="Class deleted"))


@admin_required
def remove_challenge_from_class():
    class_id = request.form.get("class_id", "").strip()
    challenge_id = request.form.get("challenge_id", "").strip()
    data = load_data()
    classroom = next((c for c in data["classes"] if c["id"] == class_id), None)
    if classroom and challenge_id in classroom.get("challenge_ids", []):
        classroom["challenge_ids"] = [cid for cid in classroom["challenge_ids"] if cid != challenge_id]
        save_data(data)
    return redirect(url_for("main.admin_class_detail", class_id=class_id, success="Challenge removed"))


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

    return admin_update_page(toasts=request_toast_messages())
