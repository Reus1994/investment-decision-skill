# -*- coding: utf-8 -*-
"""
双视角体检报告渲染器（暗色 HTML，单文件零依赖输出）

用法:
    python scripts/render_report.py input.json --outdir <目录>      # 按命名规范自动命名（推荐）
    python scripts/render_report.py input.json -o 自定义路径.html    # 手动指定文件名
    python scripts/render_report.py input.json --tech tech.json --outdir <目录>

文件命名规范（省略 -o 时自动生成）:
    {范围}_{类型}_{YYYY-MM-DD}.html
    范围 scope = 分组名/标的名/主题（持仓个股 / 持仓ETF / 关注池 / 半导体主线 / 药明康德）
    类型 kind  = 组合体检 | 个股深度 | 基本面评估 | 技术扫描 | 信号回测 | 定期跟踪
                 （默认双视角方法不写进文件名；仅基本面/仅技术面时才在 kind 标明）
    多只默认 kind=组合体检，单只默认 kind=个股深度；同日重跑自动追加 -v2/-v3

input.json 结构:
{
  "scope":    "持仓个股",                        # 命名用: 分析范围; 缺省回退 title
  "kind":     "组合体检",                        # 命名用: 报告类型; 缺省按标的数量推断
  "date":     "2026-08-08",                     # 命名用: 数据日期; 缺省今天
  "title":    "持仓个股 · 组合体检报告",          # 必填, 页面大标题
  "subtitle": "分析对象 … | 数据截至 … | 框架 …",  # 可选
  "callout":  "<b>本轮关键变化：</b>…",           # 可选, 允许 HTML, 显示为顶部红框
  "portfolio": ["<b>1. …</b> 段落一", "段落二"],  # 可选, 组合层面结论
  "footer":   "数据来源 … 非投资建议",            # 可选
  "items": [
    {
      "code":"hk00700", "name":"腾讯控股",
      "cls":"进攻",                  # 进攻/防守/替补/放弃 (守拙君分类); 缺省 "—"
      "px":620.5, "cur":"HKD",
      "pe":"22.1","pb":"4.2","div":"0.9%","roe":"23%","g":"12%","peg":"1.8",
      "hi52":700, "lo52":380,        # 给 hi52/lo52 自动算分位; 或直接给 "pos52": 88
      "valst":"合理",                # 估值状态: 低估/合理/高估
      "fv":"买入",                   # 基本面判定: 买入/观望/放弃/观望·放弃
      "blurb":"五步法结论文案…",      # 卡片正文
      "quote":"「胜于易胜者」",        # 守拙君金句
      "tech":{                       # 技术面; 也可用 --tech 外部文件按 code 注入
        "state":"右侧强趋势",         # 右侧强趋势/中性/走弱; 缺省由 ma5/ma20 推断
        "pos20":0.85,                # 0~1 或 0~100 均可
        "risk_level":"LOW","risk_score":10,
        "ma5":610.2,"ma20":588.4,"ma55":560.1,
        "sig":[["缩量回调","BUY","RIGHT"]],
        "advice":["趋势内回调 → 可低吸"]
      }
    }
  ]
}

tech.json（可选，technical_engine 批量输出）: { "hk00700": {…同上 tech 字段…}, … }
"""
import argparse
import datetime
import html
import json
import os
import re
import sys

TPL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "report.html")

CLSB = {"进攻": "b-atk", "防守": "b-def", "替补": "b-alt", "放弃": "b-drop"}
STB = {"右侧强趋势": "b-atk", "中性": "b-watch", "走弱": "b-def"}
RSKB = {"LOW": "b-def", "MEDIUM": "b-watch", "HIGH": "b-no"}
COLST = {"右侧强趋势": "#ef4444", "中性": "#eab308", "走弱": "#2ea043"}
ORDER = {"右侧强趋势": 0, "中性": 1, "走弱": 2}


def esc(v):
    return html.escape(str(v), quote=False)


