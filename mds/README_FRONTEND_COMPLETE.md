# 数据库系统课程项目 - 前端完整实现

## 项目概览

本项目是一个基于 Flask 的数据库系统课程项目展示平台，提供了完整的前后端实现。

## 技术栈

- **后端**: Flask + SQLAlchemy + Flask-Login
- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **数据库**: SQLite (可配置为其他数据库)
- **样式**: 自定义 CSS，支持亮色/暗色主题切换

## 功能模块

### 1. 用户认证模块 (`/auth`)
- **登录** (`/auth/login`): 支持用户名/邮箱登录，记住我功能
- **注册** (`/auth/register`): 用户注册，包含用户名、邮箱、学号、密码验证
- **登出** (`/auth/logout`): 安全登出

### 2. 用户管理模块 (`/user`)
- **用户列表** (`/user`): 展示所有用户，支持搜索和排序
- **用户详情** (`/user/<uid>`): 查看用户详细信息
- **个人中心** (`/user/me`): 当前用户信息
- **编辑资料** (`/user/me/edit`): 修改个人信息
- **工作组操作**:
  - 加入工作组 (`/user/me/join/<gid>`)
  - 退出工作组 (`/user/me/leave`)

### 3. 工作组管理模块 (`/group`)
- **工作组列表** (`/group`): 卡片式展示所有工作组
- **工作组详情** (`/group/<gid>`): 查看成员、项目列表
- **创建工作组** (`/group/create`): 创建新工作组（创建者自动成为组长）
- **编辑工作组** (`/group/<gid>/edit`): 修改工作组信息（组长权限）
- **更换组长** (`/group/<gid>/change_leader`): 转移组长权限
- **成员管理**:
  - 移除成员 (`/group/<gid>/members/<uid>/remove`)
- **项目管理**:
  - 创建项目 (`/group/<gid>/projects/create`)
  - 删除项目 (`/group/<gid>/projects/<pid>/delete`)

### 4. 项目展示模块 (`/project`)
- **项目列表** (`/project`): 卡片式展示所有项目
- **项目详情** (`/project/<pid>`): 查看项目信息、Docker配置
- **编辑项目** (`/project/<pid>/edit`): 修改项目信息（组内成员权限）
- **访问项目**: 直接跳转到项目运行的端口

### 5. 管理员面板 (`/admin`)
- **仪表盘** (`/admin/dashboard`): 
  - 统计数据展示（用户数、工作组数、项目数）
  - 用户管理（删除用户、重置密码）
  - 工作组管理（删除工作组）
  - 项目管理（删除项目）

### 6. API 接口 (`/api`)
- `/api/users`: 获取所有用户列表（JSON）
- `/api/groups`: 获取所有工作组列表（JSON）
- `/api/projects`: 获取所有项目列表（JSON）

## 前端架构

### 模板结构

```
templates/
├── base.html                  # 基础模板（导航栏、页脚、flash消息）
├── index.html                 # 首页
├── auth/
│   ├── login.html            # 登录页
│   └── register.html         # 注册页
├── user/
│   ├── list.html             # 用户列表
│   ├── detail.html           # 用户详情
│   └── edit.html             # 编辑资料
├── group/
│   ├── list.html             # 工作组列表
│   ├── detail.html           # 工作组详情
│   ├── create.html           # 创建工作组
│   ├── edit.html             # 编辑工作组
│   └── change_leader.html    # 更换组长
├── project/
│   ├── list.html             # 项目列表
│   ├── detail.html           # 项目详情
│   ├── create.html           # 创建项目
│   ├── edit.html             # 编辑项目
│   └── terminal.html         # 终端页面
├── admin/
│   └── dashboard.html        # 管理员仪表盘
└── errors/
    ├── 404.html              # 404 错误页
    └── 500.html              # 500 错误页
```

### JavaScript 模块

```
static/js/
├── app.js         # 全局脚本：主题切换、flash消息、列表搜索/排序/分页
├── user.js        # 用户相关交互：加入/退出工作组、删除账号
├── group.js       # 工作组相关交互：成员管理、项目管理、删除工作组
├── admin.js       # 管理员面板：数据加载、统计、CRUD操作
└── terminal.js    # 终端交互（预留）
```

### CSS 样式

`static/css/style.css` 包含：
- 全局样式和排版
- 响应式布局（移动端适配）
- 组件样式（按钮、卡片、表格、表单、模态框等）
- 主题系统（亮色/暗色主题）
- 特殊页面样式（管理员面板、项目详情、终端等）

## 核心功能特性

### 1. 主题切换
- 支持亮色/暗色主题
- 使用 localStorage 持久化用户偏好
- 一键切换，全局生效

### 2. 前端交互
- **AJAX 操作**: 所有增删改操作使用 AJAX，无需页面刷新
- **确认对话框**: 危险操作（删除等）有二次确认
- **实时反馈**: 操作结果通过 alert 或 flash 消息提示
- **表单验证**: 客户端验证 + 服务端验证双重保障

### 3. 权限控制
- **普通用户**: 查看、加入工作组、编辑个人信息
- **组长**: 管理成员、创建/编辑/删除项目、更换组长
- **管理员**: 完全控制权限，管理所有用户、工作组、项目

### 4. 搜索与排序
- 用户列表、工作组列表、项目列表均支持实时搜索
- 支持按名称升序/降序排序
- 前端分页功能（可配置每页显示数量）

### 5. 卡片式设计
- 工作组和项目采用卡片式布局
- 响应式网格，自动适配不同屏幕尺寸
- 悬停效果，提升用户体验

## 数据模型

### User（用户）
- `uid`: 用户ID（UUID）
- `uname`: 用户名
- `email`: 邮箱
- `sid`: 学号（10位数字）
- `uinfo`: 个人简介
- `gid`: 所属工作组ID
- `role`: 角色（0=普通用户，1=管理员）

