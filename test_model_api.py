"""测试模型训练API模块"""
import sys
sys.path.insert(0, 'E:/Project/dxnormaltransMag/dxnormaltransMag')

try:
    from backend.api.ml import model
    from fastapi.routing import APIRoute

    print('✅ model.py 导入成功')
    print('\n📋 已注册路由：')

    routes = [r for r in model.router.routes if isinstance(r, APIRoute)]
    for r in routes:
        methods = ', '.join(r.methods)
        print(f'  [{methods:8}] {r.path}')

    print(f'\n✅ 共 {len(routes)} 个路由端点')

except Exception as e:
    print(f'❌ 导入失败: {e}')
    import traceback
    traceback.print_exc()

