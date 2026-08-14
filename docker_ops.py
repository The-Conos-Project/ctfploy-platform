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


def build_log_path(tag: str) -> str:
    return os.path.join(BUILD_LOGS_STORE, f"{tag}.log")


def build_image_thread(name: str, build_dir: str, tag: str, challenge_ids: list, class_id: Optional[str] = None) -> None:
    os.makedirs(BUILD_LOGS_STORE, exist_ok=True)
    log_path = build_log_path(tag)

    def write_log(log, message: str) -> None:
        log.write(message if message.endswith("\n") else f"{message}\n")
        log.flush()

    try:
        docker_client = get_docker_client()
        with open(log_path, "a", encoding="utf-8") as log:
            write_log(log, "Build started...")
            _, logs = docker_client.images.build(path=build_dir, tag=tag, rm=True, nocache=True, pull=True)
            for chunk in logs:
                if "stream" in chunk:
                    write_log(log, chunk["stream"])
                elif "error" in chunk:
                    write_log(log, f"ERROR: {chunk['error']}")
                elif "errorDetail" in chunk:
                    write_log(log, f"ERROR: {chunk['errorDetail'].get('message', chunk['errorDetail'])}")
            write_log(log, "Build completed successfully!")
        image = docker_client.images.get(tag)
        exposed = image.attrs.get("Config", {}).get("ExposedPorts") or {}
        ports = sorted(int(value.split("/", 1)[0]) for value in exposed if value.endswith("/tcp"))
        if not ports:
            raise RuntimeError("Challenge image must declare one TCP port with EXPOSE")
        internal_port = 22 if 22 in ports else ports[0]
        connection_type = "ssh" if internal_port == 22 else ("web" if internal_port in {80, 3000, 5000, 8000, 8080} else "nc")
        data = load_data()
        for ch in data["challenges"]:
            if ch["id"] in challenge_ids:
                ch["build_status"] = "ready"
        if class_id:
            for classroom in data["classes"]:
                if classroom["id"] == class_id:
                    for cid in challenge_ids:
                        if cid not in classroom["challenge_ids"]:
                            classroom["challenge_ids"].append(cid)
                    break
        save_data(data)
    except Exception as e:
        with open(log_path, "a", encoding="utf-8") as log:
            write_log(log, f"Build failed: {e}")
        data = load_data()
        for ch in data["challenges"]:
            if ch["id"] in challenge_ids:
                ch["build_status"] = "failed"
        save_data(data)
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)


def _package_name(image_tag: str) -> str:
    return image_tag[4:] if image_tag.startswith("ctf-") else image_tag


def _instance_environment(challenge: dict) -> dict:
    """Build container env vars.

    setup.sh treats an empty CHALLENGE_NAME as "set up the full lab". The
    platform used to always pass the package name (e.g. linux-trail), which
    skipped every station and then crashed on `chmod /opt/challenges`.
    Only pass CHALLENGE_NAME for a per-station variant whose name differs
    from the image package.
    """
    credentials = challenge.get("credentials") or {}
    username = str(credentials.get("username") or "").strip()
    password = str(credentials.get("password") or "")
    if not username or not password:
        raise RuntimeError("Challenge credentials are missing. Re-import a package with credentials.username and credentials.password.")
    env = {"CTF_USER": username, "CTF_PASSWORD": password}
    challenge_name = str(challenge.get("name") or "").strip()
    package = _package_name(challenge.get("image_tag") or "")
    if challenge_name and challenge_name != package:
        env["CHALLENGE_NAME"] = challenge_name
    return env


def _container_logs(container) -> str:
    try:
        return container.logs(tail=80).decode("utf-8", errors="replace")
    except Exception:
        return "unavailable"


def _cleanup_container(container) -> None:
    if container is None:
        return
    try:
        container.stop(timeout=3)
    except Exception:
        pass
    try:
        container.remove(force=True)
    except Exception:
        pass


def _published_port(container, internal_port: int) -> Optional[int]:
    ports_map = (container.attrs.get("NetworkSettings") or {}).get("Ports") or {}
    bindings = ports_map.get(f"{internal_port}/tcp") or []
    if not bindings:
        return None
    host_port = bindings[0].get("HostPort")
    return int(host_port) if host_port else None


def _wait_for_lab(container, connection_type: str, timeout: int = 30) -> Tuple[bool, str]:
    """Wait until the lab stays up. A first 'running' reading is not enough —
    linux-trail's entrypoint still runs setup.sh and can exit a second later.
    """
    deadline = time.time() + timeout
    saw_running = False
    while time.time() < deadline:
        try:
            container.reload()
        except docker.errors.NotFound:
            return False, "Container was removed while starting"
        status = container.status
        if status in {"exited", "dead", "removing"}:
            return False, f"Container {status} during startup"
        if status == "running":
            saw_running = True
            if connection_type == "ssh":
                try:
                    result = container.exec_run(
                        ["/bin/sh", "-c", "pgrep -x sshd >/dev/null 2>&1 || ss -lnt 2>/dev/null | grep -q ':22'"]
                    )
                    if result.exit_code == 0:
                        return True, ""
                except docker.errors.APIError as exc:
                    message = str(exc).lower()
                    if "not running" in message or "no such container" in message or "404" in message:
                        return False, "Container stopped during startup"
            else:
                return True, ""
        time.sleep(1)
    if saw_running:
        return True, ""
    return False, "Container failed to become ready in time"