def fv_badge(fv):
    if "放弃" in fv:
        return "b-no"
    if fv.startswith("买入"):
        return "b-buy"
    return "b-watch"


def cross_verdict(fv, state, pos52):
    """Step5 双视角交叉：基本面判定 × 技术趋势状态 → 综合结论。"""
    fv = (fv or "观望").strip()
    if fv == "放弃" or fv.startswith("放弃"):
        return "放弃·不参与", "b-no"
    if fv.startswith("观望/放弃") or fv.startswith("观望·放弃"):
        return ("观望/放弃·不追高" if state == "右侧强趋势" else "观望/放弃"), "b-no"
    if fv.startswith("买入"):
        if state == "右侧强趋势":
            if pos52 is not None and pos52 >= 70:
                return "持有·勿追高", "b-watch"
            return "买入·右侧共振", "b-buy"
        if state == "中性":
            return "买入·分批建仓", "b-buy"
        return "买入·等站回MA20", "b-wait"
    # 观望 / 持有 等
    if state == "右侧强趋势":
        return "持有不加·勿追高", "b-watch"
    if state == "中性":
        return "观望", "b-watch"
    return "观望·避险", "b-wait"


def infer_state(tech):
    st = tech.get("state")
    if st in ORDER:
        return st
    last, ma5, ma20 = tech.get("last"), tech.get("ma5"), tech.get("ma20")
    if last and ma5 and ma20:
        if last > ma5 > ma20:
            return "右侧强趋势"
        return "中性" if last > ma20 else "走弱"
    return "中性"


def norm_pct(v):
    """0~1 或 0~100 统一成 0~100。"""
    if v is None:
        return None
    v = float(v)
    return v * 100 if v <= 1.0 else v


def build_rows(cfg, tech_ext):
    rows = []
    for it in cfg["items"]:
        code = it.get("code", "")
        tech = dict(it.get("tech") or {})
        if code in tech_ext:
            merged = dict(tech_ext[code])
            merged.update(tech)  # item 内 tech 优先
            tech = merged

        pos52 = it.get("pos52")
        if pos52 is None and it.get("hi52") and it.get("lo52") is not None:
            hi, lo, px = float(it["hi52"]), float(it["lo52"]), float(it.get("px") or 0)
            pos52 = (px - lo) / (hi - lo) * 100 if hi > lo else None
        pos52 = norm_pct(pos52)

        state = infer_state(tech)
        fv = it.get("fv", "观望")
        verdict, vc = cross_verdict(fv, state, pos52)

        sig = tech.get("sig") or tech.get("signals") or []
        norm_sig = []
        for s in sig:
            if isinstance(s, dict):
                norm_sig.append((s.get("strategy", "?"), s.get("type", "?"), s.get("side", "?")))
            elif isinstance(s, (list, tuple)) and len(s) >= 3:
                norm_sig.append((s[0], s[1], s[2]))

        rows.append({
            "code": code, "name": it.get("name", code),
            "cls": it.get("cls", "—"),
            "pe": it.get("pe", "—"), "pb": it.get("pb", "—"), "div": it.get("div", "—"),
            "roe": it.get("roe", "—"), "g": it.get("g", "—"), "peg": it.get("peg", "—"),
            "px": it.get("px", "—"), "cur": it.get("cur", ""),
            "pos52": pos52, "valst": it.get("valst", "—"), "fv": fv,
            "state": state, "pos20": norm_pct(tech.get("pos20")),
            "risk": tech.get("risk_level", "—"), "rs": tech.get("risk_score", "—"),
            "ma5": tech.get("ma5", "—"), "ma20": tech.get("ma20", "—"), "ma55": tech.get("ma55", "—"),
            "sig": norm_sig, "advice": tech.get("advice") or [],
            "verdict": verdict, "vc": vc,
            "blurb": it.get("blurb", ""), "quote": it.get("quote", ""),
        })
    return rows


