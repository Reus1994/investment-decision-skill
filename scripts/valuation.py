#!/usr/bin/env python3
"""
估值计算器 (standalone, 仅标准库)
将基本面五步法(参考 references/fundamental.md)中的确定性公式落地:
  - 类型A(消费/金融/医药): 合理PE = 1/(折现率 - 永续增速), 80%/120% 区间
  - 类型B(资源/周期):   预期收益率 ≈ ROE/PB
  - 类型C(高成长):      PEG = PE / 利润增速
  - 类型D(互联网):      剩余PE = (市值 - 投资价值 - 净现金) / 主营利润
  - 安全边际:          零增长3年收益率 ≈ 1/PE (盈利收益率)

用法:
    python valuation.py params.json
    cat params.json | python valuation.py --stdin

输入 JSON (字段按需填):
{
  "name": "示例", "type": "C",
  "pe": 20.0, "pb": 2.5, "roe": 18.0, "growth": 25.0, "divYield": 3.0,
  "discountRate": 0.10, "perpetualGrowth": 0.05,
  "marketCap": 1000.0, "investValue": 200.0, "netCash": 100.0, "mainProfit": 50.0
}

输出: JSON { type, computed{...}, verdicts{...}, notes[] }
"""
from __future__ import annotations

import json
import sys


def _g(d, k, default=None):
    v = d.get(k, default)
    return default if v is None else v


def main():
    args = [a for a in sys.argv[1:]]
    src = None
    for a in args:
        if a == "--stdin":
            src = sys.stdin.read()
        else:
            src = open(a, encoding="utf-8").read()
    if src is None:
        print(json.dumps({"error": "用法: valuation.py params.json 或 --stdin"}))
        sys.exit(2)

    p = json.loads(src)
    t = _g(p, "type", "C")
    pe = _g(p, "pe", 0) or 0
    pb = _g(p, "pb", 0) or 0
    roe = _g(p, "roe", 0) or 0
    growth = _g(p, "growth", 0) or 0
    div = _g(p, "divYield", 0) or 0
    r = _g(p, "discountRate", 0.10) or 0.10
    g = _g(p, "perpetualGrowth", 0.05) or 0.05
    mc = _g(p, "marketCap", 0) or 0
    inv = _g(p, "investValue", 0) or 0
    cash = _g(p, "netCash", 0) or 0
    mp = _g(p, "mainProfit", 0) or 0

    computed, verdicts, notes = {}, {}, []
    earnings_yield = (1 / pe) if pe > 0 else None

    # 类型A: 合理PE + 防守条件
    if t == "A" and r > g:
        fair = 1 / (r - g)
        low, high = fair * 0.8, fair * 1.2
        computed["reasonablePE"] = round(fair, 1)
        computed["band80_120"] = [round(low, 1), round(high, 1)]
        if pe > 0:
            verdicts["A_fairPE"] = "低估" if pe < low else ("高估" if pe > high else "合理")
        if pe > 0 and pe < 15 and div >= 4:
            notes.append("防守型达标: PE<15 且 股息率>4%")
        elif pe > 0:
            notes.append(f"防守型未达标: PE={pe}, 股息率={div}% (需 PE<15 且 股息率>4%)")

    # 类型B: ROE/PB
    if t == "B" and pb > 0:
        computed["expectedReturnPct"] = round(roe / pb, 1)
        verdicts["B_cheap"] = "低估" if (pb < 1.2 and roe > 15) else "不满足 PB<1.2 且 ROE>15"

    # 类型C: PEG
    if t == "C" and growth > 0 and pe > 0:
        computed["peg"] = round(pe / growth, 2)
        peg = computed["peg"]
        verdicts["C_peg"] = "低估(PEG<1)" if peg < 1 else ("合理持有(1-1.5)" if peg <= 1.5 else "高估(PEG>2)" if peg > 2 else "合理")
    elif t == "C":
        notes.append("缺 growth 或 pe, 无法算 PEG")

    # 类型D: 剩余PE
    if t == "D" and mp > 0:
        remaining = mc - inv - cash
        if remaining > 0:
            computed["remainingMarketCap"] = round(remaining, 1)
            computed["remainingPE"] = round(remaining / mp, 1)
            rpe = computed["remainingPE"]
            verdicts["D_remainingPE"] = "低估(<15)" if rpe < 15 else ("高估(>30)" if rpe > 30 else "合理")
        else:
            notes.append("剩余市值<=0: 股价低于其现金+投资价值, 显著低估")

    # 安全边际: 零增长盈利收益率
    if earnings_yield is not None:
        computed["earningsYieldPct"] = round(earnings_yield * 100, 1)
        verdicts["safety_zeroGrowth"] = (
            f"满足(零增长收益率{earnings_yield*100:.1f}%>8%)" if earnings_yield > 0.08
            else f"不满足(零增长收益率{earnings_yield*100:.1f}%<=8%)")
        notes.append(f"当前盈利收益率(1/PE)={earnings_yield*100:.1f}%; 若未来3年利润零增长, 年化约{earnings_yield*100:.1f}%")

    # 仓位上限参考
    computed["positionCapPct"] = {"进攻": 25, "防守": 15, "替补": "2-8"}

    out = {"name": _g(p, "name", ""), "type": t, "inputs": {
        "pe": pe, "pb": pb, "roe": roe, "growth": growth, "divYield": div},
        "computed": computed, "verdicts": verdicts, "notes": notes}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
