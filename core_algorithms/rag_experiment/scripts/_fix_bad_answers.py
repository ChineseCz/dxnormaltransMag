"""
_fix_bad_answers.py
===================
一步完成：对8个答案为报错信息的题目重新生成答案 + 重新评分 + 写回Excel + 输出统计
"""
import sys, os, re, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # 允许导入上层 run_experiment
import requests, pandas as pd
from core_algorithms.rag_experiment.src.run_experiment import (
    QUESTIONS, get_context, build_prompt, call_qwen,
    API_KEY as _KEY,
)

API_KEY  = os.environ.get("DASHSCOPE_API_KEY", "") or _KEY
MODEL    = "qwen-plus"
URL      = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
TIMEOUT  = 60
EXCEL    = str(Path(__file__).parent.parent / "results" / "experiment_result.xlsx")
Q_MAP    = {q["id"]: q for q in QUESTIONS}
METHODS  = ["纯LLM", "FAISS-Only", "KG-RAG"]

# ── 需要修复的 (题号, 方法) ──
FIX_LIST = [
    ("B06", "FAISS-Only"),
    ("B08", "FAISS-Only"),
    ("C06", "FAISS-Only"),
    ("C07", "FAISS-Only"),
    ("C07", "KG-RAG"),
    ("C09", "FAISS-Only"),
    ("C09", "KG-RAG"),
    ("C10", "FAISS-Only"),
]


# ══════════════════════════════════════════════════════
#  Judge 函数（带重试）
# ══════════════════════════════════════════════════════
def _call_judge(prompt: str) -> float:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": MODEL,
        "input": {"messages": [
            {"role": "system", "content":
                "你是一个严格的评估裁判。你只输出一个0到1之间的浮点数作为评分，"
                "不要输出任何解释文字。例如：0.85"},
            {"role": "user", "content": prompt},
        ]},
        "parameters": {"temperature": 0.0, "max_tokens": 16, "result_format": "message"},
    }
    for attempt in range(3):
        try:
            res = requests.post(URL, headers=headers, json=body, timeout=TIMEOUT)
            res.raise_for_status()
            data = res.json()
            text = data.get("output", {}).get("choices", [{}])[0] \
                       .get("message", {}).get("content", "0")
            m = re.search(r"(\d+\.?\d*)", text.strip())
            score = float(m.group(1)) if m else 0.0
            return min(max(score, 0.0), 1.0)
        except Exception as e:
            print(f"      ⚠ 重试 {attempt+1}/3: {e}")
            time.sleep(3)
    return 0.0


def judge_f(answer, context):
    return _call_judge(
        f"请评估以下【系统答案】的忠实度。\n"
        f"忠实度：答案中每个事实陈述是否都有【检索上下文】支撑。\n"
        f"完全基于上下文=1.0，有幻觉=降低。\n\n"
        f"【检索上下文】\n{context}\n\n【系统答案】\n{answer}\n\n"
        f"请输出0到1之间的忠实度得分（仅数字）：")


def judge_cr(key_points, context):
    pts = "\n".join(f"  {i+1}. {p}" for i, p in enumerate(key_points))
    return _call_judge(
        f"请评估【检索上下文】对【参考答案要点】的覆盖程度。\n"
        f"被覆盖的要点数/总要点数。\n\n"
        f"【参考答案要点】（共{len(key_points)}条）\n{pts}\n\n"
        f"【检索上下文】\n{context}\n\n"
        f"请输出0到1之间的召回率得分（仅数字）：")


def judge_ar(question, answer):
    return _call_judge(
        f"请评估以下【系统答案】对【用户问题】的相关性。\n"
        f"完全切题=1.0，答非所问=0.0。\n\n"
        f"【用户问题】\n{question}\n\n【系统答案】\n{answer}\n\n"
        f"请输出0到1之间的相关性得分（仅数字）：")


