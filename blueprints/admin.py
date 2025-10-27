import logging
from flask import Blueprint, jsonify, render_template, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from database.actions import *

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




@admin_bp.route("/delete_user/<uuid:uid>", methods=["POST"])
@login_required
@admin_required
def delete_user(uid):
    """删除用户"""
    uid = str(uid)
    user = get_user_by_id(uid)
    if not user:
        flash("用户不存在", "warning")
        return jsonify({"error": "用户不存在"}), 404
    if user.is_admin:
        flash("不能删除管理员用户", "danger")
        return jsonify({"error": "不能删除管理员用户"}), 403
    if user.is_leader:
        flash("不能删除用户组负责人，请先更换负责人", "danger")
        return jsonify({"error": "不能删除用户组负责人，请先更换负责人"}), 403
    if not delete_user(user):
        flash("删除用户失败", "error")
        return jsonify({"error": "删除用户失败"}), 500
    flash("用户已删除", "success") 
    return jsonify({"message": "用户删除成功"}), 200


@admin_bp.route("/update_user/<uuid:uid>", methods=["POST"])
@login_required
@admin_required
def update_user(uid):
    """更新用户信息"""
    uid = str(uid)
    user = get_user_by_id(uid)
    if not user:
        flash("用户不存在", "warning")
        return jsonify({"error": "用户不存在"}), 404
    # TODO: 这里可以添加更新用户信息的逻辑



    if not update_user(user):
        flash("更新用户信息失败", "error")
        return jsonify({"error": "更新用户信息失败"}), 500
    flash("用户信息已更新", "success")
    return jsonify({"message": "用户信息更新成功"}), 200



@admin_bp.route("/delete_group/<uuid:gid>", methods=["POST"])
@login_required
@admin_required
def delete_group(gid):
    """删除用户组"""
    gid = str(gid)
    group = get_group_by_id(str(gid))
    if not group:
        flash("用户组不存在", "warning")
        return jsonify({"error": "用户组不存在"}), 404
    if not delete_group(group):
        flash("删除用户组失败", "error")
        return jsonify({"error": "删除用户组失败"}), 500
    flash("用户组已删除", "success")
    return jsonify({"message": "用户组删除成功"}), 200


@admin_bp.route("/update_group/<uuid:gid>", methods=["POST"])
@login_required
@admin_required
def update_group(gid):
    """更新用户组信息"""
    gid = str(gid)
    group = get_group_by_id(gid)
    if not group:
        flash("用户组不存在", "warning")
        return jsonify({"error": "用户组不存在"}), 404
    # TODO: 这里可以添加更新用户组信息的逻辑


    
    if not update_group(group):
        flash("更新用户组信息失败", "error")
        return jsonify({"error": "更新用户组信息失败"}), 500
    flash("用户组信息已更新", "success")
    return jsonify({"message": "用户组信息更新成功"}), 200





@admin_bp.route("/delete_projects/<uuid:pid>", methods=["POST"])
@login_required
@admin_required
def delete_project(pid):
    """删除项目"""
    pid = str(pid)
    project = get_project_by_id(pid)
    if not project:
        flash("项目不存在", "warning")
        return jsonify({"error": "项目不存在"}), 404
    if not delete_project(project):
        flash("删除项目失败", "error")
        return jsonify({"error": "删除项目失败"}), 500
    flash("项目已删除", "success")
    return jsonify({"message": "项目删除成功"}), 200


@admin_bp.route("/update_project/<uuid:pid>", methods=["POST"])
@login_required
@admin_required
def update_project(pid):
    """更新项目"""
    pid = str(pid)
    project = get_project_by_id(pid)
    if not project:
        flash("项目不存在", "warning")
        return jsonify({"error": "项目不存在"}), 404
    # TODO: 这里可以添加更新项目的逻辑



    if not update_project(project):
        flash("更新项目失败", "error")
        return jsonify({"error": "更新项目失败"}), 500
    flash("项目已更新", "success")
    return jsonify({"message": "项目更新成功"}), 200