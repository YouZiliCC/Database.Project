# ⚠️ 关键：使用 eventlet 时必须在所有 import 之前调用 monkey_patch()
# 这会将标准库的阻塞操作（线程、锁、socket等）替换为非阻塞的绿色版本
import eventlet
eventlet.monkey_patch()

from app import create_app
from flask import render_template

# 创建应用实例
app, socketio = create_app()


# 全局错误处理
@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("errors/500.html"), 500


@app.route("/health")
def health_check():
    return {"status": "ok", "service": "DBSYS"}, 200


if __name__ == "__main__":
    # 支持websocket
    socketio.run(
        app,
        debug=app.config["DEBUG"],
        host=app.config["HOST"],
        port=app.config["PORT"],
        allow_unsafe_werkzeug=True,
    )
