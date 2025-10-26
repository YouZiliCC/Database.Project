from functools import wraps
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
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from database.actions import *
import logging

group_bp = Blueprint("group", __name__)
logger = logging.getLogger(__name__)


def group_required(func):
    """用户组成员权限装饰器"""
    @wraps(func)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.gid:
            flash("需要成为组成员才能访问此页面", "warning")
            return redirect(url_for("index.index"))
        return func(*args, **kwargs)
    return decorated


@group_bp.route("/my_group", methods=["GET"])
@login_required
@group_required
def my_group():
    """当前用户所属用户组页面"""
    group = get_group_by_id(current_user.gid)
    if not group:
        flash("您所属的用户组不存在", "warning")
        return redirect(url_for("index.index"))
    return redirect(url_for("group.group_detail", group_id=group.gid))


@group_bp.route("/<uuid:group_id>", methods=["GET"])
@login_required
@group_required
def group_detail(group_id):
    """用户组详情页面"""
    group = get_group_by_id(group_id)
    if not group:
        flash("用户组不存在", "warning")
        return redirect(url_for("index.groups"))
    if current_user.gid != str(group_id) and not current_user.is_admin:
        flash("您无权查看此用户组的详情", "warning")
        return redirect(url_for("index.groups"))
    return render_template("group/detail.html", group=group)

# edit