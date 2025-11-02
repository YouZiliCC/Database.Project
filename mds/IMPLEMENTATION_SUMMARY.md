# 工作组申请功能实现总结

## 实现的功能

### ✅ 用户申请加入工作组
- 未加入任何工作组的用户可以向任意工作组发出加入申请
- 用户只能同时有一个待审核的申请
- 已提交申请的用户会看到"已申请，等待审核"的提示

### ✅ 组长审批申请
- 组长可以在工作组详情页看到所有待审核的申请列表
- 组长可以选择"接受"或"拒绝"申请
- 接受申请后，用户自动加入工作组
- 拒绝申请后，用户可以重新申请

## 代码变更文件列表

### 1. 数据库模型 (database/models.py)
- 新增 `GroupApplication` 模型
- 包含字段：aid, uid, gid, status, message, created_at, updated_at

### 2. 数据库操作 (database/actions.py)
- `create_group_application()` - 创建申请
- `update_group_application()` - 更新申请状态
- `delete_group_application()` - 删除申请
- `get_application_by_aid()` - 根据ID获取申请
- `get_pending_application()` - 获取用户对某工作组的待审核申请
- `get_group_pending_applications()` - 获取工作组的所有待审核申请
- `get_user_applications()` - 获取用户的所有申请

### 3. 路由和视图 (blueprints/group.py)
- `POST /group/<gid>/apply` - 用户申请加入
- `POST /group/<gid>/applications/<aid>/accept` - 组长接受申请
- `POST /group/<gid>/applications/<aid>/reject` - 组长拒绝申请
- 更新 `group_detail()` 视图，传递申请数据到模板

### 4. 前端模板 (templates/group/detail.html)
- 添加"申请加入"按钮（未加入工作组的用户可见）
- 添加"已申请，等待审核"提示（已申请的用户可见）
- 添加"待审核申请"列表（组长可见）
- 每个待审核申请显示：用户名、邮箱、申请时间、接受/拒绝按钮

### 5. JavaScript交互 (static/js/group.js)
- `applyToGroup(gid)` - 申请加入工作组
- `acceptApplication(gid, aid)` - 接受申请
- `rejectApplication(gid, aid)` - 拒绝申请

## 使用流程

### 用户申请流程
1. 用户访问工作组详情页
2. 如果用户未加入任何工作组，显示"申请加入"按钮
3. 点击按钮后提交申请，等待组长审核
4. 按钮变为"已申请，等待审核"（不可点击）

### 组长审批流程
1. 组长访问自己管理的工作组详情页
2. 在"待审核申请"区域看到所有申请
3. 点击"接受"按钮，用户加入工作组
4. 点击"拒绝"按钮，拒绝该申请

## 下一步操作

### 🔴 必须执行：数据库迁移
在使用新功能之前，必须先创建 `group_applications` 表。

请参考 `MIGRATION_GROUP_APPLICATION.md` 文件执行数据库迁移。

推荐方法（如果有 Flask-Migrate）：
```powershell
flask db migrate -m "Add group_applications table"
flask db upgrade
```

或者简单方法（使用 SQLAlchemy）：
```powershell
python
>>> from app import app
>>> from database.base import db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### 🎯 可选增强功能
以下是可以考虑的扩展功能：

1. **申请留言功能**
   - 用户申请时可以填写申请理由
   - 组长审核时可以看到申请留言

2. **邮件通知**
   - 用户申请后，发送邮件通知组长
   - 申请被处理后，发送邮件通知用户

3. **申请历史记录**
   - 用户可以查看自己的所有申请记录
   - 组长可以查看已处理的申请历史

4. **申请过期机制**
   - 超过一定时间未处理的申请自动过期
   - 或者允许用户撤回申请

## 技术要点

### 安全性
- ✅ 使用 `@login_required` 装饰器保护路由
- ✅ 使用 `@leader_required` 装饰器确保只有组长能审批
- ✅ CSRF 保护（通过 Flask-WTF）
- ✅ 数据验证（检查用户状态、工作组存在性等）

### 数据一致性
- ✅ 使用事务保证数据一致性
- ✅ 外键级联删除（CASCADE）
- ✅ 防止重复申请（同一用户对同一工作组只能有一个待审核申请）

### 用户体验
- ✅ AJAX 异步请求，无需刷新页面
- ✅ 实时反馈（Flash 消息）
- ✅ 确认对话框（防止误操作）
- ✅ 按钮状态显示（已申请时禁用）

## 测试建议

### 功能测试
1. ✅ 测试用户申请加入工作组
2. ✅ 测试组长接受申请
3. ✅ 测试组长拒绝申请
4. ✅ 测试防止重复申请
5. ✅ 测试已加入工作组的用户不能申请其他工作组

### 边界测试
1. ✅ 测试申请不存在的工作组
2. ✅ 测试非组长用户尝试审批申请
3. ✅ 测试处理已处理的申请
4. ✅ 测试用户已加入其他工作组时的申请

## 总结

所有功能已完整实现！核心流程为：

**用户申请** → **组长审核** → **用户加入工作组**

请执行数据库迁移后即可使用新功能。
