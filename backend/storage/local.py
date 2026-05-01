"""
本地文件系统存储实现
兼容现有代码，用于开发/测试环境
"""
import os
import shutil
from datetime import datetime
from typing import List, Optional
from .base import StorageBackend, FileMetadata


class LocalStorage(StorageBackend):
    """本地文件系统存储"""

    def __init__(self, base_dir: str = None):
        """
        Args:
            base_dir: 基础目录，默认为项目根目录
        """
        if base_dir is None:
            # 默认使用项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))  # backend/storage/
            backend_dir = os.path.dirname(current_dir)  # backend/
            base_dir = os.path.dirname(backend_dir)  # project root

        self.base_dir = base_dir
        print(f"[LocalStorage] 基础目录: {self.base_dir}")

    def _get_full_path(self, remote_path: str) -> str:
        """获取完整本地路径"""
        return os.path.join(self.base_dir, remote_path)

    def save_file(self, local_path: str, remote_path: str) -> str:
        """上传文件（复制到目标位置）"""
        full_path = self._get_full_path(remote_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        shutil.copy2(local_path, full_path)
        return remote_path

    def save_bytes(self, data: bytes, remote_path: str) -> str:
        """保存字节数据"""
        full_path = self._get_full_path(remote_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(data)
        return remote_path

    def load_file(self, remote_path: str, local_path: str) -> str:
        """下载文件（复制到本地）"""
        full_path = self._get_full_path(remote_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        shutil.copy2(full_path, local_path)
        return local_path

    def load_bytes(self, remote_path: str) -> bytes:
        """读取文件为字节"""
        full_path = self._get_full_path(remote_path)
        with open(full_path, 'rb') as f:
            return f.read()

    def exists(self, remote_path: str) -> bool:
        """检查文件是否存在"""
        full_path = self._get_full_path(remote_path)
        return os.path.exists(full_path)

    def delete(self, remote_path: str) -> bool:
        """删除文件"""
        full_path = self._get_full_path(remote_path)
        if os.path.exists(full_path):
            if os.path.isfile(full_path):
                os.remove(full_path)
            else:
                shutil.rmtree(full_path)
            return True
        return False

    def list_files(self, prefix: str) -> List[str]:
        """列出指定前缀的所有文件"""
        full_prefix = self._get_full_path(prefix)
        if not os.path.exists(full_prefix):
            return []

        files = []
        for root, dirs, filenames in os.walk(full_prefix):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                # 转换为相对路径
                rel_path = os.path.relpath(full_path, self.base_dir)
                files.append(rel_path.replace('\\', '/'))  # 统一使用 / 分隔符

        return files

    def get_metadata(self, remote_path: str) -> Optional[FileMetadata]:
        """获取文件元数据"""
        full_path = self._get_full_path(remote_path)
        if not os.path.exists(full_path):
            return None

        stat = os.stat(full_path)
        return FileMetadata(
            path=remote_path,
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime)
        )

    def get_url(self, remote_path: str, expires: int = 3600) -> str:
        """
        获取文件访问URL
        本地存储返回文件协议URL（仅用于调试）
        """
        full_path = self._get_full_path(remote_path)
        return f"file://{full_path}"

