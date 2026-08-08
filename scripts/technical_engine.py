#!/usr/bin/env python3
"""
技术信号引擎 (standalone, 仅标准库)
从 TradingAssistantPy 移植的确定性计算:
  - trading_signal_service.py   → 10 种量价买卖信号
  - ma_calculator.py            → SMA
  - crossover_detector.py       → 突破/跌破状态 (简化: 末根 vs MA)
  - risk_assessment_service.py  → 0-100 风险评分
  - right_trend_analysis_service.py → 右侧趋势启发式

用法:
    python technical_engine.py kline.json [--price 12.34] [--periods 5,13,30,55]
    cat kline.json | python technical_engine.py --stdin

kline.json: 腾讯/东财公共接口行格式数组
    [["2026-08-07","1308.66","1309.22","1315.28","1301.00","24976"], ...]
    每行: [日期, 开, 收, 高, 低, 量]   (第2=开 第3=收 第4=高 第5=低 第6=量)

输出: 紧凑 JSON { bars, ma, risk, right_trend, latest, signals }
"""
from __future__ import annotations

import json
import math
import sys
from typing import Optional

LOOKBACK = 20          # 量比/价格位置窗口
MIN_BARS = 25          # 信号/风险至少需要 25 根
DEFAULT_PERIODS = [5, 13, 30, 55]

# ---------- 指标 ----------

def sma(values, period):
    if len(values) < period or period <= 0:
        return float("nan")
    return sum(values[-period:]) / period


def ema_series(values, period):
    if not values:
        return []
    k = 2 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(-period, 0):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    ag, al = sum(gains) / period, sum(losses) / period
    if al == 0:
        return 100.0
    return 100 - 100 / (1 + ag / al)


def build_bars(rows):
    bars = []
    for r in rows:
        if not r or len(r) < 6:
            continue
        try:
            bars.append({
                "time": str(r[0]),
                "open": float(r[1]), "close": float(r[2]),
                "high": float(r[3]), "low": float(r[4]),
                "volume": int(float(r[5])),
            })
        except (TypeError, ValueError):
            continue
    return bars


def bar_ctx(bars, i):
    """端口 TradingSignalService._build_context 的上下文变量."""
    bar = bars[i]
    avg_vol = sum(bars[j]["volume"] for j in range(i - LOOKBACK, i)) / LOOKBACK
    vol_ratio = bar["volume"] / avg_vol if avg_vol > 0 else 0.0
    prev_close = bars[i - 1]["close"]
    change_pct = (bar["close"] - prev_close) / prev_close * 100 if prev_close else 0.0
    is_up = bar["close"] >= bar["open"]
    body = abs(bar["close"] - bar["open"])
    rng = bar["high"] - bar["low"]
    body_to_range = body / rng if rng > 0 else 1.0
    min_price = min(bars[j]["low"] for j in range(i - LOOKBACK, i + 1))
    max_price = max(bars[j]["high"] for j in range(i - LOOKBACK, i + 1))
    span = max_price - min_price
    price_position = (bar["close"] - min_price) / span if span > 0 else 0.5
    return {
        "bar": bar, "vol_ratio": vol_ratio, "change_pct": change_pct,
        "is_up": is_up, "body_to_range": body_to_range,
        "price_position": price_position,
    }


# ---------- 量价信号 (任意位置评估) ----------

