from datetime import timedelta
from flask import Flask
from flask_wtf import CSRFProtect
from database.base import db, login_manager
from database.actions import create_user, get_user_by_uname
from dotenv import load_dotenv
from markupsafe import Markup
import logging
import os
import markdown


def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    # 加载环境变量
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        load_dotenv(env_path)
    except Exception as e:
        app.logger.error(f"加载环境变量失败: {e}", exc_info=True)
    
    app.config["WORKING_DIR"] = os.getcwd()

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = os.getenv(
        "SQLALCHEMY_TRACK_MODIFICATIONS"
    )

    # 数据库连接池配置（提升性能）
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": int(
            os.getenv("SQLALCHEMY_ENGINE_OPTIONS_POOL_SIZE", 10)
        ),  # 连接池大小
        "pool_recycle": int(
            os.getenv("SQLALCHEMY_ENGINE_OPTIONS_POOL_RECYCLE", 3600)
        ),  # 连接回收时间（秒）
        "pool_pre_ping": os.getenv("SQLALCHEMY_ENGINE_OPTIONS_POOL_PRE_PING", "True")
        == "True",  # 连接前检查是否有效
        "max_overflow": int(
            os.getenv("SQLALCHEMY_ENGINE_OPTIONS_MAX_OVERFLOW", 20)
        ),  # 超过 pool_size 后最多再创建的连接数
    }

    app.config["LOG_LEVEL"] = os.getenv("LOG_LEVEL")
    app.config["ADMIN_ONLY_LOGIN"] = os.getenv("ADMIN_ONLY_LOGIN", "False") == "True"
    app.config["TEACHER_REGISTRATION_CODE"] = os.getenv("TEACHER_REGISTRATION_CODE")
    # 测试服务器配置
    app.config["PORT"] = int(os.getenv("PORT", 5000))
    app.config["HOST"] = os.getenv("HOST", "0.0.0.0")
    app.config["DEBUG"] = os.getenv("DEBUG", "False") == "True"
    # Docker配置
    app.config["IMAGE_NAME"] = os.getenv("IMAGE_NAME", "imds:latest")

    # CSRF保护
    csrf = CSRFProtect()
    csrf.init_app(app)

    # 初始化数据库
    db.init_app(app)

    # 启用 SQLite 外键约束（测试环境）
    if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # 初始化登录管理器
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "请登录以访问此页面"
    login_manager.login_message_category = "warning"
    login_manager.remember_cookie_duration = timedelta(days=7)

    # 自定义未授权处理器：对 AJAX 请求返回 401，对普通请求重定向到登录页面
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, jsonify, redirect, url_for, flash

        # 检查是否是 AJAX/API 请求
        # 1. 检查 Accept 头是否包含 application/json
        # 2. 检查 Content-Type 是否为 application/json
        # 3. 检查 X-Requested-With 头（兼容旧代码）
        is_ajax = (
            request.is_json
            or "application/json" in request.headers.get("Accept", "")
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.headers.get("X-CSRFToken")  # fetch 请求通常会带 CSRF token
        )

        if is_ajax:
            return jsonify({"success": False, "message": "请先登录"}), 401

        # 普通请求重定向到登录页面
        flash("请登录以访问此页面", "warning")
        return redirect(url_for("auth.login", next=request.url))

    # 注册蓝图
    from blueprints.index import index_bp
    from blueprints.auth import auth_bp
    from blueprints.user import user_bp
    from blueprints.group import group_bp
    from blueprints.project import project_bp
    from blueprints.admin import admin_bp
    from blueprints.api import api_bp

    # 将蓝图注册到应用
    app.register_blueprint(index_bp)
    # 除主页面之外均制定前缀，避免与主页面路由冲突
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(group_bp, url_prefix="/group")
    app.register_blueprint(project_bp, url_prefix="/project")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    # 注册 Markdown 过滤器
    @app.template_filter("markdown")
    def markdown_filter(text):
        """将 Markdown 文本转换为 HTML"""
        if not text:
            return ""
        md = markdown.Markdown(
            extensions=[
                "extra",  # 支持表格、代码块等扩展语法
                "codehilite",  # 代码高亮
                "fenced_code",  # 围栏代码块
                "nl2br",  # 换行转 <br>
                "sane_lists",  # 更好的列表支持
            ]
        )
        return Markup(md.convert(text))

    # 创建数据库表
    with app.app_context():
        db.create_all()
        # 初始化默认管理员用户
        initial_admin = {
            "uname": os.getenv("INITIAL_ADMIN_UNAME"),
            "uinfo": os.getenv("INITIAL_ADMIN_USER_INFO"),
            "password": os.getenv("INITIAL_ADMIN_PASSWORD"),
            "email": os.getenv("INITIAL_ADMIN_EMAIL"),
            "role": int(os.getenv("INITIAL_ADMIN_ROLE", 1)),
            "sid": os.getenv("INITIAL_ADMIN_SID"),
        }
        if initial_admin and not get_user_by_uname(initial_admin["uname"]):
            try:
                admin = create_user(**initial_admin)
                if admin and admin.is_admin:
                    app.logger.info(
                        f"默认管理员用户已创建: {admin.uname} / {admin.email}"
                    )
            except Exception as e:
                app.logger.error(f"初始化默认管理员用户失败: {e}", exc_info=True)

    # 配置日志
    logging.basicConfig(
        level=app.config["LOG_LEVEL"], format="[%(levelname)s] %(name)s : %(message)s"
    )
    app.logger.setLevel(app.config["LOG_LEVEL"])

    app.logger.info("Flask应用初始化完成")
    return app
