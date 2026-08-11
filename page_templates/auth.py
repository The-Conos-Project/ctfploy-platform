from page_templates.layout import centered_layout


def sign_in_page(error: bool = False) -> str:
    error_html = '<div class="flash error">Invalid credentials</div>' if error else ''
    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>CTFploy Sign In</h2>
                <p>Access your training labs securely.</p>
                {error_html}
                <form method="post">
                    <label>Username</label>
                    <input name="username" placeholder="Username" required autofocus>
                    <label>Password</label>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Sign In</button>
                </form>
                <p class="small-text">No account yet? <a href="/register">Create one here</a>.</p>
            </div>
        </div>
    </div>
    """, title="Sign In - CTFploy")


def register_page(error: bool = False) -> str:
    error_html = '<div class="flash error">Username already exists</div>' if error else ''
    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>Create a new account</h2>
                <p>Register and start solving challenges.</p>
                {error_html}
                <form method="post">
                    <label>Username</label>
                    <input name="username" placeholder="Username" required autofocus>
                    <label>Password</label>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Register</button>
                </form>
                <p class="small-text">Already have an account? <a href="/sign-in">Sign in</a>.</p>
            </div>
        </div>
    </div>
    """, title="Register - CTFploy")

