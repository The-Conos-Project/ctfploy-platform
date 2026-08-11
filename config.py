import os

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24).hex())
INSTANCE_TIMEOUT = int(os.environ.get("INSTANCE_TIMEOUT", 30 * 60))
MAX_CONCURRENT_PER_USER = int(os.environ.get("MAX_CONCURRENT_PER_USER", 3))
DATA_FILE = "/data/data.json"
DOCKER_NETWORK = "ctf_net"
CHALLENGES_STORE = "/data/challenges_store"
