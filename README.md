# 多板块 ETF 智能投资分析系统

> **核心能力**: 银行 / 消费 / CPU / AI / 晶圆制造 / 高股息 / 稀土永磁 等多板块 ETF 与 Top10 成分股跟踪预测  
> **投资主题**: 国产替代 + 稀土永磁 + 半导体产业链 + 高股息 + AI算力 + 大消费  
> **部署状态**: 已通过 Hermes 定时任务每日自动运行并推送微信报告

---

## 📊 项目简介

本项目是一个**多板块 ETF 量化投资分析系统**，支持同时跟踪多个行业/主题 ETF 及其 Top10 成分股，集成多数据源、多周期回测、多模型预测、个股深度分析、自动预警和微信推送能力，为投资决策提供数据驱动的支持。

系统每日自动运行，生成包含各板块 ETF 回测、技术指标、交易信号、行业动态、多模型预测、可视化图表、板块排名对比的投资规划报告，并通过 Hermes 微信通道推送到用户微信。

---

## 🚀 主要功能

### 1. 多板块 ETF 跟踪
支持配置化跟踪多个行业/主题 ETF：

| ETF 代码 | 名称 | 主题 | Top10 成分股 |
|----------|------|------|--------------|
| 516150 | 稀土ETF嘉实 | 稀土永磁 | 北方稀土、中国稀土、盛和资源等 |
| 512800 | 银行ETF | 银行 | 招商银行、工商银行、建设银行等 |
| 159928 | 消费ETF | 消费 | 贵州茅台、五粮液、伊利股份等 |
| 512760 | 芯片ETF | CPU/芯片 | 中芯国际、海光信息、寒武纪等 |
| 159819 | 人工智能ETF | AI | 寒武纪、海康威视、科大讯飞等 |
| 512480 | 半导体ETF | 晶圆制造 | 中芯国际、北方华创、中微公司等 |
| 563180 | 高股息ETF | 高股息 | 中国神华、长江电力、工商银行等 |

### 2. 多周期回测分析
- 支持 **30天 / 60天 / 90天** 多周期回测
- 计算核心指标：区间收益、年化波动率、最大回撤、夏普比率、日胜率、Calmar 比率
- 对比不同周期、不同板块的趋势一致性和信号强度

### 3. 多数据源管理
统一数据源管理器 `DataSourceManager` 集成 **5 大数据源**，支持优先级配置和自动故障转移：

| 数据源 | 用途 | 优先级 |
|--------|------|--------|
| **AkShare** | A股日线/分钟线/资金流向/融资融券 | 1 |
| **东方财富** | ETF/股票 K线数据 | 2 |
| **Tushare** | 专业金融数据（需 token） | 3 |
| **Baostock** | A股历史数据（稳定备用） | 4 |
| **Yahoo Finance** | 国际市场数据 | 5 |

### 4. 技术指标计算
- **RSI(14)** — 相对强弱指数
- **MACD** — 指数平滑异同平均线
- **KDJ** — 随机指标
- **布林带 (20,2)** — 判断价格位置
- **ATR(14)** — 平均真实波幅，用于仓位管理
- **均线系统** — 5/10/20/60日均线排列
- **成交量比率** — 量价配合分析

### 5. 多模型交叉验证预测
`multi_model_predictor.py` 融合 **6 种模型**，构建 81 维特征，动态权重集成：

| 模型 | 特点 |
|------|------|
| **LightGBM** | 高效梯度提升，特征重要性可解释 |
| **XGBoost** | 高精度树模型 |
| **Random Forest** | 抗过拟合，稳定性强 |
| **LSTM** | CNN+BiLSTM+Attention+多时间窗口集成 |
| **ARIMA** | 时间序列基线模型 |
| **Prophet** | 季节性趋势分析（可选） |

- 预测周期：1日 / 3日 / 5日
- 动态权重：按测试集 RMSE 自动分配
- 置信度评估：低置信度时建议观望

### 6. ETF Top10 成分股深度分析
为每个板块 ETF 配置 **Top10 成分股**，系统会对每只成分股进行：
- 技术指标分析
- 30天收益回测
- 多模型 1日预测
- 趋势判断

### 7. 板块排名对比
自动生成板块综合排名，维度包括：
- 60天收益
- 60天夏普比率
- 综合评分
- 1日预测收益
- 预测置信度

### 8. 行业动态跟踪
`industry_news_enhanced.py` 自动跟踪以下热点行业：
- 银行 / 消费 / 高股息
- CPU / AI / 人工智能
- 晶圆制造 / 芯片制造
- 稀土永磁 / 半导体
- 机器人 / 存储行业 / 内存制造

支持情感分析和关键词提取。

