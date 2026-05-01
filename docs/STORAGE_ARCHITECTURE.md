# 存储方案架构文档

## 📋 目录
1. [方案对比](#方案对比)
2. [架构设计](#架构设计)
3. [快速开始](#快速开始)
4. [存储后端切换](#存储后端切换)
5. [API使用示例](#api使用示例)
6. [生产部署建议](#生产部署建议)

---

## 🎯 方案对比

### 问题：为什么不能只用本地文件系统？

| 场景 | 本地文件系统 | 对象存储（MinIO/OSS） |
|------|-------------|----------------------|
| 单机开发 | ✅ 简单直接 | ⚠️ 需要额外部署 |
| 分布式部署 | ❌ 文件不同步 | ✅ 统一存储池 |
| 文件备份 | ❌ 需手动脚本 | ✅ 自动快照 |
| 横向扩展 | ❌ 磁盘容量限制 | ✅ 无限扩展 |
| 安全性 | ❌ 文件系统权限 | ✅ 访问策略+签名URL |
| CDN加速 | ❌ 不支持 | ✅ 原生支持 |
| 多副本 | ❌ 需RAID | ✅ 自动多副本 |
| 容灾恢复 | ❌ 需定期备份 | ✅ 跨区域复制 |

### 推荐方案

| 环境 | 推荐方案 | 理由 |
|------|---------|------|
| **开发/测试** | 本地文件系统 | 简单、免费、快速启动 |
| **企业内网** | MinIO | 开源、可控、S3兼容 |
| **生产环境** | 阿里云OSS/腾讯云COS | 免运维、高可用、按量付费 |

---

## 🏗️ 架构设计

### 存储抽象层

```
应用层 (API/Service)
    ↓
存储抽象层 (StorageBackend)
    ↓
┌──────────┬──────────┬──────────┐
│ 本地文件 │  MinIO   │   OSS    │
│  系统    │ (S3兼容) │ (阿里云) │
└──────────┴──────────┴──────────┘
```

### 核心接口

```python
class StorageBackend(ABC):
    @abstractmethod
    def save_file(local_path, remote_path) -> str:
        """上传文件"""
    
    @abstractmethod
    def load_file(remote_path, local_path) -> str:
        """下载文件"""
    
    @abstractmethod
    def exists(remote_path) -> bool:
        """检查文件是否存在"""
    
    @abstractmethod
    def delete(remote_path) -> bool:
        """删除文件"""
    
    @abstractmethod
    def get_url(remote_path, expires) -> str:
        """获取访问URL（预签名）"""
```

### 文件组织结构

```
bucket: dx-platform
├── datasets/
│   ├── ds_5b9d4909/
│   │   ├── raw/                    # 原始上传文件
│   │   │   ├── input1.txt
│   │   │   └── output1.txt
│   │   ├── data/                   # 预处理后数据
│   │   │   ├── trainInput.txt
│   │   │   ├── trainOutput.txt
│   │   │   ├── testInput.txt
│   │   │   └── testOutput.txt
│   │   ├── pca_result/             # PCA结果
│   │   │   ├── mean_pca.txt
│   │   │   └── vector_pca.txt
│   │   ├── model/                  # 训练模型
│   │   │   ├── DNN_2026-04-06.pth
│   │   │   └── PINN_2026-04-06.pth
│   │   └── result/                 # 预测结果
│   │       └── prediction_123.npy
│   └── ds_9e9e8331/
│       └── ...
└── temp/                           # 临时文件（定期清理）
    └── upload_xxx.tmp
```

---

## 🚀 快速开始

### 方案A：本地文件系统（默认，无需配置）

```bash
# 无需任何配置，直接运行
python run.py
```

**存储位置**: `E:\Project\dxnormaltransMag\dxnormaltransMag\datasets\`

---

### 方案B：MinIO（推荐）

#### 1. 启动MinIO容器

```bash
cd env
docker-compose up -d minio
```

#### 2. 访问MinIO控制台

浏览器打开: http://localhost:9002

- 用户名: `minioadmin`
- 密码: `minioadmin123`

#### 3. 创建Bucket

在控制台点击 "Create Bucket"，名称: `dx-platform`

#### 4. 配置环境变量

创建 `.env` 文件（项目根目录）:

```bash
# 存储配置
STORAGE_BACKEND=minio

# MinIO配置
MINIO_ENDPOINT=localhost:9001
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=dx-platform
MINIO_SECURE=false
```

#### 5. 安装Python客户端

```bash
pip install minio
```

#### 6. 重启后端

```bash
python run.py
```

控制台输出应显示:
```
[MinIOStorage] 连接到 localhost:9001, bucket=dx-platform
```

---

### 方案C：阿里云OSS（生产环境）

#### 1. 开通OSS服务

访问: https://www.aliyun.com/product/oss

#### 2. 创建Bucket

- 区域: 根据业务选择（如华东2）
- 读写权限: 私有
- 名称: `dx-platform-prod`

#### 3. 获取AccessKey

控制台 → AccessKey管理 → 创建AccessKey

#### 4. 配置环境变量

```bash
STORAGE_BACKEND=oss

# 阿里云OSS配置
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY_ID=LTAI5t...
OSS_ACCESS_KEY_SECRET=xxx...
OSS_BUCKET=dx-platform-prod
```

#### 5. 安装SDK

```bash
pip install oss2
```

---

## 🔄 存储后端切换

### 运行时切换（环境变量）

```bash
# 方式1: 命令行设置
set STORAGE_BACKEND=minio
python run.py

# 方式2: .env 文件
echo STORAGE_BACKEND=minio >> .env
python run.py
```

### 代码中使用

```python
from backend.storage import get_storage

# 获取存储实例（自动根据环境变量选择）
storage = get_storage()

# 上传文件
storage.save_file(
    local_path='E:/data/input.txt',
    remote_path='datasets/ds_xxx/raw/input.txt'
)

# 下载文件
storage.load_file(
    remote_path='datasets/ds_xxx/raw/input.txt',
    local_path='C:/temp/input.txt'
)

# 检查存在
if storage.exists('datasets/ds_xxx/model/dnn.pth'):
    print('模型文件存在')

# 获取访问URL（预签名，1小时有效）
url = storage.get_url('datasets/ds_xxx/raw/input.txt', expires=3600)
print(f'下载链接: {url}')

# 删除文件
storage.delete('datasets/ds_xxx/temp/old_file.txt')
```

---

## 📝 API使用示例

### 文件上传（修改示例）

**原代码**（直接文件系统）:
```python
# backend/api/data/routes.py
upload_path = os.path.join(raw_dir, file.filename)
with open(upload_path, 'wb') as f:
    f.write(await file.read())
```

**新代码**（存储抽象层）:
```python
from backend.storage import get_storage

storage = get_storage()
content = await file.read()
remote_path = f'datasets/{ds_id}/raw/{file.filename}'
storage.save_bytes(content, remote_path)
```

### 模型训练（保存模型）

**原代码**:
```python
model_path = os.path.join(model_dir, f'DNN_{timestamp}.pth')
torch.save(net.state_dict(), model_path)
```

**新代码**:
```python
from backend.storage import get_storage
import tempfile

# 先保存到临时文件
with tempfile.NamedTemporaryFile(delete=False, suffix='.pth') as tmp:
    torch.save(net.state_dict(), tmp.name)
    
    # 上传到对象存储
    storage = get_storage()
    remote_path = f'datasets/{ds_id}/model/DNN_{timestamp}.pth'
    storage.save_file(tmp.name, remote_path)
    
    os.unlink(tmp.name)  # 删除临时文件
```

### 模型推理（加载模型）

**新代码**:
```python
from backend.storage import get_storage
import tempfile

storage = get_storage()

# 下载到临时文件
with tempfile.NamedTemporaryFile(delete=False, suffix='.pth') as tmp:
    storage.load_file(model_path, tmp.name)
    
    # 加载模型
    model.load_state_dict(torch.load(tmp.name))
    
    os.unlink(tmp.name)
```

---

## 🏭 生产部署建议

### 小规模部署（<100用户）

```yaml
方案: 单机 + MinIO
部署:
  - 应用服务器: 1台（8核16G）
  - MinIO: Docker容器
  - PostgreSQL: Docker容器
存储:
  - MinIO数据卷: 500GB SSD
成本: 低（仅服务器成本）
```

### 中等规模（100-1000用户）

```yaml
方案: Kubernetes + MinIO集群
部署:
  - 应用Pod: 3副本（自动伸缩）
  - MinIO: 4节点集群（分布式）
  - PostgreSQL: 主从复制
存储:
  - MinIO: 2TB × 4节点 = 8TB
成本: 中等（需专业运维）
```

### 大规模（>1000用户）

```yaml
方案: 云原生 + 云存储
部署:
  - 应用: 阿里云ACK/腾讯云TKE
  - 存储: 阿里云OSS/腾讯云COS
  - 数据库: RDS PostgreSQL
  - CDN: 全球加速
存储:
  - OSS: 按量付费（无上限）
  - CDN: 按流量计费
成本: 高（但免运维，按需付费）
```

---

## 🔐 安全最佳实践

### 1. 访问控制

**MinIO策略示例**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::dx-platform/datasets/*"],
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": "192.168.1.0/24"
        }
      }
    }
  ]
}
```

### 2. 预签名URL

```python
# 生成临时下载链接（1小时有效）
url = storage.get_url('datasets/ds_xxx/model/dnn.pth', expires=3600)

# 返回给前端
return {"download_url": url, "expires_at": "2026-04-06 12:00:00"}
```

### 3. 加密存储

**MinIO服务端加密**:
```bash
# 启用自动加密
mc encrypt set sse-s3 myminio/dx-platform
```

**OSS服务端加密**:
```python
# 上传时启用加密
bucket.put_object('key', data, headers={'x-oss-server-side-encryption': 'AES256'})
```

---

## 📊 成本估算

### MinIO（自建）

| 项目 | 配置 | 成本/月 |
|------|------|---------|
| 服务器 | 8核16G | ¥500 |
| 磁盘 | 2TB SSD | ¥300 |
| 带宽 | 10Mbps | ¥100 |
| **总计** | - | **¥900/月** |

### 阿里云OSS

| 项目 | 用量 | 成本/月 |
|------|------|---------|
| 存储 | 500GB | ¥62 (0.12元/GB) |
| 流量 | 100GB | ¥80 (0.8元/GB) |
| 请求 | 10万次 | ¥2 |
| **总计** | - | **¥144/月** |

**结论**: 小规模场景下云存储更经济，大规模场景自建MinIO更划算。

---

## ⚠️ 迁移注意事项

### 从本地文件系统迁移到MinIO

#### 1. 数据迁移脚本

```python
from backend.storage import LocalStorage, MinIOStorage
import os

local = LocalStorage()
minio = MinIOStorage()

# 迁移所有数据集
for dataset_id in os.listdir('datasets'):
    prefix = f'datasets/{dataset_id}'
    files = local.list_files(prefix)
    
    for file_path in files:
        print(f'迁移: {file_path}')
        data = local.load_bytes(file_path)
        minio.save_bytes(data, file_path)
```

#### 2. 数据库路径更新

```sql
-- 更新模型文件路径（如需要）
UPDATE t_model SET file_path = REPLACE(file_path, 'E:\datasets\', 'datasets/');
```

#### 3. 验证迁移

```python
# 检查文件数量
local_count = len(local.list_files('datasets/'))
minio_count = len(minio.list_files('datasets/'))
assert local_count == minio_count, "文件数量不一致"
```

---

## 🛠️ 故障排查

### MinIO连接失败

**错误**: `ConnectionError: Cannot connect to host localhost:9001`

**解决**:
```bash
# 1. 检查容器状态
docker ps | grep minio

# 2. 检查端口占用
netstat -ano | findstr 9001

# 3. 重启容器
docker-compose restart minio

# 4. 查看日志
docker logs minio
```

### 权限错误

**错误**: `AccessDenied: Access Denied`

**解决**:
```python
# 检查MinIO策略
from minio import Minio
client = Minio('localhost:9001', 'minioadmin', 'minioadmin123', secure=False)
policy = client.get_bucket_policy('dx-platform')
print(policy)
```

### 性能优化

**慢上传问题**:
```python
# 使用分片上传（大文件）
from minio import Minio
client.fput_object(
    'dx-platform',
    'datasets/large_file.pth',
    '/path/to/file.pth',
    part_size=10*1024*1024  # 10MB分片
)
```

---

## 📚 参考资料

- [MinIO 官方文档](https://min.io/docs/minio/linux/index.html)
- [MinIO Python SDK](https://min.io/docs/minio/linux/developers/python/API.html)
- [阿里云OSS文档](https://help.aliyun.com/product/31815.html)
- [AWS S3 API Reference](https://docs.aws.amazon.com/s3/index.html)

---

## 📝 更新日志

- **2026-04-06**: 初始版本
  - 实现存储抽象层
  - 支持本地文件系统和MinIO
  - 添加Docker配置

---

**维护者**: dx-platform 开发团队  
**最后更新**: 2026-04-06

