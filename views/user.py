import uuid
from flask import redirect, request, session, url_for
from data_store import get_user_by_id, load_data, save_data
from docker_ops import create_container, terminate_instance
from page_templates.dashboard import dashboard_page
from page_templates.instance import instance_page
from views.utils import login_required, request_flash_messages


def dashboard():
    data = load_data()
    user = get_user_by_id(session["user_id"])
    user_classes = [c for c in data["classes"] if user["id"] in c.get("member_ids", [])]
    user_challenges = []
    for classroom in user_classes:
        for cid in classroom.get("challenge_ids", []):
            ch = next((c for c in data["challenges"] if c["id"] == cid and c["build_status"] == "success"), None)
            if ch and ch not in user_challenges:
                user_challenges.append(ch)
    # Preserve access granted through legacy access codes.
    for code in data["access_codes"]:
        if code["code"] in user.get("used_codes", []):
            for cid in code["challenges"]:
                ch = next((c for c in data["challenges"] if c["id"] == cid), None)
                if ch and ch["build_status"] == "success" and ch not in user_challenges:
                    user_challenges.append(ch)

    instances = [i for i in data["instances"] if i["user_id"] == user["id"] and i["status"] == "running"]

    def get_instance(uid, cid):
        return next((i for i in instances if i["user_id"] == uid and i["challenge_id"] == cid), None)

    flashes = request_flash_messages()
    return dashboard_page(user, user_classes, user_challenges, get_instance, flashes=flashes)


@login_required
def join_class():
    code = request.form.get("code", "").strip().upper()
    data = load_data()
    classroom = next((c for c in data["classes"] if c["join_code"] == code), None)
    if not classroom:
        return redirect(url_for("main.dashboard", error="Invalid class code"))
    if session["user_id"] not in classroom["member_ids"]:
        classroom["member_ids"].append(session["user_id"])
        save_data(data)
    return redirect(url_for("main.dashboard", success=f"Joined {classroom['name']}"))


@login_required
def redeem_code():
    code = request.form["code"].strip()
    data = load_data()
    code_entry = next((c for c in data["access_codes"] if c["code"] == code), None)
    if not code_entry:
        return redirect(url_for("main.dashboard", error="Invalid code"))

    user = next((u for u in data["users"] if u["id"] == session["user_id"]), None)
    if not user:
        return redirect(url_for("main.dashboard", error="User not found"))

    if code in user.get("used_codes", []):
        return redirect(url_for("main.dashboard", error="You have already used this code."))

    user.setdefault("used_codes", []).append(code)
    username = user["username"]
    if username not in code_entry.get("used_by", []):
        code_entry.setdefault("used_by", []).append(username)
    save_data(data)
    return redirect(url_for("main.dashboard", success="Code unlocked successfully!"))


@login_required
def start_challenge(challenge_id):
    data = load_data()
    user = get_user_by_id(session["user_id"])
    challenge = next((c for c in data["challenges"] if c["id"] == challenge_id and c["build_status"] == "success"), None)
    if not challenge:
        return redirect(url_for("main.dashboard", error="Challenge not found or not ready"))

    allowed = any(
        challenge_id in classroom.get("challenge_ids", []) and user["id"] in classroom.get("member_ids", [])
        for classroom in data["classes"]
    ) or any(challenge_id in code.get("challenges", []) and code["code"] in user.get("used_codes", []) for code in data["access_codes"])
    if not allowed:
        return redirect(url_for("main.dashboard", error="Access denied"))

    instance, err = create_container(challenge, user["id"])
    if err:
        return redirect(url_for("main.dashboard", error=err))
    return redirect(url_for("main.view_instance", instance_id=instance["id"]))


@login_required
def view_instance(instance_id):
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if not instance:
        return redirect(url_for("main.dashboard", error="Instance not found"))

    challenge = next((c for c in data["challenges"] if c["id"] == instance["challenge_id"]), None)
    host = request.host.split(":")[0]
    msg = request.args.get("msg") or request.args.get("success") or request.args.get("error")
    hints = challenge.get("hints", []) if challenge else []
    expected_flags = [instance.get("dynamic_flag")] if challenge and challenge.get("flag_type") == "dynamic" else (challenge.get("flags") or [challenge.get("flag")])
    expected_flags = [flag for flag in expected_flags if flag]
    submitted_flags = set(instance.get("submitted_flags", []))
    progress = (len(submitted_flags.intersection(expected_flags)), len(expected_flags))
    return instance_page(challenge, instance, host, msg, hints, progress)


@login_required
def terminate(instance_id):
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if instance:
        terminate_instance(instance_id)
    return redirect(url_for("main.dashboard"))


@login_required
def submit_flag(instance_id):
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if not instance:
        return redirect(url_for("main.dashboard", error="Instance not found"))

    submitted = request.form["flag"].strip()
    challenge = next((c for c in data["challenges"] if c["id"] == instance["challenge_id"]), None)
    expected_flags = [instance.get("dynamic_flag")] if challenge and challenge.get("flag_type") == "dynamic" else (challenge.get("flags") or [challenge.get("flag")])
    expected_flags = [flag for flag in expected_flags if flag]
    if submitted not in expected_flags:
        msg = "Incorrect"
    elif submitted in instance.get("submitted_flags", []):
        msg = "Already submitted"
    else:
        instance.setdefault("submitted_flags", []).append(submitted)
        save_data(data)
        completed = len(set(instance["submitted_flags"]).intersection(expected_flags))
        msg = f"Accepted! {completed}/{len(expected_flags)} flags found"
    return redirect(url_for("main.view_instance", instance_id=instance_id, msg=msg))