### Group（工作组）
- `gid`: 工作组ID（UUID）
- `gname`: 工作组名称
- `ginfo`: 工作组描述
- `leader_id`: 组长用户ID
- `users`: 成员列表（一对多关系）
- `projects`: 项目列表（一对多关系）

### Project（项目）
- `pid`: 项目ID（UUID）
- `pname`: 项目名称
- `pinfo`: 项目描述
- `gid`: 所属工作组ID
- `docker_name`: Docker容器ID
- `port`: 对外访问端口
- `docker_port`: Docker内部端口

## 使用说明

### 1. 环境配置

创建 `.env` 文件：

```env
SECRET_KEY=your-secret-key-here
SQLALCHEMY_DATABASE_URI=sqlite:///instance/dbsys.db
SQLALCHEMY_TRACK_MODIFICATIONS=False
LOG_LEVEL=INFO
DEBUG=True
HOST=0.0.0.0
PORT=5000

# 管理员账号
INITIAL_ADMIN_UNAME=admin
INITIAL_ADMIN_USER_INFO=系统管理员
INITIAL_ADMIN_PASSWORD=admin123
INITIAL_ADMIN_EMAIL=admin@dbsys.com
INITIAL_ADMIN_ROLE=1
INITIAL_ADMIN_SID=0000000000

# 仅管理员登录模式（可选）
ADMIN_ONLY_LOGIN=False
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行应用

```bash
python main.py
```

访问: `http://localhost:5000`

### 4. 默认管理员账号

- 用户名: `admin`
- 密码: `admin123`

## API 使用示例

### 获取用户列表
```javascript
fetch('/api/users', {
    credentials: 'same-origin'
})
.then(res => res.json())
.then(users => console.log(users));
```

### 加入工作组
```javascript
fetch('/user/me/join/<gid>', {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
        'X-CSRFToken': document.querySelector('[name="csrf_token"]').value
    }
})
.then(res => res.json())
.then(data => console.log(data));
```

## 页面路由完整列表

### 公开页面
- `/` - 首页
- `/auth/login` - 登录
- `/auth/register` - 注册
- `/user` - 用户列表
- `/user/<uid>` - 用户详情
- `/group` - 工作组列表
- `/group/<gid>` - 工作组详情
- `/project` - 项目列表
- `/project/<pid>` - 项目详情

### 需要登录
- `/auth/logout` - 登出
- `/user/me` - 个人中心
- `/user/me/edit` - 编辑资料
- `/user/me/join/<gid>` - 加入工作组
- `/user/me/leave` - 退出工作组
- `/group/create` - 创建工作组
- `/group/my_group` - 我的工作组

### 组长权限
- `/group/<gid>/edit` - 编辑工作组
- `/group/<gid>/change_leader` - 更换组长
- `/group/<gid>/members/<uid>/remove` - 移除成员
- `/group/<gid>/projects/create` - 创建项目
- `/group/<gid>/projects/<pid>/delete` - 删除项目

### 组内成员权限
- `/project/<pid>/edit` - 编辑项目

### 管理员权限
- `/admin/dashboard` - 管理员仪表盘
- `/admin/del_user/<uid>` - 删除用户
- `/admin/reset_password/<uid>` - 重置密码
- `/admin/del_group/<gid>` - 删除工作组
- `/admin/del_projects/<pid>` - 删除项目

## 样式定制

### 修改主题色

在 `style.css` 中修改以下变量：

```css
/* 主色调 */
.btn-primary { background: #0d6efd; }

/* Hero 渐变 */
.hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }

/* 卡片阴影 */
.card { box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
```

### 添加自定义组件

参考现有组件的 HTML 结构和 CSS 类名，保持一致的设计风格。

## 安全考虑

1. **CSRF 保护**: 所有 POST 请求必须包含 CSRF Token
2. **密码加密**: 使用 werkzeug 的 password hash
3. **权限验证**: 后端验证用户权限
4. **SQL 注入防护**: 使用 SQLAlchemy ORM
5. **XSS 防护**: Jinja2 自动转义

## 已删除的无效文件

以下文件已被删除（与 detail.html 重复或未使用）：
- `templates/user/profile.html`
- `templates/group/profile.html`
- `templates/project/profile.html`
- `templates/project/project_detail.html`

## 浏览器支持

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- 不支持 IE

## 开发建议

1. **修改模板**: 在 `templates/` 目录下修改 HTML
2. **修改样式**: 在 `static/css/style.css` 中修改 CSS
3. **修改交互**: 在 `static/js/` 目录下修改 JavaScript
4. **添加路由**: 在 `blueprints/` 目录下添加新的蓝图

## 常见问题

### 1. 如何添加新页面？

1. 在对应蓝图中添加路由
2. 创建对应的模板文件（继承 base.html）
3. 如需特殊样式，在 style.css 中添加
4. 如需交互，在对应 JS 文件中添加

### 2. 如何修改导航栏？

编辑 `templates/base.html` 中的 `<nav>` 部分。

### 3. 如何添加新的用户角色？

1. 修改 `database/models.py` 中的 User 模型
2. 更新权限装饰器
3. 在模板中添加对应的权限判断

## 作者

数据库系统课程项目组

## 更新日志

### 2025-11-01
- ✅ 完成所有认证、用户、工作组、项目、管理员模板
- ✅ 实现完整的 JavaScript 交互功能
- ✅ 重构并增强 CSS 样式系统
- ✅ 删除重复和无效文件
- ✅ 添加主题切换功能
- ✅ 优化响应式布局
- ✅ 完善权限控制和安全措施

## 许可证

MIT License
