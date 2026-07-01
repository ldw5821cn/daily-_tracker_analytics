# 多板块 ETF 智能投资分析系统

> **核心能力**: 跟踪 **28 只市值 100 亿以上 ETF**，覆盖 机器人 / 人工智能 / AI / 芯片制造 / 半导体设备 / 存储行业 / 内存制造 / 稀土永磁 / 有色金属 / 动力电池 / 银行 / 证券 / 消费 / 医药 / 高股息 / 通信 / 互联网 / 港股科技 / 宽基指数 / 美股科技 / 美股大盘 / 美股半导体 / 美股机器人 等全市场热点板块。  
> **投资主题**: 国产替代 + 稀土永磁 + 半导体产业链 + AI算力 + 机器人 + 新能源 + 高股息 + 大消费。  
> **部署状态**: 已通过 Hermes 定时任务每日自动运行并推送微信报告。

---

## 📊 项目简介

本项目是一个**全市场多板块 ETF 量化投资分析系统**，支持同时跟踪 **28 只大型 ETF** 及其 **Top10 成分股**，集成多数据源、本地缓存、多周期回测、多模型预测、实时预警、机构研报、国际市场、个股深度分析和微信推送能力，为投资决策提供数据驱动的支持。

系统每日自动运行，采用"**快速扫描全部 ETF + 深度分析前 N 板块 + Top10 成分股预测 + 机构研报 + 实时预警**"的分层策略，生成包含板块排名、重点板块深度分析、多模型预测、Top 成分股跟踪、投资建议汇总的综合报告，并通过 Hermes 微信通道推送到用户微信。

---

## 🚀 主要功能

### 1. 全市场大型 ETF 跟踪（28 只）

覆盖 A 股、港股、美股主要热点板块，每只 ETF 可配置 Top10 成分股。

| 主题 | ETF 代码 | 名称 | 说明 |
|------|----------|------|------|
| **机器人** | 562500 | 机器人ETF华夏 | 汇川技术、埃斯顿、绿的谐波等 |
| **机器人** | 159530 | 机器人ETF易方达 | 汇川技术、埃斯顿、绿的谐波等 |
| **人工智能/AI** | 159819 | 人工智能ETF易方达 | 寒武纪、海康威视、科大讯飞等 |
| **芯片制造** | 588200 | 科创芯片ETF嘉实 | 中芯国际、海光信息、寒武纪等 |
| **半导体设备** | 159516 | 半导体设备ETF国泰 | 北方华创、中微公司、拓荆科技等 |
| **芯片设计** | 159995 | 芯片ETF华夏 | 中芯国际、韦尔股份、兆易创新等 |
| **CPU/芯片** | 512760 | 芯片ETF | 中芯国际、海光信息、寒武纪等 |
| **晶圆制造** | 512480 | 半导体ETF | 中芯国际、北方华创、中微公司等 |
| **稀土永磁** | 516150 | 稀土ETF嘉实 | 北方稀土、中国稀土、盛和资源等 |
| **有色金属** | 512400 | 有色金属ETF南方 | 紫金矿业、中国铝业、洛阳钼业等 |
| **动力电池** | 159755 | 电池ETF广发 | 宁德时代、比亚迪、亿纬锂能等 |
| **银行** | 512800 | 银行ETF | 招商银行、工商银行、建设银行等 |
| **证券** | 512880 | 证券ETF国泰 | 东方财富、中信证券、华泰证券等 |
| **证券** | 512000 | 券商ETF华宝 | 东方财富、中信证券、华泰证券等 |
| **消费** | 159928 | 消费ETF | 贵州茅台、五粮液、伊利股份等 |
| **医疗器械** | 512170 | 医疗ETF华宝 | 迈瑞医疗、联影医疗、爱美客等 |
| **创新药** | 513120 | 港股创新药ETF广发 | 药明生物、百济神州、信达生物等 |
| **高股息** | 512890 | 红利低波ETF华泰柏瑞 | 中国神华、长江电力、工商银行等 |
| **高股息** | 563180 | 高股息ETF | 中国神华、长江电力、工商银行等 |
| **通信/TMT** | 515880 | 通信ETF国泰 | 中际旭创、中兴通讯、新易盛等 |
| **互联网** | 159792 | 港股通互联网ETF富国 | 腾讯控股、阿里巴巴、美团等 |
| **港股科技** | 513180 | 恒生科技ETF华夏 | 小米集团、阿里巴巴、腾讯控股等 |
| **宽基指数** | 510300 | 沪深300ETF华泰柏瑞 | 贵州茅台、宁德时代、中国平安等 |
| **美股机器人** | BOTZ | Global X 机器人与人工智能 ETF | 美股机器人龙头 |
| **美股半导体** | SMH | VanEck 半导体 ETF | 英伟达、台积电、博通等 |
| **美股科技** | QQQ | 纳斯达克100 ETF | 苹果、微软、英伟达等 |
| **美股大盘** | SPY | 标普500 ETF | 美股大盘标杆 |
| **美股科技成长** | ARKK | ARK 创新 ETF | 创新科技成长股 |

