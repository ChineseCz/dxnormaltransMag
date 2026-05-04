"""补跑8个异常零分题目的 F/CR/AR 评分"""
import sys, os, re, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # 允许导入上层 run_experiment
import requests, pandas as pd
from core_algorithms.rag_experiment.src.run_experiment import QUESTIONS, get_context

API_KEY  = os.environ.get("DASHSCOPE_API_KEY", "")
MODEL    = "qwen-plus"
URL      = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
TIMEOUT  = 60
EXCEL    = str(Path(__file__).parent.parent / "results" / "experiment_result.xlsx")
Q_MAP    = {q["id"]: q for q in QUESTIONS}

# 需要补跑的 (题号, 方法) 列表
RETRY_LIST = [
    ("B06", "FAISS-Only"),
    ("B08", "FAISS-Only"),
    ("C06", "FAISS-Only"),
    ("C07", "FAISS-Only"),
    ("C07", "KG-RAG"),
    ("C09", "FAISS-Only"),
    ("C09", "KG-RAG"),
    ("C10", "FAISS-Only"),
]


def _call_judge(prompt: str) -> float:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": MODEL,
        "input": {"messages": [
            {"role": "system", "content": "你是一个严格的评估裁判。你只输出一个0到1之间的浮点数作为评分，不要输出任何解释文字。例如：0.85"},
            {"role": "user", "content": prompt},
        ]},
        "parameters": {"temperature": 0.0, "max_tokens": 16, "result_format": "message"},
    }
    for attempt in range(3):  # 重试3次
        try:
            res = requests.post(URL, headers=headers, json=body, timeout=TIMEOUT)
            res.raise_for_status()
            data = res.json()
            text = data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "0")
            m = re.search(r"(\d+\.?\d*)", text.strip())
            score = float(m.group(1)) if m else 0.0
            return min(max(score, 0.0), 1.0)
        except Exception as e:
            print(f"      重试 {attempt+1}/3: {e}")
            time.sleep(2)
    return -1.0  # 彻底失败标记


def judge_f(answer, context):
    prompt = f"""请评估以下【系统答案】的忠实度。
忠实度定义：答案中每一个事实性陈述是否都可以从【检索上下文】中找到明确依据。
完全基于上下文生成得分接近1.0，存在幻觉则降低分数。

【检索上下文】
{context}

【系统答案】
{answer}

请输出0到1之间的忠实度得分（仅输出数字）："""
    return _call_judge(prompt)


def judge_cr(key_points, context):
    pts = "\n".join(f"  {i+1}. {p}" for i, p in enumerate(key_points))
    prompt = f"""请评估以下【检索上下文】对【参考答案要点】的覆盖程度。
被上下文覆盖的要点数 / 总要点数。

【参考答案要点】（共{len(key_points)}条）
{pts}

【检索上下文】
{context}

请输出0到1之间的召回率得分（仅输出数字）："""
    return _call_judge(prompt)


def judge_ar(question, answer):
    prompt = f"""请评估以下【系统答案】对【用户问题】的相关性与针对性。
完全切题且全面得分接近1.0，答非所问得分接近0.0。

【用户问题】
{question}

【系统答案】
{answer}

请输出0到1之间的相关性得分（仅输出数字）："""
    return _call_judge(prompt)


def main():
    if not API_KEY:
        print("❌ 未设置 DASHSCOPE_API_KEY")
        return

    df = pd.read_excel(EXCEL, engine="openpyxl")
    # 建立 题号→行索引 映射
    qid_to_idx = {row["题号"]: idx for idx, row in df.iterrows()}

    print(f"补跑 {len(RETRY_LIST)} 个异常评分，预计 ~{len(RETRY_LIST)*3*2}s\n")

    for qid, method in RETRY_LIST:
        idx = qid_to_idx.get(qid)
        if idx is None:
            print(f"  ⚠ {qid} 不在 Excel 中，跳过")
            continue

        q = Q_MAP[qid]
        row = df.iloc[idx]
        answer = str(row[f"{method}_答案"])

        faiss_ctx, kg_ctx = get_context(q["route"], qid)
        if method == "FAISS-Only":
            ctx = faiss_ctx
        else:
            ctx = kg_ctx + "\n" + faiss_ctx

        print(f"  [{qid}] {method} ...", end=" ", flush=True)

        f_score  = judge_f(answer, ctx)
        cr_score = judge_cr(q["key_points"], ctx)
        ar_score = judge_ar(q["q"], answer)

        # 仅在成功时写入
        if f_score >= 0:
            df.at[idx, f"{method}_F"] = round(f_score, 3)
        if cr_score >= 0:
            df.at[idx, f"{method}_CR"] = round(cr_score, 3)
        if ar_score >= 0:
            df.at[idx, f"{method}_AR"] = round(ar_score, 3)

        f_d  = f"{f_score:.2f}" if f_score >= 0 else "FAIL"
        cr_d = f"{cr_score:.2f}" if cr_score >= 0 else "FAIL"
        ar_d = f"{ar_score:.2f}" if ar_score >= 0 else "FAIL"
        print(f"F={f_d}  CR={cr_d}  AR={ar_d}")

    df.to_excel(EXCEL, index=False, engine="openpyxl")
    print(f"\n✅ 补跑完成，已写回 {EXCEL}")


if __name__ == "__main__":
    main()

