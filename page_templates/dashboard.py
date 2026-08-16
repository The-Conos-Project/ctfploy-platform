from html import escape

from page_templates.layout import user_layout, icon
from challenge_meta import total_points


def dashboard_page(user, user_classes, active_instances, toasts=None) -> str:
    active_labs_html = ''
    if active_instances:
        labs_list = ''
        for item in active_instances:
            inst = item["instance"]
            ch = item["challenge"]
            labs_list += f'''
            <li>
                <div class="row">
                    <div>
                        <strong>{escape(ch["display_name"])}</strong>
                        <div class="small-text">Instance {escape(inst["id"])} · Expires {escape(inst["expires_at"].split("T")[0])}</div>
                    </div>
                    <a href="/instance/{inst["id"]}"><button>Go to Lab</button></a>
                </div>
            </li>
            '''
        active_labs_html = f'''
        <section class="card">
            <h3>Active Labs</h3>
            <ul class="list">{labs_list}</ul>
        </section>
        '''

    leaderboard_html = ''
    if user_classes:
        cards = []
        for classroom in user_classes:
            class_id = classroom['id']
            class_name = escape(classroom['name'])
            cards.append(f'''
            <div class="card" style="margin-bottom:18px;">
                <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;">
                    <h3 style="margin:0;">{class_name}</h3>
                    <a href="/leaderboard?class_id={class_id}" class="small-text">View leaderboard {icon("arrow-right")}</a>
                </div>
            </div>
            ''')
        leaderboard_html = '<h1>Leaderboard</h1><p class="muted" style="margin-bottom: 18px;">Your rankings across joined classes.</p>' + ''.join(cards)

    return user_layout(f'''
    <h1>Welcome back, {escape(user['username'])}</h1>
    <p class="muted" style="margin-bottom: 24px;">Track your training labs and rankings.</p>
    {active_labs_html}
    {leaderboard_html}
    ''', active='home', toasts=toasts)


def classes_page(classes, toasts=None) -> str:
    items = ''.join(
        f'''<div style="width:50%; padding:0 6px 12px 0; box-sizing:border-box;"><div class="card" style="margin-bottom:0; height:100%;"><div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;"><div><strong>{escape(classroom['name'])}</strong><div class="small-text">{len(classroom['challenge_ids'])} assigned challenge(s)</div></div><a href="/classes/{classroom['id']}"><button class="secondary">Open class</button></a></div></div></div>'''
        for classroom in classes
    ) or '<div style="width:100%;">No classes joined yet.</div>'
    return user_layout(f'''<div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:18px;"><h1 style="margin:0;">My classes</h1><button class="secondary" onclick="document.getElementById('join-modal').style.display='flex'" style="display:inline-flex; align-items:center; gap:6px; font-family:inherit;">{icon("plus")} Join Class</button></div><p class="muted" style="margin-bottom:18px;">Open a class to view only its assigned challenges.</p><div id="join-modal" class="modal" onclick="if(event.target===this)this.style.display='none'"><div class="modal-content" style="width:90%; max-width:480px;"><div style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:16px;"><h3 style="margin:0;">Join Class</h3><button class="modal-close" onclick="document.getElementById('join-modal').style.display='none'">{icon("circle-x")}</button></div><form method="post" action="/user/join-class"><input name="code" placeholder="CLASS-ABC123" required style="margin-bottom:12px; font-family:inherit;"><button type="submit" style="font-family:inherit;">Join class</button></form></div></div><div style="display:flex; flex-wrap:wrap; margin:0 -6px;">{items}</div>''', active='users', toasts=toasts)