def svg_bars(rows, key, colorer, labeler, axis, sorter):
    """通用横向条形图。"""
    srt = sorted(rows, key=sorter)
    h = 30 + len(srt) * 24
    out = [f'<svg width="780" height="{h}" viewBox="0 0 780 {h}" xmlns="http://www.w3.org/2000/svg" '
           f'font-family="-apple-system,sans-serif">',
           f'<line x1="150" y1="20" x2="150" y2="{h - 12}" stroke="#30363d"/>']
    for xx, lab in axis:
        if xx > 150:
            out.append(f'<line x1="{xx}" y1="20" x2="{xx}" y2="{h - 12}" stroke="#30363d" stroke-dasharray="3 3"/>')
        out.append(f'<text x="{xx - 4}" y="14" fill="#8b949e" font-size="11" text-anchor="end">{lab}</text>')
    for i, r in enumerate(srt):
        y = 26 + i * 24
        val = r[key] if r[key] is not None else 0
        w = max(3, val / 100 * 560)
        col, lc = colorer(r)
        out.append(f'<text x="144" y="{y + 10}" fill="{lc}" font-size="12" text-anchor="end">{esc(r["name"])}</text>'
                   f'<rect x="150" y="{y}" width="{w:.0f}" height="18" rx="3" fill="{col}" opacity="0.9"/>'
                   f'<text x="{150 + w + 6:.0f}" y="{y + 13}" fill="#8b949e" font-size="11">{labeler(r)}</text>')
    out.append("</svg>")
    return "\n      ".join(out)


def color52(r):
    p = r["pos52"]
    if p is None:
        return "#8b949e", "#e6edf3"
    col = "#3b82f6" if p < 30 else ("#eab308" if p <= 70 else "#ef4444")
    return col, ("#ff7b72" if p > 70 else "#e6edf3")


def pos52_cell(p):
    if p is None:
        return "—", "#e6edf3"
    return f"{p:.0f}%", ("#ff7b72" if p > 70 else ("#56d364" if p < 30 else "#e6edf3"))


