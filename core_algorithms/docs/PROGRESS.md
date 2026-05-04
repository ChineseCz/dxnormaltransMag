# 第五章实验进度备忘录

> 生成时间：2025-04-01，供下次对话快速恢复上下文

---

## 一、已完成的工作

### 1. 测试题扩充：30题 → 51题 ✅

**文件：`run_experiment.py`**

- QUESTIONS 列表已包含 **51 题**（A01-A17 / B01-B17 / C01-C17，每类 17 题）
- 已验证：`python -c "import run_experiment as r; print(len(r.QUESTIONS))"` 输出 51
- 新增 A11-A17（故障诊断）、B11-B17（调参辅助）、C11-C17（综合运维）

### 2. FAISS 文档上下文：8份 → 11份 ✅

新增 3 块文档常量（已写入 `run_experiment.py`）：

| 变量名 | 内容 | 来源 |
|--------|------|------|
| `FAISS_DATASET_INTRO` | 三类电磁场仿真数据集介绍 | 4.2.1_数据集介绍.md |
| `FAISS_PIPELINE` | 工况-空间矩阵与预处理流水线 | 4.2.2_数据流水线设计.md |
| `FAISS_PREDICTION_RESULTS` | 三场景预测精度对比 | 4.4.3_多场景预测结果分析.md |

### 3. 路由函数 `get_context()` 已更新 ✅

覆盖全部 51 个题号的 FAISS 文档路由 + KG 上下文路由。

### 4. LLM-as-Judge 自动评分已写入 ✅

**文件：`run_experiment.py`**（第 693-800 行附近）

已新增以下函数，替代原来的人工打分流程：

```python
_call_judge(prompt)          # 底层：调 Qwen 非流式 API，返回 0~1 浮点分
judge_faithfulness(answer, context)    # 忠实度 F
judge_context_recall(key_points, ctx)  # 上下文召回率 CR
judge_answer_relevancy(question, ans)  # 答案相关性 AR
```

### 5. 主实验流程 `run_experiment()` 已重写 ✅

新流程：生成答案 → 自动获取对应上下文 → 调用 3 个 Judge 函数自动打分 → 写入 Excel

Excel 列结构变为：`{method}_答案 / {method}_F / {method}_CR / {method}_AR`

### 6. 指标统计 `calc_metrics()` 已重写 ✅

- 读 Excel 中的 F/CR/AR 列自动算均值
- 输出表5-6（综合对比）和表5-7（按类别分项）的 Markdown 表格
- 纯 LLM 的 CR 列标记为 "—"（无检索步骤）

### 7. 论文数字已同步 ✅

| 文件 | 改动 |
|------|------|
| `实验.md` | 30→51，10→17，表头"各10题"→"各17题" |
| `5.5_测试问答集.md` | 文件头 "共30题"→"共51题" |

---

## 二、未完成的工作（下次对话继续）

### ❌ 1. `实验.md` 砍掉 CP 指标（四指标→三指标）

当前 `实验.md` 仍然是 **四指标**（CP/CR/F/AR），需要改为 **三指标**（CR/F/AR）：

具体要改的地方：

- **5.5.2 评价指标定义**：
  - 开头 "共定义四项量化指标" → "共定义三项量化指标"
  - 删掉整个 CP 段落（① 上下文精确率那段 + 公式 5-4）
  - CR 的编号从 ② 改为 ①，F 从 ③ 改为 ②，AR 从 ④ 改为 ③
  - 公式编号：CR 的 5-5 改为 5-4，F 的 5-6 改为 5-5，AR 的 5-7 改为 5-6

- **5.5.3**：
  - "对每题自动计算CP、CR、F、AR四项得分" → "对每题自动计算CR、F、AR三项得分"

- **5.5.4 表5-6**：
  - 删掉 `上下文精确率 CP` 列
  - 纯LLM行：删掉 CP 的 "—"
  - 注释改为 "故CR项以'—'表示"

- **5.5.4 分析段落**：
  - 删掉整个 "(3) 检索精准度（Context Precision）" 段落
  - (4) 改编号为 (3)

- **5.5.5 案例分析**：
  - 所有 `CP=[待填写]，` 删掉

- **5.6 本章小结**：
  - "检索质量（CP、CR）" → "检索质量（CR）"

### ❌ 2. `run_experiment.py` 有个小 bug

`judge_faithfulness` 函数里有一行多余代码：
```python
return judge_faithfulness.__wrapped__(prompt) if hasattr(judge_faithfulness, '__wrapped__') else _call_judge(prompt)
```
应简化为：
```python
return _call_judge(prompt)
```

### ❌ 3. 运行实验（可选，取决于是否有 API Key）

```powershell
$env:DASHSCOPE_API_KEY = "sk-你的密钥"
cd E:\Project\dxnormaltransMag\dxnormaltransMag\core_algorithms
python run_experiment.py          # 生成答案 + 自动评分 → experiment_result.xlsx
python run_experiment.py --calc   # 读取结果 → 输出论文表格
```

预计：51题 × 3方法 × (1次生成 + 3次Judge) ≈ 612 次 API 调用，耗时约 20 分钟。

---

## 三、文件清单与当前状态

| 文件 | 状态 | 说明 |
|------|------|------|
| `run_experiment.py` | ✅ 代码完成 | 51题 + 11份FAISS文档 + LLM-as-Judge自动评分 + 统计输出 |
| `实验.md` | ⚠️ 需改 | 数字已更新(51/17)，但仍是四指标，需砍掉CP改为三指标 |
| `5.5_测试问答集.md` | ✅ 已更新 | 文件头数字已同步，但只列了A01-A10/B01-B10/C01-C10的详细描述 |
| `experiment_result.xlsx` | ❌ 未生成 | 需运行 `python run_experiment.py` |

---

## 四、指标体系最终方案（三指标）

| 指标 | 层次 | 含义 | 纯LLM是否适用 |
|------|------|------|:---:|
| **上下文召回率 CR** | 检索质量 | 参考要点能否在检索上下文中找到依据 | ❌ 标记 "—" |
| **忠实度 F** | 生成质量 | 答案是否有上下文支撑（反幻觉） | ✅ 用空上下文评 |
| **答案相关性 AR** | 生成质量 | 答案是否切题 | ✅ |

> 砍掉了 **上下文精确率 CP**，理由：与 CR 高度相关，省篇幅且不影响结论。

---

## 五、快速恢复对话的提示词

复制以下内容作为新对话的开头：

> 我在做毕业论文第五章 5.5 节的 KG-RAG 对比实验。上次对话的进度记录在 `core_algorithms/PROGRESS.md`，请先读取该文件了解上下文，然后继续完成"未完成的工作"部分：
> 1. 把 `实验.md` 从四指标（CP/CR/F/AR）改为三指标（CR/F/AR），砍掉所有 CP 相关内容
> 2. 修复 `run_experiment.py` 里 `judge_faithfulness` 的小 bug
> 3. 改完后验证 py 能正常 import

