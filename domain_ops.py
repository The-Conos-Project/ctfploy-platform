"""Custom-domain and Let's Encrypt helpers for installer-managed deployments."""
import os
import re
import urllib.request

from docker_ops import get_docker_client

NGINX_CONFIG = os.environ.get("NGINX_CONFIG_PATH", "/etc/ctfploy/nginx/default.conf")
ACME_VOLUME = os.environ.get("ACME_VOLUME", "ctfploy-acme")
CERT_VOLUME = os.environ.get("CERT_VOLUME", "ctfploy-certs")


def normalize_domain(value: str) -> str:
    domain = value.strip().lower().rstrip(".")
    if not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", domain):
        raise ValueError("Enter a valid domain such as ctf.example.com")
    return domain


def public_ip() -> str:
    for url in ("https://api.ipify.org", "https://ifconfig.io/ip"):
        try:
            with urllib.request.urlopen(url, timeout=4) as response:
                return response.read().decode().strip()
        except Exception:
            continue
    return "your VPS public IP"


def _nginx_config(domain: str, secured: bool) -> str:
    acme = "location ^~ /.well-known/acme-challenge/ { root /var/www/certbot; }"
    proxy = "location / { proxy_pass http://platform:8000; proxy_http_version 1.1; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto $scheme; proxy_buffering off; proxy_read_timeout 86400s; }"
    if not secured:
        return f"server {{ listen 80; server_name {domain}; {acme} {proxy} }}\n"
    return f"server {{ listen 80; server_name {domain}; {acme} location / {{ return 301 https://$host$request_uri; }} }}\nserver {{ listen 443 ssl; server_name {domain}; ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem; ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem; {proxy} }}\n"


def _write_config(domain: str, secured: bool) -> None:
    os.makedirs(os.path.dirname(NGINX_CONFIG), exist_ok=True)
    with open(NGINX_CONFIG, "w", encoding="utf-8") as config:
        config.write(_nginx_config(domain, secured))


def _reload_nginx() -> None:
    client = get_docker_client()
    containers = client.containers.list(filters={"label": "com.docker.compose.service=nginx"})
    if not containers:
        raise RuntimeError("Installer Nginx container was not found. Re-run the CTFploy installer.")
    result = containers[0].exec_run(["nginx", "-s", "reload"])
    if result.exit_code:
        raise RuntimeError(result.output.decode("utf-8", errors="replace") or "Nginx reload failed")


def prepare_domain(value: str) -> str:
    domain = normalize_domain(value)
    _write_config(domain, secured=False)
    _reload_nginx()
    return domain


def issue_certificate(domain: str, email: str) -> None:
    domain = normalize_domain(domain)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
        raise ValueError("Enter a valid certificate notification email")
    client = get_docker_client()
    result = client.containers.run(
        "certbot/certbot:latest",
        ["certonly", "--webroot", "-w", "/var/www/certbot", "--non-interactive", "--agree-tos", "--email", email.strip(), "-d", domain],
        remove=True,
        volumes={ACME_VOLUME: {"bind": "/var/www/certbot", "mode": "rw"}, CERT_VOLUME: {"bind": "/etc/letsencrypt", "mode": "rw"}},
    )
    _write_config(domain, secured=True)
    _reload_nginx()
