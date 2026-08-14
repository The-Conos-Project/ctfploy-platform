from html import escape

from page_templates.layout import user_layout, icon
from challenge_meta import total_points


def dashboard_page(user, user_classes, active_instances, solved_count, total_count, toasts=None) -> str:
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

    class_blocks = ''.join(
        f'''<li><div class="row"><div><strong>{escape(c["name"])}</strong><div class="small-text">{len(c['challenge_ids'])} challenge(s) · Join code: <code>{escape(c['join_code'])}</code></div></div><a href="/classes/{c["id"]}"><button class="secondary">Open class</button></a></div></li>'''
        for c in user_classes
    ) or '<li>You have not joined a class yet.</li>'

    solved_percentage = 0
    if total_count > 0:
        solved_percentage = int((solved_count / total_count) * 100)

    stats_html = f'''
    <div class="grid" style="margin-bottom: 24px;">
        <div class="card">
            <div class="small-text">Classrooms Joined</div>
            <div class="stat">{len(user_classes)}</div>
        </div>
        <div class="card">
            <div class="small-text">Assigned Challenges</div>
            <div class="stat">{total_count}</div>
        </div>
        <div class="card">
            <div class="small-text">Challenges Solved</div>
            <div class="stat">{solved_count} <span style="font-size: 14px; font-weight: normal; color: #aebddd;">({solved_percentage}%)</span></div>
        </div>
    </div>
    '''

    return user_layout(f'''
    <h1>Welcome back, {escape(user['username'])}</h1>
    <p class="muted" style="margin-bottom: 24px;">Track your training labs, classrooms, and solver progress.</p>
    {stats_html}
    {active_labs_html}
    <div class="grid">
        <section class="card">
            <h3>Join a class</h3>
            <p class="small-text">Enter the join code provided by your instructor.</p>
            <form method="post" action="/user/join-class">
                <input name="code" placeholder="CLASS-ABC123" required>
                <button style="width: 100%; margin-top: 10px;">Join class</button>
            </form>
        </section>
        <section class="card">
            <h3>My classes</h3>
            <ul class="list">{class_blocks}</ul>
            <div style="margin-top: 16px;"><a href="/classes" class="small-text">View all classes {icon("arrow-right")}</a></div>
        </section>
    </div>
    ''', active='home', toasts=toasts)


