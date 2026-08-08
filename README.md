# investment-decision

WorkBuddy skill：双视角投资决策（基本面 + 技术面）。

## 适用场景

- 评估个股/ETF 能不能买、什么价位买、该不该卖
- 持仓体检与安全边际评估
- 结合守拙君五步法（基本面）与趋势状态三分法（技术面）给出 BUY/SELL/HOLD 结论

## 框架

- **基本面**：守拙君五步法（分类 → 定性 → 定量 → 估值 → 安全边际/仓位）+ 李录六维审美检查
- **技术面**：MA 状态 + 10 种量价信号 + 风险评分 + 右侧趋势确认；使用规则经 142 只样本三轮回测校准
- **输出**：文本结论、汇总表格、单文件 HTML 可视化报告

## 目录

```
.
├── SKILL.md                      # 主技能说明与工作流
├── references/
│   ├── fundamental.md            # 守拙君五步法 + 李录审美
│   ├── technical.md              # 技术信号规则与回测注记
│   └── data-sources.md           # 数据源映射
├── scripts/
│   ├── technical_engine.py       # 日K → MA/信号/风险/建议
│   ├── valuation.py              # 基本面参数 → 估值结论
│   ├── backtest.py               # 历史信号回测器
│   └── render_report.py          # JSON → HTML 可视化报告
└── templates/
    ├── report.html               # 组合体检模板（多只/组合）
    └── report_single.html        # 个股深度模板（单只全面公司分析）
```

## 快速开始

### 1. 技术面分析

```bash
python scripts/technical_engine.py kline.json
```

`kline.json` 格式：`[["日期", 开, 收, 高, 低, 量], ...]`

### 2. 基本面估值

```bash
cat > params.json <<'EOF'
{
  "type": "A",
  "pe": 18,
  "g": 0.10,
  "dividend_yield": 0.02,
  "roe": 0.18,
  "pb": 3.0,
  "discount": 0.10,
  "terminal_g": 0.03,
  "market_cap": null,
  "investments": null,
  "net_cash": null,
  "operating_profit": null
}
EOF
python scripts/valuation.py params.json
```

### 3. 生成 HTML 报告

```bash
cat > input.json <<'EOF'
{
  "title": "组合体检报告",
  "subtitle": "",
  "items": [
    {
      "code": "sh600000",
      "name": "浦发银行",
      "cls": "防守",
      "px": 7.5,
      "cur": "CNY",
      "pe": "5.2",
      "pb": "0.45",
      "div": "6%",
      "roe": "9%",
      "g": "3%",
      "peg": "1.7",
      "hi52": 9,
      "lo52": 6.8,
      "valst": "低估",
      "fv": "买入",
      "blurb": "金融蓝筹，股息率高，PB<1。",
      "quote": "「估值低允许一切容错率」",
      "tech": {
        "state": "右侧强趋势",
        "pos20": 0.85,
        "risk_level": "LOW",
        "risk_score": 10,
        "ma5": 7.4,
        "ma20": 7.1,
        "ma55": 6.9,
        "sig": [["缩量回调", "BUY", "RIGHT"]],
        "advice": ["趋势内回调 → 可低吸"]
      }
    }
  ]
}
EOF
python scripts/render_report.py input.json -o report.html
```

打开 `report.html` 即可查看图表、矩阵与逐只卡片。

### 4. 单只股票「个股深度」报告

分析单只公司时，input.json 用 `single` 字段给出全维度内容（公司画像 / 定性五块 / 财务体检 / 估值 / 安全边际 / 技术面 / 双视角结论），渲染器自动改用 `report_single.html`：

```bash
cat > single.json <<'EOF'
{
  "scope": "腾讯控股", "kind": "个股深度", "date": "2026-08-08",
  "title": "腾讯控股 · 个股深度分析",
  "single": {
    "summary": "一句话定位…",
    "profile": {"industry":"互联网","mktcap":"3.2万亿 HKD","px":520.5,"cur":"HKD",
                "pe":"22","pb":"4.2","roe":"23%","g":"12%","peg":"1.8",
                "hi52":620,"lo52":360,"cls":"进攻",
                "liulu":{"业务质量":5,"管理层":5,"长坡厚雪":5,"价格":3,"能力圈":5,"集中耐心":5}},
    "qualitative": {"business":"…","moat":"…","competition":"…","mgmt":"…","demand":"…"},
    "financials": [{"k":"ROE","v":">22%","std":"连续5年>15%","ok":"达标"}, …],
    "valuation": {"type":"D","formula":"…","fair":"…","range":"…","judge":"合理","note":"…"},
    "safety": [{"t":"估值分位<30%","ok":false,"note":"…"}, …],
    "tech": {"state":"右侧强趋势","pos20":0.85,"risk_level":"LOW","risk_score":12,
             "ma5":510,"ma20":488,"ma55":460,"sig":[["缩量回调","BUY","RIGHT"]],"advice":["可低吸"]},
    "verdict": {"action":"HOLD","target":"仓位上限25%","entry":"理想买点…","add":"加仓节奏…","exit":"卖出触发…"},
    "risks": ["…","…"],
    "quote": "胜于易胜者"
  }
}
EOF
python scripts/render_report.py single.json --outdir .   # 自动命名 腾讯控股_个股深度_2026-08-08.html
```

完整 `single` schema 见 `scripts/render_report.py` 顶部 docstring。

## 回测验证

```bash
python scripts/backtest.py /path/to/klines_dir --forward 5,10,20 --cooldown 5
```

## 免责声明

本 skill 为框架化研究工具，不构成投资建议。所有决策需结合个人风险承受能力与独立判断。

## License

MIT
