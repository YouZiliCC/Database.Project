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


@user_bp.route("/", methods=["GET"])
def user_list():
    """用户列表页面"""
    users = list_all_users()
    return render_template("user/list.html", users=users)





# edit

# as leader