def evaluate_at(bars, i):
    """评估第 i 根 K 线上的 10 种量价信号, 返回 (signals, ctx)."""
    c = bar_ctx(bars, i)
    vol_ratio = c["vol_ratio"]
    pos = c["price_position"]
    chg = c["change_pct"]
    btr = c["body_to_range"]

    # 近5日价格/量能序列 (与项目一致: k=0 最旧 → k=4 最新)
    n = min(5, i + 1)
    closes5 = [bars[i - n + 1 + k]["close"] for k in range(n)]
    vols5 = [bars[i - n + 1 + k]["volume"] for k in range(n)]
    vol_ratios5 = []
    for k in range(n):
        idx = i - n + 1 + k
        avg = sum(bars[j]["volume"] for j in range(max(0, idx - LOOKBACK), idx)) / max(1, min(LOOKBACK, idx))
        vol_ratios5.append(bars[idx]["volume"] / avg if avg > 0 else 0.0)

    out = []

    # side 标注: LEFT = 左侧反转类(猜底/猜顶, 提前埋伏)  RIGHT = 右侧确认类(趋势内/确认后动手)
    # ---- SELL ----
    if pos >= 0.75 and vol_ratio >= 1.4 and btr < 0.4 and abs(chg) <= 1.5:
        out.append({"type": "SELL", "strategy": "高位放量滞涨", "side": "LEFT",
                    "reason": f"价格接近近期高点({pos*100:.0f}%), 量比{vol_ratio:.1f}, 实体仅占振幅{btr*100:.0f}%, 大资金可能出货"})
    if vol_ratio >= 3.0 and pos >= 0.80:
        out.append({"type": "SELL", "strategy": "天量天价", "side": "LEFT",
                    "reason": f"量比{vol_ratio:.1f}倍(20日均量), 价格在近期高点, 警惕顶部"})
    if vol_ratio >= 2.0 and chg <= -2.0 and not c["is_up"]:
        out.append({"type": "SELL", "strategy": "放量大跌", "side": "RIGHT",
                    "reason": f"跌幅{chg:.1f}%, 量比{vol_ratio:.1f}, 资金大幅流出"})
    if n == 5 and closes5[0] < closes5[4] and vols5[0] > vols5[4] and pos >= 0.6:
        out.append({"type": "SELL", "strategy": "量价背离", "side": "LEFT",
                    "reason": "近5日价格上涨但成交量逐日萎缩, 上涨缺乏量能支撑"})
    # 连续缩量 + 高位横盘 (修正原项目索引, 语义: 量比向最新递减且 <0.8)
    if pos >= 0.6 and n >= 3 and vol_ratios5[-2] < 0.8 and vol_ratios5[-1] < vol_ratios5[-2] \
            and btr <= 0.5 and chg >= -2.0:
        out.append({"type": "SELL", "strategy": "缩量滞涨", "side": "LEFT",
                    "reason": f"连续缩量({vol_ratios5[-2]:.2f}->{vol_ratios5[-1]:.2f})且高位横盘, 上涨动能衰竭"})

    # ---- BUY ----
    if n >= 3 and all(closes5[k] < closes5[k - 1] for k in range(2, min(5, n))) \
            and n == 5 and vols5[2] > vols5[3] > vols5[4] and vol_ratio <= 0.7:
        out.append({"type": "BUY", "strategy": "缩量下跌", "side": "LEFT",
                    "reason": f"连续3日下跌但量能递减(量比{vol_ratio:.1f}), 下跌动能不足"})
    if vol_ratio <= 0.4 and pos <= 0.35:
        out.append({"type": "BUY", "strategy": "地量地价", "side": "LEFT",
                    "reason": f"量比仅{vol_ratio:.2f}(极度萎缩), 价格在低位({pos*100:.0f}%), 抛压枯竭"})
    if vol_ratio >= 1.8 and pos <= 0.4 and chg >= -2.0:
        out.append({"type": "BUY", "strategy": "底部放量", "side": "LEFT",
                    "reason": f"低位放量(量比{vol_ratio:.1f})但未续跌({chg:.1f}%), 资金进场吸筹"})
    if pos >= 0.55 and not c["is_up"] and -3.0 <= chg <= -0.5 and vol_ratio <= 0.7:
        out.append({"type": "BUY", "strategy": "缩量回调", "side": "RIGHT",
                    "reason": f"上升趋势中回调({chg:.1f}%)但缩量(量比{vol_ratio:.1f}), 回调充分"})
    if vol_ratio <= 0.5 and pos <= 0.4 and btr <= 0.45 and abs(chg) <= 1.0:
        out.append({"type": "BUY", "strategy": "缩量止跌", "side": "LEFT",
                    "reason": f"低位缩量(量比{vol_ratio:.1f})且几乎不动, 卖盘枯竭"})

    return out, c


