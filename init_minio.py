"""
MinIO 初始化脚本
自动创建bucket并测试连接
"""
from minio import Minio
from minio.error import S3Error

# MinIO连接配置
ENDPOINT = "localhost:9001"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin123"
BUCKET_NAME = "dx-platform"

print("=" * 60)
print("MinIO 初始化脚本")
print("=" * 60)

try:
    # 创建MinIO客户端
    print(f"\n1. 连接到MinIO: {ENDPOINT}")
    client = Minio(
        ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False  # 开发环境使用HTTP
    )
    print("   ✅ 连接成功")

    # 检查bucket是否存在
    print(f"\n2. 检查bucket: {BUCKET_NAME}")
    if client.bucket_exists(BUCKET_NAME):
        print(f"   ✅ Bucket '{BUCKET_NAME}' 已存在")
    else:
        print(f"   ⚠️ Bucket '{BUCKET_NAME}' 不存在，正在创建...")
        client.make_bucket(BUCKET_NAME)
        print(f"   ✅ Bucket '{BUCKET_NAME}' 创建成功")

    # 列出所有buckets
    print("\n3. 当前所有buckets:")
    buckets = client.list_buckets()
    for bucket in buckets:
        print(f"   - {bucket.name} (创建于: {bucket.creation_date})")

    # 测试上传文件
    print("\n4. 测试上传文件...")
    test_data = b"Hello from MinIO! This is a test file."
    from io import BytesIO
    client.put_object(
        BUCKET_NAME,
        "test/hello.txt",
        BytesIO(test_data),
        length=len(test_data),
        content_type="text/plain"
    )
    print("   ✅ 文件上传成功: test/hello.txt")

    # 测试读取文件
    print("\n5. 测试读取文件...")
    response = client.get_object(BUCKET_NAME, "test/hello.txt")
    data = response.read()
    response.close()
    response.release_conn()
    print(f"   ✅ 文件读取成功: {data.decode()}")

    # 列出文件
    print("\n6. 列出bucket中的文件:")
    objects = client.list_objects(BUCKET_NAME, recursive=True)
    for obj in objects:
        print(f"   - {obj.object_name} ({obj.size} bytes)")

    # 生成预签名URL
    print("\n7. 生成预签名URL（1小时有效）:")
    from datetime import timedelta
    url = client.presigned_get_object(
        BUCKET_NAME,
        "test/hello.txt",
        expires=timedelta(hours=1)
    )
    print(f"   ✅ URL: {url[:80]}...")

    print("\n" + "=" * 60)
    print("✅ MinIO 初始化完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 访问Web控制台: http://localhost:9002")
    print("   用户名: minioadmin")
    print("   密码: minioadmin123")
    print("\n2. 配置环境变量 (.env 文件):")
    print("   STORAGE_BACKEND=minio")
    print("\n3. 运行测试脚本:")
    print("   set STORAGE_BACKEND=minio")
    print("   python test_storage.py")

except S3Error as e:
    print(f"\n❌ MinIO错误: {e}")
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

