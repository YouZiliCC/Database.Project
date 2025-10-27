from datetime import timedelta
from flask import Flask
from flask_wtf import CSRFProtect
from database.base import db, login_manager
from database.actions import create_user, get_user_by_username
from dotenv import load_dotenv
import logging
import os


def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    # 加载环境变量
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        load_dotenv(env_path)
    except Exception as e:
        app.logger.error(f"加载环境变量失败: {e}", exc_info=True)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
    app.config['LOG_LEVEL'] = os.getenv('LOG_LEVEL')
    app.config['ADMIN_ONLY_LOGIN'] = os.getenv('ADMIN_ONLY_LOGIN', 'False') == 'True'
    app.config['PORT'] = int(os.getenv('PORT', 5000))
    app.config['HOST'] = os.getenv('HOST', '0.0.0.0')
    app.config['DEBUG'] = os.getenv('DEBUG', 'False') == 'True'
    
    # CSRF保护
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # 初始化数据库
    db.init_app(app)
    
    # 初始化登录管理器
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "请登录以访问此页面"
    login_manager.login_message_category = "warning"
    login_manager.remember_cookie_duration = timedelta(days=7)

    # 注册蓝图
    from blueprints.index import index_bp
    from blueprints.auth import auth_bp
    from blueprints.user import user_bp
    from blueprints.group import group_bp
    from blueprints.project import project_bp
    from blueprints.admin import admin_bp

    # 将蓝图注册到应用
    app.register_blueprint(index_bp)
    # 除主页面之外均制定前缀，避免与主页面路由冲突
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(group_bp, url_prefix="/group")
    app.register_blueprint(project_bp, url_prefix="/project")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # 创建数据库表
    with app.app_context():
        db.create_all()
        # 初始化默认管理员用户
        initial_admin = {
            "uname": os.getenv('INITIAL_ADMIN_UNAME'),
            "uinfo": os.getenv('INITIAL_ADMIN_USER_INFO'),
            "password": os.getenv('INITIAL_ADMIN_PASSWORD'),
            "email": os.getenv('INITIAL_ADMIN_EMAIL'),
            "role": int(os.getenv('INITIAL_ADMIN_ROLE', 1)),
            "sid": os.getenv('INITIAL_ADMIN_SID')
        }
        if initial_admin and not get_user_by_username(initial_admin["uname"]):
            try:
                admin = create_user(**initial_admin)
                if admin and admin.is_admin:
                    app.logger.info(f"默认管理员用户已创建: {admin.uname} / {admin.email}")
            except Exception as e:
                app.logger.error(f"初始化默认管理员用户失败: {e}", exc_info=True)

    # 配置日志
    logging.basicConfig(level=app.config["LOG_LEVEL"],
                        format='[%(levelname)s] %(name)s : %(message)s')
    app.logger.setLevel(app.config["LOG_LEVEL"])

    app.logger.info("Flask应用初始化完成")
    return app