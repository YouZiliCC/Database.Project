import logging
from flask import Blueprint, jsonify, render_template, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from database.actions import *
from blueprints.user import UserForm
from blueprints.group import GroupForm, ChangeLeaderForm
from blueprints.project import ProjectForm

# 管理员蓝图
admin_bp = Blueprint("admin", __name__)
logger = logging.getLogger(__name__)


@admin_bp.errorhandler(400)
@admin_bp.errorhandler(403)
@admin_bp.errorhandler(404)
@admin_bp.errorhandler(500)
def handle_errors(e):
    """统一错误处理器（强制返回JSON）"""
    return (
        jsonify(
            {
                "error": e.name,
                "message": (
                    e.description.split(": ")[-1]
                    if ":" in e.description
                    else e.description
                ),
            }
        ),
        e.code,
    )


def admin_required(func):
    """管理员权限装饰器"""

    @wraps(func)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403, description="需要管理员权限才能访问此页面")
        return func(*args, **kwargs)

    return decorated


@admin_bp.route("/dashboard", methods=["GET"])
@login_required
@admin_required
def dashboard():
    """管理员仪表板"""
    return render_template("admin/dashboard.html")


@admin_bp.route("/del_user/<uuid:uid>", methods=["POST"])
@login_required
@admin_required
def del_user(uid):
    """删除用户"""
    uid = str(uid)
    user = get_user_by_uid(uid)
    if not user:
        flash("用户不存在", "warning")
        return jsonify({"error": "用户不存在"}), 404
    if user.is_admin:
        flash("不能删除管理员用户", "danger")
        return jsonify({"error": "不能删除管理员用户"}), 403
    if user.is_leader:
        flash("不能删除工作组负责人，请先更换负责人", "danger")
        return jsonify({"error": "不能删除工作组负责人，请先更换负责人"}), 403
    if not delete_user(user):
        flash("删除用户失败", "error")
        return jsonify({"error": "删除用户失败"}), 500
    flash("用户已删除", "success")
    return jsonify({"message": "用户删除成功"}), 200


@admin_bp.route("/edit_user/<uuid:uid>", methods=["POST"])
@login_required
@admin_required
def edit_user(uid):
    """更新用户信息"""
    uid = str(uid)
    user = get_user_by_uid(uid)
    if not user:
        flash("用户不存在", "warning")
        return jsonify({"error": "用户不存在"}), 404
    form = UserForm(obj=user)
    if form.validate_on_submit():
        updated_user = update_user(
            user,
            uname=form.uname.data,
            email=form.email.data,
            sid=form.sid.data,
        )
        if not updated_user(user):
            flash("更新用户信息失败", "error")
            return jsonify({"error": "更新用户信息失败"}), 500
    flash("用户信息已更新", "success")
    return jsonify({"message": "用户信息更新成功"}), 200


@admin_bp.route("/reset_password/<uuid:uid>", methods=["POST"])
@login_required
@admin_required
def reset_password(uid):
    """重置用户密码"""
    uid = str(uid)
    user = get_user_by_uid(uid)
    if not user:
        flash("用户不存在", "warning")
        return jsonify({"error": "用户不存在"}), 404
    form = UserForm()
    if form.validate_on_submit():
        if not update_user(user, password="default_password"):
            flash("重置用户密码失败", "error")
            return jsonify({"error": "重置用户密码失败"}), 500
    flash("用户密码已重置", "success")
    return jsonify({"message": "用户密码重置成功"}), 200


@admin_bp.route("/del_group/<uuid:gid>", methods=["POST"])
@login_required
@admin_required
def del_group(gid):
    """删除工作组"""
    gid = str(gid)
    group = get_group_by_gid(str(gid))
    if not group:
        flash("工作组不存在", "warning")
        return jsonify({"error": "工作组不存在"}), 404
    if not delete_group(group):
        flash("删除工作组失败", "error")
        return jsonify({"error": "删除工作组失败"}), 500
    flash("工作组已删除", "success")
    return jsonify({"message": "工作组删除成功"}), 200


@admin_bp.route("/edit_group/<uuid:gid>", methods=["POST"])
@login_required
@admin_required
def edit_group(gid):
    """更新工作组信息"""
    gid = str(gid)
    group = get_group_by_gid(gid)
    if not group:
        flash("工作组不存在", "warning")
        return jsonify({"error": "工作组不存在"}), 404
    form = GroupForm(obj=group)
    if form.validate_on_submit():
        updated_group = update_group(
            group,
            gname=form.gname.data,
            ginfo=form.ginfo.data,
        )
        if not updated_group:
            flash("更新工作组信息失败", "error")
            return jsonify({"error": "更新工作组信息失败"}), 500
    flash("工作组信息已更新", "success")
    return jsonify({"message": "工作组信息更新成功"}), 200


@admin_bp.route("/change_leader/<uuid:gid>", methods=["POST"])
@login_required
@admin_required
def change_leader(gid):
    """更换工作组负责人"""
    gid = str(gid)
    group = get_group_by_gid(gid)
    if not group:
        flash("工作组不存在", "warning")
        return jsonify({"error": "工作组不存在"}), 404
    form = ChangeLeaderForm()
    form.new_leader_name.choices = [(user.uname, user.uname) for user in group.users]
    if form.validate_on_submit():
        new_leader = get_user_by_uname(form.new_leader_name.data)
        if not new_leader:
            flash("新组长不存在", "warning")
            return jsonify({"error": "新组长不存在"}), 404
        if not update_group(group, leader_id=new_leader.uid):
            flash("更换工作组组长失败", "error")
            return jsonify({"error": "更换工作组组长失败"}), 500
    flash("工作组组长已更换", "success")
    return jsonify({"message": "工作组组长更换成功"}), 200


@admin_bp.route("/del_projects/<uuid:pid>", methods=["POST"])
@login_required
@admin_required
def del_project(pid):
    """删除项目"""
    pid = str(pid)
    project = get_project_by_pid(pid)
    if not project:
        flash("项目不存在", "warning")
        return jsonify({"error": "项目不存在"}), 404
    if not delete_project(project):
        flash("删除项目失败", "error")
        return jsonify({"error": "删除项目失败"}), 500
    flash("项目已删除", "success")
    return jsonify({"message": "项目删除成功"}), 200


@admin_bp.route("/edit_project/<uuid:pid>", methods=["POST"])
@login_required
@admin_required
def edit_project(pid):
    """更新项目"""
    pid = str(pid)
    project = get_project_by_pid(pid)
    if not project:
        flash("项目不存在", "warning")
        return jsonify({"error": "项目不存在"}), 404
    form = ProjectForm(obj=project)
    if form.validate_on_submit():
        pass
        # TODO: 添加项目更新逻辑
    if not update_project(project):
        flash("更新项目失败", "error")
        return jsonify({"error": "更新项目失败"}), 500
    flash("项目已更新", "success")
    return jsonify({"message": "项目更新成功"}), 200
