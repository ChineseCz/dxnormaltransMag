# 文件管理系统实现方案

## 📋 需求概述

实现一个支持以下功能的文件管理系统：
1. **文件树结构** - 支持文件夹层级结构
2. **批量上传** - 一次上传多个文件
3. **用户隔离** - 每个用户有独立的文件空间
4. **不同模式** - 支持不同的存储模式（如数据集模式、个人文件模式等）

## 🗄️ 数据库设计

### 文件夹表 (t_folder)
```sql
CREATE TABLE t_folder (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES t_user(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES t_folder(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,  -- 完整路径，如 /root/folder1/subfolder
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, parent_id, name)
);
```

### 文件表 (t_file)
```sql
CREATE TABLE t_file (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES t_user(id) ON DELETE CASCADE,
    folder_id INTEGER REFERENCES t_folder(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL DEFAULT 0,
    mime_type VARCHAR(100),
    storage_path TEXT NOT NULL,  -- users/{user_id}/files/{uuid}
    file_hash VARCHAR(64),
    metadata JSONB,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, folder_id, filename)
);
```

## 📁 存储路径结构

```
users/
  ├── {user_id}/
  │   └── files/
  │       ├── {uuid1}.ext
  │       ├── {uuid2}.ext
  │       └── ...
```

## 🔌 API 接口设计

### 文件夹管理
- `GET /api/files/folders/tree` - 获取文件夹树形结构
- `POST /api/files/folders` - 创建文件夹
- `PUT /api/files/folders/{id}` - 重命名文件夹
- `DELETE /api/files/folders/{id}` - 删除文件夹（级联删除子文件夹和文件）

### 文件管理
- `GET /api/files/list` - 列出文件（支持按文件夹筛选）
- `POST /api/files/upload` - 单文件上传
- `POST /api/files/batch-upload` - 批量上传（核心功能）
- `POST /api/files/move` - 批量移动文件
- `PUT /api/files/{id}/rename` - 重命名文件
- `DELETE /api/files/{id}` - 删除文件
- `GET /api/files/{id}/download` - 下载文件

## 🔐 用户隔离机制

1. **数据库层隔离**：所有查询都带 `user_id` 过滤条件
2. **存储层隔离**：文件存储在 `users/{user_id}/files/` 目录下
3. **API层验证**：每个接口都通过JWT验证用户身份
4. **权限检查**：操作前验证资源所有权

## 🚀 实现步骤

### 第一步：数据库迁移
```bash
# 执行迁移脚本
psql -U postgres -d your_database -f backend/migrations/003_create_file_system.sql
```

### 第二步：后端API实现
文件：`backend/api/files/routes.py`

核心功能：
1. 文件夹树形结构查询（递归CTE）
2. 批量上传接口（接收多个文件）
3. 文件去重（基于SHA256哈希）
4. 用户权限验证

### 第三步：集成到主应用
在 `backend/main.py` 中注册路由：
```python
from backend.api.files.routes import router as files_router
app.include_router(files_router, prefix="/api/files", tags=["files"])
```

## 💡 核心特性

### 1. 批量上传实现
```python
@router.post('/batch-upload')
async def batch_upload(
    files: List[UploadFile] = File(...),
    folder_id: Optional[int] = Form(None),
    user: dict = Depends(get_current_user)
):
    # 验证文件夹所有权
    # 批量处理文件
    # 计算哈希去重
    # 保存到存储层
    # 批量插入数据库
    pass
```

### 2. 文件树查询
使用PostgreSQL递归CTE查询文件夹树：
```sql
WITH RECURSIVE folder_tree AS (
    SELECT id, parent_id, name, path, 0 as level
    FROM t_folder
    WHERE user_id = %s AND parent_id IS NULL
    UNION ALL
    SELECT f.id, f.parent_id, f.name, f.path, ft.level + 1
    FROM t_folder f
    INNER JOIN folder_tree ft ON f.parent_id = ft.id
)
SELECT * FROM folder_tree ORDER BY path;
```

### 3. 文件去重
基于SHA256哈希去重，避免重复存储相同文件：
```python
file_hash = hashlib.sha256(content).hexdigest()
# 检查是否已存在相同哈希的文件
# 如果存在，复用存储路径
```

## 📊 前端界面建议

### 文件树组件
- 使用Element Plus的Tree组件
- 支持拖拽移动文件
- 右键菜单（新建、重命名、删除）

### 批量上传组件
- 使用Element Plus的Upload组件
- 支持拖拽上传
- 显示上传进度
- 支持文件预览

## 🔄 下一步行动

请问您希望：
1. **继续实现完整的后端API** - 我会完成所有接口的实现
2. **先运行数据库迁移** - 创建表结构
3. **查看具体某个接口的实现** - 比如批量上传接口
4. **其他需求** - 请告诉我您的想法

请告诉我您想要优先处理哪个部分？
