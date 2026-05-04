"""补跑 B06/C10 纯LLM（检查答案+重评AR）"""
import sys, os, re, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # 允许导入上层 run_experiment
import requests, pandas as pd
from core_algorithms.rag_experiment.src.run_experiment import QUESTIONS, call_qwen

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
            print(f"    重试{i+1}/5: {e}"); time.sleep(5)
    return 0.0

df = pd.read_excel(EXCEL, engine="openpyxl")# 强制将评分列转 float，避免 int64 写入 float 报错
for col in df.columns:
    if col.endswith("_F") or col.endswith("_CR") or col.endswith("_AR"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)
qid_to_idx = {row["题号"]: idx for idx, row in df.iterrows()}

for qid in ["B06", "C10"]:
    idx = qid_to_idx[qid]
    q = Q_MAP[qid]
    answer = str(df.iloc[idx]["纯LLM_答案"])
    print(f"[{qid}] 纯LLM  答案前60字: {answer[:60]}")

    if answer.startswith("[异常") or answer.startswith("[超时"):
        print("  ⚠ 答案是报错，重新生成...")
        for att in range(5):
            _, answer = call_qwen(q["q"])  # 纯LLM = 直接问，无上下文
            if not answer.startswith("[异常"): break
            time.sleep(5)
        df.at[idx, "纯LLM_答案"] = answer
        print(f"  ✅ 重新生成 ({len(answer)}字)")

    f_s = _call_judge(
        f"评估忠实度(0~1)。上下文：（无检索上下文）\n答案：{answer[:2000]}\n仅输出数字：")
    ar_s = _call_judge(
        f"评估答案相关性(0~1)。问题：{q['q']}\n答案：{answer[:2000]}\n仅输出数字：")
    df.at[idx, "纯LLM_F"] = round(f_s, 3)
    df.at[idx, "纯LLM_AR"] = round(ar_s, 3)
    print(f"  📊 F={f_s:.2f}  AR={ar_s:.2f}")

df.to_excel(EXCEL, index=False, engine="openpyxl")
print("\n✅ 写回完成")

# 最终全量统计
METHODS = ["纯LLM", "FAISS-Only", "KG-RAG"]
cats = {"故障诊断": "A类", "调参辅助": "B类", "综合运维": "C类"}
print("\n--- 表5-6 综合 ---")
for m in METHODS:
    f_v = pd.to_numeric(df[f"{m}_F"], errors="coerce").mean()
    cr_v = pd.to_numeric(df[f"{m}_CR"], errors="coerce").dropna()
    cr_v = cr_v[cr_v >= 0]
    ar_v = pd.to_numeric(df[f"{m}_AR"], errors="coerce").mean()
    cr_s = "—" if len(cr_v) == 0 else f"{cr_v.mean():.2f}"
    print(f"  {m:15s} F={f_v:.2f} CR={cr_s:>5s} AR={ar_v:.2f}")

print("\n--- 表5-7 分类 ---")
for cat, label in cats.items():
    sub = df[df["类别"] == cat]
    for m in METHODS:
        f_v = pd.to_numeric(sub[f"{m}_F"], errors="coerce").mean()
        cr_v = pd.to_numeric(sub[f"{m}_CR"], errors="coerce").dropna()
        cr_v = cr_v[cr_v >= 0]
        ar_v = pd.to_numeric(sub[f"{m}_AR"], errors="coerce").mean()
        cr_s = "—" if len(cr_v) == 0 else f"{cr_v.mean():.2f}"
        print(f"  {label} {m:15s} F={f_v:.2f} CR={cr_s:>5s} AR={ar_v:.2f}")
    print()