def evaluate_signals(bars):
    """在最后一根 K 线上评估 10 种信号, 返回命中列表."""
    return evaluate_at(bars, len(bars) - 1)[0]


# ---------- 风险评分 (任意位置评估) ----------

def risk_at(bars, i):
    """评估第 i 根 K 线的风险评分 (0-100)."""
    sub = bars[:i + 1]
    closes = [b["close"] for b in sub]
    volumes = [b["volume"] for b in sub]
    latest = sub[-1]
    score, factors = 0, []

    ma5, ma20 = sma(closes, 5), sma(closes, 20)
    if not math.isnan(ma20) and latest["close"] < ma20:
        score += 20
        factors.append("跌破MA20")
    elif not math.isnan(ma5) and latest["close"] < ma5:
        score += 10
        factors.append("跌破MA5")

    r = rsi(closes)
    if r > 75:
        score += 20
        factors.append(f"RSI超买({r:.0f})")
    elif r < 25:
        score -= 10
        factors.append(f"RSI超卖({r:.0f})")

    if len(volumes) >= 20:
        avg = sum(volumes[-20:]) / 20
        if avg > 0 and latest["volume"] > avg * 2:
            score += 15
            factors.append("成交量异常放大")

    if len(closes) >= 2:
        chg = (closes[-1] - closes[-2]) / closes[-2] * 100
        if chg < -3:
            score += 20
            factors.append(f"大跌{chg:.1f}%")
        elif chg < -1:
            score += 10
            factors.append(f"下跌{chg:.1f}%")

    if len(closes) >= 26:
        e12, e26 = ema_series(closes, 12), ema_series(closes, 26)
        if e12 and e26 and (e12[-1] - e26[-1]) < 0:
            score += 15
            factors.append("MACD空头")

    score = max(0, min(100, score))
    level = "HIGH" if score >= 60 else ("MEDIUM" if score >= 30 else "LOW")
    return {"score": score, "level": level, "factors": factors}


def risk_assessment(bars):
    return risk_at(bars, len(bars) - 1)


# ---------- 三分法操作建议 ----------

def build_advice(ma_state, signals, risk):
    """按修正后的"趋势状态三分法"给出操作建议 (2026-08 三轮回测校准).

    右侧强趋势(close>MA5>MA20): 左侧买点=黄金坑, SELL信号反指不卖
    走弱(close<MA20)        : 左侧抄底=接刀, SELL(缩量滞涨/放量大跌)有效→减仓
    中性                    : 弱化使用, 等方向
    """
    right = ma_state.get("right_trend", False)
    below = not ma_state.get("above_ma20", False)
    left_buy = [s for s in signals if s.get("side") == "LEFT" and s["type"] == "BUY"]
    right_buy = [s for s in signals if s.get("side") == "RIGHT" and s["type"] == "BUY"]
    left_sell = [s for s in signals if s.get("side") == "LEFT" and s["type"] == "SELL"]
    right_sell = [s for s in signals if s.get("side") == "RIGHT" and s["type"] == "SELL"]
    high_risk = (risk or {}).get("level") == "HIGH"

    advice = []
    if right:
        if left_buy:
            advice.append("右侧强趋势 + 左侧买点(" + "/".join(s["strategy"] for s in left_buy) +
                          ") → 回调低吸机会（回测高置信）")
        elif right_buy:
            advice.append("右侧强趋势 + 趋势内回调(" + right_buy[0]["strategy"] + ") → 可低吸")
        if left_sell:
            advice.append("强趋势中左侧离场信号(" + "/".join(s["strategy"] for s in left_sell) +
                          ")回测反指，不据此卖出；仅跌破MA20才减仓")
        if not left_buy and not right_buy and not left_sell and not right_sell:
            advice.append("右侧强趋势，暂无信号：持有/等待回调低吸")
    elif below:
        if left_buy:
            advice.append("走弱趋势 + 左侧买点(" + "/".join(s["strategy"] for s in left_buy) +
                          ") → 回测为接刀，不抄底；等重新站回MA20再评估")
        if right_sell:
            advice.append("走弱 + 右侧确认离场(" + "/".join(s["strategy"] for s in right_sell) + ") → 减仓/止盈触发")
        elif left_sell:
            advice.append("走弱 + 左侧离场(" + "/".join(s["strategy"] for s in left_sell) + ") → 弱市有效，减仓/止盈参考")
        if not left_buy and not right_sell and not left_sell:
            advice.append("走弱趋势：不抄底，等站回MA20；破位减仓")
    else:
        advice.append("中性状态：信号弱化，观望等方向（突破MA20再评估买入）")
    if high_risk:
        advice.append("风险分≥60(HIGH)：回避买入（三轮回测5/6口径支持）")
    return advice


