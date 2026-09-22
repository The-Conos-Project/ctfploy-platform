from page_templates.layout import centered_layout, icon, lang_switcher
from i18n import t


def landing_page() -> str:
    return centered_layout(
        f'''<header class="row topbar">
  <strong class="brand-mark">CTFploy</strong>
  <div class="topbar-actions">
    {lang_switcher()}
    <a href="/sign-in"><button type="button" class="secondary">{t("sign_in")}</button></a>
    <a href="/sign-up"><button type="button">{t("get_started")}</button></a>
  </div>
</header>
<section class="hero">
  <div class="badge">{t("badge")}</div>
  <h1>{t("hero_title")}</h1>
  <p>{t("hero_body")}</p>
  <a href="/sign-up"><button type="button">{t("start_learning")}</button></a>
  <div class="grid" style="margin-top:58px;text-align:left">
    <div class="card">{icon("package")}<h3>{t("feature_isolated")}</h3><p class="small-text">{t("feature_isolated_body")}</p></div>
    <div class="card">{icon("users")}<h3>{t("feature_classes")}</h3><p class="small-text">{t("feature_classes_body")}</p></div>
    <div class="card">{icon("terminal")}<h3>{t("feature_docker")}</h3><p class="small-text">{t("feature_docker_body")}</p></div>
  </div>
</section>
<footer class="footer">{t("footer")}</footer>''',
        title="CTFploy",
    )


def not_found_page() -> str:
    return centered_layout(
        f'''<div class="centered-page">
  <div class="centered-container">
    <div class="card" style="text-align:center">
      <div style="display:flex;justify-content:center;margin-bottom:12px">{icon("circle-alert")}</div>
      <h2 style="margin-top:0">{t("not_found_title")}</h2>
      <p class="muted">{t("not_found_body")}</p>
      <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-top:18px">
        <a href="/"><button type="button">{t("go_home")}</button></a>
        <a href="/sign-in"><button type="button" class="secondary">{t("sign_in")}</button></a>
      </div>
      <div style="margin-top:18px;display:flex;justify-content:center">{lang_switcher()}</div>
    </div>
  </div>
</div>''',
        title=f'{t("not_found_title")} · CTFploy',
    )
