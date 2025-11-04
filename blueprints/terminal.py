from flask import (
    Blueprint,
    render_template,
    request,
    abort,
    jsonify,
    current_app,
)
from flask_login import login_required, current_user
from flask_socketio import emit, disconnect
from database.actions import *
from blueprints.project import group_required_pid
from utils.redis_client import terminal_sessions as TERMINAL_SESSIONS_REDIS
from utils.docker_client import docker_client
import logging
import docker
import threading

terminal_bp = Blueprint("terminal", __name__)
logger = logging.getLogger(__name__)

# 本地存储不可序列化的对象 (socket, container对象)
# session_id -> {'socket': socket_obj, 'container': container_obj}
_LOCAL_SESSION_OBJECTS = {}


def _get_container_by_project(pid: str):
    """根据项目 ID 获取运行中的容器"""
    project = get_project_by_pid(pid)
    if not project:
        logger.warning(f"项目 {pid} 不存在，无法获取容器")
        return None
    if not docker_client:
        logger.warning(f"项目 {pid} 的 Docker 客户端未初始化")
        return None
    try:
        container = docker_client.containers.get(project.docker_name)
        if container.status == "running":
            logger.debug(f"成功获取项目 {pid} 的容器: {container.id}")
            return container
    except Exception as e:
        logger.error(f"获取容器失败: {e}", exc_info=True)
    return None


@terminal_bp.route("/<uuid:pid>", methods=["GET"])
@login_required
@group_required_pid
def terminal(pid):
    """WebShell 终端页面"""
    pid = str(pid)
    project = get_project_by_pid(pid)

    if not project:
        abort(404, description="项目不存在")

    # 检查容器是否运行
    container = _get_container_by_project(pid)
    if not container:
        logger.debug(f"用户 {current_user.uname} 访问项目 {pid} 终端时，容器未运行")
        return jsonify({"status": "error", "message": "容器未运行，请先启动项目"}), 400

    return render_template("project/terminal.html", project=project)


