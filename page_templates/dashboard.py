from page_templates.layout import user_layout


def dashboard_page(user, user_classes, user_challenges, get_instance, flashes=None) -> str:
    flash_html = ''.join(f'<div class="flash {category}">{message}</div>' for category, message in (flashes or []))
    class_blocks = ''.join(f'<li><strong>{c["name"]}</strong><div class="small-text">Code: <code>{c["join_code"]}</code> · {len(c["challenge_ids"])} assignment(s)</div></li>' for c in user_classes) or '<li>You have not joined a class yet.</li>'
    challenge_blocks = ''
    for challenge in user_challenges:
        instance = get_instance(user['id'], challenge['id'])
        action = f'<a href="/instance/{instance["id"]}"><button class="secondary">Open lab</button></a>' if instance else f'<a href="/start/{challenge["id"]}"><button>Start lab</button></a>'
        challenge_blocks += f'<li><div class="row"><div><strong>{challenge["display_name"]}</strong><div class="small-text">{challenge["connection_type"].upper()} challenge</div></div>{action}</div></li>'
    if not challenge_blocks:
        challenge_blocks = '<li>Join a class to receive challenge assignments.</li>'
    return user_layout(f'''<h1>Welcome back, {user['username']}</h1><p class="muted">Your CTF classes and challenge labs.</p>{flash_html}<div class="grid"><section class="card"><h3>Join a class</h3><p class="small-text">Enter the class code from your instructor.</p><form method="post" action="/user/join-class"><input name="code" placeholder="CLASS-ABC123" required><button>Join class</button></form></section><section class="card"><h3>My classes</h3><ul class="list">{class_blocks}</ul></section></div><section class="card"><h2>Assigned challenges</h2><ul class="list">{challenge_blocks}</ul></section>''')
