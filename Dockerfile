# 使用官方Python运行时作为基础镜像
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml ./

# 安装依赖
RUN pip install --no-cache-dir .

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# 运行应用
CMD ["python", "main.py"]
