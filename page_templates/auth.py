from html import escape

from page_templates.layout import centered_layout, icon


def sign_in_page(error: bool = False) -> str:
    toasts = []
    if error:
        toasts.append(("error", "Invalid credentials"))
    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>CTFploy Sign In</h2>
                <p>Access your training labs securely.</p>
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
    """, title="Sign In - CTFploy", toasts=toasts)


def admin_sign_in_page(error: bool = False) -> str:
    toasts = []
    if error:
        toasts.append(("error", "Invalid admin credentials"))
    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>CTFploy Admin Sign In</h2>
                <p>Admin username is fixed to <strong>root</strong>.</p>
                <form method="post">
                    <label>Username</label>
                    <input name="username" value="root" readonly>
                    <label>Password</label>
                    <input type="password" name="password" placeholder="Admin password" required autofocus>
                    <button type="submit">Sign In</button>
                </form>
            </div>
        </div>
    </div>
    """, title="Admin Sign In - CTFploy", toasts=toasts)


def register_page(error: bool = False) -> str:
    toasts = []
    if error:
        toasts.append(("error", "Username already exists"))
    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>Create a new account</h2>
                <p>Register and start solving challenges.</p>
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
    """, title="Register - CTFploy", toasts=toasts)
