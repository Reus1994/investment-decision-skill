#!/usr/bin/env python3
"""
信号引擎历史回测器 — 验证 investment-decision 技术信号的有效性.
复用 technical_engine 的确定性逻辑, 在历史每根 K 线上触发信号并统计未来收益.

用法:
    python backtest.py <data_dir> [--forward 5,10,20] [--cooldown 5] [--json out.json]
    data_dir 下每个 *.json: 一支股票的 K 线数组 [["日期",开,收,高,低,量], ...]

统计口径:
    - 信号在当日收盘价触发; forward 收益 = 未来 D 日收盘/信号日收盘 - 1
    - 命中率: BUY 信号未来收益>0 的比例 / SELL 信号未来收益<0 的比例
    - 盈亏比: 正收益均值 / |负收益均值| (仅二者都存在时)
    - 基准: 任意交易日收盘买入的未来 D 日收益均值 (随机买入对照)
    - cooldown: 同一股票同一(类型,策略)信号 N 日内只取首个, 模拟实际冷却
"""
from __future__ import annotations

import glob
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from technical_engine import LOOKBACK, build_bars, evaluate_at, risk_at  # noqa: E402


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _med(xs):
    return statistics.median(xs) if xs else 0.0


def run_stock(bars, forwards, cooldown):
    n = len(bars)
    closes = [b["close"] for b in bars]
    samples = {"BUY": [], "SELL": []}
    baseline = {d: [] for d in forwards}
    last_signal = {}  # (type, strategy) -> index
    for i in range(LOOKBACK + 1, n):
        for d in forwards:
            if i + d < n:
                baseline[d].append((closes[i + d] / closes[i] - 1) * 100)
        try:
            signals, _ = evaluate_at(bars, i)
            risk = risk_at(bars, i)
        except Exception:
            continue
        if not signals:
            continue
        for s in signals:
            key = (s["type"], s["strategy"])
            if cooldown and last_signal.get(key) is not None and i - last_signal[key] < cooldown:
                continue
            last_signal[key] = i
            fwd = {}
            for d in forwards:
                if i + d < n:
                    fwd[d] = (closes[i + d] / closes[i] - 1) * 100
            samples[s["type"]].append({
                "strategy": s["strategy"], "date": bars[i]["time"],
                "close": closes[i], "fwd": fwd,
                "risk": risk["score"], "level": risk["level"],
            })
    return samples, baseline


def strategy_stats(samples_by_type, forwards):
    out = {}
    for typ in ("BUY", "SELL"):
        strategies = sorted({s["strategy"] for s in samples_by_type[typ]})
        out[typ] = {}
        for strat in strategies:
            ss = [s for s in samples_by_type[typ] if s["strategy"] == strat]
            row = {"n": len(ss)}
            for d in forwards:
                fwds = [s["fwd"][d] for s in ss if d in s["fwd"]]
                if not fwds:
                    continue
                hit = sum(1 for x in fwds if (x > 0) == (typ == "BUY"))
                gains = [x for x in fwds if x > 0]
                losses = [x for x in fwds if x <= 0]
                pl = None
                if gains and losses and _mean(losses) != 0:
                    pl = _mean(gains) / abs(_mean(losses))
                row[f"fwd{d}"] = {
                    "hit_rate": round(hit / len(fwds), 3),
                    "avg": round(_mean(fwds), 3),
                    "med": round(_med(fwds), 3),
                    "profit_loss": round(pl, 2) if pl is not None else None,
                }
            out[typ][strat] = row
    return out


