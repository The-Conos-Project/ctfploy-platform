from html import escape


def icon(name: str) -> str:
    """Render a Lucide icon (lucide.dev) via data-lucide + createIcons()."""
    aliases = {
        "boxes": "package",
        "classes": "users",
        "cube": "box",
        "log-out": "log-out",
        "circle-x": "circle-x",
        "circle-alert": "circle-alert",
        "leaderboard": "trophy",
    }
    lucide_name = aliases.get(name, name)
    return f'<i data-lucide="{lucide_name}" aria-hidden="true"></i>'


def lang_switcher() -> str:
    from i18n import get_lang, t
    current = get_lang()
    uz_cls = "active" if current == "uz" else ""
    en_cls = "active" if current == "en" else ""
    return (
        f'<div class="lang-switch" role="group" aria-label="Language">'
        f'<a class="{uz_cls}" href="/lang/uz">{t("lang_uz")}</a>'
        f'<a class="{en_cls}" href="/lang/en">{t("lang_en")}</a>'
        f'</div>'
    )

STYLE = """
*{box-sizing:border-box}body{margin:0;background:#080c16;color:#edf2ff;font:15px 'Space Grotesk',ui-sans-serif,system-ui,sans-serif}a{color:inherit;text-decoration:none}svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}.shell{display:flex;min-height:100vh}.sidebar{width:248px;padding:18px 12px;background:#0d1527;border-right:1px solid #1f2d47;display:flex;flex-direction:column;transition:width .2s,padding .2s;position:sticky;top:0;height:100vh;overflow-y:auto;flex-shrink:0;z-index:10}.sidebar-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding:0 4px}.collapse-toggle{background:transparent;color:#aebddd;border:none;outline:none;cursor:pointer;padding:8px;font-size:18px;display:flex;align-items:center;justify-content:center;transition:color .2s,background .2s;border-radius:6px}.collapse-toggle:hover{color:#fff;background:#1e2d4a}.brand{font-weight:800;font-size:20px;color:#fff;transition:opacity .2s}.brand small{display:block;font-size:11px;color:#8da2ce;font-weight:600;margin-top:3px}.nav{display:grid;gap:5px;margin-top:12px}.nav a,.logout-link{display:flex;gap:12px;align-items:center;padding:11px 12px;border-radius:9px;color:#aebddd;transition:all 0.2s}.nav a:hover,.nav a.active,.logout-link:hover{background:#1e2d4a;color:#fff}.logout{margin-top:auto;padding:8px 0;position:sticky;bottom:0;background:#0d1527;z-index:5}.logout-link{display:flex;gap:10px;align-items:center;padding:11px 12px;border-radius:8px;color:#aebddd;transition:all 0.2s;white-space:nowrap}.logout-link:hover{background:#1e2d4a;color:#fff}.main{flex:1;padding:36px;max-width:1100px;margin:0 auto}.card{background:#11192e;border:1px solid #203154;border-radius:14px;padding:24px;margin-bottom:18px;box-shadow:0 4px 20px rgba(0,0,0,0.25)}.grid{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}.stat{font-size:32px;font-weight:800;color:#79a6ff;margin-top:6px}.muted,.small-text{color:#8da2ce}.flash{padding:12px 14px;border-radius:10px;margin-bottom:16px;font-weight:550}.flash.success{background:#0e3025;color:#8efcd4;border:1px solid #164e3c}.flash.error{background:#3d1620;color:#ffb3c1;border:1px solid #5e2230}input,select,textarea{width:100%;background:#090d1a;border:1px solid #203154;border-radius:8px;color:#fff;padding:11px;margin:7px 0 12px;outline:none;transition:border-color 0.2s;font-family:'Space Grotesk',ui-sans-serif,system-ui,sans-serif}input:focus,select:focus{border-color:#4f7bf7}button{border:0;border-radius:8px;padding:11px 18px;background:linear-gradient(135deg,#79a6ff,#4f7bf7);color:#fff;font-weight:700;cursor:pointer;transition:transform 0.15s,filter 0.15s;font-family:'Space Grotesk',ui-sans-serif,system-ui,sans-serif}button:hover{filter:brightness(1.1)}button:active{transform:scale(0.97)}button.secondary{background:#1b263e;color:#aebddd;border:1px solid #2d3e5c}button.secondary:hover{background:#233252;color:#fff}.list{list-style:none;padding:0;margin:0}.list li{padding:16px 0;border-bottom:1px solid #1f2d47}.list li:last-child{border:0}.status-badge{display:inline-block;border-radius:99px;padding:4px 10px;font-size:11px;font-weight:700;margin-top:7px;text-transform:uppercase;letter-spacing:0.5px}.status-success{background:#0f382a;color:#7bf5c3}.status-ready{background:#1b263e;color:#aebddd;border:1px solid #2d3e5c}.status-building{background:#3d2f0f;color:#ffd77a}.status-failed{background:#3d131f;color:#ffa3b8}.row{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}.command{margin:8px 0;padding:12px;white-space:pre-wrap;background:#07101d;color:#aef5bf;border-radius:8px;font-family:ui-monospace,monospace}.hero{padding:80px 24px;text-align:center;max-width:900px;margin:auto}.hero h1{font-size:clamp(38px,7vw,70px);margin:0;background:linear-gradient(to right,#fff,#8da2ce);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.hero p{font-size:18px;color:#8da2ce;line-height:1.7}.footer{padding:24px;text-align:center;color:#60739b}.log-window{white-space:pre-wrap;background:#050a12;color:#aef5bf;padding:16px;border-radius:10px;min-height:220px;max-height:420px;overflow:auto;font-family:ui-monospace,monospace;border:1px solid #1c273c}.sidebar.collapsed{width:64px;padding:18px 7px}.sidebar.collapsed .brand{display:none}.sidebar.collapsed .sidebar-header{justify-content:center;padding:0}.sidebar.collapsed .nav span,.sidebar.collapsed .logout-link span{display:none}.sidebar.collapsed .nav a,.sidebar.collapsed .logout-link{justify-content:center}.sidebar.collapsed .collapse-toggle{margin-left:0}.sidebar.collapsed .lang-switch-wrap{display:none!important}.terminal-snippet{display:flex;align-items:center;gap:10px;background:#050912;border:1px solid #1f2d47;border-radius:8px;padding:10px 14px;margin:8px 0;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:13.5px}.terminal-prompt{color:#4f7bf7;font-weight:bold;user-select:none}.terminal-cmd{color:#7bf5c3;flex:1;overflow-x:auto;white-space:nowrap}.copy-btn{background:#16223b;color:#aebddd;border:1px solid #2d3e5c;border-radius:6px;padding:5px 10px;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s;width:auto;margin:0;white-space:nowrap}.copy-btn:hover{background:#233252;color:#fff}.inline-code{background:#141f36;border:1px solid #243557;color:#79a6ff;padding:2px 6px;border-radius:5px;font-family:ui-monospace,monospace;font-size:13px}.modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.75);z-index:999;align-items:center;justify-content:center;padding:24px}.modal-content{background:#0d1527;border:1px solid #203154;border-radius:14px;padding:28px;box-shadow:0 20px 60px rgba(0,0,0,0.6)}.flag-card{background:#11192e;border:1px solid #203154;border-radius:12px;padding:18px;transition:border-color .2s}.flag-card:hover{border-color:#4f7bf7}.flag-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:0 12px}.toast-container{position:fixed;top:16px;right:16px;z-index:9999;display:flex;flex-direction:column;gap:10px;pointer-events:none}.toast{background:#11192e;border:1px solid #203154;border-radius:12px;padding:14px 18px;color:#edf2ff;font-size:14px;box-shadow:0 8px 30px rgba(0,0,0,0.4);display:flex;align-items:center;gap:10px;pointer-events:auto;transform:translateX(120%);opacity:0;transition:all 0.3s cubic-bezier(0.16,1,0.3,1)}.toast.show{transform:translateX(0);opacity:1}.toast.hide{transform:translateX(120%);opacity:0}.toast.success{border-left:4px solid #7bf5c3}.toast.error{border-left:4px solid #ffb3c1}.toast.info{border-left:4px solid #79a6ff}.badge-external{position:absolute;top:-10px;right:12px;background:#11192e;border:1px solid #203154;border-radius:99px;padding:3px 10px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;z-index:2}.badge-external.status-ready{background:#0f382a;color:#7bf5c3;border-color:#164e3c}.badge-external.status-building{background:#3d2f0f;color:#ffd77a;border-color:#5e4a1a}.badge-external.status-failed{background:#3d131f;color:#ffa3b8;border-color:#5e2230}.badge-external.status-success{background:#0f382a;color:#7bf5c3;border-color:#164e3c}.challenge-card.solved{border-color:#164e3c;box-shadow:0 0 0 1px #164e3c}.challenge-card.solved::after{content:"✓";position:absolute;top:12px;right:12px;width:28px;height:28px;background:#0f382a;color:#7bf5c3;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:bold}.modal-close{background:transparent;border:none;color:#aebddd;padding:6px;cursor:pointer;border-radius:6px;display:flex;align-items:center;justify-content:center;transition:all 0.2s}.modal-close:hover{background:#1e2d4a;color:#fff}.centered-page{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:24px}.centered-container{width:100%;max-width:420px}.labs-fab{position:fixed;bottom:24px;right:24px;z-index:50;width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,#1e3a8a,#0f172a);color:#fff;border:0;cursor:pointer;box-shadow:0 8px 24px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;transition:transform .15s,filter .15s}.labs-fab:hover{filter:brightness(1.2);transform:scale(1.05)}.labs-menu{display:none;position:fixed;bottom:88px;right:24px;z-index:50;width:340px;max-height:480px;overflow-y:auto;background:#0d1527;border:1px solid #203154;border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,0.6);padding:14px}.labs-menu.open{display:block}.labs-menu-item{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:8px 6px;border-bottom:1px solid #1f2d47}.lab-name{display:block;font-size:13px;font-weight:650;line-height:1.25;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.lab-endpoint{margin-top:2px;font-size:12px;color:#8da2ce;font-family:ui-monospace,monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.labs-menu-item:last-child{border:0}.labs-menu-item .lab-info{flex:1;min-width:0;overflow:hidden}.labs-menu-item .lab-x{width:32px;height:32px;border-radius:50%;background:#3d131f;color:#ffb3c1;border:1px solid #5e2230;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s;flex-shrink:0}.labs-menu-item .lab-x:hover{background:#5e2230;color:#fff}.copy-class{background:#16223b;color:#aebddd;border:1px solid #2d3e5c;border-radius:6px;padding:4px 8px;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s;width:auto;margin:0;white-space:nowrap}.copy-class:hover{background:#233252;color:#fff}@media(max-width:700px){.sidebar{width:64px;padding:12px 7px}.brand,.nav span,.logout-link span,.lang-switch-wrap{display:none}.nav a,.logout-link{justify-content:center}.main{padding:20px}.flag-grid{grid-template-columns:1fr}.labs-menu{left:12px;right:12px;width:auto;bottom:80px}}
.brand-mark{font-weight:800;font-size:20px;color:#fff}.topbar{padding:18px 7%;border-bottom:1px solid #283452}.topbar-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.lang-switch{display:inline-flex;border:1px solid #2d3e5c;border-radius:8px;overflow:hidden;background:#0d1527}.lang-switch a{padding:7px 10px;font-size:12px;font-weight:650;color:#8da2ce}.lang-switch a.active,.lang-switch a:hover{background:#1e2d4a;color:#fff}.auth-card h2{font-size:24px}.auth-form label{display:block;font-size:13px;color:#8da2ce;font-weight:600}i[data-lucide],svg.lucide{width:19px;height:19px;display:inline-block;vertical-align:middle;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}.badge{display:inline-block;padding:6px 12px;border-radius:999px;border:1px solid #2d3e5c;background:#11192e;color:#aebddd;font-size:12px;font-weight:700;letter-spacing:.3px;margin-bottom:18px}"""


