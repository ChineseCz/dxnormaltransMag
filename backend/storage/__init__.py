"""
存储抽象层 - 支持多种存储后端
支持：本地文件系统、MinIO、阿里云OSS、腾讯云COS
通过环境变量切换：STORAGE_BACKEND=local|minio|oss|cos
"""
import os
from .base import StorageBackend
from .local import LocalStorage
from .minio_storage import MinIOStorage

# 加载.env文件（如果存在）
try:
    from dotenv import load_dotenv
    import pathlib
    env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[Storage] 已加载配置文件: {env_path}")
except ImportError:
    pass

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


