# 数据规范体系 📚

本文档提供了电磁场数据集管理平台的统一数据规范说明。

---

## 📋 文档概览

本规范体系包含3个核心文档：

### 1. [完整技术规范](./DATA_SPECIFICATION.md) ⭐
**适合对象**：开发者、高级用户  
**内容**：
- 3种数据组织模式的详细定义（multicolumn / perfile / separated）
- COMSOL 导出格式标准
- 坐标系统说明（xyz / rz / rphiz）
- 文件质量要求
- Python 验证脚本
- 版本规划路线图

### 2. [快速上手指南](./QUICK_START_DATA_UPLOAD.md) 🚀
**适合对象**：初次使用者  
**内容**：
- 4个典型场景分步教程
  - 场景一：电抗器参数化数据（最简单）
  - 场景二：单相变压器时域数据
  - 场景三：变压器温升数据（多参数文件名）
  - 场景四：三相变压器（多通道输入）⚠️高级
- 常见错误排查
- 上传前检查清单

### 3. [前端界面说明](../frontend/src/components/DataSpecGuide.vue)
**适合对象**：所有用户  
**形式**：交互式 Vue 组件，嵌入在"数据集管理"页面中  
**功能**：
- 场景快速选择器
- 实时代码示例
- 配置参数说明
- 关键操作提示

---

## 🎯 核心概念速查

### 数据组织方式对比表

| 模式 | 文件数量 | 输入来源 | 典型应用 |
|------|----------|----------|----------|
| **multicolumn**<br>单文件多工况 | 1个输出文件<br>+ N个输入文件 | 独立时间序列文件 | COMSOL 时域仿真<br>（400个时间步在一个文件） |
| **perfile**<br>逐工况分文件 | N个工况文件<br>（每个一个txt） | 从文件名提取 | COMSOL 参数化扫描<br>（100A.txt, 200A.txt, ...） |
| **separated**<br>输入输出分离 | 1个输出文件<br>+ N个输入文件<br>（可能多通道） | 独立文件（可能交织） | 三相系统、多物理场耦合<br>（3个线圈电流在一个文件） |

### 坐标系统对比表

| 坐标系代码 | 说明 | 坐标列数 | 适用场景 |
|------------|------|----------|----------|
| `xyz` | 直角坐标（笛卡尔） | 3 | 3D 变压器、电机、GIS |
| `rz` | 2D 轴对称（柱坐标） | 2 | 2D 电抗器、圆柱形设备 |
| `rphiz` | 3D 柱坐标 | 3 | 旋转对称但有周向变化的场 |

---

## 🔄 数据处理流程

```
上传阶段                          处理阶段
┌─────────────────┐              ┌────────────────────┐
│ 创建数据集       │              │ Step 1: 装配/截取    │
│ ├─ 选择组织方式  │              │ ├─ multicolumn: 时域截取 │
│ ├─ 选择坐标系    │              │ ├─ perfile: 工况排序   │
│ └─ 定义输入/输出 │              │ └─ separated: 通道解析│
└─────────────────┘              └────────────────────┘
         ↓                                  ↓
┌─────────────────┐              ┌────────────────────┐
│ 上传文件         │              │ Step 2: 划分        │
│ ├─ output: 场量  │              │ ├─ 训练集 80%       │
│ ├─ input: 激励   │              │ ├─ 验证集 15%       │
│ └─ 设置角色索引  │              │ └─ 测试集 5%        │
└─────────────────┘              └────────────────────┘
         ↓                                  ↓
┌─────────────────┐              ┌────────────────────┐
│ 自动解析         │              │ Step 3: 归一化      │
│ ├─ 提取坐标列    │              │ └─ Z-Score (μ, σ)  │
│ ├─ 识别工况值    │              └────────────────────┘
│ └─ 验证维度一致性│                         ↓
└─────────────────┘              ┌────────────────────┐
                                 │ Step 4: PCA 降维    │
                                 │ ├─ N_spatial → 60维 │
                                 │ └─ 保存均值/主成分  │
                                 └────────────────────┘
                                            ↓
                                 ┌────────────────────┐
                                 │ 进入模型训练         │
                                 └────────────────────┘
```

---

