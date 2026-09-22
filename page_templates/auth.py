from html import escape

from page_templates.layout import centered_layout, lang_switcher
from i18n import t


def _auth_shell(title: str, subtitle: str, form_html: str, footer_html: str = "") -> str:
    return centered_layout(
        f'''<div class="centered-page">
  <div class="centered-container">
    <div style="display:flex;justify-content:flex-end;margin-bottom:12px">{lang_switcher()}</div>
    <div class="card auth-card">
      <a href="/" class="brand-mark" style="display:inline-block;margin-bottom:14px">CTFploy</a>
      <h2 style="margin:0 0 6px">{title}</h2>
      <p class="muted" style="margin-top:0">{subtitle}</p>
      {form_html}
      {footer_html}
    </div>
  </div>
</div>''',
        title=f"{title} · CTFploy",
    )


def sign_in_page(error: bool = False) -> str:
    flash = f'<div class="flash error">{escape(t("invalid_credentials"))}</div>' if error else ""
    form = f'''{flash}
<form method="post" class="auth-form">
  <label for="username">{t("username")}</label>
  <input id="username" name="username" autocomplete="username" placeholder="{escape(t("username"))}" required autofocus>
  <label for="password">{t("password")}</label>
  <input id="password" type="password" name="password" autocomplete="current-password" placeholder="{escape(t("password"))}" required>
  <button type="submit" style="width:100%;margin-top:4px">{t("sign_in_button")}</button>
</form>
<p class="small-text" style="margin-top:12px"><a href="/reset-password">{t("forgot_password")}</a></p>'''
    footer = f'<p class="small-text">{t("no_account")} <a href="/sign-up">{t("sign_up_link")}</a></p>'
    return _auth_shell(t("sign_in_title"), t("sign_in_body"), form, footer)


def admin_sign_in_page(error: bool = False) -> str:
    flash = f'<div class="flash error">{escape(t("invalid_admin"))}</div>' if error else ""
    form = f'''{flash}
<form method="post" class="auth-form">
  <label for="username">{t("username")}</label>
  <input id="username" name="username" value="root" readonly>
  <label for="password">{t("password")}</label>
  <input id="password" type="password" name="password" autocomplete="current-password" placeholder="{escape(t("admin_password"))}" required autofocus>
  <button type="submit" style="width:100%;margin-top:4px">{t("sign_in_button")}</button>
</form>'''
    return _auth_shell(t("admin_sign_in_title"), t("admin_sign_in_body"), form)


def register_page(error: bool = False) -> str:
    flash = f'<div class="flash error">{escape(t("username_exists"))}</div>' if error else ""
    form = f'''{flash}
<form method="post" class="auth-form">
  <label for="username">{t("username")}</label>
  <input id="username" name="username" autocomplete="username" placeholder="{escape(t("username"))}" required autofocus>
  <label for="password">{t("password")}</label>
  <input id="password" type="password" name="password" autocomplete="new-password" placeholder="{escape(t("password"))}" required minlength="6">
  <button type="submit" style="width:100%;margin-top:4px">{t("sign_up_button")}</button>
</form>'''
    footer = f'<p class="small-text">{t("have_account")} <a href="/sign-in">{t("sign_in")}</a></p>'
    return _auth_shell(t("sign_up_title"), t("sign_up_body"), form, footer)


def change_password_page(toasts=None) -> str:
    flashes = "".join(
        f'<div class="flash {kind}">{escape(message)}</div>' for kind, message in (toasts or [])
    )
    form = f'''{flashes}
<form method="post" class="auth-form">
  <label for="old_password">{t("current_password")}</label>
  <input id="old_password" type="password" name="old_password" autocomplete="current-password" placeholder="{escape(t("current_password"))}" required>
  <label for="new_password">{t("new_password")}</label>
  <input id="new_password" type="password" name="new_password" autocomplete="new-password" placeholder="{escape(t("new_password"))}" required minlength="6">
  <button type="submit" style="width:100%;margin-top:4px">{t("update_password")}</button>
</form>'''
    footer = f'<p class="small-text"><a href="/dashboard">{t("back_dashboard")}</a></p>'
    return _auth_shell(t("change_password_title"), t("change_password_body"), form, footer)


def reset_password_request_page(error: bool = False) -> str:
    flash = f'<div class="flash error">{escape(t("invalid_credentials"))}</div>' if error else ""
    body = f'''{flash}<p class="muted">{t("reset_body")}</p>'''
    footer = f'<p class="small-text"><a href="/sign-in">{t("back_sign_in")}</a></p>'
    return _auth_shell(t("reset_title"), "", body, footer)
