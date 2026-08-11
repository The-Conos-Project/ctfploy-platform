from page_templates.dashboard import dashboard_page
from page_templates.instance import instance_page
from page_templates.auth import sign_in_page, register_page
from page_templates.layout import admin_layout


def admin_challenges_page(challenges):
    challenges_html = '<div class="card"><h3>All challenges</h3><ul class="challenge-list">'
    for ch in challenges:
        status_cls = 'status-ready' if ch['build_status'] == 'success' else ('status-building' if ch['build_status'] == 'building' else 'status-failed')
        status_label = 'Ready' if ch['build_status'] == 'success' else ('Building' if ch['build_status'] == 'building' else 'Failed')
        challenges_html += f"""
        <li>
            <strong>{ch['display_name']}</strong>
            <span class=\"status-badge {status_cls}\">{status_label}</span>
            <div class=\"small-text\">{ch['image_tag']} · <a href=\"/admin/build_log/{ch['id']}\">Logs</a> · <a href=\"/admin/delete_challenge/{ch['id']}\">Delete</a></div>
        </li>
        """
    challenges_html += '</ul></div>'

    return admin_layout(f"""
    <div class=\"content-wrapper\">
        <div class=\"card\">
            <h2>Challenges</h2>
            <div class=\"card\">
                <h3>Import from URL</h3>
                <form action=\"/admin/import-url\" method=\"post\">
                    <input name=\"url\" placeholder=\"https://example.com/challenge.tar.gz\" required>
                    <button type=\"submit\">Fetch & Build</button>
                </form>
                <p class=\"small-text\">Import URLs only. Manual upload is no longer supported.</p>
            </div>
            {challenges_html}
        </div>
    </div>
    """, active='terminal')


def admin_codes_page(access_codes, challenges, get_challenge, flashes=None):
    flash_html = ''
    if flashes:
        for category, message in flashes:
            flash_html += f'<div class="flash {category}">{message}</div>'

    codes_html = '<div class="card"><ul class="challenge-list">'
    for code in access_codes:
        used_by = f'<span class="small-text">(used by: {", ".join(code.get("used_by", []))})</span>' if code.get('used_by') else '<span class="small-text">(unused)</span>'
        challenges_list = ''
        for cid in code.get('challenges', []):
            ch = get_challenge(cid)
            if ch:
                challenges_list += f'<li>{ch["display_name"]} ({ch["build_status"]})</li>'

        select_options = ' '.join(
            f'<option value="{ch["id"]}">{ch["display_name"]}</option>'
            for ch in challenges
            if ch['build_status'] == 'success'
        )

        codes_html += f"""
        <li>
            <strong>{code['code']}</strong> {used_by}
            <ul style="margin-left:18px; margin-top:10px;">{challenges_list}</ul>
            <form action="/admin/add_challenge_to_code" method="post" style="display:flex; gap:10px; flex-wrap:wrap; margin-top:10px;">
                <input type="hidden" name="code" value="{code['code']}">
                <select name="challenge_id" style="flex:1;">
                    {select_options}
                </select>
                <button type="submit">Add</button>
            </form>
            <div class="small-text"><a href="/admin/delete_code/{code['code']}">Delete</a></div>
        </li>
        """
    codes_html += '</ul></div>'

    return admin_layout(f"""
    <div class=\"content-wrapper\">
        {flash_html}
        <div class=\"card\">
            <h2>Access Codes</h2>
            <form action=\"/admin/gencode\" method=\"post\">
                <button type=\"submit\">Generate New Code</button>
            </form>
        </div>
        {codes_html}
    </div>
    """, active='code_badge')


def admin_dashboard_page(challenges, instances, flashes=None):
    flash_html = ''
    if flashes:
        for category, message in flashes:
            flash_html += f'<div class="flash {category}">{message}</div>'

    active_count = len([i for i in instances if i['status'] == 'running'])
    return admin_layout(f"""
    <div class=\"content-wrapper\">
        {flash_html}
        <div class=\"card\">
            <h2>Admin dashboard</h2>
            <p>Total challenges: {len(challenges)}</p>
            <p>Active instances: {active_count}</p>
        </div>
    </div>
    """, active='dashboard')


def admin_update_page(flashes=None):
    flash_html = ''
    if flashes:
        for category, message in flashes:
            flash_html += f'<div class="flash {category}">{message}</div>'

    return admin_layout(f"""
    <div class=\"content-wrapper\">
        {flash_html}
        <div class=\"card\">
            <h2>Update platform</h2>
            <p>Pull the latest image and restart the platform container.</p>
            <form method=\"post\">
                <button type=\"submit\">Update Now</button>
            </form>
        </div>
    </div>
    """, active='upload')


def build_log_page(challenge_id: str):
    return admin_layout(f"""
    <div class=\"content-wrapper\">
        <div class=\"card\">
            <h2>Build Log</h2>
            <div id=\"log\" class=\"log-window\"></div>
            <a href=\"/admin/challenges\"><button class=\"secondary-button\">Back to challenges</button></a>
        </div>
    </div>
    <script>
        const evtSource = new EventSource('/admin/build_log_stream/{challenge_id}');
        const logDiv = document.getElementById('log');
        evtSource.onmessage = function(event) {{
            if (event.data === 'END') {{ evtSource.close(); return; }}
            logDiv.innerHTML += event.data;
            logDiv.scrollTop = logDiv.scrollHeight;
        }};
        evtSource.onerror = function() {{ evtSource.close(); }};
    </script>
    """, active='terminal')
