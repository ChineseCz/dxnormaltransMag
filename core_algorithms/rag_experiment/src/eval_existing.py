"""
eval_existing.py  ──  对已有30题答案做 RAGAS 三指标自动评分
=====================================================
读取 experiment_result.xlsx 中已有的答案列，
调用 Qwen LLM-as-Judge 为每道题的三方法答案打 F / CR / AR 分，
结果写回同一 Excel（新增列）并输出论文表格。

用法：
  $env:DASHSCOPE_API_KEY = "sk-xxx"
  python eval_existing.py
"""

import os, re, time, sys
import requests
import pandas as pd
from pathlib import Path

# ── 从 run_experiment.py 复用所有上下文常量和路由函数 ──
from run_experiment import (
    QUESTIONS, get_context,
    KG_PHYSICAL, KG_SOFTWARE,
    SYSTEM_PROMPT,
)

# ══════════════════════════════════════════════════════
#  配置
# ══════════════════════════════════════════════════════
API_KEY     = os.getenv("DASHSCOPE_API_KEY", "")
MODEL       = "qwen-plus"
TIMEOUT_SEC = 60
QWEN_URL    = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
EXCEL_PATH  = Path(__file__).parent / "results" / "experiment_result.xlsx"
METHODS     = ["纯LLM", "FAISS-Only", "KG-RAG"]

# 构建 题号 → QUESTIONS dict 的快查表
Q_MAP = {q["id"]: q for q in QUESTIONS}


# ══════════════════════════════════════════════════════
#  LLM-as-Judge 核心函数（简化版，修复了原 bug）
# ══════════════════════════════════════════════════════
def _call_judge(judge_prompt: str) -> float:
    """调用 Qwen 做评分裁判，返回 0.0~1.0"""
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
        text = data.get("output", {}).get("choices", [{}])[0] \
                   .get("message", {}).get("content", "0")
        match = re.search(r"(\d+\.?\d*)", text.strip())
        score = float(match.group(1)) if match else 0.0
        return min(max(score, 0.0), 1.0)
    except Exception as e:
        print(f"    ⚠ Judge 调用失败: {e}")
        return 0.0


def judge_faithfulness(answer: str, context: str) -> float:
    prompt = f"""请评估以下【系统答案】的忠实度。
忠实度定义：答案中每一个事实性陈述是否都可以从【检索上下文】中找到明确依据。
如果答案完全基于上下文内容生成、没有编造任何信息，得分接近1.0。
如果答案中存在上下文完全未提及的事实断言（即幻觉），应降低分数。

【检索上下文】
{context}

【系统答案】
{answer}

请输出0到1之间的忠实度得分（仅输出数字）："""
    return _call_judge(prompt)


def judge_context_recall(key_points: list, context: str) -> float:
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
#  主流程
# ══════════════════════════════════════════════════════
def main():
    if not API_KEY:
        print("❌ 未设置 DASHSCOPE_API_KEY，请先执行：")
        print('   $env:DASHSCOPE_API_KEY = "sk-你的密钥"')
        sys.exit(1)

    if not EXCEL_PATH.exists():
        print(f"❌ 找不到 {EXCEL_PATH}")
        sys.exit(1)

    df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
    n = len(df)
    print(f"📖 读取 {EXCEL_PATH.name}，共 {n} 行")

    # 预估 API 调用量
    # 每题 × 3方法 × (F + CR + AR)，纯LLM无CR → 每题约 3*3-1 = 8 次
    total_calls = n * (3 * 3 - 1)  # 纯LLM跳过CR
    print(f"📊 预计 ~{total_calls} 次 Judge API 调用，耗时约 {total_calls * 2 // 60 + 1} 分钟\n")

    # 初始化新列
    for m in METHODS:
        for metric in ["F", "CR", "AR"]:
            col = f"{m}_{metric}"
            if col not in df.columns:
                df[col] = None

    t_start = time.time()

    for idx, row in df.iterrows():
        qid = row["题号"]
        q_info = Q_MAP.get(qid)
        if not q_info:
            print(f"  ⚠ 题号 {qid} 未在 QUESTIONS 中找到，跳过")
            continue

        question   = q_info["q"]
        key_points = q_info["key_points"]
        route      = q_info["route"]

        # 获取该题的检索上下文
        faiss_ctx, kg_ctx = get_context(route, qid)

        print(f"[{idx+1:02d}/{n}] {qid} ({q_info['cat']})", flush=True)

        for method in METHODS:
            ans_col = f"{method}_答案"
            answer  = str(row.get(ans_col, ""))
            if not answer or answer == "nan":
                print(f"  {method}: 无答案，跳过")
                continue

            # 确定该方法的上下文
            if method == "纯LLM":
                ctx = "（无检索上下文，模型完全依赖自身参数）"
            elif method == "FAISS-Only":
                ctx = faiss_ctx
            else:  # KG-RAG
                ctx = kg_ctx + "\n" + faiss_ctx

            # ── F: Faithfulness ──
            f_score = judge_faithfulness(answer, ctx)

            # ── CR: Context Recall（纯LLM跳过）──
            if method == "纯LLM":
                cr_score = None
            else:
                cr_score = judge_context_recall(key_points, ctx)

            # ── AR: Answer Relevancy ──
            ar_score = judge_answer_relevancy(question, answer)

            # 写入 DataFrame
            df.at[idx, f"{method}_F"]  = round(f_score, 3)
            df.at[idx, f"{method}_CR"] = round(cr_score, 3) if cr_score is not None else ""
            df.at[idx, f"{method}_AR"] = round(ar_score, 3)

            cr_disp = "—" if cr_score is None else f"{cr_score:.2f}"
            print(f"  {method}: F={f_score:.2f}  CR={cr_disp}  AR={ar_score:.2f}")

    elapsed = time.time() - t_start
    print(f"\n⏱ 评分完成，耗时 {elapsed/60:.1f} 分钟")

    # ── 保存 Excel ──
    df.to_excel(EXCEL_PATH, index=False, engine="openpyxl")
    print(f"✅ 结果已写回 {EXCEL_PATH.name}")

    # ── 输出统计 ──
    print_summary(df)