> 配置入口：`etf_tracker/config.json` 的 `etfs` 数组。

### 2. 智能分层运行策略

为避免 28 只 ETF 全量多模型预测导致运行时间过长，系统采用分层策略：

1. **快速扫描**：对所有 28 只 ETF 进行 30/60/90/120/200/280/365 天回测和信号评分（命中本地缓存后约 **3 秒**）
2. **深度分析**：仅对评分前 N 的 ETF 运行 LightGBM/XGBoost/RF/ARIMA/LSTM 多模型预测
3. **LSTM 隔夜训练**：收盘后自动训练 LSTM，第二天早上直接加载缓存，不再重复训练
4. **成分股跟踪**：仅对重点 ETF 的 Top10 成分股进行 30 天收益和多模型预测
5. **机构研报**：自动扫描 `~/etf_tracker/research_reports/` 目录，提取评级、目标价、核心观点
6. **实时预警**：检测价格突破、异常波动、MACD 金叉死叉、RSI 超买超卖等信号
7. **自动生成**：板块排名表 + 重点板块深度分析 + 国际市场 + 投资建议汇总

### 3. 本地缓存与并行加速

- **本地 Parquet 缓存**：K 线数据按代码/类型缓存，1 天失效，盘中重复请求命中缓存
- **并行扫描**：ETF 快速扫描使用 `ThreadPoolExecutor(max_workers=8)`，IO 密集型任务并行
- **模型缓存**：LSTM 模型收盘后训练并保存到 `~/etf_tracker/models/`，次日复用
- **运行计时**：每个阶段耗时清晰记录，方便定位瓶颈

### 4. 多数据源管理

统一数据源管理器 `DataSourceManager` 集成 **5 大数据源**，支持优先级配置和自动故障转移：

| 数据源 | 用途 | 优先级 |
|--------|------|--------|
| **Yahoo Finance** | ETF/港股/美股/国际市场数据 | 1 |
| **AkShare** | A股日线/分钟线/资金流向/融资融券 | 2 |
| **东方财富** | ETF/股票 K线数据 | 3 |
| **Tushare** | 专业金融数据（需 token，免费权限有限） | 4 |
| **Baostock** | A股历史数据（稳定备用） | 5 |

配置入口：`etf_tracker/config.json` 的 `data_sources`。

### 5. 多模型交叉验证预测

`multi_model_predictor.py` 融合 **5 种模型**，构建 86+ 维特征，动态权重集成：

| 模型 | 特点 |
|------|------|
| **LightGBM** | 高效梯度提升，特征重要性可解释 |
| **XGBoost** | 高精度树模型 |
| **Random Forest** | 抗过拟合，稳定性强 |
| **LSTM** | CNN+BiLSTM+Attention+多时间窗口集成 |
| **ARIMA** | 时间序列基线模型 |

- 预测周期：1日 / 3日 / 5日
- 动态权重：按测试集 RMSE 自动分配
- 置信度评估：低置信度时建议观望
- **LSTM 隔夜训练**：收盘后训练，次日加载，避免早上重复训练耗时

### 6. 实时预警引擎

`alert_engine.py` 自动检测以下信号并生成 `info/warning/critical` 三级预警：

