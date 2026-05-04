"""
rag_experiment/config.py  ──  实验全局配置常量
"""
import os
from pathlib import Path

# ── Qwen API ──────────────────────────────────────────────────
API_KEY      = os.getenv("DASHSCOPE_API_KEY", "")
MODEL        = "qwen-plus"       # qwen-turbo(快/便宜) | qwen-plus | qwen-max
TEMPERATURE  = 0.1               # 低温使答案更稳定，适合评测
MAX_TOKENS   = 1024
REPEAT_TIMES = 1                 # 每题重复N次取平均时延（1次足够，节省费用）
TIMEOUT_SEC  = 60

QWEN_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

# ── 文件路径 ──────────────────────────────────────────────────
_HERE       = Path(__file__).parent          # core_algorithms/rag_experiment/
_CORE_DIR   = _HERE.parent                   # core_algorithms/
OUTPUT_FILE = _CORE_DIR / "results" / "experiment_result.xlsx"

# ── 系统提示词 ────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "你是一个专业的电力设备电磁场预测平台的技术专家，"
    "擅长铁心电抗器与变压器的故障诊断、DNN/CNN深度学习模型调参，"
    "以及平台操作指导。请根据提供的上下文知识给出准确、专业的回答。"
    "若上下文中没有相关信息，请基于自身知识作答，并注明。"
)