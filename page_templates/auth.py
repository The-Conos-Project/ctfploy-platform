from html import escape

from page_templates.layout import centered_layout, icon


def sign_in_page(error: bool = False, show_reset: bool = False) -> str:
    toasts = []
    if error:
        toasts.append(("error", "Invalid credentials"))
    reset_link = '<p class="small-text" style="margin-top:10px;"><a href="/reset-password">Forgot password?</a></p>' if not show_reset else ''
    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>CTFploy Sign In</h2>
                <p>Access your training labs securely.</p>
                {''.join(f'<div class="flash {kind}">{escape(message)}</div>' for kind, message in toasts)}
                <form method="post">
                    <label>Username</label>
                    <input name="username" placeholder="Username" required autofocus>
                    <label>Password</label>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Sign In</button>
                </form>
                {reset_link}
                <p class="small-text">No account yet? <a href="/sign-up">Sign up</a>.</p>
            </div>
        </div>
    </div>
    """, title="Sign In - CTFploy")


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
                {''.join(f'<div class="flash {kind}">{escape(message)}</div>' for kind, message in toasts)}
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
    """, title="Admin Sign In - CTFploy")


def register_page(error: bool = False) -> str:
    toasts = []
    if error:
        toasts.append(("error", "Username already exists"))
    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>Create a new account</h2>
                <p>Sign up and start solving challenges.</p>
                {''.join(f'<div class="flash {kind}">{escape(message)}</div>' for kind, message in toasts)}
                <form method="post">
                    <label>Username</label>
                    <input name="username" placeholder="Username" required autofocus>
                    <label>Password</label>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Sign up</button>
                </form>
                <p class="small-text">Already have an account? <a href="/sign-in">Sign in</a>.</p>
            </div>
        </div>
    </div>
    """, title="Sign up - CTFploy")


def change_password_page(toasts=None) -> str:
    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>Change Password</h2>
                <p>Update your account password.</p>
                {''.join(f'<div class="flash {kind}">{escape(message)}</div>' for kind, message in (toasts or []))}
                <form method="post">
                    <label>Current password</label>
                    <input type="password" name="old_password" placeholder="Current password" required>
                    <label>New password</label>
                    <input type="password" name="new_password" placeholder="New password" required>
                    <button type="submit">Update Password</button>
                </form>
                <p class="small-text"><a href="/dashboard">Back to dashboard</a></p>
            </div>
        </div>
    </div>
    """, title="Change Password - CTFploy")


def reset_password_request_page(error: bool = False) -> str:
    toasts = []
    if error:
        toasts.append(("error", "Username not found"))
    return centered_layout(f"""
    <div class="centered-page">
        <div class="centered-container">
            <div class="card">
                <h2>Reset Password</h2>
                <p>Only an administrator can reset your password. Please request a reset from your instructor.</p>
                {''.join(f'<div class="flash {kind}">{escape(message)}</div>' for kind, message in toasts)}
                <p class="small-text"><a href="/sign-in">Back to sign in</a></p>
            </div>
        </div>
    </div>
    """, title="Reset Password - CTFploy")
