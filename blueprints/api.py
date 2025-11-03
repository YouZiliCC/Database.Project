from flask import (
    Blueprint,
    jsonify,
)
from flask_login import login_user, logout_user, login_required, current_user
from database.actions import *
from blueprints.auth import login_required
from blueprints.admin import admin_required
import logging

api_bp = Blueprint("api", __name__)
logger = logging.getLogger(__name__)


@api_bp.route("/users", methods=["GET"])
@login_required
@admin_required
def api_users():
    """列出所有用户"""
    users = list_all_users()
    users_data = [
        {
            "uid": user.uid,
            "uname": user.uname,
            "sid": user.sid,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_teacher": user.is_teacher,
            "gid": user.gid,
        }
        for user in users
    ]
    return jsonify(users_data)


@api_bp.route("/groups", methods=["GET"])
@login_required
@admin_required
def api_groups():
    """列出所有工作组"""
    groups = list_all_groups()
    groups_data = [
        {
            "gid": group.gid,
            "gname": group.gname,
            "ginfo": group.ginfo,
            "leader_id": group.leader_id,
            "users": [user.uname for user in group.users],
            "projects": [project.pname for project in group.projects],
        }
        for group in groups
    ]
    return jsonify(groups_data)


@api_bp.route("/projects", methods=["GET"])
@login_required
@admin_required
def list_projects():
    """列出所有项目"""
    projects = list_all_projects()
    projects_data = [
        {
            "pid": project.pid,
            "pname": project.pname,
            "gid": project.gid,
            "gname": project.group.gname,
            "docker_name": project.docker_name,
            "port": project.port,
            "docker_port": project.docker_port,
            "star_count": len(project.stars),
        }
        for project in projects
    ]
    return jsonify(projects_data)
