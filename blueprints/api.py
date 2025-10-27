from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    jsonify,
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from database.actions import get_user_by_email, get_user_by_username, create_user, list_all_users, list_all_groups, list_all_projects
from blueprints.auth import login_required, admin_required
import logging

api_bp = Blueprint("api", __name__)
logger = logging.getLogger(__name__)

@api_bp.route("/users", methods=["GET"])
@login_required
@admin_required
def list_users():
    """列出所有用户"""
    users = list_all_users()
    users_data = [
        {
            "uid": user.uid,
            "uname": user.uname,
            "email": user.email,
            "is_admin": user.is_admin,
            "gid": user.gid,
        }
        for user in users
    ]
    return jsonify(users_data)


@api_bp.route("/groups", methods=["GET"])
@login_required
@admin_required
def list_groups():
    """列出所有用户组"""
    groups = list_all_groups()
    groups_data = [
        {
            "gid": group.gid,
            "gname": group.gname,
            "ginfo": group.ginfo,
            "leader_id": group.leader_id,
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
            "docker_id": project.docker_id,
            "port": project.port,
            "docker_port": project.docker_port,
        }
        for project in projects
    ]
    return jsonify(projects_data)