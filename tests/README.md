# 测试脚本目录

## 📁 目录结构

```
tests/
├── storage/              # 存储相关测试
│   ├── test_storage.py   # 存储功能完整测试
│   ├── verify_storage.py # 快速验证脚本
│   └── init_minio.py     # MinIO初始化脚本
└── README.md             # 本文件
```

## 🧪 存储测试说明

### test_storage.py
**完整功能测试**，测试所有存储操作：
- 保存/读取字节数据
- 上传/下载文件
- 文件列表
- 文件删除
- 元数据获取
- URL生成

**运行方法**：
```bash
python tests/storage/test_storage.py
```

### verify_storage.py
**快速验证脚本**，验证当前存储后端是否正常工作。

**运行方法**：
```bash
python tests/storage/verify_storage.py
```

### init_minio.py
**MinIO初始化脚本**，自动创建bucket并测试连接。

**运行方法**：
```bash
python tests/storage/init_minio.py
```

## 🔄 切换存储后端测试

### 测试MinIO
```bash
# 确保.env中配置了
STORAGE_BACKEND=minio

# 运行测试
python tests/storage/test_storage.py
```

### 测试本地存储
```bash
# 临时切换
set STORAGE_BACKEND=local
python tests/storage/test_storage.py

# 或修改.env
STORAGE_BACKEND=local
```

## 📝 添加新测试

在相应目录下创建测试脚本，命名规范：
- `test_*.py` - 功能测试
- `verify_*.py` - 验证脚本
- `init_*.py` - 初始化脚本

