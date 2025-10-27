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
    

@user_bp.route("/", methods=["GET"])
def user_list():
    """用户列表页面"""
    users = list_all_users()
    return render_template("user/list.html", users=users)





# edit

# as leader