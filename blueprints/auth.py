from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from database.actions import *
import logging

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


# 创建登录表单类
class LoginForm(FlaskForm):
    account = StringField("邮箱/用户名", validators=[DataRequired()])
    password = PasswordField("密码", validators=[DataRequired(), Length(min=6)])
    remember_me = BooleanField("记住我")
    submit = SubmitField("登录")


# 创建注册表单类
class RegisterForm(FlaskForm):
    uname = StringField("用户名", validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField("邮箱", validators=[DataRequired(), Email()])
    sid = StringField("学号", validators=[DataRequired(), Length(min=10, max=10)])
    password = PasswordField("密码", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        "确认密码",
        validators=[
            DataRequired(),
            EqualTo("password", message="密码不一致"),
        ],
    )
    submit = SubmitField("注册")

    # 自定义验证器
    def validate_uname(self, uname):
        if get_user_by_uname(uname.data) or get_user_by_email(uname.data):
            raise ValidationError("该用户名已被使用，请选择其他用户名")

    def validate_email(self, email):
        if get_user_by_email(email.data):
            raise ValidationError("该邮箱已被注册，请使用其他邮箱")

    def validate_sid(self, sid):
        if get_user_by_sid(sid.data):
            raise ValidationError("该学号已被注册，请使用其他学号")
        if len(sid.data) != 10 or not sid.data.isdigit():
            raise ValidationError("学号格式不正确，应为10位数字")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # 创建表单实例
    form = LoginForm()
    # 检查是否只允许管理员登录（从配置中获取）
    admin_only_login = current_app.config.get("ADMIN_ONLY_LOGIN", False)
    # 处理表单提交
    if form.validate_on_submit():
        # 查找用户
        user = get_user_by_email(form.account.data)
        if not user:
            user = get_user_by_uname(form.account.data)
        # 验证用户和密码
        if user and user.check_password(form.password.data):
            # 检查是否只允许管理员登录且当前用户不是管理员
            if admin_only_login and not user.is_admin:
                flash("系统当前设置为仅允许管理员登录，请联系管理员", "danger")
                return render_template("auth/login.html", form=form)
            # 登录用户
            login_user(user, remember=form.remember_me.data)
            # 获取next参数，如果存在则重定向到该URL
            next_page = request.args.get("next")
            # 重定向到首页或next页面
            return redirect(next_page or url_for("index.index"))
        else:
            # 登录失败提示
            flash("账户和密码不匹配", "danger")
    # 渲染模板并传递表单
    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # 如果用户已登录，重定向到首页
    if current_user.is_authenticated:
        return redirect(url_for("index.index"))
    # 检查是否只允许管理员登录（从配置中获取）
    admin_only_login = current_app.config.get("ADMIN_ONLY_LOGIN", False)
    # 如果开启了管理员专属模式，禁止注册
    if admin_only_login:
        flash("系统当前设置为仅允许管理员使用，注册功能已关闭", "danger")
        return redirect(url_for("auth.login"))
    # 创建注册表单实例
    form = RegisterForm()
    # 处理表单提交
    if form.validate_on_submit():
        # 创建新用户
        create_user(
            uname=form.uname.data,
            email=form.email.data,
            sid=form.sid.data,
            password=form.password.data,
        )
        if not create_user:
            flash("注册失败，请重试", "danger")
            logger.warning(f"注册用户失败: {form.uname.data} / {form.email.data}")
            return render_template("auth/register.html", form=form)
        flash("注册成功！现在您可以登录了", "success")
        logger.info(f"注册用户成功: {form.uname.data} / {form.email.data}")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout", methods=["GET"])
@login_required
def logout():
    # 登出逻辑
    logout_user()
    return redirect(url_for("index.index"))