def render(cfg, tech_ext):
    rows = build_rows(cfg, tech_ext)

    svg52 = svg_bars(rows, "pos52", color52,
                     lambda r: "—" if r["pos52"] is None else f'{r["pos52"]:.0f}%',
                     ((150, "0%"), (430, "50%"), (710, "100%")),
                     lambda r: (r["pos52"] is None, r["pos52"] or 0))
    svgtech = svg_bars(rows, "pos20", lambda r: (COLST.get(r["state"], "#8b949e"), "#e6edf3"),
                       lambda r: f'{(r["pos20"] or 0):.0f}% · {r["state"]} · 风险{r["rs"]}',
                       ((150, "20日最低"), (430, "中位"), (710, "20日最高")),
                       lambda r: (ORDER.get(r["state"], 9), -(r["pos20"] or 0)))

    # KPI：按综合结论分布 + 趋势分布
    kpi_defs = [("买入·右侧共振", "#ff7b72"), ("买入·分批建仓", "#ff7b72"), ("买入·等站回MA20", "#79b8ff"),
                ("持有不加·勿追高", "#eab308"), ("持有·勿追高", "#eab308"), ("观望", "#eab308"),
                ("观望·避险", "#eab308"), ("观望/放弃", "#8b949e"), ("观望/放弃·不追高", "#8b949e"),
                ("放弃·不参与", "#8b949e")]
    kpis = []
    for label, col in kpi_defs:
        n = sum(1 for r in rows if r["verdict"] == label)
        if n:
            kpis.append(f'<div class="kpi"><div class="n" style="color:{col}">{n}</div>'
                        f'<div class="l">{esc(label)}</div></div>')
    for label, col, cnt in (("右侧强趋势", "#ff7b72", sum(1 for r in rows if r["state"] == "右侧强趋势")),
                            ("技术走弱", "#56d364", sum(1 for r in rows if r["state"] == "走弱"))):
        kpis.append(f'<div class="kpi"><div class="n" style="color:{col}">{cnt}</div>'
                    f'<div class="l">{esc(label)}</div></div>')

    # 表格
    trs = []
    for r in rows:
        sigtxt = "、".join(f'{esc(a)}<span style="color:#8b949e">({esc(c)})</span>' for a, b, c in r["sig"]) \
                 or '<span style="color:#8b949e">—</span>'
        ptxt, pcol = pos52_cell(r["pos52"])
        trs.append(
            f'<tr><td><b>{esc(r["name"])}</b><div style="color:#8b949e;font-size:11px">{esc(r["code"])}</div></td>'
            f'<td><span class="badge {CLSB.get(r["cls"], "b-drop")}">{esc(r["cls"])}</span></td>'
            f'<td>{esc(r["pe"])}</td><td>{esc(r["pb"])}</td><td>{esc(r["div"])}</td>'
            f'<td>{esc(r["roe"])}</td><td>{esc(r["peg"])}</td>'
            f'<td style="color:{pcol}">{ptxt}</td>'
            f'<td>{esc(r["valst"])}</td>'
            f'<td><span class="badge {fv_badge(r["fv"])}">{esc(r["fv"])}</span></td>'
            f'<td><span class="badge {STB.get(r["state"], "b-drop")}">{esc(r["state"])}</span></td>'
            f'<td><span class="badge {RSKB.get(r["risk"], "b-drop")}">{esc(r["risk"])} {esc(r["rs"])}</span></td>'
            f'<td style="font-size:11.5px">{sigtxt}</td>'
            f'<td><span class="badge {r["vc"]}">{esc(r["verdict"])}</span></td></tr>')

    # 卡片
    cards = []
    for r in rows:
        sigtxt = "、".join(f"{esc(a)}·{esc(b)}/{esc(c)}" for a, b, c in r["sig"]) or "无触发信号"
        adv = "；".join(esc(a) for a in r["advice"]) or "无特别建议"
        ptxt, pcol = pos52_cell(r["pos52"])
        quote = f'<div class="quote">{esc(r["quote"])}</div>' if r["quote"] else ""
        blurb = f'<div class="blurb">{r["blurb"]}</div>' if r["blurb"] else ""
        cards.append(f'''<div class="card">
      <h3>{esc(r["name"])} <span class="badge {CLSB.get(r["cls"], "b-drop")}">{esc(r["cls"])}</span></h3>
      <div><span class="badge {r["vc"]}">{esc(r["verdict"])}</span> <span class="badge {STB.get(r["state"], "b-drop")}">{esc(r["state"])}</span> <span class="badge {RSKB.get(r["risk"], "b-drop")}">风险{esc(r["rs"])}</span></div>
      <div class="grid"><span>现价</span><b>{esc(r["px"])} {esc(r["cur"])}</b><span>PE/PB</span><b>{esc(r["pe"])} / {esc(r["pb"])}</b>
        <span>ROE</span><b>{esc(r["roe"])}</b><span>增速g</span><b>{esc(r["g"])}</b>
        <span>52w分位</span><b style="color:{pcol}">{ptxt}</b><span>股息率</span><b>{esc(r["div"])}</b></div>
      <div class="tech">
        <div class="tech-t">技术面（引擎输出 · 多轮回测校准）</div>
        <div class="tech-r"><span>均线</span><b>MA5 {esc(r["ma5"])} / MA20 {esc(r["ma20"])} / MA55 {esc(r["ma55"])}</b></div>
        <div class="tech-r"><span>20日位置</span><b>{"—" if r["pos20"] is None else f'{r["pos20"]:.0f}%'}</b></div>
        <div class="tech-r"><span>信号</span><b>{sigtxt}</b></div>
        <div class="adv">→ {adv}</div>
      </div>
      {blurb}
      {quote}
    </div>''')

    callout = f'<div class="callout">{cfg["callout"]}</div>' if cfg.get("callout") else ""
    portfolio = ""
    if cfg.get("portfolio"):
        body = "<br><br>".join(cfg["portfolio"])
        portfolio = ('<div class="sec-t">五、组合层面结论与操作纪律</div>\n'
                     f'  <div class="card" style="background:#11161f"><div class="blurb">{body}</div></div>')

    with open(TPL_PATH, encoding="utf-8") as f:
        tpl = f.read()
    out = (tpl.replace("{{TITLE}}", esc(cfg.get("title", "双视角体检报告")))
              .replace("{{SUBTITLE}}", cfg.get("subtitle", ""))
              .replace("{{CALLOUT}}", callout)
              .replace("{{KPIS}}", "\n    ".join(kpis))
              .replace("{{SVG52}}", svg52)
              .replace("{{SVGTECH}}", svgtech)
              .replace("{{TABLE}}", "\n      ".join(trs))
              .replace("{{CARDS}}", "\n\n    ".join(cards))
              .replace("{{PORTFOLIO}}", portfolio)
              .replace("{{FOOTER}}", cfg.get("footer", "本报告为框架化研究，非投资建议。")))
    return out, rows


