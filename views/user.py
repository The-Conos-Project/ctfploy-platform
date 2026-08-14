from html import escape
from flask import redirect, request, session, url_for
from data_store import get_user_by_id, load_data, save_data
from docker_ops import create_container, terminate_instance
from domain_ops import public_ip
from challenge_meta import flag_specs, flag_values, total_points
from page_templates.dashboard import (
    dashboard_page,
    classes_page,
    class_detail_page,
    student_challenges_page,
    student_challenge_detail_page,
    leaderboard_page,
)
from views.utils import login_required, request_toast_messages


@login_required
def dashboard():
    data = load_data()
    user = get_user_by_id(session["user_id"])
    user_classes = [c for c in data["classes"] if user["id"] in c.get("member_ids", [])]

    # Calculate solved count and total count across assigned challenges
    assigned_challenge_ids = set()
    for c in user_classes:
        assigned_challenge_ids.update(c.get("challenge_ids", []))

    challenges = [ch for ch in data["challenges"] if ch["id"] in assigned_challenge_ids]
    solved_count = 0
    for ch in challenges:
        for inst in data["instances"]:
            if inst["user_id"] == user["id"] and inst["challenge_id"] == ch["id"]:
                expected = flag_values(ch, inst.get("dynamic_flag"))
                submitted = set(inst.get("submitted_flags", []))
                if set(expected).issubset(submitted):
                    solved_count += 1
                    break

    active_instances = []
    for inst in data["instances"]:
        if inst["user_id"] == user["id"] and inst["status"] == "running":
            ch = next((c for c in data["challenges"] if c["id"] == inst["challenge_id"]), None)
            if ch:
                active_instances.append({"instance": inst, "challenge": ch})

    flashes = request_toast_messages()
    return dashboard_page(user, user_classes, active_instances, solved_count, len(challenges), toasts=flashes)


@login_required
def classes():
    data = load_data()
    user = get_user_by_id(session["user_id"])
    user_classes = [c for c in data["classes"] if user["id"] in c.get("member_ids", [])]
    return classes_page(user_classes, toasts=request_toast_messages())


@login_required
def class_detail(class_id: str):
    data = load_data()
    classroom = next((c for c in data["classes"] if c["id"] == class_id and session["user_id"] in c.get("member_ids", [])), None)
    if not classroom:
        return redirect(url_for("main.classes", error="Class not found"))
    challenges = [c for c in data["challenges"] if c["id"] in classroom.get("challenge_ids", [])]
    instances = [i for i in data["instances"] if i["user_id"] == session["user_id"] and i["status"] == "running"]
    return class_detail_page(classroom, challenges, instances, toasts=request_toast_messages())


@login_required
def student_challenges():
    data = load_data()
    user = get_user_by_id(session["user_id"])

    # Get all challenge IDs assigned to classes the user belongs to
    user_classes = [c for c in data["classes"] if user["id"] in c.get("member_ids", [])]
    assigned_challenge_ids = set()
    for c in user_classes:
        assigned_challenge_ids.update(c.get("challenge_ids", []))

    challenges = [c for c in data["challenges"] if c["id"] in assigned_challenge_ids]
    instances = [i for i in data["instances"] if i["user_id"] == user["id"] and i["status"] == "running"]

    # Calculate solved challenge IDs
    solved_challenge_ids = set()
    for ch in challenges:
        expected = {f["flag"] for f in flag_specs(ch)}
        for inst in data["instances"]:
            if inst["user_id"] == user["id"] and inst["challenge_id"] == ch["id"]:
                submitted = set(inst.get("submitted_flags", []))
                if expected.issubset(submitted):
                    solved_challenge_ids.add(ch["id"])
                    break

    return student_challenges_page(challenges, instances, solved_challenge_ids, toasts=request_toast_messages())


@login_required
def student_challenge_detail(challenge_id: str):
    data = load_data()
    user = get_user_by_id(session["user_id"])

    allowed = any(
        challenge_id in c.get("challenge_ids", []) and user["id"] in c.get("member_ids", [])
        for c in data["classes"]
    )
    if not allowed:
        return redirect(url_for("main.dashboard", error="Access denied"))

    challenge = next((c for c in data["challenges"] if c["id"] == challenge_id), None)
    if not challenge:
        return redirect(url_for("main.dashboard", error="Challenge not found"))

    instance = next(
        (i for i in data["instances"] if i["challenge_id"] == challenge_id and i["user_id"] == user["id"] and i["status"] == "running"),
        None
    )

    msg = request.args.get("msg") or request.args.get("success") or request.args.get("error")
    host = public_ip()

    attempts_remaining = {}
    for index, spec in enumerate(flag_specs(challenge)):
        used = sum(
            int((item.get("attempt_counts") or {}).get(str(index), 0))
            for item in data["instances"]
            if item.get("user_id") == user["id"] and item.get("challenge_id") == challenge_id
        )
        attempts_remaining[index] = max(0, spec["max_attempts"] - used)
    return student_challenge_detail_page(
        challenge,
        instance,
        host,
        msg,
        attempts_remaining=attempts_remaining,
        expires_at=instance.get("expires_at") if instance else None,
    )


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
def start_challenge(challenge_id):
    data = load_data()
    user = get_user_by_id(session["user_id"])
    challenge = next((c for c in data["challenges"] if c["id"] == challenge_id and c["build_status"] == "ready"), None)
    if not challenge:
        return redirect(url_for("main.student_challenge_detail", challenge_id=challenge_id, error="Challenge not found or not ready"))

    allowed = any(challenge_id in classroom.get("challenge_ids", []) and user["id"] in classroom.get("member_ids", []) for classroom in data["classes"])
    if not allowed:
        return redirect(url_for("main.dashboard", error="Access denied"))

    instance, err = create_container(challenge, user["id"])
    if err:
        return redirect(url_for("main.student_challenge_detail", challenge_id=challenge_id, error=err))
    return redirect(url_for("main.student_challenge_detail", challenge_id=challenge_id))


