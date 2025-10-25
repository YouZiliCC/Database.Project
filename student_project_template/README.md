# 学生项目模板

这是一个简单的Flask项目模板，供学生参考使用。

## 文件说明

- `app.py` - Flask应用主文件
- `Dockerfile` - Docker镜像构建文件
- `requirements.txt` - Python依赖列表
- `templates/` - HTML模板目录
- `static/` - 静态资源目录

## 使用方法

1. 修改`app.py`实现你的功能
2. 在`templates/`中创建HTML页面
3. 在`static/`中添加CSS和JavaScript文件
4. 构建Docker镜像: `docker build -t 你的用户名/项目名:latest .`
5. 运行容器测试: `docker run -p 5000:5000 你的用户名/项目名:latest`

## 提交到展示平台

将你的项目信息告知管理员，包括：
- 姓名
- 项目名称
- 项目描述
- Docker镜像名称
- 运行端口
