import eventlet

eventlet.monkey_patch()

# Gunicorn 配置文件
# 用于生产环境部署 Flask-SocketIO + WebSocket
import dotenv
import multiprocessing
import os

env_path = os.path.join(os.path.dirname(__file__), ".env")
dotenv.load_dotenv(env_path)

# 服务器绑定地址
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '5000')}"

# Worker 类型 - 必须使用 eventlet 或 gevent 以支持 WebSocket
worker_class = os.getenv("WORKER_CLASS", "eventlet")

# Worker 进程数
# 对于 eventlet/gevent，建议使用 CPU 核心数的 2-4 倍
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2))

# 每个 worker 的线程数（eventlet 模式下此设置无效，但保留以备用）
threads = 1

# Worker 超时时间（秒）
timeout = int(os.getenv("TIMEOUT", 120))

# 保持连接活动时间（秒）- 对 WebSocket 很重要
keepalive = int(os.getenv("KEEPALIVE", 5))

# 日志级别
loglevel = os.getenv("LOG_LEVEL", "info").lower()

# 捕获
capture_output = os.getenv("CAPTURE_OUTPUT", "True") == "True"

# 访问日志文件（- 表示 stdout）
accesslog = os.getenv("ACCESSLOG", "-")

# 错误日志文件（- 表示 stderr）
errorlog = os.getenv("ERRORLOG", "-")

# 访问日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 守护进程模式（生产环境可设为 True）
daemon = os.getenv("DAEMON", "False") == "True"

# PID 文件路径（可选）
pidfile = None

# 热重载
reload = os.getenv("RELOAD", "False") == "True"

# 预加载应用（可提高性能，但热重载会失效）
preload_app = os.getenv("PRELOAD", "False") == "True"

# 最大请求数（处理后重启 worker，防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 优雅重启超时
graceful_timeout = 30

# WebSocket 特定配置
# 允许的最大请求大小（MB）
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Worker 临时目录
worker_tmp_dir = "/dev/shm" if os.path.exists("/dev/shm") else None


# 启动时回调
def on_starting(server):
    server.log.info("=" * 60)
    server.log.info("  Gunicorn 服务器启动")
    server.log.info("=" * 60)
    server.log.info(f"  绑定地址: {bind}")
    server.log.info(f"  Worker 类: {worker_class}")
    server.log.info(f"  Worker 数: {workers}")
    server.log.info(f"  日志级别: {loglevel}")
    server.log.info("=" * 60)


def on_reload(server):
    server.log.info("代码变更，正在重新加载...")


def worker_int(worker):
    worker.log.info(f"Worker {worker.pid} 收到中断信号")


def worker_abort(worker):
    worker.log.error(f"Worker {worker.pid} 异常退出")