def init_terminal_socketio(socketio_instance):
    """初始化 Terminal WebSocket 事件处理器"""

    @socketio_instance.on("connect", namespace="/terminal")
    def handle_connect():
        """客户端连接"""
        logger.info(f"Terminal WebSocket 已连接: sid={request.sid}")

    @socketio_instance.on("disconnect", namespace="/terminal")
    def handle_disconnect():
        """客户端断开连接，清理会话"""
        logger.info(f"Terminal WebSocket 断开: sid={request.sid}")

        # 从 Redis 获取会话信息
        session_info = TERMINAL_SESSIONS_REDIS.get(request.sid)
        local_objs = _LOCAL_SESSION_OBJECTS.get(request.sid)

        if session_info or local_objs:
            try:
                # 发送 exit 命令让 bash 优雅退出
                if local_objs and local_objs.get("socket"):
                    sock = local_objs["socket"]

                    try:
                        if hasattr(sock, "_sock"):
                            sock._sock.close()
                        if hasattr(sock, "close"):
                            sock.close()
                        logger.info(f"Socket 已关闭: sid={request.sid}")
                    except Exception as close_error:
                        logger.warning(f"关闭 socket 时出错（可忽略）: {close_error}")

                if session_info:
                    logger.info(
                        f"清理会话: sid={request.sid}, pid={session_info.get('pid')}"
                    )

                    # 从容器内部强制杀死本次会话的 bash 进程
                    # 使用环境变量标记来精确定位容器内的进程
                    session_marker = session_info.get("session_marker")
                    container_name = session_info.get("container_name")
                    if session_marker and container_name:
                        try:
                            container = docker_client.containers.get(container_name)
                            # 在容器内查找带有特定环境变量的 bash 进程并杀死
                            # 使用 grep 环境变量来精确匹配
                            kill_cmd = f"for pid in $(ps -eo pid,cmd | grep bash | grep -v grep | awk '{{print $1}}'); do cat /proc/$pid/environ 2>/dev/null | tr '\\0' '\\n' | grep -q '^{session_marker}=' && kill -9 $pid && echo killed $pid; done"
                            kill_result = container.exec_run(
                                f'sh -c "{kill_cmd}"', user="root"
                            )
                            logger.info(
                                f"杀死容器内 bash (marker={session_marker}): exit_code={kill_result.exit_code}, output={kill_result.output.decode('utf-8', errors='ignore').strip()}"
                            )
                        except Exception as e:
                            logger.warning(f"容器内杀死 bash 失败: {e}")
            except Exception as e:
                logger.error(f"清理会话失败: {e}", exc_info=True)
            finally:
                # 清理 Redis 和本地存储
                TERMINAL_SESSIONS_REDIS.delete(request.sid)
                _LOCAL_SESSION_OBJECTS.pop(request.sid, None)

    @socketio_instance.on("start_shell", namespace="/terminal")
    def handle_start_shell(data):
        """启动交互式 Shell"""
        if not current_user.is_authenticated:
            emit("error", {"message": "请先登录"})
            disconnect()
            return

        pid = data.get("pid")
        if not pid:
            emit("error", {"message": "缺少项目 ID"})
            return

        project = get_project_by_pid(str(pid))
        if not project:
            emit("error", {"message": "项目不存在"})
            return

        # 检查权限
        if not current_user.gid or str(current_user.gid) != str(project.gid):
            emit("error", {"message": "无权访问此项目"})
            disconnect()
            return

        container_name = project.docker_name

        if not docker_client:
            emit("error", {"message": "Docker 客户端未初始化"})
            return

        try:
            container = docker_client.containers.get(container_name)
            if container.status != "running":
                emit("error", {"message": "容器未运行"})
                return

            # 保存当前会话ID（在请求上下文中）
            current_sid = request.sid
            logger.info(f"为会话 {current_sid} 创建 exec 实例")

            # 生成唯一的会话标记，用于在容器内识别此进程
            session_marker = f"TERMINAL_SESSION_{current_sid.replace('-', '_')}"

            # 创建 exec 实例（不立即运行）
            timeout = current_app.config["TIMEOUT_COMMAND_EXECUTION"]
            exec_cmd = container.client.api.exec_create(
                container.id,
                f"/bin/bash -c 'export TMOUT={timeout}; export {session_marker}=1; exec bash'",
                stdin=True,
                tty=True,
                environment={"TERM": "xterm-256color", "LANG": "en_US.UTF-8"},
                user="root",
            )
            exec_id = exec_cmd["Id"]
            logger.info(
                f"Exec ID: {exec_id} TIMEOUT: {timeout} SESSION_MARKER: {session_marker}"
            )

            # 启动 exec 并获取 socket
            exec_socket = container.client.api.exec_start(
                exec_id, socket=True, tty=True
            )

            # 保存会话信息（分离可序列化和不可序列化数据）
            # Redis 存储：可序列化的元数据（不设置过期时间，手动清理）
            TERMINAL_SESSIONS_REDIS.set(
                current_sid,
                {
                    "exec_id": exec_id,
                    "pid": pid,
                    "session_marker": session_marker,
                    "container_id": container.id,
                    "container_name": container.name,
                },
            )

            # 本地存储：不可序列化的对象
            _LOCAL_SESSION_OBJECTS[current_sid] = {
                "socket": exec_socket,
                "container": container,
            }

            # 启动后台线程读取容器输出
            def read_output():
                sock = exec_socket
                try:
                    logger.debug(f"开始读取容器输出: sid={current_sid}")
                    logger.debug(f"Socket 类型: {type(sock).__name__}")

                    # 根据 socket 类型设置阻塞模式
                    try:
                        if hasattr(sock, "_sock"):
                            # Unix socket (Linux/Mac)
                            sock._sock.setblocking(True)
                            logger.debug("使用 Unix socket 模式")
                        else:
                            # Windows named pipe - 默认就是阻塞的
                            logger.debug("使用 Windows NpipeSocket 模式")
                    except Exception as e:
                        logger.warning(f"设置阻塞模式失败（可忽略）: {e}")

                    while True:
                        try:
                            # 对于 TTY 模式，直接读取原始数据（不使用多路复用协议）
                            # 一次读取最多 4KB
                            if hasattr(sock, "_sock"):
                                # Unix socket (Linux/Mac)
                                chunk = sock._sock.recv(4096)
                            else:
                                # Windows named pipe socket
                                chunk = sock.recv(4096)

                            if not chunk:
                                logger.debug(
                                    f"读取到空数据，退出循环: sid={current_sid}"
                                )
                                break

                            # 解码并发送到客户端
                            output_text = chunk.decode("utf-8", errors="replace")
                            socketio_instance.emit(
                                "output",
                                {"data": output_text},
                                namespace="/terminal",
                                room=current_sid,
                            )
                            logger.debug(
                                f"发送输出: {len(output_text)} 字符, sid={current_sid}"
                            )

                        except OSError as e:
                            # socket timeout 或其他 OS 错误
                            if e.errno == 11:  # EAGAIN/EWOULDBLOCK
                                continue
                            logger.error(f"Socket 错误: {e}", exc_info=True)
                            break
                        except Exception as e:
                            logger.error(f"读取数据块失败: {e}", exc_info=True)
                            break
                except Exception as e:
                    logger.error(f"读取容器输出失败: {e}", exc_info=True)
                    socketio_instance.emit(
                        "error",
                        {"message": f"读取输出失败: {str(e)}"},
                        namespace="/terminal",
                        room=current_sid,  # 使用保存的 sid
                    )
                finally:
                    logger.info(f"读取线程结束: sid={current_sid}")
                    socketio_instance.emit(
                        "disconnected",
                        {"message": "Shell 会话已关闭"},
                        namespace="/terminal",
                        room=current_sid,  # 使用保存的 sid
                    )

            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()

            emit("ready", {"message": "Shell 已就绪"})
            logger.info(
                f"Terminal 会话已启动: pid={pid}, user={current_user.uname}, sid={current_sid}"
            )

        except docker.errors.NotFound:
            emit("error", {"message": "容器不存在"})
        except Exception as e:
            logger.error(f"启动 Terminal 失败: {e}", exc_info=True)
            emit("error", {"message": f"启动失败: {str(e)}"})

    @socketio_instance.on("input", namespace="/terminal")
    def handle_input(data):
        """处理用户输入"""
        local_objs = _LOCAL_SESSION_OBJECTS.get(request.sid)

        if not local_objs:
            logger.warning(f"Shell 会话不存在: sid={request.sid}")
            emit("error", {"message": "Shell 会话不存在"})
            return

        sock = local_objs.get("socket")

        if not sock:
            logger.warning(f"Socket 不存在: sid={request.sid}")
            emit("error", {"message": "Socket 不存在"})
            return

        try:
            input_data = data.get("data", "")
            logger.debug(f"收到输入: {repr(input_data)[:50]}, sid={request.sid}")

            # 写入到容器的 stdin
            input_bytes = input_data.encode("utf-8")

            try:
                if hasattr(sock, "_sock"):
                    # Unix socket (Linux/Mac)
                    sock._sock.sendall(input_bytes)
                else:
                    # Windows named pipe socket
                    sock.sendall(input_bytes)
            except AttributeError:
                # 备用方案：直接使用 socket 的 send 方法
                sock.send(input_bytes)

            logger.debug(f"输入已发送: {len(input_bytes)} 字节, sid={request.sid}")
        except Exception as e:
            logger.error(f"发送输入到容器失败: {e}", exc_info=True)
            emit("error", {"message": f"发送输入失败: {str(e)}"})

    @socketio_instance.on("resize", namespace="/terminal")
    def handle_resize(data):
        """调整终端大小"""
        session_info = TERMINAL_SESSIONS_REDIS.get(request.sid)
        local_objs = _LOCAL_SESSION_OBJECTS.get(request.sid)

        if not session_info or not local_objs:
            return

        try:
            rows = int(data.get("rows", 24))
            cols = int(data.get("cols", 80))
            exec_id = session_info.get("exec_id")
            container = local_objs.get("container")

            # 调用 Docker API 调整终端大小
            if container and exec_id:
                container.client.api.exec_resize(exec_id, height=rows, width=cols)
                logger.debug(
                    f"终端大小已调整: rows={rows}, cols={cols}, sid={request.sid}"
                )
        except Exception as e:
            logger.error(f"调整终端大小失败: {e}", exc_info=True)
