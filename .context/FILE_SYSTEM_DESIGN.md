# 文件管理系统设计文档

## 需求概述

实现一个支持以下功能的文件管理系统：
1. **文件树结构** - 支持文件夹层级结构
2. **批量上传** - 一次上传多个文件
3. **用户隔离** - 每个用户有独立的文件空间
4. **不同模式** - 支持不同的存储模式（如数据集模式、个人文件模式等）

## 数据库设计

### 1. 文件夹表 (t_folder)
```sql
- id: 主键
- user_id: 用户ID（外键）
- parent_id: 父文件夹ID（自关联）
- name: 文件夹名称
- path: 完整路径（如 /root/folder1/subfolder）
- description: 描述
- created_at, updated_at: 时间戳
```

### 2. 文件表 (t_file)
```sql
- id: 主键
- user_id: 用户ID（外键）
- folder_id: 所属文件夹ID
- filename: 文件名
- original_filename: 原始文件名
- file_size: 文件大小
- mime_type: MIME类型
- storage_path: 存储路径（users/{user_id}/files/{uuid}）
- file_hash: SHA256哈希（用于去重）
- metadata: 额外元数据（JSONB）
- tags: 标签数组
- created_at, updated_at: 时间戳
```

## 存储路径结构

```
users/
  ├── {user_id}/
  │   ├── files/           # 用户文件
  │   │   ├── {uuid1}.ext
  │   │   └── {uuid2}.ext
  │   └── folders/         # 文件夹元数据（数据库）
```

## API 接口设计

### 文件夹管理
- `GET /api/files/folders/tree` - 获取文件夹树
- `POST /api/files/folders` - 创建文件夹
- `PUT /api/files/folders/{id}` - 重命名文件夹
- `DELETE /api/files/folders/{id}` - 删除文件夹

### 文件管理
- `GET /api/files/list` - 列出文件（支持按文件夹筛选）
- `POST /api/files/upload` - 单文件上传
- `POST /api/files/batch-upload` - 批量上传
- `PUT /api/files/{id}/move` - 移动文件
- `PUT /api/files/{id}/rename` - 重命名文件
- `DELETE /api/files/{id}` - 删除文件
- `GET /api/files/{id}/download` - 下载文件

## 实现步骤

1. ✅ 创建数据库迁移脚本
2. ⏳ 实现完整的后端API
3. ⏳ 集成到主应用
4. ⏳ 前端界面实现（可选）
