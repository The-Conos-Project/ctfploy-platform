def centered_layout(content: str, title: str = "CTFploy") -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600&display=swap');
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family: 'Space Grotesk', sans-serif; background:#0a0a0a; color:#e8e8e8; min-height:100vh; }}
        a {{ color:#a8a8a8; text-decoration:none; }}
        a:hover {{ color:#fff; }}
        .centered-page {{ display:flex; justify-content:center; align-items:center; min-height:100vh; padding:20px; }}
        .centered-container {{ width:100%; max-width:520px; }}
        .card {{ background:#141414; border:1px solid #262626; border-radius:18px; padding:28px; box-shadow:0 14px 40px rgba(0,0,0,0.25); }}
        h2 {{ margin-bottom:18px; font-size:1.8rem; font-weight:600; }}
        p {{ color:#bdbdbd; line-height:1.6; }}
        input, button {{ font-family: inherit; font-size: 14px; border-radius: 12px; border: 1px solid #333; }}
        input {{ width:100%; color:#fff; background:#101010; padding:14px 16px; margin:8px 0; }}
        button {{ cursor:pointer; color:#fff; background:#5e6fff; border:none; padding:14px 18px; font-weight:600; transition:transform .18s ease, background .18s ease; }}
        button:hover {{ transform: translateY(-1px); background:#4b55e8; }}
        .secondary-button {{ background:#2b2b2b; color:#d8d8d8; }}
        .secondary-button:hover {{ background:#373737; }}
        .flash {{ border-radius: 12px; padding: 14px 16px; margin-bottom:18px; font-weight:500; }}
        .flash.success {{ background:#2ecc71; color:#061a10; }}
        .flash.error {{ background:#e74c3c; color:#fff; }}
        code {{ background:#0f0f0f; padding:4px 8px; border-radius:8px; color:#f0f0f0; }}
        form button {{ width:100%; margin-top:10px; }}
        .small-text {{ color:#8f8f8f; font-size:0.92rem; margin-top:8px; }}
    </style>
</head>
<body>
    {content}
</body>
</html>
"""


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
        items += f'<li><a href="{href}" class="{cls}"><span class="sidebar-icon">{_get_icon(key)}</span><span>{label}</span></a></li>'
    return f"""
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <h3>CTFploy Admin</h3>
            <button class="sidebar-toggle" id="sidebarToggle" aria-label="Toggle sidebar"><span></span></button>
        </div>
        <ul>
            {items}
            <li class="sidebar-logout"><a href="/admin/logout"><span class="sidebar-icon">{_get_icon('logout')}</span><span>Logout</span></a></li>
        </ul>
    </div>
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
        body {{ font-family: 'Space Grotesk', sans-serif; background:#0a0a0a; color:#e7e7e7; min-height:100vh; }}
        a {{ color:#b9b9b9; text-decoration:none; }}
        a:hover {{ color:#fff; }}
        .admin-layout {{ display:flex; min-height:100vh; }}
        .sidebar {{ width:250px; background:#111; border-right:1px solid #222; transition: width .25s ease, padding .25s ease; overflow:hidden; position:relative; }}
        .sidebar.collapsed {{ width:72px; padding:18px 10px; }}
        .sidebar-header {{ display:flex; align-items:center; justify-content:space-between; gap:10px; padding:18px; }}
        .sidebar h3 {{ font-size:1.05rem; color:#fff; line-height:1.2; transition: opacity .2s ease; }}
        .sidebar.collapsed h3 {{ opacity:0; width:0; overflow:hidden; height:0; }}
        .sidebar-toggle {{ background:#1f1f1f; border:1px solid #2a2a2a; color:#d1d1d1; border-radius:14px; width:44px; height:44px; display:flex; align-items:center; justify-content:center; cursor:pointer; transition:background .2s ease, transform .2s ease; }}
        .sidebar-toggle:hover {{ background:#2d2d2d; transform:scale(1.02); }}
        .sidebar-toggle span {{ display:block; width:18px; height:2px; background:#c1c1c1; border-radius:999px; position:relative; }}
        .sidebar-toggle span::before, .sidebar-toggle span::after {{ content:''; position:absolute; left:0; width:100%; height:100%; background:#c1c1c1; border-radius:999px; }}
        .sidebar-toggle span::before {{ top:-6px; }}
        .sidebar-toggle span::after {{ top:6px; }}
        .sidebar.collapsed .sidebar-toggle span {{ transform: rotate(45deg); }}
        .sidebar.collapsed .sidebar-toggle span::before {{ top:0; transform: rotate(90deg); }}
        .sidebar.collapsed .sidebar-toggle span::after {{ display:none; }}
        .sidebar ul {{ list-style:none; padding:0 10px 18px; }}
        .sidebar li {{ margin-bottom:10px; }}
        .sidebar a {{ display:flex; align-items:center; gap:14px; padding:12px 14px; border-radius:14px; color:#c3c3c3; transition:background .2s ease, color .2s ease; }}
        .sidebar a:hover, .sidebar a.active {{ background:#222; color:#fff; }}
        .sidebar.collapsed a {{ justify-content:center; gap:0; padding:12px 0; font-size:0; }}
        .sidebar.collapsed a span:last-child {{ display:none; }}
        .sidebar-icon {{ font-size:1.15rem; display:inline-flex; align-items:center; justify-content:center; width:24px; }}
        .sidebar-logout {{ margin-top:auto; padding:0 10px 18px; }}
        .main-content {{ flex:1; padding:32px; overflow:auto; }}
        .content-wrapper {{ max-width:1040px; margin:0 auto; }}
        .card {{ background:#141414; border:1px solid #232323; border-radius:18px; padding:26px; margin-bottom:24px; box-shadow:0 18px 40px rgba(0,0,0,0.18); }}
        h1,h2,h3 {{ color:#f5f5f5; font-weight:600; }}
        p, li, label, span {{ color:#b9b9b9; line-height:1.65; }}
        input, select, button, textarea {{ font-family: inherit; border-radius:12px; border:1px solid #2a2a2a; background:#111; color:#f4f4f4; }}
        input, select, textarea {{ padding:12px 14px; width:100%; margin-top:10px; }}
        button {{ border:none; padding:12px 18px; font-weight:600; cursor:pointer; background:#6a7cff; color:#fff; transition:background .18s ease, transform .18s ease; }}
        button:hover {{ background:#5b67d1; transform:translateY(-1px); }}
        .secondary-button {{ background:#1f1f1f; color:#d2d2d2; }}
        .secondary-button:hover {{ background:#2a2a2a; }}
        .status-badge {{ display:inline-flex; align-items:center; gap:6px; padding:6px 12px; border-radius:999px; font-size:.85rem; font-weight:700; }}
        .status-ready {{ background:#2ecc71; color:#081c0f; }}
        .status-building {{ background:#f1c40f; color:#1d1600; }}
        .status-failed {{ background:#e74c3c; color:#fff; }}
        .log-window {{ background:#060606; color:#9cff88; padding:16px; border-radius:14px; overflow:auto; max-height:320px; font-family:SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; font-size:13px; line-height:1.5; }}
        .challenge-list {{ list-style:none; padding:0; }}
        .challenge-list li {{ padding:16px 18px; margin-bottom:14px; background:#161616; border-radius:16px; border:1px solid #222; }}
        .challenge-list li strong {{ display:block; margin-bottom:8px; }}
        .form-row {{ display:flex; gap:14px; flex-wrap:wrap; }}
        .form-row > * {{ flex:1; }}
        .flash {{ padding:14px 16px; border-radius:14px; margin-bottom:20px; }}
        .flash.success {{ background:#2ecc71; color:#081c0f; }}
        .flash.error {{ background:#e74c3c; color:#fff; }}
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
    <script>
        const sidebar = document.getElementById('sidebar');
        const toggle = document.getElementById('sidebarToggle');
        const stateKey = 'ctfploy-sidebar-collapsed';
        function updateSidebar() {{
            const collapsed = sidebar.classList.contains('collapsed');
            toggle.setAttribute('aria-label', collapsed ? 'Open sidebar' : 'Close sidebar');
        }}
        if (localStorage.getItem(stateKey) === '1') {{
            sidebar.classList.add('collapsed');
        }}
        updateSidebar();
        toggle?.addEventListener('click', () => {{
            sidebar.classList.toggle('collapsed');
            localStorage.setItem(stateKey, sidebar.classList.contains('collapsed') ? '1' : '0');
            updateSidebar();
        }});
    </script>
</body>
</html>
"""
