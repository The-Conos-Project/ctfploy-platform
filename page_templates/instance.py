from page_templates.layout import centered_layout


def instance_page(ch, inst, host, msg, hints) -> str:
    if inst["connection_type"] == "ssh":
        connection_html = f'<p>SSH: <code>ssh {inst["username"]}@{host} -p {inst["host_port"]}</code></p><p>Password: <code>{inst["password"]}</code></p>'
    elif inst["connection_type"] == "web":
        connection_html = f'<p><a href="http://{host}:{inst["host_port"]}">http://{host}:{inst["host_port"]}</a></p>'
    elif inst["connection_type"] == "nc":
        connection_html = f'<p>Netcat: <code>nc {host} {inst["host_port"]}</code></p>'
    else:
        connection_html = f'<p>Port: {inst["host_port"]}</p>'

    hints_html = ''
    if hints:
        hints_html = '<div style="margin-top:18px;"><strong>Hints</strong><ul style="margin-top:10px; margin-left:18px;">'
        for hint in hints:
            hints_html += f'<li>{hint}</li>'
        hints_html += '</ul></div>'

    flash_html = ''
    if msg:
        color = '#2ecc71' if msg == 'Correct!' else '#e74c3c'
        flash_html = f'<div class="flash" style="background:{color}; color:#000;">{msg}</div>'

    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <div style="display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; margin-bottom:18px;">
                    <div>
                        <h2>{ch['display_name']}</h2>
                        <p class="small-text">Instance ID: {inst['id']} · Expires at {inst['expires_at']}</p>
                    </div>
                    <a href="/terminate/{inst['id']}"><button class="secondary-button">Terminate</button></a>
                </div>
                {flash_html}
                <div style="margin-top:16px;">
                    <h3>Connection details</h3>
                    {connection_html}
                </div>
                {hints_html}
                <div style="margin-top:24px;">
                    <h3>Submit flag</h3>
                    <form method="post" action="/submit_flag/{inst['id']}" style="display:flex; gap:12px; flex-wrap:wrap; align-items:flex-start;">
                        <input name="flag" placeholder="flag{{...}}" required style="flex:1; min-width:240px;">
                        <button type="submit">Submit</button>
                    </form>
                </div>
                <div style="margin-top:22px;"><a href="/dashboard" class="small-text">Back to dashboard</a></div>
            </div>
        </div>
    </div>
    """, title=f"{ch['display_name']} - CTFploy")