| 预警类型 | 触发条件 |
|----------|----------|
| 单日异常波动 | 日涨跌幅 ≥ 5% |
| 成交量异常 | 成交量 ≥ 2 倍 20 日均量 |
| RSI 超买/超卖 | RSI ≥ 70 或 ≤ 30 |
| MACD 金叉/死叉 | MACD 柱由负转正/正转负 |
| 突破/跌破 MA20 | 收盘价突破/跌破 MA20 2% |
| 突破/跌破 MA60 | 收盘价突破/跌破 MA60 2% |
| 高位回撤 | 从近20日高点回撤 ≥ 10% |

预警记录持久化到 SQLite，并汇总到报告和微信摘要。

### 7. 机构研报自动解析

`report_reader.py` + `report_scanner.py` 自动处理 `~/etf_tracker/research_reports/` 目录：

- 支持 **PDF 研报**（PyMuPDF / PyPDF2）
- 支持 **文本/网页** 研报
- 自动提取：标题、机构、评级、目标价、当前价、核心观点、风险提示
- 聚合多家观点，生成"机构研报观点"章节
- 微信摘要自动附带研报关键数据

**使用方式**：把券商研报 PDF 放到 `~/etf_tracker/research_reports/`，文件名建议包含代码，如 `600519_贵州茅台_中信证券.pdf`。

### 8. 国际市场扩展

`international_market.py` 跟踪约 **20 个国际品种**：

- 美股指数：标普500、纳斯达克100、道琼斯、罗素2000
- 港股：恒生指数、恒生科技指数
- 商品：黄金、白银、铂金、原油、天然气、伦铝、小麦、大豆、可可、铁矿石
- 外汇：美元指数、欧元/美元、美元/日元、英镑/美元、离岸人民币

生成"国际市场环境"章节，分析对 A 股的影响。

### 9. 技术指标与回测

- **RSI(14)** — 相对强弱指数
- **MACD** — 指数平滑异同平均线
- **KDJ** — 随机指标
- **布林带 (20,2)** — 判断价格位置
- **ATR(14)** — 平均真实波幅，用于仓位管理
- **均线系统** — 5/10/20/60日均线排列
- **成交量比率** — 量价配合分析
- **回测周期**：30/60/90/120/200/280/365 天
- **回测指标**：区间收益、年化波动率、最大回撤、夏普比率、日胜率、Calmar 比率

### 10. ETF Top10 成分股深度分析

为每个板块 ETF 配置 **Top10 成分股**，系统会对每只成分股进行：
- 技术指标分析
- 30天收益回测
- 多模型 1日预测
- 趋势判断
- **支持港股成分股**（通过 Yahoo Finance）

### 11. 可视化图表

自动生成多种专业图表：
- K线图（含均线、MACD、成交量）
- 资金流向趋势图
- 预测趋势图（含置信区间）
- 多股票综合仪表盘
- 板块资金流向图
- 板块排名对比图
- 背离检测图
- 收益率对比图
- 风险收益散点图
- 综合评分雷达图

### 12. 数据持久化

`data_persistence.py` 使用 SQLite 持久化：
- 历史行情数据
- 预测结果
- 预警记录
- 行业新闻

### 13. 微信自动推送

- **Hermes 微信通道**（主通道）
- **企业微信机器人**（备用通道）
- 报告摘要自动控制在 800-1200 字以内，避免频率限制
- 非交易日静默（`[SILENT]`）

---

## 🏆 核心优势

1. **全市场大型 ETF 覆盖**: 28 只市值 100 亿以上 ETF，覆盖 A 股/港股/美股主要热点板块
2. **ETF + 成分股联动**: 既分析板块 ETF 整体趋势，也深挖 Top10 成分股机会
3. **智能分层分析**: 快速扫描 + 前 N 深度分析，兼顾全面性和运行效率
4. **LSTM 隔夜训练**: 收盘后训练，次日复用，早上运行时间从 70 秒降到 1 秒以内
5. **多源数据冗余**: 5 大数据源自动故障转移，单一数据源失败不影响系统运行
6. **本地缓存加速**: Parquet 缓存 + 模型缓存，显著减少网络请求和训练时间
7. **港股/美股数据支持**: 通过 Yahoo Finance 支持港股、美股 ETF 及成分股分析
8. **多模型集成**: 5 种算法交叉验证，降低单一模型偏差，提升预测稳健性
9. **实时预警**: 7 类预警自动检测，及时发现价格突破和异常波动
10. **机构研报接入**: 自动读取本地券商研报，生成机构观点章节
11. **国际市场跟踪**: 20+ 国际品种，辅助判断 A 股外部环境
12. **全链路自动化**: 数据获取 → 分析 → 预测 → 可视化 → 报告 → 推送，无需人工干预
13. **可配置化设计**: 通过 `config.json` 自定义跟踪板块、ETF、Top10 个股、回测周期、数据源优先级
14. **模块化架构**: 数据、分析、预测、报告、推送各模块独立，易于扩展
15. **生产级部署**: 已通过 Hermes 定时任务每日自动运行

