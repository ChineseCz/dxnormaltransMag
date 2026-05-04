"""快速测试：验证 API 连通 + 前2题 AR 评分"""
import sys, os, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # 允许导入上层 run_experiment
import requests, pandas as pd
from core_algorithms.rag_experiment.src.run_experiment import QUESTIONS

_EXCEL = Path(__file__).parent.parent / "results" / "experiment_result.xlsx"

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
MODEL = "qwen-plus"
URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
Q_MAP = {q["id"]: q for q in QUESTIONS}

def call_judge(prompt):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    body = {"model": MODEL, "input": {"messages": [
        {"role": "system", "content": "你是一个严格的评估裁判。你只输出一个0到1之间的浮点数作为评分，不要输出任何解释文字。例如：0.85"},
        {"role": "user", "content": prompt}
    ]}, "parameters": {"temperature": 0.0, "max_tokens": 16, "result_format": "message"}}
    res = requests.post(URL, headers=headers, json=body, timeout=60)
    res.raise_for_status()
    data = res.json()
    text = data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "0")
    m = re.search(r"(\d+\.?\d*)", text.strip())
    return min(max(float(m.group(1)), 0.0), 1.0) if m else 0.0

df = pd.read_excel(_EXCEL)
print(f"Loaded {len(df)} rows\n")

for idx in range(2):
    row = df.iloc[idx]
    qid = row["题号"]
    q = Q_MAP[qid]
    question_text = q["q"]
    print(f"[{qid}] {question_text[:50]}...")

    for method in ["纯LLM", "FAISS-Only", "KG-RAG"]:
        answer = str(row[method + "_答案"])[:300]
        prompt = (
            "请评估以下答案对问题的相关性。答案完全切题得分接近1.0，答非所问得分接近0.0。\n\n"
            f"问题：{question_text}\n\n答案：{answer}\n\n请输出0到1之间的得分（仅数字）："
        )
        ar = call_judge(prompt)
        print(f"  {method}: AR={ar:.2f}")

print("\n✅ API 连通正常！")

