import os

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24).hex())
INSTANCE_TIMEOUT = int(os.environ.get("INSTANCE_TIMEOUT", 30 * 60))
MAX_CONCURRENT_PER_USER = int(os.environ.get("MAX_CONCURRENT_PER_USER", 3))
DATA_DB = "/data/data.db"
DATA_JSON = "/data/data.json"
HASH_ITERATIONS = int(os.environ.get("HASH_ITERATIONS", "150000"))
HASH_SALT_BYTES = int(os.environ.get("HASH_SALT_BYTES", "16"))
DOCKER_NETWORK = "ctf_net"
CHALLENGES_STORE = "/data/challenges_store"
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
