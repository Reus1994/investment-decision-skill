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

================================================================================
单只股票「个股深度」模式（全面公司分析，非组合卡片）
--------------------------------------------------------------------------------
当 input.json 含 "single" 字段时，渲染器走 report_single.html，输出一家公司的
    全面深度分析（基本面为主、技术面辅助）：公司画像 / 定性(5块,含量化证据) / 业务结构 /
近N年核心财务数据(真实报表) / 财务质量体检 / 资本回报与现金创造力(李录核心) /
股东回报 / 估值(含历史分位与价位) / 安全边际 / 技术面(辅助·含具体读数) / 双视角结论。

设计原则：所有定性判断必须配量化证据；财务必须给真实多年数字，不得只写"达标/观察"。

{
  "scope":"腾讯控股", "kind":"个股深度", "date":"2026-08-08",
  "title":"腾讯控股 · 个股深度分析",
  "subtitle":"数据截至 … | 框架：守拙君五步法 + 李录审美",
  "single":{
    "summary":"一句话定位：…",
    "profile":{
      "industry":"互联网/社交游戏", "mktcap":"3.2万亿 HKD",
      "px":520.5, "cur":"HKD", "pe":"22", "pb":"4.2", "roe":"23%", "g":"12%", "peg":"1.8",
      "hi52":620, "lo52":360,            # 自动算 52w 分位
      "cls":"进攻",                       # 守拙君分类
      # —— 以下为「公司画像」丰富字段（可缺省，缺省则折叠，不报错）——
      "desc":"以微信/QQ 社交底座为核心的平台型互联网公司，业务横跨游戏、广告、金融科技与企业服务。",
      "listing":"港交所主板 2004-06 上市", "founded":"1998", "hq":"中国深圳",
      "chairman":"马化腾（董事会主席兼CEO）", "employees":"约10.8万人",
      "ctrl":"MIH(南非报业)为大股东，核心团队持表决权；无单一实控人",
      "core_products":["微信/WeChat","《王者荣耀》等游戏","腾讯视频","腾讯云","微信支付"],
      "position":"社交与游戏双领域国内绝对龙头，广告与金融科技稳居第一梯队",
      "liulu":{"业务质量":5,"管理层":5,"长坡厚雪":5,"价格":3,"能力圈":5,"集中耐心":5}  # 李录六维 1-5
    },
    "qualitative":{                       # 五块定性 + 量化证据
      "business":"商业模式：微信+游戏+广告+金融科技+云，平台型高转换成本",
      "moat":"护城河：社交关系链网络效应 + 游戏IP壁垒 + 支付牌照",
      "moat_type":["网络效应","品牌","转换成本","牌照"],
      "moat_data":[                       # 护城河量化证据（必须给数字）
        {"k":"微信月活 MAU","v":"13.7亿"},
        {"k":"游戏市场份额(国内)","v":"~45%"},
        {"k":"微信支付笔数市占","v":"~40%"}
      ],
      "competition":"竞争格局：社交绝对寡头；游戏与网易双寡头；广告面对字节竞争",
      "comp_data":[                       # 竞争格局量化证据
        {"k":"国内游戏份额-腾讯","v":"~45%"},
        {"k":"国内游戏份额-网易","v":"~18%"},
        {"k":"社交份额","v":">90% 寡头"}
      ],
      "mgmt":"管理层：马化腾+刘炽平，专注主业、资本配置理性、连续大额定向回购注销",
      "mgmt_tags":["专注主业","资本配置理性","诚信透明"],
      "demand":"长期需求：社交/娱乐/数字化营销5-10年后仍在，AI赋能广告与游戏生产"
    },
    "seg_total":"8323亿",                  # 总营收（可选，用于业务结构概览行）
    "segments":[                          # 业务结构（收入构成，必须给占比/金额；yoy/gm/note 可选）
      {"seg":"游戏","pct":"24%","rev":"1960亿","yoy":"+11%","gm":"55%","note":"国内+海外，长青IP"},
      {"seg":"社交网络","pct":"16%","rev":"1300亿","yoy":"+6%","gm":"50%","note":"微信增值+音乐"},
      {"seg":"广告","pct":"14%","rev":"1170亿","yoy":"+17%","gm":"52%","note":"视频号拉动"},
      {"seg":"金融科技及企业服务","pct":"46%","rev":"2080亿","yoy":"+4%","gm":"40%","note":"支付+云"}
    ],
    "fin_quarters":[                      # 近N季核心财务数据（可选；与 fin_years 同结构，yr 用 "2026Q1" 等）
      {"yr":"2026Q1","rev":"1800亿","rev_yoy":"+13%","np":"478亿","np_yoy":"+22%",
       "ocf":"600亿","fcf":"430亿","gm":"54%","nm":"27%","roe":"6%","roic":"5%",
       "note":"单位：人民币；单季"},
      {"yr":"2025Q4","rev":"1900亿","rev_yoy":"+11%","np":"510亿","np_yoy":"+18%",
       "ocf":"700亿","fcf":"520亿","gm":"53%","nm":"27%","roe":"6%","roic":"5%"}
    ],
    "fin_years":[                         # 近N年核心财务数据（真实报表口径，最新在前）
      {"yr":"2025","rev":"7240亿","rev_yoy":"+9%","np":"1940亿","np_yoy":"+12%",
       "ocf":"2500亿","fcf":"1900亿","gm":"52%","nm":"27%","roe":"24%","roic":"20%",
       "note":"单位：人民币；港股财年与自然年一致"},
      {"yr":"2024","rev":"6610亿","rev_yoy":"+8%","np":"1730亿","np_yoy":"+10%",
       "ocf":"2300亿","fcf":"1750亿","gm":"51%","nm":"26%","roe":"23%","roic":"19%"},
      {"yr":"2023","rev":"6100亿","rev_yoy":"-1%","np":"1570亿","np_yoy":"-7%",
       "ocf":"2150亿","fcf":"1600亿","gm":"50%","nm":"25%","roe":"22%","roic":"18%"},
      {"yr":"2022","rev":"6160亿","rev_yoy":"+1%","np":"1690亿","np_yoy":"-7%",
       "ocf":"2000亿","fcf":"1500亿","gm":"50%","nm":"25%","roe":"22%","roic":"18%"}
    ],
    "financials":[                        # 财务体检表（门槛指标，可扩展任意行）
      {"k":"ROIC(近5年)","v":">20%","std":"高于WACC","ok":"达标"},
      {"k":"ROE(近5年)","v":">22%","std":"连续5年>15%","ok":"达标"},
      {"k":"毛利率","v":"52%","std":"稳定/提升","ok":"达标"},
      {"k":"净利率","v":"28%","std":"稳定","ok":"达标"},
      {"k":"经营现金流/净利","v":"110%","std":">80%","ok":"达标"},
      {"k":"自由现金流/净利","v":"95%","std":">80%","ok":"达标"},
      {"k":"资本开支/净利","v":"25%","std":"轻资产<30%","ok":"达标"},
      {"k":"有息负债率","v":"<10%","std":"<60%","ok":"达标"},
      {"k":"分红率","v":"40%","std":"防守>50%","ok":"观察"}
    ],
    "capital":{                           # 资本回报与现金创造力（李录核心）
      "roic":"ROIC 近5年 18-23%，高于 WACC 约 10pct",
      "fcf":"自由现金流/净利润 95%，现金创造力强",
      "blackhole":false,                  # true=资本黑洞(警告)
      "blackhole_note":"资本开支可控，未吞噬自由现金流",
      "summary":"高 ROIC + 强现金转化，典型非资本黑洞优质生意"
    },
    "returns":{                           # 股东回报（分红/回购）
      "payout":"分红率 40%","div_yield":"股息率 0.9%",
      "buyback":"年回购约 3% 股本（等效收益率 ~3%）",
      "total":"分红+回购综合收益率 ~4%",
      "note":"成长阶段回购为主，股东回报实在但股息率偏低"
    },
    "valuation":{                         # 估值分析
      "type":"D","formula":"剩余PE = (市值-净现金-股权)/主营利润",
      "fair":"合理剩余PE 15-25","range":"低估<15 / 合理15-30 / 高估>30",
      "judge":"合理","pos_hist":45,       # 历史估值分位 %
      "fair_price":"安全边际买点：剩余PE<18 ≈ 460 HKD 以下",
      "note":"当前剩余PE≈20，处历史45%分位，合理"
    },
    "safety":[                            # 安全边际清单
      {"t":"估值历史分位<30% 或 PEG<1 或 PB<1.2","ok":false,"note":"当前45%分位，未达最优买点"},
      {"t":"零增长收益率>8%","ok":true,"note":"股息+回购收益率约4%，安全边际一般"},
      {"t":"单只仓位≤25%(进攻)/15%(防守)","ok":true},
      {"t":"看得懂未来5年利润来源","ok":true},
      {"t":"股价再跌30%睡得着","ok":true}
    ],
    "tech":{ "state":"右侧强趋势","pos20":0.85,"risk_level":"LOW","risk_score":12,
             "ma5":510,"ma20":488,"ma55":460,
             "vol_ratio":0.72,            # 量比（具体读数）
             "drawdown":6.5,              # 距52w高点回撤 %（正数=低于高点）
             "price_vs_ma20":6.6,         # 现价 vs MA20 （%）
             "sig":[["缩量回调","BUY","RIGHT"]],
             "signal_detail":[            # 信号具体读数（名称+具体量化描写）
               {"name":"缩量回调","side":"RIGHT","reading":"量比0.72，连续3日缩量，价回踩MA20未破"},
               {"name":"缩量滞涨","side":"LEFT","reading":"量比0.55，价在高位横盘5日"}
             ],
             "advice":["趋势内回调可低吸，SELL信号反指"] },
    "verdict":{                           # 双视角交叉结论
      "action":"HOLD","target":"仓位上限25%，首次建仓30-50%",
      "entry":"理想买点：剩余PE<18（≈460以下）或回踩MA20",
      "add":"每跌10-15%加仓，涨20%停加，保留5-15%现金",
      "exit":"卖出触发：估值>70%分位且无更高理由 / 护城河证伪 / 连续2季超预期下滑"
    },
    "risks":[                            # 风险提示：结构化(推荐) 或 纯字符串(兼容)
      {"type":"政策","level":"高","text":"游戏版号审批节奏不确定性，新游上线可能延后，直接影响游戏管线释放","watch":"每月版署版号发放数量与腾讯在列情况、未成年防沉迷政策"},
      {"type":"经营","level":"中","text":"广告业务复苏依赖宏观消费，若复苏不及预期将拖累整体增速","watch":"季度广告收入同比、社零/互联网广告大盘数据"},
      {"type":"估值","level":"中","text":"PE 处历史低分位但非极端便宜，若美债利率上行港股估值承压","watch":"10Y 美债收益率、港股风险溢价"},
      {"type":"竞争","level":"低","text":"短视频挤占用户时长，字节系仍是最大广告与娱乐对手","watch":"微信视频号时长/加载率、腾讯广告份额变化"}
    ],
    "quote":"「胜于易胜者」"
  }
}
注：单只模式也可同时保留 items:[{code,name,...}] 以兼容旧字段，但渲染优先用 single。
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


