"""
5.5节 KG-RAG 对比实验脚本  ——  直接调用 Qwen API
=======================================================
三组方法的本质区别在于注入给 LLM 的上下文不同：

  纯LLM      → 无任何检索上下文，LLM 凭自身参数回答
  FAISS-Only → 注入模拟向量检索返回的文档片段
  KG-RAG     → 注入知识图谱三元组 + 文档片段（双轨）

运行前提：
  设置环境变量  $env:DASHSCOPE_API_KEY = "sk-xxxx"
  或在脚本顶部 API_KEY 变量直接填入

使用方式：
  python run_experiment.py          # 运行实验，生成 experiment_result.xlsx
  python run_experiment.py --calc   # 读取打分结果，输出论文指标
"""

import os, time, argparse
import requests
import pandas as pd
from pathlib import Path

# ══════════════════════════════════════════════════════
#  配置区（修改这里）
# ══════════════════════════════════════════════════════
API_KEY      = os.getenv("DASHSCOPE_API_KEY", "")   # 优先读环境变量，也可直接填 "sk-xxx"
MODEL        = "qwen-plus"                           # qwen-turbo(快/便宜) | qwen-plus | qwen-max
TEMPERATURE  = 0.1                                   # 低温使答案更稳定，适合评测
MAX_TOKENS   = 1024
REPEAT_TIMES = 1                                     # 每题重复N次取平均时延（1次足够，节省费用）
TIMEOUT_SEC  = 60
OUTPUT_FILE  = Path(__file__).parent / "results" / "experiment_result.xlsx"

QWEN_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

SYSTEM_PROMPT = (
    "你是一个专业的电力设备电磁场预测平台的技术专家，"
    "擅长铁心电抗器与变压器的故障诊断、DNN/CNN深度学习模型调参，"
    "以及平台操作指导。请根据提供的上下文知识给出准确、专业的回答。"
    "若上下文中没有相关信息，请基于自身知识作答，并注明。"
)

# ══════════════════════════════════════════════════════
#  知识上下文定义
#  这里预定义了 KG三元组 和 文档片段，模拟真实检索结果
#  来源：平台实际知识图谱Schema + 系统内已有的领域知识
# ══════════════════════════════════════════════════════

# ── 知识图谱三元组（物理维度：设备故障 — 以铁心电抗器与单相变压器为例） ──
# 节点统计：Device(4)+Component(16)+Phenomenon(16)+Fault_Cause(14)+Solution(14) = 64节点
# 边统计：HAS_PART(23)+SHOWS_ABNORMALITY(17)+INDICATES_CAUSE(16)+REQUIRES(16) = 72边
KG_PHYSICAL = """
【知识图谱检索结果 · 物理维度因果链（以铁心电抗器与单相变压器为例）】
三元组路径如下：

── 设备-部件关系（HAS_PART）──
- (铁心电抗器) -[HAS_PART]→ (中部绕组)
- (铁心电抗器) -[HAS_PART]→ (上部绕组)
- (铁心电抗器) -[HAS_PART]→ (下部绕组)
- (铁心电抗器) -[HAS_PART]→ (铁心叠片)
- (铁心电抗器) -[HAS_PART]→ (气隙垫片)
- (220kV单相变压器) -[HAS_PART]→ (高压侧绕组)
- (220kV单相变压器) -[HAS_PART]→ (低压侧绕组)
- (220kV单相变压器) -[HAS_PART]→ (铁心柱)
- (220kV单相变压器) -[HAS_PART]→ (铁轭)
- (220kV单相变压器) -[HAS_PART]→ (绝缘油)
- (220kV单相变压器) -[HAS_PART]→ (变压器套管)
- (220kV单相变压器) -[HAS_PART]→ (铁心接地片)
- (220kV单相变压器) -[HAS_PART]→ (冷却器)
- (500kV单相变压器) -[HAS_PART]→ (高压侧绕组)
- (500kV单相变压器) -[HAS_PART]→ (低压侧绕组)
- (500kV单相变压器) -[HAS_PART]→ (铁心柱)
- (500kV单相变压器) -[HAS_PART]→ (绝缘油)
- (500kV单相变压器) -[HAS_PART]→ (端绝缘)
- (干式变压器) -[HAS_PART]→ (高压侧绕组)
- (干式变压器) -[HAS_PART]→ (低压侧绕组)
- (干式变压器) -[HAS_PART]→ (铁心柱)
- (干式变压器) -[HAS_PART]→ (主绝缘)
- (干式变压器) -[HAS_PART]→ (低压套管)

── 部件异常表征（SHOWS_ABNORMALITY）──
- (中部绕组) -[SHOWS_ABNORMALITY]→ (磁通密度畸变)  confidence=0.963
- (高压侧绕组) -[SHOWS_ABNORMALITY]→ (局部磁场分布异常)  confidence=0.921
- (铁心叠片) -[SHOWS_ABNORMALITY]→ (局部过热)  confidence=0.887
- (铁心叠片) -[SHOWS_ABNORMALITY]→ (铁心涡流损耗增大)  confidence=0.854
- (绝缘油) -[SHOWS_ABNORMALITY]→ (绝缘油介损超标)  confidence=0.901
- (变压器套管) -[SHOWS_ABNORMALITY]→ (套管端部电场畸变)  confidence=0.876
- (高压侧绕组) -[SHOWS_ABNORMALITY]→ (局部放电量超标)  confidence=0.832
- (气隙垫片) -[SHOWS_ABNORMALITY]→ (气隙磁密局部极大值异常)  confidence=0.848
- (高压侧绕组) -[SHOWS_ABNORMALITY]→ (绕组端部电场畸变)  confidence=0.813
- (铁心叠片) -[SHOWS_ABNORMALITY]→ (铁心振动噪声异常)  confidence=0.791
- (低压侧绕组) -[SHOWS_ABNORMALITY]→ (局部磁场分布异常)  confidence=0.808
- (低压侧绕组) -[SHOWS_ABNORMALITY]→ (漏磁场极值异常)  confidence=0.821
- (高压侧绕组) -[SHOWS_ABNORMALITY]→ (绕组温升超标)  confidence=0.846
- (端绝缘) -[SHOWS_ABNORMALITY]→ (绝缘电阻下降)  confidence=0.879
- (绝缘油) -[SHOWS_ABNORMALITY]→ (油中溶解气体异常)  confidence=0.913
- (铁心叠片) -[SHOWS_ABNORMALITY]→ (铁心磁滞损耗增大)  confidence=0.837
- (铁心接地片) -[SHOWS_ABNORMALITY]→ (局部磁场不对称分布)  confidence=0.804

── 现象→根因指示（INDICATES_CAUSE）──
- (磁通密度畸变) -[INDICATES_CAUSE]→ (匝间短路, severity=Critical)  confidence=0.935
- (局部磁场分布异常) -[INDICATES_CAUSE]→ (绕组匝间短路, severity=Critical)  confidence=0.850
- (局部过热) -[INDICATES_CAUSE]→ (硅钢片绝缘漆脱落)  confidence=0.812
- (局部过热) -[INDICATES_CAUSE]→ (铁心接地不良)  confidence=0.743
- (绝缘油介损超标) -[INDICATES_CAUSE]→ (主绝缘受潮)  confidence=0.897
- (局部放电量超标) -[INDICATES_CAUSE]→ (绕组绝缘老化)  confidence=0.863
- (气隙磁密局部极大值异常) -[INDICATES_CAUSE]→ (气隙不均匀)  confidence=0.831
- (铁心涡流损耗增大) -[INDICATES_CAUSE]→ (铁心叠片间绝缘破坏)  confidence=0.819
- (铁心振动噪声异常) -[INDICATES_CAUSE]→ (铁心多点接地)  confidence=0.787
- (绕组端部电场畸变) -[INDICATES_CAUSE]→ (绕组绝缘老化)  confidence=0.851
- (漏磁场极值异常) -[INDICATES_CAUSE]→ (绕组变形)  confidence=0.829
- (绕组温升超标) -[INDICATES_CAUSE]→ (冷却系统堵塞)  confidence=0.823
- (绝缘电阻下降) -[INDICATES_CAUSE]→ (绝缘纸板老化)  confidence=0.871
- (油中溶解气体异常) -[INDICATES_CAUSE]→ (铁心片间短路)  confidence=0.844
- (铁心磁滞损耗增大) -[INDICATES_CAUSE]→ (铁心饱和)  confidence=0.837
- (局部磁场不对称分布) -[INDICATES_CAUSE]→ (铁心多点接地)  confidence=0.798

── 根因→处置方案（REQUIRES）──
- (匝间短路) -[REQUIRES]→ (直流电阻三相不平衡度测量)
- (匝间短路) -[REQUIRES]→ (频率响应分析FRA)
- (绕组匝间短路) -[REQUIRES]→ (更换高压侧绕组)
- (硅钢片绝缘漆脱落) -[REQUIRES]→ (铁心绝缘处理)
- (主绝缘受潮) -[REQUIRES]→ (变压器油色谱分析)
- (绕组绝缘老化) -[REQUIRES]→ (局部放电测试)
- (气隙不均匀) -[REQUIRES]→ (气隙重新整定)
- (铁心叠片间绝缘破坏) -[REQUIRES]→ (铁心绝缘处理)
- (铁心多点接地) -[REQUIRES]→ (绕组变形分析)
- (绕组绝缘老化) -[REQUIRES]→ (套管绝缘电阻测量)
- (绕组变形) -[REQUIRES]→ (吊芯检修)
- (冷却系统堵塞) -[REQUIRES]→ (冷却器清洗检修)
- (绝缘纸板老化) -[REQUIRES]→ (绝缘电阻测量)
- (铁心片间短路) -[REQUIRES]→ (励磁电流特性测试)
- (铁心饱和) -[REQUIRES]→ (励磁电流特性测试)
- (铁心接地不良) -[REQUIRES]→ (接地网络修复)
"""

