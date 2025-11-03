# Eventlet Monkey Patch 修复说明

## 问题

运行 Gunicorn 时出现错误：
```
1 RLock(s) were not greened, to fix this error make sure you run eventlet.monkey_patch() before importing any other modules.
```

## 原因

使用 eventlet 作为 Gunicorn worker 时，必须在**所有模块导入之前**调用 `eventlet.monkey_patch()`。

Monkey patching 会将 Python 标准库的阻塞操作替换为非阻塞的"绿色"版本：
- 线程 → 绿色线程（greenlet）
- 锁（Lock/RLock）→ 绿色锁
- Socket → 非阻塞 socket
- 时间函数（sleep）→ 协程式等待

如果不提前 patch，某些模块在导入时会创建标准的线程锁，导致阻塞整个 eventlet event loop。

## 解决方案

### 已修复 ✅

在 `main.py` 文件开头添加：

```python
# ⚠️ 关键：使用 eventlet 时必须在所有 import 之前调用 monkey_patch()
import eventlet
eventlet.monkey_patch()

# 然后才能导入其他模块
from app import create_app
from flask import render_template
# ...
```

### 为什么必须在最开始

```python
# ❌ 错误示例 - monkey_patch 在其他 import 之后
from flask import Flask
import threading  # 这里会创建标准锁
import eventlet
eventlet.monkey_patch()  # 太晚了，threading 已经创建了非绿色的锁

# ✅ 正确示例 - monkey_patch 必须在第一行
import eventlet
eventlet.monkey_patch()
from flask import Flask  # 现在导入的模块会使用绿色版本
import threading  # threading 的锁已被替换为绿色锁
```

## 启动命令

### Ubuntu 服务器（生产环境）

```bash
# 方式 1: 使用配置文件
gunicorn -c gunicorn_config.py main:app

# 方式 2: 直接指定参数
gunicorn -k eventlet -w 4 --bind 0.0.0.0:5000 main:app
```

### 本地开发

```bash
# 直接运行（会使用 socketio.run）
python main.py
```

## 验证

启动后应该看到类似日志：

```
[INFO] Gunicorn + Flask-SocketIO + WebSocket 服务器启动
  绑定地址: 0.0.0.0:5000
  Worker 类: eventlet
  Worker 数: 4
```

不应再有 "RLock(s) were not greened" 错误。

## 相关配置文件

- **main.py**: 应用入口，包含 `eventlet.monkey_patch()`
- **app.py**: Flask 应用工厂，SocketIO 使用 `async_mode="eventlet"`
- **gunicorn_config.py**: Gunicorn 配置，`worker_class = "eventlet"`
- **pyproject.toml**: 依赖列表，包含 `eventlet>=0.40.3`

## 常见问题

### Q: 为什么不在 `app.py` 里 monkey_patch？

A: 因为 Gunicorn 会导入 `main:app`，`main.py` 是真正的入口点。必须在入口文件的第一行 patch。

### Q: 开发环境也需要吗？

A: 是的，虽然 `python main.py` 使用 `socketio.run()` 不强制要求，但为了保持一致性建议加上。

### Q: 可以用 gevent 替代 eventlet 吗？

A: 可以，修改：
1. `pyproject.toml`: `gevent>=24.0.0`
2. `main.py`: `import gevent.monkey; gevent.monkey.patch_all()`
3. `app.py`: `async_mode="gevent"`
4. `gunicorn_config.py`: `worker_class="gevent"`

### Q: 会影响性能吗？

A: 不会。Monkey patching 是 eventlet/gevent 的标准做法，专为并发优化设计。

## 更多信息

- [Eventlet 官方文档](https://eventlet.readthedocs.io/)
- [Flask-SocketIO 部署指南](https://flask-socketio.readthedocs.io/en/latest/deployment.html)
- [Gunicorn 配置](https://docs.gunicorn.org/en/stable/settings.html)
