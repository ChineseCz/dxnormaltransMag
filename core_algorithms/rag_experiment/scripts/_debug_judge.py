"""调试：看 Judge 原始返回内容"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # 允许导入上层 run_experiment
import requests, pandas as pd
from core_algorithms.rag_experiment.src.run_experiment import QUESTIONS, get_context

_EXCEL = Path(__file__).parent.parent / "results" / "experiment_result.xlsx"

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
MODEL   = "qwen-plus"
URL     = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
Q_MAP   = {q["id"]: q for q in QUESTIONS}

df = pd.read_excel(_EXCEL, engine="openpyxl")

# 取 B06 FAISS-Only 做调试
qid, method = "B06", "FAISS-Only"
row = df[df["题号"] == qid].iloc[0]
q = Q_MAP[qid]
answer = str(row[f"{method}_答案"])
faiss_ctx, _ = get_context(q["route"], qid)

print(f"答案长度: {len(answer)} 字符")
print(f"上下文长度: {len(faiss_ctx)} 字符")
print(f"答案前200字: {answer[:200]}")
print()

# 手动调 Judge 看原始返回
for label, prompt in [
    ("F", f"请评估以下答案的忠实度（0~1）。答案完全基于上下文得1.0，有幻觉得0。\n\n【上下文】\n{faiss_ctx[:2000]}\n\n【答案】\n{answer[:2000]}\n\n仅输出数字："),
    ("AR", f"请评估以下答案对问题的相关性（0~1）。完全切题得1.0，答非所问得0。\n\n【问题】\n{q['q']}\n\n【答案】\n{answer[:2000]}\n\n仅输出数字："),
]:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": MODEL,
        "input": {"messages": [
            {"role": "system", "content": "你是一个严格的评估裁判。你只输出一个0到1之间的浮点数作为评分，不要输出任何解释文字。例如：0.85"},
            {"role": "user", "content": prompt},
        ]},
        "parameters": {"temperature": 0.0, "max_tokens": 16, "result_format": "message"},
    }
    res = requests.post(URL, headers=headers, json=body, timeout=60)
    data = res.json()
    print(f"[{label}] status={res.status_code}")
    print(f"  raw output: {data.get('output', {})}")
    text = data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "EMPTY")
    print(f"  content: '{text}'")
    print()