def class_detail_page(classroom, challenges, instances, toasts=None) -> str:
    instance_by_challenge = {instance['challenge_id']: instance for instance in instances}
    rows = ''
    for challenge in challenges:
        status = challenge.get('build_status', 'failed')
        label = {'ready': 'ready', 'building': 'building', 'failed': 'failed'}.get(status, 'failed')
        instance = instance_by_challenge.get(challenge['id'])
        if instance:
            badge = '<span class="status-badge status-building">active lab</span>'
            action = f'<a href="/instance/{instance["id"]}"><button class="secondary">Go to Lab</button></a>'
        elif status == 'ready':
            badge = '<span class="status-badge status-ready">ready</span>'
            action = f'<a href="/challenges/{challenge["id"]}"><button class="secondary">Open challenge</button></a>'
        elif status == 'building':
            badge = '<span class="status-badge status-building">building</span>'
            action = f'<a href="/challenges/{challenge["id"]}"><button class="secondary">Open challenge</button></a>'
        else:
            badge = '<span class="status-badge status-failed">failed</span>'
            action = f'<a href="/challenges/{challenge["id"]}"><button class="secondary">Open challenge</button></a>'
        rows += f'''<li><div class="row"><div><strong>{escape(challenge['display_name'])}</strong><div class="small-text">{escape(challenge.get('description', ''))}</div><div class="small-text" style="color:#ffd77a; font-weight:600;">{total_points(challenge)} points</div>{badge}</div>{action}</div></li>'''
    return user_layout(f'''<a href="/classes" class="small-text">{icon("arrow-left")} All classes</a><h1>{escape(classroom['name'])}</h1><section class="card"><h3>Assigned challenges</h3><ul class="list">{rows or '<li>No challenges have been assigned yet.</li>'}</ul></section>''', active='users', toasts=toasts)


def student_challenges_page(challenges, instances, solved_challenge_ids, toasts=None) -> str:
    rows = ''
    instance_by_challenge = {instance['challenge_id']: instance for instance in instances}
    for challenge in challenges:
        instance = instance_by_challenge.get(challenge['id'])
        status = challenge.get('build_status', 'failed')

        badge_html = ''
        if challenge['id'] in solved_challenge_ids:
            badge_html = '<span class="status-badge status-success">solved</span>'
        elif instance:
            badge_html = '<span class="status-badge status-building">active lab</span>'
        else:
            badge_html = f'<span class="status-badge status-{status}">{status}</span>'

        action = f'<a href="/challenges/{challenge["id"]}"><button class="secondary">Open challenge</button></a>'
        rows += f'''<li><div class="row"><div><strong>{escape(challenge['display_name'])}</strong><div class="small-text">{escape(challenge.get('description', ''))}</div><div class="small-text" style="color:#ffd77a; font-weight:600;">{total_points(challenge)} points</div>{badge_html}</div>{action}</div></li>'''

    return user_layout(f'''
    <h1>All Assigned Challenges</h1>
    <p class="muted">Access and solve challenges assigned to you across all joined classes.</p>
    <section class="card">
        <ul class="list">{rows or '<li>No challenges have been assigned yet. Join a classroom first!</li>'}</ul>
    </section>
    ''', active='users', toasts=toasts)