_DEPREFIX = ["理想买点：", "加仓节奏：", "卖出触发：", "目标仓位：", "仓位管理：", "仓位："]


def _deprefix(s):
    """去掉 verdict 字段值里习惯性带的中文标签前缀，避免与版式标签重复。"""
    if not isinstance(s, str):
        return s
    for p in _DEPREFIX:
        if s.startswith(p):
            return s[len(p):]
    return s


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


# ================ 单只股票「个股深度」渲染（全面公司分析） ================
SINGLE_TPL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "report_single.html")


def action_badge(action):
    a = (action or "观望").strip()
    if a.startswith("买入"):
        return "b-buy"
    if a.startswith("卖出") or a.startswith("放弃"):
        return "b-no"
    if "等" in a:
        return "b-wait"
    return "b-watch"


def liulu_color(s):
    try:
        s = int(s)
    except (TypeError, ValueError):
        return "#8b949e"
    return "#56d364" if s >= 4 else ("#e3c14a" if s == 3 else "#ff7b72")


def col52(p):
    if p is None:
        return "#8b949e"
    return "#3b82f6" if p < 30 else ("#eab308" if p <= 70 else "#ef4444")


def sbar(pct, col, label):
    p = 0 if pct is None else max(0, min(100, pct))
    return (f'<div class="sbar"><div class="sf" style="width:{p:.0f}%;background:{col}"></div>'
            f'<span class="lab">{esc(label)}</span></div>')


