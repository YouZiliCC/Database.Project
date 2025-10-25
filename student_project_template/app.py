from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    """首页"""
    return render_template('index.html', 
                         student_name='你的姓名',
                         project_name='你的项目名称')

@app.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')

# 添加更多路由...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
