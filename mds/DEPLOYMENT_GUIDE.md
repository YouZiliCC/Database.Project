# 生产环境部署指南

## 问题诊断

你遇到的 `Invalid websocket upgrade` 错误是因为：
1. Gunicorn 默认的 sync worker 不支持 WebSocket
2. Flask-SocketIO 需要使用 eventlet 或 gevent 作为异步后端

## 解决方案

### 1. 安装依赖

已在 `pyproject.toml` 中添加 `eventlet>=0.37.0`，请重新安装依赖：

```bash
# 如果使用 uv
uv sync

# 或使用 pip
pip install -r requirements.txt
# 或
pip install eventlet
```

### 2. 启动命令

**使用 Gunicorn 配置文件（推荐）：**

```bash
gunicorn -c gunicorn_config.py main:app
```

**或直接指定参数：**

```bash
gunicorn -k eventlet -w 4 --bind 0.0.0.0:5000 --timeout 120 main:app
```

### 3. 参数说明

- `-k eventlet`: 使用 eventlet worker（必需）
- `-w 4`: 4 个 worker 进程
- `--bind 0.0.0.0:5000`: 绑定地址和端口
- `--timeout 120`: 请求超时时间（秒）
- `-c gunicorn_config.py`: 使用配置文件
- `main:app`: 应用模块和对象

### 4. 环境变量

在 `.env` 文件中配置：

```env
HOST=0.0.0.0
PORT=5000
LOG_LEVEL=info
GUNICORN_WORKERS=4
```

### 5. 使用 systemd 服务（Ubuntu 推荐）

创建服务文件 `/etc/systemd/system/dbsys.service`：

```ini
[Unit]
Description=DBSYS Flask-SocketIO Application
After=network.target docker.service mysql.service
Requires=docker.service

[Service]
Type=notify
User=your-user
Group=your-group
WorkingDirectory=/path/to/db_sys
Environment="PATH=/path/to/your/venv/bin"
ExecStart=/path/to/your/venv/bin/gunicorn -c gunicorn_config.py main:app
Restart=always
RestartSec=10

# 日志
StandardOutput=journal
StandardError=journal
SyslogIdentifier=dbsys

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable dbsys
sudo systemctl start dbsys
sudo systemctl status dbsys
```

### 6. 使用 Nginx 反向代理（可选）

在 `/etc/nginx/sites-available/dbsys` 中：

```nginx
upstream dbsys_app {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://dbsys_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    location /socket.io {
        proxy_pass http://dbsys_app/socket.io;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/dbsys /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. 验证

启动后检查：

```bash
# 查看进程
ps aux | grep gunicorn

# 查看日志
journalctl -u dbsys -f

# 测试 WebSocket 连接
curl -I http://localhost:5000/socket.io/?transport=polling
```

应该看到类似输出：
```
HTTP/1.1 200 OK
Content-Type: text/plain; charset=UTF-8
```

### 8. 常见问题

**Q: 仍然报 "Invalid websocket upgrade"？**
- 确保安装了 eventlet: `pip show eventlet`
- 确保使用 `-k eventlet` 启动
- 检查是否有反向代理拦截了 WebSocket 升级

**Q: Worker 频繁重启？**
- 增加 `timeout` 值（默认 30 秒可能不够）
- 检查是否有内存泄漏或死循环

**Q: 性能问题？**
- 调整 worker 数量：`workers = (2 * CPU_CORES) + 1`
- 使用 `preload_app = True` 预加载应用
- 启用 Nginx 缓存和 gzip 压缩

## 开发环境

如果只是本地开发，可以直接使用：

```bash
python main.py
```

这会使用 `socketio.run()` 启动，无需 Gunicorn。
