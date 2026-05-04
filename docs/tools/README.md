# 数据处理工具集 🛠️

本目录包含用于处理COMSOL导出数据的实用工具脚本。

---

## 📂 工具列表

### 1. deinterleave_separated.py - Separated模式数据解交织工具

**用途**：将COMSOL Dimension=0的多通道交织数据拆分为独立的单通道文件。

**适用场景**：
- 三相变压器的多线圈电流数据（如H1.txt）
- 多物理场耦合系统的全局评估导出
- 任何Dimension=0且包含多通道交织的输入文件

**功能特性**：
- ✅ 自动从列头检测通道数和通道名称
- ✅ 智能解交织算法
- ✅ 自动验证输出正确性
- ✅ 支持批量处理多个文件
- ✅ 详细的处理日志

---

## 🚀 快速开始

### 安装依赖

```bash
pip install numpy
```

### 基本用法

```bash
# 自动检测通道数并解交织
python deinterleave_separated.py H1.txt

# 指定输出目录
python deinterleave_separated.py H1.txt -o deinterleaved/

# 手动指定通道数（如果自动检测失败）
python deinterleave_separated.py H1.txt -c 3

# 批量处理多个文件
python deinterleave_separated.py H1.txt HV1.txt L1.txt

# 跳过验证步骤（加快处理速度）
python deinterleave_separated.py H1.txt --no-validate
```

### 查看帮助

```bash
python deinterleave_separated.py --help
```

---

## 📖 详细示例

### 示例1：处理三相变压器数据

**原始文件**：`H1.txt`（Dimension=0，1行×243列）
```
% Dimension: 0
% Nodes: 1
% Expressions: 243
% ICoil_1@t=1.16  ICoil_4@t=1.16  ICoil_7@t=1.16  ICoil_1@t=1.1605  ...
-7.046           -55.030          60.880           3.349             ...
```

**执行命令**：
```bash
python deinterleave_separated.py H1.txt -o deinterleaved/
```

**输出**：
```
============================================================
  COMSOL Separated 模式数据解交织工具 v1.0
============================================================

✓ 检测到 3 个通道: ['mf.ICoil_1', 'mf.ICoil_4', 'mf.ICoil_7']
   列头中共有 243 个数据列 (=3通道 × 81时间步)

📂 读取文件: H1.txt
   原始形状: (243,)
   通道数: 3
   时间步数: 81
   解交织后形状: (81, 3)

💾 保存拆分后的文件到: deinterleaved/
   ✓ H1_mf.ICoil_1.txt (81 行)
   ✓ H1_mf.ICoil_4.txt (81 行)
   ✓ H1_mf.ICoil_7.txt (81 行)

🔍 验证解交织结果...
   ✅ 验证通过！解交织结果正确

════════════════════════════════════════════════════════════
✅ 完成！共生成 3 个文件
```

**生成的文件**：
```
deinterleaved/
├── H1_mf.ICoil_1.txt  # 线圈1的81个时间步数据（81行×1列）
├── H1_mf.ICoil_4.txt  # 线圈4的81个时间步数据
└── H1_mf.ICoil_7.txt  # 线圈7的81个时间步数据
```

**下一步操作**：
1. 在数据集管理中创建数据集，**选择multicolumn模式**（不是separated！）
2. 上传生成的3个文件，每个设为`input`角色
3. 设置variableIndex：`mf.ICoil_1.txt`→0, `mf.ICoil_4.txt`→1, `mf.ICoil_7.txt`→2
4. 上传输出场量文件（如`三相1.0.txt`）
5. 进行数据处理

---

### 示例2：批量处理

**场景**：一次性处理多个separated文件

```bash
python deinterleave_separated.py \
    H1.txt \
    HV1.txt \
    L1.txt \
    -o batch_output/ \
    -c 3
```

**效果**：
- 同时处理3个文件
- 所有输出保存到`batch_output/`目录
- 手动指定通道数为3（加快处理速度）

---

## ⚠️ 常见问题

### Q1: 提示"无法自动检测通道数"怎么办？

**原因**：文件列头格式不标准或损坏。

**解决方案**：
1. 手动查看文件，确认实际通道数（如3个线圈=3个通道）
2. 使用`-c`参数手动指定：
   ```bash
   python deinterleave_separated.py H1.txt -c 3
   ```

---

### Q2: 提示"数据元素数不能被通道数整除"怎么办？

**原因**：通道数设置错误，或文件损坏。

**解决方案**：
1. 检查列头，手动数通道数：
   ```
   % ICoil_1@t0  ICoil_4@t0  ICoil_7@t0  ICoil_1@t1  ...
     ↑ 通道1      ↑ 通道2      ↑ 通道3      ↑ 通道1（重复）
   
   → 共3个通道（ICoil_1, ICoil_4, ICoil_7）
   ```
2. 用`-c`参数手动指定正确的通道数

---

### Q3: 验证失败怎么办？

**原因**：解交织算法错误或数据损坏。

**解决方案**：
1. 检查生成的文件是否有意义（用文本编辑器打开查看）
2. 如果确定数据正确，可以使用`--no-validate`跳过验证
3. 向开发团队报告Bug

---

### Q4: 如何判断我的文件需要解交织？

**判断方法**：
1. 打开文件，查看元数据：
   ```
   % Dimension: 0   ← 如果是0，就需要解交织
   % Nodes: 1       ← 如果是1，通常需要解交织
   ```
2. 查看数据行数：
   - 只有1行数据 → 需要解交织
   - 有几百行数据 → 不需要（标准multicolumn格式）

---

## 🔧 高级用法

### 与其他工具配合

```bash
# 解交织后直接查看第一个通道的前10行
python deinterleave_separated.py H1.txt -o temp/ && head -n 10 temp/H1_mf.ICoil_1.txt

# 批量处理并统计
python deinterleave_separated.py *.txt -o output/ && echo "处理完成，共生成 $(ls output/*.txt | wc -l) 个文件"
```

### 在Python脚本中调用

```python
from deinterleave_separated import deinterleave_separated_data

# 解交织
output_files = deinterleave_separated_data(
    input_file='H1.txt',
    output_dir='deinterleaved/',
    n_channels=3  # 或None自动检测
)

print(f"生成了 {len(output_files)} 个文件:")
for f in output_files:
    print(f"  - {f}")
```

---

## 📊 性能参考

| 文件大小 | 通道数 | 时间步 | 处理时间 |
|----------|--------|--------|----------|
| 50 KB    | 3      | 81     | <1秒     |
| 500 KB   | 10     | 1000   | 1-2秒    |
| 5 MB     | 20     | 10000  | 5-10秒   |

---

## 🛡️ 安全性说明

- ✅ 不修改原始文件（只读取）
- ✅ 自动创建输出目录（如果不存在）
- ✅ 内置验证机制（确保解交织正确性）
- ✅ 详细的日志输出（便于调试）

---

## 📝 版本历史

### v1.0 (2026-04-05)
- ✅ 初始版本发布
- ✅ 自动通道检测
- ✅ 解交织功能
- ✅ 验证功能
- ✅ 批量处理支持

---

## 🤝 贡献

如有Bug或改进建议，请：
1. 在GitHub提Issue
2. 或向开发团队反馈
3. 附上错误日志和示例文件

---

## 📜 许可证

本工具为内部使用工具，版权归系统开发团队所有。

---

**维护者**：系统开发团队  
**最后更新**：2026-04-05