def student_challenge_detail_page(challenge, inst, host, msg, attempts_remaining=None, expires_at=None) -> str:
    def format_hint(hint: str) -> str:
        stripped = hint.strip()
        command_prefixes = ('$', 'ssh ', 'curl ', 'nc ', 'cat ', 'ls ', 'find ', 'grep ', 'tar ', 'sudo ', 'chmod ', 'ps ', 'netstat ', 'ss ', 'echo ', 'export ', 'python', 'pip', 'nano ', 'vim ', 'vi ', 'touch ', 'mkdir ', 'cd ', 'pwd', 'whoami', 'id', 'file ', 'head ', 'tail ', 'less ', 'more ', 'wc ', 'sort ', 'uniq ', 'awk ', 'sed ', 'cut ', 'tr ', 'xargs ', 'jq ')
        if any(stripped.startswith(p) for p in command_prefixes):
            cmd = stripped.lstrip('$ ').strip()
            return f'<div class="terminal-snippet"><span class="terminal-prompt">$</span><span class="terminal-cmd">{escape(cmd)}</span></div>'
        return escape(hint)

    flags = challenge.get("flags", [])
    attempts_remaining = attempts_remaining or {}
    challenge_cards = []
    for idx, spec in enumerate(flags):
        flag_name = spec.get("flag", "")
        submitted = flag_name in inst.get("submitted_flags", []) if inst else False
        challenge_cards.append({
            "index": idx,
            "spec": spec,
            "submitted": submitted,
        })

    cards_html = ""
    for card in challenge_cards:
        idx = card["index"]
        spec = card["spec"]
        description = escape(spec.get("description", ""))
        points = spec.get("points", 100)
        submitted = card["submitted"]

        if submitted:
            card_class = "flag-card solved"
            status_class = "status-success"
            status_text = "completed"
            badge_extra = 'style="background:#0f382a; color:#7bf5c3; border-color:#164e3c;"'
        else:
            card_class = "flag-card"
            status_class = "status-ready"
            status_text = "ready"
            badge_extra = 'style="background:#1b263e; color:#aebddd; border-color:#2d3e5c;"'

        cards_html += f'''
        <div class="{card_class}" onclick="openModal({idx})" style="cursor:pointer; position:relative;">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;">
                <div>
                    <strong style="font-size:15px;">Challenge {idx + 1}</strong>
                    <div class="small-text" style="margin-top:4px;">{description}</div>
                    <div class="small-text" style="margin-top:4px;"><span style="color:#ffd77a; font-weight:600;">{points} points</span></div>
                </div>
                <span class="badge-external {status_class}" {badge_extra}>{status_text}</span>
            </div>
        </div>
        '''

    flags_section = f'''
    <section class="card" style="margin-top:18px;">
        <h3>Challenge Collection</h3>
        <div class="flag-grid" style="margin-top:10px;">{cards_html}</div>
    </section>
    '''

    modals_html = ""
    for card in challenge_cards:
        idx = card["index"]
        spec = card["spec"]
        description = escape(spec.get("description", ""))
        hints = spec.get("hints", [])
        hints_list = "".join(f"<li style='margin-top:6px;'>{format_hint(h)}</li>" for h in hints)
        hints_block = f"<ul style='margin-left:18px; font-size:13px; color:#8da2ce; list-style:square;'>{hints_list}</ul>" if hints_list else ""
        points = spec.get("points", 100)
        remaining = attempts_remaining.get(idx, spec.get("max_attempts", 3))
        submitted = card["submitted"]

        if inst:
            connection = f'''
            <button class="secondary" onclick="toggleModalDetails({idx}, this)" style="margin-top:16px; font-family:inherit; width:auto; display:inline-flex; align-items:center; gap:6px;">Show connection details</button>
            <div id="modal-details-{idx}" style="display:none; margin-top:12px;">
                <p class="small-text" style="margin-bottom:8px;">Connect to your lab environment via SSH:</p>
                <div class="terminal-snippet">
                    <span class="terminal-prompt">$</span>
                    <span class="terminal-cmd" id="modal-ssh-cmd-{idx}">ssh {escape(inst["username"])}@{escape(host)} -p {inst["host_port"]}</span>
                    <button class="copy-btn" onclick="copyText('modal-ssh-cmd-{idx}', this)">Copy</button>
                </div>
                <p class="small-text" style="margin-top:10px; margin-bottom:4px;">Password:</p>
                <div class="terminal-snippet">
                    <span class="terminal-cmd" id="modal-ssh-passwd-{idx}" style="user-select:all; color:#ffd77a;">{escape(inst["password"])}</span>
                    <button class="copy-btn" onclick="copyText('modal-ssh-passwd-{idx}', this)">Copy</button>
                </div>
            </div>
            '''
            if submitted:
                action_area = f'''
                <div class="card" style="border:1px solid #164e3c; background:#0e3025; margin-top:16px;">
                    <h4 style="margin:0; color:#8efcd4;">Challenge completed</h4>
                </div>
                <form method="post" action="/terminate/{inst['id']}" onsubmit="return confirm('End this lab?')" style="margin-top:12px;">
                    <button type="submit" class="secondary" style="color:#ffb3c1; border-color:#5e2230; font-family:inherit; width:auto; padding:6px 12px; font-size:12px;">{icon("x")} End</button>
                </form>
                '''
            elif remaining > 0:
                action_area = f'''
                <form method="post" action="/submit_flag/{inst['id']}" style="display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin-top:16px;">
                    <input type="hidden" name="flag_index" value="{idx}">
                    <input name="flag" placeholder="CN{{...}}" required style="flex:1; min-width:240px; margin:0; font-family:inherit;">
                    <button type="submit" style="font-family:inherit;">Submit Flag</button>
                </form>
                <form method="post" action="/terminate/{inst['id']}" onsubmit="return confirm('End this lab?')" style="margin-top:10px;">
                    <button type="submit" class="secondary" style="color:#ffb3c1; border-color:#5e2230; font-size:12px; padding:6px 12px; font-family:inherit; width:auto;">{icon("x")} End</button>
                </form>
                '''
            else:
                action_area = '<div class="card" style="border:1px solid #5e2230; background:#3d131f; margin-top:16px;"><h4 style="margin:0; color:#ffb3c1;">No attempts remaining</h4></div>'
        else:
            connection = ""
            action_area = f'''
            <a href="/start/{challenge['id']}"><button style="margin-top:16px; font-family:inherit;">Start Container</button></a>
            '''

        modals_html += f'''
        <div id="modal-{idx}" class="modal" onclick="if(event.target===this)closeModal({idx})">
            <div class="modal-content" style="width:90%; max-width:640px; max-height:90vh; overflow-y:auto;">
                <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:12px;">
                    <div>
                        <strong style="font-size:18px;">Challenge {idx + 1}</strong>
                        <span class="badge-external {status_class}" style="position:static; margin-left:8px;" {badge_extra}>{status_text}</span>
                    </div>
                    <button class="modal-close" onclick="closeModal({idx})">{icon("circle-x")}</button>
                </div>
                <p style="color:#aebddd; margin-bottom:12px;">{description}</p>
                <div style="margin-bottom:16px;">
                    <h4 style="margin-bottom:8px; font-weight:600;">Hints</h4>
                    {hints_block}
                </div>
                <div class="small-text" style="margin-bottom:16px; color:#ffd77a; font-weight:600;">{points} points · {remaining}/{spec.get("max_attempts", 3)} attempts remaining</div>
                {f'<div style="margin-bottom:16px;"><h4 style="margin-bottom:8px; font-weight:600;">Connection Details</h4>{connection}</div>' if connection else ''}
                {action_area}
            </div>
        </div>
        '''

    status = challenge.get('build_status', 'failed')
    action_card_html = ''
    if status != 'ready':
        if status == 'building':
            action_card_html = '<div class="card" style="text-align: center; padding: 32px 24px;"><span class="status-badge status-building" style="margin-bottom: 12px;">Building Challenge</span><p class="muted small-text">The instructor recently uploaded this challenge and it is currently compiling. Please wait...</p></div>'
        else:
            action_card_html = '<div class="card" style="text-align: center; padding: 32px 24px; border: 1px solid #3d131f;"><span class="status-badge status-failed" style="margin-bottom: 12px;">Build Failed</span><p class="muted small-text">This challenge could not build correctly. Please contact your administrator.</p></div>'

    toasts_list = []
    if msg:
        toasts_list.append(("success" if msg.startswith("Accepted!") else "error", msg))

    countdown_html = ""
    if expires_at:
        instance_id = inst.get("id", "") if inst else ""
        extend_form = ""
        if instance_id:
            extend_form = f'<form method="post" action="/extend/{instance_id}" style="display:inline;" onsubmit="return confirm(\'Extend this lab by 1 hour?\')"><button type="submit" class="secondary" style="font-size:11px; padding:5px 10px; font-family:inherit;">+1h</button></form>'
        countdown_html = f'''
        <div class="card" style="margin-bottom:18px; border:1px solid #203154; background:#11192e;">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;">
                <div>
                    <strong style="font-size:14px;">Lab Timer</strong>
                    <div class="small-text" style="margin-top:4px;">Auto-terminates when timer reaches zero</div>
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <span id="lab-countdown" style="font-size:20px; font-weight:800; color:#ffd77a; font-variant-numeric:tabular-nums;">--:--</span>
                    {extend_form}
                </div>
            </div>
        </div>
        <script>
        (function() {{
            const target = {expires_at};
            const el = document.getElementById('lab-countdown');
            const warned = new Set();
            function tick() {{
                const now = Date.now();
                let diff = Math.max(0, Math.floor((target - now) / 1000));
                const m = String(Math.floor(diff / 60)).padStart(2, '0');
                const s = String(diff % 60).padStart(2, '0');
                if (el) el.textContent = m + ':' + s;
                if (diff <= 0 && el) {{
                    el.textContent = '00:00';
                    el.style.color = '#ffb3c1';
                }}
                const mins = Math.ceil(diff / 60);
                if ([1, 5, 10].includes(mins) && !warned.has(mins)) {{
                    warned.add(mins);
                    showToast(mins + ' minute' + (mins > 1 ? 's' : '') + ' remaining. Extend your lab by 1 hour?', 'info');
                }}
            }}
            tick();
            setInterval(tick, 1000);
        }})();
        </script>
        '''

    return user_layout(f'''
    <a href="/classes" class="small-text">{icon("arrow-left")} Back to My Classes</a>
    <div style="margin-top: 12px; margin-bottom: 24px;">
        <h1>{escape(challenge['display_name'])}</h1>
        <p class="muted" style="margin-top: 6px; font-size: 16px;">{escape(challenge.get('description', ''))}</p>
        <p class="small-text" style="margin-top: 6px;">{total_points(challenge)} points available</p>
    </div>

    {countdown_html}
    {action_card_html}
    {flags_section}

    {modals_html}

    <script>
    function openModal(idx) {{
        const modal = document.getElementById('modal-' + idx);
        if (modal) modal.style.display = 'flex';
    }}
    function closeModal(idx) {{
        const modal = document.getElementById('modal-' + idx);
        if (modal) modal.style.display = 'none';
    }}
    function copyText(elementId, btn) {{
        const el = document.getElementById(elementId);
        if (!el) return;
        let text = el.textContent || el.innerText;
        const reset = () => {{
            btn.textContent = oldText;
            btn.style.background = oldBg;
            btn.style.color = oldColor;
        }};
        if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(text).then(() => {{
                btn.textContent = 'Copied!';
                btn.style.background = '#0f382a';
                btn.style.color = '#7bf5c3';
                setTimeout(reset, 1500);
            }}).catch(() => {{
                fallbackCopy(text, btn, reset);
            }});
        }} else {{
            fallbackCopy(text, btn, reset);
        }}
    }}
    function fallbackCopy(text, btn, reset) {{
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try {{
            document.execCommand('copy');
            btn.textContent = 'Copied!';
            btn.style.background = '#0f382a';
            btn.style.color = '#7bf5c3';
            setTimeout(reset, 1500);
        }} catch (e) {{
            console.error(e);
        }}
        document.body.removeChild(ta);
    }}
    function toggleModalDetails(idx, btn) {{
        const details = document.getElementById('modal-details-' + idx);
        if (!details || !btn) return;
        const isHidden = details.style.display === 'none' || details.style.display === '';
        details.style.display = isHidden ? 'block' : 'none';
        btn.textContent = isHidden ? 'Hide connection details' : 'Show connection details';
    }}
    </script>
    ''', active='users', toasts=toasts_list)


