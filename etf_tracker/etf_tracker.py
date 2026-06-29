#!/usr/bin/env python3
"""
ETF 趋势跟踪与投资规划报告系统
支持配置化：可自定义跟踪的 ETF/股票、回测周期、数据源
"""

import os
import json
import urllib.request
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# 尝试导入同花顺 iFinD 数据接口
try:
    from iFinDPy import *
    IFIND_AVAILABLE = True
except ImportError:
    IFIND_AVAILABLE = False

# 尝试使用 yfinance 作为备用
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# 尝试使用 akshare 作为备用（A股数据最丰富）
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False


# ============ 配置加载 ============

class Config:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        "etf_code": "516150",
        "etf_name": "稀土ETF嘉实",
        "tracking_industries": ["机器人", "人工智能", "AI", "芯片制造", "存储行业", "内存制造"],
        "backtest_periods": [30, 60, 90],
        "data_source": "akshare",
        "wechat_push": {
            "enabled": True,
            "channel": "hermes"
        },
        "features": {
            "minute_data": True,
            "fund_flow": True,
            "sector_comparison": True,
            "margin_trading": True
        },
        "sector_comparison": {
            "enabled": True,
            "sector_name": "稀土永磁",
            "leading_stocks": ["北方稀土", "中国稀土", "盛和资源", "广晟有色", "厦门钨业"]
        }
    }
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.json")
        self.config = self._load_config()
        
        # 提取常用配置
        self.etf_code = self.config.get("etf_code", "516150")
        self.etf_name = self.config.get("etf_name", "稀土ETF嘉实")
        self.tracking_industries = self.config.get("tracking_industries", [])
        self.backtest_periods = self.config.get("backtest_periods", [30, 60, 90])
        self.data_source = self.config.get("data_source", "akshare")
        self.features = self.config.get("features", {})
        self.sector_config = self.config.get("sector_comparison", {})
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 读取配置失败: {e}，使用默认配置")
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def update(self, key: str, value):
        """更新配置项"""
        self.config[key] = value
        # 更新实例属性
        if hasattr(self, key):
            setattr(self, key, value)


# ============ 数据获取模块 ============

