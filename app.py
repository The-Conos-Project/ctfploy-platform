#!/usr/bin/env python3
"""
Conos CTFploy Platform – Flask Application
"""
import os, json, time, random, uuid, threading, queue, tarfile, hashlib
from datetime import datetime, timedelta
from flask import Flask, request, redirect, render_template_string, session, url_for, Response
import docker

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24).hex())
INSTANCE_TIMEOUT = int(os.environ.get("INSTANCE_TIMEOUT", 30 * 60))
MAX_CONCURRENT_PER_USER = int(os.environ.get("MAX_CONCURRENT_PER_USER", 3))
DATA_FILE = "/data/data.json"
DOCKER_NETWORK = "ctf_net"

app = Flask(__name__)
app.secret_key = SECRET_KEY

docker_client = docker.from_env()
build_logs = {}

# ---------- DATA STORAGE ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"challenges": [], "codes": [], "instances": [], "users": [], "groups": []}
    with open(DATA_FILE) as f:
        return json.load(f)

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

# ---------- STYLES ----------
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600&display=swap');
@import url('https://cdn.jsdelivr.net/npm/devicons@1.8.0/css/devicons.min.css');
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: 'Space Grotesk', sans-serif; background:#0a0a0a; color:#e0e0e0; padding:20px; }
.container { max-width:900px; margin:0 auto; }
.card { background:#1a1a1a; border:1px solid #333; border-radius:12px; padding:20px; margin:20px 0; }
input, select, button { background:#222; color:#fff; border:1px solid #444; padding:10px; margin:5px 0; border-radius:6px; font-family:inherit; }
button { background:#fff; color:#000; font-weight:600; cursor:pointer; }
button:hover { background:#ddd; }
a { color:#aaa; text-decoration:none; }
a:hover { color:#fff; }
h2, h3 { font-weight:400; margin-bottom:15px; }
code { background:#333; padding:2px 6px; border-radius:4px; }
.log-window { background:#000; color:#0f0; padding:10px; border-radius:6px; height:200px; overflow-y:auto; font-family:monospace; font-size:12px; margin:10px 0; }
.flag-input { display:flex; gap:10px; }
.flag-input input { flex:1; }
nav { display:flex; gap:20px; margin-bottom:20px; }
.status-badge { display:inline-block; padding:2px 8px; border-radius:4px; font-size:12px; }
.status-ready { background:#2ecc71; color:#000; }
.status-failed { background:#e74c3c; color:#fff; }
.devicons { font-size:20px; margin-right:8px; }
</style>
"""

# ---------- AUTH ROUTES ----------
@app.route("/")
def index():
    if session.get("admin"):
        return redirect(url_for("admin_panel"))
    if session.get("user_id"):
        return redirect(url_for("user_dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        user = get_user(username)
        if user and user["password_hash"] == hash_password(password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("user_dashboard"))
        return render_template_string(STYLE + """<div class="container"><h2>Login</h2><p style="color:red">Invalid credentials</p><form method="post"><input name="username" placeholder="Username" required><br><input type="password" name="password" placeholder="Password" required><br><button type="submit">Login</button></form><p>No account? <a href="/register">Register</a></p></div>""")
    return render_template_string(STYLE + """<div class="container"><h2>Login</h2><form method="post"><input name="username" placeholder="Username" required><br><input type="password" name="password" placeholder="Password" required><br><button type="submit">Login</button></form><p>No account? <a href="/register">Register</a></p></div>""")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        if get_user(username):
            return render_template_string(STYLE + """<div class="container"><h2>Register</h2><p style="color:red">User already exists</p><form method="post"><input name="username" placeholder="Username" required><br><input type="password" name="password" placeholder="Password" required><br><button type="submit">Register</button></form></div>""")
        data = load_data()
        new_user = {"id": str(uuid.uuid4())[:8], "username": username, "password_hash": hash_password(password), "joined_groups": []}
        data["users"].append(new_user)
        save_data(data)
        session["user_id"] = new_user["id"]
        session["username"] = new_user["username"]
        return redirect(url_for("user_dashboard"))
    return render_template_string(STYLE + """<div class="container"><h2>Register</h2><form method="post"><input name="username" placeholder="Username" required><br><input type="password" name="password" placeholder="Password" required><br><button type="submit">Register</button></form></div>""")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- USER DASHBOARD ----------
@app.route("/user")
def user_dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    data = load_data()
    user = get_user_by_id(session["user_id"])
    groups = [g for g in data["groups"] if g["id"] in user["joined_groups"]]
    instances = [i for i in data["instances"] if i["user_id"] == user["id"] and i["status"] == "running"]
    return render_template_string(STYLE + """
        <div class="container">
            <nav><a href="/user">Dashboard</a> <a href="/logout">Logout</a></nav>
            <h2>Welcome, {{ user.username }}</h2>
            <div class="card">
                <h3>Join Challenge Group</h3>
                <form method="post" action="/user/join">
                    <input name="code" placeholder="Group Code" required>
                    <button type="submit">Join</button>
                </form>
                {% if error %}<p style="color:red">{{ error }}</p>{% endif %}
            </div>
            {% for group in groups %}
            <div class="card">
                <h3>{{ group.name }}</h3>
                <ul>
                {% for cid in group.challenges %}
                    {% set ch = get_challenge(cid) %}
                    <li>
                        <strong>{{ ch.display_name }}</strong>
                        {% if ch.build_status == "success" %}
                            <span class="status-badge status-ready">Ready</span>
                        {% else %}
                            <span class="status-badge status-failed">Unavailable</span>
                        {% endif %}
                        {% set inst = get_instance(user.id, cid) %}
                        {% if inst %}
                            (port {{ inst.host_port }} – <a href="/user/instance/{{ inst.id }}">View</a>)
                        {% else %}
                            <a href="/user/start/{{ cid }}">Start</a>
                        {% endif %}
                    </li>
                {% endfor %}
                </ul>
            </div>
            {% endfor %}
        </div>
    """, user=user, groups=groups, error=request.args.get("error"),
       get_challenge=lambda cid: next((c for c in data["challenges"] if c["id"] == cid), None),
       get_instance=lambda uid, cid: next((i for i in instances if i["user_id"] == uid and i["challenge_id"] == cid), None))

@app.route("/user/join", methods=["POST"])
def join_group():
    if not session.get("user_id"): return redirect(url_for("login"))
    code = request.form["code"].strip()
    data = load_data()
    group = next((g for g in data["groups"] if g["join_code"] == code), None)
    if not group:
        return redirect(url_for("user_dashboard", error="Invalid group code"))
    user = get_user_by_id(session["user_id"])
    if group["id"] not in user["joined_groups"]:
        user["joined_groups"].append(group["id"])
        save_data(data)
    return redirect(url_for("user_dashboard"))

@app.route("/user/start/<challenge_id>")
def start_challenge_for_user(challenge_id):
    if not session.get("user_id"): return redirect(url_for("login"))
    data = load_data()
    user = get_user_by_id(session["user_id"])
    challenge = next((c for c in data["challenges"] if c["id"] == challenge_id), None)
    if not challenge: return redirect(url_for("user_dashboard", error="Challenge not found"))
    access = any(challenge_id in g["challenges"] for g in data["groups"] if g["id"] in user["joined_groups"])
    if not access: return redirect(url_for("user_dashboard", error="Access denied"))
    instance, err = create_container(challenge, user["id"])
    if err: return redirect(url_for("user_dashboard", error=err))
    return redirect(url_for("view_instance", instance_id=instance["id"]))

@app.route("/user/instance/<instance_id>")
def view_instance(instance_id):
    if not session.get("user_id"): return redirect(url_for("login"))
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if not instance: return redirect(url_for("user_dashboard", error="Instance not found"))
    challenge = next((c for c in data["challenges"] if c["id"] == instance["challenge_id"]), None)
    host = request.host.split(":")[0]
    msg = request.args.get("msg")
    return render_template_string(STYLE + """
        <div class="container">
            <h3>{{ ch.display_name }}</h3>
            <p>Status: {{ inst.status }}</p>
            {% if inst.connection_type == 'ssh' %}
                <p>SSH: <code>ssh ctfuser@{{ host }} -p {{ inst.host_port }}</code></p>
                <p>Password: <code>ctfpassword</code></p>
            {% elif inst.connection_type == 'web' %}
                <p>URL: <a href="http://{{ host }}:{{ inst.host_port }}">http://{{ host }}:{{ inst.host_port }}</a></p>
            {% elif inst.connection_type == 'nc' %}
                <p>Netcat: <code>nc {{ host }} {{ inst.host_port }}</code></p>
            {% endif %}
            <p>Expires: <span id="countdown">{{ inst.expires_at }}</span></p>
            <a href="/user/terminate/{{ inst.id }}"><button>Terminate</button></a>
            <div class="card">
                <h4>Submit Flag</h4>
                <form action="/user/submit_flag/{{ inst.id }}" method="post" class="flag-input">
                    <input name="flag" placeholder="flag{...}" required>
                    <button type="submit">Submit</button>
                </form>
                {% if msg %}<p>{{ msg }}</p>{% endif %}
            </div>
            <a href="/user">Back</a>
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
    """, ch=challenge, inst=instance, host=host, msg=msg)

@app.route("/user/terminate/<instance_id>")
def user_terminate(instance_id):
    if not session.get("user_id"): return redirect(url_for("login"))
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if instance:
        terminate_instance(instance_id)
    return redirect(url_for("user_dashboard"))

@app.route("/user/submit_flag/<instance_id>", methods=["POST"])
def submit_flag(instance_id):
    if not session.get("user_id"): return redirect(url_for("login"))
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if not instance: return redirect(url_for("user_dashboard", error="Instance not found"))
    submitted = request.form["flag"].strip()
    challenge = next((c for c in data["challenges"] if c["id"] == instance["challenge_id"]), None)
    correct = instance.get("dynamic_flag") if challenge.get("flag_type") == "dynamic" else challenge.get("flag")
    msg = "✅ Correct!" if correct and submitted == correct else "❌ Incorrect"
    return redirect(url_for("view_instance", instance_id=instance_id, msg=msg))

# ---------- ADMIN ----------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_panel"))
        return render_template_string(STYLE + """<div class="container"><h2>Admin Login</h2><p style="color:red">Wrong password</p><form method="post"><input type="password" name="password" placeholder="Password"><button type="submit">Login</button></form></div>""")
    return render_template_string(STYLE + """<div class="container"><h2>Admin Login</h2><form method="post"><input type="password" name="password" placeholder="Password"><button type="submit">Login</button></form></div>""")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

@app.route("/admin")
def admin_panel():
    if not session.get("admin"): return redirect(url_for("admin_login"))
    data = load_data()
    return render_template_string(STYLE + """
        <div class="container">
            <nav><a href="/admin">Dashboard</a> <a href="/">User View</a> <a href="/admin/logout">Logout</a></nav>
            <h2>Admin Panel</h2>

            <div class="card">
                <h3><span class="devicons devicons-docker"></span> Upload Docker Image</h3>
                <form action="/admin/upload" method="post">
                    <input name="name" placeholder="Image name (no spaces)" required><br>
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
                    <button type="submit">Build Image</button>
                </form>
            </div>

            <div class="card">
                <h3>Challenges</h3>
                <ul>
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

            <div class="card">
                <h3>Access Codes</h3>
                <form action="/admin/gencode" method="post" style="display:inline;"><button type="submit">Generate Code</button></form>
                <ul>
                {% for code in codes %}
                    <li>{{ code.code }} ({{ code.used_count }}/{{ code.max_uses }}) [<a href="/admin/delete_code/{{ code.code }}">Delete</a>]</li>
                {% endfor %}
                </ul>
            </div>

            <div class="card">
                <h3>Challenge Groups</h3>
                <form action="/admin/create_group" method="post">
                    <input name="group_name" placeholder="Group name" required>
                    <button type="submit">Create Group</button>
                </form>
                <ul>
                {% for g in groups %}
                    <li><strong>{{ g.name }}</strong> – Join Code: <code>{{ g.join_code }}</code>
                        [<a href="/admin/delete_group/{{ g.id }}">Delete</a>]
                        <ul>
                        {% for cid in g.challenges %}
                            {% set ch = get_challenge(cid) %}
                            <li>{{ ch.display_name }} ({{ ch.build_status }})</li>
                        {% endfor %}
                        </ul>
                        <form action="/admin/add_challenge_to_group" method="post" style="display:inline">
                            <input type="hidden" name="group_id" value="{{ g.id }}">
                            <select name="challenge_id">
                            {% for ch in challenges %}
                                {% if ch.build_status == "success" %}
                                    <option value="{{ ch.id }}">{{ ch.display_name }}</option>
                                {% endif %}
                            {% endfor %}
                            </select>
                            <button type="submit">Add to Group</button>
                        </form>
                    </li>
                {% endfor %}
                </ul>
            </div>

            <div class="card">
                <h3>Running Instances</h3>
                <ul>
                {% for inst in instances if inst.status == "running" %}
                    <li>{{ inst.container_name }} :{{ inst.host_port }} (user: {{ inst.user_id }}) – Expires {{ inst.expires_at }}</li>
                {% endfor %}
                </ul>
            </div>
        </div>
    """, challenges=data["challenges"], codes=data.get("codes",[]), groups=data.get("groups",[]), instances=data.get("instances",[]),
       get_challenge=lambda cid: next((c for c in data["challenges"] if c["id"] == cid), None))

# Admin actions (upload, logs, codes, groups)
@app.route("/admin/upload", methods=["POST"])
def admin_upload():
    if not session.get("admin"): return redirect(url_for("admin_login"))
    data = load_data()
    name = request.form["name"].strip().lower().replace(" ", "-")
    display_name = request.form["display_name"]
    internal_port = int(request.form.get("internal_port", 22))
    connection_type = request.form.get("connection_type", "ssh")
    flag_type = request.form.get("flag_type", "static")
    static_flag = request.form.get("flag", "")
    filepath = request.form["filepath"].strip()
    if not filepath or not os.path.exists(filepath): return "File not found", 400
    build_dir = f"/tmp/ctf_build_{name}_{int(time.time())}"
    os.makedirs(build_dir, exist_ok=True)
    with tarfile.open(filepath, "r:gz") as tar: tar.extractall(build_dir)
    image_tag = f"ctf-{name}"
    challenge_id = str(uuid.uuid4())[:8]
    challenge = {"id": challenge_id, "name": name, "display_name": display_name, "image_tag": image_tag,
                 "internal_port": internal_port, "connection_type": connection_type, "flag_type": flag_type,
                 "flag": static_flag, "build_status": "building", "build_log": ""}
    data["challenges"].append(challenge)
    save_data(data)
    threading.Thread(target=build_image_thread, args=(name, build_dir, image_tag, challenge_id), daemon=True).start()
    return redirect(url_for("build_log_view", challenge_id=challenge_id))

@app.route("/admin/build_log/<challenge_id>")
def build_log_view(challenge_id):
    if not session.get("admin"): return redirect(url_for("admin_login"))
    return render_template_string(STYLE + """
        <div class="container"><h2>Build Log</h2><div id="log" class="log-window"></div></div>
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
def build_log_stream(challenge_id):
    q = build_logs.get(challenge_id)
    if not q:
        q = queue.Queue()
        build_logs[challenge_id] = q
    def generate():
        while True:
            line = q.get()
            if line is None: yield "data: END\n\n"; break
            yield f"data: {line}\n\n"
            time.sleep(0.05)
    return Response(generate(), mimetype="text/event-stream")

@app.route("/admin/delete_challenge/<challenge_id>")
def delete_challenge(challenge_id):
    if not session.get("admin"): return redirect(url_for("admin_login"))
    data = load_data()
    data["challenges"] = [c for c in data["challenges"] if c["id"] != challenge_id]
    for inst in data["instances"]:
        if inst["challenge_id"] == challenge_id and inst["status"] == "running":
            terminate_instance(inst["id"])
    save_data(data)
    return redirect(url_for("admin_panel"))

@app.route("/admin/gencode", methods=["POST"])
def generate_code():
    if not session.get("admin"): return redirect(url_for("admin_login"))
    data = load_data()
    code_str = f"CTF-{uuid.uuid4().hex[:6].upper()}"
    data.setdefault("codes", []).append({"code": code_str, "max_uses": 1, "used_count": 0, "created_at": datetime.now().isoformat()})
    save_data(data)
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete_code/<code>")
def delete_code(code):
    if not session.get("admin"): return redirect(url_for("admin_login"))
    data = load_data()
    data["codes"] = [c for c in data["codes"] if c["code"] != code]
    save_data(data)
    return redirect(url_for("admin_panel"))

@app.route("/admin/create_group", methods=["POST"])
def create_group():
    if not session.get("admin"): return redirect(url_for("admin_login"))
    data = load_data()
    name = request.form["group_name"].strip()
    join_code = f"CLASS-{uuid.uuid4().hex[:6].upper()}"
    group = {"id": str(uuid.uuid4())[:8], "name": name, "join_code": join_code, "challenges": []}
    data.setdefault("groups", []).append(group)
    save_data(data)
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete_group/<group_id>")
def delete_group(group_id):
    if not session.get("admin"): return redirect(url_for("admin_login"))
    data = load_data()
    data["groups"] = [g for g in data["groups"] if g["id"] != group_id]
    save_data(data)
    return redirect(url_for("admin_panel"))

@app.route("/admin/add_challenge_to_group", methods=["POST"])
def add_challenge_to_group():
    if not session.get("admin"): return redirect(url_for("admin_login"))
    data = load_data()
    group_id = request.form["group_id"]
    challenge_id = request.form["challenge_id"]
    for g in data["groups"]:
        if g["id"] == group_id and challenge_id not in g["challenges"]:
            g["challenges"].append(challenge_id)
    save_data(data)
    return redirect(url_for("admin_panel"))

# ---------- STARTUP ----------
with app.app_context():
    ensure_network()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)