# ── 知识图谱三元组（软件维度：DNN / CNN / RF 三类模型调参） ──
# 节点统计：Model_Type(3)+Metric(8)+Alg_Issue(22)+Tuning_Strategy(22) = 55节点
# 边统计：EVALUATED_BY(15)+EXHIBITS/INDICATES_CAUSE(17)+MITIGATED_BY(22) = 54边
KG_SOFTWARE = """
【知识图谱检索结果 · 软件维度调参链（DNN / CNN / RF 三类模型）】
三元组路径如下：

── 模型-指标绑定（EVALUATED_BY）──
- (DNN) -[EVALUATED_BY]→ (MAPE)
- (DNN) -[EVALUATED_BY]→ (验证集Loss)
- (DNN) -[EVALUATED_BY]→ (R²)
- (DNN) -[EVALUATED_BY]→ (MAE)
- (DNN) -[EVALUATED_BY]→ (测试Loss)
- (CNN) -[EVALUATED_BY]→ (MAPE)
- (CNN) -[EVALUATED_BY]→ (验证集Loss)
- (CNN) -[EVALUATED_BY]→ (R²)
- (CNN) -[EVALUATED_BY]→ (MAE)
- (CNN) -[EVALUATED_BY]→ (训练时间)
- (CNN) -[EVALUATED_BY]→ (测试Loss)
- (RF) -[EVALUATED_BY]→ (MAPE)
- (RF) -[EVALUATED_BY]→ (R²)
- (RF) -[EVALUATED_BY]→ (MAE)
- (RF) -[EVALUATED_BY]→ (特征重要性得分)

── 指标/状态→问题呈现（EXHIBITS / INDICATES_CAUSE）──
- (MAPE偏高) -[EXHIBITS]→ (训练样本稀疏, 低电流段100~300A)  confidence=0.928
- (MAPE偏高) -[EXHIBITS]→ (PCA主成分数量不足)  confidence=0.853
- (MAPE偏高) -[EXHIBITS]→ (过拟合)  confidence=0.791
- (MAPE偏高) -[EXHIBITS]→ (欠拟合)  confidence=0.762
- (验证集Loss剧烈震荡) -[INDICATES_CAUSE]→ (学习率过大)
- (梯度消失) -[INDICATES_CAUSE]→ (学习率过小)
- (训练不收敛) -[EXHIBITS]→ (学习率过大)
- (卷积核感受野不足) -[EXHIBITS]→ (MAPE偏高)
- (RF特征重要性分布不均) -[EXHIBITS]→ (MAPE偏高)
- (特征维度冗余) -[EXHIBITS]→ (MAPE偏高)
- (归一化失效) -[INDICATES_CAUSE]→ (测试集分布偏移)
- (批归一化统计量偏移) -[INDICATES_CAUSE]→ (归一化失效)
- (批大小过小) -[EXHIBITS]→ (训练不收敛)
- (RF树数量不足) -[EXHIBITS]→ (MAPE偏高)
- (测试集分布偏移) -[EXHIBITS]→ (MAPE偏高)
- (池化层过度压缩) -[INDICATES_CAUSE]→ (卷积核感受野不足)
- (早停过早触发) -[EXHIBITS]→ (欠拟合)

── 问题→调优策略（MITIGATED_BY）──
- (训练样本稀疏) -[MITIGATED_BY]→ (数据增强/插值过采样)
- (PCA主成分数量不足) -[MITIGATED_BY]→ (增加PCA维度至8维)
- (过拟合) -[MITIGATED_BY]→ (增大Dropout率至0.3~0.5)
- (过拟合) -[MITIGATED_BY]→ (L2正则化, 权重衰减=1e-4)
- (学习率过大) -[MITIGATED_BY]→ (降低学习率, 使用ReduceLROnPlateau)
- (梯度消失) -[MITIGATED_BY]→ (调整学习率至2e-3 + Warmup策略)
- (梯度消失) -[MITIGATED_BY]→ (将Sigmoid替换为ReLU/LeakyReLU)
- (梯度消失) -[MITIGATED_BY]→ (添加BatchNorm层)
- (欠拟合) -[MITIGATED_BY]→ (增加网络层数)
- (数据泄露) -[MITIGATED_BY]→ (使用训练集统计量重新归一化)
- (训练不收敛) -[MITIGATED_BY]→ (调整Batch Size)
- (卷积核感受野不足) -[MITIGATED_BY]→ (增大卷积核尺寸)
- (RF树深度过大) -[MITIGATED_BY]→ (RF限制最大树深度)
- (RF特征重要性分布不均) -[MITIGATED_BY]→ (RF增加特征采样比例)
- (特征维度冗余) -[MITIGATED_BY]→ (特征重要性筛选降维)
- (测试集分布偏移) -[MITIGATED_BY]→ (重新采集目标域数据)
- (批大小过小) -[MITIGATED_BY]→ (增大Batch Size)
- (RF树数量不足) -[MITIGATED_BY]→ (RF增加树数量)
- (池化层过度压缩) -[MITIGATED_BY]→ (减少池化层)
- (早停过早触发) -[MITIGATED_BY]→ (调整Early Stopping patience)
- (批归一化统计量偏移) -[MITIGATED_BY]→ (BatchNorm重新校准)
- (测试集分布偏移) -[MITIGATED_BY]→ (迁移学习微调)
"""

# ── FAISS 向量库检索结果（文档片段） ──
FAISS_REGULATION = """
【向量知识库检索结果 · 电抗器运行规程 DL/T 617-2021】
相似度: 93.6%，来源：DL/T 617-2021 第6.4.2条

铁心电抗器运行规程关键条款：
1. 绕组温升限值：额定运行工况下，绕组温升不得超过 65 K。超过限值时，应立即停电，进行绕组绝缘试验。
2. 气隙磁密限值：气隙磁密不得超过设计值的 110%。超过时，铁心可能进入饱和区，导致磁场畸变加剧、温升超标。
3. 匝间短路判定：频率响应分析（FRA）相关系数 R < 0.98 时，判定绕组存在形变或匝间短路。
   应结合直流电阻三相不平衡度（>2% 判定异常）综合判定，两项均超阈值时执行停电检修。
4. 冲击电压法或FRA可定位短路匝数；结合DNN预测差值图（B真值−预测）可标定异常节点位置。
5. 预防性试验周期：每年不少于一次绝缘电阻测量，每3年进行一次FRA检测。
"""

