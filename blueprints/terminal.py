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
from flask_login import login_required, current_user
from flask_socketio import emit, disconnect
from database.actions import *
from blueprints.project import group_required_pid, docker_client
import logging
import docker
import threading
import struct
import socket

terminal_bp = Blueprint("terminal", __name__)
logger = logging.getLogger(__name__)


# 存储每个 WebSocket 会话的数据
# session_id (request.sid) -> {'container': container, 'exec_id': exec_instance, 'pid': pid}
TERMINAL_SESSIONS = {}


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
        container = docker_client.containers.get(project.docker_id)
        if container.status == 'running':
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
    
    @socketio_instance.on('connect', namespace='/terminal')
    def handle_connect():
        """客户端连接"""
        logger.info(f"Terminal WebSocket 已连接: sid={request.sid}")
    
    @socketio_instance.on('disconnect', namespace='/terminal')
    def handle_disconnect():
        """客户端断开连接，清理会话"""
        logger.info(f"Terminal WebSocket 断开: sid={request.sid}")
        if request.sid in TERMINAL_SESSIONS:
            try:
                session = TERMINAL_SESSIONS[request.sid]
                # 关闭 socket
                sock = session.get('socket')
                if sock:
                    try:
                        # 尝试多种关闭方法以确保兼容性
                        if hasattr(sock, '_sock'):
                            sock._sock.close()
                        if hasattr(sock, 'close'):
                            sock.close()
                        logger.info(f"Socket 已关闭: sid={request.sid}")
                    except Exception as close_error:
                        logger.warning(f"关闭 socket 时出错（可忽略）: {close_error}")
                logger.info(f"清理会话: sid={request.sid}, pid={session.get('pid')}")
            except Exception as e:
                logger.error(f"清理会话失败: {e}", exc_info=True)
            finally:
                del TERMINAL_SESSIONS[request.sid]
    
    @socketio_instance.on('start_shell', namespace='/terminal')
    def handle_start_shell(data):
        """启动交互式 Shell"""
        if not current_user.is_authenticated:
            emit('error', {'message': '请先登录'})
            disconnect()
            return
        
        pid = data.get('pid')
        if not pid:
            emit('error', {'message': '缺少项目 ID'})
            return
        
        project = get_project_by_pid(str(pid))
        if not project:
            emit('error', {'message': '项目不存在'})
            return
        
        # 检查权限
        if not current_user.gid or str(current_user.gid) != str(project.gid):
            emit('error', {'message': '无权访问此项目'})
            disconnect()
            return
        
        container_name = project.docker_id
        
        if not docker_client:
            emit('error', {'message': 'Docker 客户端未初始化'})
            return
        
        try:
            container = docker_client.containers.get(container_name)
            if container.status != 'running':
                emit('error', {'message': '容器未运行'})
                return
            
            # 保存当前会话ID（在请求上下文中）
            current_sid = request.sid
            logger.info(f"为会话 {current_sid} 创建 exec 实例")
            
            # 创建 exec 实例（不立即运行）
            exec_cmd = container.client.api.exec_create(
                container.id,
                '/bin/bash',
                stdin=True,
                tty=True,
                environment={'TERM': 'xterm-256color', 'LANG': 'en_US.UTF-8'},
                user='root'
            )
            exec_id = exec_cmd['Id']
            logger.info(f"Exec ID: {exec_id}")
            
            # 启动 exec 并获取 socket
            exec_socket = container.client.api.exec_start(
                exec_id,
                socket=True,
                tty=True
            )
            
            # 保存会话
            TERMINAL_SESSIONS[current_sid] = {
                'container': container,
                'exec_id': exec_id,
                'socket': exec_socket,
                'pid': pid,
            }
            
            # 启动后台线程读取容器输出
            def read_output():
                sock = exec_socket
                try:
                    logger.debug(f"开始读取容器输出: sid={current_sid}")
                    logger.debug(f"Socket 类型: {type(sock).__name__}")
                    
                    # 根据 socket 类型设置阻塞模式
                    try:
                        if hasattr(sock, '_sock'):
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
                            if hasattr(sock, '_sock'):
                                # Unix socket (Linux/Mac)
                                chunk = sock._sock.recv(4096)
                            else:
                                # Windows named pipe socket
                                chunk = sock.recv(4096)
                            
                            if not chunk:
                                logger.debug(f"读取到空数据，退出循环: sid={current_sid}")
                                break
                            
                            # 解码并发送到客户端
                            output_text = chunk.decode('utf-8', errors='replace')
                            socketio_instance.emit(
                                'output',
                                {'data': output_text},
                                namespace='/terminal',
                                room=current_sid
                            )
                            logger.debug(f"发送输出: {len(output_text)} 字符, sid={current_sid}")
                            
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
                        'error',
                        {'message': f'读取输出失败: {str(e)}'},
                        namespace='/terminal',
                        room=current_sid  # 使用保存的 sid
                    )
                finally:
                    logger.info(f"读取线程结束: sid={current_sid}")
                    socketio_instance.emit(
                        'disconnected',
                        {'message': 'Shell 会话已关闭'},
                        namespace='/terminal',
                        room=current_sid  # 使用保存的 sid
                    )
            
            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()
            
            emit('ready', {'message': 'Shell 已就绪'})
            logger.info(f"Terminal 会话已启动: pid={pid}, user={current_user.uname}, sid={current_sid}")
            
        except docker.errors.NotFound:
            emit('error', {'message': '容器不存在'})
        except Exception as e:
            logger.error(f"启动 Terminal 失败: {e}", exc_info=True)
            emit('error', {'message': f'启动失败: {str(e)}'})
    
    @socketio_instance.on('input', namespace='/terminal')
    def handle_input(data):
        """处理用户输入"""
        if request.sid not in TERMINAL_SESSIONS:
            logger.warning(f"Shell 会话不存在: sid={request.sid}")
            emit('error', {'message': 'Shell 会话不存在'})
            return
        
        session = TERMINAL_SESSIONS[request.sid]
        sock = session.get('socket')
        
        if not sock:
            logger.warning(f"Socket 不存在: sid={request.sid}")
            emit('error', {'message': 'Socket 不存在'})
            return
        
        try:
            input_data = data.get('data', '')
            logger.debug(f"收到输入: {repr(input_data)[:50]}, sid={request.sid}")
            
            # 写入到容器的 stdin
            input_bytes = input_data.encode('utf-8')
            
            try:
                if hasattr(sock, '_sock'):
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
            emit('error', {'message': f'发送输入失败: {str(e)}'})
    
    @socketio_instance.on('resize', namespace='/terminal')
    def handle_resize(data):
        """调整终端大小"""
        if request.sid not in TERMINAL_SESSIONS:
            return
        
        try:
            rows = int(data.get('rows', 24))
            cols = int(data.get('cols', 80))
            logger.debug(f"终端大小调整请求: rows={rows}, cols={cols}, sid={request.sid}")
            # 注意: Docker SDK 的 exec_run 不直接支持动态 resize
            # 这个功能在某些场景下可能不完全生效
        except Exception as e:
            logger.error(f"调整终端大小失败: {e}", exc_info=True)
