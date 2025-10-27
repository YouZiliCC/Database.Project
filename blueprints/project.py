from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    abort,
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from database.actions import *
from blueprints.group import group_required, leader_required
import logging

# 项目蓝图
project_bp = Blueprint("project", __name__)
logger = logging.getLogger(__name__)

# details

@project_bp.route("/", methods=["GET"])
def project_list():
    """项目列表页面"""
    projects = list_all_projects()
    return render_template("project/list.html", projects=projects)


#TODO: project details
@project_bp.route("/<uuid:pid>", methods=["GET"])
def project_detail(pid):
    """项目详情页面"""
    project = get_project_by_id(pid)
    if not project:
        abort(404, description="项目不存在")
    return render_template("project/detail.html", project=project)

#TODO: terminal

#TODO: iframe
