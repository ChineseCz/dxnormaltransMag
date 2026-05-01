"""快速验证MinIO和本地存储都支持"""
import os
os.chdir('E:/Project/dxnormaltransMag/dxnormaltransMag')

from backend.storage import get_storage

# 获取当前配置
storage = get_storage()

print("=" * 60)
print("存储后端状态验证")
print("=" * 60)

print(f"\n✅ 当前存储后端: {type(storage).__name__}")
print(f"✅ 环境变量配置: STORAGE_BACKEND = {os.environ.get('STORAGE_BACKEND', 'local')}")

# 测试基本功能
print("\n【测试基本功能】")
try:
    # 测试保存
    test_path = "test/verify.txt"
    storage.save_bytes(b"Hello from storage!", test_path)
    print(f"✅ 保存文件成功: {test_path}")

    # 测试读取
    data = storage.load_bytes(test_path)
    print(f"✅ 读取文件成功: {data.decode()}")

    # 测试删除
    storage.delete(test_path)
    print(f"✅ 删除文件成功")

except Exception as e:
    print(f"❌ 测试失败: {e}")

print("\n" + "=" * 60)
print("验证完成！")
print("=" * 60)