def build_profile(prof, pos52):
    if not prof:
        return '<div class="qb" style="color:var(--mut)">（未提供公司画像）</div>'

    # —— 左栏：业务简述 + 关键信息 ——
    desc = prof.get("desc")
    fact_map = [("上市", prof.get("listing")), ("成立", prof.get("founded")), ("总部", prof.get("hq")),
                ("管理层", prof.get("chairman")), ("员工", prof.get("employees")),
                ("实控人", prof.get("ctrl")), ("行业地位", prof.get("position"))]
    facts = []
    for k, v in fact_map:
        if v:
            facts.append(f'<div class="fact"><span class="fk">{esc(k)}</span><span class="fv">{esc(v)}</span></div>')
    left = ""
    if desc:
        left += f'<div class="pdesc">{esc(desc)}</div>'
    if facts:
        left += f'<div class="facts">{"".join(facts)}</div>'
    left = left or '<div class="qb" style="color:var(--mut)">（未提供画像信息）</div>'

    # —— 右栏：核心指标网格 + 核心产品 ——
    def cell(k, v, col=None):
        vv = esc(v) if v is not None else "—"
        style = f' style="color:{col}"' if col else ""
        return f'<div class="pcell"><div class="k">{k}</div><div class="v"{style}>{vv}</div></div>'

    parts = [cell("行业", prof.get("industry")), cell("市值", prof.get("mktcap"))]
    px, cur = prof.get("px"), prof.get("cur", "")
    parts.append(cell("现价", f"{px} {cur}".strip() if px is not None else None))
    parts.append(cell("PE", prof.get("pe")))
    parts.append(cell("PB", prof.get("pb")))
    parts.append(cell("ROE", prof.get("roe")))
    parts.append(cell("增速g", prof.get("g")))
    parts.append(cell("PEG", prof.get("peg")))
    parts.append(cell("股息率", prof.get("div")))
    pp, pcol = pos52_cell(pos52)
    parts.append(cell("52w分位", pp, pcol))
    grid = f'<div class="pgrid">{"".join(parts)}</div>'

    prods = prof.get("core_products") or []
    chips = ('<div class="chips" style="margin-top:10px">'
             + "".join(f'<span class="chip">{esc(x)}</span>' for x in prods) + '</div>') if prods else ""
    right = grid + chips

    # —— 底部：李录六维审美（迷你进度条）——
    liulu = prof.get("liulu") or {}
    dims = []
    for name, sc in liulu.items():
        c = liulu_color(sc)
        try:
            pct = int(sc) * 20
        except (TypeError, ValueError):
            pct = 0
        dims.append(f'<div class="ldim"><span class="ln">{esc(name)}</span>'
                    f'<span class="lbar"><i style="width:{pct}%;background:{c}"></i></span>'
                    f'<span class="lsc" style="color:{c}">{esc(sc)}/5</span></div>')
    liulu_html = (f'<div class="liulu"><div class="liulu-t">李录六维审美（1–5 分）</div>'
                  f'{"".join(dims)}</div>') if dims else ""

    return f'<div class="pwrap"><div class="pleft">{left}</div><div class="pright">{right}</div></div>{liulu_html}'


QUAL_LABELS = [("business", "商业模式"), ("moat", "护城河"), ("competition", "竞争格局"),
               ("mgmt", "管理层"), ("demand", "长期需求")]
QUAL_CHIPS = {"moat": "moat_type", "mgmt": "mgmt_tags"}


def build_evid(items):
    """量化证据列表（护城河/竞争格局的具体数字）。"""
    if not items:
        return ""
    lis = []
    for it in items:
        if isinstance(it, dict):
            k = esc(it.get("k") or it.get("name") or "")
            v = esc(it.get("v") or it.get("val") or "")
        else:
            k, v = "", esc(it)
        if not (k or v):
            continue
        lis.append(f'<li><span class="ek">{k}</span><span class="ev">{v}</span></li>')
    return f'<ul class="evid">{"".join(lis)}</ul>' if lis else ""


SEG_PALETTE = ["#3b82f6", "#22c55e", "#f59e0b", "#a855f7", "#ef4444",
                "#06b6d4", "#ec4899", "#84cc16", "#f97316", "#6366f1"]


