"""
stress_test.py  ──  平台核心接口并发压力测试（真实 MySQL 版）
=================================================================
对应第六章表 6-8 四个核心接口：
  1. 用户登录鉴权          /api/user/login          500 并发  MySQL bcrypt+audit
  2. 三维场点加载(电抗器)   /api/reactor/field3d      50 并发  30000点·1.66MB JSON
  3. 智能助手问答           /api/ai/chat             100 并发  LLM 首字响应模拟
  4. 实时预测任务           /api/predict/realtime     50 并发  DNN推理+Celery队列

使用方式：
  python stress_test.py              # 快速模式 (每场景 30s，冒烟验证)
  python stress_test.py --full       # 完整模式 (每场景 600s = 10min，对应论文描述)
  python stress_test.py --scene auth # 只测单个场景
"""
import sys, os
# 强制 UTF-8 输出（兼容 Windows GBK 终端和文件重定向）
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

import requests, time, random, threading, statistics, argparse
from dataclasses import dataclass, field
from typing import List

BASE_URL = "http://127.0.0.1:5000"

# 压测用户池 —— 对应 db_setup_mysql.py 写入的 53 个用户
_USERS = (
    [("admin", "admin123"), ("user1", "user1pass"), ("tester", "test1234")]
    + [(f"worker{i:03d}", "worker123") for i in range(1, 51)]
)
_QUESTIONS = [
    "电抗器磁场分布异常如何诊断？",
    "DNN模型预测精度如何评估？",
    "铁心绕组温升超标怎么处理？",
    "频率响应分析FRA的判定标准是什么？",
    "如何对低电流区间做数据增强？",
]

# ── 场景定义 ─────────────────────────────────────────────────────────────────
SCENES = {
    "auth": {
        "name":        "用户登录鉴权",
        "concurrency": 500,
        # Little's Law: N=500, λ≈95.6, W≈0.115s, Z̄=5.5s → N̂≈531 (偏差6%)
        "think_time":  (3.0, 8.0),
        "method":      "POST",
        "url":         f"{BASE_URL}/api/user/login",
        "body_fn":     lambda: {"username": u, "password": p}
                       if False else
                       (lambda u, p: {"username": u, "password": p})(*random.choice(_USERS)),
        "note":        "MySQL bcrypt(cost=10) + 异步audit_log写入",
    },
    "field3d": {
        "name":        "三维场点加载(电抗器·30000点)",
        "concurrency": 50,
        # Little's Law: N=50, λ≈6.2, W≈3.93s, Z̄=5.5s → N̂≈58 (偏差16%)
        "think_time":  (3.0, 8.0),
        "method":      "GET",
        "url":         f"{BASE_URL}/api/reactor/field3d",
        "params":      {"n_base": 2500, "n_angles": 12},   # →30000点,~1.66MB
        "note":        "COMSOL 91462点→分层采样→绕轴旋转 30000点",
    },
    "ai": {
        "name":        "智能助手问答",
        "concurrency": 100,
        # Little's Law: N=100, λ≈15.1, W≈1.99s, Z̄=5.5s → N̂≈113 (偏差13%)
        "think_time":  (3.0, 8.0),
        "method":      "POST",
        "url":         f"{BASE_URL}/api/ai/chat",
        "body_fn":     lambda: {
            "session_id": f"sess_{random.randint(1000,9999)}",
            "message":    random.choice(_QUESTIONS),
        },
        "note":        "LLM首字响应模拟(μ=2.0s σ=0.35s)",
    },
    "predict": {
        "name":        "实时预测任务",
        "concurrency": 50,
        # Little's Law: N=50, λ≈6.6, W≈3.18s, Z̄=5.5s → N̂≈57 (偏差14%)
        "think_time":  (3.0, 8.0),
        "method":      "POST",
        "url":         f"{BASE_URL}/api/predict/realtime",
        "body_fn":     lambda: {
            "inputs": [
                round(random.uniform(180, 260), 1),
                round(random.uniform(80,  130), 1),
                round(random.uniform(3.0,  8.0), 2),
                round(random.uniform(1.5,  4.0), 2),
            ],
            "model_type": "DNN",
        },
        "note":        "GPU DNN推理(μ=280ms) + Celery队列等待(μ=2.9s)",
    },
}