def print_summary(df: pd.DataFrame):
    """输出论文表格格式的统计"""
    print("\n" + "=" * 60)
    print("  📊 表5-6 综合性能对比（30题）")
    print("=" * 60)

    summary = {}
    for method in METHODS:
        f_vals  = pd.to_numeric(df.get(f"{method}_F"),  errors="coerce")
        cr_vals = pd.to_numeric(df.get(f"{method}_CR"), errors="coerce")
        ar_vals = pd.to_numeric(df.get(f"{method}_AR"), errors="coerce")

        avg_f  = round(f_vals.mean(), 3) if f_vals.notna().any() else 0
        avg_ar = round(ar_vals.mean(), 3) if ar_vals.notna().any() else 0
        cr_valid = cr_vals.dropna()
        cr_valid = cr_valid[cr_valid >= 0]
        avg_cr = round(cr_valid.mean(), 3) if len(cr_valid) > 0 else None

        summary[method] = {"F": avg_f, "CR": avg_cr, "AR": avg_ar}
        print(f"\n  【{method}】")
        print(f"    忠实度 F       : {avg_f:.3f}")
        print(f"    上下文召回率 CR: {'—' if avg_cr is None else f'{avg_cr:.3f}'}")
        print(f"    答案相关性 AR  : {avg_ar:.3f}")

    # Markdown 表格
    print("\n" + "=" * 60)
    print("  📋 Markdown 表格（直接复制进论文）")
    print("=" * 60)
    print("\n| 方法 | 上下文召回率 CR | 忠实度 F | 答案相关性 AR |")
    print("|-----|:-----------:|:------:|:----------:|")
    for m, v in summary.items():
        b = "**" if m == "KG-RAG" else ""
        cr_str = "—" if v["CR"] is None else f"{b}{v['CR']}{b}"
        print(f"| {b}{m}{b} | {cr_str} | {b}{v['F']}{b} | {b}{v['AR']}{b} |")

    # ── 按类别细分（表5-7） ──
    print("\n" + "=" * 60)
    print("  📋 表5-7 按类别分项对比")
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
            f_v  = pd.to_numeric(sub.get(f"{method}_F"),  errors="coerce").mean()
            cr_v = pd.to_numeric(sub.get(f"{method}_CR"), errors="coerce").dropna()
            cr_v = cr_v[cr_v >= 0]
            cr_mean = round(cr_v.mean(), 3) if len(cr_v) > 0 else 0
            ar_v = pd.to_numeric(sub.get(f"{method}_AR"), errors="coerce").mean()
            b = "**" if method == "KG-RAG" else ""
            prefix = f"**{label}**（{len(sub)}题）" if method == "FAISS-Only" else ""
            print(f"| {prefix} | {b}{method}{b} | {b}{cr_mean:.3f}{b} | {b}{f_v:.3f}{b} | {b}{ar_v:.3f}{b} |")


if __name__ == "__main__":
    main()