FAISS_TRANSFORMER = """
【向量知识库检索结果 · 变压器漏磁场计算原理】
相似度: 88.3%，来源：变压器漏磁场计算原理.pdf

变压器漏磁场分布规律：
1. 漏磁场主要集中在铁心窗口区域，绕组内外侧均有分布。
2. 磁通密度沿绕组高度方向呈近似梯形分布，中部磁密最高，两端逐渐降低。
3. 高压侧与低压侧绕组间的漏磁密度受安匝分布影响显著。
4. 220kV/500kV单相变压器在额定工况下，漏磁场极值通常出现在绕组端部区域。
5. 预测值与实测值偏差超过5%时，需同时从设备状态（绕组变形/铁心磁导率变化）
   和模型角度（输入特征缺失/PCA降维信息损失）排查。
"""

FAISS_DNN_TUNING = """
【向量知识库检索结果 · DNN模型调参经验总结】
相似度: 91.2%，来源：DNN模型调参经验总结.md

平台DNN调参关键经验：
1. Z-Score标准化：必须使用训练集的均值和方差，测试/推理阶段不可重新计算，
   否则造成数据泄露，导致评估指标虚高，部署后误差增大。
2. 学习率建议初始值 1e-3，使用 ReduceLROnPlateau（patience=10，factor=0.5）动态调整。
   Optuna搜索范围建议设为 [1e-4, 1e-2]，采用 suggest_loguniform 对数均匀分布。
3. PCA降维：保留方差比建议 ≥ 95%，对应主成分数通常为6~8维（视数据集而定）。
   验证方法：直接用原始特征训练，对比精度差异。
4. 低电流段（100~300A）样本稀疏时：使用插值过采样扩充，或对该区段Loss赋予更高权重。
5. 工程精度标准：MAPE < 3%、R² > 0.99、MAE < 0.05T 视为满足工程要求。
6. 过拟合处理：Dropout=0.3~0.5，L2权重衰减=1e-4，可配合Early Stopping（patience=20）。
"""

FAISS_PLATFORM = """
【向量知识库检索结果 · 平台使用指南】
相似度: 85.7%，来源：平台使用指南.md

平台基本操作流程：
1. 上传数据集：进入"数据管理"页面 → 点击"上传数据集" → 选择CSV/TXT格式文件
   → 系统自动执行Z-Score标准化和PCA降维预处理。
2. 模型训练：进入"模型管理"页面 → 选择数据集和模型类型（DNN/CNN）
   → 配置超参数 → 提交训练任务（Celery异步执行）。
3. 执行预测：选择已训练模型 → 上传预测输入数据 → 点击"开始预测"
   → 系统返回电磁场三维分布结果并在ECharts中可视化渲染。
4. 平台支持电场（kV/mm）和磁场（T）两种场类型预测，分别对应独立的模型和数据集。
5. 铁心电抗器磁场预测所需输入参数：励磁电流幅值（A）、频率（Hz）、绕组匝数、
   铁心几何尺寸（内径/外径/高度）。PCA预处理由平台后台自动完成，用户无需干预。
"""

FAISS_TRANSFORMER_FIELD = """
【向量知识库检索结果 · 变压器电场仿真分析手册】
相似度: 87.4%，来源：变压器电场仿真分析手册.pdf

变压器电场分析关键知识：
1. 变压器电场主要分布于绕组端部、绝缘层界面与套管引线区域，极值通常出现在绝缘薄弱处。
2. 220kV变压器绝缘系统在额定工况下，绕组端部电场强度不应超过绝缘材料耐受值的70%。
3. 500kV及以上变压器因电位梯度更高，需重点关注匝间电场与层间绝缘的均匀性。
4. CNN模型相较DNN对空间分布特征提取能力更强，在电场三维分布预测中表现更优。
5. 电场预测精度评估：MAPE < 2.5%、R² > 0.995 为高精度工程标准（电场要求严于磁场）。
6. 电场预测输入特征：施加电压（kV）、绕组几何尺寸、绝缘材料介电常数、电极形状参数。
"""

FAISS_PRETESTING = """
【向量知识库检索结果 · 电力设备预防性试验规程 GB/T 7595】
相似度: 90.1%，来源：GB/T 7595-2017 电力变压器运行规程

变压器预防性试验关键条款：
1. 绝缘电阻测量：每年至少进行一次，R60/R15（吸收比）应 ≥ 1.3，极化指数 PI ≥ 1.5。
2. 油中溶解气体分析（DGA）：总烃含量 > 150μL/L 或 H₂ > 150μL/L 时，判定存在潜伏性故障。
3. 直流电阻测量：三相不平衡度 > 2% 时，停电进行绕组检查；单相变压器与铭牌偏差 > 1% 告警。
4. 局部放电测量：在 1.05 倍额定电压下，局放量不得超过 100 pC（110kV及以上等级）。
5. 空载损耗与负载损耗测量：与出厂值偏差 > 5% 时，需结合油色谱综合判断铁心状态。
6. 变压器大修周期：油浸式一般 10~15 年或累计运行满 20 万小时后进行吊芯大修。
"""

FAISS_DL_OPTIM = """
【向量知识库检索结果 · 深度学习超参数优化最佳实践】
相似度: 89.3%，来源：深度学习超参数优化最佳实践.md

超参数搜索与模型优化指南：
1. Optuna贝叶斯优化：建议 n_trials=100，采用 TPE采样器，比随机搜索效率提升约3倍。
2. 学习率调度策略：CosineAnnealingLR（T_max=50）在电磁场预测任务中表现优于StepLR。
3. 批大小（Batch Size）影响：BS=32适合小数据集（<5000条），BS=128适合大数据集，过小会导致梯度噪声大、训练不收敛。
4. 正则化组合：Dropout(0.3) + L2(1e-4) + BatchNorm的组合在电磁场预测场景中验证有效。
5. 迁移学习策略：在不同电压等级间迁移时，冻结前3层，仅微调后2层可有效缩短训练时间60%。
6. 模型集成：DNN + CNN + RF的集成预测（加权平均，权重按验证集MAPE反比分配）可将MAPE进一步降低约0.3个百分点。
"""

FAISS_RF_GUIDE = """
【向量知识库检索结果 · 随机森林与集成学习工程实践】
相似度: 84.9%，来源：随机森林工程实践指南.md

随机森林（RF）模型调参与应用指南：
1. 关键超参数：n_estimators（树数量，建议100~500）、max_depth（最大深度，建议10~30）、
   max_features（特征采样比，建议"sqrt"或0.5~0.8）。
2. RF特征重要性：可用于电磁场预测的输入特征筛选，重要性得分 < 0.01 的特征可安全剔除，
   减少维度同时不损失预测精度。
3. 过拟合判断：训练集R²与测试集R²差值 > 0.05 时，判定过拟合，应增大min_samples_leaf或减小max_depth。
4. RF与DNN的适用场景对比：RF在小样本（<2000条）场景下收敛更稳定，DNN在大样本场景优势更明显。
5. 特征重要性分布不均时：增加max_features比例（如从sqrt调至0.6），或使用ExtraTreesRegressor增加随机性。
6. RF训练时间随n_estimators线性增长，在电磁场预测任务中n_estimators=200为精度与速度的平衡点。
"""

FAISS_DATASET_INTRO = """
【向量知识库检索结果 · 电气设备电磁场仿真数据集介绍】
相似度: 92.1%，来源：4.2.1_数据集介绍.md

平台三类电磁场仿真数据集：
1. 单相变压器漏磁场数据集：以V₁(V)、V₂(V)、I₁(A)、I₂(A)作为4维工况输入，
   每个时刻对应1241个固定三维坐标节点处的磁通密度B(T)分布快照。
   训练样本97组，测试样本26组，时间步长Δt=0.0005s。
2. 工频电抗器磁场数据集：单一电流输入（1维），I=100A至1005.1A，步长约18.1A，
   共51个激励工况，每个工况对应设备内部固定网格节点的三维稳态磁场分布。
3. 变压器内部套管电场数据集：导杆峰值电压为输入（1维），185.2kV至226.3kV，
   共11个电压激励工况，场量类型为电场E(kV/mm)。
"""