def risk_buckets(samples_by_type, forwards):
    rows = {}
    d = forwards[len(forwards) // 2]
    for level in ("LOW", "MEDIUM", "HIGH"):
        ss = [s for s in samples_by_type["BUY"] if s["level"] == level]
        fwds = [s["fwd"][d] for s in ss if d in s["fwd"]]
        if not fwds:
            rows[level] = {"n": 0}
            continue
        rows[level] = {
            "n": len(ss),
            "avg_fwd%d" % d: round(_mean(fwds), 3),
            "hit_rate": round(sum(1 for x in fwds if x > 0) / len(fwds), 3),
        }
    return rows


def main():
    args = [a for a in sys.argv[1:]]
    data_dir = None
    forwards = [5, 10, 20]
    cooldown = 5
    json_out = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--forward" and i + 1 < len(args):
            forwards = [int(x) for x in args[i + 1].split(",") if x.strip().isdigit()]
            i += 2
        elif a == "--cooldown" and i + 1 < len(args):
            cooldown = int(args[i + 1]); i += 2
        elif a == "--json" and i + 1 < len(args):
            json_out = args[i + 1]; i += 2
        else:
            data_dir = a; i += 1

    if not data_dir:
        print("用法: backtest.py <data_dir> [--forward 5,10,20] [--cooldown 5] [--json out.json]")
        sys.exit(2)

    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    if not files:
        print(f"no json files in {data_dir}")
        sys.exit(1)

    agg = {"BUY": [], "SELL": []}
    baseline = {d: [] for d in forwards}
    stocks_done, min_date, max_date = 0, None, None
    for fp in files:
        try:
            with open(fp, encoding="utf-8") as f:
                rows = json.load(f)
        except Exception as e:
            print(f"skip {os.path.basename(fp)}: {e}")
            continue
        bars = build_bars(rows)
        if len(bars) < 40:
            continue
        samples, bl = run_stock(bars, forwards, cooldown)
        agg["BUY"].extend(samples["BUY"])
        agg["SELL"].extend(samples["SELL"])
        for d in forwards:
            baseline[d].extend(bl[d])
        stocks_done += 1
        if min_date is None or bars[0]["time"] < min_date:
            min_date = bars[0]["time"]
        if max_date is None or bars[-1]["time"] > max_date:
            max_date = bars[-1]["time"]

    stats = strategy_stats(agg, forwards)
    buckets = risk_buckets(agg, forwards)

    print("=" * 72)
    print(f"回测标的: {stocks_done} 只股票 | 样本期: {min_date} ~ {max_date} | forward={forwards}日 | cooldown={cooldown}日")
    print(f"信号总数: BUY={len(agg['BUY'])}, SELL={len(agg['SELL'])}")
    print("-" * 72)
    print("随机买入基准 (任意交易日收盘买入的未来D日收益均值):")
    for d in forwards:
        b = baseline[d]
        print(f"  基准 fwd{d}: avg={_mean(b):+.2f}% med={_med(b):+.2f}% n={len(b)}")
    print("-" * 72)

    for typ in ("BUY", "SELL"):
        print(f"【{typ} 信号 · 各策略】")
        print(f"{'策略':<10}{'n':>5} {'fwd5命中':>8} {'fwd5均值':>9} {'fwd10命中':>9} {'fwd10均值':>10} {'fwd20命中':>9} {'fwd20均值':>10} {'盈亏比10':>8}")
        for strat, row in stats[typ].items():
            cells = []
            for d in forwards:
                f = row.get(f"fwd{d}")
                if f:
                    cells.append(f"{f['hit_rate']*100:5.0f}%")
                    cells.append(f"{f['avg']:+6.2f}%")
                else:
                    cells.append("  -")
                    cells.append("   -")
            pl = row.get("fwd10", {}).get("profit_loss")
            print(f"{strat:<10}{row['n']:>5} {cells[0]:>8} {cells[1]:>9} {cells[2]:>9} {cells[3]:>10} {cells[4]:>9} {cells[5]:>10} {str(pl) if pl is not None else '-':>8}")
        print("-" * 72)

    print("【BUY 信号 · 按风险分层】(fwd10 表现):")
    for level, row in buckets.items():
        print(f"  {level:<8} n={row.get('n',0):>4}  avg={row.get('avg_fwd10','-'):>8}  hit={row.get('hit_rate','-'):>6}")
    print("=" * 72)

    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump({
                "stocks": stocks_done, "min_date": min_date, "max_date": max_date,
                "forwards": forwards, "cooldown": cooldown,
                "signal_counts": {"BUY": len(agg["BUY"]), "SELL": len(agg["SELL"])},
                "baseline": {str(d): {"avg": round(_mean(b), 3), "med": round(_med(b), 3)}
                             for d, b in baseline.items()},
                "strategies": stats, "risk_buckets": buckets,
            }, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