# ── 结果类 ────────────────────────────────────────────────────────────────────
@dataclass
class SceneResult:
    name:          str
    concurrency:   int
    note:          str = ""
    durations:     List[float] = field(default_factory=list)
    success_count: int = 0
    error_count:   int = 0
    start_time:    float = 0.0
    end_time:      float = 0.0

    @property
    def total(self):        return self.success_count + self.error_count
    @property
    def avg_ms(self):       return statistics.mean(self.durations)   if self.durations else 0
    @property
    def p50_ms(self):       return statistics.median(self.durations) if self.durations else 0
    @property
    def p99_ms(self):
        if not self.durations: return 0
        s = sorted(self.durations)
        return s[min(int(len(s) * 0.99), len(s) - 1)]
    @property
    def throughput(self):
        e = self.end_time - self.start_time
        return round(self.success_count / e, 1) if e > 0 else 0
    @property
    def success_rate(self):
        return round(self.success_count / self.total * 100, 2) if self.total > 0 else 0
    @property
    def littles_n_hat(self):
        """N̂ = λ × (W + Z̄),  Z̄ = (3+8)/2 = 5.5s"""
        return round(self.throughput * (self.avg_ms / 1000 + 5.5), 1)


# ── 虚拟用户循环 ──────────────────────────────────────────────────────────────
def _worker(scene: dict, result: SceneResult, stop: threading.Event):
    sess = requests.Session()
    lo, hi = scene["think_time"]
    body_fn = scene.get("body_fn")
    static  = scene.get("body")
    params  = scene.get("params", {})

    while not stop.is_set():
        body = body_fn() if body_fn else static
        t0   = time.perf_counter()
        try:
            resp = (sess.post(scene["url"], json=body, timeout=30)
                    if scene["method"] == "POST"
                    else sess.get(scene["url"], params=params, timeout=30))
            ms = (time.perf_counter() - t0) * 1000
            if resp.status_code < 500:
                result.durations.append(ms)
                result.success_count += 1
            else:
                result.error_count += 1
        except Exception:
            result.error_count += 1
        if not stop.is_set():
            time.sleep(random.uniform(lo, hi))


# ── 单场景运行 ────────────────────────────────────────────────────────────────
RAMP_UP_SEC = 30   # 爬坡时长：30s 均匀拉起，避免冷启动浪涌（--full 模式）
RAMP_UP_QUICK = 15 # 快速冒烟模式爬坡时长

def run_scene(key: str, duration: int, ramp_sec: int = RAMP_UP_SEC) -> SceneResult:
    """
    duration = 稳定采集时长（不含爬坡）
    总耗时   = RAMP_UP_SEC + duration
    """
    scene  = SCENES[key]
    n_vu   = scene["concurrency"]
    result = SceneResult(name=scene["name"], concurrency=n_vu,
                         note=scene.get("note", ""))
    stop   = threading.Event()

    total_sec = ramp_sec + duration
    print(f"\n{'═'*64}")
    print(f"  场景 : {scene['name']}")
    print(f"  并发 : {n_vu} VU   爬坡: {ramp_sec}s   稳定采集: {duration}s")
    print(f"  接口 : {scene['method']} {scene['url']}")
    print(f"  说明 : {scene.get('note','')}")
    print(f"{'═'*64}")

    interval = ramp_sec / n_vu
    interval = RAMP_UP_SEC / n_vu   # 每个 VU 间隔（秒）
    print(f"  [爬坡中] 每 {interval*1000:.0f}ms 启动 1 VU，共 {RAMP_UP_SEC}s ...")
    threads = []
    ramp_start = time.time()
    for i in range(n_vu):
        t = threading.Thread(target=_worker, args=(scene, result, stop), daemon=True)
        t.start()
        threads.append(t)
        # 均匀间隔（最后一个 VU 不需要再等）
        if i < n_vu - 1:
            time.sleep(interval)
    print(f"  [爬坡完成] 全部 {n_vu} VU 已就绪，开始稳定采集 {duration}s ...")

    # ── 稳定采集阶段：重置计数，只统计这段数据 ──────────────────────────────
    result.durations     = []
    result.success_count = 0
    result.error_count   = 0
    result.start_time    = time.time()

    for i in range(duration):
        time.sleep(1)
        elapsed = time.time() - result.start_time
        done    = result.total
        tput    = round(result.success_count / elapsed, 1) if elapsed > 0 else 0.0
        filled  = int(32 * i / duration)
        bar     = "█" * filled + "░" * (32 - filled)
        print(f"\r  [{bar}] {i+1:3d}s  完成:{done:5d}  "
              f"均值:{result.avg_ms:6.0f}ms  "
              f"吞吐:{tput:5.1f}r/s  "
              f"成功:{result.success_rate:.1f}%",
              end="", flush=True)

    stop.set()
    result.end_time = time.time()
    for t in threads:
        t.join(timeout=5)
    print()
    return result


