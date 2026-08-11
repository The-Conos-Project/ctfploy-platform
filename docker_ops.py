import os, time, random, uuid, threading, queue
from datetime import datetime, timedelta
from typing import Optional, Tuple
import docker

from config import DOCKER_NETWORK, INSTANCE_TIMEOUT, MAX_CONCURRENT_PER_USER
from data_store import load_data, save_data

docker_client = docker.from_env()
build_logs = {}


def ensure_network() -> None:
    try:
        docker_client.networks.get(DOCKER_NETWORK)
    except docker.errors.NotFound:
        docker_client.networks.create(DOCKER_NETWORK, driver="bridge")


def build_image_thread(name: str, build_dir: str, tag: str, challenge_id: str) -> None:
    q = build_logs.get(challenge_id)
    if not q:
        q = queue.Queue()
        build_logs[challenge_id] = q
    try:
        q.put("Build started...\n")
        img, logs = docker_client.images.build(path=build_dir, tag=tag, rm=True)
        for chunk in logs:
            if "stream" in chunk:
                q.put(chunk["stream"])
            elif "error" in chunk:
                q.put(f"ERROR: {chunk['error']}\n")
        q.put("Build completed successfully!\n")
        data = load_data()
        for ch in data["challenges"]:
            if ch["id"] == challenge_id:
                ch["build_status"] = "success"
        save_data(data)
    except Exception as e:
        q.put(f"Build failed: {str(e)}\n")
        data = load_data()
        for ch in data["challenges"]:
            if ch["id"] == challenge_id:
                ch["build_status"] = "failed"
        save_data(data)
    finally:
        q.put(None)


def _random_credentials() -> Tuple[str, str]:
    username = f"ctf_{uuid.uuid4().hex[:8]}"
    password = uuid.uuid4().hex[:12]
    return username, password


def create_container(challenge: dict, user_id: str) -> Tuple[Optional[dict], Optional[str]]:
    data = load_data()
    user_instances = [i for i in data["instances"] if i["user_id"] == user_id and i["status"] == "running"]
    if len(user_instances) >= MAX_CONCURRENT_PER_USER:
        return None, "Maximum concurrent instances reached"

    port = random.randint(10000, 60000)
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
        container = docker_client.containers.run(
            f"{image_tag}:latest",
            detach=True,
            name=container_name,
            ports={f"{internal_port}/tcp": port},
            environment=env,
            mem_limit="512m",
            nano_cpus=int(0.5 * 1e9),
            network=DOCKER_NETWORK,
            remove=True
        )
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
            container = docker_client.containers.get(inst["container_id"])
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
    from flask import current_app
    with current_app.app_context():
        terminate_instance(instance_id)
