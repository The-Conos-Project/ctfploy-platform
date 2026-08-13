from html import escape


def icon(name: str) -> str:
    paths = {
        "home": '<path d="m3 12 9-9 9 9"/><path d="M5 10v10h14V10"/>',
        "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
        "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
        "boxes": '<path d="m21 16-9 5-9-5V6l9-5 9 5Z"/><path d="m3.3 7 8.7 5 8.7-5M12 22V12"/>',
        "key": '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6M15.5 7.5l1 1M18.5 4.5l1 1"/>',
        "settings": '<path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.1 2.1-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1 1.55V20h-3v-.08a1.7 1.7 0 0 0-1-1.55 1.7 1.7 0 0 0-1.88.34l-.06.06-2.1-2.1.06-.06A1.7 1.7 0 0 0 7.12 15a1.7 1.7 0 0 0-1.55-1H5.5v-3h.08a1.7 1.7 0 0 0 1.55-1A1.7 1.7 0 0 0 6.78 8.1l-.06-.06 2.1-2.1.06.06A1.7 1.7 0 0 0 10.76 6.34a1.7 1.7 0 0 0 1-1.55V4.7h3v.08a1.7 1.7 0 0 0 1 1.55A1.7 1.7 0 0 0 17.64 6l.06-.06 2.1 2.1-.06.06A1.7 1.7 0 0 0 19.4 10a1.7 1.7 0 0 0 1.55 1h.08v3h-.08A1.7 1.7 0 0 0 19.4 15Z"/>',
        "log-out": '<path d="M10 17l5-5-5-5"/><path d="M15 12H3"/><path d="M21 19V5a2 2 0 0 0-2-2h-6"/>',
        "terminal": '<path d="m4 17 6-6-6-6"/><path d="M12 19h8"/>',
    }
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{paths.get(name, paths["home"])}</svg>'


STYLE = """
*{box-sizing:border-box}body{margin:0;background:#0b1020;color:#edf2ff;font:15px Inter,ui-sans-serif,system-ui,sans-serif}a{color:inherit;text-decoration:none}svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}.shell{display:flex;min-height:100vh}.sidebar{width:248px;padding:18px 12px;background:#11182b;border-right:1px solid #283452;display:flex;flex-direction:column}.brand{font-weight:800;font-size:20px;padding:12px;color:#fff}.brand small{display:block;font-size:11px;color:#8da2ce;font-weight:600;margin-top:3px}.nav{display:grid;gap:5px;margin-top:22px}.nav a{display:flex;gap:12px;align-items:center;padding:11px 12px;border-radius:9px;color:#aebddd}.nav a:hover,.nav a.active{background:#24375f;color:#fff}.logout{margin-top:auto}.main{width:100%;padding:36px;max-width:1280px;margin:auto}.card{background:#131d33;border:1px solid #293958;border-radius:14px;padding:22px;margin-bottom:18px}.grid{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}.stat{font-size:28px;font-weight:800;margin-top:6px}.muted,.small-text{color:#a8b6d4}.flash{padding:12px 14px;border-radius:10px;margin-bottom:16px}.flash.success{background:#123d31;color:#bff6dc}.flash.error{background:#4a1e2a;color:#ffd0d7}input,select{width:100%;background:#0c1426;border:1px solid #344667;border-radius:8px;color:#fff;padding:11px;margin:7px 0 12px}button{border:0;border-radius:8px;padding:11px 15px;background:#79a6ff;color:#071022;font-weight:750;cursor:pointer}button.secondary{background:#283957;color:#e8efff}.list{list-style:none;padding:0;margin:0}.list li{padding:15px 0;border-bottom:1px solid #263754}.list li:last-child{border:0}.badge{display:inline-block;border-radius:99px;padding:3px 9px;font-size:12px;font-weight:700;background:#253b62;color:#c8d9ff}.ready{background:#164b38;color:#aaf1ca}.building{background:#574416;color:#ffe7a5}.failed{background:#562333;color:#ffd0da}.row{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}.hero{padding:80px 24px;text-align:center;max-width:900px;margin:auto}.hero h1{font-size:clamp(38px,7vw,70px);margin:0}.hero p{font-size:18px;color:#a8b6d4;line-height:1.7}.footer{padding:24px;text-align:center;color:#8090b2}.log-window{white-space:pre-wrap;background:#07101d;color:#aef5bf;padding:16px;border-radius:10px;min-height:220px;max-height:420px;overflow:auto;font-family:ui-monospace,monospace}@media(max-width:700px){.sidebar{width:64px;padding:12px 7px}.brand{font-size:0}.brand small{display:none}.nav a{font-size:0;justify-content:center}.nav svg{width:21px;height:21px}.main{padding:20px}}
"""


def layout(content: str, title="CTFploy", sidebar=None) -> str:
    nav = ""
    if sidebar:
        links, active, subtitle = sidebar
        nav = '<aside class="sidebar"><div class="brand">CTFploy<small>' + escape(subtitle) + '</small></div><nav class="nav">' + ''.join(f'<a class="{"active" if key == active else ""}" href="{href}">{icon(key)}<span>{label}</span></a>' for key, href, label in links) + f'</nav><div class="logout"><a class="nav" href="{("/admin/logout" if subtitle == "Administrator" else "/logout")}"><span>{icon("log-out")}</span><span>Logout</span></a></div></aside>'
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title><style>{STYLE}</style></head><body>{"<div class=\"shell\">" + nav + "<main class=\"main\">" + content + "</main></div>" if sidebar else content}</body></html>'


def centered_layout(content: str, title="CTFploy") -> str:
    return layout(content, title)


def admin_layout(content, active="home"):
    return layout(content, "CTFploy Admin", ([('home','/admin','Overview'),('users','/admin/classes','Classes'),('boxes','/admin/challenges','Challenges'),('key','/admin/codes','Legacy codes'),('settings','/admin/update','Update')], active, 'Administrator'))


def user_layout(content, active="home"):
    return layout(content, "CTFploy", ([('home','/dashboard','Dashboard'),('book','/dashboard','My classes')], active, 'Student workspace'))
