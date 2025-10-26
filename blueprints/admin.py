import logging
from flask import Blueprint, jsonify, render_template, url_for, flash, redirect
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
            flash("需要管理员权限才能访问此页面", "warning")
            return redirect(url_for("index.index"))
        return func(*args, **kwargs)
    return decorated


@admin_bp.route("/dashboard", methods=["GET"])
@login_required
@admin_required
def dashboard():
    """管理员仪表板"""
    return render_template("admin/dashboard.html")


@admin_bp.route("/users", methods=["GET"])
@login_required
@admin_required
def list_users():
    """列出所有用户"""
    users = list_all_users()
    users_data = [
        {
            "user_id": user.uid,
            "username": user.uname,
            "email": user.email,
            "is_admin": user.is_admin,
            "group_id": user.gid,
        }
        for user in users
    ]
    return jsonify(users_data)


@admin_bp.route("/delete_user/<uuid:user_id>", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    """删除用户"""
    user = get_user_by_id(str(user_id))
    if not user:
        flash("用户不存在", "warning")
        return redirect(url_for("admin.list_users"))
    if user.is_admin:
        flash("不能删除管理员用户", "danger")
        return redirect(url_for("admin.list_users"))
    if user.is_leader:
        flash("不能删除用户组负责人，请先更换负责人", "danger")
        return redirect(url_for("admin.list_users"))
    if delete_user(user):
        flash("用户已删除", "success")
    else:
        flash("删除用户失败", "error")
    return redirect(url_for("admin.list_users"))


@admin_bp.route("/update_user/<uuid:user_id>", methods=["POST"])
@login_required
@admin_required
def update_user(user_id):
    """更新用户信息"""
    user = get_user_by_id(str(user_id))
    if not user:
        flash("用户不存在", "warning")
        return redirect(url_for("admin.list_users"))
    # 这里可以添加更新用户信息的逻辑
    if update_user(user):
        flash("用户信息已更新", "success")
    else:
        flash("更新用户信息失败", "error")
    return redirect(url_for("admin.list_users"))


@admin_bp.route("/groups", methods=["GET"])
@login_required
@admin_required
def list_groups():
    """列出所有用户组"""
    groups = list_all_groups()
    groups_data = [
        {
            "group_id": group.gid,
            "group_name": group.gname,
            "group_info": group.ginfo,
            "leader_id": group.leader_id,
        }
        for group in groups
    ]
    return jsonify(groups_data)

@admin_bp.route("/delete_group/<uuid:group_id>", methods=["POST"])
@login_required
@admin_required
def delete_group(group_id):
    """删除用户组"""
    group = get_group_by_id(str(group_id))
    if not group:
        flash("用户组不存在", "warning")
        return redirect(url_for("admin.list_groups"))
    if delete_group(group):
        flash("用户组已删除", "success")
    else:
        flash("删除用户组失败", "error")
    return redirect(url_for("admin.list_groups"))


@admin_bp.route("/update_group/<uuid:group_id>", methods=["POST"])
@login_required
@admin_required
def update_group(group_id):
    """更新用户组信息"""
    group = get_group_by_id(str(group_id))
    if not group:
        flash("用户组不存在", "warning")
        return redirect(url_for("admin.list_groups"))
    # 这里可以添加更新用户组信息的逻辑
    if update_group(group):
        flash("用户组信息已更新", "success")
    else:
        flash("更新用户组信息失败", "error")
    return redirect(url_for("admin.list_groups"))


@admin_bp.route("/projects", methods=["GET"])
@login_required
@admin_required
def list_projects():
    """列出所有项目"""
    projects = list_all_projects()
    projects_data = [
        {
            "project_id": project.pid,
            "project_name": project.pname,
            "group_id": project.gid,
            "docker_id": project.docker_id,
            "port": project.port,
            "docker_port": project.docker_port,
        }
        for project in projects
    ]
    return jsonify(projects_data)


@admin_bp.route("/delete_projects/<uuid:project_id>", methods=["POST"])
@login_required
@admin_required
def delete_project(project_id):
    """删除项目"""
    project = get_project_by_id(str(project_id))
    if not project:
        flash("项目不存在", "warning")
        return redirect(url_for("admin.list_projects"))
    if delete_project(project):
        flash("项目已删除", "success")
    else:
        flash("删除项目失败", "error")
    return redirect(url_for("admin.list_projects"))

@admin_bp.route("/update_project/<uuid:project_id>", methods=["POST"])
@login_required
@admin_required
def update_project(project_id):
    """更新项目"""
    project = get_project_by_id(str(project_id))
    if not project:
        flash("项目不存在", "warning")
        return redirect(url_for("admin.list_projects"))
    # 这里可以添加更新项目的逻辑
    if update_project(project):
        flash("项目已更新", "success")
    else:
        flash("更新项目失败", "error")
    return redirect(url_for("admin.list_projects"))