FAISS_PIPELINE = """
【向量知识库检索结果 · 多源数据构建与处理流水线设计】
相似度: 88.7%，来源：4.2.2_数据流水线设计.md

工况-空间矩阵与预处理流水线：
1. 工况-空间矩阵Y∈R^(N×M)：行切片B_i代表特定工况下全域电磁场空间分布快照，
   列切片代表某一空间节点在所有工况条件下的响应变化规律。
2. Z-Score标准化：必须仅用训练集统计量（均值/方差），验证集与测试集作为"未见域"。
3. PCA线性降维算子：适用于电磁场分布具有较强线性特征的场景，通过奇异值分解提取正交基向量。
4. AE非线性降维算子：面向复杂边界条件下的强非线性电磁场畸变，基于多层感知机编码器-解码器。
5. 元数据驱动动态模板：用户定义输入变量列表与输出目标，平台自动完成多维映射装配，
   兼容1维/4维等不同输入维度的设备数据。
"""

FAISS_PREDICTION_RESULTS = """
【向量知识库检索结果 · 多场景电磁场预测结果分析】
相似度: 90.5%，来源：4.4.3_多场景预测结果分析.md

三类场景预测精度对比（DNN最优）：
1. 单相变压器漏磁场：DNN MAE=2.29×10⁻²T, MAPE=2.37%, R²=0.99；
   RF MAPE=17.05%；CNN MAPE=2.83%。
2. 工频电抗器磁场：DNN MAE=1.83×10⁻²T, MAPE=1.94%, R²=0.998；
   RF MAPE=13.71%；CNN MAPE=2.28%。
3. 变压器套管电场：DNN MAE=8.31×10⁻³kV/mm, MAPE=2.48%, R²=0.991；
   RF MAPE=12.83%；CNN MAPE=3.74%。
结论：DNN在三类场景中均取得最优精度（R²≥0.99, MAPE≤2.48%），
RF因线性分段拟合局限MAPE均超12%，CNN介于两者之间。
"""

# ══════════════════════════════════════════════════════
#  根据题目路由类型，返回对应的上下文
# ══════════════════════════════════════════════════════
def get_context(route: str, question_id: str) -> tuple[str, str]:
    """返回 (faiss_ctx, kg_ctx)，根据路由和题号决定注入哪些知识"""
    q_id = question_id.upper()

    # ── FAISS 上下文选择（11份文档按题意路由） ──
    if q_id in ("A06", "A07", "A09", "A14", "C05"):
        faiss_ctx = FAISS_REGULATION + "\n" + FAISS_PRETESTING
    elif q_id in ("A01", "A02", "A03", "A04", "A10", "A11", "A12", "A13", "A16"):
        faiss_ctx = FAISS_TRANSFORMER + "\n" + FAISS_TRANSFORMER_FIELD
    elif q_id in ("A05", "A08", "A17", "C01", "C04", "C08"):
        faiss_ctx = FAISS_TRANSFORMER + "\n" + FAISS_TRANSFORMER_FIELD + "\n" + FAISS_PRETESTING
    elif q_id in ("A15",):
        faiss_ctx = FAISS_DATASET_INTRO
    elif q_id in ("B01", "B02", "B04", "B05", "B06", "B07", "B12", "B16", "C09"):
        faiss_ctx = FAISS_DNN_TUNING + "\n" + FAISS_DL_OPTIM
    elif q_id in ("B08", "B09", "B10", "B03"):
        faiss_ctx = FAISS_DNN_TUNING
    elif q_id in ("B11",):
        faiss_ctx = FAISS_RF_GUIDE + "\n" + FAISS_PREDICTION_RESULTS
    elif q_id in ("B13",):
        faiss_ctx = FAISS_PIPELINE
    elif q_id in ("B14",):
        faiss_ctx = FAISS_PREDICTION_RESULTS + "\n" + FAISS_DNN_TUNING
    elif q_id in ("B15",):
        faiss_ctx = FAISS_PIPELINE + "\n" + FAISS_DNN_TUNING
    elif q_id in ("B17",):
        faiss_ctx = FAISS_DATASET_INTRO + "\n" + FAISS_DNN_TUNING
    elif q_id in ("C06",):
        faiss_ctx = FAISS_DNN_TUNING + "\n" + FAISS_PIPELINE
    elif q_id in ("C02", "C03", "C07", "C10", "C15"):
        faiss_ctx = FAISS_PLATFORM
    elif q_id in ("C11", "C14", "C16"):
        faiss_ctx = FAISS_DATASET_INTRO + "\n" + FAISS_DNN_TUNING
    elif q_id in ("C12",):
        faiss_ctx = FAISS_PLATFORM + "\n" + FAISS_PIPELINE + "\n" + FAISS_DATASET_INTRO
    elif q_id in ("C13",):
        faiss_ctx = FAISS_TRANSFORMER + "\n" + FAISS_PLATFORM
    elif q_id in ("C17",):
        faiss_ctx = FAISS_PIPELINE
    else:
        faiss_ctx = FAISS_DNN_TUNING + "\n" + FAISS_RF_GUIDE + "\n" + FAISS_REGULATION

    # ── KG 上下文选择 ──
    if q_id.startswith("A") or q_id in ("C01", "C04", "C05", "C08"):
        kg_ctx = KG_PHYSICAL
    elif q_id.startswith("B") or q_id in ("C06", "C09"):
        kg_ctx = KG_SOFTWARE
    else:  # C类综合题注入双轨
        kg_ctx = KG_PHYSICAL + "\n" + KG_SOFTWARE

    return faiss_ctx, kg_ctx


