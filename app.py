#!/usr/bin/env python3
"""
Conos CTFploy Platform – Flask Application
"""
import os, json, time, random, uuid, threading, queue, tarfile, hashlib, subprocess, tempfile, urllib.request
from datetime import datetime, timedelta
from flask import Flask, request, redirect, render_template_string, session, url_for, Response, flash
import docker

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24).hex())
INSTANCE_TIMEOUT = int(os.environ.get("INSTANCE_TIMEOUT", 30 * 60))
MAX_CONCURRENT_PER_USER = int(os.environ.get("MAX_CONCURRENT_PER_USER", 3))
DATA_FILE = "/data/data.json"
DOCKER_NETWORK = "ctf_net"
CHALLENGES_STORE = "/data/challenges_store"

app = Flask(__name__)
app.secret_key = SECRET_KEY

docker_client = docker.from_env()
build_logs = {}

# ---------- DATA STORAGE (JSON) ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"challenges": [], "access_codes": [], "instances": [], "users": []}
    with open(DATA_FILE) as f:
        data = json.load(f)
        for key in ["challenges", "access_codes", "instances", "users"]:
            if key not in data:
                data[key] = []
        return data

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

# ---------- USER HELPERS ----------
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_user(username):
    data = load_data()
    for u in data["users"]:
        if u["username"] == username:
            return u
    return None

def get_user_by_id(uid):
    data = load_data()
    for u in data["users"]:
        if u["id"] == uid:
            return u
    return None

# ---------- DOCKER ----------
def ensure_network():
    try:
        docker_client.networks.get(DOCKER_NETWORK)
    except docker.errors.NotFound:
        docker_client.networks.create(DOCKER_NETWORK, driver="bridge")

def build_image_thread(name, build_dir, tag, challenge_id):
    q = build_logs.get(challenge_id)
    if not q:
        q = queue.Queue()
        build_logs[challenge_id] = q
    try:
        q.put("🔨 Build started...\n")
        img, logs = docker_client.images.build(path=build_dir, tag=tag, rm=True)
        for chunk in logs:
            if "stream" in chunk:
                q.put(chunk["stream"])
            elif "error" in chunk:
                q.put(f"ERROR: {chunk['error']}\n")
        q.put("✅ Build completed successfully!\n")
        data = load_data()
        for ch in data["challenges"]:
            if ch["id"] == challenge_id:
                ch["build_status"] = "success"
        save_data(data)
    except Exception as e:
        q.put(f"❌ Build failed: {str(e)}\n")
        data = load_data()
        for ch in data["challenges"]:
            if ch["id"] == challenge_id:
                ch["build_status"] = "failed"
        save_data(data)
    finally:
        q.put(None)

def create_container(challenge, user_id):
    data = load_data()
    user_instances = [i for i in data["instances"] if i["user_id"] == user_id and i["status"] == "running"]
    if len(user_instances) >= MAX_CONCURRENT_PER_USER:
        return None, "Maximum concurrent instances reached"

    port = random.randint(10000, 60000)
    image_tag = challenge["image_tag"]
    internal_port = challenge["internal_port"]

    env = {}
    dyn_flag = None
    if challenge.get("flag_type") == "dynamic":
        dyn_flag = f"flag{{{uuid.uuid4()}}}"
        env["FLAG"] = dyn_flag

    container_name = f"ctf_{challenge['id']}_{int(time.time())}"
    try:
        container = docker_client.containers.run(
            f"{image_tag}:latest",
            detach=True,
            name=container_name,
            ports={f"{internal_port}/tcp": port},
            environment=env,
            mem_limit="512m",
            nano_cpus=int(0.5 * 1e9),
            network=DOCKER_NETWORK,
            remove=True
        )
    except Exception as e:
        return None, f"Docker error: {e}"

    instance = {
        "id": str(uuid.uuid4())[:8],
        "user_id": user_id,
        "challenge_id": challenge["id"],
        "container_id": container.id,
        "container_name": container_name,
        "host_port": port,
        "connection_type": challenge["connection_type"],
        "status": "running",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(seconds=INSTANCE_TIMEOUT)).isoformat(),
        "dynamic_flag": dyn_flag,
        "flag": challenge.get("flag", "")
    }
    data["instances"].append(instance)
    save_data(data)
    threading.Thread(target=auto_terminate, args=(instance["id"], INSTANCE_TIMEOUT), daemon=True).start()
    return instance, None