def build_segments(segs, total=None):
    """业务结构：总量概览 + 100% 堆叠条 + 多维明细表。

    segs: [{seg, pct, rev, yoy?, gm?, note?}, ...]  pct 可为 "24%" 或 24 或 None
    total: 总营收字符串（如 "8323亿"），用于概览行
    """
    if not segs:
        return '<div class="qb" style="color:var(--mut)">（未提供业务分部数据）</div>'

    # —— 解析占比，用于堆叠条比例 ——
    parsed = []
    for sg in segs:
        pct = sg.get("pct")
        try:
            p = float(str(pct).replace("%", "").strip())
        except (TypeError, ValueError):
            p = 0.0
        parsed.append((sg, p))
    ssum = sum(p for _, p in parsed) or 1.0  # 归一化基准

    # —— 概览行：总量 + 前两大分部集中度 ——
    parsed_sorted = sorted(parsed, key=lambda x: x[1], reverse=True)
    top2 = sum(p for _, p in parsed_sorted[:2])
    ov = []
    if total:
        ov.append(f'总营收 <b>{esc(total)}</b>')
    ov.append(f'分部数 <b>{len(segs)}</b>')
    ov.append(f'前两大分部合计占比 <b>{top2:.0f}%</b>')
    ov_html = f'<div class="seg-ov">{" · ".join(ov)}</div>'

    # —— 100% 堆叠条 ——
    stack_items = []
    for i, (sg, p) in enumerate(parsed):
        w = (p / ssum) * 100 if ssum else 0
        col = SEG_PALETTE[i % len(SEG_PALETTE)]
        nm = esc(sg.get("seg", "—"))
        stack_items.append(
            f'<span class="stk-seg" style="width:{w:.2f}%;background:{col}" '
            f'title="{nm} {p:.1f}%"></span>')
    legend = "".join(
        f'<span class="stk-lg"><i style="background:{SEG_PALETTE[i % len(SEG_PALETTE)]}"></i>'
        f'{esc(sg.get("seg", "—"))}</span>'
        for i, (sg, _) in enumerate(parsed))
    stack_html = (f'<div class="seg-stack">{"".join(stack_items)}</div>'
                  f'<div class="stk-legend">{legend}</div>')

    # —— 多维明细表 ——
    head_cells = ['<th>业务分部</th>', '<th>收入</th>', '<th>占比</th>']
    has_yoy = any(sg.get("yoy") is not None for sg, _ in parsed)
    has_gm = any(sg.get("gm") is not None for sg, _ in parsed)
    if has_yoy:
        head_cells.append('<th>同比</th>')
    if has_gm:
        head_cells.append('<th>毛利率</th>')
    head_cells.append('<th>说明</th>')
    head = '<tr>' + "".join(head_cells) + '</tr>'

    body_rows = []
    for sg, p in parsed:
        tds = [f'<td class="seg-nm">{esc(sg.get("seg", "—"))}</td>',
               f'<td>{esc(sg.get("rev", "—"))}</td>',
               f'<td><b>{esc(sg.get("pct", "—"))}</b></td>']
        if has_yoy:
            yv = sg.get("yoy")
            yc = "up" if str(yv).startswith("+") else ("dn" if str(yv).startswith("-") else "neu")
            tds.append(f'<td class="{yc}">{esc(yv) if yv is not None else "—"}</td>')
        if has_gm:
            tds.append(f'<td>{esc(sg.get("gm")) if sg.get("gm") is not None else "—"}</td>')
        tds.append(f'<td class="seg-note">{esc(sg.get("note", "—"))}</td>')
        body_rows.append(f'<tr>{"".join(tds)}</tr>')
    table = (f'<table class="segtab"><thead>{head}</thead>'
             f'<tbody>{"".join(body_rows)}</tbody></table>')

    return f'<div class="segs">{ov_html}{stack_html}{table}</div>'


FIN_METRICS = [
    ("rev", "营收", False), ("rev_yoy", "营收同比", True),
    ("np", "归母净利", False), ("np_yoy", "净利同比", True),
    ("ocf", "经营现金流", False), ("fcf", "自由现金流", False),
    ("gm", "毛利率", False), ("nm", "净利率", False),
    ("roe", "ROE", False), ("roic", "ROIC", False),
]


def build_fin_table(rows, caption_label=None):
    """核心财务数据表（指标 × 期次），真实报表口径。rows 最新在前。"""
    if not rows:
        return '<div class="qb" style="color:var(--mut)">（未提供财务数据）</div>'
    periods = [esc(r.get("yr", "?")) for r in rows]
    head = '<tr><th>指标</th>' + "".join(f'<th>{p}</th>' for p in periods) + '</tr>'
    body = []
    for key, lab, is_yoy in FIN_METRICS:
        tds = []
        for r in rows:
            val = r.get(key)
            if val is None:
                tds.append('<td class="neu">—</td>')
                continue
            cell_cls = "neu"
            if is_yoy:
                s = str(val).strip()
                if s.startswith("+"):
                    cell_cls = "up"
                elif s.startswith("-"):
                    cell_cls = "dn"
            tds.append(f'<td class="{cell_cls}">{esc(val)}</td>')
        body.append(f'<tr><td>{lab}</td>{"".join(tds)}</tr>')
    note = esc(rows[0].get("note", "")) if rows else ""
    cap = f'<caption>{caption_label + " · " if caption_label else ""}{note}</caption>' if (caption_label or note) else ""
    return (f'<table class="fintab"><thead>{head}</thead><tbody>{"".join(body)}</tbody>{cap}</table>')


def build_fin_years(rows):
    return build_fin_table(rows)


