#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

python3 -m pip install --upgrade pip
python3 -m pip install --no-cache-dir -r requirements.txt
mkdir -p /data
mkdir -p /data/challenges_store
mkdir -p /data

cat <<'INSTR'
Install complete.
Next steps:
  export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
  export ADMIN_PASSWORD="your-admin-password"
  python3 app.py

Or build the Docker image:
  docker build -t ctfploy-platform .
INSTR
