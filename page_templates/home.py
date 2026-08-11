from page_templates.layout import centered_layout


def landing_page() -> str:
    return centered_layout(
        """
        <div class="centered-page">
            <div class="centered-container">
                <div class="card" style="text-align:center;">
                    <h2>Welcome to CTFploy</h2>
                    <p>Self-hosted CTF training with URL-only challenge imports.</p>
                    <a href="/sign-in"><button>Get Started</button></a>
                </div>
            </div>
        </div>
        """,
        title="CTFploy"
    )