def leaderboard_page(grouped_entries) -> str:
    sections = ''
    for class_id, entries in grouped_entries.items():
        class_name = escape(entries[0]['class_name']) if entries else escape(class_id)
        rows = ''.join(
            f'''<li><div class="row"><strong>#{index} {escape(entry["username"])}</strong><div style="text-align:right;"><strong style="color:#ffd77a;">{entry["points"]} points</strong><div class="small-text">{entry["solved"]} challenge(s) solved</div></div></div></li>'''
            for index, entry in enumerate(entries, start=1)
        ) or '<li>No scores yet.</li>'
        sections += f'''
        <section class="card" style="margin-bottom:18px;">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:12px;">
                <h3 style="margin:0;">{class_name}</h3>
                <button class="copy-class" onclick="copyText(this, '/leaderboard?class_id={class_id}')">Copy link {icon("copy")}</button>
            </div>
            <ul class="list">{rows}</ul>
        </section>
        '''

    if not sections:
        sections = '<section class="card"><p class="muted">No leaderboard data yet. Join a class and start solving challenges.</p></section>'

    return user_layout(f'''
    <h1>Leaderboard</h1>
    <p class="muted">Rankings by class. Sorted by points, then challenges solved.</p>
    {sections}
    <script>
    function copyText(btn, text) {{
        navigator.clipboard.writeText(text).then(() => {{
            const old = btn.textContent;
            btn.textContent = 'Copied!';
            btn.style.background = '#0f382a';
            btn.style.color = '#7bf5c3';
            setTimeout(() => {{
                btn.textContent = old;
                btn.style.background = '#16223b';
                btn.style.color = '#aebddd';
            }}, 1500);
        }}).catch(() => {{}});
    }}
    </script>
    ''', active='leaderboard')
