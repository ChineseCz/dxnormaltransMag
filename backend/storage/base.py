"""
存储后端基类 - 定义统一接口
所有存储实现必须继承此类
"""
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional, List
from datetime import datetime


class FileMetadata:
    """文件元数据"""
    def __init__(self, path: str, size: int, modified_at: datetime):
        self.path = path
        self.size = size
        self.modified_at = modified_at


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    def save_file(self, local_path: str, remote_path: str) -> str:
        """
        上传文件

        Args:
            local_path: 本地文件路径
            remote_path: 远程存储路径（如 datasets/ds_xxx/raw/file.txt）

        Returns:
            远程文件的访问路径/URL
        """
        pass

    @abstractmethod
    def save_bytes(self, data: bytes, remote_path: str) -> str:
        """
        保存字节数据

        Args:
            data: 字节数据
            remote_path: 远程存储路径

        Returns:
            远程文件的访问路径/URL
        """
        pass

    @abstractmethod
    def load_file(self, remote_path: str, local_path: str) -> str:
        """
        下载文件到本地

        Args:
            remote_path: 远程存储路径
            local_path: 本地保存路径

        Returns:
            本地文件路径
        """
        pass

    @abstractmethod
    def load_bytes(self, remote_path: str) -> bytes:
        """
        读取文件为字节

        Args:
            remote_path: 远程存储路径

        Returns:
            文件字节内容
        """
        pass

    @abstractmethod
    def exists(self, remote_path: str) -> bool:
        """检查文件是否存在"""
        pass

    @abstractmethod
    def delete(self, remote_path: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    def list_files(self, prefix: str) -> List[str]:
        """
        列出指定前缀的所有文件

        Args:
            prefix: 路径前缀（如 datasets/ds_xxx/）

        Returns:
            文件路径列表
        """
        pass

    @abstractmethod
    def get_metadata(self, remote_path: str) -> Optional[FileMetadata]:
        """获取文件元数据"""
        pass

    @abstractmethod
    def get_url(self, remote_path: str, expires: int = 3600) -> str:
        """
        获取文件访问URL（用于直接下载）

        Args:
            remote_path: 远程存储路径
            expires: 过期时间（秒），0表示永久

        Returns:
            可访问的URL
        """
        pass