# ---------------- 文件命名规范 ----------------
# 统一格式: {范围}_{类型}_{YYYY-MM-DD}.html
#   范围 scope : 分组名/标的名/主题 —— 持仓个股 / 持仓ETF / 关注池 / 半导体主线 / 药明康德
#   类型 kind  : 组合体检(多只,基本面+技术面) / 个股深度(单只) / 基本面评估(仅基本面)
#                / 技术扫描(仅技术面) / 信号回测 / 定期跟踪
#   默认方法即"双视角"，不写进文件名；只有偏离默认（仅基本面/仅技术面）才在 kind 中标明。
# 同日重跑自动追加 -v2/-v3，不覆盖旧文件。
KIND_DEFAULT_MULTI = "组合体检"
KIND_DEFAULT_SINGLE = "个股深度"
_BAD = re.compile(r'[\\/:*?"<>|\s]+')


def build_filename(cfg, n_items, ext="html"):
    scope = str(cfg.get("scope") or cfg.get("title") or "标的").strip()
    kind = str(cfg.get("kind") or (KIND_DEFAULT_SINGLE if n_items == 1 else KIND_DEFAULT_MULTI)).strip()
    date = str(cfg.get("date") or datetime.date.today().isoformat()).strip()
    return f"{_BAD.sub('_', scope)}_{_BAD.sub('_', kind)}_{date}.{ext}"


def dedupe_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 2
    while os.path.exists(f"{base}-v{i}{ext}"):
        i += 1
    return f"{base}-v{i}{ext}"


def main():
    ap = argparse.ArgumentParser(description="渲染双视角体检报告 HTML")
    ap.add_argument("input", help="报告数据 JSON")
    ap.add_argument("-o", "--output", help="输出 HTML 路径；省略时按命名规范自动生成 {范围}_{类型}_{日期}.html")
    ap.add_argument("--outdir", default=".", help="自动命名时的输出目录（默认当前目录）")
    ap.add_argument("--tech", help="technical_engine 批量输出 JSON（按 code 索引），可选")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        cfg = json.load(f)
    if not cfg.get("items"):
        sys.exit("input.json 缺少 items")

    tech_ext = {}
    if args.tech:
        with open(args.tech, encoding="utf-8") as f:
            tech_ext = json.load(f)

    out, rows = render(cfg, tech_ext)

    if args.output:
        target = args.output
    else:
        target = dedupe_path(os.path.join(args.outdir, build_filename(cfg, len(rows))))
    d = os.path.dirname(os.path.abspath(target))
    os.makedirs(d, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(out)
    args.output = target

    print(f"written: {args.output} ({os.path.getsize(args.output)} bytes, {len(rows)} items)")
    dist = {}
    for r in rows:
        dist[r["verdict"]] = dist.get(r["verdict"], 0) + 1
    print("结论分布:", " | ".join(f"{k} {v}" for k, v in sorted(dist.items(), key=lambda x: -x[1])))


if __name__ == "__main__":
    main()