# ══════════════════════════════════════════════════════
#  51道测试题（A/B/C 各17题）
# ══════════════════════════════════════════════════════
QUESTIONS = [
    {"id": "A01", "cat": "故障诊断", "route": "KG",     "max_score": 4,
     "q": "铁心电抗器中部绕组出现磁通密度偏低约12%的现象，请问最可能的故障根因是什么？",
     "key_points": ["定位到具体部件：中部绕组", "指出故障根因：匝间短路", "给出严重程度判断", "给出后续处置方向（直流电阻测量/FRA）"]},
    {"id": "A02", "cat": "故障诊断", "route": "KG",     "max_score": 4,
     "q": "变压器高压侧发生局部磁场分布异常，请列出完整的因果链路（现象→根因→处置）。",
     "key_points": ["识别异常表征实体：局部磁场分布异常", "指向根因：绕组匝间短路", "给出严重等级评估", "给出处置方案"]},
    {"id": "A03", "cat": "故障诊断", "route": "KG",     "max_score": 3,
     "q": "铁心电抗器气隙区域的磁密分布出现局部极大值异常，这通常由哪些部件问题引起？",
     "key_points": ["定位到气隙相关部件", "给出可能根因", "建议排查手段"]},
    {"id": "A04", "cat": "故障诊断", "route": "KG",     "max_score": 3,
     "q": "变压器铁心出现局部过热，过热现象与哪些部件异常相关联？应如何处置？",
     "key_points": ["识别相关部件（硅钢片绝缘/铁心接地）", "给出根因", "处置方案"]},
    {"id": "A05", "cat": "故障诊断", "route": "Hybrid", "max_score": 3,
     "q": "运维人员发现某台220kV单相变压器的漏磁场预测值与实测值偏差超过5%，这是否属于故障征兆？可能的原因有哪些？",
     "key_points": ["给出偏差阈值判断", "从物理维度分析原因", "从软件维度分析原因"]},
    {"id": "A06", "cat": "故障诊断", "route": "FAISS",  "max_score": 3,
     "q": "DL/T 617-2021规程对铁心电抗器绕组温升有何限制？超过限值时应执行什么操作？",
     "key_points": ["给出具体温升限值（65K）", "说明超限处置流程（停电检测）", "引用规程条款"]},
    {"id": "A07", "cat": "故障诊断", "route": "FAISS",  "max_score": 3,
     "q": "频率响应分析（FRA）相关系数R低于多少时，判定绕组存在形变？应结合哪些其他指标综合判定？",
     "key_points": ["给出阈值（R<0.98）", "指出需结合直流电阻不平衡度", "说明综合判定逻辑"]},
    {"id": "A08", "cat": "故障诊断", "route": "Hybrid", "max_score": 3,
     "q": "变压器绕组发生匝间短路后，对平台DNN电磁场预测结果会产生什么影响？",
     "key_points": ["说明匝间短路改变实际绕组分布", "指出模型输入特征偏移", "说明预测误差增大"]},
    {"id": "A09", "cat": "故障诊断", "route": "FAISS",  "max_score": 3,
     "q": "铁心电抗器在额定工况（600A）下，气隙磁密不得超过设计值的百分之多少？超标后的安全风险是什么？",
     "key_points": ["给出限值（110%）", "说明超标后风险（铁心饱和→磁场畸变→温升超标）", "建议降额运行或检修"]},
    {"id": "A10", "cat": "故障诊断", "route": "KG",     "max_score": 2,
     "q": "请列举铁心电抗器的所有一跳关联组件，以及每个组件可能导致的故障根因。",
     "key_points": ["列出关联组件（至少2个）", "列出关联故障根因（至少2个）"]},
    # ── A11~A17：新增设备故障诊断题 ──
    {"id": "A11", "cat": "故障诊断", "route": "KG",     "max_score": 3,
     "q": "变压器油纸套管在高压导杆附近出现局部电场集中，从知识图谱物理维度出发，最可能的根因与排查方法是什么？",
     "key_points": ["指出根因（油纸绝缘受潮/微气泡→介电常数下降→电场畸变）", "说明严重程度（局部放电→绝缘劣化）", "给出排查手段（介损角tanδ/局放检测）"]},
    {"id": "A12", "cat": "故障诊断", "route": "KG",     "max_score": 3,
     "q": "铁心电抗器铁心叠片出现局部饱和时，气隙磁密分布会发生什么变化？应如何处置？",
     "key_points": ["说明影响（导磁率下降→磁通向气隙集中→局部极值升高）", "指出根因（电流超额定/硅钢片退化）", "处置建议（降额运行/空载磁化曲线复测）"]},
    {"id": "A13", "cat": "故障诊断", "route": "KG",     "max_score": 3,
     "q": "变压器高压绕组与低压绕组之间的漏磁场出现明显不对称分布，从知识图谱出发对应什么故障路径？",
     "key_points": ["识别异常（漏磁场不对称→安培匝数失衡）", "指向根因（绕组偏移/匝间短路）", "建议检测方法（短路阻抗/FRA）"]},
    {"id": "A14", "cat": "故障诊断", "route": "FAISS",  "max_score": 3,
     "q": "DL/T 617-2021规程要求铁心电抗器应开展哪些周期性预防性试验？各项试验的合格判定标准是什么？",
     "key_points": ["列出试验项目（绝缘电阻/直流电阻/FRA）", "给出试验周期（年度/大修）", "合格标准（绝缘电阻≥历史值70%，不平衡度<2%）"]},
    {"id": "A15", "cat": "故障诊断", "route": "FAISS",  "max_score": 2,
     "q": "平台变压器漏磁场数据集共有多少组训练样本和测试样本？其输入特征包含哪几个物理量？",
     "key_points": ["给出训练97组/测试26组", "给出4维输入（V₁/V₂/I₁/I₂）"]},
    {"id": "A16", "cat": "故障诊断", "route": "KG",     "max_score": 3,
     "q": "变压器高压绕组绝缘电阻明显下降但直流电阻正常，从知识图谱物理维度分析最可能的故障根因是什么？",
     "key_points": ["区分两类指标含义", "指向根因（绝缘受潮/油纸老化/局放腐蚀）", "确认方法（介损角tanδ/油色谱）"]},
    {"id": "A17", "cat": "故障诊断", "route": "Hybrid", "max_score": 3,
     "q": "变压器铁心接地不良（接地线断路）会导致哪些可观测的电磁场异常？对DNN预测结果有何影响？",
     "key_points": ["电场异常（悬浮电位→感应电压升高→电场集中）", "潜在风险（对地放电/涡流损耗增大）", "预测影响（边界条件改变→DNN误差增大）"]},

    # ── B01~B10：原有模型调参辅助题 ──
    {"id": "B01", "cat": "调参辅助", "route": "KG",     "max_score": 4,
     "q": "铁心电抗器DNN预测模型在低电流区间（100~300A）的MAPE持续偏高，请排查参数配置问题并给出优化建议。",
     "key_points": ["识别问题类型：低电流段样本稀疏", "给出路径：MAPE偏高→训练样本稀疏→数据增强", "给出具体操作：插值过采样", "补充参数建议"]},
    {"id": "B02", "cat": "调参辅助", "route": "KG",     "max_score": 4,
     "q": "DNN模型训练时，验证集Loss在后期出现剧烈震荡，该问题的标准处置路径是什么？",
     "key_points": ["识别问题根因：学习率过大", "给出路径：验证集Loss震荡→降低学习率", "给出具体调整策略", "说明何时停止降低"]},
    {"id": "B03", "cat": "调参辅助", "route": "Hybrid", "max_score": 3,
     "q": "训练完成的DNN模型在测试集上MAPE为2.37%，这个指标是否达到工程要求？",
     "key_points": ["给出工程评价（MAPE<3%为合格）", "指出R²指标要求（>0.99）", "补充MAE绝对误差物理含义"]},
    {"id": "B04", "cat": "调参辅助", "route": "KG",     "max_score": 4,
     "q": "平台DNN模型出现梯度消失现象，训练Loss长期不下降，请给出排查步骤和参数调整方案。",
     "key_points": ["识别根因：学习率过小/激活函数不当", "给出路径：梯度消失→调整学习率+Warmup", "给出激活函数建议（ReLU替换Sigmoid）", "建议添加BatchNorm"]},
    {"id": "B05", "cat": "调参辅助", "route": "KG",     "max_score": 4,
     "q": "PCA降维后模型预测精度明显下降，如何判断是PCA主成分数量不足还是模型本身的问题？",
     "key_points": ["给出判断方法：检查PCA保留方差比≥95%", "给出路径：MAPE偏高→PCA主成分不足→增加维度", "排除方法：用原始特征对比", "说明PCA维度选取规则"]},
    {"id": "B06", "cat": "调参辅助", "route": "KG",     "max_score": 3,
     "q": "CNN模型与DNN模型相比，在变压器电场预测任务中各有什么优劣？应如何选择？",
     "key_points": ["说明DNN vs CNN各自优势", "结合平台任务说明选择依据", "给出性能指标对比依据"]},
    {"id": "B07", "cat": "调参辅助", "route": "KG",     "max_score": 3,
     "q": "训练集和验证集Loss都很低，但测试集MAPE偏高，这是什么问题？应如何处置？",
     "key_points": ["判断为过拟合", "给出路径：过拟合→增大Dropout/L2正则", "给出具体参数范围（Dropout=0.3~0.5，L2=1e-4）"]},
    {"id": "B08", "cat": "调参辅助", "route": "Hybrid", "max_score": 3,
     "q": "使用Optuna进行超参数搜索时，DNN模型的学习率搜索空间应设定在什么范围？有没有先验经验？",
     "key_points": ["给出学习率范围（1e-4~1e-2）", "说明对数均匀分布采样更合理", "结合平台实验给出推荐值"]},
    {"id": "B09", "cat": "调参辅助", "route": "FAISS",  "max_score": 3,
     "q": "DNN模型的训练Loss下降正常，但MAE绝对误差始终高于0.05T，应从哪些角度检查？",
     "key_points": ["检查Z-Score归一化是否正确（训练集统计量）", "检查输出反归一化是否正确", "检查数据分布偏移"]},
    {"id": "B10", "cat": "调参辅助", "route": "FAISS",  "max_score": 3,
     "q": "平台引入PCA降维的主要目的是什么？主成分数量对模型训练速度和精度分别有什么影响？",
     "key_points": ["说明PCA降维目的（去冗余/降计算量）", "主成分越少→训练快但精度损失", "主成分越多→信息全但降维意义减弱"]},
    # ── B11~B17：新增模型调参辅助题 ──
    {"id": "B11", "cat": "调参辅助", "route": "Hybrid", "max_score": 3,
     "q": "RF模型在三类电磁场预测任务中MAPE均超过12%，其精度瓶颈的根本原因是什么？",
     "key_points": ["RF固有局限（线性分段拟合→高维非线性映射能力不足）", "KG路径（RF→MAPE→精度不足→更换DNN/CNN）", "适用场景（RF适合快速基线，不适合精细预测）"]},
    {"id": "B12", "cat": "调参辅助", "route": "KG",     "max_score": 3,
     "q": "DNN模型的隐藏层层数与神经元数量应如何配置？增加层数一定会提升精度吗？",
     "key_points": ["推荐配置（3~5层，128~512神经元/层）", "过深风险（梯度消失/过拟合/边际递减）", "缓解方法（残差连接/BatchNorm）"]},
    {"id": "B13", "cat": "调参辅助", "route": "FAISS",  "max_score": 3,
     "q": "平台数据流水线中工况-空间矩阵Y的行维度和列维度分别代表什么物理含义？",
     "key_points": ["行切片=特定工况下全域场空间分布快照", "列切片=某空间节点在所有工况下的响应变化", "暂态行索引为时间步/参数化行索引为激励扫描序列"]},
    {"id": "B14", "cat": "调参辅助", "route": "Hybrid", "max_score": 3,
     "q": "电抗器磁场预测中DNN的MAPE为1.94%而CNN为2.28%，二者差异的可能原因是什么？",
     "key_points": ["电抗器输入仅1维→DNN全连接更高效", "CNN卷积核在低维下难以提取有效局部特征", "结论：低维优选DNN，高维再考虑CNN"]},
    {"id": "B15", "cat": "调参辅助", "route": "FAISS",  "max_score": 3,
     "q": "平台支持的自编码器(AE)非线性降维与PCA线性降维各适用于什么场景？",
     "key_points": ["PCA适用线性特征场景（均匀磁场）", "AE适用强非线性畸变场景", "AE训练成本更高，工程中优先尝试PCA"]},
    {"id": "B16", "cat": "调参辅助", "route": "KG",     "max_score": 3,
     "q": "训练DNN模型时Batch Size设置过大或过小分别会带来什么问题？平台推荐范围是多少？",
     "key_points": ["过大（显存溢出/泛化性下降）", "过小（梯度噪声大/训练震荡）", "推荐范围（32~128）"]},
    {"id": "B17", "cat": "调参辅助", "route": "Hybrid", "max_score": 3,
     "q": "变压器套管电场数据集仅有11组样本，样本量极少是否会影响DNN可靠性？应采取什么措施？",
     "key_points": ["确认小样本风险（过拟合/泛化不足）", "KG路径（样本不足→数据增强/交叉验证/正则化）", "优先Leave-One-Out交叉验证+Dropout+L2"]},

    # ── C01~C10：原有综合运维咨询题 ──
    {"id": "C01", "cat": "综合运维", "route": "Hybrid", "max_score": 5,
     "q": "现场工程师反映变压器局部磁场异常，同时DNN预测模型的近期MAPE也出现上升趋势，请综合分析可能原因并给出处置建议。",
     "key_points": ["物理维度分析：磁场异常指向绕组/铁心故障", "软件维度分析：MAPE上升因特征分布漂移", "关联分析：匝间短路导致工况偏离训练分布", "处置1：先排查设备故障（FRA+直流电阻）", "处置2：补充新工况数据重训练模型"]},
    {"id": "C02", "cat": "综合运维", "route": "FAISS",  "max_score": 4,
     "q": "如何使用本平台完成从上传数据集到获取电磁场预测结果的完整操作流程？",
     "key_points": ["上传数据集步骤", "选择或训练模型步骤", "执行预测并查看可视化结果", "导出或解读预测结果"]},
    {"id": "C03", "cat": "综合运维", "route": "Hybrid", "max_score": 3,
     "q": "对于初次使用本平台的电气工程师，进行铁心电抗器磁场预测时需要准备哪些输入参数？",
     "key_points": ["说明所需输入特征（电流幅值、频率、几何参数）", "说明数据格式要求", "说明PCA预处理是否需要用户干预"]},
    {"id": "C04", "cat": "综合运维", "route": "Hybrid", "max_score": 3,
     "q": "变压器在500kV电压等级下运行，漏磁场的分布规律是什么？DNN模型对该电压等级的预测精度如何？",
     "key_points": ["描述漏磁场分布规律（梯形分布/端部极值）", "给出该电压等级下的模型精度指标", "说明高压等级下的特殊挑战"]},
    {"id": "C05", "cat": "综合运维", "route": "Hybrid", "max_score": 3,
     "q": "匝间短路的直流电阻三相不平衡度超过多少时判定异常？此时平台预测模型是否还可信？",
     "key_points": ["给出不平衡度阈值（>2%）", "说明此时模型预测不可信（工况偏离训练分布）", "建议采集故障工况更新模型"]},
    {"id": "C06", "cat": "综合运维", "route": "Hybrid", "max_score": 3,
     "q": "请解释平台中Z-Score标准化的作用，以及为什么必须用训练集的均值和方差而不是测试集？",
     "key_points": ["解释Z-Score作用（消除量纲/加速收敛）", "解释必须用训练集统计量的原因（防止数据泄露）", "说明若用测试集统计量的后果（评估虚高）"]},
    {"id": "C07", "cat": "综合运维", "route": "Hybrid", "max_score": 3,
     "q": "平台是否支持同时对变压器电场和磁场进行预测？两类预测任务在模型选择上有何建议？",
     "key_points": ["说明平台支持电场和磁场双类型预测", "给出各自适用的模型建议", "说明PCA降维参数是否共享"]},
    {"id": "C08", "cat": "综合运维", "route": "Hybrid", "max_score": 4,
     "q": "铁心电抗器出现绕组绝缘老化时，电磁场分布会发生什么变化？对平台预测结果有何影响？需要做什么维护？",
     "key_points": ["物理影响：绝缘老化→漏电流增加→局部热点", "对预测影响：工况偏离训练集分布", "维护建议：绝缘电阻测量（每年一次）", "引用规程依据"]},
    {"id": "C09", "cat": "综合运维", "route": "Hybrid", "max_score": 4,
     "q": "训练DNN模型时发现低电流段数据很少，会不会影响实际运行时的预测可靠性？应如何解决？",
     "key_points": ["确认会影响（样本不平衡问题）", "解决方案：插值过采样", "补充方案：加权Loss", "工程建议：补采低电流工况实测数据"]},
    {"id": "C10", "cat": "综合运维", "route": "Hybrid", "max_score": 3,
     "q": "当平台预测出的电场极值超过设备额定绝缘强度的90%时，平台应如何告警？现场工程师应如何响应？",
     "key_points": ["说明平台告警阈值机制", "给出现场响应步骤（降负荷/停机检查）", "引用绝缘强度相关标准"]},
    # ── C11~C17：新增综合运维咨询题 ──
    {"id": "C11", "cat": "综合运维", "route": "Hybrid", "max_score": 3,
     "q": "平台三类数据集在输入维度和激励方式上有什么区别？这些区别对模型训练有何影响？",
     "key_points": ["三者差异（变压器4维暂态/电抗器1维稳态/套管1维稳态）", "输入维度影响模型选择（低维DNN/高维CNN）", "暂态时序对训练集划分的约束"]},
    {"id": "C12", "cat": "综合运维", "route": "Hybrid", "max_score": 4,
     "q": "某运维单位希望将本平台扩展至110kV电压互感器的电场预测，请从数据准备和模型配置两方面给出建议。",
     "key_points": ["数据准备（有限元仿真→工况-空间矩阵）", "输入特征定义（施加电压等级等）", "模型配置（参照套管电场经验选DNN）", "不可直接复用变压器模型权重"]},
    {"id": "C13", "cat": "综合运维", "route": "FAISS",  "max_score": 2,
     "q": "平台DNN模型预测输出的磁通密度单位是T，如果需要转换为高斯(Gs)，换算关系是什么？",
     "key_points": ["1T = 10000 Gs", "平台目前需用户自行换算"]},
    {"id": "C14", "cat": "综合运维", "route": "Hybrid", "max_score": 3,
     "q": "电抗器运行电流从额定值600A突变至1005A（接近数据集上限），平台DNN的预测结果是否仍然可信？",
     "key_points": ["边界工况外推风险（泛化能力下降）", "KG路径（MAPE偏高→边界外推→扩充训练数据）", "工程建议（标记置信度，谨慎参考）"]},
    {"id": "C15", "cat": "综合运维", "route": "Hybrid", "max_score": 3,
     "q": "平台同时运行Neo4j图谱查询和FAISS向量检索时，如果Neo4j服务宕机，智能助手是否还能正常工作？",
     "key_points": ["平台具备降级容错机制", "Neo4j异常→自动切换纯FAISS单轨", "降级后丧失因果推演但规程查询仍可用"]},
    {"id": "C16", "cat": "综合运维", "route": "Hybrid", "max_score": 3,
     "q": "电抗器数据集以约18.1A步长扫描51个工况，若实际运行电流落在两个扫描点之间，模型能否准确预测？",
     "key_points": ["DNN具有连续函数拟合能力可插值预测", "精度取决于训练数据在该区间的密度", "建议在关键区间加密扫描点"]},
    {"id": "C17", "cat": "综合运维", "route": "FAISS",  "max_score": 3,
     "q": "平台构建数据集时采用的'元数据驱动动态模板'机制是什么？如何兼容不同设备的输入维度差异？",
     "key_points": ["动态模板（用户定义输入变量列表与输出目标，平台自动映射装配）", "兼容机制（每个变量分配独立角色，适配1维/4维）", "举例（电抗器1维I vs 变压器4维V₁/V₂/I₁/I₂）"]},
]