def build_qual(q):
    cells = []
    for key, lab in QUAL_LABELS:
        txt = q.get(key)
        if not txt:
            continue
        chip_key = QUAL_CHIPS.get(key)
        chips = ""
        if chip_key:
            vals = q.get(chip_key) or []
            if vals:
                chips = '<div class="chips">' + "".join(f'<span class="chip">{esc(x)}</span>' for x in vals) + '</div>'
        evid = ""
        if key == "moat":
            evid = build_evid(q.get("moat_data"))
        elif key == "competition":
            evid = build_evid(q.get("comp_data"))
        cells.append(f'<div class="qcell"><div class="qt">{lab}</div>'
                     f'<div class="qb">{esc(txt)}</div>{chips}{evid}</div>')
    return "".join(cells) or '<div class="qb" style="color:var(--mut)">（未提供定性内容）</div>'


def build_capital(c):
    """李录核心：资本回报与现金创造力（高 ROIC、忌资本黑洞）。"""
    if not c:
        return '<div class="qb" style="color:var(--mut)">（未提供资本回报分析）</div>'
    bh = c.get("blackhole")
    if bh:
        bh_html = '<span class="badge b-no">⚠ 资本黑洞</span> '
        bh_cls = "ok-n"
    else:
        bh_html = '<span class="badge b-def">✓ 非资本黑洞</span> '
        bh_cls = "ok-y"
    bh_note = esc(c.get("blackhole_note", ""))
    summary = c.get("summary", "")
    summary_html = (f'结论：<b>{esc(summary)}</b>' if summary else "")
    return (f'<div class="cap">'
            f'<div class="cr"><div class="ck">ROIC（近5年）</div><div class="cv">{esc(c.get("roic", "—"))}</div></div>'
            f'<div class="cr"><div class="ck">自由现金流/净利</div><div class="cv">{esc(c.get("fcf", "—"))}</div></div>'
            f'<div class="cr"><div class="ck">资本黑洞检查</div><div class="cv">{bh_html}<span class="{bh_cls}">{bh_note}</span></div></div>'
            f'<div class="note">{summary_html}</div></div>')


def build_returns(r):
    """股东回报：分红 / 回购 / 综合收益率。"""
    if not r:
        return '<div class="qb" style="color:var(--mut)">（未提供股东回报数据）</div>'
    total = r.get("total")
    tcls = " rv hi" if total else "rv"
    return (f'<div class="retbox">'
            f'<div class="rk">分红率</div><div class="rv">{esc(r.get("payout", "—"))}</div>'
            f'<div class="rk">股息率</div><div class="rv">{esc(r.get("div_yield", "—"))}</div>'
            f'<div class="rk">年回购力度</div><div class="rv">{esc(r.get("buyback", "—"))}</div>'
            f'<div class="rk">综合收益率</div><div class="rv{tcls}">{esc(total or "—")}</div>'
            f'</div><div class="qb" style="margin-top:10px;color:#c9d1d9">{esc(r.get("note", ""))}</div>')


def build_fin(rows):
    if not rows:
        return '<div class="qb" style="color:var(--mut)">（未提供财务数据）</div>'
    trs = []
    for r in rows:
        ok = r.get("ok", "观察")
        cls = "ok-y" if ok == "达标" else ("ok-n" if ok == "淘汰" else "ok-w")
        trs.append(f'<tr><td>{esc(r.get("k"))}</td><td>{esc(r.get("v"))}</td>'
                   f'<td style="color:var(--mut)">{esc(r.get("std"))}</td>'
                   f'<td class="{cls}">{esc(ok)}</td></tr>')
    return ('<table><thead><tr><th>指标</th><th>实测值</th><th>门槛/标准</th><th>状态</th></tr></thead>'
            f'<tbody>{"".join(trs)}</tbody></table>')


def build_val(v):
    if not v:
        return '<div class="qb" style="color:var(--mut)">（未提供估值分析）</div>'
    jc = {"低估": "b-buy", "合理": "b-watch", "高估": "b-no"}.get(v.get("judge"), "b-watch")
    pos_hist = v.get("pos_hist")
    hist_bar = ""
    if pos_hist is not None:
        try:
            p = float(pos_hist)
            hc = "#3b82f6" if p < 30 else ("#eab308" if p <= 70 else "#ef4444")
            hist_bar = sbar(p, hc, f"历史估值分位 {p:.0f}%")
        except (TypeError, ValueError):
            pass
    fair = v.get("fair_price")
    fair_html = f'<div class="vk">安全边际价位</div><div class="vv hi">{esc(fair)}</div>' if fair else ""
    return (f'<div class="valbox">'
            f'<div class="vk">估值类型</div><div class="vv"><span class="badge b-alt">类型{v.get("type", "—")}</span></div>'
            f'<div class="vk">公式</div><div class="vv">{esc(v.get("formula", "—"))}</div>'
            f'<div class="vk">合理区间</div><div class="vv">{esc(v.get("range", "—"))}</div>'
            f'<div class="vk">判断</div><div class="vv"><span class="badge {jc}">{esc(v.get("judge", "—"))}</span></div>'
            f'{fair_html}'
            f'</div>{hist_bar}'
            f'<div class="qb" style="margin-top:10px;color:#c9d1d9">{esc(v.get("note", ""))}</div>')


def build_safety(items):
    if not items:
        return '<div class="qb" style="color:var(--mut)">（未提供安全边际清单）</div>'
    out = []
    for it in items:
        ok = it.get("ok")
        mk = '<span class="mk ok-y">✓</span>' if ok else '<span class="mk ok-n">✗</span>'
        out.append(f'<li>{mk}<div class="txt">{esc(it.get("t"))}'
                   f'<div class="nt">{esc(it.get("note", ""))}</div></div></li>')
    return f'<ul class="safety">{"".join(out)}</ul>'


def _norm_sig(s):
    if isinstance(s, dict):
        return (s.get("strategy", s.get("type", "?")), s.get("type", s.get("side", "?")), s.get("side", "?"))
    if isinstance(s, (list, tuple)) and len(s) >= 3:
        return (s[0], s[1], s[2])
    return ("?", "?", "?")