def _provision_ssh_user(container, username: str, password: str) -> None:
    """Create the per-instance login account after an SSH image has started.

    Challenge images keep their own users and files intact.  This only adds the
    generated account advertised by the platform; images must include common
    Linux tools (`useradd`, `chpasswd`, and `/bin/sh`) for SSH mode.
    """
    command = (
        "set -eu; "
        f"id {username} >/dev/null 2>&1 || useradd -m -s /bin/bash {username}; "
        f"printf '%s:%s\\n' '{username}' '{password}' | chpasswd"
    )
    try:
        result = container.exec_run(["/bin/sh", "-c", command], user="root")
    except docker.errors.APIError as exc:
        if "already in progress" in str(exc) or "not running" in str(exc):
            try:
                logs = container.logs(tail=50).decode("utf-8", errors="replace")
            except Exception:
                logs = "unavailable"
            raise RuntimeError(f"Container stopped before SSH user could be created. Check container logs. Logs: {logs}") from exc
        raise
    if result.exit_code != 0:
        output = result.output.decode("utf-8", errors="replace").strip()
        raise RuntimeError(output or "could not create the generated SSH user")


def create_container(challenge: dict, user_id: str) -> Tuple[Optional[dict], Optional[str]]:
    data = load_data()
    user_instances = [i for i in data["instances"] if i["user_id"] == user_id and i["status"] == "running"]
    if len(user_instances) >= MAX_CONCURRENT_PER_USER:
        return None, "Maximum concurrent instances reached"

    image_tag = challenge["image_tag"]
    credentials = challenge.get("credentials") or {}
    username = str(credentials.get("username") or "")
    password = str(credentials.get("password") or "")
    env = _instance_environment(challenge)
    dyn_flag = None
    if challenge.get("flag_type") == "dynamic":
        dyn_flag = f"flag{{{uuid.uuid4()}}}"
        env["FLAG"] = dyn_flag

    container_name = f"ctf_{challenge['id']}_{int(time.time())}"
    container = None
    try:
        ensure_network()
        docker_client = get_docker_client()
        image = docker_client.images.get(f"{image_tag}:latest")
        exposed = image.attrs.get("Config", {}).get("ExposedPorts") or {}
        ports = sorted(int(value.split("/", 1)[0]) for value in exposed if value.endswith("/tcp"))
        if not ports:
            return None, "Challenge image must declare one TCP port with EXPOSE"
        internal_port = 22 if 22 in ports else ports[0]
        connection_type = "ssh" if internal_port == 22 else ("web" if internal_port in {80, 3000, 5000, 8000, 8080} else "nc")

        container = docker_client.containers.run(
            f"{image_tag}:latest",
            detach=True,
            name=container_name,
            ports={f"{internal_port}/tcp": None},
            environment=env,
            mem_limit="512m",
            nano_cpus=int(0.5 * 1e9),
            network=DOCKER_NETWORK,
            remove=False,
        )
        ready, reason = _wait_for_lab(container, connection_type)
        if not ready:
            logs = _container_logs(container)
            _cleanup_container(container)
            return None, f"{reason}. Logs: {logs}"

        port = None
        for _ in range(10):
            try:
                container.reload()
            except docker.errors.NotFound:
                return None, f"Container disappeared before a port was published. Logs: {_container_logs(container)}"
            port = _published_port(container, internal_port)
            if port:
                break
            time.sleep(0.5)
        if not port:
            logs = _container_logs(container)
            _cleanup_container(container)
            return None, f"Docker did not publish the challenge port. Logs: {logs}"
    except docker.errors.ImageNotFound:
        return None, f"Challenge image {image_tag}:latest was not found. Rebuild the challenge."
    except docker.errors.NotFound as e:
        logs = _container_logs(container)
        _cleanup_container(container)
        return None, f"Lab container vanished during start. Logs: {logs or e}"
    except Exception as e:
        logs = _container_logs(container)
        _cleanup_container(container)
        return None, f"Docker error: {e}. Logs: {logs}"

    instance = {
        "id": str(uuid.uuid4())[:8],
        "user_id": user_id,
        "challenge_id": challenge["id"],
        "container_id": container.id,
        "container_name": container_name,
        "host_port": port,
        "connection_type": connection_type,
        "status": "running",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(seconds=INSTANCE_TIMEOUT)).isoformat(),
        "dynamic_flag": dyn_flag,
        "flag": challenge.get("flag", ""),
        "submitted_flags": [],
        "attempt_counts": {},
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
    if not inst or inst["status"] != "running":
        return False
    try:
        container = get_docker_client().containers.get(inst["container_id"])
        container.stop(timeout=3)
    except docker.errors.NotFound:
        inst["status"] = "terminated"
        inst["terminated_at"] = datetime.now().isoformat()
        save_data(data)
        return True
    except docker.errors.APIError as exc:
        if "already in progress" in str(exc) or "not running" in str(exc) or "removal" in str(exc):
            inst["status"] = "terminated"
            inst["terminated_at"] = datetime.now().isoformat()
            save_data(data)
            return True
        return False
    try:
        container.remove(force=True)
    except Exception:
        pass
    inst["status"] = "terminated"
    inst["terminated_at"] = datetime.now().isoformat()
    save_data(data)
    return True


def auto_terminate(instance_id: str, delay: int) -> None:
    time.sleep(delay)
    terminate_instance(instance_id)