# ══════════════════════════════════════════════════════
#  Qwen API 调用
# ══════════════════════════════════════════════════════
def build_prompt(method: str, question: str, q_id: str, route: str) -> str:
    """根据方法类型拼装不同的 Prompt"""
    faiss_ctx, kg_ctx = get_context(route, q_id)

    if method == "纯LLM":
        # 无任何检索上下文
        return question

    elif method == "FAISS-Only":
        # 仅注入文档片段
        return f"{faiss_ctx}\n\n请根据以上知识库文档内容回答：\n{question}"

    else:  # KG-RAG
        # 注入图谱三元组 + 文档片段（双轨）
        return (
            f"{kg_ctx}\n\n"
            f"{faiss_ctx}\n\n"
            f"请综合以上知识图谱因果链和文档知识回答：\n{question}"
        )


import json as _json   # json 已在顶部 import os 中可用，单独别名避免冲突

def call_qwen(prompt: str) -> tuple[float, str]:
    """
    调用 Qwen 流式 API，返回 (首Token时延秒, 完整答案文本)
    首Token时延 = 从请求发出 → 收到第一个有内容的 SSE chunk 的时间
    """
    if not API_KEY:
        return 0.0, "未设置 DASHSCOPE_API_KEY"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
        "Accept":        "text/event-stream",
    }
    body = {
        "model": MODEL,
        "input": {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ]
        },
        "parameters": {
            "temperature":        TEMPERATURE,
            "max_tokens":         MAX_TOKENS,
            "result_format":      "message",
            "incremental_output": True,   # 每个 chunk 只含新增内容
        },
        "stream": True,
    }

    try:
        t0  = time.perf_counter()
        res = requests.post(
            QWEN_URL, headers=headers, json=body,
            timeout=TIMEOUT_SEC, stream=True
        )
        res.raise_for_status()

        ttft        = None   # 首Token时延
        full_answer = ""

        for raw_line in res.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            if not raw_line.startswith("data:"):
                continue

            data_str = raw_line[5:].strip()
            if data_str == "[DONE]":
                break

            try:
                chunk   = _json.loads(data_str)
                choices = chunk.get("output", {}).get("choices", [])
                if not choices:
                    continue
                content = choices[0].get("message", {}).get("content", "")

                # 第一个有内容的 chunk → 记录首Token时延
                if content and ttft is None:
                    ttft = round(time.perf_counter() - t0, 3)

                full_answer += content

                if choices[0].get("finish_reason") == "stop":
                    break

            except _json.JSONDecodeError:
                continue

        # 若未触发（空响应兜底）
        if ttft is None:
            ttft = round(time.perf_counter() - t0, 3)

        return ttft, full_answer

    except requests.Timeout:
        return float(TIMEOUT_SEC), "[超时]"
    except Exception as e:
        return 0.0, f"[异常: {e}]"