class ETFDataFetcher:
    """ETF 历史数据获取器 - 支持多数据源"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
    
    @staticmethod
    def get_kline_data_from_akshare(etf_code: str, days: int = 120) -> pd.DataFrame:
        """使用 AkShare 获取 ETF K线数据（A股专用，数据最丰富）"""
        import akshare as ak
        
        start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
        
        print(f"  📡 正在从 AkShare 获取 {etf_code} 数据...")
        
        df = ak.fund_etf_hist_em(symbol=etf_code, period="daily", 
                                  start_date=start_date, adjust="qfq")
        
        if len(df) == 0:
            raise ValueError("AkShare 返回空数据")
        
        df = df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount'
        })
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        if len(df) > days:
            df = df.tail(days).reset_index(drop=True)
        
        print(f"  ✅ AkShare 数据获取成功: {len(df)} 条")
        return df
    
    @staticmethod
    def get_minute_data_from_akshare(etf_code: str, period: str = "1", days: int = 5) -> pd.DataFrame:
        """使用 AkShare 获取 ETF 分钟级数据（用于高频回测）"""
        import akshare as ak
        
        print(f"  📡 正在从 AkShare 获取 {etf_code} {period}分钟数据...")
        
        df = ak.fund_etf_hist_min_em(symbol=etf_code, period=period, adjust="qfq")
        
        if len(df) == 0:
            raise ValueError("AkShare 返回空数据")
        
        df = df.rename(columns={
            '时间': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount'
        })
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # 截取最近N天
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df['date'] >= cutoff_date].reset_index(drop=True)
        
        print(f"  ✅ AkShare 分钟数据获取成功: {len(df)} 条")
        return df
    
    @staticmethod
    def get_fund_flow_from_akshare(etf_code: str, market: str = "sh") -> pd.DataFrame:
        """使用 AkShare 获取 ETF 资金流向数据"""
        import akshare as ak
        
        print(f"  📡 正在从 AkShare 获取 {etf_code} 资金流向...")
        
        # 获取资金流向
        df = ak.stock_individual_fund_flow(symbol=etf_code, market=market)
        
        if len(df) == 0:
            raise ValueError("AkShare 返回空数据")
        
        print(f"  ✅ AkShare 资金流向获取成功: {len(df)} 条")
        return df
    
    @staticmethod
    def get_margin_trading_from_akshare(etf_code: str) -> pd.DataFrame:
        """使用 AkShare 获取融资融券数据"""
        import akshare as ak
        
        print(f"  📡 正在从 AkShare 获取 {etf_code} 融资融券数据...")
        
        # 获取融资融券数据
        df = ak.stock_margin_detail_em(symbol=etf_code)
        
        if len(df) == 0:
            raise ValueError("AkShare 返回空数据")
        
        print(f"  ✅ AkShare 融资融券数据获取成功: {len(df)} 条")
        return df
    
    @staticmethod
    def get_sector_data_from_akshare(sector_name: str = "稀土永磁") -> pd.DataFrame:
        """使用 AkShare 获取行业板块数据"""
        import akshare as ak
        
        print(f"  📡 正在从 AkShare 获取 {sector_name} 板块数据...")
        
        # 获取行业板块成分股
        df = ak.stock_board_industry_name_em()
        
        # 查找相关板块
        sector_df = df[df['板块名称'].str.contains(sector_name.replace('永磁', ''), na=False)]
        
        print(f"  ✅ AkShare 板块数据获取成功: {len(sector_df)} 个相关板块")
        return sector_df
    
    @staticmethod
    def get_stock_kline_from_akshare(stock_code: str, days: int = 120) -> pd.DataFrame:
        """使用 AkShare 获取个股K线数据（用于板块对比）"""
        import akshare as ak
        
        start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
        
        print(f"  📡 正在从 AkShare 获取 {stock_code} 个股数据...")
        
        # 判断市场
        if stock_code.startswith('6'):
            market = "sh"
        else:
            market = "sz"
        
        df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                 start_date=start_date, adjust="qfq")
        
        if len(df) == 0:
            raise ValueError("AkShare 返回空数据")
        
        df = df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount'
        })
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        if len(df) > days:
            df = df.tail(days).reset_index(drop=True)
        
        print(f"  ✅ AkShare 个股数据获取成功: {len(df)} 条")
        return df
    
    @staticmethod
    def get_kline_data_eastmoney(secid: str, days: int = 120) -> pd.DataFrame:
        """使用东方财富获取 ETF K线数据（备用）"""
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&end=20500101&lmt={days}"
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://quote.eastmoney.com/'
                })
                resp = urllib.request.urlopen(req, timeout=15)
                data = json.loads(resp.read().decode('utf-8'))
                
                klines = data['data']['klines']
                records = []
                for line in klines:
                    parts = line.split(',')
                    records.append({
                        'date': parts[0],
                        'open': float(parts[1]),
                        'close': float(parts[2]),
                        'high': float(parts[3]),
                        'low': float(parts[4]),
                        'volume': int(parts[5]),
                        'amount': float(parts[6])
                    })
                
                df = pd.DataFrame(records)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
                return df
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠️ 第 {attempt + 1} 次尝试失败，重试中...")
                    time.sleep(2)
                else:
                    raise e
    
    @staticmethod
    def get_kline_data_from_ifind(etf_code: str, days: int = 120) -> pd.DataFrame:
        """使用本地 CSV 作为回退"""
        history_file = f"/home/zhihu/etf_tracker/{etf_code}_history.csv"
        if os.path.exists(history_file):
            df = pd.read_csv(history_file)
            df['date'] = pd.to_datetime(df['date'])
            if len(df) >= days:
                return df.tail(days).reset_index(drop=True)
            else:
                return df
        else:
            raise FileNotFoundError(f"历史数据文件不存在: {history_file}")
    
    def get_kline_data(self, etf_code: str, days: int = 120) -> pd.DataFrame:
        """获取 ETF K线数据 - 多数据源优先级策略"""
        
        # 1. 优先使用 AkShare（A股数据最丰富）
        if 'AKSHARE_AVAILABLE' in globals() and AKSHARE_AVAILABLE:
            try:
                df = ETFDataFetcher.get_kline_data_from_akshare(etf_code, days)
                return df
            except Exception as e:
                print(f"  ⚠️ AkShare 获取失败: {e}")
        
        # 2. 备用：东方财富 API
        try:
            print(f"  📡 正在从东方财富获取 {etf_code} 数据...")
            secid = f"1.{etf_code}"  # 1=上海, 0=深圳
            df = ETFDataFetcher.get_kline_data_eastmoney(secid, days)
            print(f"  ✅ 东方财富数据获取成功: {len(df)} 条")
            return df
        except Exception as e:
            print(f"  ⚠️ 东方财富获取失败: {e}")
        
        # 3. 尝试使用本地 CSV 缓存
        try:
            print(f"  📂 尝试使用本地 CSV 缓存...")
            df = ETFDataFetcher.get_kline_data_from_ifind(etf_code, days)
            print(f"  ✅ 本地 CSV 数据获取成功: {len(df)} 条")
            return df
        except Exception as e:
            print(f"  ⚠️ 本地 CSV 获取失败: {e}")
        
        # 4. 尝试使用 yfinance（国际数据源）
        if 'YFINANCE_AVAILABLE' in globals() and YFINANCE_AVAILABLE:
            try:
                print(f"  📡 正在从 yfinance 获取 {etf_code}.SS 数据...")
                import yfinance as yf
                ticker = yf.Ticker(f"{etf_code}.SS")
                df = ticker.history(period="6mo")
                if len(df) >= days:
                    df = df.tail(days).reset_index(drop=True)
                df = df.rename(columns={
                    'Open': 'open', 'Close': 'close', 'High': 'high', 
                    'Low': 'low', 'Volume': 'volume'
                })
                df['date'] = df.index
                df['amount'] = df['volume'] * df['close']
                print(f"  ✅ yfinance 数据获取成功: {len(df)} 条")
                return df
            except Exception as e:
                print(f"  ⚠️ yfinance 获取失败: {e}")
        
        # 5. 所有数据源失败
        raise FileNotFoundError(f"所有数据源均失败，请检查网络连接或手动提供数据")


# ============ 技术指标模块 ============

class TechnicalIndicators:
    """技术指标计算"""
    
    @staticmethod
    def ma(df: pd.DataFrame, period: int) -> pd.Series:
        """简单移动平均线"""
        return df['close'].rolling(window=period).mean()
    
    @staticmethod
    def ema(df: pd.DataFrame, period: int) -> pd.Series:
        """指数移动平均线"""
        return df['close'].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """相对强弱指数 RSI"""
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD 指标"""
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """布林带"""
        ma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        upper = ma + (std * std_dev)
        lower = ma - (std * std_dev)
        return upper, ma, lower
    
    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """平均真实波幅 ATR"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    @staticmethod
    def volume_ma(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """成交量均线"""
        return df['volume'].rolling(window=period).mean()
    
    @staticmethod
    def kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """KDJ 随机指标"""
        low_list = df['low'].rolling(window=n, min_periods=n).min()
        high_list = df['high'].rolling(window=n, min_periods=n).max()
        rsv = (df['close'] - low_list) / (high_list - low_list) * 100
        k = rsv.ewm(com=m1-1, adjust=False).mean()
        d = k.ewm(com=m2-1, adjust=False).mean()
        j = 3 * k - 2 * d
        return k, d, j


# ============ 回测模块 ============

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        """计算所有技术指标"""
        ti = TechnicalIndicators()
        self.df['ma5'] = ti.ma(self.df, 5)
        self.df['ma10'] = ti.ma(self.df, 10)
        self.df['ma20'] = ti.ma(self.df, 20)
        self.df['ma60'] = ti.ma(self.df, 60)
        self.df['rsi14'] = ti.rsi(self.df, 14)
        self.df['macd'], self.df['macd_signal'], self.df['macd_hist'] = ti.macd(self.df)
        self.df['bb_upper'], self.df['bb_middle'], self.df['bb_lower'] = ti.bollinger_bands(self.df)
        self.df['atr14'] = ti.atr(self.df, 14)
        self.df['vol_ma20'] = ti.volume_ma(self.df, 20)
        self.df['k'], self.df['d'], self.df['j'] = ti.kdj(self.df)
    
    def backtest_period(self, days: int) -> Dict:
        """回测指定周期"""
        if len(self.df) < days:
            return {"error": f"数据不足{days}天"}
        
        recent = self.df.tail(days).copy()
        
        # 基础统计
        start_price = recent.iloc[0]['close']
        end_price = recent.iloc[-1]['close']
        total_return = (end_price - start_price) / start_price * 100
        
        # 波动率
        daily_returns = recent['close'].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        
        # 最大回撤
        cumulative = (1 + daily_returns).cumprod()
        peak = cumulative.expanding().max()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min() * 100
        
        # 夏普比率 (假设无风险利率 2%)
        excess_return = daily_returns.mean() * 252 - 0.02
        sharpe = excess_return / (daily_returns.std() * np.sqrt(252)) if daily_returns.std() != 0 else 0
        
        # 胜率
        win_rate = (daily_returns > 0).sum() / len(daily_returns) * 100
        
        # 技术指标状态
        latest = recent.iloc[-1]
        
        # 均线排列
        ma_bull = latest['close'] > latest['ma5'] > latest['ma10'] > latest['ma20']
        ma_bear = latest['close'] < latest['ma5'] < latest['ma10'] < latest['ma20']
        
        # RSI 状态
        rsi_value = latest['rsi14']
        rsi_status = "超买" if rsi_value > 70 else "超卖" if rsi_value < 30 else "中性"
        
        # MACD 状态
        macd_bull = latest['macd'] > latest['macd_signal'] and latest['macd_hist'] > 0
        macd_bear = latest['macd'] < latest['macd_signal'] and latest['macd_hist'] < 0
        
        # 布林带位置
        bb_position = (latest['close'] - latest['bb_lower']) / (latest['bb_upper'] - latest['bb_lower'])
        
        # KDJ
        kdj_signal = "超买" if latest['j'] > 80 else "超卖" if latest['j'] < 20 else "中性"
        
        return {
            "period_days": days,
            "start_date": recent.iloc[0]['date'].strftime('%Y-%m-%d'),
            "end_date": recent.iloc[-1]['date'].strftime('%Y-%m-%d'),
            "start_price": round(start_price, 3),
            "end_price": round(end_price, 3),
            "total_return": round(total_return, 2),
            "volatility": round(volatility, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe, 3),
            "win_rate": round(win_rate, 2),
            "avg_volume": int(recent['volume'].mean()),
            "latest_rsi": round(rsi_value, 2),
            "rsi_status": rsi_status,
            "macd_signal": "bullish" if macd_bull else "bearish" if macd_bear else "neutral",
            "ma_trend": "多头排列" if ma_bull else "空头排列" if ma_bear else "震荡",
            "bb_position": round(bb_position, 3),
            "atr14": round(latest['atr14'], 3),
            "volume_ratio": round(latest['volume'] / latest['vol_ma20'], 2) if latest['vol_ma20'] > 0 else 0,
            "kdj_j": round(latest['j'], 2),
            "kdj_signal": kdj_signal
        }
    
    def run_all_backtests(self, periods: List[int] = None) -> List[Dict]:
        """运行所有周期回测"""
        results = []
        for days in (periods or [30, 60, 90]):
            result = self.backtest_period(days)
            results.append(result)
        return results


# ============ 资金流向分析模块 ============

class FundFlowAnalyzer:
    """资金流向分析器"""
    
    @staticmethod
    def analyze_fund_flow(etf_code: str) -> Dict:
        """分析资金流向"""
        try:
            import akshare as ak
            
            # 获取近5日资金流向
            df = ak.stock_individual_fund_flow(symbol=etf_code, market="sh")
            
            if len(df) == 0:
                return {"error": "无资金流向数据"}
            
            # 计算汇总
            latest = df.iloc[0]
            
            # 主力净流入（超大单+大单）
            main_inflow = float(latest['主力净流入-净额']) if '主力净流入-净额' in latest else 0
            
            # 散户净流入（中单+小单）
            retail_inflow = float(latest['小单净流入-净额']) if '小单净流入-净额' in latest else 0
            
            # 净流入占比
            total_amount = float(latest['成交额']) if '成交额' in latest else 1
            main_inflow_ratio = main_inflow / total_amount * 100 if total_amount > 0 else 0
            
            return {
                "date": latest['日期'] if '日期' in latest else "",
                "main_inflow": round(main_inflow / 10000, 2),  # 万元
                "retail_inflow": round(retail_inflow / 10000, 2),
                "main_inflow_ratio": round(main_inflow_ratio, 2),
                "signal": "主力流入" if main_inflow > 0 else "主力流出",
                "strength": "强" if abs(main_inflow_ratio) > 5 else "中" if abs(main_inflow_ratio) > 2 else "弱"
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def analyze_margin_trading(etf_code: str) -> Dict:
        """分析融资融券数据"""
        try:
            import akshare as ak
            
            df = ak.stock_margin_detail_em(symbol=etf_code)
            
            if len(df) == 0:
                return {"error": "无融资融券数据"}
            
            latest = df.iloc[0]
            
            # 融资余额
            rz_balance = float(latest['融资余额']) if '融资余额' in latest else 0
            # 融券余额
            rq_balance = float(latest['融券余额']) if '融券余额' in latest else 0
            # 融资融券余额
            total_balance = rz_balance + rq_balance
            
            # 杠杆多空比
            leverage_ratio = rz_balance / rq_balance if rq_balance > 0 else 0
            
            return {
                "date": latest['日期'] if '日期' in latest else "",
                "rz_balance": round(rz_balance / 10000, 2),  # 万元
                "rq_balance": round(rq_balance / 10000, 2),
                "total_balance": round(total_balance / 10000, 2),
                "leverage_ratio": round(leverage_ratio, 2),
                "signal": "融资增加" if rz_balance > 0 else "融资减少",
                "sentiment": "看多" if leverage_ratio > 10 else "中性" if leverage_ratio > 5 else "谨慎"
            }
        except Exception as e:
            return {"error": str(e)}


# ============ 板块对比模块 ============

class SectorComparison:
    """板块对比分析器"""
    
    @staticmethod
    def get_sector_leaders_performance(sector_config: dict) -> List[Dict]:
        """获取板块龙头股表现"""
        try:
            import akshare as ak
            
            results = []
            leading_stocks = sector_config.get("leading_stocks", [])
            
            # 获取股票代码映射（简化版，实际需要查询）
            stock_mapping = {
                "北方稀土": "600111",
                "中国稀土": "000831",
                "盛和资源": "600392",
                "广晟有色": "600259",
                "厦门钨业": "600549"
            }
            
            for stock_name in leading_stocks:
                stock_code = stock_mapping.get(stock_name)
                if not stock_code:
                    continue
                
                try:
                    # 获取个股数据
                    df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                           start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
                                           adjust="qfq")
                    
                    if len(df) > 0:
                        latest = df.iloc[-1]
                        first = df.iloc[0]
                        
                        return_pct = (float(latest['收盘']) - float(first['收盘'])) / float(first['收盘']) * 100
                        
                        results.append({
                            "name": stock_name,
                            "code": stock_code,
                            "latest_price": round(float(latest['收盘']), 2),
                            "return_30d": round(return_pct, 2),
                            "volume": int(latest['成交量']),
                            "trend": "上涨" if return_pct > 0 else "下跌"
                        })
                except Exception as e:
                    print(f"  ⚠️ 获取 {stock_name} 数据失败: {e}")
                    continue
            
            return results
        except Exception as e:
            return [{"error": str(e)}]
    
    @staticmethod
    def compare_with_etf(etf_code: str, sector_leaders: List[Dict]) -> Dict:
        """对比 ETF 与板块龙头股"""
        try:
            import akshare as ak
            
            # 获取 ETF 同期表现
            df = ak.fund_etf_hist_em(symbol=etf_code, period="daily", 
                                      start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
                                      adjust="qfq")
            
            if len(df) > 0:
                latest = df.iloc[-1]
                first = df.iloc[0]
                etf_return = (float(latest['收盘']) - float(first['收盘'])) / float(first['收盘']) * 100
                
                # 计算平均跑赢/跑输
                leader_returns = [s['return_30d'] for s in sector_leaders if 'return_30d' in s]
                avg_leader_return = sum(leader_returns) / len(leader_returns) if leader_returns else 0
                
                return {
                    "etf_return_30d": round(etf_return, 2),
                    "avg_leader_return": round(avg_leader_return, 2),
                    "outperform": round(etf_return - avg_leader_return, 2),
                    "conclusion": "ETF跑赢板块" if etf_return > avg_leader_return else "ETF跑输板块"
                }
            
            return {"error": "无ETF数据"}
        except Exception as e:
            return {"error": str(e)}


# ============ 信号生成模块 ============

class SignalGenerator:
    """交易信号生成器"""
    
    def __init__(self, backtest_results: List[Dict], df: pd.DataFrame, 
                 fund_flow: Dict = None, margin_data: Dict = None):
        self.results = backtest_results
        self.df = df
        self.fund_flow = fund_flow or {}
        self.margin_data = margin_data or {}
        self.latest = df.iloc[-1]
        self._ensure_indicators()
    
    def _ensure_indicators(self):
        """确保技术指标已计算"""
        ti = TechnicalIndicators()
        if 'rsi14' not in self.df.columns:
            self.df['rsi14'] = ti.rsi(self.df, 14)
        if 'macd' not in self.df.columns:
            self.df['macd'], self.df['macd_signal'], self.df['macd_hist'] = ti.macd(self.df)
        if 'ma5' not in self.df.columns:
            self.df['ma5'] = ti.ma(self.df, 5)
            self.df['ma10'] = ti.ma(self.df, 10)
            self.df['ma20'] = ti.ma(self.df, 20)
        if 'bb_upper' not in self.df.columns:
            self.df['bb_upper'], self.df['bb_middle'], self.df['bb_lower'] = ti.bollinger_bands(self.df)
        if 'atr14' not in self.df.columns:
            self.df['atr14'] = ti.atr(self.df, 14)
        if 'vol_ma20' not in self.df.columns:
            self.df['vol_ma20'] = ti.volume_ma(self.df, 20)
        if 'j' not in self.df.columns:
            self.df['k'], self.df['d'], self.df['j'] = ti.kdj(self.df)
        self.latest = self.df.iloc[-1]
    
    def generate_signals(self) -> Dict:
        """生成综合交易信号"""
        signals = []
        score = 0
        max_score = 0
        
        # 1. 多周期趋势一致性
        returns = [r['total_return'] for r in self.results if 'total_return' in r]
        if all(r > 0 for r in returns):
            signals.append("✅ 多周期趋势一致向上（30/60/90天均上涨）")
            score += 3
        elif all(r < 0 for r in returns):
            signals.append("❌ 多周期趋势一致向下")
            score -= 3
        else:
            signals.append("⚠️ 多周期趋势分化，需观望")
        max_score += 3
        
        # 2. RSI 信号
        rsi = self.latest['rsi14']
        if rsi < 30:
            signals.append(f"✅ RSI 超卖 ({rsi:.1f})，潜在反弹机会")
            score += 2
        elif rsi > 70:
            signals.append(f"❌ RSI 超买 ({rsi:.1f})，注意回调风险")
            score -= 2
        else:
            signals.append(f"📊 RSI 中性 ({rsi:.1f})")
        max_score += 2
        
        # 3. MACD 信号
        macd = self.latest['macd']
        macd_sig = self.latest['macd_signal']
        macd_hist = self.latest['macd_hist']
        if macd > macd_sig and macd_hist > 0:
            signals.append("✅ MACD 金叉且柱状图向上，动能强劲")
            score += 2
        elif macd < macd_sig and macd_hist < 0:
            signals.append("❌ MACD 死叉且柱状图向下，动能减弱")
            score -= 2
        else:
            signals.append("📊 MACD 方向不明")
        max_score += 2
        
        # 4. 均线排列
        close = self.latest['close']
        ma5 = self.latest['ma5']
        ma10 = self.latest['ma10']
        ma20 = self.latest['ma20']
        if close > ma5 > ma10 > ma20:
            signals.append("✅ 均线多头排列，趋势健康")
            score += 2
        elif close < ma5 < ma10 < ma20:
            signals.append("❌ 均线空头排列，趋势走弱")
            score -= 2
        else:
            signals.append("📊 均线纠缠，趋势不明")
        max_score += 2
        
        # 5. 布林带位置
        bb_pos = (close - self.latest['bb_lower']) / (self.latest['bb_upper'] - self.latest['bb_lower'])
        if bb_pos > 0.8:
            signals.append("⚠️ 价格接近布林带上轨，注意压力")
            score -= 1
        elif bb_pos < 0.2:
            signals.append("✅ 价格接近布林带下轨，潜在支撑")
            score += 1
        else:
            signals.append("📊 价格位于布林带中位")
        max_score += 1
        
        # 6. 成交量
        vol_ratio = self.latest['volume'] / self.latest['vol_ma20'] if self.latest['vol_ma20'] > 0 else 0
        if vol_ratio > 1.5:
            signals.append(f"✅ 成交量放大 ({vol_ratio:.1f}x)，资金活跃")
            score += 1
        elif vol_ratio < 0.5:
            signals.append(f"❌ 成交量萎缩 ({vol_ratio:.1f}x)，参与度低")
            score -= 1
        else:
            signals.append(f"📊 成交量正常 ({vol_ratio:.1f}x)")
        max_score += 1
        
        # 7. KDJ 信号
        j_value = self.latest['j']
        if j_value < 20:
            signals.append(f"✅ KDJ J值超卖 ({j_value:.1f})")
            score += 1
        elif j_value > 80:
            signals.append(f"❌ KDJ J值超买 ({j_value:.1f})")
            score -= 1
        else:
            signals.append(f"📊 KDJ J值中性 ({j_value:.1f})")
        max_score += 1
        
        # 8. 资金流向（如果有）
        if self.fund_flow and 'main_inflow' in self.fund_flow:
            main_inflow = self.fund_flow['main_inflow']
            if main_inflow > 0:
                signals.append(f"✅ 主力资金净流入 {main_inflow}万元")
                score += 1
            else:
                signals.append(f"❌ 主力资金净流出 {abs(main_inflow)}万元")
                score -= 1
            max_score += 1
        
        # 9. 融资融券（如果有）
        if self.margin_data and 'leverage_ratio' in self.margin_data:
            leverage = self.margin_data['leverage_ratio']
            if leverage > 10:
                signals.append(f"✅ 融资杠杆高 ({leverage:.1f}x)，市场情绪乐观")
                score += 1
            elif leverage < 5:
                signals.append(f"⚠️ 融资杠杆低 ({leverage:.1f}x)，市场情绪谨慎")
            max_score += 1
        
        # 综合评分
        normalized_score = (score / max_score * 100) if max_score > 0 else 0
        
        if normalized_score >= 60:
            overall = "bullish"
            action = "建议关注买入机会"
        elif normalized_score <= -40:
            overall = "bearish"
            action = "建议减仓或观望"
        else:
            overall = "neutral"
            action = "建议持仓观望，等待明确信号"
        
        return {
            "signals": signals,
            "score": round(normalized_score, 1),
            "overall": overall,
            "action": action
        }
    
    def calculate_position_sizing(self) -> Dict:
        """计算仓位建议"""
        atr = self.latest['atr14']
        close = self.latest['close']
        
        risk_per_trade = 0.02
        stop_loss = 2 * atr
        
        position_size = risk_per_trade / (stop_loss / close) * 100
        position_size = min(position_size, 100)
        
        return {
            "suggested_position": f"{position_size:.1f}%",
            "stop_loss": round(close - stop_loss, 3),
            "take_profit_1": round(close + 2 * atr, 3),
            "take_profit_2": round(close + 3 * atr, 3),
            "risk_reward_ratio": "1:2 ~ 1:3"
        }


# ============ 报告生成模块 ============

class ReportGenerator:
    """投资规划报告生成器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.etf_code = config.etf_code
        self.etf_name = config.etf_name
        self.date = datetime.now().strftime('%Y-%m-%d')
    
    def generate_report(self, backtest_results: List[Dict], signals: Dict, 
                       position: Dict, df: pd.DataFrame, 
                       fund_flow: Dict = None, margin_data: Dict = None,
                       sector_comparison: Dict = None,
                       industry_news: str = "") -> str:
        """生成完整的投资规划报告"""
        
        latest = df.iloc[-1]
        
        report = f"""# 📊 {self.etf_name} ({self.etf_code}) 投资规划报告

> **报告日期**: {self.date}  
> **数据来源**: AkShare + 东方财富  
> **分析周期**: {'/'.join([str(p) for p in self.config.backtest_periods])}天滚动回测

---

## 一、ETF 基本信息

| 项目 | 内容 |
|------|------|
| 基金名称 | {self.etf_name} |
| 基金代码 | {self.etf_code} |
| 最新净值 | {latest['close']:.3f} |
| 今日开盘 | {latest['open']:.3f} |
| 今日最高 | {latest['high']:.3f} |
| 今日最低 | {latest['low']:.3f} |
| 成交量 | {latest['volume']:,} |
| 成交额 | {latest['amount']:,.0f} |

---

## 二、多周期回测分析

"""
        
        for result in backtest_results:
            report += f"""### 📈 {result['period_days']}天回测 ({result['start_date']} ~ {result['end_date']})

| 指标 | 数值 | 评价 |
|------|------|------|
| 区间收益 | {result['total_return']:+.2f}% | {'✅ 上涨' if result['total_return'] > 0 else '❌ 下跌'} |
| 年化波动率 | {result['volatility']:.2f}% | {'⚠️ 高波动' if result['volatility'] > 30 else '📊 中等波动' if result['volatility'] > 20 else '✅ 低波动'} |
| 最大回撤 | {result['max_drawdown']:.2f}% | {'❌ 深回撤' if result['max_drawdown'] < -15 else '⚠️ 中等回撤' if result['max_drawdown'] < -8 else '✅ 浅回撤'} |
| 夏普比率 | {result['sharpe_ratio']:.3f} | {'✅ 优秀' if result['sharpe_ratio'] > 1 else '⚠️ 一般' if result['sharpe_ratio'] > 0 else '❌ 较差'} |
| 日胜率 | {result['win_rate']:.1f}% | {'✅ 高胜率' if result['win_rate'] > 55 else '📊 均衡' if result['win_rate'] > 45 else '❌ 低胜率'} |
| 平均成交量 | {result['avg_volume']:,} | - |
| RSI(14) | {result['latest_rsi']:.2f} ({result['rsi_status']}) | - |
| MACD | {result['macd_signal']} | - |
| KDJ J值 | {result['kdj_j']:.2f} ({result['kdj_signal']}) | - |
| 均线趋势 | {result['ma_trend']} | - |
| 布林带位置 | {result['bb_position']:.1%} | {'⚠️ 高位' if result['bb_position'] > 0.8 else '✅ 低位' if result['bb_position'] < 0.2 else '📊 中位'} |
| ATR(14) | {result['atr14']} | - |
| 量比 | {result['volume_ratio']:.2f}x | {'✅ 放量' if result['volume_ratio'] > 1.5 else '❌ 缩量' if result['volume_ratio'] < 0.5 else '📊 正常'} |

---

"""
        
        report += f"""## 三、综合交易信号

### 信号评分: {signals['score']}/100 ({signals['overall']})

"""
        for sig in signals['signals']:
            report += f"- {sig}\n"
        
        report += f"""
### 操作建议

> **{signals['action']}**

---

## 四、资金流向分析（AkShare）

### 主力资金动向
"""
        
        if fund_flow and 'error' not in fund_flow:
            report += f"""
| 指标 | 数值 | 信号 |
|------|------|------|
| 日期 | {fund_flow.get('date', '-')} | - |
| 主力净流入 | {fund_flow.get('main_inflow', 0)} 万元 | {fund_flow.get('signal', '-')} |
| 散户净流入 | {fund_flow.get('retail_inflow', 0)} 万元 | - |
| 主力净流入占比 | {fund_flow.get('main_inflow_ratio', 0)}% | 强度: {fund_flow.get('strength', '-')} |

> 💡 **解读**: 主力资金{fund_flow.get('signal', '流向不明')}，{'建议跟随主力' if '流入' in fund_flow.get('signal', '') else '注意主力出货风险'}
"""
        else:
            report += "\n> ⚠️ 资金流向数据暂不可用\n"
        
        report += f"""
### 融资融券数据
"""
        
        if margin_data and 'error' not in margin_data:
            report += f"""
| 指标 | 数值 | 信号 |
|------|------|------|
| 日期 | {margin_data.get('date', '-')} | - |
| 融资余额 | {margin_data.get('rz_balance', 0)} 万元 | {margin_data.get('signal', '-')} |
| 融券余额 | {margin_data.get('rq_balance', 0)} 万元 | - |
| 融资融券余额 | {margin_data.get('total_balance', 0)} 万元 | - |
| 杠杆多空比 | {margin_data.get('leverage_ratio', 0)}x | 情绪: {margin_data.get('sentiment', '-')} |

> 💡 **解读**: 市场情绪{margin_data.get('sentiment', '不明')}，杠杆{margin_data.get('leverage_ratio', 0)}倍
"""
        else:
            report += "\n> ⚠️ 融资融券数据暂不可用\n"
        
        report += f"""
---

## 五、稀土板块对比（AkShare）

### 板块内成分股表现
"""
        
        if sector_comparison and 'error' not in sector_comparison:
            if 'leaders' in sector_comparison:
                report += "\n| 股票 | 代码 | 最新价 | 30天收益 | 趋势 |\n"
                report += "|------|------|--------|----------|------|\n"
                for leader in sector_comparison['leaders']:
                    if 'error' not in leader:
                        report += f"| {leader.get('name', '-')} | {leader.get('code', '-')} | {leader.get('latest_price', '-')} | {leader.get('return_30d', 0):+.2f}% | {leader.get('trend', '-')} |\n"
            
            if 'etf_comparison' in sector_comparison:
                comp = sector_comparison['etf_comparison']
                report += f"\n### ETF vs 板块对比\n\n"
                report += f"- ETF 30天收益: {comp.get('etf_return_30d', 0):+.2f}%\n"
                report += f"- 板块平均收益: {comp.get('avg_leader_return', 0):+.2f}%\n"
                report += f"- 相对表现: {comp.get('outperform', 0):+.2f}%\n"
                report += f"- 结论: {comp.get('conclusion', '数据不足')}\n"
        else:
            report += "\n> ⚠️ 板块对比数据暂不可用\n"
        
        report += f"""
---

## 六、个股跟踪（AkShare）

"""
        
        # 添加个股跟踪数据
        individual_stocks = self.config.config.get("individual_stocks", {})
        if individual_stocks.get("enabled", False):
            stocks = individual_stocks.get("stocks", [])
            if stocks:
                report += "### 重点跟踪个股\n\n"
                report += "| 股票 | 代码 | 行业 | 跟踪理由 | 最新价 | 30天收益 | 趋势 |\n"
                report += "|------|------|------|----------|--------|----------|------|\n"
                
                # 获取个股数据
                for stock in stocks:
                    try:
                        import akshare as ak
                        stock_code = stock['code']
                        stock_name = stock['name']
                        sector = stock.get('sector', '-')
                        reason = stock.get('reason', '-')
                        
                        # 获取个股30天数据
                        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
                        df_stock = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                                       start_date=start_date, adjust="qfq")
                        
                        if len(df_stock) > 0:
                            latest_price = float(df_stock.iloc[-1]['收盘'])
                            first_price = float(df_stock.iloc[0]['收盘'])
                            return_30d = (latest_price - first_price) / first_price * 100
                            trend = "上涨" if return_30d > 0 else "下跌"
                            
                            report += f"| {stock_name} | {stock_code} | {sector} | {reason} | {latest_price:.2f} | {return_30d:+.2f}% | {trend} |\n"
                        else:
                            report += f"| {stock_name} | {stock_code} | {sector} | {reason} | - | - | 数据不足 |\n"
                    except Exception as e:
                        report += f"| {stock.get('name', '-')} | {stock.get('code', '-')} | {stock.get('sector', '-')} | {stock.get('reason', '-')} | - | - | 获取失败 |\n"
                
                report += "\n"
        
        report += f"""
---

## 七、仓位管理建议

| 项目 | 建议值 |
|------|--------|
| 建议仓位 | {position['suggested_position']} |
| 止损位 | {position['stop_loss']} |
| 第一目标位 | {position['take_profit_1']} |
| 第二目标位 | {position['take_profit_2']} |
| 风险收益比 | {position['risk_reward_ratio']} |

---

## 八、国际稀土市场动态

{industry_news if industry_news else "_待补充最新国际稀土市场动态、政策变化、供需数据等_"}

---

## 九、热点行业跟踪

### 🤖 机器人行业
- 关注人形机器人产业化进展
- 伺服电机、减速器对稀土永磁需求
- 特斯拉 Optimus、波士顿动力等动态

### 🧠 人工智能 / AI
- AI 算力需求对芯片、存储的拉动
- 大模型训练/推理对高性能计算硬件需求
- 相关 ETF: 159819 AIETF、512930 AIETF

### 💻 芯片制造
- 国产替代进程
- 先进制程突破
- 相关 ETF: 512760 芯片ETF、159995 芯片ETF

### 💾 存储行业 / 内存制造
- DRAM/NAND 价格周期
- 国产存储厂商进展
- 相关 ETF: 159321 半导体设备ETF

---

## 十、风险提示

1. ⚠️ 稀土价格受国际地缘政治影响较大
2. ⚠️ 新能源政策变化可能影响稀土需求预期
3. ⚠️ 本报告仅供参考，不构成投资建议
4. ⚠️ 过往业绩不代表未来表现

---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  
*数据来源: AkShare + 东方财富 | 分析框架: 多因子量化模型*
"""
        
        return report