def terminate_instance(instance_id):
    data = load_data()
    inst = next((i for i in data["instances"] if i["id"] == instance_id), None)
    if inst and inst["status"] == "running":
        try:
            container = docker_client.containers.get(inst["container_id"])
            container.stop(timeout=3)
        except:
            pass
        inst["status"] = "terminated"
        inst["terminated_at"] = datetime.now().isoformat()
        save_data(data)
        return True
    return False

def auto_terminate(instance_id, delay):
    time.sleep(delay)
    with app.app_context():
        terminate_instance(instance_id)

# ---------- CSS (centered, sidebar admin) ----------
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600&display=swap');
@import url('https://cdn.jsdelivr.net/npm/devicons@1.8.0/css/devicons.min.css');
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: 'Space Grotesk', sans-serif; background:#0a0a0a; color:#e0e0e0; }
a { color:#aaa; text-decoration:none; }
a:hover { color:#fff; }
code { background:#333; padding:2px 6px; border-radius:4px; }

/* Admin layout */
.admin-layout { display:flex; min-height:100vh; }
.sidebar { width:250px; background:#1a1a1a; border-right:1px solid #333; padding:20px; }
.sidebar h3 { color:#fff; margin-bottom:20px; }
.sidebar ul { list-style:none; }
.sidebar li { margin-bottom:12px; }
.sidebar a { color:#aaa; text-decoration:none; display:flex; align-items:center; gap:8px; }
.sidebar a:hover { color:#fff; }
.main-content { flex:1; padding:40px; display:flex; justify-content:center; }
.main-content .content-wrapper { width:100%; max-width:800px; }

/* Cards for admin & user */
.card { background:#1a1a1a; border:1px solid #333; border-radius:12px; padding:25px; margin-bottom:25px; }
.card h2, .card h3 { margin-bottom:20px; font-weight:400; }
input, select, button { background:#222; color:#fff; border:1px solid #444; padding:10px 14px; margin:6px 0; border-radius:6px; font-family:inherit; font-size:15px; width:100%; box-sizing:border-box; }
button { background:#fff; color:#000; font-weight:600; cursor:pointer; width:auto; padding:10px 20px; }
button:hover { background:#ddd; }
.flag-input { display:flex; gap:10px; }
.flag-input input { flex:1; }
.status-badge { display:inline-block; padding:2px 8px; border-radius:4px; font-size:12px; }
.status-ready { background:#2ecc71; color:#000; }
.status-failed { background:#e74c3c; color:#fff; }
.log-window { background:#000; color:#0f0; padding:10px; border-radius:6px; height:200px; overflow-y:auto; font-family:monospace; font-size:12px; margin:10px 0; text-align:left; }
.challenge-list { list-style:none; padding:0; }
.challenge-list li { margin:8px 0; }

/* Centered user pages */
.centered-page { display:flex; justify-content:center; align-items:center; min-height:100vh; padding:20px; }
.centered-container { width:100%; max-width:650px; }

.landing-title { font-size:3rem; font-weight:600; margin-bottom:20px; }
.landing-sub { font-size:1.2rem; opacity:0.7; margin-bottom:30px; }
</style>
"""

# ---------- AUTH ----------
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("sign_in"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_sign_in"))
        return f(*args, **kwargs)
    return decorated

# ---------- ROUTES ----------
@app.route("/")
def index():
    return render_template_string(STYLE + """
    <div class="centered-page">
        <div class="centered-container">
            <div class="card" style="text-align:center;">
                <h1 class="landing-title">Conos CTFploy</h1>
                <p class="landing-sub">Self‑hosted CTF platform. Deploy, manage, and solve challenges.</p>
                <a href="/sign-in"><button style="font-size:1.1rem;">Get Started</button></a>
            </div>
        </div>
    </div>
    """)

@app.route("/sign-in", methods=["GET", "POST"])
def sign_in():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        user = get_user(username)
        if user and user["password_hash"] == hash_password(password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        return render_template_string(STYLE + """
        <div class="centered-page">
            <div class="centered-container">
                <div class="card">
                    <h2>Sign In</h2>
                    <p style="color:red;">Invalid credentials</p>
                    <form method="post">
                        <input name="username" placeholder="Username" required><br>
                        <input type="password" name="password" placeholder="Password" required><br>
                        <button type="submit">Sign In</button>
                    </form>
                    <p style="margin-top:15px;">No account? <a href="/register">Register</a></p>
                </div>
            </div>
        </div>""")
    return render_template_string(STYLE + """
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>Sign In</h2>
                <form method="post">
                    <input name="username" placeholder="Username" required><br>
                    <input type="password" name="password" placeholder="Password" required><br>
                    <button type="submit">Sign In</button>
                </form>
                <p style="margin-top:15px;">No account? <a href="/register">Register</a></p>
            </div>
        </div>
    </div>""")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        if get_user(username):
            return render_template_string(STYLE + """
            <div class="centered-page">
                <div class="centered-container"><div class="card"><h2>Register</h2><p style="color:red">User already exists</p>
                <form method="post"><input name="username" placeholder="Username" required><br>
                <input type="password" name="password" placeholder="Password" required><br>
                <button type="submit">Register</button></form></div></div></div>""")
        data = load_data()
        new_user = {"id": str(uuid.uuid4())[:8], "username": username, "password_hash": hash_password(password), "used_codes": []}
        data["users"].append(new_user)
        save_data(data)
        session["user_id"] = new_user["id"]
        session["username"] = new_user["username"]
        return redirect(url_for("dashboard"))
    return render_template_string(STYLE + """
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>Register</h2>
                <form method="post">
                    <input name="username" placeholder="Username" required><br>
                    <input type="password" name="password" placeholder="Password" required><br>
                    <button type="submit">Register</button>
                </form>
            </div>
        </div>
    </div>""")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("sign_in"))

# ---------- USER DASHBOARD (code-based, with success/error messages) ----------
@app.route("/dashboard")
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
    return render_template_string(STYLE + """
    <div class="centered-page">
        <div class="centered-container">
            <div class="card" style="text-align:left;">
                <h2>Welcome, {{ user.username }}</h2>
                <a href="/logout"><button style="float:right;">Logout</button></a>
                {% with messages = get_flashed_messages(with_categories=true) %}
                  {% if messages %}
                    {% for category, message in messages %}
                      <p style="color:{{ 'lime' if category == 'success' else 'red' }};">{{ message }}</p>
                    {% endfor %}
                  {% endif %}
                {% endwith %}
                <div style="margin-top:20px;">
                    <h3>Enter Access Code</h3>
                    <form method="post" action="/user/redeem-code">
                        <input name="code" placeholder="Access Code" required>
                        <button type="submit">Unlock Challenges</button>
                    </form>
                </div>
                {% if user_challenges %}
                <div style="margin-top:30px;">
                    <h3>Your Challenges</h3>
                    <ul class="challenge-list">
                    {% for ch in user_challenges %}
                        <li>
                            <strong>{{ ch.display_name }}</strong>
                            <span class="status-badge status-ready">Ready</span>
                            {% set inst = get_instance(user.id, ch.id) %}
                            {% if inst %}
                                (port {{ inst.host_port }} – <a href="/instance/{{ inst.id }}">View</a>)
                            {% else %}
                                <a href="/start/{{ ch.id }}"><button>Start</button></a>
                            {% endif %}
                        </li>
                    {% endfor %}
                    </ul>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    """, user=user, user_challenges=user_challenges,
       get_instance=lambda uid, cid: next((i for i in instances if i["user_id"] == uid and i["challenge_id"] == cid), None))

@app.route("/user/redeem-code", methods=["POST"])
@login_required
def redeem_code():
    code = request.form["code"].strip()
    data = load_data()
    code_entry = next((c for c in data["access_codes"] if c["code"] == code), None)
    if not code_entry:
        flash("Invalid code", "error")
        return redirect(url_for("dashboard"))
    user = get_user_by_id(session["user_id"])
    if code in user.get("used_codes", []):
        flash("You have already used this code.", "error")
        return redirect(url_for("dashboard"))
    user.setdefault("used_codes", []).append(code)
    username = user["username"]
    if username not in code_entry.get("used_by", []):
        code_entry.setdefault("used_by", []).append(username)
    save_data(data)
    flash("Code unlocked successfully!", "success")
    return redirect(url_for("dashboard"))

@app.route("/start/<challenge_id>")
@login_required
def start_challenge(challenge_id):
    data = load_data()
    user = get_user_by_id(session["user_id"])
    challenge = next((c for c in data["challenges"] if c["id"] == challenge_id and c["build_status"] == "success"), None)
    if not challenge:
        return redirect(url_for("dashboard", error="Challenge not found or not ready"))
    # Verify user has unlocked this challenge via a code
    allowed = False
    for code in data["access_codes"]:
        if code["code"] in user.get("used_codes", []) and challenge_id in code["challenges"]:
            allowed = True
            break
    if not allowed:
        return redirect(url_for("dashboard", error="Access denied"))
    instance, err = create_container(challenge, user["id"])
    if err:
        return redirect(url_for("dashboard", error=err))
    return redirect(url_for("view_instance", instance_id=instance["id"]))

@app.route("/instance/<instance_id>")
@login_required
def view_instance(instance_id):
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if not instance:
        return redirect(url_for("dashboard", error="Instance not found"))
    challenge = next((c for c in data["challenges"] if c["id"] == instance["challenge_id"]), None)
    host = request.host.split(":")[0]
    msg = request.args.get("msg")
    hints = challenge.get("hints", [])
    return render_template_string(STYLE + """
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>{{ ch.display_name }}</h2>
                <p>Status: {{ inst.status }}</p>
                {% if inst.connection_type == 'ssh' %}
                    <p>SSH: <code>ssh ctfuser@{{ host }} -p {{ inst.host_port }}</code></p>
                    <p>Password: <code>ctfpassword</code></p>
                {% elif inst.connection_type == 'web' %}
                    <p>URL: <a href="http://{{ host }}:{{ inst.host_port }}">http://{{ host }}:{{ inst.host_port }}</a></p>
                {% elif inst.connection_type == 'nc' %}
                    <p>Netcat: <code>nc {{ host }} {{ inst.host_port }}</code></p>
                {% endif %}
                {% if hints %}
                <div style="margin-top:10px;">
                    <strong>Hints:</strong>
                    <ul>
                    {% for hint in hints %}
                        <li>{{ hint }}</li>
                    {% endfor %}
                    </ul>
                </div>
                {% endif %}
                <p>Expires: <span id="countdown">{{ inst.expires_at }}</span></p>
                <a href="/terminate/{{ inst.id }}"><button>Terminate</button></a>
                <div style="margin-top:20px;">
                    <h3>Submit Flag</h3>
                    <form action="/submit_flag/{{ inst.id }}" method="post" class="flag-input">
                        <input name="flag" placeholder="flag{...}" required>
                        <button type="submit">Submit</button>
                    </form>
                    {% if msg %}<p>{{ msg }}</p>{% endif %}
                </div>
                <a href="/dashboard">Back</a>
            </div>
        </div>
    </div>
    <script>
        const expires = new Date("{{ inst.expires_at }}");
        setInterval(() => {
            const diff = expires - new Date();
            if (diff <= 0) document.getElementById('countdown').textContent = 'Expired';
            else {
                const m = Math.floor(diff/60000);
                const s = Math.floor((diff%60000)/1000);
                document.getElementById('countdown').textContent = m + ':' + (s<10?'0':'') + s;
            }
        }, 1000);
    </script>
    """, ch=challenge, inst=instance, host=host, msg=msg, hints=hints)

@app.route("/terminate/<instance_id>")
@login_required
def terminate(instance_id):
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if instance:
        terminate_instance(instance_id)
    return redirect(url_for("dashboard"))

@app.route("/submit_flag/<instance_id>", methods=["POST"])
@login_required
def submit_flag(instance_id):
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if not instance:
        return redirect(url_for("dashboard", error="Instance not found"))
    submitted = request.form["flag"].strip()
    challenge = next((c for c in data["challenges"] if c["id"] == instance["challenge_id"]), None)
    correct = instance.get("dynamic_flag") if challenge.get("flag_type") == "dynamic" else challenge.get("flag")
    msg = "✅ Correct!" if correct and submitted == correct else "❌ Incorrect"
    return redirect(url_for("view_instance", instance_id=instance_id, msg=msg))

# ---------- ADMIN (with used_by display) ----------
@app.route("/admin/sign-in", methods=["GET", "POST"])
def admin_sign_in():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        return render_template_string(STYLE + """
        <div class="centered-page"><div class="centered-container"><div class="card">
        <h2>Admin Sign In</h2><p style="color:red">Wrong password</p>
        <form method="post"><input type="password" name="password" placeholder="Password"><button type="submit">Sign In</button></form>
        </div></div></div>""")
    return render_template_string(STYLE + """
    <div class="centered-page"><div class="centered-container"><div class="card">
    <h2>Admin Sign In</h2>
    <form method="post"><input type="password" name="password" placeholder="Password"><button type="submit">Sign In</button></form>
    </div></div></div>""")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_sign_in"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    data = load_data()
    return render_template_string(STYLE + """
    <div class="admin-layout">
        <div class="sidebar">
            <h3>CTFploy Admin</h3>
            <ul>
                <li><a href="/admin"><span class="devicons devicons-dashboard"></span> Dashboard</a></li>
                <li><a href="/admin/challenges"><span class="devicons devicons-terminal"></span> Challenges</a></li>
                <li><a href="/admin/codes"><span class="devicons devicons-code_badge"></span> Access Codes</a></li>
                <li><a href="/admin/update"><span class="devicons devicons-upload"></span> Update</a></li>
                <li><a href="/admin/logout">Logout</a></li>
            </ul>
        </div>
        <div class="main-content">
            <div class="content-wrapper">
                <h2>Dashboard</h2>
                <div class="card">
                    <p>Total challenges: {{ challenges|length }}</p>
                    <p>Active instances: {{ instances|selectattr('status','equalto','running')|list|length }}</p>
                </div>
            </div>
        </div>
    </div>
    """, challenges=data["challenges"], instances=data["instances"])

@app.route("/admin/challenges", methods=["GET"])
@admin_required
def admin_challenges():
    data = load_data()
    store_files = []
    if os.path.isdir(CHALLENGES_STORE):
        store_files = [f for f in os.listdir(CHALLENGES_STORE) if f.endswith(".tar.gz")]
    return render_template_string(STYLE + """
    <div class="admin-layout">
        <div class="sidebar">
            <h3>CTFploy Admin</h3>
            <ul>
                <li><a href="/admin"><span class="devicons devicons-dashboard"></span> Dashboard</a></li>
                <li><a href="/admin/challenges"><span class="devicons devicons-terminal"></span> Challenges</a></li>
                <li><a href="/admin/codes"><span class="devicons devicons-code_badge"></span> Access Codes</a></li>
                <li><a href="/admin/update"><span class="devicons devicons-upload"></span> Update</a></li>
                <li><a href="/admin/logout">Logout</a></li>
            </ul>
        </div>
        <div class="main-content">
            <div class="content-wrapper">
                <h2>Challenges</h2>

                <!-- Import from URL -->
                <div class="card">
                    <h3>Import from URL</h3>
                    <form action="/admin/import-url" method="post">
                        <input name="url" placeholder="https://example.com/challenge.tar.gz" required>
                        <button type="submit">Fetch & Build</button>
                    </form>
                    <p style="font-size:0.9rem; color:#aaa;">Archive must contain a Dockerfile (and optionally <code>ctfploy.json</code>).</p>
                </div>

                <!-- Pre‑built gallery -->
                {% if store_files %}
                <div class="card">
                    <h3>Pre‑built Challenges</h3>
                    <ul class="challenge-list">
                    {% for f in store_files %}
                        <li>
                            <form method="post" action="/admin/build-from-store" style="display:inline;">
                                <input type="hidden" name="filename" value="{{ f }}">
                                <span>{{ f }}</span>
                                <button type="submit" style="margin-left:10px;">Build</button>
                            </form>
                        </li>
                    {% endfor %}
                    </ul>
                </div>
                {% endif %}

                <!-- Manual upload -->
                <div class="card">
                    <h3>Manual Upload (server path)</h3>
                    <form action="/admin/upload" method="post">
                        <input name="name" placeholder="Image name" required><br>
                        <input name="display_name" placeholder="Display name" required><br>
                        <input name="internal_port" value="22"><br>
                        <select name="connection_type">
                            <option value="ssh">SSH</option>
                            <option value="web">Web (HTTP)</option>
                            <option value="nc">Netcat</option>
                        </select><br>
                        <select name="flag_type">
                            <option value="static">Static</option>
                            <option value="dynamic">Dynamic</option>
                        </select><br>
                        <input name="flag" placeholder="Flag (if static)"><br>
                        <input name="filepath" placeholder="Server path to .tar.gz" required><br>
                        <button type="submit">Build</button>
                    </form>
                </div>

                <!-- Existing challenges -->
                <div class="card">
                    <h3>All Challenges</h3>
                    <ul class="challenge-list">
                    {% for ch in challenges %}
                        <li>
                            <strong>{{ ch.display_name }}</strong> ({{ ch.image_tag }})
                            {% if ch.build_status == "success" %}
                                <span class="status-badge status-ready">Ready</span>
                            {% elif ch.build_status == "building" %}
                                <span class="status-badge" style="background:#f1c40f;color:#000">Building</span>
                            {% else %}
                                <span class="status-badge status-failed">Failed</span>
                            {% endif %}
                            [<a href="/admin/build_log/{{ ch.id }}">Logs</a>]
                            [<a href="/admin/delete_challenge/{{ ch.id }}">Delete</a>]
                        </li>
                    {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
    </div>
    """, challenges=data["challenges"], store_files=store_files)

# URL import with metadata detection
@app.route("/admin/import-url", methods=["POST"])
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
            "build_log": ""
        }
        data = load_data()
        data["challenges"].append(challenge)
        save_data(data)
        threading.Thread(target=build_image_thread, args=(name, build_dir, image_tag, challenge_id), daemon=True).start()
        return redirect(url_for("build_log_view", challenge_id=challenge_id))
    except Exception as e:
        return f"Error: {str(e)}", 500

# Manual upload (also supports metadata)
@app.route("/admin/upload", methods=["POST"])
@admin_required
def admin_upload():
    data = load_data()
    name = request.form["name"].strip().lower().replace(" ", "-")
    display_name = request.form["display_name"]
    internal_port = int(request.form.get("internal_port", 22))
    connection_type = request.form.get("connection_type", "ssh")
    flag_type = request.form.get("flag_type", "static")
    flag = request.form.get("flag", "")
    filepath = request.form["filepath"].strip()
    if not filepath or not os.path.exists(filepath):
        return "File not found", 400

    build_dir = f"/tmp/ctf_build_{name}_{int(time.time())}"
    os.makedirs(build_dir, exist_ok=True)
    with tarfile.open(filepath, "r:gz") as tar:
        tar.extractall(build_dir)

    metadata_path = os.path.join(build_dir, "ctfploy.json")
    if os.path.exists(metadata_path):
        with open(metadata_path) as f:
            meta = json.load(f)
        name = meta.get("name", name)
        display_name = meta.get("display_name", display_name)
        internal_port = meta.get("internal_port", internal_port)
        connection_type = meta.get("connection_type", connection_type)
        flag_type = meta.get("flag_type", flag_type)
        flag = meta.get("flag", flag)

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
        "build_log": ""
    }
    data["challenges"].append(challenge)
    save_data(data)
    threading.Thread(target=build_image_thread, args=(name, build_dir, image_tag, challenge_id), daemon=True).start()
    return redirect(url_for("build_log_view", challenge_id=challenge_id))

@app.route("/admin/build-from-store", methods=["POST"])
@admin_required
def build_from_store():
    filename = request.form["filename"].strip()
    filepath = os.path.join(CHALLENGES_STORE, filename)
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
        "build_log": ""
    }
    data = load_data()
    data["challenges"].append(challenge)
    save_data(data)
    threading.Thread(target=build_image_thread, args=(name, build_dir, image_tag, challenge_id), daemon=True).start()
    return redirect(url_for("build_log_view", challenge_id=challenge_id))

@app.route("/admin/build_log/<challenge_id>")
@admin_required
def build_log_view(challenge_id):
    return render_template_string(STYLE + """
    <div class="centered-page"><div class="centered-container"><div class="card">
    <h2>Build Log</h2><div id="log" class="log-window"></div></div></div></div>
    <script>
        const evtSource = new EventSource("/admin/build_log_stream/{{ challenge_id }}");
        const logDiv = document.getElementById("log");
        evtSource.onmessage = function(event) {
            if (event.data === "END") { evtSource.close(); return; }
            logDiv.innerHTML += event.data;
            logDiv.scrollTop = logDiv.scrollHeight;
        };
        evtSource.onerror = function() { evtSource.close(); };
    </script>
    """, challenge_id=challenge_id)

@app.route("/admin/build_log_stream/<challenge_id>")
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

@app.route("/admin/delete_challenge/<challenge_id>")
@admin_required
def delete_challenge(challenge_id):
    data = load_data()
    data["challenges"] = [c for c in data["challenges"] if c["id"] != challenge_id]
    for inst in data["instances"]:
        if inst["challenge_id"] == challenge_id and inst["status"] == "running":
            terminate_instance(inst["id"])
    save_data(data)
    return redirect(url_for("admin_challenges"))

# ---------- ACCESS CODES (show used_by) ----------
@app.route("/admin/codes", methods=["GET"])
@admin_required
def admin_codes():
    data = load_data()
    return render_template_string(STYLE + """
    <div class="admin-layout">
        <div class="sidebar">
            <h3>CTFploy Admin</h3>
            <ul>
                <li><a href="/admin"><span class="devicons devicons-dashboard"></span> Dashboard</a></li>
                <li><a href="/admin/challenges"><span class="devicons devicons-terminal"></span> Challenges</a></li>
                <li><a href="/admin/codes"><span class="devicons devicons-code_badge"></span> Access Codes</a></li>
                <li><a href="/admin/update"><span class="devicons devicons-upload"></span> Update</a></li>
                <li><a href="/admin/logout">Logout</a></li>
            </ul>
        </div>
        <div class="main-content">
            <div class="content-wrapper">
                <h2>Access Codes</h2>
                <div class="card">
                    <form action="/admin/gencode" method="post">
                        <button type="submit">Generate New Code</button>
                    </form>
                </div>
                <div class="card">
                    <ul class="challenge-list">
                    {% for code in access_codes %}
                        <li>
                            <strong>{{ code.code }}</strong>
                            {% if code.used_by %}
                            <span style="color:#aaa;">(used by: {{ ', '.join(code.used_by) }})</span>
                            {% else %}
                            <span style="color:#aaa;">(unused)</span>
                            {% endif %}
                            <ul>
                            {% for cid in code.challenges %}
                                {% set ch = get_challenge(cid) %}
                                <li>{{ ch.display_name }} ({{ ch.build_status }})</li>
                            {% endfor %}
                            </ul>
                            <form action="/admin/add_challenge_to_code" method="post" style="margin-top:5px;">
                                <input type="hidden" name="code" value="{{ code.code }}">
                                <select name="challenge_id">
                                {% for ch in challenges if ch.build_status == "success" %}
                                    <option value="{{ ch.id }}">{{ ch.display_name }}</option>
                                {% endfor %}
                                </select>
                                <button type="submit">Add Challenge</button>
                            </form>
                            [<a href="/admin/delete_code/{{ code.code }}">Delete Code</a>]
                        </li>
                    {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
    </div>
    """, access_codes=data["access_codes"], challenges=data["challenges"],
       get_challenge=lambda cid: next((c for c in data["challenges"] if c["id"] == cid), None))

@app.route("/admin/gencode", methods=["POST"])
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
    return redirect(url_for("admin_codes"))

@app.route("/admin/add_challenge_to_code", methods=["POST"])
@admin_required
def add_challenge_to_code():
    data = load_data()
    code = request.form["code"]
    challenge_id = request.form["challenge_id"]
    for c in data["access_codes"]:
        if c["code"] == code and challenge_id not in c["challenges"]:
            c["challenges"].append(challenge_id)
    save_data(data)
    return redirect(url_for("admin_codes"))

@app.route("/admin/delete_code/<code>")
@admin_required
def delete_code(code):
    data = load_data()
    data["access_codes"] = [c for c in data["access_codes"] if c["code"] != code]
    save_data(data)
    return redirect(url_for("admin_codes"))

# Update platform
@app.route("/admin/update", methods=["GET", "POST"])
@admin_required
def admin_update():
    if request.method == "POST":
        try:
            subprocess.run(["docker", "pull", "zohidjonmarufov/ctfploy-platform:main"], check=True)
            subprocess.run(["docker", "compose", "-f", "/etc/ctfploy/docker-compose.yml", "up", "-d", "platform"], check=True)
            flash("Platform updated successfully!", "success")
        except Exception as e:
            flash(f"Update failed: {str(e)}", "error")
        return redirect(url_for("admin_update"))
    return render_template_string(STYLE + """
    <div class="admin-layout">
        <div class="sidebar">
            <h3>CTFploy Admin</h3>
            <ul>
                <li><a href="/admin"><span class="devicons devicons-dashboard"></span> Dashboard</a></li>
                <li><a href="/admin/challenges"><span class="devicons devicons-terminal"></span> Challenges</a></li>
                <li><a href="/admin/codes"><span class="devicons devicons-code_badge"></span> Access Codes</a></li>
                <li><a href="/admin/update"><span class="devicons devicons-upload"></span> Update</a></li>
                <li><a href="/admin/logout">Logout</a></li>
            </ul>
        </div>
        <div class="main-content">
            <div class="content-wrapper">
                <h2>Update Platform</h2>
                <div class="card">
                    <p>Pull the latest image from Docker Hub and restart the platform container.</p>
                    <form method="post">
                        <button type="submit">Update Now</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    """)

# ---------- STARTUP ----------
with app.app_context():
    ensure_network()
    os.makedirs(CHALLENGES_STORE, exist_ok=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)