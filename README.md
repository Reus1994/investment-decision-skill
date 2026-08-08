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
    └── report.html               # 报告模板
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

## 回测验证

```bash
python scripts/backtest.py /path/to/klines_dir --forward 5,10,20 --cooldown 5
```

## 免责声明

本 skill 为框架化研究工具，不构成投资建议。所有决策需结合个人风险承受能力与独立判断。

## License

MIT
