from functools import wraps
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    jsonify,
    abort,
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from database.actions import *
import logging

group_bp = Blueprint("group", __name__)
logger = logging.getLogger(__name__)


class GroupForm(FlaskForm):
    gname = StringField("用户组名称", validators=[DataRequired(), Length(min=3, max=50)])
    ginfo = StringField("用户组描述", validators=[Length(max=200)])
    submit = SubmitField("保存")


def group_required(func):
    """用户组成员权限装饰器"""
    @wraps(func)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.gid:
            abort(403, description="需要用户组成员权限才能访问此页面")
        return func(*args, **kwargs)
    return decorated


@group_bp.route("/", methods=["GET"])
def group_list():
    """用户组列表页面"""
    groups = list_all_groups()
    return render_template("group/list.html", groups=groups)


@group_bp.route("/create", methods=["GET", "POST"])
@login_required
def group_create():
    """创建用户组页面"""
    form = GroupForm()
    if form.validate_on_submit():
        group = create_group(
            gname=form.gname.data,
            ginfo=form.ginfo.data,
            leader_id=current_user.uid,
        )
        if not group:
            flash("创建用户组失败，请重试", "danger")
            logger.warning(f"创建用户组失败: {form.gname.data}")
            return render_template("group/create.html", form=form)
        # 将当前用户加入新创建的用户组
        if not update_user(current_user, gid=group.gid):
            flash("将用户加入用户组失败，请联系管理员", "danger")
            logger.error(f"将用户 {current_user.username} 加入用户组 {group.gname} 失败")
            return render_template("group/create.html", form=form)
        flash("用户组创建成功！您已成为该组成员", "success")
        logger.info(f"创建用户组成功: {form.gname.data} by user {current_user.username}")
        return redirect(url_for("group.group_detail", group_id=group.gid))
    return render_template("group/create.html", form=form)


@group_bp.route("/my_group", methods=["GET"])
@login_required
@group_required
def my_group():
    """当前用户所属用户组页面"""
    group = get_group_by_id(current_user.gid)
    if not group:
        abort(404, description="您所属的用户组不存在")
    return redirect(url_for("group.group_detail", group_id=group.gid))


@group_bp.route("/<uuid:group_id>", methods=["GET"])
@login_required
def group_detail(group_id):
    """用户组详情页面"""
    group = get_group_by_id(group_id)
    if not group:
        abort(404, description="用户组不存在")
    return render_template("group/detail.html", group=group)


# TODO: 模态窗口
@group_bp.route("/<uuid:group_id>/edit", methods=["GET", "POST"])
@login_required
@group_required
def group_edit(group_id):
    """用户组编辑页面"""
    group = get_group_by_id(group_id)
    if not group:
        flash("用户组不存在", "warning")
        return jsonify({"error": "用户组不存在"}), 404
    if current_user.gid != str(group_id) and not current_user.is_admin:
        flash("您无权编辑此用户组", "warning")
        return jsonify({"error": "无权编辑此用户组"}), 403
    form = GroupForm(obj=group)
    if form.validate_on_submit():
        updated_group = update_group(
            group,
            gname=form.gname.data,
            ginfo=form.ginfo.data,
        )
        if not updated_group:
            flash("更新用户组信息失败，请重试", "danger")
            logger.warning(f"更新用户组信息失败: {form.gname.data}")
            return jsonify({"error": "更新用户组信息失败"}), 500
        flash("用户组信息更新成功", "success")
        logger.info(f"更新用户组信息成功: {form.gname.data} by user {current_user.username}")
        return jsonify({"message": "用户组信息更新成功"}), 200
    return render_template("group/edit.html", form=form, group=group)
    