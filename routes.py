import os, threading, tarfile, tempfile, time, uuid, urllib.request, queue
from datetime import datetime, timedelta
from flask import Blueprint, redirect, render_template_string, request, session, url_for, Response
import docker

from config import INSTANCE_TIMEOUT, MAX_CONCURRENT_PER_USER
from data_store import get_user, get_user_by_id, hash_password, load_data, save_data
from docker_ops import build_image_thread, create_container, terminate_instance, ensure_network, build_logs
from templates import (
    admin_codes_page,
    admin_dashboard_page,
    admin_challenges_page,
    admin_update_page,
    build_log_page,
    dashboard_page,
    hub_page,
    instance_page,
    register_page,
    sign_in_page,
)

bp = Blueprint("main", __name__)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("main.sign_in"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("main.admin_sign_in"))
        return f(*args, **kwargs)
    return decorated


def _flashes_from_request():
    flashes = []
    success = request.args.get("success")
    error = request.args.get("error")
    if success:
        flashes.append(("success", success))
    if error:
        flashes.append(("error", error))
    return flashes


@bp.route("/")
def index():
    return render_template_string("""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card" style="text-align:center;">
                <h2 style="font-size:1.8rem; margin-bottom:8px; font-weight:600;">Conos CTFploy</h2>
                <p style="color:#888; margin-bottom:24px;">Self-hosted CTF platform. Deploy, manage, and solve challenges.</p>
                <a href="/sign-in"><button style="font-size:1rem; width:auto; padding:10px 24px;">Get Started</button></a>
            </div>
        </div>
    </div>
    """)


@bp.route("/sign-in", methods=["GET", "POST"])
def sign_in():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        user = get_user(username)
        if user and user["password_hash"] == hash_password(password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("main.dashboard"))
        return sign_in_page(error=True)
    return sign_in_page()


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        if get_user(username):
            return register_page(error=True)
        data = load_data()
        new_user = {"id": str(uuid.uuid4())[:8], "username": username, "password_hash": hash_password(password), "used_codes": []}
        data["users"].append(new_user)
        save_data(data)
        session["user_id"] = new_user["id"]
        session["username"] = new_user["username"]
        return redirect(url_for("main.dashboard"))
    return register_page()


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.sign_in"))


@bp.route("/dashboard")
@login_required
def dashboard():
    data = load_data()
    user = get_user_by_id(session["user_id"])
    user_challenges = []
    for code in data["access_codes"]:
        if code["code"] in user.get("used_codes", []):
            for cid in code["challenges"]:
                ch = next((c for c in data["challenges"] if c["id"] == cid), None)
                if ch and ch["build_status"] == "success":
                    user_challenges.append(ch)
    instances = [i for i in data["instances"] if i["user_id"] == user["id"] and i["status"] == "running"]

    def get_instance(uid, cid):
        return next((i for i in instances if i["user_id"] == uid and i["challenge_id"] == cid), None)

    flashes = _flashes_from_request()
    return dashboard_page(user, user_challenges, get_instance, flashes=flashes)


@bp.route("/user/redeem-code", methods=["POST"])
@login_required
def redeem_code():
    code = request.form["code"].strip()
    data = load_data()
    code_entry = next((c for c in data["access_codes"] if c["code"] == code), None)
    if not code_entry:
        return redirect(url_for("main.dashboard", error="Invalid code"))
    user = next((u for u in data["users"] if u["id"] == session["user_id"]), None)
    if not user:
        return redirect(url_for("main.dashboard", error="User not found"))
    if code in user.get("used_codes", []):
        return redirect(url_for("main.dashboard", error="You have already used this code."))
    user.setdefault("used_codes", []).append(code)
    username = user["username"]
    if username not in code_entry.get("used_by", []):
        code_entry.setdefault("used_by", []).append(username)
    save_data(data)
    return redirect(url_for("main.dashboard", success="Code unlocked successfully!"))


@bp.route("/start/<challenge_id>")
@login_required
def start_challenge(challenge_id):
    data = load_data()
    user = get_user_by_id(session["user_id"])
    challenge = next((c for c in data["challenges"] if c["id"] == challenge_id and c["build_status"] == "success"), None)
    if not challenge:
        return redirect(url_for("main.dashboard", error="Challenge not found or not ready"))
    allowed = False
    for code in data["access_codes"]:
        if code["code"] in user.get("used_codes", []) and challenge_id in code["challenges"]:
            allowed = True
            break
    if not allowed:
        return redirect(url_for("main.dashboard", error="Access denied"))
    instance, err = create_container(challenge, user["id"])
    if err:
        return redirect(url_for("main.dashboard", error=err))
    return redirect(url_for("main.view_instance", instance_id=instance["id"]))


