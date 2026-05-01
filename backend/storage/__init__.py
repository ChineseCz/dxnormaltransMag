"""
存储抽象层 - 支持多种存储后端
支持：本地文件系统、MinIO、阿里云OSS、腾讯云COS
通过环境变量切换：STORAGE_BACKEND=local|minio|oss|cos
"""
import os
from .base import StorageBackend
from .local import LocalStorage
from .minio_storage import MinIOStorage

# 从环境变量读取配置
STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")

# 全局存储实例
_storage_instance = None


def get_storage() -> StorageBackend:
    """获取存储后端单例"""
    global _storage_instance

    if _storage_instance is None:
        if STORAGE_BACKEND == "minio":
            _storage_instance = MinIOStorage()
        elif STORAGE_BACKEND == "local":
            _storage_instance = LocalStorage()
        # 未来可扩展：elif STORAGE_BACKEND == "oss": ...
        else:
            raise ValueError(f"不支持的存储后端: {STORAGE_BACKEND}")

    return _storage_instance


__all__ = ['get_storage', 'StorageBackend']

