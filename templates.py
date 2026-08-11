import json
from typing import Optional


def _get_icon(name: str) -> str:
    icons = {
        "dashboard": "dashboard",
        "terminal": "terminal",
        "code_badge": "code-badge",
        "upload": "upload",
        "logout": "log-out",
    }
    return f'<span class="devicons devicons-{icons.get(name, name)}"></span>'


def sidebar_html(active: str) -> str:
    links = [
        ("dashboard", "/admin", "Dashboard"),
        ("terminal", "/admin/challenges", "Challenges"),
        ("code_badge", "/admin/codes", "Access Codes"),
        ("upload", "/admin/update", "Update"),
    ]
    items = ""
    for key, href, label in links:
        cls = "active" if active == key else ""
        items += f'<li><a href="{href}" class="{cls}">{_get_icon(key)} {label}</a></li>'

    return f"""
<div class="sidebar" id="sidebar">
    <div class="sidebar-header">
        <h3>CTFploy Admin</h3>
        <button class="sidebar-toggle" id="sidebarToggle" aria-label="Toggle sidebar">
            <span class="sidebar-toggle-bar"></span>
            <span class="sidebar-toggle-bar"></span>
            <span class="sidebar-toggle-bar"></span>
        </button>
    </div>
    <ul>
        {items}
        <li class="sidebar-logout"><a href="/admin/logout">{_get_icon('logout')} Logout</a></li>
    </ul>
</div>
<script>
(function() {{
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');
    if (!sidebar || !toggle) return;
    const key = 'ctfploy-sidebar-collapsed';
    function update() {{
        if (sidebar.classList.contains('collapsed')) {{
            sidebar.setAttribute('data-collapsed', 'true');
        }} else {{
            sidebar.removeAttribute('data-collapsed');
        }}
    }}
    toggle.addEventListener('click', () => {{
        sidebar.classList.toggle('collapsed');
        localStorage.setItem(key, sidebar.classList.contains('collapsed') ? '1' : '0');
        update();
    }});
    if (localStorage.getItem(key) === '1') {{
        sidebar.classList.add('collapsed');
    }}
    update();
}})();
</script>
"""