@bp.route("/instance/<instance_id>")
@login_required
def view_instance(instance_id):
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if not instance:
        return redirect(url_for("main.dashboard", error="Instance not found"))
    challenge = next((c for c in data["challenges"] if c["id"] == instance["challenge_id"]), None)
    host = request.host.split(":")[0]
    msg = request.args.get("msg") or request.args.get("success") or request.args.get("error")
    hints = challenge.get("hints", [])
    return instance_page(challenge, instance, host, msg, hints)


@bp.route("/terminate/<instance_id>")
@login_required
def terminate(instance_id):
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if instance:
        terminate_instance(instance_id)
    return redirect(url_for("main.dashboard"))


@bp.route("/submit_flag/<instance_id>", methods=["POST"])
@login_required
def submit_flag(instance_id):
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if not instance:
        return redirect(url_for("main.dashboard", error="Instance not found"))
    submitted = request.form["flag"].strip()
    challenge = next((c for c in data["challenges"] if c["id"] == instance["challenge_id"]), None)
    correct = instance.get("dynamic_flag") if challenge.get("flag_type") == "dynamic" else challenge.get("flag")
    msg = "Correct!" if correct and submitted == correct else "Incorrect"
    return redirect(url_for("main.view_instance", instance_id=instance_id, msg=msg))


# ---------- ADMIN ----------
@bp.route("/admin/sign-in", methods=["GET", "POST"])
def admin_sign_in():
    if request.method == "POST":
        if request.form.get("password") == "admin123":
            session["admin"] = True
            return redirect(url_for("main.admin_dashboard"))
        return sign_in_page(error=True)
    return sign_in_page()


@bp.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("main.admin_sign_in"))


@bp.route("/admin")
@admin_required
def admin_dashboard():
    data = load_data()
    return admin_dashboard_page(data["challenges"], data["instances"])


@bp.route("/admin/challenges", methods=["GET"])
@admin_required
def admin_challenges():
    data = load_data()
    store_files = []
    if os.path.isdir("/data/challenges_store"):
        store_files = [f for f in os.listdir("/data/challenges_store") if f.endswith(".tar.gz")]
    return admin_challenges_page(data["challenges"], store_files)


@bp.route("/admin/import-url", methods=["POST"])
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

        name = meta.get("name", os.path.basename(url).replace(".tar.gz","").replace(" ","-").lower())
        display_name = meta.get("display_name", name.replace("-"," ").title())
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
        return f"Error: {str(e)}", 500


@bp.route("/admin/build-from-store", methods=["POST"])
@admin_required
def build_from_store():
    filename = request.form["filename"].strip()
    filepath = os.path.join("/data/challenges_store", filename)
    if not os.path.exists(filepath):
        return "File not found", 400
    build_dir = f"/tmp/ctf_build_{int(time.time())}"
    os.makedirs(build_dir, exist_ok=True)
    with tarfile.open(filepath, "r:gz") as tar:
        tar.extractall(build_dir)

    metadata_path = os.path.join(build_dir, "ctfploy.json")
    meta = {}
    if os.path.exists(metadata_path):
        with open(metadata_path) as f:
            meta = json.load(f)

    name = meta.get("name", filename.replace(".tar.gz","").replace(" ","-").lower())
    display_name = meta.get("display_name", name.replace("-"," ").title())
    internal_port = meta.get("internal_port", 22)
    connection_type = meta.get("connection_type", "ssh")
    flag_type = meta.get("flag_type", "static")
    flag = meta.get("flag", "flag{default}")
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
        "build_status": "building",
    }
    data = load_data()
    data["challenges"].append(challenge)
    save_data(data)
    threading.Thread(target=build_image_thread, args=(name, build_dir, image_tag, challenge_id), daemon=True).start()
    return redirect(url_for("main.build_log_view", challenge_id=challenge_id))


@bp.route("/admin/build_log/<challenge_id>")
@admin_required
def build_log_view(challenge_id):
    return build_log_page(challenge_id)


@bp.route("/admin/build_log_stream/<challenge_id>")
@admin_required
def build_log_stream(challenge_id):
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


