from flask import Blueprint, render_template

index_bp = Blueprint("index", __name__)

@index_bp.route("/")
def index():
    """主页"""
    return render_template("index.html")