@login_required
def view_instance(instance_id):
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if not instance:
        return redirect(url_for("main.dashboard", error="Instance not found"))

    challenge = next((c for c in data["challenges"] if c["id"] == instance["challenge_id"]), None)
    if challenge:
        return redirect(url_for("main.student_challenge_detail", challenge_id=instance["challenge_id"], **request.args))
    return redirect(url_for("main.dashboard"))


@login_required
def terminate(instance_id):
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if instance:
        terminate_instance(instance_id)
        return redirect(url_for("main.student_challenge_detail", challenge_id=instance["challenge_id"], success="Lab terminated"))
    return redirect(url_for("main.dashboard"))


@login_required
def leaderboard():
    data = load_data()
    user = get_user_by_id(session["user_id"])
    user_classes = [c for c in data["classes"] if user["id"] in c.get("member_ids", [])]
    assigned_challenge_ids = set()
    for c in user_classes:
        assigned_challenge_ids.update(c.get("challenge_ids", []))
    challenges = [ch for ch in data["challenges"] if ch["id"] in assigned_challenge_ids]

    scores = {}
    for participant in data["users"]:
        submitted_by_challenge = {}
        for inst in data["instances"]:
            if inst.get("user_id") == participant["id"] and inst.get("challenge_id") in assigned_challenge_ids:
                submitted_by_challenge.setdefault(inst["challenge_id"], set()).update(inst.get("submitted_flags", []))
        points = 0
        solved = 0
        for challenge in challenges:
            solved_flags = submitted_by_challenge.get(challenge["id"], set())
            awarded = [spec for spec in flag_specs(challenge) if spec["flag"] in solved_flags]
            points += sum(spec["points"] for spec in awarded)
            if len(awarded) == len(flag_specs(challenge)) and awarded:
                solved += 1
        if points:
            scores[participant["id"]] = {"username": participant["username"], "points": points, "solved": solved}
    ordered = sorted(scores.values(), key=lambda row: (-row["points"], -row["solved"], row["username"].lower()))
    return leaderboard_page(ordered)


@login_required
def submit_flag(instance_id):
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if not instance:
        return redirect(url_for("main.dashboard", error="Instance not found"))

    submitted = request.form["flag"].strip()
    challenge = next((c for c in data["challenges"] if c["id"] == instance["challenge_id"]), None)
    specs = flag_specs(challenge)
    expected_flags = flag_values(challenge, instance.get("dynamic_flag"))

    flag_index = request.form.get("flag_index")
    if flag_index is not None:
        try:
            idx = int(flag_index)
            if idx < 0 or idx >= len(expected_flags):
                msg = "Invalid flag"
            elif submitted in instance.get("submitted_flags", []):
                msg = "Already submitted"
            elif idx < len(specs) and _attempts_used(data, session["user_id"], challenge["id"], idx) >= specs[idx]["max_attempts"]:
                msg = "No attempts remaining for this flag"
            elif submitted != expected_flags[idx]:
                _record_attempt(instance, idx)
                save_data(data)
                msg = "Incorrect"
            else:
                instance.setdefault("submitted_flags", []).append(submitted)
                save_data(data)
                completed = len(set(instance["submitted_flags"]).intersection(expected_flags))
                msg = f"Accepted! {completed}/{len(expected_flags)} flags found"
        except ValueError:
            msg = "Invalid flag index"
    else:
        msg = "Invalid flag index"
    return redirect(url_for("main.view_instance", instance_id=instance_id, msg=msg))


def _attempts_used(data: dict, user_id: str, challenge_id: str, flag_index: int) -> int:
    return sum(
        int((instance.get("attempt_counts") or {}).get(str(flag_index), 0))
        for instance in data["instances"]
        if instance.get("user_id") == user_id and instance.get("challenge_id") == challenge_id
    )


def _record_attempt(instance: dict, flag_index: int) -> None:
    counts = instance.setdefault("attempt_counts", {})
    key = str(flag_index)
    counts[key] = int(counts.get(key, 0)) + 1
