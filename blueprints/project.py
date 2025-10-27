from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from database.actions import get_user_by_email, get_user_by_username, create_user, list_all_projects
from blueprints.group import group_required, leader_required
import logging

# 项目蓝图
project_bp = Blueprint("project", __name__)
logger = logging.getLogger(__name__)

# details

@project_bp.route("/projects", methods=["GET"])
def projects():
    """项目列表页面"""
    projects = list_all_projects()
    return render_template("project/list.html", projects=projects)
# terminal

# iframe