def layout(content: str, title="CTFploy", sidebar=None, toasts=None) -> str:
    from i18n import get_lang, t

    lang = get_lang()
    nav = ""
    if sidebar:
        links, active, role = sidebar
        subtitle = t("role_admin") if role == "admin" else t("role_student")
        logout_href = "/admin/logout" if role == "admin" else "/logout"
        lang_block = f'<div class="lang-switch-wrap" style="padding:8px 4px 12px">{lang_switcher()}</div>'
        nav = (
            f'<aside class="sidebar" id="sidebar">'
            f'<div class="sidebar-header"><div class="brand">CTFploy<small>{escape(subtitle)}</small></div>'
            f'<button class="collapse-toggle" type="button" aria-label="Toggle sidebar" onclick="toggleSidebar()">☰</button></div>'
            f'{lang_block}<nav class="nav">'
            + "".join(
                f'<a class="{"active" if key == active else ""}" href="{href}">{icon(key)}<span>{label}</span></a>'
                for key, href, label in links
            )
            + f'</nav><div class="logout"><a class="logout-link" href="{logout_href}">{icon("log-out")}<span>{t("logout")}</span></a></div></aside>'
        )
    body = f'<div class="shell">{nav}<main class="main">{content}</main></div>' if sidebar else content
    script = (
        "<script>function toggleSidebar(){const s=document.getElementById('sidebar');s.classList.toggle('collapsed');"
        "localStorage.setItem('ctfploy-sidebar',s.classList.contains('collapsed')?'1':'0')}"
        "if(localStorage.getItem('ctfploy-sidebar')==='1')document.getElementById('sidebar')?.classList.add('collapsed')</script>"
        if sidebar
        else ""
    )
    toast_container = '<div class="toast-container" id="toast-container"></div>'
    toast_script = """
    <script>
    function showToast(message, type) {
      const container = document.getElementById('toast-container');
      if (!container) return;
      const toast = document.createElement('div');
      toast.className = 'toast ' + (type || 'info');
      toast.textContent = message;
      container.appendChild(toast);
      requestAnimationFrame(() => toast.classList.add('show'));
      setTimeout(() => {
        toast.classList.remove('show');
        toast.classList.add('hide');
        toast.addEventListener('transitionend', () => toast.remove());
      }, 5000);
    }
    """
    for kind, message in (toasts or []):
        toast_script += f"showToast({escape(message)!r}, {escape(kind)!r});\n"
    toast_script += "</script>"
    no_labs = escape(t("no_active_labs"))
    fail_load = escape(t("failed_load"))
    labs_menu_js = f"""
function htmlEsc(s){{
    return String(s==null?'':s)
      .replace(/&/g,'&amp;')
      .replace(/</g,'&lt;')
      .replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;')
      .replace(/'/g,'&#39;');
}}
function toggleLabsMenu(){{
    const m=document.getElementById('labs-menu');
    const b=document.getElementById('labs-fab');
    if(!m||!b)return;
    const open=m.classList.contains('open');
    if(open){{
        m.classList.remove('open');
    }}else{{
        m.classList.add('open');
        fetch('/api/labs').then(r=>r.json()).then(data=>{{
            const el=document.getElementById('labs-list');
            if(!el)return;
            if(!data.labs||!data.labs.length){{
                el.innerHTML='<span class=\'small-text\'>{no_labs}</span>';
                return;
            }}
            let html='';
            data.labs.forEach(lab=>{{
                const name=lab.display_name||'Lab';
                const endpoint=(lab.host||'')+':'+(lab.host_port||'');
                const safeName=htmlEsc(name).replace(/&#39;/g,"\\'");
                html+='<div class=\'labs-menu-item\'>'
                    +'<div class=\'lab-info\'>'
                    +'<strong class=\'lab-name\'>'+htmlEsc(name)+'</strong>'
                    +'<div class=\'lab-endpoint\'>'+htmlEsc(endpoint)+'</div>'
                    +'</div>'
                    +'<button class=\'lab-x\' onclick=\"terminateLab(\''+lab.instance_id+'\', \''+safeName+'\')" title=\'{escape(t("end_lab"))}\'>__X_ICON__</button>'
                    +'</div>';
            }});
            el.innerHTML=html;
            if(window.lucide) lucide.createIcons();
        }}).catch(()=>{{
            document.getElementById('labs-list').innerHTML='<span class=\'small-text\'>{fail_load}</span>';
        }});
    }}
}}
function terminateLab(id, name){{
    if(confirm('{escape(t("end_lab"))}: '+name+'?')){{
        const f=document.createElement('form');
        f.method='POST';
        f.action='/terminate/'+id;
        document.body.appendChild(f);
        f.submit();
    }}
}}
"""
    labs_menu_js = labs_menu_js.replace("__X_ICON__", icon("x"))
    labs_fab = (
        f'<button class="labs-fab" id="labs-fab" onclick="toggleLabsMenu()" title="{escape(t("active_labs"))}">'
        + icon("terminal")
        + f'</button><div class="labs-menu" id="labs-menu"><div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px;">'
        f'<strong style="font-size:14px;">{t("active_labs")}</strong>'
        f'<button class="modal-close" onclick="toggleLabsMenu()">{icon("circle-x")}</button></div>'
        f'<div id="labs-list"><span class="small-text">{t("loading")}</span></div></div>'
        f'<script>{labs_menu_js}</script>'
        if sidebar
        else ""
    )
    lucide = (
        '<script src="https://unpkg.com/lucide@0.469.0"></script>'
        "<script>window.lucide&&lucide.createIcons();</script>"
    )
    return (
        f'<!doctype html><html lang="{escape(lang)}"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<link rel="preconnect" href="https://fonts.googleapis.com">'
        f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        f'<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">'
        f'<title>{escape(title)}</title><style>{STYLE}</style></head>'
        f'<body>{toast_container}{body}{script}{toast_script}{labs_fab}{lucide}</body></html>'
    )


def centered_layout(content: str, title="CTFploy", toasts=None) -> str:
    return layout(content, title, toasts=toasts)


def admin_layout(content, active="home", toasts=None):
    from i18n import t

    links = [
        ("home", "/admin", t("nav_overview")),
        ("classes", "/admin/classes", t("nav_classes")),
        ("boxes", "/admin/challenges", t("nav_challenges")),
        ("leaderboard", "/admin/leaderboard", t("nav_leaderboard")),
        ("users", "/admin/users", t("nav_users")),
        ("settings", "/admin/settings", t("nav_settings")),
    ]
    return layout(content, "CTFploy Admin", (links, active, "admin"), toasts=toasts)


def user_layout(content, active="home", toasts=None):
    from i18n import t

    links = [
        ("home", "/dashboard", t("nav_dashboard")),
        ("users", "/classes", t("nav_my_classes")),
        ("leaderboard", "/leaderboard", t("nav_leaderboard")),
        ("key", "/change-password", t("nav_password")),
    ]
    return layout(content, "CTFploy", (links, active, "student"), toasts=toasts)
