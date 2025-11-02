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
import docker
import threading

# 项目蓝图
project_bp = Blueprint("project", __name__)
logger = logging.getLogger(__name__)

# In-memory status map for builds/starts (pid -> 'stopped'|'starting'|'running')
DOCKER_STATUS = {}

# Docker client (会自动连接到本地 Docker daemon)
try:
    docker_client = docker.from_env()
except Exception as e:
    logger.error(f"无法连接到 Docker daemon: {e}", exc_info=True)
    docker_client = None


def _docker_image_exists(image_name: str) -> bool:
    """检查 Docker 镜像是否存在"""
    if not docker_client:
        logger.warning("Docker client 未初始化，无法检查镜像")
        return False
    try:
        docker_client.images.get(image_name)
        logger.debug(f"镜像 {image_name} 已存在")
        return True
    except docker.errors.ImageNotFound:
        # 正常情况，不需要记录
        return False
    except Exception as e:
        logger.error(f"检查镜像 {image_name} 时发生异常: {e}", exc_info=True)
        return False


def _docker_container_exists(container_name: str) -> bool:
    """检查 Docker 容器是否存在"""
    if not docker_client:
        logger.warning("Docker client 未初始化，无法检查容器")
        return False
    try:
        docker_client.containers.get(container_name)
        logger.debug(f"容器 {container_name} 已存在")
        return True
    except docker.errors.NotFound:
        # 正常情况，不需要记录
        return False
    except Exception as e:
        logger.error(f"检查容器 {container_name} 时发生异常: {e}", exc_info=True)
        return False


def _docker_container_status(container_name: str) -> str:
    """获取容器状态: running, stopped"""
    if not docker_client:
        logger.debug("Docker client 未初始化")
        return "stopped"
    try:
        container = docker_client.containers.get(container_name)
        status = container.status  # running, exited, paused, restarting, etc.
        logger.debug(f"容器 {container_name} 状态: {status}")
        if status == "running":
            return "running"
        else:
            return "stopped"
    except docker.errors.NotFound:
        # 正常情况，容器不存在
        return "stopped"
    except Exception as e:
        logger.error(f"获取容器 {container_name} 状态失败: {e}", exc_info=True)
        return "stopped"


def _docker_build_image(image_name: str, path: str = None) -> bool:
    """构建 Docker 镜像（阻塞）。成功返回 True"""
    if not docker_client:
        logger.warning("Docker client 未初始化，无法构建镜像")
        return False
    try:
        build_path = path or os.getcwd()
        logger.info(f"开始构建镜像: {image_name} (路径: {build_path})")
        image, build_logs = docker_client.images.build(
            path=build_path,
            tag=image_name,
            rm=True,  # 删除中间容器
        )
        # 构建日志仅在 DEBUG 级别输出
        for log in build_logs:
            if "stream" in log:
                logger.debug(log["stream"].strip())
        logger.info(f"镜像构建成功: {image_name}")
        return True
    except docker.errors.BuildError as e:
        logger.error(f"镜像构建失败: {image_name}, 错误: {e}")
        return False
    except Exception as e:
        logger.error(f"镜像构建异常: {image_name}", exc_info=True)
        return False


def _docker_run_container(
    image_name: str, container_name: str, host_port: int, container_port: int
) -> str:
    """运行容器（detached）并返回容器 ID，失败返回空字符串"""
    if not docker_client:
        logger.warning("Docker client 未初始化，无法运行容器")
        return ""
    try:
        container = docker_client.containers.run(
            image_name,
            name=container_name,
            ports={f"{container_port}/tcp": host_port},
            detach=True,
            remove=False,  # 不自动删除
        )
        logger.info(
            f"容器创建并启动成功: {container_name} (ID: {container.short_id}, 端口: {host_port}:{container_port})"
        )
        return container.id
    except docker.errors.APIError as e:
        logger.error(f"容器运行失败: {container_name}, 错误: {e}")
        return ""
    except Exception as e:
        logger.error(f"容器运行异常: {container_name}", exc_info=True)
        return ""


def _docker_start_container(container_name: str) -> bool:
    """启动已存在的容器"""
    if not docker_client:
        logger.warning("Docker client 未初始化，无法启动容器")
        return False
    try:
        container = docker_client.containers.get(container_name)
        container.start()
        logger.info(f"容器启动成功: {container_name}")
        return True
    except docker.errors.NotFound:
        logger.warning(f"容器不存在，无法启动: {container_name}")
        return False
    except docker.errors.APIError as e:
        logger.error(f"容器启动失败: {container_name}, 错误: {e}")
        return False
    except Exception as e:
        logger.error(f"容器启动异常: {container_name}", exc_info=True)
        return False


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
            logger.error(
                f"取消点赞失败: user={current_user.uname}, project={project.pname}"
            )
            return jsonify({"success": False, "message": "取消点赞失败"}), 500
        # get fresh count
        star_count = get_project_star_count_by_pid(pid)
        logger.debug(f"取消点赞: user={current_user.uname}, project={project.pname}")
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
        logger.error(f"点赞失败: user={current_user.uname}, project={project.pname}")
        return jsonify({"success": False, "message": "点赞失败"}), 500
    star_count = get_project_star_count_by_pid(pid)
    logger.debug(f"点赞成功: user={current_user.uname}, project={project.pname}")
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
            logger.error(
                f"更新项目失败: project={form.pname.data}, user={current_user.uname}"
            )
            return render_template("project/edit.html", form=form, project=project)
        flash("项目更新成功", "success")
        logger.info(
            f"更新项目成功: project={form.pname.data}, user={current_user.uname}"
        )
        return redirect(url_for("project.project_detail", pid=pid))
    return render_template("project/edit.html", form=form, project=project)