@bp.route("/admin/delete_challenge/<challenge_id>")
@admin_required
def delete_challenge(challenge_id):
    data = load_data()
    data["challenges"] = [c for c in data["challenges"] if c["id"] != challenge_id]
    for inst in data["instances"]:
        if inst["challenge_id"] == challenge_id and inst["status"] == "running":
            terminate_instance(inst["id"])
    save_data(data)
    return redirect(url_for("main.admin_challenges"))


@bp.route("/admin/codes", methods=["GET"])
@admin_required
def admin_codes():
    data = load_data()
    def get_challenge(cid):
        return next((c for c in data["challenges"] if c["id"] == cid), None)
    return admin_codes_page(data["access_codes"], data["challenges"], get_challenge)


@bp.route("/admin/gencode", methods=["POST"])
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


@bp.route("/admin/add_challenge_to_code", methods=["POST"])
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


@bp.route("/admin/delete_code/<code>")
@admin_required
def delete_code(code):
    data = load_data()
    data["access_codes"] = [c for c in data["access_codes"] if c["code"] != code]
    save_data(data)
    return redirect(url_for("main.admin_codes"))


@bp.route("/admin/update", methods=["GET", "POST"])
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
    flashes = _flashes_from_request()
    return admin_update_page(flashes=flashes)


# ---------- HUB ----------
@bp.route("/hub")
def hub():
    query = request.args.get("q", "").strip().lower()
    challenges = _fetch_hub_challenges()
    if query:
        challenges = [c for c in challenges if query in c["display_name"].lower() or query in c["name"].lower()]
    return hub_page(challenges, query)


@bp.route("/hub/import", methods=["POST"])
@admin_required
def hub_import():
    url = request.form.get("url", "").strip()
    if not url:
        return redirect(url_for("main.hub", error="Missing URL"))
    return redirect(url_for("main.admin_import_url_proxy", url=url))


@bp.route("/admin/import-url-proxy", methods=["POST"])
@admin_required
def admin_import_url_proxy():
    url = request.form.get("url", "").strip()
    if not url:
        return redirect(url_for("main.admin_challenges", error="Missing URL"))
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

        name = meta.get("name", os.path.basename(url).replace(".tar.gz","").replace(" ","-").lower())
        display_name = meta.get("display_name", name.replace("-"," ").title())
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
        return redirect(url_for("main.hub", error=str(e)))


def _fetch_hub_challenges():
    challenges = []
    try:
        api_url = "https://api.github.com/repos/The-Conos-Project/ctf-challenges/contents/challenges"
        req = urllib.request.Request(api_url, headers={"User-Agent": "CTFploy"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            items = json.loads(resp.read())

        for item in items:
            if item.get("type") != "dir":
                continue
            name = item["name"]
            folder_url = f"https://api.github.com/repos/The-Conos-Project/ctf-challenges/contents/challenges/{name}"
            req2 = urllib.request.Request(folder_url, headers={"User-Agent": "CTFploy"})
            try:
                with urllib.request.urlopen(req2, timeout=10) as resp2:
                    files = json.loads(resp2.read())
            except Exception:
                continue

            md_file = next((f for f in files if f.get("name", "").endswith(".md")), None)
            tar_file = next((f for f in files if f.get("name", "").endswith(".tar.gz")), None)
            if not md_file or not tar_file:
                continue

            try:
                with urllib.request.urlopen(md_file.get("download_url", ""), timeout=10) as resp3:
                    md_content = resp3.read().decode("utf-8", errors="ignore")
            except Exception:
                continue

            meta = _parse_md_frontmatter(md_content)
            meta.setdefault("name", name)
            meta.setdefault("display_name", name.replace("-", " ").title())
            meta.setdefault("internal_port", 22)
            meta.setdefault("connection_type", "ssh")
            meta.setdefault("flag_type", "static")
            meta.setdefault("flag", "flag{change_me}")
            meta.setdefault("hints", [])
            meta["download_url"] = tar_file.get("download_url", "")
            challenges.append(meta)
    except Exception:
        pass
    return challenges


def _parse_md_frontmatter(text: str) -> dict:
    meta = {}
    if not text.startswith("---"):
        return meta
    end = text.find("---", 3)
    if end == -1:
        return meta
    block = text[3:end].strip()
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        meta[key] = value
    return meta


# ---------- STARTUP ----------
@bp.before_app_first_request
def startup():
    ensure_network()
    os.makedirs("/data/challenges_store", exist_ok=True)
