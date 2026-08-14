from html import escape
from typing import Optional

from page_templates.layout import admin_layout


def _flashes(flashes):
    return ''.join(f'<div class="flash {kind}">{escape(message)}</div>' for kind, message in (flashes or []))


def admin_challenges_page(challenges, flashes=None):
    rows = ''
    for ch in challenges:
        status = ch.get('build_status', 'failed')
        label = {'ready': 'ready', 'building': 'building', 'failed': 'failed'}.get(status, 'failed')
        rows += f'''<li><div class="row"><div><strong>{escape(ch['display_name'])}</strong><div class="small-text">{escape(ch.get('description', ''))}</div><span class="status-badge status-{status}">{label}</span></div><div><a href="/admin/build_log/{ch['id']}" class="small-text">Build logs</a> · <a href="/admin/delete_challenge/{ch['id']}" class="small-text">Delete</a></div></div></li>'''
    return admin_layout(f'''{_flashes(flashes)}<h1>Challenges</h1><section class="card"><h3>Import from URL</h3><form action="/admin/import-url" method="post"><input name="url" placeholder="https://example.com/challenge.tar.gz" required><button>Fetch & build</button></form><p class="small-text">A package needs a Dockerfile and ctfploy.json. Docker connection details are detected from EXPOSE.</p></section><section class="card"><h2>All challenges</h2><ul class="list">{rows or '<li>No challenges imported yet.</li>'}</ul></section>''', active='boxes')


def admin_dashboard_page(challenges, instances, flashes=None):
    active = sum(instance['status'] == 'running' for instance in instances)
    ready = sum(challenge.get('build_status') == 'ready' for challenge in challenges)
    return admin_layout(f'''{_flashes(flashes)}<h1>Platform overview</h1><p class="muted">Manage training classes, challenge images, and active labs.</p><div class="grid"><div class="card"><div class="small-text">Ready challenges</div><div class="stat">{ready}</div></div><div class="card"><div class="small-text">Active instances</div><div class="stat">{active}</div></div><div class="card"><div class="small-text">Imported challenges</div><div class="stat">{len(challenges)}</div></div></div>''', active='home')


def admin_classes_page(classes, challenges, users, flashes=None):
    rows = ''
    for classroom in classes:
        members = len(classroom.get('member_ids', []))
        assignments = len(classroom.get('challenge_ids', []))
        rows += f'''<li><div class="row"><div><strong>{escape(classroom['name'])}</strong><div class="small-text">{members} student(s) · {assignments} assignment(s) · Join code: <code>{escape(classroom['join_code'])}</code></div></div><a href="/admin/classes/{classroom['id']}"><button>Open class</button></a></div></li>'''
    return admin_layout(f'''{_flashes(flashes)}<h1>Classes</h1><p class="muted">Create a class, share its join code, then open it to assign challenges.</p><section class="card"><h3>Create a class</h3><form method="post" action="/admin/classes/create" class="row"><input name="name" placeholder="Linux Foundations — Group A" required><button>Create class</button></form></section><section class="card"><h2>All classes</h2><ul class="list">{rows or '<li>No classes yet.</li>'}</ul></section>''', active='users')


def admin_class_detail_page(classroom, challenges, users, flashes=None):
    assigned = [challenge for challenge in challenges if challenge['id'] in classroom.get('challenge_ids', [])]
    available = [challenge for challenge in challenges if challenge['id'] not in classroom.get('challenge_ids', []) and challenge.get('build_status') == 'ready']
    assigned_html = ''.join(f'<li><strong>{escape(challenge["display_name"])}</strong><span class="status-badge status-ready">Ready</span></li>' for challenge in assigned) or '<li>No challenges assigned.</li>'
    options = ''.join(f'<option value="{challenge["id"]}">{escape(challenge["display_name"])}</option>' for challenge in available) or '<option value="">No ready challenges available</option>'
    members = ''.join(f'<li>{escape(user["username"])}</li>' for user in users if user['id'] in classroom.get('member_ids', [])) or '<li>No students yet.</li>'
    return admin_layout(f'''{_flashes(flashes)}<a href="/admin/classes" class="small-text">← All classes</a><h1>{escape(classroom['name'])}</h1><p class="muted">Join code: <code>{escape(classroom['join_code'])}</code></p><div class="grid"><section class="card"><h3>Assign a challenge</h3><form method="post" action="/admin/classes/assign"><input type="hidden" name="class_id" value="{classroom['id']}"><select name="challenge_id">{options}</select><button style="width: 100%; margin-top: 10px;">Assign challenge</button></form><h3>Assigned challenges</h3><ul class="list">{assigned_html}</ul></section><section class="card"><h3>Import & Build Challenge</h3><form action="/admin/import-url" method="post"><input type="hidden" name="class_id" value="{classroom['id']}"><input name="url" placeholder="https://example.com/challenge.tar.gz" required><button style="width: 100%; margin-top: 10px;">Fetch, build & assign</button></form><p class="small-text" style="margin-top: 8px;">It will be built in the background and auto-assigned to this class once ready.</p></section><section class="card"><h3>Students</h3><ul class="list">{members}</ul></section></div><form method="post" action="/admin/classes/delete/{classroom['id']}"><button class="secondary">Delete class</button></form>''', active='users')


def admin_update_page(flashes=None):
    return admin_layout(f'''{_flashes(flashes)}<section class="card"><h2>Update platform</h2><p>Pull the latest image and restart the platform container.</p><form method="post"><button>Update now</button></form></section>''', active='settings')


def build_log_page(challenge_id: str, class_id: Optional[str] = None):
    back_url = f"/admin/classes/{class_id}" if class_id else "/admin/challenges"
    back_label = "Back to Class" if class_id else "Back to Challenges"
    return admin_layout(f'''<section class="card"><h2>Build log</h2><div id="log" class="log-window"></div><a href="{back_url}"><button class="secondary">{back_label}</button></a></section><script>const source=new EventSource('/admin/build_log_stream/{challenge_id}');const output=document.getElementById('log');source.onmessage=e=>{{output.textContent+=JSON.parse(e.data)+'\\n';output.scrollTop=output.scrollHeight}};source.addEventListener('complete',()=>source.close());source.onerror=()=>source.close();</script>''', active='boxes')
