"""读取 Excel 评分数据，输出论文表格"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pandas as pd

_EXCEL = Path(__file__).parent.parent / "results" / "experiment_result.xlsx"
df = pd.read_excel(_EXCEL, engine="openpyxl")
METHODS = ["纯LLM", "FAISS-Only", "KG-RAG"]

print("=" * 60)
print("  表5-6 综合性能对比（30题）")
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
    cr_d = "—" if avg_cr is None else f"{avg_cr:.3f}"
    print(f"  {method:15s}  F={avg_f:.3f}  CR={cr_d}  AR={avg_ar:.3f}")

print()
print("| 方法 | 上下文召回率 CR | 忠实度 F | 答案相关性 AR |")
print("|-----|:-----------:|:------:|:----------:|")
for m, v in summary.items():
    b = "**" if m == "KG-RAG" else ""
    cr_val = v["CR"]
    cr_str = "—" if cr_val is None else f"{b}{cr_val}{b}"
    f_str = f"{b}{v['F']}{b}"
    ar_str = f"{b}{v['AR']}{b}"
    print(f"| {b}{m}{b} | {cr_str} | {f_str} | {ar_str} |")

print()
print("=" * 60)
print("  表5-7 按类别分项对比")
print("=" * 60)
print()
print("| 问题类别 | 方法 | CR | F | AR |")
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
        cr_mean = round(cr_v.mean(), 3) if len(cr_v) > 0 else 0
        ar_v = pd.to_numeric(sub.get(f"{method}_AR"), errors="coerce").mean()
        b = "**" if method == "KG-RAG" else ""
        prefix = f"**{label}**（{len(sub)}题）" if method == "FAISS-Only" else ""
        print(f"| {prefix} | {b}{method}{b} | {b}{cr_mean:.3f}{b} | {b}{f_v:.3f}{b} | {b}{ar_v:.3f}{b} |")

print()
print("=" * 60)
print("  异常数据检查（F=0 或 AR=0 的题目）")
print("=" * 60)
for idx, row in df.iterrows():
    qid = row["题号"]
    for method in METHODS:
        f_val = pd.to_numeric(row.get(f"{method}_F", 0), errors="coerce")
        ar_val = pd.to_numeric(row.get(f"{method}_AR", 0), errors="coerce")
        if method != "纯LLM" and (f_val == 0 or ar_val == 0):
            print(f"  ⚠ {qid} {method}: F={f_val}, AR={ar_val}")