def admin_layout(content: str, active: str = "dashboard") -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CTFploy Admin</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/devicons@1.8.0/css/devicons.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600&display=swap');
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family: 'Space Grotesk', sans-serif; background:#0a0a0a; color:#e0e0e0; }}
        a {{ color:#aaa; text-decoration:none; }}
        a:hover {{ color:#fff; }}
        code {{ background:#333; padding:2px 6px; border-radius:4px; }}

        .admin-layout {{ display:flex; min-height:100vh; }}
        .sidebar {{
            width: 250px;
            background: #111;
            border-right: 1px solid #333;
            padding: 20px;
            transition: width 0.3s ease, padding 0.3s ease;
            overflow: hidden;
            white-space: nowrap;
        }}
        .sidebar[data-collapsed="true"] {{
            width: 64px;
            padding: 16px 10px;
        }}
        .sidebar-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
        }}
        .sidebar h3 {{
            color: #fff;
            font-size: 1.1rem;
            transition: opacity 0.2s;
        }}
        .sidebar[data-collapsed="true"] h3 {{
            opacity: 0;
            width: 0;
            overflow: hidden;
        }}
        .sidebar-toggle {{
            display: flex;
            flex-direction: column;
            gap: 5px;
            background: none;
            border: none;
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
        }}
        .sidebar-toggle:hover {{ background: #222; }}
        .sidebar-toggle-bar {{
            width: 18px;
            height: 2px;
            background: #888;
            border-radius: 2px;
            transition: transform 0.3s ease, opacity 0.2s;
        }}
        .sidebar[data-collapsed="true"] .sidebar-toggle-bar:nth-child(1) {{ transform: translateX(4px) rotate(45deg) translateY(4px); }}
        .sidebar[data-collapsed="true"] .sidebar-toggle-bar:nth-child(2) {{ opacity: 0; }}
        .sidebar[data-collapsed="true"] .sidebar-toggle-bar:nth-child(3) {{ transform: translateX(4px) rotate(-45deg) translateY(-4px); }}
        .sidebar ul {{ list-style: none; }}
        .sidebar li {{ margin-bottom: 8px; }}
        .sidebar a {{
            color: #aaa;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 8px;
            transition: background 0.2s, color 0.2s;
            font-size: 0.95rem;
        }}
        .sidebar a:hover {{ background: #222; color: #fff; }}
        .sidebar a.active {{ background: #222; color: #fff; font-weight: 500; }}
        .sidebar[data-collapsed="true"] a {{
            justify-content: center;
            padding: 10px;
            font-size: 0;
            gap: 0;
        }}
        .sidebar[data-collapsed="true"] a span {{ font-size: 1.1rem; }}
        .sidebar-logout {{ margin-top: auto; }}

        .main-content {{
            flex: 1;
            padding: 40px;
            display: flex;
            justify-content: center;
            overflow-y: auto;
        }}
        .main-content .content-wrapper {{ width: 100%; max-width: 900px; }}

        .card {{
            background: #151515;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .card h2, .card h3 {{ margin-bottom: 16px; font-weight: 500; }}
        input, select, button {{
            background: #1e1e1e;
            color: #fff;
            border: 1px solid #333;
            padding: 10px 14px;
            margin: 6px 0;
            border-radius: 8px;
            font-family: inherit;
            font-size: 14px;
            width: 100%;
            box-sizing: border-box;
        }}
        button {{
            background: #fff;
            color: #000;
            font-weight: 600;
            cursor: pointer;
            width: auto;
            padding: 10px 20px;
            border: none;
        }}
        button:hover {{ background: #ddd; }}
        .status-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 500;
        }}
        .status-ready {{ background: #2ecc71; color: #000; }}
        .status-failed {{ background: #e74c3c; color: #fff; }}
        .status-building {{ background: #f1c40f; color: #000; }}
        .log-window {{
            background: #000;
            color: #0f0;
            padding: 12px;
            border-radius: 8px;
            height: 240px;
            overflow-y: auto;
            font-family: 'Space Grotesk', monospace;
            font-size: 12px;
            margin-top: 12px;
            text-align: left;
        }}
        .challenge-list {{ list-style: none; padding: 0; }}
        .challenge-list li {{ margin: 10px 0; padding: 12px; background: #1a1a1a; border-radius: 8px; }}
        .flash {{ padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; }}
        .flash.success {{ background: #2ecc71; color: #000; }}
        .flash.error {{ background: #e74c3c; color: #fff; }}
    </style>
</head>
<body>
    <div class="admin-layout">
        {sidebar_html(active)}
        <div class="main-content">
            <div class="content-wrapper">
                {content}
            </div>
        </div>
    </div>
</body>
</html>
"""


def centered_layout(content: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CTFploy</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600&display=swap');
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family: 'Space Grotesk', sans-serif; background:#0a0a0a; color:#e0e0e0; }}
        a {{ color:#aaa; text-decoration:none; }}
        a:hover {{ color:#fff; }}
        code {{ background:#333; padding:2px 6px; border-radius:4px; }}
        .centered-page {{ display:flex; justify-content:center; align-items:center; min-height:100vh; padding:20px; }}
        .centered-container {{ width:100%; max-width:500px; }}
        .card {{ background:#151515; border:1px solid #2a2a2a; border-radius:12px; padding:28px; }}
        .card h2 {{ margin-bottom:20px; font-weight:500; }}
        input, button {{
            background: #1e1e1e;
            color: #fff;
            border: 1px solid #333;
            padding: 10px 14px;
            margin: 6px 0;
            border-radius: 8px;
            font-family: inherit;
            font-size: 14px;
            width: 100%;
            box-sizing: border-box;
        }}
        button {{
            background: #fff;
            color: #000;
            font-weight: 600;
            cursor: pointer;
            width: auto;
            padding: 10px 20px;
            border: none;
        }}
        button:hover {{ background: #ddd; }}
        .flash {{ padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; }}
        .flash.success {{ background: #2ecc71; color: #000; }}
        .flash.error {{ background: #e74c3c; color: #fff; }}
    </style>
</head>
<body>
    {content}
</body>
</html>
"""


def sign_in_page(error: bool = False) -> str:
    error_msg = '<p style="color:#e74c3c; margin-bottom:12px;">Invalid credentials</p>' if error else ""
    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card" style="text-align:center;">
                <h2 style="font-size:1.5rem; margin-bottom:8px;">CTFploy</h2>
                <p style="color:#888; margin-bottom:24px;">Sign in to your account</p>
                {error_msg}
                <form method="post">
                    <input name="username" placeholder="Username" required autofocus>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit" style="width:100%; margin-top:8px;">Sign In</button>
                </form>
                <p style="margin-top:16px; font-size:0.9rem; color:#888;">
                    No account? <a href="/register" style="color:#fff;">Register</a>
                </p>
            </div>
        </div>
    </div>
    """)


def register_page(error: bool = False) -> str:
    error_msg = '<p style="color:#e74c3c; margin-bottom:12px;">User already exists</p>' if error else ""
    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card" style="text-align:center;">
                <h2 style="font-size:1.5rem; margin-bottom:8px;">Create Account</h2>
                <p style="color:#888; margin-bottom:24px;">Join CTFploy</p>
                {error_msg}
                <form method="post">
                    <input name="username" placeholder="Username" required autofocus>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit" style="width:100%; margin-top:8px;">Register</button>
                </form>
            </div>
        </div>
    </div>
    """)


def dashboard_page(user, user_challenges, get_instance, flashes=None) -> str:
    flash_html = ""
    if flashes:
        for category, message in flashes:
            flash_html += f'<div class="flash {category}">{message}</div>'

    challenges_html = ""
    if user_challenges:
        challenges_html = '<div style="margin-top:24px;"><h3 style="margin-bottom:12px; font-weight:500;">Your Challenges</h3><ul class="challenge-list">'
        for ch in user_challenges:
            inst = get_instance(user["id"], ch["id"])
            if inst:
                challenges_html += f'<li><strong>{ch["display_name"]}</strong> <span class="status-badge status-ready">Ready</span> (port {inst["host_port"]} – <a href="/instance/{inst["id"]}">View</a>)</li>'
            else:
                challenges_html += f'<li><strong>{ch["display_name"]}</strong> <span class="status-badge status-ready">Ready</span> <a href="/start/{ch["id"]}"><button style="margin-left:8px;">Start</button></a></li>'
        challenges_html += "</ul></div>"

    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                    <h2 style="margin:0;">Welcome, {user["username"]}</h2>
                    <a href="/logout"><button>Logout</button></a>
                </div>
                {flash_html}
                <div style="margin-top:20px;">
                    <h3 style="margin-bottom:8px; font-weight:500;">Enter Access Code</h3>
                    <form method="post" action="/user/redeem-code">
                        <input name="code" placeholder="Access Code" required>
                        <button type="submit" style="width:100%; margin-top:8px;">Unlock Challenges</button>
                    </form>
                </div>
                {challenges_html}
            </div>
        </div>
    </div>
    """)


def instance_page(ch, inst, host, msg, hints) -> str:
    hints_html = ""
    if hints:
        hints_html = '<div style="margin-top:16px;"><strong>Hints:</strong><ul style="margin-left:20px; margin-top:8px;">'
        for hint in hints:
            hints_html += f"<li>{hint}</li>"
        hints_html += "</ul></div>"

    if inst["connection_type"] == "ssh":
        conn_html = f'<p>SSH: <code>ssh {inst["username"]}@{host} -p {inst["host_port"]}</code></p><p>Password: <code>{inst["password"]}</code></p>'
    elif inst["connection_type"] == "web":
        conn_html = f'<p>URL: <a href="http://{host}:{inst["host_port"]}">http://{host}:{inst["host_port"]}</a></p>'
    elif inst["connection_type"] == "nc":
        conn_html = f'<p>Netcat: <code>nc {host} {inst["host_port"]}</code></p>'
    else:
        conn_html = f'<p>Port: {inst["host_port"]}</p>'

    msg_html = f'<p style="color:{"#2ecc71" if msg == "Correct!" else "#e74c3c"};">{msg}</p>' if msg else ""

    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>{ch["display_name"]}</h2>
                <p>Status: {inst["status"]}</p>
                {conn_html}
                {hints_html}
                <p style="margin-top:12px;">Expires: <span id="countdown">{inst["expires_at"]}</span></p>
                <a href="/terminate/{inst["id"]}"><button style="margin-top:16px;">Terminate</button></a>
                <div style="margin-top:24px;">
                    <h3 style="margin-bottom:8px; font-weight:500;">Submit Flag</h3>
                    <form action="/submit_flag/{inst["id"]}" method="post" style="display:flex; gap:8px;">
                        <input name="flag" placeholder="flag{{...}}" required style="flex:1;">
                        <button type="submit">Submit</button>
                    </form>
                    {msg_html}
                </div>
                <a href="/dashboard" style="display:inline-block; margin-top:16px; color:#888;">Back to dashboard</a>
            </div>
        </div>
    </div>
    <script>
        const expires = new Date("{inst["expires_at"]}");
        setInterval(() => {{
            const diff = expires - new Date();
            if (diff <= 0) document.getElementById('countdown').textContent = 'Expired';
            else {{
                const m = Math.floor(diff/60000);
                const s = Math.floor((diff%60000)/1000);
                document.getElementById('countdown').textContent = m + ':' + (s<10?'0':'') + s;
            }}
        }}, 1000);
    </script>
    """)


def build_log_page(challenge_id: str) -> str:
    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>Build Log</h2>
                <div id="log" class="log-window"></div>
                <a href="/admin/challenges" style="display:inline-block; margin-top:16px; color:#888;">Back to challenges</a>
            </div>
        </div>
    </div>
    <script>
        const evtSource = new EventSource("/admin/build_log_stream/{challenge_id}");
        const logDiv = document.getElementById("log");
        evtSource.onmessage = function(event) {{
            if (event.data === "END") {{ evtSource.close(); return; }}
            logDiv.innerHTML += event.data;
            logDiv.scrollTop = logDiv.scrollHeight;
        }};
        evtSource.onerror = function() {{ evtSource.close(); }};
    </script>
    """)


def admin_dashboard_page(challenges, instances, flashes=None) -> str:
    flash_html = ""
    if flashes:
        for category, message in flashes:
            flash_html += f'<div class="flash {category}">{message}</div>'

    active_count = len([i for i in instances if i["status"] == "running"])
    return admin_layout(f"""
    {flash_html}
    <div class="card">
        <h2>Dashboard</h2>
        <p>Total challenges: {len(challenges)}</p>
        <p>Active instances: {active_count}</p>
    </div>
    """, active="dashboard")


def admin_challenges_page(challenges, store_files) -> str:
    store_html = ""
    if store_files:
        store_html = '<div class="card"><h3>Pre-built Challenges</h3><ul class="challenge-list">'
        for f in store_files:
            store_html += f"""
            <li>
                <form method="post" action="/admin/build-from-store" style="display:inline;">
                    <input type="hidden" name="filename" value="{f}">
                    <span>{f}</span>
                    <button type="submit" style="margin-left:10px;">Build</button>
                </form>
            </li>
            """
        store_html += "</ul></div>"

    challenges_html = '<div class="card"><h3>All Challenges</h3><ul class="challenge-list">'
    for ch in challenges:
        status_cls = "status-ready" if ch["build_status"] == "success" else ("status-building" if ch["build_status"] == "building" else "status-failed")
        status_label = "Ready" if ch["build_status"] == "success" else ("Building" if ch["build_status"] == "building" else "Failed")
        challenges_html += f"""
        <li>
            <strong>{ch["display_name"]}</strong> ({ch["image_tag"]})
            <span class="status-badge {status_cls}">{status_label}</span>
            [<a href="/admin/build_log/{ch["id"]}">Logs</a>]
            [<a href="/admin/delete_challenge/{ch["id"]}">Delete</a>]
        </li>
        """
    challenges_html += "</ul></div>"

    return admin_layout(f"""
    <h2>Challenges</h2>

    <div class="card">
        <h3>Import from URL</h3>
        <form action="/admin/import-url" method="post">
            <input name="url" placeholder="https://example.com/challenge.tar.gz" required>
            <button type="submit">Fetch & Build</button>
        </form>
        <p style="font-size:0.85rem; color:#888; margin-top:8px;">Archive must contain a Dockerfile (and optionally <code>ctfploy.json</code>).</p>
    </div>

    {store_html}
    {challenges_html}
    """, active="terminal")


def admin_codes_page(access_codes, challenges, get_challenge, flashes=None) -> str:
    flash_html = ""
    if flashes:
        for category, message in flashes:
            flash_html += f'<div class="flash {category}">{message}</div>'

    codes_html = '<div class="card"><ul class="challenge-list">'
    for code in access_codes:
        used_by = f'<span style="color:#aaa;">(used by: {", ".join(code.get("used_by", []))})</span>' if code.get("used_by") else '<span style="color:#aaa;">(unused)</span>'
        challenges_list = ""
        for cid in code.get("challenges", []):
            ch = get_challenge(cid)
            if ch:
                challenges_list += f"<li>{ch['display_name']} ({ch['build_status']})</li>"

        codes_html += f"""
        <li>
            <strong>{code["code"]}</strong> {used_by}
            <ul style="margin-left:20px; margin-top:6px;">{challenges_list}</ul>
            <form action="/admin/add_challenge_to_code" method="post" style="margin-top:8px; display:flex; gap:8px;">
                <input type="hidden" name="code" value="{code["code"]}">
                <select name="challenge_id" style="flex:1;">
                    {' '.join([f'<option value="{ch["id"]}">{ch["display_name"]}</option>' for ch in challenges if ch["build_status"] == "success"])}
                </select>
                <button type="submit">Add</button>
            </form>
            [<a href="/admin/delete_code/{code["code"]}">Delete</a>]
        </li>
        """
    codes_html += "</ul></div>"

    return admin_layout(f"""
    {flash_html}
    <h2>Access Codes</h2>
    <div class="card">
        <form action="/admin/gencode" method="post">
            <button type="submit">Generate New Code</button>
        </form>
    </div>
    {codes_html}
    """, active="code_badge")


def admin_update_page(flashes=None) -> str:
    flash_html = ""
    if flashes:
        for category, message in flashes:
            flash_html += f'<div class="flash {category}">{message}</div>'

    return admin_layout(f"""
    {flash_html}
    <h2>Update Platform</h2>
    <div class="card">
        <p style="margin-bottom:16px;">Pull the latest image from Docker Hub and restart the platform container.</p>
        <form method="post">
            <button type="submit">Update Now</button>
        </form>
    </div>
    """, active="upload")
