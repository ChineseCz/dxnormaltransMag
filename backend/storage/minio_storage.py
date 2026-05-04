"""
MinIO 对象存储实现
MinIO是开源的S3兼容对象存储服务，适合企业内网部署
文档：https://min.io/docs/minio/linux/developers/python/API.html
"""
import os
from datetime import datetime, timedelta
from typing import List, Optional
from .base import StorageBackend, FileMetadata

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    print("[MinIOStorage] 警告: minio包未安装，请运行: pip install minio")


class MinIOStorage(StorageBackend):
    """MinIO 对象存储"""

    def __init__(self):
        if not MINIO_AVAILABLE:
            raise ImportError("MinIO客户端未安装，请运行: pip install minio")

        # 从环境变量读取配置
        self.endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.environ.get("MINIO_BUCKET", "dx-platform")
        self.secure = os.environ.get("MINIO_SECURE", "false").lower() == "true"

        # 创建MinIO客户端
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )

        # 确保bucket存在
        self._ensure_bucket()

        print(f"[MinIOStorage] 连接到 {self.endpoint}, bucket={self.bucket_name}")

    def _ensure_bucket(self):
        """确保bucket存在，不存在则创建"""
        try:
            # 直接尝试创建bucket，如果已存在会抛出BucketAlreadyOwnedByYou错误
            self.client.make_bucket(self.bucket_name)
            print(f"[MinIOStorage] 创建bucket: {self.bucket_name}")
        except S3Error as e:
            # Bucket已存在是正常情况
            if 'BucketAlreadyOwnedByYou' in str(e) or 'BucketAlreadyExists' in str(e):
                print(f"[MinIOStorage] Bucket '{self.bucket_name}' 已存在")
            else:
                print(f"[MinIOStorage] Bucket检查/创建错误: {e}")
        except Exception as e:
            print(f"[MinIOStorage] Bucket初始化失败: {e}")

    def save_file(self, local_path: str, remote_path: str) -> str:
        """上传文件到MinIO"""
        try:
            self.client.fput_object(
                self.bucket_name,
                remote_path,
                local_path
            )
            return remote_path
        except S3Error as e:
            raise RuntimeError(f"上传文件失败: {e}")

    def save_bytes(self, data: bytes, remote_path: str) -> str:
        """保存字节数据到MinIO"""
        try:
            from io import BytesIO
            self.client.put_object(
                self.bucket_name,
                remote_path,
                BytesIO(data),
                length=len(data)
            )
            return remote_path
        except S3Error as e:
            raise RuntimeError(f"保存数据失败: {e}")

    def load_file(self, remote_path: str, local_path: str) -> str:
        """从MinIO下载文件"""
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.client.fget_object(
                self.bucket_name,
                remote_path,
                local_path
            )
            return local_path
        except S3Error as e:
            raise RuntimeError(f"下载文件失败: {e}")

    def load_bytes(self, remote_path: str) -> bytes:
        """从MinIO读取字节数据"""
        try:
            response = self.client.get_object(
                self.bucket_name,
                remote_path
            )
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise RuntimeError(f"读取文件失败: {e}")

    def exists(self, remote_path: str) -> bool:
        """检查文件是否存在"""
        try:
            self.client.stat_object(self.bucket_name, remote_path)
            return True
        except S3Error:
            return False

    def delete(self, remote_path: str) -> bool:
        """删除文件"""
        try:
            self.client.remove_object(self.bucket_name, remote_path)
            return True
        except S3Error as e:
            print(f"[MinIOStorage] 删除失败: {e}")
            return False

    def list_files(self, prefix: str) -> List[str]:
        """列出指定前缀的所有文件"""
        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"[MinIOStorage] 列表失败: {e}")
            return []

    def get_metadata(self, remote_path: str) -> Optional[FileMetadata]:
        """获取文件元数据"""
        try:
            stat = self.client.stat_object(self.bucket_name, remote_path)
            return FileMetadata(
                path=remote_path,
                size=stat.size,
                modified_at=stat.last_modified
            )
        except S3Error:
            return None

    def get_url(self, remote_path: str, expires: int = 3600) -> str:
        """
        获取预签名URL（用于直接下载）

        Args:
            remote_path: 远程文件路径
            expires: 过期时间（秒），默认1小时
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                remote_path,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            raise RuntimeError(f"生成URL失败: {e}")




