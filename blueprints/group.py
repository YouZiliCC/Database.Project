from functools import wraps
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    jsonify,
    abort,
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length
from database.actions import *
import logging

group_bp = Blueprint("group", __name__)
logger = logging.getLogger(__name__)


class GroupForm(FlaskForm):
    gname = StringField("用户组名称", validators=[DataRequired(), Length(min=3, max=50)])
    ginfo = StringField("用户组描述", validators=[Length(max=200)])
    submit = SubmitField("保存")


class ChangeLeaderForm(FlaskForm):
    new_leader_name = SelectField("新组长用户名", validators=[DataRequired()])
    submit = SubmitField("更换组长")


def group_required(func):
    """用户组成员权限装饰器"""
    @wraps(func)
    def decorated(*args, **kwargs):
        gid = kwargs.get("gid")
        if any([
            not current_user.is_authenticated,
            not current_user.gid,
            str(current_user.gid) != str(gid)
        ]):
            abort(403, description="需要用户组成员权限才能访问此页面")
        return func(*args, **kwargs)
    return decorated


def leader_required(func):
    """用户组组长权限装饰器"""
    @wraps(func)
    def decorated(*args, **kwargs):
        gid = kwargs.get("gid")
        group = get_group_by_id(gid)
        if any([
            not current_user.is_authenticated,
            not current_user.gid,
            str(current_user.gid) != str(gid),
            str(group.leader_id) != str(current_user.uid),
        ]):
            abort(403, description="需要用户组组长权限才能访问此页面")
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
    if current_user.gid:
        abort(403, description="您已属于某个用户组，无法创建新用户组")
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
            logger.error(f"将用户 {current_user.uname} 加入用户组 {group.gname} 失败")
            return render_template("group/create.html", form=form)
        flash("用户组创建成功！您已成为该组成员", "success")
        logger.info(f"创建用户组成功: {form.gname.data} by user {current_user.uname}")
        return redirect(url_for("group.group_detail", gid=group.gid))
    return render_template("group/create.html", form=form)


@group_bp.route("/my_group", methods=["GET"])
@login_required
def my_group():
    """当前用户所属用户组页面"""
    group = get_group_by_id(current_user.gid)
    if not group:
        flash("您当前未加入任何用户组", "warning")
        return redirect(url_for("group.group_list"))
    return redirect(url_for("group.group_detail", gid=group.gid))


@group_bp.route("/<uuid:gid>", methods=["GET"])
@login_required
def group_detail(gid):
    """用户组详情页面"""
    gid = str(gid)
    group = get_group_by_id(gid)
    if not group:
        abort(404, description="用户组不存在")
    return render_template("group/detail.html", group=group)


# TODO: 模态窗口
@group_bp.route("/<uuid:gid>/edit", methods=["GET", "POST"])
@login_required
@group_required
def group_edit(gid):
    """用户组编辑页面"""
    gid = str(gid)
    group = get_group_by_id(gid)
    if not group:
        flash("用户组不存在", "warning")
        return jsonify({"error": "用户组不存在"}), 404
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
        logger.info(f"更新用户组信息成功: {form.gname.data} by user {current_user.uname}")
        return jsonify({"message": "用户组信息更新成功"}), 200
    return render_template("group/edit.html", form=form, group=group)


@group_bp.route("/<uuid:gid>/change_leader", methods=["GET", "POST"])
@login_required
@leader_required
def leader_change(gid):
    """用户组组长更换"""
    gid = str(gid)
    group = get_group_by_id(gid)
    users = get_users_by_group_id(gid)
    if not group:
        flash("用户组不存在", "warning")
        return jsonify({"error": "用户组不存在"}), 404
    form = ChangeLeaderForm()
    form.new_leader_name.choices = [(user.uname, user.email) for user in users]
    if form.validate_on_submit():
        new_leader_id = form.new_leader_name.data
        if not new_leader_id:
            flash("新组长ID不能为空", "warning")
            return jsonify({"error": "新组长ID不能为空"}), 400
        if not update_group(group, leader_id=new_leader_id):
            flash("更换组长失败，请重试", "danger")
            logger.warning(f"更换组长失败: {group.gname} by user {current_user.uname}")
            return jsonify({"error": "更换组长失败"}), 500
        flash("用户组组长更换成功", "success")
        logger.info(f"用户组组长更换成功: {group.gname} by user {current_user.uname}")
        return jsonify({"message": "用户组组长更换成功"}), 200
    return render_template("group/change_leader.html", form=form, group=group)