# ── 汇总打印 ──────────────────────────────────────────────────────────────────
def print_summary(results: List[SceneResult], db: str):
    W = 84
    sep_top = "┌" + "─"*24 + "┬" + "─"*6 + "┬" + "─"*9 + "┬" + "─"*9 + "┬" + "─"*9 + "┬" + "─"*9 + "┬" + "─"*9 + "┬" + "─"*5 + "┐"
    sep_mid = "├" + "─"*24 + "┼" + "─"*6 + "┼" + "─"*9 + "┼" + "─"*9 + "┼" + "─"*9 + "┼" + "─"*9 + "┼" + "─"*9 + "┼" + "─"*5 + "┤"
    sep_bot = "└" + "─"*24 + "┴" + "─"*6 + "┴" + "─"*9 + "┴" + "─"*9 + "┴" + "─"*9 + "┴" + "─"*9 + "┴" + "─"*9 + "┴" + "─"*5 + "┘"
    hdr = f"  平台压测结果汇总  DB={db.upper()}"
    print(f"\n\n{'='*84}")
    print(f"{hdr:^84}")
    print("="*84)
    print(sep_top)
    print(f"│{'接口':<24}│{'并发':^6}│{'均值ms':^9}│{'P50ms':^9}│{'P99ms':^9}│{'吞吐r/s':^9}│{'成功率%':^9}│{'N̂':^5}│")
    print(sep_mid)
    for r in results:
        print(f"│{r.name:<24}│{r.concurrency:^6}│{r.avg_ms:^9.0f}│{r.p50_ms:^9.0f}│{r.p99_ms:^9.0f}│{r.throughput:^9.1f}│{r.success_rate:^9.2f}│{r.littles_n_hat:^5.0f}│")
    print(sep_bot)

    print("\n  ── 论文表 6-8 格式（可直接复制）──")
    print(f"{'接口':<28}  {'并发':>5}  {'均值(ms)':>9}  {'P99(ms)':>8}  {'吞吐量(req/s)':>10}  {'成功率(%)':>9}")
    print("  " + "-"*75)
    for r in results:
        print(f"{r.name:<28}  {r.concurrency:>5}  {r.avg_ms:>9.0f}  {r.p99_ms:>8.0f}  {r.throughput:>10.1f}  {r.success_rate:>9.2f}")

    print("\n  ── Little's Law 验证 (N̂ = λ·(W+Z̄), Z̄=5.5s) ──")
    for r in results:
        err = abs(r.concurrency - r.littles_n_hat) / r.concurrency * 100
        ok  = "✓" if err < 20 else "△"
        print(f"  {r.name:<28}  实际N={r.concurrency:3d}  N̂={r.littles_n_hat:5.1f}  偏差={err:.1f}%  {ok}")


# ── 入口 ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full",  action="store_true", help="完整模式 120s/场景")
    ap.add_argument("--scene", choices=list(SCENES.keys()), help="只测单个场景")
    args = ap.parse_args()
    duration = 240 if args.full else 30          # 稳定采集时长
    ramp     = RAMP_UP_SEC if args.full else RAMP_UP_QUICK
    n_scenes = 1 if args.scene else len(SCENES)
    total_min = round(n_scenes * (ramp + duration) / 60, 1)

    print("\n" + "="*64)
    print("  平台核心接口压力测试  (第六章 表6-8 复现)")
    print(f"  模式  : {'完整 4min/场景 (爬坡30s+采集240s)' if args.full else '快速 冒烟 (爬坡15s+采集30s)'}")
    print(f"  爬坡  : {ramp}s/场景（均匀拉起，避免冷启动浪涌）")
    print(f"  预计  : 约 {total_min} 分钟")
    print("="*64)

    # 后端检查
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"\n  ✓ 后端在线: {r.text.strip()[:60]}")
    except Exception as e:
        print(f"\n  ✗ 后端离线: {e}\n    请先运行: python server.py")
        sys.exit(1)

    # 数据库后端确认
    db = "unknown"
    try:
        info = requests.get(f"{BASE_URL}/api/user/db_mode", timeout=5).json()
        db   = info.get("db_mode", "unknown")
        icon = "✓" if db == "mysql" else "⚠"
        tip  = "Docker dx_platform_db @ 127.0.0.1:13306" if db == "mysql" else "SQLite（结果仅供参考）"
        print(f"  {icon} 数据库后端: {db.upper()} — {tip}")
    except Exception:
        pass

    scenes = [args.scene] if args.scene else list(SCENES.keys())
    results = []
    for key in scenes:
        r = run_scene(key, duration, ramp_sec=ramp)
        results.append(r)
        print(f"  ✓ {r.name}  总:{r.total}  均值:{r.avg_ms:.0f}ms  "
              f"P99:{r.p99_ms:.0f}ms  吞吐:{r.throughput}r/s  成功率:{r.success_rate}%")

    print_summary(results, db)


if __name__ == "__main__":
    main()












