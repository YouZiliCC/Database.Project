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
import os

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

    def __init__(self, *args, **kwargs):
        self.original_port = kwargs.pop("original_port", None)
        self.original_docker_port = kwargs.pop("original_docker_port", None)
        super(ProjectForm, self).__init__(*args, **kwargs)

    # 自定义验证器
    def validate_port(self, port):
        if not port.data.isdigit() or not (10000 <= int(port.data) <= 65535):
            raise ValidationError("端口号必须是10000到65535之间的数字")
        # 如果端口号没有改变，跳过验证
        if self.original_port and int(port.data) == int(self.original_port):
            return
        # 检查端口是否被其他项目占用
        existing_project = get_projects_by_port(port.data)
        if existing_project:
            raise ValidationError("端口号已被占用")

    def validate_docker_port(self, docker_port):
        if not docker_port.data.isdigit() or not (
            1024 <= int(docker_port.data) <= 65535
        ):
            raise ValidationError("Docker端口号必须是1024到65535之间的数字")
        # 如果端口号没有改变，跳过验证
        if self.original_docker_port and int(docker_port.data) == int(
            self.original_docker_port
        ):
            return
        # 检查端口是否被其他项目占用
        existing_project = get_projects_by_docker_port(docker_port.data)
        if existing_project:
            raise ValidationError("Docker端口号已被占用")


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


@project_bp.route("/<uuid:pid>", methods=["GET"])
def project_detail(pid):
    """项目详情页面"""
    pid = str(pid)
    project = get_project_by_pid(pid)
    if not project:
        abort(404, description="项目不存在")

    # 获取评论列表
    comments = get_ordered_project_comments_by_pid(pid)

    # 获取点赞数和当前用户点赞状态
    star_count = get_project_star_count_by_pid(pid)
    user_starred = False
    if current_user.is_authenticated:
        user_starred = check_user_starred(current_user.uid, pid)

    return render_template(
        "project/detail.html",
        project=project,
        comments=comments,
        star_count=star_count,
        user_starred=user_starred,
    )


# -------------------------------------------------------------------------------------------
# ProjectStar
# -------------------------------------------------------------------------------------------
@project_bp.route("/<uuid:pid>/star", methods=["POST"])
@login_required
def project_star(pid):
    """项目点赞功能"""
    pid = str(pid)
    project = get_project_by_pid(pid)
    if not project:
        return jsonify({"success": False, "message": "项目不存在"}), 404

    # find existing star record by current user
    existing_star = next((s for s in project.stars if s.uid == current_user.uid), None)
    if existing_star:
        # 已点赞，取消点赞
        if not delete_project_star(existing_star):
            logger.warning("取消点赞失败")
            return jsonify({"success": False, "message": "取消点赞失败"}), 500
        # get fresh count
        star_count = get_project_star_count_by_pid(pid)
        return (
            jsonify(
                {
                    "success": True,
                    "message": "取消点赞成功",
                    "star_count": star_count,
                    "starred": False,
                }
            ),
            200,
        )

    # 未点赞，添加点赞
    new_star = create_project_star(current_user.uid, project.pid)
    if not new_star:
        logger.warning("点赞失败")
        return jsonify({"success": False, "message": "点赞失败"}), 500
    star_count = get_project_star_count_by_pid(pid)
    return (
        jsonify(
            {
                "success": True,
                "message": "点赞成功",
                "star_count": star_count,
                "starred": True,
            }
        ),
        200,
    )


# -------------------------------------------------------------------------------------------
# ProjectComment
# -------------------------------------------------------------------------------------------
@project_bp.route("/<uuid:pid>/comment", methods=["POST"])
@login_required
def project_comment(pid):
    """项目评论功能"""
    pid = str(pid)
    project = get_project_by_pid(pid)
    if not project:
        return jsonify({"success": False, "message": "项目不存在"}), 404

    # accept JSON or form-encoded content
    content = None
    if request.is_json:
        data = request.get_json(silent=True) or {}
        content = data.get("content")
    else:
        content = request.form.get("content")

    if not content or not content.strip():
        return jsonify({"success": False, "message": "评论不能为空"}), 400

    created = create_project_comment(current_user.uid, project.pid, content.strip())
    if not created:
        return jsonify({"success": False, "message": "创建评论失败"}), 500

    # respond with comment data for client-side rendering
    return (
        jsonify(
            {
                "success": True,
                "message": "评论已发布",
                "comment": {
                    "pcid": created.pcid,
                    "uid": created.uid,
                    "uname": created.user.uname if created.user else current_user.uname,
                    "content": created.content,
                    "created_at": created.created_at.strftime("%Y-%m-%d %H:%M"),
                },
            }
        ),
        200,
    )


@project_bp.route("/<uuid:pid>/comment/<pcid>", methods=["PUT", "PATCH"])
@login_required
def project_comment_edit(pid, pcid):
    """编辑评论"""
    from database.actions import get_comment_by_pcid, update_comment

    comment = get_comment_by_pcid(pcid)
    if not comment:
        return jsonify({"success": False, "message": "评论不存在"}), 404

    # 只允许作者编辑自己的评论
    if str(comment.uid) != str(current_user.uid):
        return jsonify({"success": False, "message": "无权编辑此评论"}), 403

    # 获取新内容
    data = request.get_json(silent=True) or {}
    content = data.get("content", "").strip()

    if not content:
        return jsonify({"success": False, "message": "评论内容不能为空"}), 400

    # 更新评论
    if not update_comment(comment, content=content):
        return jsonify({"success": False, "message": "更新评论失败"}), 500

    return (
        jsonify(
            {
                "success": True,
                "message": "评论已更新",
                "comment": {
                    "pcid": comment.pcid,
                    "content": comment.content,
                },
            }
        ),
        200,
    )


@project_bp.route("/<uuid:pid>/comment/<pcid>", methods=["DELETE"])
@login_required
def project_comment_delete(pid, pcid):
    """删除评论"""
    from database.actions import get_comment_by_pcid

    comment = get_comment_by_pcid(pcid)
    if not comment:
        return jsonify({"success": False, "message": "评论不存在"}), 404

    # 只允许作者删除自己的评论
    if str(comment.uid) != str(current_user.uid):
        return jsonify({"success": False, "message": "无权删除此评论"}), 403

    # 删除评论
    if not delete_project_comment(comment):
        return jsonify({"success": False, "message": "删除评论失败"}), 500

    return jsonify({"success": True, "message": "评论已删除"}), 200


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

    form = ProjectForm(
        obj=project,
        original_port=project.port,
        original_docker_port=project.docker_port,
    )
    if form.validate_on_submit():
        # 处理图片上传
        if "pimg" in request.files:
            file = request.files["pimg"]
            if file and file.filename:
                # 检查文件扩展名
                allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
                if (
                    "." in file.filename
                    and file.filename.rsplit(".", 1)[1].lower() in allowed_extensions
                ):
                    # 保存为 {pid}.png
                    img_folder = "static/img/projects"
                    os.makedirs(img_folder, exist_ok=True)
                    img_path = os.path.join(img_folder, f"{pid}.png")
                    file.save(img_path)
                    flash("图片上传成功", "success")
                else:
                    flash("不支持的图片格式", "warning")

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
