# 数据库系统课程 - 学生项目展示平台

这是一个用于展示数据库系统课程学生项目的Web平台，基于Flask构建，支持Docker部署，并提供交互式命令行终端。

## 📋 功能特性

- **项目展示**：展示所有学生的数据库项目，包含项目信息和Docker配置
- **在线访问**：直接访问各个学生部署的Web应用
- **命令行终端**：Web界面中的交互式命令行终端，支持基本系统命令和Docker操作
- **Docker支持**：完整的Docker部署方案，方便统一管理和部署

## 🚀 快速开始

### 方式1：直接运行（开发模式）

1. **安装依赖**
```bash
pip install .
# 或者
pip install flask
```

2. **运行应用**
```bash
python main.py
```

3. **访问应用**
打开浏览器访问: http://localhost:5000

### 方式2：使用Docker

1. **构建镜像**
```bash
docker build -t db-sys-platform .
```

2. **运行容器**
```bash
docker run -d -p 5000:5000 --name db-sys db-sys-platform
```

3. **访问应用**
打开浏览器访问: http://localhost:5000

### 方式3：使用Docker Compose

1. **启动所有服务**
```bash
docker-compose up -d
```

2. **查看运行状态**
```bash
docker-compose ps
```

3. **停止服务**
```bash
docker-compose down
```

## 📁 项目结构

```
db_sys/
├── main.py                 # Flask应用主文件
├── pyproject.toml          # 项目依赖配置
├── Dockerfile              # Docker镜像构建文件
├── docker-compose.yml      # Docker Compose配置
├── .dockerignore           # Docker构建忽略文件
├── README.md               # 项目说明文档
├── templates/              # HTML模板目录
│   ├── index.html          # 首页 - 项目列表
│   ├── terminal.html       # 命令行终端页面
│   └── project_detail.html # 项目详情页面
└── static/                 # 静态资源目录
    ├── css/
    │   └── style.css       # 样式文件
    └── js/
        └── terminal.js     # 终端交互逻辑
```

## 🎯 使用说明

### 1. 查看项目列表
访问首页可以看到所有学生的项目卡片，包含：
- 学生姓名
- 项目名称和描述
- Docker配置信息
- 访问端口

### 2. 访问学生项目
点击项目卡片上的"访问应用"按钮，可以在新窗口打开对应的学生Web应用。

### 3. 使用命令行终端
点击顶部导航的"命令行终端"进入交互式终端界面，支持以下命令：
- `ls` - 列出文件
- `pwd` - 显示当前目录
- `echo <text>` - 输出文本
- `date` - 显示日期时间
- `whoami` - 显示当前用户
- `docker ps` - 显示运行中的容器
- `docker images` - 显示Docker镜像
- `clear` / `cls` - 清空终端
- `help` - 显示帮助信息

## 🔧 添加新的学生项目

在 `main.py` 中的 `students_projects` 列表添加新项目：

```python
students_projects.append({
    'id': 4,
    'name': '新同学',
    'project_name': '新项目名称',
    'description': '项目描述',
    'docker_image': 'student4/project:latest',
    'port': 5004
})
```

## 🐳 学生项目Docker部署示例

学生需要为自己的项目创建Dockerfile：

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

构建并推送镜像：

```bash
docker build -t studentX/project-name:latest .
docker push studentX/project-name:latest
```

## 🛡️ 安全说明

- 命令行终端实施了白名单机制，只允许执行预定义的安全命令
- 命令执行有5秒超时限制
- 建议在生产环境中进一步加强安全措施


## 📝 技术栈

- **后端**: Flask (Python)
- **前端**: HTML5, CSS3, JavaScript
- **容器化**: Docker, Docker Compose
- **交互**: AJAX, Fetch API

## 👥 贡献

欢迎提交Issue和Pull Request！

---

**数据库系统课程项目展示平台** © 2025