@project_bp.route("/<uuid:pid>/start", methods=["POST"])
@login_required
@group_required_pid
def start_docker(pid):
    """启动Docker容器"""
    pid = str(pid)
    project = get_project_by_pid(pid)
    if not project:
        flash("项目不存在", "warning")
        abort(404, description="项目不存在")
    # 使用每个项目独立的 image/container 名称，避免冲突
    image_name = f"dbsys_{pid}"
    container_name = f"dbsys_{pid}"

    # 需要提前配置好端口映射
    try:
        host_port = int(project.port) if project.port else None
        container_port = int(project.docker_port) if project.docker_port else None
    except Exception:
        host_port = None
        container_port = None

    if not host_port or not container_port:
        return (
            jsonify(
                {"success": False, "message": "未配置项目端口或容器端口，无法启动"}
            ),
            400,
        )

    # 如果已有正在处理的任务，直接返回启动中
    if DOCKER_STATUS.get(pid) == "starting":
        return (
            jsonify({"success": True, "message": "启动中", "status": "starting"}),
            202,
        )

    # 检查镜像是否存在
    image_exists = _docker_image_exists(image_name)

    # 检查容器是否存在
    container_exists = _docker_container_exists(container_name)

    # 启动流程可能比较耗时（build），我们使用后台线程执行并立即返回启动中状态
    def _build_and_start():
        try:
            DOCKER_STATUS[pid] = "starting"
            logger.info(
                f"开始启动项目容器: project={project.pname}, pid={pid}, user={current_user.uname}"
            )

            # 如果镜像不存在，先 build
            if not image_exists:
                logger.info(
                    f"镜像不存在，开始构建: image={image_name}, project={project.pname}"
                )
                success = _docker_build_image(image_name, path=os.getcwd())
                if not success:
                    DOCKER_STATUS[pid] = "stopped"
                    logger.error(
                        f"镜像构建失败，容器启动终止: project={project.pname}, pid={pid}"
                    )
                    return

            # 如果容器不存在，创建并运行；否则尝试启动已存在的容器
            if not _docker_container_exists(container_name):
                logger.info(
                    f"容器不存在，创建并运行: container={container_name}, project={project.pname}"
                )
                container_id = _docker_run_container(
                    image_name, container_name, host_port, container_port
                )
                if container_id:
                    # persist container id to project record
                    update_project(project, docker_id=container_id)
                    DOCKER_STATUS[pid] = "running"
                    logger.info(
                        f"容器启动成功: container={container_name}, id={container_id[:12]}, project={project.pname}"
                    )
                    return
                else:
                    DOCKER_STATUS[pid] = "stopped"
                    logger.error(
                        f"容器创建失败: container={container_name}, project={project.pname}"
                    )
                    return
            else:
                # 尝试启动已存在容器
                logger.info(
                    f"容器已存在，尝试启动: container={container_name}, project={project.pname}"
                )
                started = _docker_start_container(container_name)
                if started:
                    DOCKER_STATUS[pid] = "running"
                    logger.info(
                        f"已存在容器启动成功: container={container_name}, project={project.pname}"
                    )
                    return
                else:
                    DOCKER_STATUS[pid] = "stopped"
                    logger.error(
                        f"已存在容器启动失败: container={container_name}, project={project.pname}"
                    )
                    return
        finally:
            # 如果线程结束且状态仍为 starting，则设置为 stopped 以表示未运行
            if DOCKER_STATUS.get(pid) == "starting":
                DOCKER_STATUS[pid] = "stopped"
                logger.warning(
                    f"容器启动超时或异常终止: project={project.pname}, pid={pid}"
                )

    # 启动后台线程
    t = threading.Thread(target=_build_and_start, daemon=True)
    t.start()

    return (
        jsonify({"success": True, "message": "启动已开始", "status": "starting"}),
        202,
    )


# 重置docker容器

# 连接docker


# TODO: terminal


@project_bp.route("/<uuid:pid>/docker/status", methods=["GET"])
def project_docker_status(pid):
    """返回项目 docker 状态：stopped | starting | running"""
    pid = str(pid)
    project = get_project_by_pid(pid)
    if not project:
        return jsonify({"success": False, "message": "项目不存在"}), 404

    # 首先检查内存状态
    status = DOCKER_STATUS.get(pid)
    if status:
        return jsonify({"success": True, "status": status}), 200

    # 如果没有内存标记，检测容器实际状态
    container_name = f"dbsys_{pid}"
    if _docker_container_exists(container_name):
        st = _docker_container_status(container_name)
        mapped = "running" if st == "running" else "stopped"
        return jsonify({"success": True, "status": mapped}), 200

    # 默认视为已停止
    return jsonify({"success": True, "status": "stopped"}), 200

    # TODO: iframe 或者别的实现方法
