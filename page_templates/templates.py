from html import escape
from typing import Optional

from page_templates.layout import admin_layout, icon


def _toasts(toasts):
    return ''.join(f'<div class="flash {kind}">{escape(message)}</div>' for kind, message in (toasts or []))


def admin_challenges_page(challenges, toasts=None):
    rows = ''
    for ch in challenges:
        status = ch.get('build_status', 'failed')
        label = {'ready': 'ready', 'building': 'building', 'failed': 'failed'}.get(status, 'failed')
        rows += f'''<li><div class="row"><div><strong>{escape(ch['display_name'])}</strong><div class="small-text">{escape(ch.get('description', ''))}</div><span class="status-badge status-{status}">{label}</span></div><div><a href="/admin/build_log/{ch['id']}" class="small-text">Build logs</a> · <a href="/admin/delete_challenge/{ch['id']}" class="small-text" style="color:#ffb3c1;font-weight:600;">Delete</a></div></div></li>'''
    return admin_layout(f'''<div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:18px;"><h1 style="margin:0;">Challenges</h1><button class="secondary" onclick="document.getElementById('import-modal').style.display='flex'" style="display:inline-flex; align-items:center; gap:6px; font-family:inherit;">{icon("plus")} Import</button></div><div id="import-modal" class="modal" onclick="if(event.target===this)this.style.display='none'"><div class="modal-content" style="width:90%; max-width:480px;"><div style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:16px;"><h3 style="margin:0;">Import Challenge</h3><button class="modal-close" onclick="document.getElementById('import-modal').style.display='none'">{icon("circle-x")}</button></div><form action="/admin/import-url" method="post"><input name="url" placeholder="https://example.com/challenge.tar.gz" required style="margin-bottom:12px; font-family:inherit;"><button type="submit" style="font-family:inherit;">Fetch & build</button></form></div></div><section class="card"><h2>All challenges</h2><ul class="list">{rows or '<li>No challenges imported yet.</li>'}</ul></section>''', active='boxes', toasts=toasts)


def admin_dashboard_page(challenges, instances, toasts=None):
    active = sum(instance['status'] == 'running' for instance in instances)
    ready = sum(challenge.get('build_status') == 'ready' for challenge in challenges)
    return admin_layout(f'''<h1>Platform overview</h1><p class="muted">Manage training classes, challenge images, and active labs.</p><div class="grid"><div class="card"><div class="small-text">Ready challenges</div><div class="stat">{ready}</div></div><div class="card"><div class="small-text">Active instances</div><div class="stat">{active}</div></div><div class="card"><div class="small-text">Imported challenges</div><div class="stat">{len(challenges)}</div></div></div>''', active='home', toasts=toasts)


def admin_classes_page(classes, challenges, users, toasts=None):
    rows = ''
    for classroom in classes:
        members = len(classroom.get('member_ids', []))
        assignments = len(classroom.get('challenge_ids', []))
        rows += f'''<li><div class="row"><div><strong>{escape(classroom['name'])}</strong><div class="small-text">{members} student(s) · {assignments} assignment(s) · Join code: <code>{escape(classroom['join_code'])}</code></div></div><div style="display:flex; gap:8px;"><a href="/admin/classes/{classroom['id']}"><button class="secondary">Open</button></a><form method="post" action="/admin/classes/delete/{classroom['id']}" onsubmit="return confirm('Delete this class?')"><button class="secondary" style="color:#ffb3c1; border-color:#5e2230; font-family:inherit;">Delete</button></form></div></div></li>'''
    return admin_layout(f'''<div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:18px;"><h1 style="margin:0;">Classes</h1><div style="display:flex; gap:8px;"><button class="secondary" onclick="document.getElementById('create-modal').style.display='flex'" style="display:inline-flex; align-items:center; gap:6px; font-family:inherit;">{icon("plus")} New Class</button><button class="secondary" onclick="document.getElementById('join-modal').style.display='flex'" style="display:inline-flex; align-items:center; gap:6px; font-family:inherit;">{icon("plus")} Join Class</button></div></div><p class="muted">Create a class, share its join code, then open it to assign challenges. Or join an existing class.</p><section class="card"><ul class="list">{rows or '<li>No classes yet.</li>'}</ul></section><div id="create-modal" class="modal" onclick="if(event.target===this)this.style.display='none'"><div class="modal-content" style="width:90%; max-width:480px;"><div style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:16px;"><h3 style="margin:0;">Create Class</h3><button class="modal-close" onclick="document.getElementById('create-modal').style.display='none'">{icon("circle-x")}</button></div><form method="post" action="/admin/classes/create"><input name="name" placeholder="Linux Foundations — Group A" required style="margin-bottom:12px; font-family:inherit;"><button type="submit" style="font-family:inherit;">Create class</button></form></div></div><div id="join-modal" class="modal" onclick="if(event.target===this)this.style.display='none'"><div class="modal-content" style="width:90%; max-width:480px;"><div style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:16px;"><h3 style="margin:0;">Join Class</h3><button class="modal-close" onclick="document.getElementById('join-modal').style.display='none'">{icon("circle-x")}</button></div><form method="post" action="/admin/join-class"><input name="code" placeholder="CLASS-ABC123" required style="margin-bottom:12px; font-family:inherit;"><button type="submit" style="font-family:inherit;">Join class</button></form></div></div>''', active='classes', toasts=toasts)