### 9. 自动预警系统
自动检测以下信号并生成预警：
- RSI > 70（超买） 或 RSI < 30（超卖）
- 综合评分 > 80
- 30天涨幅 > 50%（短期暴涨）
- 30天跌幅 > 20%（短期暴跌）
- 布林带突破
- MACD 金叉/死叉

### 10. 可视化图表
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

### 11. 数据持久化
`data_persistence.py` 使用 SQLite 持久化：
- 历史行情数据
- 预测结果
- 预警记录
- 行业新闻

### 12. 微信自动推送
- **Hermes 微信通道**（主通道）
- **企业微信机器人**（备用通道）
- 报告摘要自动控制在 800-1200 字以内，避免频率限制
- 非交易日静默（[SILENT]）

---

## 🏆 核心优势

1. **多板块覆盖**: 不仅限于稀土，同时覆盖银行、消费、CPU、AI、晶圆制造、高股息等热门板块
2. **ETF + 成分股联动**: 既分析板块 ETF 整体趋势，也深挖 Top10 成分股机会
3. **多源数据冗余**: 5 大数据源自动故障转移，单一数据源失败不影响系统运行
4. **多模型集成**: 6 种算法交叉验证，降低单一模型偏差，提升预测稳健性
5. **深度学习增强**: CNN+BiLSTM+Attention LSTM 捕捉复杂时序模式
6. **板块轮动洞察**: 自动排名对比，帮助识别强势板块
7. **全链路自动化**: 数据获取 → 分析 → 预测 → 可视化 → 报告 → 推送，无需人工干预
8. **可配置化设计**: 通过 `config.json` 自定义跟踪板块、ETF、Top10 个股、回测周期、数据源优先级
9. **模块化架构**: 数据、分析、预测、报告、推送各模块独立，易于扩展
10. **生产级部署**: 已通过 Hermes 定时任务每日自动运行

---

## 📁 项目结构

```
daily_tracker_analytics/
├── etf_tracker/
│   ├── etf_tracker.py              # 主程序（含多 ETF 分析引擎）
│   ├── config.json                 # 配置文件（多板块 ETF + Top10 个股）
│   ├── data_source_manager.py      # 统一数据源管理器
│   ├── multi_model_predictor.py    # 多模型预测系统
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

### 方式二：GitHub Actions 自动运行

已配置 `.github/workflows/daily-etf-analysis.yml`，每天 UTC 10:00 自动运行。

---

## ⚙️ 环境要求

- Python 3.12（TensorFlow 2.21 需要）
- TensorFlow 2.21+
- LightGBM, XGBoost, scikit-learn
- pandas, numpy, matplotlib
- akshare, baostock, tushare, yfinance
- statsmodels

TensorFlow 环境已预装在 `/home/zhihu/tf_venv`。

---

## 📈 最新运行结果示例

**2026-06-30 多板块 ETF 多模型预测结果：**

| ETF | 主题 | 1日预测 | 置信度 | 建议 |
|-----|------|---------|--------|------|
| 稀土ETF嘉实 | 稀土永磁 | -0.12% | 29.1% | 观望 |
| 银行ETF | 银行 | 待运行 | — | — |
| 消费ETF | 消费 | 待运行 | — | — |
| 芯片ETF | CPU/芯片 | 待运行 | — | — |
| 人工智能ETF | AI | 待运行 | — | — |
| 半导体ETF | 晶圆制造 | 待运行 | — | — |
| 高股息ETF | 高股息 | 待运行 | — | — |

> 低置信度表明市场方向不明，建议观望。

---

## 📝 配置说明

编辑 `etf_tracker/config.json` 可自定义：

- `etfs`: 跟踪的 ETF 列表，每个 ETF 可配置 code/name/theme/sector/top_stocks
- `default_etf`: 默认主分析 ETF
- `backtest_periods`: 回测周期，如 `[30, 60, 90]`
- `data_sources`: 数据源优先级和启用状态
- `tracking_industries`: 跟踪的行业关键词
- `wechat_push.enabled`: 是否启用微信推送

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

---

## 🤝 贡献与扩展

- 添加更多板块：在 `config.json` 的 `etfs` 数组中新增配置
- 添加更多数据源：实现 `DataSourceManager` 的数据源接口
- 添加更多模型：在 `multi_model_predictor.py` 中扩展模型
- 优化 LSTM：调整窗口大小、网络层数、注意力头数

---

## ⚠️ 风险提示

本项目仅供研究和学习使用，不构成投资建议。金融市场有风险，投资需谨慎。模型预测结果存在不确定性，低置信度时应保持观望。

---

**Maintainer**: ldw5821cn  
**GitHub**: https://github.com/ldw5821cn/daily_tracker_analytics
