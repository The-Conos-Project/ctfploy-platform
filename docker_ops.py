import os, shutil, time, uuid, threading
from datetime import datetime, timedelta
from typing import Optional, Tuple
import docker

from config import BUILD_LOGS_STORE, DOCKER_NETWORK, INSTANCE_TIMEOUT, MAX_CONCURRENT_PER_USER
from data_store import load_data, save_data

_docker_client = None
_docker_lock = threading.Lock()


def get_docker_client():
    """Create the Docker client lazily so the web UI can start without Docker."""
    global _docker_client
    with _docker_lock:
        if _docker_client is None:
            try:
                client = docker.from_env(timeout=5)
                client.ping()
                _docker_client = client
            except Exception as exc:
                raise RuntimeError(
                    "Docker is unavailable. Mount /var/run/docker.sock and ensure the Docker daemon is running."
                ) from exc
    return _docker_client


def ensure_network() -> None:
    docker_client = get_docker_client()
    try:
        docker_client.networks.get(DOCKER_NETWORK)
    except docker.errors.NotFound:
        docker_client.networks.create(DOCKER_NETWORK, driver="bridge")


def build_log_path(challenge_id: str) -> str:
    return os.path.join(BUILD_LOGS_STORE, f"{challenge_id}.log")


def build_image_thread(name: str, build_dir: str, tag: str, challenge_id: str) -> None:
    os.makedirs(BUILD_LOGS_STORE, exist_ok=True)
    log_path = build_log_path(challenge_id)

    def write_log(log, message: str) -> None:
        log.write(message if message.endswith("\n") else f"{message}\n")
        log.flush()

    try:
        docker_client = get_docker_client()
        with open(log_path, "a", encoding="utf-8") as log:
            write_log(log, "Build started...")
            _, logs = docker_client.images.build(path=build_dir, tag=tag, rm=True)
            for chunk in logs:
                if "stream" in chunk:
                    write_log(log, chunk["stream"])
                elif "error" in chunk:
                    write_log(log, f"ERROR: {chunk['error']}")
                elif "errorDetail" in chunk:
                    write_log(log, f"ERROR: {chunk['errorDetail'].get('message', chunk['errorDetail'])}")
            write_log(log, "Build completed successfully!")
        data = load_data()
        for ch in data["challenges"]:
            if ch["id"] == challenge_id:
                ch["build_status"] = "success"
        save_data(data)
    except Exception as e:
        with open(log_path, "a", encoding="utf-8") as log:
            write_log(log, f"Build failed: {e}")
        data = load_data()
        for ch in data["challenges"]:
            if ch["id"] == challenge_id:
                ch["build_status"] = "failed"
        save_data(data)
    finally:
        # The image is now in Docker; retaining untrusted build contexts wastes disk.
        shutil.rmtree(build_dir, ignore_errors=True)


def _random_credentials() -> Tuple[str, str]:
    username = f"ctf_{uuid.uuid4().hex[:8]}"
    password = uuid.uuid4().hex[:12]
    return username, password


def create_container(challenge: dict, user_id: str) -> Tuple[Optional[dict], Optional[str]]:
    data = load_data()
    user_instances = [i for i in data["instances"] if i["user_id"] == user_id and i["status"] == "running"]
    if len(user_instances) >= MAX_CONCURRENT_PER_USER:
        return None, "Maximum concurrent instances reached"

    image_tag = challenge["image_tag"]
    internal_port = challenge["internal_port"]
    username, password = _random_credentials()

    env = {}
    dyn_flag = None
    if challenge.get("flag_type") == "dynamic":
        dyn_flag = f"flag{{{uuid.uuid4()}}}"
        env["FLAG"] = dyn_flag

    env["SSH_USER"] = username
    env["SSH_PASSWORD"] = password

    container_name = f"ctf_{challenge['id']}_{int(time.time())}"
    try:
        ensure_network()
        docker_client = get_docker_client()
        container = docker_client.containers.run(
            f"{image_tag}:latest",
            detach=True,
            name=container_name,
            ports={f"{internal_port}/tcp": None},
            environment=env,
            mem_limit="512m",
            nano_cpus=int(0.5 * 1e9),
            network=DOCKER_NETWORK,
            remove=True
        )
        container.reload()
        bindings = container.attrs["NetworkSettings"]["Ports"].get(f"{internal_port}/tcp")
        if not bindings:
            container.stop(timeout=3)
            return None, "Docker did not publish the challenge port"
        port = int(bindings[0]["HostPort"])
    except Exception as e:
        return None, f"Docker error: {e}"

    instance = {
        "id": str(uuid.uuid4())[:8],
        "user_id": user_id,
        "challenge_id": challenge["id"],
        "container_id": container.id,
        "container_name": container_name,
        "host_port": port,
        "connection_type": challenge["connection_type"],
        "status": "running",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(seconds=INSTANCE_TIMEOUT)).isoformat(),
        "dynamic_flag": dyn_flag,
        "flag": challenge.get("flag", ""),
        "username": username,
        "password": password,
    }
    data["instances"].append(instance)
    save_data(data)
    threading.Thread(target=auto_terminate, args=(instance["id"], INSTANCE_TIMEOUT), daemon=True).start()
    return instance, None


def terminate_instance(instance_id: str) -> bool:
    data = load_data()
    inst = next((i for i in data["instances"] if i["id"] == instance_id), None)
    if inst and inst["status"] == "running":
        try:
            container = get_docker_client().containers.get(inst["container_id"])
            container.stop(timeout=3)
        except Exception:
            pass
        inst["status"] = "terminated"
        inst["terminated_at"] = datetime.now().isoformat()
        save_data(data)
        return True
    return False


def auto_terminate(instance_id: str, delay: int) -> None:
    time.sleep(delay)
    terminate_instance(instance_id)
