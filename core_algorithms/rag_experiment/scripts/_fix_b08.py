"""单独补跑 B08 FAISS-Only（上次SSL失败）"""
import sys, os, re, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # 允许导入上层 run_experiment
import requests, pandas as pd
from core_algorithms.rag_experiment.src.run_experiment import QUESTIONS, get_context, build_prompt, call_qwen

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
MODEL   = "qwen-plus"
URL     = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
Q_MAP   = {q["id"]: q for q in QUESTIONS}
EXCEL   = str(Path(__file__).parent.parent / "results" / "experiment_result.xlsx")

def _call_judge(prompt):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    body = {"model": MODEL, "input": {"messages": [
        {"role": "system", "content": "你是一个严格的评估裁判。你只输出一个0到1之间的浮点数作为评分，不要输出任何解释文字。例如：0.85"},
        {"role": "user", "content": prompt},
    ]}, "parameters": {"temperature": 0.0, "max_tokens": 16, "result_format": "message"}}
    for i in range(5):
        try:
            res = requests.post(URL, headers=headers, json=body, timeout=60)
            res.raise_for_status()
            text = res.json().get("output",{}).get("choices",[{}])[0].get("message",{}).get("content","0")
            m = re.search(r"(\d+\.?\d*)", text.strip())
            return min(max(float(m.group(1)),0),1) if m else 0.0
        except Exception as e:
            print(f"  重试{i+1}/5: {e}")
            time.sleep(5)
    return 0.0

df = pd.read_excel(EXCEL, engine="openpyxl")
qid, method = "B08", "FAISS-Only"
idx = df[df["题号"]==qid].index[0]
q = Q_MAP[qid]

print(f"补跑 {qid} {method}...")
# 生成答案（重试5次）
for attempt in range(5):
    prompt = build_prompt(method, q["q"], qid, q["route"])
    _, answer = call_qwen(prompt)
    if not answer.startswith("[异常") and not answer.startswith("[超时"):
        break
    print(f"  生成重试 {attempt+1}/5")
    time.sleep(5)

if answer.startswith("[异常") or answer.startswith("[超时"):
    print(f"❌ 彻底失败: {answer[:80]}")
else:
    df.at[idx, f"{method}_答案"] = answer
    print(f"✅ 答案生成成功 ({len(answer)}字)")
    faiss_ctx, _ = get_context(q["route"], qid)
    f_s = _call_judge(f"评估忠实度(0~1)。\n上下文：{faiss_ctx}\n答案：{answer}\n仅输出数字：")
    cr_s = _call_judge(f"评估上下文对要点的覆盖(0~1)。\n要点：{chr(10).join(q['key_points'])}\n上下文：{faiss_ctx}\n仅输出数字：")
    ar_s = _call_judge(f"评估答案对问题的相关性(0~1)。\n问题：{q['q']}\n答案：{answer}\n仅输出数字：")
    df.at[idx, f"{method}_F"] = round(f_s, 3)
    df.at[idx, f"{method}_CR"] = round(cr_s, 3)
    df.at[idx, f"{method}_AR"] = round(ar_s, 3)
    print(f"📊 F={f_s:.2f}  CR={cr_s:.2f}  AR={ar_s:.2f}")
    df.to_excel(EXCEL, index=False, engine="openpyxl")
    print(f"✅ 已写回 {EXCEL}")