# ══════════════════════════════════════════════════════
#  LLM-as-Judge：RAGAS三指标自动评分（F / CR / AR）
#  每个函数调用一次Qwen，要求返回0~1之间的浮点数
# ══════════════════════════════════════════════════════

def _call_judge(judge_prompt: str) -> float:
    """调用Qwen做评分裁判，返回0.0~1.0之间的分数"""
    if not API_KEY:
        return 0.0
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }
    body = {
        "model": MODEL,
        "input": {
            "messages": [
                {"role": "system", "content": (
                    "你是一个严格的评估裁判。你只输出一个0到1之间的浮点数作为评分，"
                    "不要输出任何解释文字。例如：0.85"
                )},
                {"role": "user", "content": judge_prompt},
            ]
        },
        "parameters": {
            "temperature": 0.0,
            "max_tokens":  16,
            "result_format": "message",
        },
    }
    try:
        res = requests.post(QWEN_URL, headers=headers, json=body, timeout=TIMEOUT_SEC)
        res.raise_for_status()
        data = res.json()
        text = data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "0")
        # 提取第一个浮点数
        import re
        match = re.search(r"(\d+\.?\d*)", text.strip())
        score = float(match.group(1)) if match else 0.0
        return min(max(score, 0.0), 1.0)
    except Exception:
        return 0.0


def judge_faithfulness(answer: str, context: str) -> float:
    """
    忠实度(F)：答案中每个事实陈述是否都有上下文支撑
    F=1.0表示完全忠实，F=0.0表示完全幻觉
    """
    prompt = f"""请评估以下【系统答案】的忠实度。
忠实度定义：答案中每一个事实性陈述是否都可以从【检索上下文】中找到明确依据。
如果答案完全基于上下文内容生成、没有编造任何信息，得分接近1.0。
如果答案中存在上下文完全未提及的事实断言（即幻觉），应降低分数。

【检索上下文】
{context}

【系统答案】
{answer}

请输出0到1之间的忠实度得分（仅输出数字）："""
    return judge_faithfulness.__wrapped__(prompt) if hasattr(judge_faithfulness, '__wrapped__') else _call_judge(prompt)


def judge_context_recall(key_points: list[str], context: str) -> float:
    """
    上下文召回率(CR)：参考答案的关键要点能否在检索上下文中找到依据
    CR=1.0表示所有要点都有覆盖
    """
    points_str = "\n".join(f"  {i+1}. {p}" for i, p in enumerate(key_points))
    prompt = f"""请评估以下【检索上下文】对【参考答案要点】的覆盖程度。
上下文召回率定义：参考答案中的每个关键陈述，是否都能在检索到的上下文中找到支撑依据。

【参考答案要点】（共{len(key_points)}条）
{points_str}

【检索上下文】
{context}

计算方式：被上下文覆盖的要点数 / 总要点数。
请输出0到1之间的召回率得分（仅输出数字）："""
    return _call_judge(prompt)


def judge_answer_relevancy(question: str, answer: str) -> float:
    """
    答案相关性(AR)：答案是否切题、是否针对原始问题给出有效回复
    AR=1.0表示完全切题
    """
    prompt = f"""请评估以下【系统答案】对【用户问题】的相关性与针对性。
答案相关性定义：答案是否直接回答了用户的问题，是否聚焦而不跑题。
答案完全切题且全面得分接近1.0，答非所问或过度宽泛得分接近0.0。

【用户问题】
{question}

【系统答案】
{answer}

请输出0到1之间的相关性得分（仅输出数字）："""
    return _call_judge(prompt)


# ══════════════════════════════════════════════════════
#  主实验流程（生成答案 + LLM-as-Judge自动评分）
# ══════════════════════════════════════════════════════
METHODS = ["纯LLM", "FAISS-Only", "KG-RAG"]