def _sig_row(cls, arrow, nm, side_cn, rd):
    side = f'<span class="ts-side">{esc(side_cn)}</span>' if side_cn else ""
    return (f'<div class="tsig {cls}"><span class="ts-arrow">{arrow}</span>'
            f'<span class="ts-name">{esc(nm)}</span>{side}'
            f'<span class="ts-read">{esc(rd)}</span></div>')


def build_tech_single(tech, pos52, verdict=None):
    """技术面（辅助）：重构成「择时仪表盘」。
    重点放在顶部一句择时结论（cross_verdict 推导），下面三栏核心指标 +
    价格位置标尺 + 按买/卖方向分组的量价信号，让基本面投资者一眼看懂「现在该不该动手」。"""
    if not tech:
        return '<div class="qb" style="color:var(--mut)">无技术数据</div>'
    vd = verdict if isinstance(verdict, dict) else {}
    fv = vd.get("action", "观望")
    state = infer_state(tech)
    pos20 = norm_pct(tech.get("pos20"))
    p52 = pos52 if pos52 is not None else norm_pct(tech.get("pos52"))
    p52v = p52 if p52 is not None else 50
    risk_level = tech.get("risk_level", "—")
    risk_score = tech.get("risk_score", "—")

    # 1) 择时结论横幅（整块重点）
    verdict, vc = cross_verdict(fv, state, p52)
    if p52 is not None:
        if p52v < 30:
            zone = f"52周低位（便宜区间，{p52:.0f}%）"
        elif p52v > 70:
            zone = f"52周高位（偏贵，{p52:.0f}%）"
        else:
            zone = f"52周中位（{p52:.0f}%）"
    else:
        zone = "52周分位未知"
    if verdict.startswith("买入"):
        tv = f"基本面看好 + 技术面 {zone}，可逢回调分批建仓。"
    elif "持有" in verdict:
        if p52v < 30:
            tv = f"趋势仍强且处于 {zone}：回踩 MA20 可逢低加仓；基本面结论为「持有」，故以持有为主、低位才加。"
        else:
            tv = f"趋势仍强但 {zone}：持有不加，回踩均线（MA20）再考虑补仓。"
    elif "观望" in verdict or "避险" in verdict:
        tv = f"技术面尚未给出动手信号（{zone}），等方向明确（放量站回 MA20 / 突破）再评估。"
    elif "放弃" in verdict:
        tv = "基本面与技术面均不支持参与，回避。"
    else:
        tv = "技术面辅助判断，不改变基本面结论。"

    # 2) 三栏核心：趋势 / 位置 / 风险
    ma5, ma20, ma55 = tech.get("ma5", "—"), tech.get("ma20", "—"), tech.get("ma55", "—")
    try:
        m5, m2, m5_ = float(ma5), float(ma20), float(ma55)
        arrange = "多头排列 ↑" if m5 > m2 > m5_ else ("空头排列 ↓" if m5 < m2 < m5_ else "均线纠缠")
    except (TypeError, ValueError):
        arrange = "—"
    trend_sub = f"{arrange} · MA5 {ma5} / MA20 {ma20} / MA55 {ma55}"

    pos_class = "低位" if p52v < 30 else ("高位" if p52v > 70 else "中位")
    pos_v = f"{p52:.0f}%" if p52 is not None else "—"
    pos_sub = f"20日位置 {pos20:.0f}%" if pos20 is not None else "20日位置 —"

    rr = tech.get("drawdown")
    pma = tech.get("price_vs_ma20")
    risk_sub = ""
    if rr is not None:
        try:
            risk_sub += f"距52w高点回撤 -{float(rr):.1f}%"
        except (TypeError, ValueError):
            pass
    if pma is not None:
        try:
            risk_sub += f" · 现价vsMA20 {float(pma):+.1f}%"
        except (TypeError, ValueError):
            pass
    risk_sub = risk_sub or "—"

    # 3) 价格位置标尺说明
    if p52 is not None:
        zone = "低位（便宜区间）" if p52 < 30 else ("高位（偏贵、不追）" if p52 > 70 else "中位（合理区间）")
        pa_cap = f"当前价处于 52 周 <b>{zone}</b>"
        if rr is not None:
            try:
                pa_cap += f" · 距高点回撤 <b>-{float(rr):.1f}%</b>"
            except (TypeError, ValueError):
                pass
        ptr_left = f"{min(98, max(2, p52)):.0f}%"
    else:
        pa_cap = "52周分位数据缺失"
        ptr_left = "50%"

    # 4) 信号按买/卖方向分组
    sigs = tech.get("sig") or tech.get("signals") or []
    detail_map = {d.get("name"): d for d in (tech.get("signal_detail") or []) if isinstance(d, dict)}
    buys, sells = [], []
    for s in sigs:
        if isinstance(s, dict):
            nm, typ, side = s.get("strategy", "?"), s.get("type", "?"), s.get("side", "")
        elif isinstance(s, (list, tuple)) and len(s) >= 3:
            nm, typ, side = s[0], s[1], s[2]
        else:
            continue
        det = detail_map.get(nm, {})
        reading = det.get("reading") or (s.get("reason") if isinstance(s, dict) else "")
        side_cn = "左侧" if side == "LEFT" else ("右侧" if side == "RIGHT" else "")
        if typ == "BUY":
            buys.append((nm, side_cn, reading))
        elif typ == "SELL":
            sells.append((nm, side_cn, reading))
    if buys or sells:
        parts = [f'<div class="ts-h">量价信号（买入 {len(buys)} · 卖出 {len(sells)}）</div>']
        for nm, sc, rd in buys:
            parts.append(_sig_row("buy", "↑", nm, sc, rd))
        for nm, sc, rd in sells:
            parts.append(_sig_row("sell", "↓", nm, sc, rd))
        sig_html = "".join(parts)
    else:
        sig_html = '<div class="ts-h">量价信号：暂无明显买卖信号触发</div>'
    if sells and state == "右侧强趋势":
        sig_html += ('<div class="ts-h" style="color:#eab308;margin-top:2px">'
                     '提示：强趋势中的「左侧卖出」信号多属反指，不据此卖出；仅当跌破 MA20 才考虑减仓。</div>')

    # 5.5) 操作信号卡（从基本面结论 verdict 提取动作化指引：买点/加仓/卖出触发/仓位）
    entry = _deprefix(vd.get("entry"))
    add = _deprefix(vd.get("add"))
    exit_ = _deprefix(vd.get("exit"))
    target = _deprefix(vd.get("target"))
    act_rows = []
    if entry:
        act_rows.append(f'<div class="tact-item buy"><span class="tact-k">理想买点</span>'
                        f'<span class="tact-v">{esc(entry)}</span></div>')
    if add:
        act_rows.append(f'<div class="tact-item add"><span class="tact-k">加仓节奏</span>'
                        f'<span class="tact-v">{esc(add)}</span></div>')
    if exit_:
        act_rows.append(f'<div class="tact-item exit"><span class="tact-k">卖出触发</span>'
                        f'<span class="tact-v">{esc(exit_)}</span></div>')
    if target:
        act_rows.append(f'<div class="tact-item"><span class="tact-k">仓位管理</span>'
                        f'<span class="tact-v">{esc(target)}</span></div>')
    act_html = (f'<div class="tact"><div class="tact-h">⚡ 操作信号（买点 / 加仓 / 卖出触发）</div>'
                f'{"".join(act_rows)}</div>') if act_rows else ""

    # 5) 择时建议
    adv = "；".join(esc(a) for a in tech.get("advice") or []) or "无特别建议"

    border_c = {"b-buy": "var(--red)", "b-watch": "var(--yel)",
                "b-wait": "var(--blue)", "b-no": "var(--mut)"}.get(vc, "var(--mut)")

    return (f'<div class="tech2">'
            f'<div class="tverdict" style="border-left:4px solid {border_c}">'
            f'<span class="tv-badge badge {vc}">{esc(verdict)}</span>'
            f'<div class="tv-text">{esc(tv)}</div></div>'
            f'<div class="tcols">'
            f'<div class="tcol"><div class="tc-k">趋势方向</div>'
            f'<div class="tc-v"><span class="badge {STB.get(state, "b-drop")}">{esc(state)}</span></div>'
            f'<div class="tc-sub">{esc(trend_sub)}</div></div>'
            f'<div class="tcol"><div class="tc-k">价格位置（52w分位）</div>'
            f'<div class="tc-v">{pos_v} <small>{pos_class}</small></div>'
            f'<div class="tc-sub">{esc(pos_sub)}</div></div>'
            f'<div class="tcol"><div class="tc-k">追高风险</div>'
            f'<div class="tc-v"><span class="badge {RSKB.get(risk_level, "b-drop")}">{esc(risk_level)} {esc(risk_score)}</span></div>'
            f'<div class="tc-sub">{esc(risk_sub)}</div></div>'
            f'</div>'
            f'<div class="posaxis"><div class="pa-track">'
            f'<span class="pa-z low">低位</span><span class="pa-z mid">中位</span><span class="pa-z high">高位</span>'
            f'<i class="pa-ptr" style="left:{ptr_left}"></i></div>'
            f'<div class="pa-cap">{pa_cap}</div></div>'
            f'<div class="tsigs">{sig_html}</div>'
            f'{act_html}'
            f'<div class="tadv">→ {adv}</div>'
            f'<div class="aux-note">技术面仅作买入/加仓的择时辅助，不改变基本面结论；右侧不追高、破位减仓，仅供参考。</div>'
            f'</div>')