# ============ 主程序 ============

def main():
    """主程序：生成每日投资规划报告"""
    
    # 加载配置
    config = Config()
    
    print("=" * 60)
    print(f"🚀 ETF 趋势跟踪系统启动")
    print(f"📊 目标标的: {config.etf_name} ({config.etf_code})")
    print(f"📅 报告日期: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"⚙️  配置来源: {config.config_path}")
    print("=" * 60)
    
    # 1. 获取数据
    print("\n📥 正在获取历史数据...")
    fetcher = ETFDataFetcher(config)
    df = fetcher.get_kline_data(config.etf_code, days=120)
    print(f"✅ 获取成功: {len(df)} 个交易日")
    
    # 2. 运行回测
    print("\n📊 正在运行多周期回测...")
    engine = BacktestEngine(df)
    backtest_results = engine.run_all_backtests(config.backtest_periods)
    for result in backtest_results:
        print(f"  ✅ {result['period_days']}天回测完成: 收益 {result['total_return']:+.2f}%")
    
    # 3. 获取资金流向（如果启用）
    fund_flow = None
    margin_data = None
    if config.features.get("fund_flow", False):
        print("\n💰 正在获取资金流向...")
        try:
            fund_flow = FundFlowAnalyzer.analyze_fund_flow(config.etf_code)
            print(f"  ✅ 资金流向: {fund_flow.get('signal', '未知')}")
        except Exception as e:
            print(f"  ⚠️ 资金流向获取失败: {e}")
        
        print("\n📈 正在获取融资融券数据...")
        try:
            margin_data = FundFlowAnalyzer.analyze_margin_trading(config.etf_code)
            print(f"  ✅ 融资融券: {margin_data.get('sentiment', '未知')}")
        except Exception as e:
            print(f"  ⚠️ 融资融券获取失败: {e}")
    
    # 4. 获取板块对比（如果启用）
    sector_comparison = None
    if config.features.get("sector_comparison", False) and config.sector_config.get("enabled", False):
        print("\n🏭 正在获取板块对比数据...")
        try:
            sector_leaders = SectorComparison.get_sector_leaders_performance(config.sector_config)
            etf_comparison = SectorComparison.compare_with_etf(config.etf_code, sector_leaders)
            sector_comparison = {
                "leaders": sector_leaders,
                "etf_comparison": etf_comparison
            }
            print(f"  ✅ 板块对比完成: {len(sector_leaders)} 只龙头股")
        except Exception as e:
            print(f"  ⚠️ 板块对比获取失败: {e}")
    
    # 5. 生成信号
    print("\n🔍 正在生成交易信号...")
    signal_gen = SignalGenerator(backtest_results, df, fund_flow, margin_data)
    signals = signal_gen.generate_signals()
    position = signal_gen.calculate_position_sizing()
    print(f"  ✅ 综合评分: {signals['score']}/100 ({signals['overall']})")
    
    # 获取行业新闻
    print("\n📰 正在获取行业动态...")
    try:
        from industry_news import IndustryNewsTracker
        news_tracker = IndustryNewsTracker()
        industry_news = news_tracker.get_daily_news_summary()
        print("✅ 行业动态获取完成")
    except Exception as e:
        print(f"⚠️ 行业动态获取失败: {e}")
        industry_news = ""
    
    # 6. 生成报告
    print("\n📝 正在生成投资规划报告...")
    report_gen = ReportGenerator(config)
    report = report_gen.generate_report(
        backtest_results, signals, position, df,
        fund_flow=fund_flow,
        margin_data=margin_data,
        sector_comparison=sector_comparison,
        industry_news=industry_news
    )
    
    # 7. 保存报告
    report_path = f"{config.config.get('data_dir', '/home/zhihu/etf_tracker')}/reports/report_{datetime.now().strftime('%Y%m%d')}.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✅ 报告已保存: {report_path}")
    
    # 8. 保存数据
    data_path = f"/home/zhihu/etf_tracker/{config.etf_code}_history.csv"
    df.to_csv(data_path, index=False)
    print(f"✅ 数据已保存: {data_path}")
    
    # 9. 微信推送
    if config.config.get("wechat_push", {}).get("enabled", False):
        print("\n📱 正在推送微信通知...")
        try:
            if config.config.get("wechat_push", {}).get("channel") == "hermes":
                from hermes_wechat_pusher import send_daily_report
                send_daily_report(
                    report_path=report_path,
                    etf_name=config.etf_name,
                    etf_code=config.etf_code,
                    score=signals['score'],
                    signal=signals['overall'],
                    action=signals['action']
                )
            else:
                from wechat_pusher import send_daily_report
                send_daily_report(
                    report_path=report_path,
                    etf_name=config.etf_name,
                    etf_code=config.etf_code,
                    score=signals['score'],
                    signal=signals['overall'],
                    action=signals['action']
                )
        except Exception as e:
            print(f"⚠️ 微信推送失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 报告生成完成!")
    print("=" * 60)
    
    return report_path


if __name__ == "__main__":
    main()