def admin_class_detail_page(classroom, challenges, users, toasts=None):
    assigned = [challenge for challenge in challenges if challenge['id'] in classroom.get('challenge_ids', [])]
    available = [challenge for challenge in challenges if challenge['id'] not in classroom.get('challenge_ids', []) and challenge.get('build_status') == 'ready']
    assigned_html = ''.join(f"<li><div class=\"row\" style=\"align-items:center;\"><div><strong>{escape(challenge['display_name'])}</strong></div><form method=\"post\" action=\"/admin/classes/remove_challenge\" onsubmit=\"return confirm('Remove this challenge?')\" style=\"display:inline;\"><input type=\"hidden\" name=\"class_id\" value=\"{classroom['id']}\"><input type=\"hidden\" name=\"challenge_id\" value=\"{challenge['id']}\"><button class=\"secondary\" style=\"color:#ffb3c1; border-color:#5e2230; padding:4px 10px; font-size:11px; font-family:inherit;\">Remove</button></form></div></li>" for challenge in assigned) or '<li>No challenges assigned.</li>'
    options = ''.join(f'<option value="{challenge["id"]}">{escape(challenge["display_name"])}</option>' for challenge in available) or '<option value="">No ready challenges available</option>'
    members = ''.join("<li><div class=\"row\" style=\"align-items:center;\"><div><strong>" + escape(user["username"]) + "</strong><div class=\"small-text\">ID: " + escape(user["id"]) + "</div></div><form method=\"post\" action=\"/admin/classes/remove-student\" onsubmit=\"return confirm('Remove " + escape(user["username"]) + " from this class?')\" style=\"display:inline;\"><input type=\"hidden\" name=\"class_id\" value=\"" + classroom['id'] + "\"><input type=\"hidden\" name=\"user_id\" value=\"" + user['id'] + "\"><button class=\"secondary\" style=\"color:#ffb3c1; border-color:#5e2230; padding:4px 10px; font-size:11px; font-family:inherit;\">Remove</button></form></div></li>" for user in users if user['id'] in classroom.get('member_ids', [])) or '<li>No students yet.</li>'
    return admin_layout(f'''<a href="/admin/classes" class="small-text">{icon("arrow-left")} All classes</a><h1 onclick="navigator.clipboard.writeText({escape(classroom['name'])!r}).then(()=>showToast('Class name copied','success'))" style=\"cursor:pointer;\" title=\"Click to copy class name\">{escape(classroom['name'])} {icon("copy")}</h1><p class=\"muted\">Join code: <code>{escape(classroom['join_code'])}</code></p><div class=\"grid\"><section class=\"card\"><h3>Assign a challenge</h3><form method=\"post\" action=\"/admin/classes/assign\"><input type=\"hidden\" name=\"class_id\" value=\"{classroom['id']}\"><select name=\"challenge_id\">{options}</select><button style=\"width: 100%; margin-top: 10px; font-family:inherit;\">Assign challenge</button></form><h3>Assigned challenges</h3><ul class=\"list\">{assigned_html}</ul></section><section class=\"card\"><h3>Students</h3><ul class=\"list\">{members}</ul></section></div><form method=\"post\" action=\"/admin/classes/delete/{classroom['id']}\" onsubmit=\"return confirm('Delete this class? This cannot be undone.')\" style=\"margin-top:12px;\"><button class=\"secondary\" style=\"color:#ffb3c1; border-color:#5e2230; font-family:inherit;\">Delete class</button></form>''', active='classes', toasts=toasts)


def admin_update_page(toasts=None):
    return admin_layout(f'''<section class="card"><h2>Update platform</h2><p>Pull the latest image and restart the platform container.</p><form method="post"><button style="font-family:inherit;">Update now</button></form></section>''', active='settings', toasts=toasts)


def admin_domain_page(domain, public_ip, toasts=None):
    domain = escape(domain or "")
    return admin_layout(f'''<section class="card"><h2>Custom domain</h2><p class="muted">Use your domain for the platform and SSH commands (with each lab's displayed port).</p><form method="post" action="/admin/domain"><label>Domain</label><input name="domain" placeholder="ctf.example.com" value="{domain}" required style="font-family:inherit;"><button style="font-family:inherit;">Save domain and prepare DNS validation</button></form></section><section class="card" style="margin-top:18px;"><h3>DNS record to create</h3><p class="small-text">At your DNS provider, create this record, wait for propagation, then issue the certificate below.</p><div class="command">Type: A\nHost/Name: {domain or 'ctf'}\nValue: {escape(public_ip)}\nTTL: Auto</div></section><section class="card" style="margin-top:18px;"><h3>Issue Let's Encrypt certificate</h3><form method="post" action="/admin/domain/certificate"><input type="hidden" name="domain" value="{domain}"><label>Certificate email</label><input name="email" type="email" required style="font-family:inherit;"><button style="font-family:inherit;">Verify DNS and enable HTTPS</button></form></section>''', active='settings', toasts=toasts)


