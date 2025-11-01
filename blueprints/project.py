from functools import wraps
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    abort,
    jsonify,
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from database.actions import *
import logging

# 项目蓝图
project_bp = Blueprint("project", __name__)
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------------------------
# Project Forms
# -------------------------------------------------------------------------------------------
class ProjectForm(FlaskForm):
    pname = StringField("项目名称", validators=[DataRequired(), Length(min=3, max=100)])
    pinfo = TextAreaField("项目描述", validators=[Length(max=5000)])
    port = StringField("项目端口", validators=[DataRequired(), Length(min=2, max=10)])
    docker_port = StringField(
        "Docker端口", validators=[DataRequired(), Length(min=2, max=10)]
    )
    submit = SubmitField("保存")

    # 自定义验证器
    def validate_port(self, port):
        if not port.data.isdigit() or not (10000 <= int(port.data) <= 65535):
            raise ValidationError("端口号必须是10000到65535之间的数字")

    def validate_docker_port(self, docker_port):
        if not docker_port.data.isdigit() or not (1024 <= int(docker_port.data) <= 65535):
            raise ValidationError("Docker端口号必须是1024到65535之间的数字")


# -------------------------------------------------------------------------------------------
# Group Decorators
# -------------------------------------------------------------------------------------------
def group_required_pid(func):
    """工作组成员权限装饰器"""

    @wraps(func)
    def decorated(*args, **kwargs):
        pid = str(kwargs.get("pid"))
        project = get_project_by_pid(pid)
        if not project:
            abort(404, description="项目不存在")
        if any(
            [
                not current_user.is_authenticated,
                not current_user.gid,
                str(current_user.gid) != str(project.gid),
            ]
        ):
            abort(403, description="需要工作组成员权限才能访问此页面")
        return func(*args, **kwargs)

    return decorated


# -------------------------------------------------------------------------------------------
# Project Views
# -------------------------------------------------------------------------------------------
@project_bp.route("/", methods=["GET"])
def project_list():
    """项目列表页面"""
    projects = list_all_projects()
    return render_template("project/list.html", projects=projects)


# TODO: project details
@project_bp.route("/<uuid:pid>", methods=["GET"])
def project_detail(pid):
    """项目详情页面"""
    project = get_project_by_pid(pid)
    if not project:
        abort(404, description="项目不存在")
    return render_template("project/detail.html", project=project)


# -------------------------------------------------------------------------------------------
# Project Actions
# -------------------------------------------------------------------------------------------
@project_bp.route("/<uuid:pid>/edit", methods=["GET", "POST"])
@login_required
@group_required_pid
def project_edit(pid):
    """项目编辑页面"""
    pid = str(pid)
    project = get_project_by_pid(pid)
    if not project:
        flash("项目不存在", "warning")
        abort(404, description="项目不存在")

    form = ProjectForm(obj=project)
    if form.validate_on_submit():
        updated_project = update_project(
            project,
            pname=form.pname.data,
            pinfo=form.pinfo.data,
            port=form.port.data,
            docker_port=form.docker_port.data,
        )
        if not updated_project:
            flash("更新项目失败，请重试", "danger")
            logger.warning(f"更新项目失败: {form.pname.data}")
            return render_template("project/edit.html", form=form, project=project)
        flash("项目更新成功", "success")
        logger.info(f"更新项目成功: {form.pname.data} by user {current_user.uname}")
        return redirect(url_for("project.project_detail", pid=pid))
    return render_template("project/edit.html", form=form, project=project)


# TODO: terminal

# TODO: iframe 或者别的实现方法
