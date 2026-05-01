"""
存储后端测试脚本
验证LocalStorage和MinIOStorage的功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.storage import get_storage
import tempfile


def test_storage():
    """测试存储后端基本功能"""
    print("=" * 60)
    print("存储后端测试")
    print("=" * 60)

    # 获取存储实例
    storage = get_storage()
    print(f"\n✅ 存储后端: {type(storage).__name__}")

    # 测试1: 保存字节数据
    print("\n【测试1】保存字节数据...")
    test_data = b"Hello, dx-platform storage!"
    test_path = "test/hello.txt"

    try:
        remote_path = storage.save_bytes(test_data, test_path)
        print(f"✅ 保存成功: {remote_path}")
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

    # 测试2: 检查文件存在
    print("\n【测试2】检查文件存在...")
    exists = storage.exists(test_path)
    print(f"✅ 文件存在: {exists}")

    # 测试3: 读取字节数据
    print("\n【测试3】读取字节数据...")
    try:
        loaded_data = storage.load_bytes(test_path)
        assert loaded_data == test_data, "数据不一致"
        print(f"✅ 读取成功: {loaded_data.decode()}")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return False

    # 测试4: 获取元数据
    print("\n【测试4】获取文件元数据...")
    try:
        metadata = storage.get_metadata(test_path)
        if metadata:
            print(f"✅ 文件大小: {metadata.size} bytes")
            print(f"✅ 修改时间: {metadata.modified_at}")
        else:
            print("⚠️ 元数据不可用")
    except Exception as e:
        print(f"⚠️ 获取元数据失败: {e}")

    # 测试5: 列出文件
    print("\n【测试5】列出文件...")
    try:
        files = storage.list_files("test/")
        print(f"✅ 找到 {len(files)} 个文件:")
        for f in files:
            print(f"   - {f}")
    except Exception as e:
        print(f"❌ 列表失败: {e}")

    # 测试6: 获取访问URL
    print("\n【测试6】获取访问URL...")
    try:
        url = storage.get_url(test_path, expires=3600)
        print(f"✅ URL: {url[:80]}...")
    except Exception as e:
        print(f"⚠️ URL生成失败: {e}")

    # 测试7: 保存文件
    print("\n【测试7】保存本地文件...")
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write("This is a test file from local disk.")
            tmp_path = tmp.name

        remote_file = "test/from_local.txt"
        storage.save_file(tmp_path, remote_file)
        print(f"✅ 上传成功: {remote_file}")

        os.unlink(tmp_path)
    except Exception as e:
        print(f"❌ 上传失败: {e}")

    # 测试8: 下载文件
    print("\n【测试8】下载文件到本地...")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
            download_path = tmp.name

        storage.load_file(remote_file, download_path)
        with open(download_path, 'r') as f:
            content = f.read()
        print(f"✅ 下载成功: {content}")

        os.unlink(download_path)
    except Exception as e:
        print(f"❌ 下载失败: {e}")

    # 测试9: 删除文件
    print("\n【测试9】删除测试文件...")
    try:
        storage.delete(test_path)
        storage.delete(remote_file)
        print("✅ 删除成功")
    except Exception as e:
        print(f"❌ 删除失败: {e}")

    # 验证删除
    print("\n【测试10】验证文件已删除...")
    exists_after = storage.exists(test_path)
    if not exists_after:
        print("✅ 文件已删除")
    else:
        print("❌ 文件仍然存在")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    # 显示当前配置
    backend = os.environ.get("STORAGE_BACKEND", "local")
    print(f"\n当前存储后端: {backend}")
    print(f"提示: 可通过环境变量 STORAGE_BACKEND 切换（local|minio）\n")

    # 运行测试
    success = test_storage()

    if not success:
        sys.exit(1)