---

## 📁 项目结构

```
daily_tracker_analytics/
├── etf_tracker/
│   ├── etf_tracker.py              # 主程序（含多 ETF 分析引擎、报告生成）
│   ├── config.json                 # 配置文件（28 只 ETF + Top10 个股）
│   ├── data_source_manager.py      # 统一数据源管理器（5 源自动故障转移）
│   ├── data_cache.py               # 本地 Parquet 缓存模块
│   ├── multi_model_predictor.py    # 多模型预测系统（含 LSTM 缓存）
│   ├── lstm_model_cache.py         # LSTM 模型缓存管理器
│   ├── train_lstm_nightly.py       # LSTM 隔夜训练脚本
│   ├── alert_engine.py             # 实时预警引擎
│   ├── report_reader.py            # 研报解析器（PDF/文本）
│   ├── report_scanner.py           # 自动扫描研报目录
│   ├── international_market.py     # 国际市场数据模块
│   ├── stock_analyzer.py           # 个股深度分析
│   ├── advanced_predictor.py       # 趋势预测与预警
│   ├── industry_news_enhanced.py   # 行业新闻跟踪
│   ├── data_persistence.py         # SQLite 数据持久化
│   ├── hermes_wechat_pusher.py     # Hermes 微信推送
│   ├── wechat_pusher.py            # 企业微信机器人推送
│   ├── run_daily.sh                # 定时执行脚本
│   └── reports/                    # 生成的报告和图表
├── run_with_tf_venv.sh             # TensorFlow venv 运行包装脚本
├── DATA_SOURCES.md                 # 数据源配置文档
├── README.md                       # 本文件
└── .github/workflows/
    └── daily-etf-analysis.yml      # GitHub Actions 工作流
```

---

## 🔧 运行方式

### 方式一：使用 TensorFlow venv（推荐，支持 LSTM）

```bash
cd /home/zhihu/daily-_tracker_analytics
./run_with_tf_venv.sh
```

或直接：

```bash
cd /home/zhihu/daily-_tracker_analytics/etf_tracker
/home/zhihu/tf_venv/bin/python etf_tracker.py
```

运行后将生成：
- `reports/multi_etf_report_YYYYMMDD.md` — 多板块综合报告
- `reports/multi_model_prediction_YYYYMMDD.md` — 多模型预测报告
- 微信推送摘要（如果启用）

### 方式二：手动运行指定参数

```python
from etf_tracker import run_multi_etf_daily_report

# 深度分析前 3 名，不分析成分股
run_multi_etf_daily_report(deep_analysis_top_n=3, analyze_top_stocks=False, enable_wechat_push=True)
```

### 方式三：LSTM 隔夜训练（收盘后）

```bash
cd /home/zhihu/daily-_tracker_analytics/etf_tracker
/home/zhihu/tf_venv/bin/python train_lstm_nightly.py
```

训练结果保存到 `~/etf_tracker/models/<etf_code>/`，次日早报自动加载。

### 方式四：扫描本地研报

```bash
cd /home/zhihu/daily-_tracker_analytics/etf_tracker
/home/zhihu/tf_venv/bin/python report_scanner.py
```

自动读取 `~/etf_tracker/research_reports/` 下所有 PDF，生成 `research_summary_YYYYMMDD.md`。

### 方式五：GitHub Actions 自动运行

已配置 `.github/workflows/daily-etf-analysis.yml`，每天 UTC 10:00 自动运行。