def run_experiment():
    if not API_KEY:
        print("❌ 未找到 DASHSCOPE_API_KEY，请先执行：")
        print('   $env:DASHSCOPE_API_KEY = "sk-你的密钥"')
        return

    # 生成答案：51题 × 3方法 = 153次；自动评分：每题每方法3次judge ≈ 459次
    gen_calls   = len(QUESTIONS) * len(METHODS) * REPEAT_TIMES
    judge_calls = len(QUESTIONS) * len(METHODS) * 3  # F + CR + AR (纯LLM无CR则少一些)
    total_calls = gen_calls + judge_calls
    print(f"开始实验：{len(QUESTIONS)} 题 × {len(METHODS)} 方法")
    print(f"  生成答案: {gen_calls} 次 API 调用")
    print(f"  自动评分: ~{judge_calls} 次 Judge 调用")
    print(f"  模型：{MODEL}，预计耗时约 {total_calls * 2 // 60 + 1} 分钟\n")

    rows = []
    for i, q in enumerate(QUESTIONS, 1):
        row = {
            "题号":     q["id"],
            "类别":     q["cat"],
            "意图路由": q["route"],
            "问题":     q["q"],
            "评分要点": "\n".join(f"{j+1}. {p}" for j, p in enumerate(q["key_points"])),
        }

        for method in METHODS:
            print(f"  [{i:02d}/{len(QUESTIONS)}] {q['id']} | {method} ...", end=" ", flush=True)

            # ── Step1: 生成答案 ──
            prompt = build_prompt(method, q["q"], q["id"], q["route"])
            _, answer = call_qwen(prompt)
            row[f"{method}_答案"] = answer

            # ── Step2: 获取该方法的检索上下文（评分用） ──
            faiss_ctx, kg_ctx = get_context(q["route"], q["id"])
            if method == "纯LLM":
                ctx_for_judge = ""       # 纯LLM无检索上下文
            elif method == "FAISS-Only":
                ctx_for_judge = faiss_ctx
            else:  # KG-RAG
                ctx_for_judge = kg_ctx + "\n" + faiss_ctx

            # ── Step3: LLM-as-Judge 自动评分 ──
            # Faithfulness（纯LLM也评，用空上下文→预期得分低）
            f_score = judge_faithfulness(answer, ctx_for_judge) if ctx_for_judge else judge_faithfulness(answer, "（无检索上下文，模型完全依赖自身参数）")

            # Context Recall（纯LLM无检索步骤，CR设为N/A→记-1用于后续过滤）
            if method == "纯LLM":
                cr_score = -1.0   # 标记为不适用
            else:
                cr_score = judge_context_recall(q["key_points"], ctx_for_judge)

            # Answer Relevancy
            ar_score = judge_answer_relevancy(q["q"], answer)

            row[f"{method}_F"]  = round(f_score, 3)
            row[f"{method}_CR"] = round(cr_score, 3) if cr_score >= 0 else ""
            row[f"{method}_AR"] = round(ar_score, 3)

            print(f"F={f_score:.2f} CR={'—' if cr_score<0 else f'{cr_score:.2f}'} AR={ar_score:.2f} ✓")

        rows.append(row)

    # ── 输出 Excel ──
    cols_fixed  = ["题号", "类别", "意图路由", "问题", "评分要点"]
    cols_method = []
    for m in METHODS:
        cols_method += [f"{m}_答案", f"{m}_F", f"{m}_CR", f"{m}_AR"]

    df = pd.DataFrame(rows)[cols_fixed + cols_method]
    df.to_excel(OUTPUT_FILE, index=False, engine="openpyxl")

    print(f"\n✅ 实验完成！结果已保存至: {OUTPUT_FILE}")
    print("运行 python run_experiment.py --calc 查看论文表格数据")


# ══════════════════════════════════════════════════════
#  指标统计（读取Excel自动评分，输出论文表格）
# ══════════════════════════════════════════════════════
def calc_metrics():
    if not OUTPUT_FILE.exists():
        print(f"❌ 找不到 {OUTPUT_FILE}，请先运行实验")
        return

    df = pd.read_excel(OUTPUT_FILE, engine="openpyxl")
    print("\n" + "="*60)
    print("  📊 5.5节 KG-RAG 对比实验结果（RAGAS三指标）")
    print("="*60)

    summary = {}
    for method in METHODS:
        f_vals  = pd.to_numeric(df.get(f"{method}_F"),  errors="coerce").fillna(0)
        cr_vals = pd.to_numeric(df.get(f"{method}_CR"), errors="coerce")
        ar_vals = pd.to_numeric(df.get(f"{method}_AR"), errors="coerce").fillna(0)

        avg_f  = round(f_vals.mean(), 3)
        avg_ar = round(ar_vals.mean(), 3)
        # CR：纯LLM的CR列为空/NaN，取有效值均值
        cr_valid = cr_vals.dropna()
        cr_valid = cr_valid[cr_valid >= 0]
        avg_cr = round(cr_valid.mean(), 3) if len(cr_valid) > 0 else None

        summary[method] = {"F": avg_f, "CR": avg_cr, "AR": avg_ar}
        print(f"\n  【{method}】")
        print(f"    忠实度 F       : {avg_f:.3f}")
        print(f"    上下文召回率 CR: {'—' if avg_cr is None else f'{avg_cr:.3f}'}")
        print(f"    答案相关性 AR  : {avg_ar:.3f}")

    # ── 按类别细分（表5-7） ──
    print("\n" + "-"*60)
    print("  📊 按类别细分（对应论文表5-7）")
    print("-"*60)
    cat_summary = {}
    for cat in df["类别"].unique():
        sub = df[df["类别"] == cat]
        cat_summary[cat] = {}
        print(f"\n  【{cat}】（{len(sub)}题）")
        for method in ["FAISS-Only", "KG-RAG"]:
            f_v  = pd.to_numeric(sub.get(f"{method}_F"),  errors="coerce").fillna(0).mean()
            cr_v = pd.to_numeric(sub.get(f"{method}_CR"), errors="coerce").dropna()
            cr_v = cr_v[cr_v >= 0].mean() if len(cr_v[cr_v >= 0]) > 0 else 0
            ar_v = pd.to_numeric(sub.get(f"{method}_AR"), errors="coerce").fillna(0).mean()
            cat_summary[cat][method] = {"F": round(f_v,3), "CR": round(cr_v,3), "AR": round(ar_v,3)}
            print(f"    {method}: F={f_v:.3f}  CR={cr_v:.3f}  AR={ar_v:.3f}")

    # ── Markdown 表格（直接复制进论文） ──
    print("\n" + "="*60)
    print("  📋 表5-6 综合性能对比（直接复制进论文）")
    print("="*60)
    print("\n| 方法 | 上下文召回率 CR | 忠实度 F | 答案相关性 AR |")
    print("|-----|:-----------:|:------:|:----------:|")
    for m, v in summary.items():
        b = "**" if m == "KG-RAG" else ""
        cr_str = "—" if v["CR"] is None else f"{b}{v['CR']}{b}"
        print(f"| {b}{m}{b} | {cr_str} | {b}{v['F']}{b} | {b}{v['AR']}{b} |")

    print('\n> 注：纯LLM方法不涉及显式检索步骤，故CR项以"—"表示；各项指标取值范围均为[0,1]，越高越好。')

    print("\n" + "="*60)
    print("  📋 表5-7 按类别分项对比（直接复制进论文）")
    print("="*60)
    print("\n| 问题类别（各17题） | 方法 | 上下文召回率 CR | 忠实度 F | 答案相关性 AR |")
    print("|:---------------|:---:|:-----------:|:------:|:----------:|")
    cat_labels = {"故障诊断": "A类·设备故障诊断", "调参辅助": "B类·模型调参辅助", "综合运维": "C类·综合运维咨询"}
    for cat, label in cat_labels.items():
        if cat in cat_summary:
            for method in ["FAISS-Only", "KG-RAG"]:
                v = cat_summary[cat][method]
                b = "**" if method == "KG-RAG" else ""
                prefix = f"**{label}**" if method == "FAISS-Only" else ""
                print(f"| {prefix} | {b}{method}{b} | {b}{v['CR']}{b} | {b}{v['F']}{b} | {b}{v['AR']}{b} |")

    print("\n✅ 将上表数据填入论文5.5.4节即可。")


# ══════════════════════════════════════════════════════
#  入口
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--calc", action="store_true", help="统计已评分的Excel，输出论文指标")
    args = parser.parse_args()
    calc_metrics() if args.calc else run_experiment()