def build_verdict(v):
    if not v:
        return '<div class="qb" style="color:var(--mut)">（未提供结论）</div>'
    return (f'<div class="vrow"><div class="vk">综合结论</div><div class="vv"><span class="badge {action_badge(v.get("action"))}">{esc(v.get("action", "—"))}</span></div></div>'
            f'<div class="vrow"><div class="vk">目标仓位</div><div class="vv">{esc(_deprefix(v.get("target", "—")))}</div></div>'
            f'<div class="vrow"><div class="vk">理想买点</div><div class="vv">{esc(_deprefix(v.get("entry", "—")))}</div></div>'
            f'<div class="vrow"><div class="vk">加仓节奏</div><div class="vv">{esc(_deprefix(v.get("add", "—")))}</div></div>'
            f'<div class="vrow"><div class="vk">卖出触发</div><div class="vv">{esc(_deprefix(v.get("exit", "—")))}</div></div>')


RLB = {"高": "r-high", "中": "r-mid", "低": "r-low"}


def build_risks(items):
    """风险提示：支持结构化项 {type,level,text,watch}；纯字符串向后兼容。"""
    if not items:
        return '<div class="qb" style="color:var(--mut)">（未提供风险分析）</div>'
    # 计数概览
    cnt = {"高": 0, "中": 0, "低": 0}
    cards = []
    for it in items:
        if isinstance(it, dict):
            lvl = it.get("level") or "中"
            cnt[lvl] = cnt.get(lvl, 0) + 1
            badge = f'<span class="rbadge {RLB.get(lvl, "r-mid")}">{esc(lvl)}风险</span>'
            typ = it.get("type")
            tag = f'<span class="rtag">{esc(typ)}</span>' if typ else ""
            txt = esc(it.get("text") or it.get("risk") or "")
            watch = it.get("watch")
            watch_html = (f'<div class="rwatch">→ 关注信号：{esc(watch)}</div>') if watch else ""
            cards.append(f'<li class="ritem">{badge}{tag}'
                         f'<div class="rbody"><div class="rtext">{txt}</div>{watch_html}</div></li>')
        else:
            cnt["中"] += 1
            cards.append(f'<li class="ritem"><span class="rbadge r-mid">中风险</span>'
                         f'<div class="rbody"><div class="rtext">{esc(it)}</div></div></li>')
    overview = (f'<div class="roverview">共 {sum(cnt.values())} 项风险 · '
                f'<span class="r-high">高 {cnt["高"]}</span> · '
                f'<span class="r-mid">中 {cnt["中"]}</span> · '
                f'<span class="r-low">低 {cnt["低"]}</span></div>')
    note = ('<div class="rnote">分级标准：<b>高</b>=可能直接侵蚀护城河或自由现金流（一票否决级）；'
            '<b>中</b>=影响增速但可逆；<b>低</b>=短期扰动、不改长期逻辑。每项附「关注信号」便于持续跟踪。</div>')
    return overview + note + f'<ul class="risklist">{"".join(cards)}</ul>'


