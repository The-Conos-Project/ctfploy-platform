import os
from flask import Blueprint
from config import CHALLENGES_STORE
from docker_ops import ensure_network
from views.auth import index, sign_in, register, logout, admin_sign_in, admin_logout
from views.user import (
    dashboard,
    classes,
    class_detail,
    join_class,
    start_challenge,
    view_instance,
    terminate,
    submit_flag,
    student_challenges,
    student_challenge_detail,
    leaderboard,
    change_password,
    reset_password_request,
    api_labs,
    extend_lab,
)
from views.admin import (
    admin_dashboard,
    admin_challenges,
    import_url,
    build_log_view,
    build_log_stream,
    delete_challenge,
    update_challenge,
    admin_class_detail,
    admin_update,
    admin_domain,
    save_domain,
    create_domain_certificate,
    admin_classes,
    create_class,
    assign_challenge_to_class,
    delete_class,
    remove_challenge_from_class,
    admin_settings,
    admin_users,
    admin_reset_password,
    admin_join_class,
    remove_student_from_class,
    admin_leaderboard,
)

bp = Blueprint("main", __name__)

bp.add_url_rule("/", "index", index)
bp.add_url_rule("/sign-in", "sign_in", sign_in, methods=["GET", "POST"])
bp.add_url_rule("/sign-up", "register", register, methods=["GET", "POST"])
bp.add_url_rule("/logout", "logout", logout)

bp.add_url_rule("/dashboard", "dashboard", dashboard)
bp.add_url_rule("/classes", "classes", classes)
bp.add_url_rule("/classes/<class_id>", "class_detail", class_detail)
bp.add_url_rule("/challenges", "student_challenges", student_challenges)
bp.add_url_rule("/challenges/<challenge_id>", "student_challenge_detail", student_challenge_detail)
bp.add_url_rule("/api/labs", "api_labs", api_labs)
bp.add_url_rule("/leaderboard", "leaderboard", leaderboard)
bp.add_url_rule("/api/leaderboard", "api_leaderboard", leaderboard)
bp.add_url_rule("/user/join-class", "join_class", join_class, methods=["POST"])
bp.add_url_rule("/start/<challenge_id>", "start_challenge", start_challenge)
bp.add_url_rule("/instance/<instance_id>", "view_instance", view_instance)
bp.add_url_rule("/terminate/<instance_id>", "terminate", terminate)
bp.add_url_rule("/extend/<instance_id>", "extend_lab", extend_lab, methods=["POST"])
bp.add_url_rule("/submit_flag/<instance_id>", "submit_flag", submit_flag, methods=["POST"])
bp.add_url_rule("/change-password", "change_password", change_password, methods=["GET", "POST"])
bp.add_url_rule("/reset-password", "reset_password_request", reset_password_request, methods=["GET", "POST"])

bp.add_url_rule("/admin/sign-in", "admin_sign_in", admin_sign_in, methods=["GET", "POST"])
bp.add_url_rule("/admin/logout", "admin_logout", admin_logout)
bp.add_url_rule("/admin", "admin_dashboard", admin_dashboard)
bp.add_url_rule("/admin/challenges", "admin_challenges", admin_challenges)
bp.add_url_rule("/admin/import-url", "import_url", import_url, methods=["POST"])
bp.add_url_rule("/admin/build_log/<challenge_id>", "build_log_view", build_log_view)
bp.add_url_rule("/admin/build_log_stream/<challenge_id>", "build_log_stream", build_log_stream)
bp.add_url_rule("/admin/delete_challenge/<challenge_id>", "delete_challenge", delete_challenge)
bp.add_url_rule("/admin/update_challenge/<challenge_id>", "update_challenge", update_challenge, methods=["POST"])
bp.add_url_rule("/admin/classes", "admin_classes", admin_classes)
bp.add_url_rule("/admin/classes/<class_id>", "admin_class_detail", admin_class_detail)
bp.add_url_rule("/admin/classes/create", "create_class", create_class, methods=["POST"])
bp.add_url_rule("/admin/classes/assign", "assign_challenge_to_class", assign_challenge_to_class, methods=["POST"])
bp.add_url_rule("/admin/classes/delete/<class_id>", "delete_class", delete_class, methods=["POST"])
bp.add_url_rule("/admin/classes/remove_challenge", "remove_challenge_from_class", remove_challenge_from_class, methods=["POST"])
bp.add_url_rule("/admin/classes/remove-student", "remove_student_from_class", remove_student_from_class, methods=["POST"])
bp.add_url_rule("/admin/classes/join", "admin_join_class", admin_join_class, methods=["POST"])
bp.add_url_rule("/admin/update", "admin_update", admin_update, methods=["GET", "POST"])
bp.add_url_rule("/admin/domain", "admin_domain", admin_domain)
bp.add_url_rule("/admin/domain", "save_domain", save_domain, methods=["POST"])
bp.add_url_rule("/admin/domain/certificate", "create_domain_certificate", create_domain_certificate, methods=["POST"])
bp.add_url_rule("/admin/settings", "admin_settings", admin_settings)
bp.add_url_rule("/admin/users", "admin_users", admin_users)
bp.add_url_rule("/admin/users/reset-password", "admin_reset_password", admin_reset_password, methods=["POST"])
bp.add_url_rule("/admin/leaderboard", "admin_leaderboard", admin_leaderboard)