# ---------- 主流程 ----------

def main():
    args = [a for a in sys.argv[1:]]
    price_override = None
    periods = DEFAULT_PERIODS
    src = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--price" and i + 1 < len(args):
            price_override = float(args[i + 1]); i += 2
        elif a == "--periods" and i + 1 < len(args):
            periods = [int(x) for x in args[i + 1].split(",") if x.strip().isdigit()] or DEFAULT_PERIODS
            i += 2
        elif a == "--stdin":
            src = sys.stdin.read(); i += 1
        else:
            src = open(a, encoding="utf-8").read(); i += 1

    if src is None:
        print(json.dumps({"error": "用法: technical_engine.py kline.json [--price X] [--periods a,b,c]"}))
        sys.exit(2)

    rows = json.loads(src)
    bars = build_bars(rows)
    if len(bars) < MIN_BARS:
        print(json.dumps({"bars": len(bars), "insufficient": True,
                          "error": f"K线不足{MIN_BARS}根, 无法评估技术信号"}))
        sys.exit(0)

    closes = [b["close"] for b in bars]
    latest = bars[-1]
    ma = {str(p): (round(sma(closes, p), 3) if not math.isnan(sma(closes, p)) else None)
          for p in periods}
    risk = risk_assessment(bars)

    ma5, ma20 = sma(closes, 5), sma(closes, 20)
    right_trend = (not math.isnan(ma5) and not math.isnan(ma20)
                   and latest["close"] > ma5 > ma20)
    above_ma20 = not math.isnan(ma20) and latest["close"] > ma20

    signals, c = evaluate_at(bars, len(bars) - 1)
    ref_price = price_override if price_override and price_override > 0 else latest["close"]

    out = {
        "bars": len(bars),
        "insufficient": False,
        "latest": {"date": latest["time"], "close": latest["close"],
                   "ref_price": ref_price,
                   "vol_ratio": round(c["vol_ratio"], 2),
                   "price_position": round(c["price_position"], 2),
                   "change_pct": round(c["change_pct"], 2)},
        "ma": ma,
        "ma_state": {
            "above_ma20": above_ma20,
            "right_trend": right_trend,   # close > MA5 > MA20
            "right_trend_note": "收盘 > MA5 > MA20" if right_trend else "未满足右侧趋势",
        },
        "risk": risk,
        "signals": signals,
        "signal_counts": {"BUY": sum(1 for s in signals if s["type"] == "BUY"),
                          "SELL": sum(1 for s in signals if s["type"] == "SELL")},
        "advice": build_advice({"right_trend": right_trend, "above_ma20": above_ma20},
                               signals, risk),
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
