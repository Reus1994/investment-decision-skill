# 行情数据获取指南

## 优先：已连接的行情工具（推荐）
通过连接器（如 westock-mcp 腾讯自选股、东方财富等）直接查询：
- `data_quote`：现价、涨跌幅、PE、PB、股息率、52周高低、历史估值分位（一手数据，最准）
- `data_consensus`：ROE 预测、净利预测、营收预测（增速做 PEG/内在收益测算）
- `data_kline`：日/周K（技术面信号输入）
- `data_finance` / `data_dividend` / `data_score`：财务明细、分红、综合评分
- 先用对应工具看 `help`，确认市场（A/港/美）与代码格式（如 `sh603259`、`hk00700`、`usAAPL`）

## 备选：腾讯公共接口（无需登录）
- 实时报价：`https://qt.gtimg.cn/q=sh600519,hk00700,usAAPL`（GBK 编码；字段 ~3=现价 ~4=昨收 ~1=名称）
- 日/周K：`https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600519,day,,,320,qfq`
  - 必须 HTTPS；响应 `data.<code>.qfqday|qfqweek|day|week`
  - 行格式：`[日期, 开, 收, 高, 低, 量]`（注意：**第2=开、第3=收**）
  - 覆盖：A股/港股完整；**美股仅返回首尾两根，不可用于技术分析**

## 备选：东方财富公共接口（无需登录，覆盖美股）
- 日/周K：`https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=<市场>.<代码>&fields1=f1,f2,f3&fields2=f51,f52,f53,f54,f55,f56&klt=101&fqt=1&end=20500101&lmt=320`
  - secid 市场段：A股沪=1、A股深=0、港股=116、美股=105（如 `1.600519`、`116.00700`、`105.AAPL`）
  - klt：日=101、周=102；fqt=1 前复权
  - 行格式：`"日期,开,收,高,低,量,..."`（与腾讯同序）
- 实时报价：`https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields=f2,f12,f13,f14,f18&secids=1.600519,105.AAPL`
  - f2=最新价、f18=昨收、f14=名称、f12=代码、f13=市场段

## 建议的分工
- 实时报价：腾讯优先（一次请求可带全部代码，全市场可用）
- 日/周K：A股/港股腾讯优先；**美股必须东财**（腾讯无美股历史K）
- 任一源失败自动切换另一个；K 线 <25 根视为数据不足
