from page_templates.layout import centered_layout


def dashboard_page(user, user_challenges, get_instance, flashes=None) -> str:
    flash_html = ""
    if flashes:
        for category, message in flashes:
            flash_html += f'<div class="flash {category}">{message}</div>'

    challenge_blocks = ""
    if user_challenges:
        for ch in user_challenges:
            inst = get_instance(user["id"], ch["id"])
            if inst:
                challenge_blocks += f"""
                <li>
                    <strong>{ch['display_name']}</strong>
                    <span class="status-badge status-ready">Ready</span>
                    <div class="small-text">Port {inst['host_port']} · <a href="/instance/{inst['id']}">View</a></div>
                </li>
                """
            else:
                challenge_blocks += f"""
                <li>
                    <strong>{ch['display_name']}</strong>
                    <span class="status-badge status-ready">Ready</span>
                    <div class="small-text"><a href="/start/{ch['id']}"><button>Start</button></a></div>
                </li>
                """
    else:
        challenge_blocks = '<li>No unlocked challenges yet. Redeem an access code to get started.</li>'

    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <div style="display:flex; align-items:center; justify-content:space-between; gap:14px; flex-wrap:wrap; margin-bottom:22px;">
                    <div>
                        <h2>Welcome, {user['username']}</h2>
                        <p class="small-text">Your active lab sessions are listed below.</p>
                    </div>
                    <a href="/logout"><button class="secondary-button">Logout</button></a>
                </div>
                {flash_html}
                <div style="margin-top:18px;">
                    <h3>Unlock a lab</h3>
                    <form method="post" action="/user/redeem-code">
                        <input name="code" placeholder="Access Code" required>
                        <button type="submit">Redeem Code</button>
                    </form>
                </div>
                <div class="card" style="margin-top:24px; padding:22px;">
                    <h3>Unlocked labs</h3>
                    <ul class="challenge-list">{challenge_blocks}</ul>
                </div>
            </div>
        </div>
    </div>
    """, title="Dashboard - CTFploy")
