from html import escape
from flask import redirect, request, session, url_for
from data_store import get_user_by_id, load_data, save_data
from docker_ops import create_container, terminate_instance
from challenge_meta import flag_specs, flag_values
from page_templates.dashboard import (
    dashboard_page,
    classes_page,
    class_detail_page,
    student_challenges_page,
    student_challenge_detail_page,
)
from views.utils import login_required, request_flash_messages


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
        expected = {f["flag"] for f in flag_specs(ch)}
        for inst in data["instances"]:
            if inst["user_id"] == user["id"] and inst["challenge_id"] == ch["id"]:
                submitted = set(inst.get("submitted_flags", []))
                if expected.issubset(submitted):
                    solved_count += 1
                    break

    active_instances = []
    for inst in data["instances"]:
        if inst["user_id"] == user["id"] and inst["status"] == "running":
            ch = next((c for c in data["challenges"] if c["id"] == inst["challenge_id"]), None)
            if ch:
                active_instances.append({"instance": inst, "challenge": ch})

    flashes = request_flash_messages()
    return dashboard_page(user, user_classes, active_instances, solved_count, len(challenges), flashes=flashes)


@login_required
def classes():
    data = load_data()
    user = get_user_by_id(session["user_id"])
    user_classes = [c for c in data["classes"] if user["id"] in c.get("member_ids", [])]
    return classes_page(user_classes, flashes=request_flash_messages())


@login_required
def class_detail(class_id: str):
    data = load_data()
    classroom = next((c for c in data["classes"] if c["id"] == class_id and session["user_id"] in c.get("member_ids", [])), None)
    if not classroom:
        return redirect(url_for("main.classes", error="Class not found"))
    challenges = [c for c in data["challenges"] if c["id"] in classroom.get("challenge_ids", [])]
    instances = [i for i in data["instances"] if i["user_id"] == session["user_id"] and i["status"] == "running"]
    return class_detail_page(classroom, challenges, instances, flashes=request_flash_messages())


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

    return student_challenges_page(challenges, instances, solved_challenge_ids, flashes=request_flash_messages())


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
    host = request.host.split(":")[0]

    return student_challenge_detail_page(challenge, instance, host, msg)


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

    rows = ''
    for ch in challenges:
        expected_flags = {f["flag"] for f in ch.get("flags", [])}
        solvers = []
        for inst in data["instances"]:
            if inst["challenge_id"] == ch["id"] and inst["status"] == "running":
                submitted = set(inst.get("submitted_flags", []))
                if expected_flags.issubset(submitted):
                    solver = get_user_by_id(inst["user_id"])
                    if solver:
                        solvers.append(solver["username"])
        solvers_html = ", ".join(escape(s) for s in solvers) if solvers else '<span class="small-text">No solvers yet</span>'
        rows += f'''<li><div class="row"><div><strong>{escape(ch['display_name'])}</strong><div class="small-text">{escape(ch.get('description', ''))}</div></div><div style="text-align:right;">{solvers_html}</div></div></li>'''
    return leaderboard_page(challenges, rows or '<li>No challenges assigned yet.</li>')


@login_required
def submit_flag(instance_id):
    data = load_data()
    instance = next((i for i in data["instances"] if i["id"] == instance_id and i["user_id"] == session["user_id"]), None)
    if not instance:
        return redirect(url_for("main.dashboard", error="Instance not found"))

    submitted = request.form["flag"].strip()
    challenge = next((c for c in data["challenges"] if c["id"] == instance["challenge_id"]), None)
    expected_flags = flag_values(challenge, instance.get("dynamic_flag"))

    flag_index = request.form.get("flag_index")
    if flag_index is not None:
        try:
            idx = int(flag_index)
            if idx < 0 or idx >= len(expected_flags):
                msg = "Invalid flag"
            elif submitted != expected_flags[idx]:
                msg = "Incorrect"
            elif submitted in instance.get("submitted_flags", []):
                msg = "Already submitted"
            else:
                instance.setdefault("submitted_flags", []).append(submitted)
                save_data(data)
                completed = len(set(instance["submitted_flags"]).intersection(expected_flags))
                msg = f"Accepted! {completed}/{len(expected_flags)} flags found"
        except ValueError:
            msg = "Invalid flag index"
    else:
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
