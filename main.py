from app import create_app
from flask import render_template

# 创建应用实例
app = create_app()


# # 全局错误处理
# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template("errors/404.html"), 404


# @app.errorhandler(500)
# def internal_server_error(e):
#     return render_template("errors/500.html"), 500


@app.route("/health")
def health_check():
    return {"status": "ok", "service": "DBSYS"}, 200


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], host=app.config["HOST"], port=app.config["PORT"])
