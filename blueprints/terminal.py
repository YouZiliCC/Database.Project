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
from database.actions import *
import logging

terminal_bp = Blueprint("terminal", __name__)
logger = logging.getLogger(__name__)

