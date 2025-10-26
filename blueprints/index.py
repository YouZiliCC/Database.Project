from flask import Blueprint, render_template
from database.actions import list_all_users, list_all_groups, list_all_projects

index_bp = Blueprint("index", __name__)

@index_bp.route("/", methods=["GET"])
def index():
    """主页"""
    return render_template("index.html")
    

@index_bp.route("/users", methods=["GET"])
def users():
    """用户列表页面"""
    users = list_all_users()
    return render_template("user/list.html", users=users)


@index_bp.route("/groups", methods=["GET"])
def groups():
    """用户组列表页面"""
    groups = list_all_groups()
    return render_template("group/list.html", groups=groups)


@index_bp.route("/projects", methods=["GET"])
def projects():
    """项目列表页面"""
    projects = list_all_projects()
    return render_template("project/list.html", projects=projects)