## ⚠️ 当前版本限制与规划

### ✅ v1.0（当前）完全支持
- ✅ multicolumn 模式（时域数据）
- ✅ perfile 模式（单参数工况文件）
- ⚠️ separated 模式（仅单通道，多通道取第一通道）

### 🚧 v1.1（计划中）
- [ ] separated 模式完整支持多通道交织解析
  - 三相变压器的 H1.txt（3通道×81时间步）自动解交织
- [ ] perfile 模式支持多参数文件名
  - 如 `1158.6_865.8.txt` → 自动提取 P1=1158.6, P2=865.8
- [ ] 数据可视化增强
  - 2D 热图（rz 坐标）
  - 3D 场分布（xyz 坐标）

### 🔮 v2.0（未来）
- [ ] 支持 HDF5、VTK 等格式
- [ ] 网格自动匹配与插值
- [ ] 云端数据集共享

---

## 🛠️ 实用工具

### Python 快速检查脚本

```python
# check_data.py - 验证数据格式
import numpy as np
import re
import os

def validate_comsol_file(filepath):
    """验证 COMSOL 导出文件格式"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    metadata = {}
    for line in lines:
        if line.startswith('%'):
            m = re.search(r'%\s+(\w+):\s+(.+)', line)
            if m:
                metadata[m.group(1)] = m.group(2).strip()
    
    data = np.loadtxt(filepath, encoding='utf-8', comments='%')
    
    print(f"✓ 文件: {os.path.basename(filepath)}")
    print(f"  维度: {metadata.get('Dimension', 'N/A')}")
    print(f"  节点数: {metadata.get('Nodes', 'N/A')}")
    print(f"  数据形状: {data.shape}")
    print(f"  {'✓' if not np.isnan(data).any() else '✗'} 无 NaN")
    print(f"  {'✓' if not np.isinf(data).any() else '✗'} 无 Inf\n")
    
    return metadata, data

# 批量检查目录
def batch_validate(folder):
    files = [f for f in os.listdir(folder) if f.endswith('.txt')]
    print(f"检查目录: {folder}")
    print(f"找到 {len(files)} 个文件\n")
    for fname in files:
        try:
            validate_comsol_file(os.path.join(folder, fname))
        except Exception as e:
            print(f"✗ {fname}: {e}\n")

# 使用示例
batch_validate("E:/path/to/your/raw_data")
```

### 文件名批量重命名脚本

```python
# rename_files.py - 清理文件名格式
import os
import re

def rename_perfile_data(folder, pattern=r'^([\d.]+)'):
    """
    将文件名规范化为 "数值[单位].txt" 格式
    示例：1158.6_865.8.txt → 1158.6[W].txt
    """
    files = [f for f in os.listdir(folder) if f.endswith('.txt')]
    renamed = 0
    
    for fname in files:
        m = re.search(pattern, fname)
        if m:
            value = m.group(1)
            new_name = f"{value}[A].txt"  # 修改单位为实际单位
            old_path = os.path.join(folder, fname)
            new_path = os.path.join(folder, new_name)
            
            if old_path != new_path:
                os.rename(old_path, new_path)
                print(f"✓ {fname} → {new_name}")
                renamed += 1
    
    print(f"\n完成！重命名了 {renamed} 个文件")

# 使用示例
rename_perfile_data("E:/path/to/reactor_data")
```

---

## 📞 技术支持

### 遇到问题？

1. **查看快速上手指南**：[QUICK_START_DATA_UPLOAD.md](./QUICK_START_DATA_UPLOAD.md)
2. **检查常见错误**：文档中的"错误排查"章节
3. **使用验证脚本**：运行上面的 Python 检查脚本
4. **提交 Issue**：附上文件前10行和错误信息

### 需要新功能？

请在 [PROGRESS_REPORT.md](./PROGRESS_REPORT.md) 中查看开发路线图，或提出功能请求。

---

## 📚 相关文档

- [完整 API 文档](../backend/api/data/README.md)（如果存在）
- [数据处理算法说明](../core_algorithms/README.md)（如果存在）
- [前端组件文档](../frontend/README.md)（如果存在）

---

**最后更新**：2026-04-05  
**维护者**：系统开发团队

