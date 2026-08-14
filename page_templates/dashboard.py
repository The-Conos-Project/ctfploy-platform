from html import escape

from page_templates.layout import user_layout


def _flashes(flashes):
    return ''.join(f'<div class="flash {category}">{escape(message)}</div>' for category, message in (flashes or []))


def dashboard_page(user, user_classes, active_instances, solved_count, total_count, flashes=None) -> str:
    flash_html = _flashes(flashes)

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
        f'''<li><div class="row"><div><strong>{escape(c["name"])}</strong><div class="small-text">{len(c["challenge_ids"])} challenge(s) · Join code: <code>{escape(c["join_code"])}</code></div></div><a href="/classes/{c["id"]}"><button class="secondary">Open class</button></a></div></li>'''
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
    {flash_html}
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
            <div style="margin-top: 16px;"><a href="/classes" class="small-text">View all classes →</a></div>
        </section>
    </div>
    ''', active='home')


def classes_page(classes, flashes=None) -> str:
    items = ''.join(
        f'''<li><div class="row"><div><strong>{escape(classroom['name'])}</strong><div class="small-text">{len(classroom['challenge_ids'])} assigned challenge(s)</div></div><a href="/classes/{classroom['id']}"><button>Open class</button></a></div></li>'''
        for classroom in classes
    ) or '<li>No classes joined yet.</li>'
    return user_layout(f'''{_flashes(flashes)}<h1>My classes</h1><p class="muted">Open a class to view only its assigned challenges.</p><section class="card"><ul class="list">{items}</ul></section>''', active='users')


def class_detail_page(classroom, challenges, instances, flashes=None) -> str:
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
        rows += f'''<li><div class="row"><div><strong>{escape(challenge['display_name'])}</strong><div class="small-text">{escape(challenge.get('description', ''))}</div>{badge}</div>{action}</div></li>'''
    return user_layout(f'''{_flashes(flashes)}<a href="/classes" class="small-text">← All classes</a><h1>{escape(classroom['name'])}</h1><p class="muted">Join code: <code>{escape(classroom['join_code'])}</code></p><section class="card"><h3>Assigned challenges</h3><ul class="list">{rows or '<li>No challenges have been assigned yet.</li>'}</ul></section>''', active='users')


def student_challenges_page(challenges, instances, solved_challenge_ids, flashes=None) -> str:
    flash_html = _flashes(flashes)

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
        rows += f'''<li><div class="row"><div><strong>{escape(challenge['display_name'])}</strong><div class="small-text">{escape(challenge.get('description', ''))}</div>{badge_html}</div>{action}</div></li>'''

    return user_layout(f'''
    {flash_html}
    <h1>All Assigned Challenges</h1>
    <p class="muted">Access and solve challenges assigned to you across all joined classes.</p>
    <section class="card">
        <ul class="list">{rows or '<li>No challenges have been assigned yet. Join a classroom first!</li>'}</ul>
    </section>
    ''', active='users')


def student_challenge_detail_page(ch, inst, host, msg, flag_specs, progress) -> str:
    def format_hint(hint: str) -> str:
        stripped = hint.strip()
        command_prefixes = ('$', 'ssh ', 'curl ', 'nc ', 'cat ', 'ls ', 'find ', 'grep ', 'tar ', 'sudo ', 'chmod ', 'ps ', 'netstat ', 'ss ', 'echo ', 'export ', 'python', 'pip', 'nano ', 'vim ', 'vi ', 'touch ', 'mkdir ', 'cd ', 'pwd', 'whoami', 'id', 'file ', 'head ', 'tail ', 'less ', 'more ', 'wc ', 'sort ', 'uniq ', 'awk ', 'sed ', 'cut ', 'tr ', 'xargs ', 'jq ')
        if any(stripped.startswith(p) for p in command_prefixes):
            cmd = stripped.lstrip('$ ').strip()
            return f'<div class="terminal-snippet"><span class="terminal-prompt">$</span><span class="terminal-cmd">{escape(cmd)}</span></div>'
        parts = hint.split('`')
        result = []
        for i, part in enumerate(parts):
            if i % 2 == 1:
                result.append(f'<code class="inline-code">{escape(part)}</code>')
            else:
                result.append(escape(part))
        return '<br>'.join(result)

    connection_html = ''
    if inst:
        connection_html = f'''
        <p class="small-text" style="margin-bottom: 8px;">Connect to your lab environment via SSH:</p>
        <div class="terminal-snippet">
            <span class="terminal-prompt">$</span>
            <span class="terminal-cmd" id="ssh-cmd">ssh {escape(inst["username"])}@{escape(host)} -p {inst["host_port"]}</span>
            <button class="copy-btn" onclick="copyText('ssh-cmd', this)">Copy</button>
        </div>
        <p style="margin-top: 8px;">Password: <code class="inline-code" id="ssh-passwd" style="user-select: all;">{escape(inst["password"])}</code> <button class="copy-btn" style="padding: 2px 6px; font-size: 10px; margin-left: 6px;" onclick="copyText('ssh-passwd', this)">Copy</button></p>
        '''

    objectives_html = ''
    for index, spec in enumerate(flag_specs, start=1):
        hints_html = ''.join(f'<li style="margin-top: 8px;">{format_hint(hint)}</li>' for hint in spec['hints'])
        description_text = f'<p style="margin: 8px 0 4px; color: #aebddd;">{escape(spec["description"])}</p>' if spec['description'] else ''
        hint_list_html = f'<ul style="margin-left: 18px; font-size: 13px; color: #8da2ce; list-style: square;">{hints_html}</ul>' if hints_html else ''
        objectives_html += f'<li style="padding: 16px 0; border-bottom: 1px solid #1f2d47;"><strong style="font-size: 15px;">Flag {index}</strong>{description_text}{hint_list_html}</li>'
    if objectives_html:
        objectives_html = f'''
        <section class="card" style="margin-top: 18px;">
            <h3>Objectives & Hints</h3>
            <ul class="list" style="margin-top: 10px;">{objectives_html}</ul>
        </section>
        '''

    flash_html = ''
    if msg:
        color = '#0e3025' if msg.startswith('Accepted!') or msg == 'Correct!' else '#3d1620'
        text_color = '#8efcd4' if msg.startswith('Accepted!') or msg == 'Correct!' else '#ffb3c1'
        border_color = '#164e3c' if msg.startswith('Accepted!') or msg == 'Correct!' else '#5e2230'
        flash_html = f'<div class="flash" style="background:{color}; color:{text_color}; border: 1px solid {border_color}; font-weight: 600;">{escape(msg)}</div>'

    action_card_html = ''
    status = ch.get('build_status', 'failed')
    if inst:
        progress_html = ''
        if progress[1] > 1:
            progress_html = f'<p class="small-text" style="margin-bottom: 8px;">Flag progress: <strong>{progress[0]}/{progress[1]}</strong></p>'

        action_card_html = f'''
        <div class="card" style="border: 1px solid #79a6ff;">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; margin-bottom:18px;">
                <div>
                    <h3 style="margin:0; display:flex; align-items:center; gap:8px;">
                        <span class="status-badge status-ready" style="margin:0;">Active Lab</span>
                    </h3>
                    <p class="small-text" style="margin-top: 4px;">Instance ID: {inst['id']} · Expires in: <span id="countdown" style="font-weight: 600; color: #79a6ff;">{inst['expires_at']}</span></p>
                </div>
                <a href="/terminate/{inst['id']}"><button class="secondary" style="background: #3d131f; color: #ffa3b8; border: 1px solid #5e2230;">Terminate Lab</button></a>
            </div>

            <div style="margin-top:16px; border-top: 1px solid #1f2d47; padding-top: 16px;">
                <h4 style="margin-bottom: 8px; font-weight: 600;">Connection Details</h4>
                {connection_html}
            </div>

            <div style="margin-top:24px; border-top: 1px solid #1f2d47; padding-top: 16px;">
                <h4 style="margin-bottom:8px; font-weight: 600;">Submit Flag</h4>
                {progress_html}
                <form method="post" action="/submit_flag/{inst['id']}" style="display:flex; gap:12px; flex-wrap:wrap; align-items:center;">
                    <input name="flag" placeholder="flag{{...}}" required style="flex:1; min-width:240px; margin:0;">
                    <button type="submit">Submit Flag</button>
                </form>
            </div>
        </div>

        <script>
            const expires = new Date("{inst["expires_at"]}");
            const timer = setInterval(() => {{
                const diff = expires - new Date();
                if (diff <= 0) {{
                    document.getElementById('countdown').textContent = 'Expired';
                    clearInterval(timer);
                }} else {{
                    const m = Math.floor(diff/60000);
                    const s = Math.floor((diff%60000)/1000);
                    document.getElementById('countdown').textContent = m + ':' + (s<10?'0':'') + s;
                }}
            }}, 1000);
        </script>
        '''
    else:
        if status == 'ready':
            action_card_html = f'''
            <div class="card" style="text-align: center; padding: 32px 24px;">
                <h3>Ready to start?</h3>
                <p class="muted small-text" style="margin-bottom: 18px;">Clicking start will spin up an isolated, temporary container environment for this challenge.</p>
                <a href="/start/{ch['id']}"><button style="padding: 12px 28px; font-size: 16px;">Start Lab Environment</button></a>
            </div>
            '''
        elif status == 'building':
            action_card_html = f'''
            <div class="card" style="text-align: center; padding: 32px 24px;">
                <span class="status-badge status-building" style="margin-bottom: 12px;">Building Challenge</span>
                <p class="muted small-text">The instructor recently uploaded this challenge and it is currently compiling. Please wait...</p>
            </div>
            '''
        else:
            action_card_html = f'''
            <div class="card" style="text-align: center; padding: 32px 24px; border: 1px solid #3d131f;">
                <span class="status-badge status-failed" style="margin-bottom: 12px;">Build Failed</span>
                <p class="muted small-text">This challenge could not build correctly. Please contact your administrator.</p>
            </div>
            '''

    return user_layout(f'''
    <a href="/classes" class="small-text">← Back to My Classes</a>
    <div style="margin-top: 12px; margin-bottom: 24px;">
        <h1>{escape(ch['display_name'])}</h1>
        <p class="muted" style="margin-top: 6px; font-size: 16px;">{format_hint(ch.get('description', ''))}</p>
    </div>

    {flash_html}
    {action_card_html}
    {objectives_html}

    <script>
    function copyText(elementId, btn) {{
        const el = document.getElementById(elementId);
        if (!el) return;
        let text = el.textContent || el.innerText;
        navigator.clipboard.writeText(text).then(() => {{
            const oldText = btn.textContent;
            btn.textContent = 'Copied!';
            const oldBg = btn.style.background;
            const oldColor = btn.style.color;
            btn.style.background = '#0f382a';
            btn.style.color = '#7bf5c3';
            setTimeout(() => {{
                btn.textContent = oldText;
                btn.style.background = oldBg;
                btn.style.color = oldColor;
            }}, 1500);
        }});
    }}
    </script>
    ''', active='users')


