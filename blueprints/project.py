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


class ProjectForm(FlaskForm):
    pname = StringField(
        "项目名称", validators=[DataRequired(), Length(min=3, max=100)]
    )
    pinfo = StringField("项目描述", validators=[Length(max=500)])
    port = StringField(
        "项目端口", validators=[DataRequired(), Length(min=2, max=10)]
    )
    docker_port = StringField(
        "Docker端口", validators=[DataRequired(), Length(min=2, max=10)]
    )
    submit = SubmitField("保存")

    # 自定义验证器
    def validate_port(self, port):
        if not port.data.isdigit() or not (1 <= int(port.data) <= 65535):
            raise ValidationError("端口号必须是1到65535之间的数字")

    def validate_docker_port(self, docker_port):
        if not docker_port.data.isdigit() or not (1 <= int(docker_port.data) <= 65535):
            raise ValidationError("Docker端口号必须是1到65535之间的数字")


@project_bp.route("/", methods=["GET"])
def project_list():
    """项目列表页面"""
    projects = list_all_projects()
    return render_template("project/list.html", projects=projects)


# TODO: project details
@project_bp.route("/<uuid:pid>", methods=["GET"])
def project_detail(pid):
    """项目详情页面"""
    project = get_group_by_pid(pid)
    if not project:
        abort(404, description="项目不存在")
    return render_template("project/detail.html", project=project)


# TODO: terminal

# TODO: iframe 或者别的实现方法