# ══════════════════════════════════════════════════════
#  主流程
# ══════════════════════════════════════════════════════
def main():
    if not API_KEY:
        print("❌ 未设置 DASHSCOPE_API_KEY"); return

    df = pd.read_excel(EXCEL, engine="openpyxl")
    qid_to_idx = {row["题号"]: idx for idx, row in df.iterrows()}

    print(f"🔧 修复 {len(FIX_LIST)} 个坏答案（重新生成 + 重新评分）\n")

    for qid, method in FIX_LIST:
        idx = qid_to_idx[qid]
        q = Q_MAP[qid]

        print(f"  [{qid}] {method}", flush=True)

        # ── Step1: 重新生成答案 ──
        prompt = build_prompt(method, q["q"], qid, q["route"])
        _, answer = call_qwen(prompt)

        if answer.startswith("[异常") or answer.startswith("[超时"):
            print(f"    ❌ 生成仍然失败: {answer[:60]}")
            continue

        df.at[idx, f"{method}_答案"] = answer
        print(f"    ✅ 答案已重新生成 ({len(answer)}字)")

        # ── Step2: 获取上下文 ──
        faiss_ctx, kg_ctx = get_context(q["route"], qid)
        ctx = faiss_ctx if method == "FAISS-Only" else (kg_ctx + "\n" + faiss_ctx)

        # ── Step3: 评分 ──
        f_score  = judge_f(answer, ctx)
        cr_score = judge_cr(q["key_points"], ctx)
        ar_score = judge_ar(q["q"], answer)

        df.at[idx, f"{method}_F"]  = round(f_score, 3)
        df.at[idx, f"{method}_CR"] = round(cr_score, 3)
        df.at[idx, f"{method}_AR"] = round(ar_score, 3)

        print(f"    📊 F={f_score:.2f}  CR={cr_score:.2f}  AR={ar_score:.2f}")

    # ── 写回 Excel ──
    df.to_excel(EXCEL, index=False, engine="openpyxl")
    print(f"\n✅ 已写回 {EXCEL}")

    # ── 输出修正后的论文表格 ──
    print_summary(df)


def print_summary(df):
    print("\n" + "=" * 60)
    print("  📊 表5-6 综合性能对比（修正后，30题）")
    print("=" * 60)

    summary = {}
    for method in METHODS:
        f_vals  = pd.to_numeric(df.get(f"{method}_F"),  errors="coerce")
        cr_vals = pd.to_numeric(df.get(f"{method}_CR"), errors="coerce")
        ar_vals = pd.to_numeric(df.get(f"{method}_AR"), errors="coerce")
        avg_f  = round(f_vals.mean(), 3)
        avg_ar = round(ar_vals.mean(), 3)
        cr_valid = cr_vals.dropna()
        cr_valid = cr_valid[cr_valid >= 0]
        avg_cr = round(cr_valid.mean(), 3) if len(cr_valid) > 0 else None
        summary[method] = {"F": avg_f, "CR": avg_cr, "AR": avg_ar}

    print("\n| 方法 | 上下文召回率 CR | 忠实度 F | 答案相关性 AR |")
    print("|-----|:-----------:|:------:|:----------:|")
    for m, v in summary.items():
        b = "**" if m == "KG-RAG" else ""
        cr_s = "—" if v["CR"] is None else f"{b}{v['CR']}{b}"
        print(f"| {b}{m}{b} | {cr_s} | {b}{v['F']}{b} | {b}{v['AR']}{b} |")

    # 按类别
    print("\n" + "=" * 60)
    print("  📊 表5-7 按类别分项对比（修正后）")
    print("=" * 60)
    print("\n| 问题类别 | 方法 | CR | F | AR |")
    print("|:-------|:---:|:--:|:-:|:--:|")
    cat_labels = {
        "故障诊断": "A类·设备故障诊断",
        "调参辅助": "B类·模型调参辅助",
        "综合运维": "C类·综合运维咨询",
    }
    for cat, label in cat_labels.items():
        sub = df[df["类别"] == cat]
        if len(sub) == 0:
            continue
        for method in ["FAISS-Only", "KG-RAG"]:
            f_v = pd.to_numeric(sub.get(f"{method}_F"), errors="coerce").mean()
            cr_v = pd.to_numeric(sub.get(f"{method}_CR"), errors="coerce").dropna()
            cr_v = cr_v[cr_v >= 0]
            cr_m = round(cr_v.mean(), 3) if len(cr_v) > 0 else 0
            ar_v = pd.to_numeric(sub.get(f"{method}_AR"), errors="coerce").mean()
            b = "**" if method == "KG-RAG" else ""
            pf = f"**{label}**（{len(sub)}题）" if method == "FAISS-Only" else ""
            print(f"| {pf} | {b}{method}{b} | {b}{cr_m:.3f}{b} | {b}{f_v:.3f}{b} | {b}{ar_v:.3f}{b} |")

    print("\n✅ 论文数据已就绪！")


if __name__ == "__main__":
    main()

