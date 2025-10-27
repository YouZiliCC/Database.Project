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
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from database.actions import *
from blueprints.auth import login_required
import logging

user_bp = Blueprint("user", __name__)
logger = logging.getLogger(__name__)

# details

# TODO: 学号解析工具
# def parse_student_id(sid: str) -> dict:
#     """解析学号，返回包含院系和专业信息的字典"""
#     # 假设学号格式为: YYYYMMDD-XXXX-XX
#     try:
#         date_part, dept_code, major_code = sid.split("-")
#         return {
#             "admission_date": datetime.strptime(date_part, "%Y%m%d"),
#             "department": DEPARTMENT_MAP.get(dept_code, "未知"),
#             "major": MAJOR_MAP.get(major_code, "未知"),
#         }
#     except ValueError:
#         logger.error(f"学号解析失败: {sid}")
#         return {"error": "学号格式错误"}
# 字段
# 用户信息表单类
class UserForm(FlaskForm):
    uname = StringField("用户名", validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField("邮箱", validators=[DataRequired(), Email(), Length(max=100)])
    sid = StringField("学号", validators=[DataRequired(), Length(min=10, max=10)])
    #TODO uimg = StringField("用户头像URL", validators=[Length(max=200)])
    uinfo = StringField("个人简介", validators=[Length(max=200)])
    submit = SubmitField("保存")

    # 自定义验证器
    def validate_uname(self, uname):
        if get_user_by_username(uname.data) or get_user_by_email(uname.data):
            raise ValidationError("该用户名已被使用，请选择其他用户名")

    def validate_email(self, email):
        if get_user_by_email(email.data):
            raise ValidationError("该邮箱已被注册，请使用其他邮箱")
    
    def validate_sid(self, sid):
        if get_user_by_sid(sid.data):
            raise ValidationError("该学号已被注册，请使用其他学号")
        if len(sid.data) != 10 or not sid.data.isdigit():
            raise ValidationError("学号格式不正确，应为10位数字")

@user_bp.route("/", methods=["GET"])
def user_list():
    """用户列表页面"""
    users = list_all_users()
    return render_template("user/list.html", users=users)


# TODO
@user_bp.route("/me", methods=["GET"])
@login_required
def user_me():
    """当前用户信息页面"""
    user = current_user
    if not user:
        abort(404, description="用户不存在")
    return render_template("user/detail.html", user=user)


@user_bp.route("/<uuid:uid>", methods=["GET"])
def user_detail(uid):
    """用户详情页面"""
    uid = str(uid)
    user = get_user_by_id(uid)
    if not user:
        abort(404, description="用户不存在")
    return render_template("user/detail.html", user=user)


# TODO: 模态窗口
@user_bp.route("/me/edit", methods=["GET", "POST"])
@login_required
def user_edit():
    """用户编辑页面"""
    user = current_user
    if not user:
        flash("用户不存在", "warning")
        return jsonify({"error": "用户不存在"}), 404
    form = UserForm(obj=user)
    if form.validate_on_submit():
        updated_user = update_user(
            user,
            uname=form.uname.data,
            email=form.email.data,
            sid=form.sid.data,
            uinfo=form.uinfo.data,
            # TODO uimg=form.uimg.data,
        )
        if not updated_user:
            flash("更新用户信息失败，请重试", "danger")
            logger.warning(f"更新用户信息失败: {form.uname.data}")
            return jsonify({"error": "更新用户信息失败"}), 500
        flash("用户信息更新成功", "success")
        logger.info(f"更新用户信息成功: {form.uname.data} by user {current_user.uname}")
        return jsonify({"message": "用户信息更新成功"}), 200
    return render_template("user/edit.html", form=form, user=user)


#TODO: Password change

#TODO: EMAIL change

#TODO: IMAGE upload

#TODO: join group

#TODO: leave group

#TODO: delete account