def classes_page(classes, toasts=None) -> str:
    items = ''.join(
        f'''<li><div class="row"><div><strong>{escape(classroom['name'])}</strong><div class="small-text">{len(classroom['challenge_ids'])} assigned challenge(s)</div></div><a href="/classes/{classroom['id']}"><button>Open class</button></a></div></li>'''
        for classroom in classes
    ) or '<li>No classes joined yet.</li>'
    return user_layout(f'''<h1>My classes</h1><p class="muted">Open a class to view only its assigned challenges.</p><section class="card"><ul class="list">{items}</ul></section>''', active='users', toasts=toasts)


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
        rows += f'''<li><div class="row"><div><strong>{escape(challenge['display_name'])}</strong><div class="small-text">{escape(challenge.get('description', ''))}</div><div class="small-text">{total_points(challenge)} points</div>{badge}</div>{action}</div></li>'''
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
        rows += f'''<li><div class="row"><div><strong>{escape(challenge['display_name'])}</strong><div class="small-text">{escape(challenge.get('description', ''))}</div><div class="small-text">{total_points(challenge)} points</div>{badge_html}</div>{action}</div></li>'''

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
        status_class = "status-success" if submitted else "status-ready"
        status_text = "solved" if submitted else "ready"
        challenge_cards.append({
            "index": idx,
            "spec": spec,
            "submitted": submitted,
            "status_class": status_class,
            "status_text": status_text,
        })

    cards_html = ""
    for card in challenge_cards:
        idx = card["index"]
        spec = card["spec"]
        description = escape(spec.get("description", ""))
        hints = spec.get("hints", [])
        hints_list = "".join(f"<li style='margin-top:6px;'>{format_hint(h)}</li>" for h in hints)
        hints_block = f"<ul style='margin-left:18px; font-size:13px; color:#8da2ce; list-style:square;'>{hints_list}</ul>" if hints_list else ""
        flag_value = escape(spec.get("flag", ""))
        card_class = "flag-card solved" if card["submitted"] else "flag-card"
        remaining = attempts_remaining.get(idx, spec.get("max_attempts", 3))
        points = spec.get("points", 100)

        cards_html += f'''
        <div class="{card_class}" onclick="openModal({idx})" style="cursor:pointer; position:relative;">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;">
                <div>
                    <strong style="font-size:15px;">Challenge {idx + 1}</strong>
                    <div class="small-text" style="margin-top:4px;">{description}</div>
                    <div class="small-text" style="margin-top:4px;">{points} points · {remaining}/{spec.get("max_attempts", 3)} attempts remaining</div>
                </div>
                <span class="badge-external {card['status_class']}">{card['status_text']}</span>
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
        flag_value = escape(spec.get("flag", ""))
        submitted = card["submitted"]
        remaining = attempts_remaining.get(idx, spec.get("max_attempts", 3))
        points = spec.get("points", 100)

        if inst:
            connection = f'''
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
            '''
            if submitted:
                action_area = f'''
                <div class="card" style="border:1px solid #164e3c; background:#0e3025; margin-top:16px;">
                    <h4 style="margin:0; color:#8efcd4;">Challenge completed</h4>
                </div>
                <form method="post" action="/terminate/{inst['id']}" onsubmit="return confirm('Terminate this lab?')" style="margin-top:12px;">
                    <button type="submit" class="secondary" style="color:#ffb3c1; border-color:#5e2230;">Terminate Lab</button>
                </form>
                '''
            elif remaining > 0:
                action_area = f'''
                <form method="post" action="/submit_flag/{inst['id']}" style="display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin-top:16px;">
                    <input type="hidden" name="flag_index" value="{idx}">
                    <input name="flag" placeholder="CN{{...}}" required style="flex:1; min-width:240px; margin:0; font-family:inherit;">
                    <button type="submit" style="font-family:inherit;">Submit Flag</button>
                </form>
                <form method="post" action="/terminate/{inst['id']}" onsubmit="return confirm('Terminate this lab?')" style="margin-top:10px;">
                    <button type="submit" class="secondary" style="color:#ffb3c1; border-color:#5e2230; font-size:12px; padding:6px 12px; font-family:inherit;">Terminate Lab</button>
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
                        <span class="badge-external {card['status_class']}" style="position:static; margin-left:8px;">{card['status_text']}</span>
                    </div>
                    <button class="modal-close" onclick="closeModal({idx})">{icon("circle-x")}</button>
                </div>
                <p style="color:#aebddd; margin-bottom:12px;">{description}</p>
                <div style="margin-bottom:16px;">
                    <h4 style="margin-bottom:8px; font-weight:600;">Hints</h4>
                    {hints_block}
                </div>
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

    toasts_list = []
    if msg:
        toasts_list.append(("success" if msg.startswith("Accepted!") else "error", msg))

    countdown_html = ""
    if expires_at:
        countdown_html = f'''
        <div class="card" style="margin-bottom:18px; border:1px solid #203154; background:#11192e;">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;">
                <div>
                    <strong style="font-size:14px;">Lab Timer</strong>
                    <div class="small-text" style="margin-top:4px;">Auto-terminates when timer reaches zero</div>
                </div>
                <span id="lab-countdown" style="font-size:20px; font-weight:800; color:#ffd77a; font-variant-numeric:tabular-nums;">--:--</span>
            </div>
        </div>
        <script>
        (function() {{
            const target = new Date({escape(expires_at)}).getTime();
            const el = document.getElementById('lab-countdown');
            function tick() {{
                const now = new Date().getTime();
                let diff = Math.max(0, Math.floor((target - now) / 1000));
                const m = String(Math.floor(diff / 60)).padStart(2, '0');
                const s = String(diff % 60).padStart(2, '0');
                if (el) el.textContent = m + ':' + s;
                if (diff <= 0 && el) {{
                    el.textContent = '00:00';
                    el.style.color = '#ffb3c1';
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
    </script>
    ''', active='users', toasts=toasts_list)


def leaderboard_page(entries) -> str:
    rows = ''.join(
        f'''<li><div class="row"><strong>#{index} {escape(entry["username"])}</strong><div style="text-align:right;"><strong>{entry["points"]} points</strong><div class="small-text">{entry["solved"]} challenge(s) solved</div></div></div></li>'''
        for index, entry in enumerate(entries, start=1)
    ) or '<li>No scores yet.</li>'
    return user_layout(f'''
    <h1>Leaderboard</h1>
    <p class="muted">Ranked by points earned from submitted flags.</p>
    <section class="card">
        <ul class="list">{rows}</ul>
    </section>
    ''', active='leaderboard')