def render_single(cfg):
    s = cfg.get("single") or {}
    prof = s.get("profile", {}) or {}
    pos52 = prof.get("pos52")
    if pos52 is None and prof.get("hi52") and prof.get("lo52") is not None:
        hi, lo, px = float(prof["hi52"]), float(prof["lo52"]), float(prof.get("px") or 0)
        pos52 = (px - lo) / (hi - lo) * 100 if hi > lo else None
    pos52 = norm_pct(pos52)

    items = cfg.get("items") or []
    name = prof.get("name") or cfg.get("scope") or (items[0].get("name", "") if items else "")
    code = prof.get("code") or (items[0].get("code", "") if items else "")
    cls = prof.get("cls") or "—"
    action = (s.get("verdict") or {}).get("action", "观望")
    summary = s.get("summary", "")
    quote = s.get("quote")

    with open(SINGLE_TPL_PATH, encoding="utf-8") as f:
        tpl = f.read()
    out = (tpl
           .replace("{{TITLE}}", esc(cfg.get("title", f"{name} · 个股深度分析")))
           .replace("{{SUBTITLE}}", cfg.get("subtitle", ""))
           .replace("{{CALLOUT}}", f'<div class="callout">{cfg["callout"]}</div>' if cfg.get("callout") else "")
           .replace("{{NAME}}", esc(name))
           .replace("{{CODE}}", esc(code))
           .replace("{{CLS}}", esc(cls))
           .replace("{{CLSB}}", CLSB.get(cls, "b-drop"))
           .replace("{{ACTION}}", esc(action))
           .replace("{{VC}}", action_badge(action))
           .replace("{{SUMMARY}}", esc(summary))
           .replace("{{PROFILE}}", build_profile(prof, pos52))
           .replace("{{QUAL}}", build_qual(s.get("qualitative", {})))
           .replace("{{SEGS}}", build_segments(s.get("segments"), s.get("seg_total")))
           .replace("{{FINYEARS}}", build_fin_years(s.get("fin_years")))
           .replace("{{FINQ}}", build_fin_table(s.get("fin_quarters"), "季度"))
           .replace("{{HAS_Q}}", "" if s.get("fin_quarters") else ' style="display:none"')
           .replace("{{FIN}}", build_fin(s.get("financials", [])))
           .replace("{{CAPITAL}}", build_capital(s.get("capital")))
           .replace("{{RETURNS}}", build_returns(s.get("returns")))
           .replace("{{VAL}}", build_val(s.get("valuation")))
           .replace("{{SAFETY}}", build_safety(s.get("safety", [])))
           .replace("{{TECH}}", build_tech_single(s.get("tech"), pos52, s.get("verdict")))
           .replace("{{VERDICT}}", build_verdict(s.get("verdict")))
           .replace("{{RISKS}}", build_risks(s.get("risks", [])))
           .replace("{{QUOTE}}", f'<div class="sec-t">九、守拙君金句</div><div class="quote">「{esc(quote)}」</div>' if quote else "")
           .replace("{{FOOTER}}", cfg.get("footer", "本报告为框架化研究，非投资建议。")))
    return out


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
    if not cfg.get("single") and not cfg.get("items"):
        sys.exit("input.json 缺少 items（组合模式）或 single（个股深度模式）")

    tech_ext = {}
    if args.tech:
        with open(args.tech, encoding="utf-8") as f:
            tech_ext = json.load(f)

    if cfg.get("single"):
        out = render_single(cfg)
        n_items = 1
    else:
        out, rows = render(cfg, tech_ext)
        n_items = len(rows)

    if args.output:
        target = args.output
    else:
        target = dedupe_path(os.path.join(args.outdir, build_filename(cfg, n_items)))
    d = os.path.dirname(os.path.abspath(target))
    os.makedirs(d, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(out)
    args.output = target

    print(f"written: {args.output} ({os.path.getsize(args.output)} bytes, mode={'个股深度' if cfg.get('single') else '组合体检'}, {n_items} item)")
    if cfg.get("single"):
        action = (cfg.get("single", {}).get("verdict") or {}).get("action", "观望")
        print("单只结论:", action)
    else:
        dist = {}
        for r in rows:
            dist[r["verdict"]] = dist.get(r["verdict"], 0) + 1
        print("结论分布:", " | ".join(f"{k} {v}" for k, v in sorted(dist.items(), key=lambda x: -x[1])))


if __name__ == "__main__":
    main()
