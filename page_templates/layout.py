from html import escape


def icon(name: str) -> str:
    paths = {
        "home": '<path d="m3 12 9-9 9 9"/><path d="M5 10v10h14V10"/>',
        "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
        "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
        "boxes": '<path d="m21 16-9 5-9-5V6l9-5 9 5Z"/><path d="M3.3 7 8.7 12 8.7 7M12 22V12"/>',
        "key": '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6M15.5 7.5l1 1M18.5 4.5l1 1"/>',
        "settings": '<path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.1 2.1-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1 1.55V20h-3v-.08a1.7 1.7 0 0 0-1-1.55 1.7 1.7 0 0 0-1.88.34l-.06-.06-2.1-2.1.06-.06A1.7 1.7 0 0 0 7.12 15a1.7 1.7 0 0 0-1.55-1H5.5v-3h.08a1.7 1.7 0 0 0 1.55-1A1.7 1.7 0 0 0 6.78 8.1l-.06-.06 2.1-2.1.06.06A1.7 1.7 0 0 0 10.76 6.34a1.7 1.7 0 0 0 1-1.55V4.7h3v.08a1.7 1.7 0 0 0 1 1.55A1.7 1.7 0 0 0 17.64 6l.06-.06 2.1 2.1-.06.06A1.7 1.7 0 0 0 19.4 10a1.7 1.7 0 0 0 1.55 1h.08v3h-.08A1.7 1.7 0 0 0 19.4 15Z"/>',
        "log-out": '<path d="M10 17l5-5-5-5"/><path d="M15 12H3"/><path d="M21 19V5a2 2 0 0 0-2-2h-6"/>',
        "terminal": '<path d="m4 17 6-6-6-6"/><path d="M12 19h8"/>',
        "trophy": '<path d="M6 9H4a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2h-2"/><path d="M12 15V3"/><path d="M6 15a6 6 0 0 0 12 0"/>',
        "arrow-left": '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
        "arrow-right": '<path d="m12 5 7 7-7 7"/><path d="M5 12h14"/>',
        "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
        "x": '<path d="M18 6 6 18"/><path d="M6 6l12 12"/>',
        "chevron-right": '<path d="m9 18 6-6-6-6"/>',
        "chevron-left": '<path d="m15 18-6-6 6-6"/>',
        "circle-x": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
        "copy": '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    }
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{paths.get(name, paths["home"])}</svg>'


STYLE = """
*{box-sizing:border-box}body{margin:0;background:#080c16;color:#edf2ff;font:15px 'Space Grotesk',ui-sans-serif,system-ui,sans-serif}a{color:inherit;text-decoration:none}svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}.shell{display:flex;min-height:100vh}.sidebar{width:248px;padding:18px 12px;background:#0d1527;border-right:1px solid #1f2d47;display:flex;flex-direction:column;transition:width .2s,padding .2s;position:sticky;top:0;height:100vh;overflow-y:auto;flex-shrink:0;z-index:10}.sidebar-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding:0 4px}.collapse-toggle{background:transparent;color:#aebddd;border:none;outline:none;cursor:pointer;padding:8px;font-size:18px;display:flex;align-items:center;justify-content:center;transition:color .2s,background .2s;border-radius:6px}.collapse-toggle:hover{color:#fff;background:#1e2d4a}.brand{font-weight:800;font-size:20px;color:#fff;transition:opacity .2s}.brand small{display:block;font-size:11px;color:#8da2ce;font-weight:600;margin-top:3px}.nav{display:grid;gap:5px;margin-top:12px}.nav a,.logout-link{display:flex;gap:12px;align-items:center;padding:11px 12px;border-radius:9px;color:#aebddd;transition:all 0.2s}.nav a:hover,.nav a.active,.logout-link:hover{background:#1e2d4a;color:#fff}.logout{margin-top:auto;padding:8px 0;position:sticky;bottom:0;background:#0d1527;z-index:5}.logout-link{display:flex;gap:10px;align-items:center;padding:11px 12px;border-radius:8px;color:#aebddd;transition:all 0.2s;white-space:nowrap}.logout-link:hover{background:#1e2d4a;color:#fff}.main{flex:1;padding:36px;max-width:1100px;margin:0 auto}.card{background:#11192e;border:1px solid #203154;border-radius:14px;padding:24px;margin-bottom:18px;box-shadow:0 4px 20px rgba(0,0,0,0.25)}.grid{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}.stat{font-size:32px;font-weight:800;color:#79a6ff;margin-top:6px}.muted,.small-text{color:#8da2ce}.flash{padding:12px 14px;border-radius:10px;margin-bottom:16px;font-weight:550}.flash.success{background:#0e3025;color:#8efcd4;border:1px solid #164e3c}.flash.error{background:#3d1620;color:#ffb3c1;border:1px solid #5e2230}input,select,textarea{width:100%;background:#090d1a;border:1px solid #203154;border-radius:8px;color:#fff;padding:11px;margin:7px 0 12px;outline:none;transition:border-color 0.2s;font-family:'Space Grotesk',ui-sans-serif,system-ui,sans-serif}input:focus,select:focus{border-color:#4f7bf7}button{border:0;border-radius:8px;padding:11px 18px;background:linear-gradient(135deg,#79a6ff,#4f7bf7);color:#fff;font-weight:700;cursor:pointer;transition:transform 0.15s,filter 0.15s;font-family:'Space Grotesk',ui-sans-serif,system-ui,sans-serif}button:hover{filter:brightness(1.1)}button:active{transform:scale(0.97)}button.secondary{background:#1b263e;color:#aebddd;border:1px solid #2d3e5c}button.secondary:hover{background:#233252;color:#fff}.list{list-style:none;padding:0;margin:0}.list li{padding:16px 0;border-bottom:1px solid #1f2d47}.list li:last-child{border:0}.status-badge{display:inline-block;border-radius:99px;padding:4px 10px;font-size:11px;font-weight:700;margin-top:7px;text-transform:uppercase;letter-spacing:0.5px}.status-success{background:#0f382a;color:#7bf5c3}.status-ready{background:#1b263e;color:#aebddd;border:1px solid #2d3e5c}.status-building{background:#3d2f0f;color:#ffd77a}.status-failed{background:#3d131f;color:#ffa3b8}.row{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}.command{margin:8px 0;padding:12px;white-space:pre-wrap;background:#07101d;color:#aef5bf;border-radius:8px;font-family:ui-monospace,monospace}.hero{padding:80px 24px;text-align:center;max-width:900px;margin:auto}.hero h1{font-size:clamp(38px,7vw,70px);margin:0;background:linear-gradient(to right,#fff,#8da2ce);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.hero p{font-size:18px;color:#8da2ce;line-height:1.7}.footer{padding:24px;text-align:center;color:#60739b}.log-window{white-space:pre-wrap;background:#050a12;color:#aef5bf;padding:16px;border-radius:10px;min-height:220px;max-height:420px;overflow:auto;font-family:ui-monospace,monospace;border:1px solid #1c273c}.sidebar.collapsed{width:64px;padding:18px 7px}.sidebar.collapsed .brand{display:none}.sidebar.collapsed .sidebar-header{justify-content:center;padding:0}.sidebar.collapsed .nav span,.sidebar.collapsed .logout-link span{display:none}.sidebar.collapsed .nav a,.sidebar.collapsed .logout-link{justify-content:center}.sidebar.collapsed .collapse-toggle{margin-left:0}.terminal-snippet{display:flex;align-items:center;gap:10px;background:#050912;border:1px solid #1f2d47;border-radius:8px;padding:10px 14px;margin:8px 0;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:13.5px}.terminal-prompt{color:#4f7bf7;font-weight:bold;user-select:none}.terminal-cmd{color:#7bf5c3;flex:1;overflow-x:auto;white-space:nowrap}.copy-btn{background:#16223b;color:#aebddd;border:1px solid #2d3e5c;border-radius:6px;padding:5px 10px;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s;width:auto;margin:0;white-space:nowrap}.copy-btn:hover{background:#233252;color:#fff}.inline-code{background:#141f36;border:1px solid #243557;color:#79a6ff;padding:2px 6px;border-radius:5px;font-family:ui-monospace,monospace;font-size:13px}.modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.75);z-index:999;align-items:center;justify-content:center;padding:24px}.modal-content{background:#0d1527;border:1px solid #203154;border-radius:14px;padding:28px;box-shadow:0 20px 60px rgba(0,0,0,0.6)}.flag-card{background:#11192e;border:1px solid #203154;border-radius:12px;padding:18px;transition:border-color .2s}.flag-card:hover{border-color:#4f7bf7}.flag-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:0 12px}.toast-container{position:fixed;top:16px;right:16px;z-index:9999;display:flex;flex-direction:column;gap:10px;pointer-events:none}.toast{background:#11192e;border:1px solid #203154;border-radius:12px;padding:14px 18px;color:#edf2ff;font-size:14px;box-shadow:0 8px 30px rgba(0,0,0,0.4);display:flex;align-items:center;gap:10px;pointer-events:auto;transform:translateX(120%);opacity:0;transition:all 0.3s cubic-bezier(0.16,1,0.3,1)}.toast.show{transform:translateX(0);opacity:1}.toast.hide{transform:translateX(120%);opacity:0}.toast.success{border-left:4px solid #7bf5c3}.toast.error{border-left:4px solid #ffb3c1}.toast.info{border-left:4px solid #79a6ff}.badge-external{position:absolute;top:-10px;right:12px;background:#11192e;border:1px solid #203154;border-radius:99px;padding:3px 10px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;z-index:2}.badge-external.status-ready{background:#0f382a;color:#7bf5c3;border-color:#164e3c}.badge-external.status-building{background:#3d2f0f;color:#ffd77a;border-color:#5e4a1a}.badge-external.status-failed{background:#3d131f;color:#ffa3b8;border-color:#5e2230}.badge-external.status-success{background:#0f382a;color:#7bf5c3;border-color:#164e3c}.challenge-card.solved{border-color:#164e3c;box-shadow:0 0 0 1px #164e3c}.challenge-card.solved::after{content:"✓";position:absolute;top:12px;right:12px;width:28px;height:28px;background:#0f382a;color:#7bf5c3;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:bold}.modal-close{background:transparent;border:none;color:#aebddd;padding:6px;cursor:pointer;border-radius:6px;display:flex;align-items:center;justify-content:center;transition:all 0.2s}.modal-close:hover{background:#1e2d4a;color:#fff}.centered-page{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:24px}.centered-container{width:100%;max-width:420px}.labs-fab{position:fixed;bottom:24px;right:24px;z-index:50;width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,#1e3a8a,#0f172a);color:#fff;border:0;cursor:pointer;box-shadow:0 8px 24px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;transition:transform .15s,filter .15s}.labs-fab:hover{filter:brightness(1.2);transform:scale(1.05)}.labs-menu{display:none;position:fixed;bottom:88px;right:24px;z-index:50;width:340px;max-height:480px;overflow-y:auto;background:#0d1527;border:1px solid #203154;border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,0.6);padding:14px}.labs-menu.open{display:block}.labs-menu-item{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 8px;border-bottom:1px solid #1f2d47;flex-wrap:wrap}.labs-menu-item:last-child{border:0}.labs-menu-item .lab-info{flex:1;min-width:0;overflow:hidden}.labs-menu-item .lab-ssh{display:flex;align-items:center;gap:8px;margin-top:6px;background:#050912;border:1px solid #1f2d47;border-radius:6px;padding:6px 10px;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:12px;color:#7bf5c3;overflow-x:auto;white-space:nowrap}.labs-menu-item .lab-pass{display:flex;align-items:center;gap:8px;margin-top:4px;background:#050912;border:1px solid #1f2d47;border-radius:6px;padding:6px 10px;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:12px;color:#ffd77a;overflow-x:auto;white-space:nowrap}.labs-menu-item .lab-x{width:32px;height:32px;border-radius:50%;background:#3d131f;color:#ffb3c1;border:1px solid #5e2230;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s;flex-shrink:0}.labs-menu-item .lab-x:hover{background:#5e2230;color:#fff}.copy-class{background:#16223b;color:#aebddd;border:1px solid #2d3e5c;border-radius:6px;padding:4px 8px;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s;width:auto;margin:0;white-space:nowrap}.copy-class:hover{background:#233252;color:#fff}@media(max-width:700px){.sidebar{width:64px;padding:12px 7px}.brand,.nav span,.logout-link span{display:none}.nav a,.logout-link{justify-content:center}.main{padding:20px}.flag-grid{grid-template-columns:1fr}.labs-menu{left:12px;right:12px;width:auto;bottom:80px}}
"""


def layout(content: str, title="CTFploy", sidebar=None, toasts=None) -> str:
    nav = ""
    if sidebar:
        links, active, subtitle = sidebar
        nav = f'<aside class="sidebar" id="sidebar"><div class="sidebar-header"><div class="brand">CTFploy<small>{escape(subtitle)}</small></div><button class="collapse-toggle" type="button" aria-label="Toggle sidebar" onclick="toggleSidebar()">☰</button></div><nav class="nav">' + ''.join(f'<a class="{"active" if key == active else ""}" href="{href}">{icon(key)}<span>{label}</span></a>' for key, href, label in links) + f'</nav><div class="logout"><a class="logout-link" href="{("/admin/logout" if subtitle == "Admin" else "/logout")}">{icon("log-out")}<span>Logout</span></a></div></aside>'
    body = f'<div class="shell">{nav}<main class="main">{content}</main></div>' if sidebar else content
    script = "<script>function toggleSidebar(){const s=document.getElementById('sidebar');s.classList.toggle('collapsed');localStorage.setItem('ctfploy-sidebar',s.classList.contains('collapsed')?'1':'0')}if(localStorage.getItem('ctfploy-sidebar')==='1')document.getElementById('sidebar')?.classList.add('collapsed')</script>" if sidebar else ''
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
    labs_menu_js = """
function toggleLabsMenu(){
    const m=document.getElementById('labs-menu');
    const b=document.getElementById('labs-fab');
    if(!m||!b)return;
    const open=m.classList.contains('open');
    if(open){
        m.classList.remove('open');
        b.innerHTML='__CIRCLE_X__';
    }else{
        m.classList.add('open');
        b.innerHTML='__X__';
        fetch('/api/labs').then(r=>r.json()).then(data=>{
            const el=document.getElementById('labs-list');
            if(!el)return;
            if(!data.labs||!data.labs.length){
                el.innerHTML='<span class=\\'small-text\\'>No active labs.</span>';
                return;
            }
            let html='';
            data.labs.forEach(lab=>{
                const name=decodeURIComponent(lab.display_name);
                html+='<div class=\\'labs-menu-item\\'>'
                    +'<div class=\\'lab-info\\'>'
                    +'<strong style=\\"font-size:13px;\\">'+escape(name)+'</strong>'
                    +'<button class=\\'copy-btn\\' onclick=\\"toggleLabDetails(this)\\" style=\\"margin-top:6px;\\">Show details</button>'
                    +'<div class=\\'lab-details\\' style=\\"display:none; margin-top:6px;\\">'
                    +'<div class=\\'lab-ssh\\'>ssh '+escape(lab.username)+'@'+escape(lab.host)+':'+lab.host_port
                    +'<button class=\\'copy-btn\\' onclick=\\"copyText(this, \\'ssh '+escape(lab.username)+'@'+escape(lab.host)+':'+lab.host_port+'\\')\\">Copy</button></div>'
                    +'<div class=\\'lab-pass\\'>Password: '+escape(lab.password)
                    +'<button class=\\'copy-btn\\' onclick=\\"copyText(this, \\''+escape(lab.password).replace(/'/g, "\\'")+'\\')\\">Copy</button></div>'
                    +'</div>'
                    +'</div>'
                    +'<button class=\\'lab-x\\' onclick=\\"terminateLab(\\''+lab.instance_id+'\\', \\''+escape(name).replace(/'/g, "\\'")+'\\')\\" title=\\"End lab\\">__X_ICON__</button>'
                    +'</div>';
            });
            el.innerHTML=html;
        }).catch(()=>{
            document.getElementById('labs-list').innerHTML='<span class=\\'small-text\\'>Failed to load.</span>';
        });
    }
}
function toggleLabDetails(btn){
    const details=btn.nextElementSibling;
    if(!details)return;
    const isHidden=details.style.display==='none'||details.style.display==='';
    details.style.display=isHidden?'block':'none';
    btn.textContent=isHidden?'Hide details':'Show details';
}
function copyText(btn, text){
    navigator.clipboard.writeText(text).then(()=>{
        const old=btn.textContent;
        btn.textContent='Copied!';
        btn.style.background='#0f382a';
        btn.style.color='#7bf5c3';
        setTimeout(()=>{
            btn.textContent=old;
            btn.style.background='#16223b';
            btn.style.color='#aebddd';
        },1500);
    }).catch(()=>{});
}
function terminateLab(id, name){
    if(confirm('End '+name+'?')){
        const f=document.createElement('form');
        f.method='POST';
        f.action='/terminate/'+id;
        document.body.appendChild(f);
        f.submit();
    }
}
"""
    labs_menu_js = labs_menu_js.replace("__CIRCLE_X__", icon("circle-x")).replace("__X__", icon("x")).replace("__X_ICON__", icon("x"))
    labs_fab = '<button class="labs-fab" id="labs-fab" onclick="toggleLabsMenu()" title="Active Labs">' + icon("circle-x") + '</button><div class="labs-menu" id="labs-menu"><div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px;"><strong style="font-size:14px;">Active Labs</strong><button class="modal-close" onclick="toggleLabsMenu()">' + icon("circle-x") + '</button></div><div id="labs-list"><span class="small-text">Loading...</span></div></div><script>' + labs_menu_js + '</script>' if sidebar else ''
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet"><title>{escape(title)}</title><style>{STYLE}</style></head><body>{toast_container}{body}{script}{toast_script}{labs_fab}</body></html>'


def centered_layout(content: str, title="CTFploy", toasts=None) -> str:
    return layout(content, title, toasts=toasts)


def admin_layout(content, active="home", toasts=None):
    return layout(content, "CTFploy Admin", ([('home','/admin','Overview'),('classes','/admin/classes','Classes'),('boxes','/admin/challenges','Challenges'),('leaderboard','/admin/leaderboard','Leaderboard'),('users','/admin/users','Users'),('settings','/admin/settings','Settings')], active, 'Admin'), toasts=toasts)


def user_layout(content, active="home", toasts=None):
    return layout(content, "CTFploy", ([('home','/dashboard','Dashboard'),('users','/classes','My classes'),('terminal','/leaderboard','Leaderboard'),('key','/change-password','Password')], active, 'Student'), toasts=toasts)
