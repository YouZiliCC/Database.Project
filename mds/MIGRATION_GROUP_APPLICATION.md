# 工作组申请功能 - 数据库迁移说明

## 新增功能
实现了用户申请加入工作组以及组长审批的功能。

## 数据库变更

### 新增表：group_applications

需要创建新的 `group_applications` 表，包含以下字段：

- `gaid` (String, Primary Key): 申请ID
- `uid` (String, Foreign Key -> users.uid): 申请用户ID
- `gid` (String, Foreign Key -> groups.gid): 目标工作组ID
- `status` (Integer): 申请状态 (0=待审核, 1=已接受, 2=已拒绝)
- `message` (Text, Nullable): 申请留言
- `created_at` (DateTime): 创建时间
- `updated_at` (DateTime): 更新时间

## 迁移步骤

### 方法1: 使用 Flask-Migrate (推荐)

如果项目使用了 Flask-Migrate，执行以下命令：

```powershell
# 生成迁移脚本
flask db migrate -m "Add group_applications table"

# 应用迁移
flask db upgrade
```

### 方法2: 直接使用 SQLAlchemy

如果没有使用 Flask-Migrate，在 Python shell 中执行：

```python
from app import app
from database.base import db

with app.app_context():
    db.create_all()
```

### 方法3: 手动 SQL (如果需要)

```sql
CREATE TABLE group_applications (
    gaid VARCHAR(512) PRIMARY KEY,
    uid VARCHAR(512) NOT NULL,
    gid VARCHAR(512) NOT NULL,
    status INTEGER NOT NULL DEFAULT 0,
    message TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (gid) REFERENCES groups(gid) ON DELETE CASCADE
);

CREATE INDEX idx_group_applications_uid ON group_applications(uid);
CREATE INDEX idx_group_applications_gid ON group_applications(gid);
CREATE INDEX idx_group_applications_status ON group_applications(status);
```

## 功能说明

### 用户端功能
1. **申请加入工作组**: 未加入任何工作组的用户可以在工作组详情页点击"申请加入"按钮
2. **查看申请状态**: 如果已提交申请，按钮会显示"已申请，等待审核"
3. **一次只能申请一个**: 用户只能向一个工作组提交待审核的申请

### 组长端功能
1. **查看待审核申请**: 组长在工作组详情页可以看到"待审核申请"列表
2. **接受申请**: 点击"接受"按钮将用户加入工作组
3. **拒绝申请**: 点击"拒绝"按钮拒绝申请

## 相关文件变更

### 后端文件
- `database/models.py` - 新增 GroupApplication 模型
- `database/actions.py` - 新增申请相关 CRUD 操作函数
- `blueprints/group.py` - 新增申请、接受、拒绝申请的路由

### 前端文件
- `templates/group/detail.html` - 更新页面显示申请按钮和待审核列表
- `static/js/group.js` - 新增申请相关的 JavaScript 交互函数

## API 端点

### POST /group/<gid>/apply
用户申请加入工作组

**权限**: 需要登录，未加入任何工作组

**响应**:
- 200: 申请提交成功
- 400: 用户已加入工作组或已有待审核申请
- 404: 工作组不存在

### POST /group/<gid>/applications/<gaid>/accept
组长接受申请

**权限**: 需要是该工作组的组长

**响应**:
- 200: 接受成功
- 400: 申请已被处理或用户已加入其他工作组
- 404: 申请不存在

### POST /group/<gid>/applications/<gaid>/reject
组长拒绝申请

**权限**: 需要是该工作组的组长

**响应**:
- 200: 拒绝成功
- 400: 申请已被处理
- 404: 申请不存在

## 注意事项

1. 当用户被接受加入工作组后，申请状态会更新为"已接受"(status=1)
2. 当申请被拒绝后，申请状态会更新为"已拒绝"(status=2)
3. 用户只能有一个待审核(status=0)的申请
4. 当工作组或用户被删除时，相关申请会自动删除（CASCADE）
5. 申请记录会保留在数据库中用于审计，不会自动删除