---

## ⏰ 定时任务（Hermes cron）

已配置两个定时任务：

| 任务 | 执行时间 | 说明 |
|------|----------|------|
| 多板块 ETF 每日投资分析 | 工作日 UTC 08:00（北京 16:00） | 运行主程序，生成报告并微信推送 |
| LSTM 隔夜训练 | 工作日 UTC 07:30（北京 15:30） | 收盘后训练 LSTM，保存模型缓存 |

查看任务：

```bash
hermes cron list
```

---

## ⚙️ 环境要求

- Python 3.12（TensorFlow 2.21 需要）
- TensorFlow 2.21+
- LightGBM, XGBoost, scikit-learn
- pandas, numpy, matplotlib
- akshare, baostock, tushare, yfinance
- statsmodels, pymupdf

TensorFlow 环境已预装在 `/home/zhihu/tf_venv`。

快速安装缺失依赖：

```bash
/home/zhihu/tf_venv/bin/pip install pymupdf
```

---

## 📈 最新运行结果示例

**2026-07-01 多板块 ETF 快速扫描结果（前 5 名）**：

| 排名 | ETF | 主题 | 60天收益 | 综合评分 | 信号 |
|------|-----|------|----------|----------|------|
| 1 | 人工智能ETF易方达 | AI | +50.20% | 41.7 | bullish |
| 2 | 沪深300ETF华泰柏瑞 | 宽基指数 | +11.23% | 41.7 | bullish |
| 3 | 科创芯片ETF嘉实 | 芯片制造 | +110.18% | 25.0 | bullish |
| 4 | 半导体ETF | 晶圆制造 | +110.08% | 25.0 | bullish |
| 5 | 半导体设备ETF国泰 | 半导体设备 | +134.55% | 25.0 | bullish |

> 系统仅对前 N 名 ETF 运行多模型深度预测，详细结果见生成的报告。

---

## 📝 配置说明

编辑 `etf_tracker/config.json` 可自定义：

- `etfs`: 跟踪的 ETF 列表，每个 ETF 可配置 code/name/theme/sector/top_stocks
- `default_etf`: 默认主分析 ETF
- `backtest_periods`: 回测周期，如 `[30, 60, 90, 120, 200, 280, 365]`
- `data_sources`: 数据源优先级和启用状态
- `tracking_industries`: 跟踪的行业关键词
- `wechat_push.enabled`: 是否启用微信推送
- `features.multi_etf`: 是否启用多板块综合报告

### 添加新板块示例

```json
{
  "code": "512000",
  "name": "券商ETF",
  "theme": "券商",
  "sector": "非银金融",
  "leading_stocks": ["中信证券", "东方财富", "华泰证券"],
  "top_stocks": [
    {"code": "600030", "name": "中信证券", "reason": "券商龙头"},
    {"code": "300059", "name": "东方财富", "reason": "互联网券商"}
  ]
}
```

### 添加券商研报

把 PDF 文件放入 `~/etf_tracker/research_reports/`，文件名建议包含代码：

```bash
~/etf_tracker/research_reports/
├── 600519_贵州茅台_中信证券.pdf
├── 516150_稀土永磁_中金公司.pdf
├── 000858_五粮液_国泰君安.pdf
```

---

## 🤝 贡献与扩展

- 添加更多板块：在 `config.json` 的 `etfs` 数组中新增配置
- 添加更多数据源：实现 `DataSourceManager` 的数据源接口
- 添加更多模型：在 `multi_model_predictor.py` 中扩展模型
- 调整深度分析数量：修改 `run_multi_etf_daily_report` 的 `deep_analysis_top_n` 参数
- 调整预警阈值：修改 `alert_engine.py` 中的参数配置
- 接入更多研报来源：扩展 `report_reader.py` 的解析器

---

## ⚠️ 风险提示

本项目仅供研究和学习使用，不构成投资建议。金融市场有风险，投资需谨慎。模型预测结果存在不确定性，低置信度时应保持观望。机构研报观点仅供参考，可能存在滞后性或利益冲突。

---

**Maintainer**: ldw5821cn  
**GitHub**: https://github.com/ldw5821cn/daily_tracker_analytics
