from flask import Flask, render_template, request, jsonify
import subprocess
import os

app = Flask(__name__)

# 模拟学生项目数据
students_projects = [
    {
        'id': 1,
        'name': '张三',
        'project_name': '图书管理系统',
        'description': '基于Flask的图书借阅管理系统',
        'docker_image': 'student1/library-system:latest',
        'port': 5001
    },
    {
        'id': 2,
        'name': '李四',
        'project_name': '在线商城',
        'description': '电子商务平台Demo',
        'docker_image': 'student2/shop-system:latest',
        'port': 5002
    },
    {
        'id': 3,
        'name': '王五',
        'project_name': '学生信息管理',
        'description': '学生信息CRUD系统',
        'docker_image': 'student3/student-system:latest',
        'port': 5003
    }
]

@app.route('/')
def index():
    """主页 - 显示所有学生项目"""
    return render_template('index.html', projects=students_projects)

@app.route('/terminal')
def terminal():
    """命令行交互页面"""
    return render_template('terminal.html')

@app.route('/api/execute', methods=['POST'])
def execute_command():
    """执行命令行命令（安全限制版本）"""
    data = request.json
    command = data.get('command', '')
    
    # 安全限制：只允许特定命令
    allowed_commands = ['ls', 'pwd', 'echo', 'date', 'whoami', 'docker ps', 'docker images']
    
    # 检查命令是否在允许列表中
    if not any(command.startswith(cmd) for cmd in allowed_commands):
        return jsonify({
            'output': f'错误：命令 "{command}" 不在允许列表中\n允许的命令：{", ".join(allowed_commands)}',
            'success': False
        })
    
    try:
        # 执行命令
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout if result.stdout else result.stderr
        return jsonify({
            'output': output if output else '命令执行成功，无输出',
            'success': result.returncode == 0
        })
    except subprocess.TimeoutExpired:
        return jsonify({
            'output': '错误：命令执行超时',
            'success': False
        })
    except Exception as e:
        return jsonify({
            'output': f'错误：{str(e)}',
            'success': False
        })

@app.route('/api/projects')
def get_projects():
    """API：获取所有项目信息"""
    return jsonify(students_projects)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """项目详情页"""
    project = next((p for p in students_projects if p['id'] == project_id), None)
    if project:
        return render_template('project_detail.html', project=project)
    return "项目未找到", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