def admin_settings_page(domain, public_ip, toasts=None):
    domain = escape(domain or "")
    return admin_layout(f'''<h1>Settings</h1><p class="muted">Manage platform domain and updates.</p><section class="card"><h2>Custom domain</h2><p class="muted">Use your domain for the platform and SSH commands (with each lab's displayed port).</p><form method="post" action="/admin/domain"><label>Domain</label><input name="domain" placeholder="ctf.example.com" value="{domain}" required style="font-family:inherit;"><button style="font-family:inherit;">Save domain and prepare DNS validation</button></form><h3 style="margin-top:18px;">DNS record to create</h3><p class="small-text">At your DNS provider, create this record, wait for propagation, then issue the certificate below.</p><div class="command">Type: A\nHost/Name: {domain or 'ctf'}\nValue: {escape(public_ip)}\nTTL: Auto</div><h3 style="margin-top:18px;">Issue Let's Encrypt certificate</h3><form method="post" action="/admin/domain/certificate"><input type="hidden" name="domain" value="{domain}"><label>Certificate email</label><input name="email" type="email" required style="font-family:inherit;"><button style="font-family:inherit;">Verify DNS and enable HTTPS</button></form></section><section class="card" style="margin-top:18px; border:2px dashed #203154; background:#0b101e;"><h2>Update platform</h2><p>Pull the latest image and restart the platform container.</p><form method="post"><button style="font-family:inherit;">Update now</button></form></section>''', active='settings', toasts=toasts)


def admin_users_page(users, toasts=None):
    rows = ''
    for user in users:
        rows += f'''<li><div class="row"><div><strong>{escape(user['username'])}</strong><div class="small-text">ID: {escape(user['id'])}</div></div><form method="post" action="/admin/users/reset-password" onsubmit="return confirm('Reset password for {escape(user['username'])}?')" style="display:inline;"><input type="hidden" name="user_id" value="{user['id']}"><button class="secondary" style="color:#ffb3c1; border-color:#5e2230; font-family:inherit;">Reset Password</button></form></div></li>'''
    return admin_layout(f'''<h1>Users</h1><p class="muted">Manage platform users and reset passwords.</p><section class="card"><ul class="list">{rows or '<li>No users yet.</li>'}</ul></section>''', active='users', toasts=toasts)


def build_log_page(challenge_id: str, class_id: Optional[str] = None):
    back_url = f"/admin/classes/{class_id}" if class_id else "/admin/challenges"
    back_label = "Back to Class" if class_id else "Back to Challenges"
    return admin_layout(f'''<section class="card"><div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:12px;"><div style="display:flex; align-items:center; gap:8px;"><a href="{back_url}" style="display:inline-flex; align-items:center; color:#8da2ce; text-decoration:none;">{icon("arrow-left")}</a><h2 style="margin:0;">Build log</h2></div></div><div id="log" class="log-window"></div></section><script>const source=new EventSource('/admin/build_log_stream/{challenge_id}');const output=document.getElementById('log');source.onmessage=e=>{{output.textContent+=JSON.parse(e.data)+'\\n';output.scrollTop=output.scrollHeight}};source.addEventListener('complete',()=>source.close());source.onerror=()=>source.close();</script>''', active='boxes')


def admin_leaderboard_page(grouped_entries, toasts=None) -> str:
    sections = ''
    for class_id, entries in grouped_entries.items():
        class_name = escape(entries[0].get('class_name', class_id)) if entries else escape(str(class_id))
        rows = ''.join(
            f'''<li><div class="row"><strong>#{index} {escape(entry.get("username", "Unknown"))}</strong><div style="text-align:right;"><strong style="color:#ffd77a;">{entry.get("points", 0)} points</strong><div class="small-text">{entry.get("solved", 0)} challenge(s) solved</div></div></div></li>'''
            for index, entry in enumerate(entries, start=1)
        ) or '<li>No scores yet.</li>'
        sections += f'''
        <section class="card" style="margin-bottom:18px;">
            <h3 style="margin:0;">{class_name}</h3>
            <ul class="list">{rows}</ul>
        </section>
        '''

    if not sections:
        sections = '<section class="card"><p class="muted">No leaderboard data yet. Join a class and start solving challenges.</p></section>'

    return admin_layout(f'''
    <h1>Leaderboard</h1>
    <p class="muted">Rankings by class. Sorted by points, then challenges solved.</p>
    {sections}
    ''', active='leaderboard', toasts=toasts)
