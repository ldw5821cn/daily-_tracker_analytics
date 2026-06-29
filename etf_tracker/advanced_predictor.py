#!/usr/bin/env python3
"""
高级预测与预警模块
功能：
1. 趋势预测（1日/3日/5日）
2. 自动预警（评分>80或RSI>70时提醒）
3. 策略优化（根据实际趋势调整权重）
4. K线图生成
5. 资金流向趋势图
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/zhihu/.linuxbrew/Cellar/python@3.10/3.10.9/lib/python3.10/site-packages')

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False


class TrendPredictor:
    """趋势预测器"""
    
    @staticmethod
    def predict_trend(df: pd.DataFrame, days: int = 5) -> Dict:
        """预测未来趋势"""
        if len(df) < 20:
            return {"error": "数据不足"}
        
        latest = df.iloc[-1]
        
        # 1. 线性回归预测
        x = np.arange(len(df))
        y = df['close'].values.astype(float)
        coeffs = np.polyfit(x[-20:].astype(float), y[-20:], 1)
        slope = coeffs[0]
        
        # 预测未来价格
        future_prices = []
        for i in range(1, days + 1):
            pred_price = coeffs[0] * (len(df) + i) + coeffs[1]
            future_prices.append(pred_price)
        
        # 2. 基于技术指标的预测
        # RSI 趋势
        rsi_trend = "up" if df['rsi14'].iloc[-1] > df['rsi14'].iloc[-5] else "down"
        
        # MACD 趋势
        macd_trend = "up" if df['macd_hist'].iloc[-1] > df['macd_hist'].iloc[-3] else "down"
        
        # 均线趋势
        ma_trend = "up" if df['ma5'].iloc[-1] > df['ma10'].iloc[-1] > df['ma20'].iloc[-1] else "down"
        
        # 3. 综合预测
        predictions = {}
        for day in [1, 3, 5]:
            if day <= len(future_prices):
                pred_price = future_prices[day - 1]
                current_price = latest['close']
                expected_return = (pred_price - current_price) / current_price * 100
                
                # 综合信号判断
                signals = []
                if slope > 0: signals.append("up")
                if rsi_trend == "up": signals.append("up")
                if macd_trend == "up": signals.append("up")
                if ma_trend == "up": signals.append("up")
                
                up_count = signals.count("up")
                total = len(signals)
                
                if up_count >= total * 0.75:
                    trend = "强烈看涨"
                    confidence = 0.8
                elif up_count >= total * 0.5:
                    trend = "看涨"
                    confidence = 0.6
                elif up_count >= total * 0.25:
                    trend = "震荡"
                    confidence = 0.4
                else:
                    trend = "看跌"
                    confidence = 0.3
                
                predictions[f"day_{day}"] = {
                    "predicted_price": round(pred_price, 2),
                    "expected_return": round(expected_return, 2),
                    "trend": trend,
                    "confidence": confidence,
                    "signals": {
                        "linear_slope": slope,
                        "rsi_trend": rsi_trend,
                        "macd_trend": macd_trend,
                        "ma_trend": ma_trend
                    }
                }
        
        return predictions
    
    @staticmethod
    def optimize_strategy(df: pd.DataFrame, predictions: Dict, current_signals: Dict) -> Dict:
        """根据预测优化策略"""
        latest = df.iloc[-1]
        
        # 计算各指标权重
        weights = {
            "trend": 0.3,
            "rsi": 0.2,
            "macd": 0.2,
            "volume": 0.15,
            "prediction": 0.15
        }
        
        # 趋势得分
        trend_score = 0
        if latest['close'] > latest['ma5'] > latest['ma10']:
            trend_score = 1
        elif latest['close'] < latest['ma5'] < latest['ma10']:
            trend_score = -1
        
        # RSI得分
        rsi = latest['rsi14']
        rsi_score = 0
        if 30 < rsi < 50:
            rsi_score = 0.5
        elif 50 <= rsi < 70:
            rsi_score = 0.8
        elif rsi >= 70:
            rsi_score = -0.3
        elif rsi <= 30:
            rsi_score = 0.3
        
        # MACD得分
        macd_score = 0
        if latest['macd'] > latest['macd_signal'] and latest['macd_hist'] > 0:
            macd_score = 1
        elif latest['macd'] < latest['macd_signal'] and latest['macd_hist'] < 0:
            macd_score = -1
        
        # 成交量得分
        vol_ratio = latest['volume'] / latest['vol_ma20'] if latest['vol_ma20'] > 0 else 1
        vol_score = 0
        if vol_ratio > 1.5:
            vol_score = 0.5
        elif vol_ratio < 0.5:
            vol_score = -0.5
        
        # 预测得分
        pred_score = 0
        if 'day_1' in predictions:
            pred = predictions['day_1']
            if pred['trend'] in ['强烈看涨', '看涨']:
                pred_score = pred['confidence']
            elif pred['trend'] == '看跌':
                pred_score = -pred['confidence']
        
        # 综合评分
        total_score = (
            trend_score * weights['trend'] +
            rsi_score * weights['rsi'] +
            macd_score * weights['macd'] +
            vol_score * weights['volume'] +
            pred_score * weights['prediction']
        )
        
        # 生成策略建议
        if total_score > 0.6:
            action = "强烈建议买入"
            position = "80-100%"
        elif total_score > 0.3:
            action = "建议买入"
            position = "50-80%"
        elif total_score > -0.3:
            action = "持仓观望"
            position = "30-50%"
        elif total_score > -0.6:
            action = "建议减仓"
            position = "10-30%"
        else:
            action = "强烈建议卖出"
            position = "0-10%"
        
        return {
            "total_score": round(total_score, 3),
            "action": action,
            "position": position,
            "weights": weights,
            "scores": {
                "trend": trend_score,
                "rsi": rsi_score,
                "macd": macd_score,
                "volume": vol_score,
                "prediction": pred_score
            }
        }


class AlertSystem:
    """预警系统"""
    
    @staticmethod
    def check_alerts(stock_data: Dict) -> List[Dict]:
        """检查预警条件"""
        alerts = []
        
        # 1. 评分预警
        score = stock_data.get('score', 0)
        max_score = stock_data.get('max_score', 5)
        score_pct = score / max_score * 100 if max_score > 0 else 0
        
        if score_pct >= 80:
            alerts.append({
                "level": "info",
                "type": "高评分",
                "message": f"{stock_data.get('name', '')} 综合评分 {score_pct:.0f}/100，技术面强势"
            })
        
        # 2. RSI 预警
        rsi = stock_data.get('rsi', 50)
        if rsi > 70:
            alerts.append({
                "level": "warning",
                "type": "RSI超买",
                "message": f"{stock_data.get('name', '')} RSI {rsi:.1f} > 70，注意回调风险"
            })
        elif rsi < 30:
            alerts.append({
                "level": "info",
                "type": "RSI超卖",
                "message": f"{stock_data.get('name', '')} RSI {rsi:.1f} < 30，潜在反弹机会"
            })
        
        # 3. 涨幅预警
        total_return = stock_data.get('total_return', 0)
        if total_return > 50:
            alerts.append({
                "level": "warning",
                "type": "短期暴涨",
                "message": f"{stock_data.get('name', '')} 30天涨幅 {total_return:+.1f}%，注意获利了结"
            })
        elif total_return < -20:
            alerts.append({
                "level": "info",
                "type": "短期暴跌",
                "message": f"{stock_data.get('name', '')} 30天跌幅 {total_return:.1f}%，关注抄底机会"
            })
        
        # 4. 资金流向预警
        fund_flow = stock_data.get('fund_flow', {})
        if isinstance(fund_flow, dict):
            main_inflow = fund_flow.get('main_inflow', 0)
            if main_inflow > 5000:  # 5000万
                alerts.append({
                    "level": "info",
                    "type": "主力大幅流入",
                    "message": f"{stock_data.get('name', '')} 主力净流入 {main_inflow:.0f}万元"
                })
            elif main_inflow < -5000:
                alerts.append({
                    "level": "warning",
                    "type": "主力大幅流出",
                    "message": f"{stock_data.get('name', '')} 主力净流出 {abs(main_inflow):.0f}万元"
                })
        
        return alerts


class AdvancedVisualizer:
    """高级可视化"""
    
    @staticmethod
    def generate_kline_chart(stock_code: str, stock_name: str, df: pd.DataFrame, output_path: str):
        """生成K线图（带均线、MACD、RSI）"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib.patches import Rectangle
            
            fig, axes = plt.subplots(4, 1, figsize=(16, 14), gridspec_kw={'height_ratios': [3, 1, 1, 1]})
            
            # 1. K线图 + 均线
            ax1 = axes[0]
            
            # 绘制K线
            for idx, row in df.iterrows():
                color = 'red' if row['close'] >= row['open'] else 'green'
                
                # 实体
                height = abs(row['close'] - row['open'])
                bottom = min(row['close'], row['open'])
                rect = Rectangle((idx - 0.4, bottom), 0.8, height, 
                                facecolor=color, edgecolor=color, alpha=0.8)
                ax1.add_patch(rect)
                
                # 影线
                ax1.plot([idx, idx], [row['low'], row['high']], color=color, linewidth=0.8)
            
            # 绘制均线
            ax1.plot(df.index, df['ma5'], label='MA5', color='orange', linewidth=1)
            ax1.plot(df.index, df['ma10'], label='MA10', color='blue', linewidth=1)
            ax1.plot(df.index, df['ma20'], label='MA20', color='purple', linewidth=1)
            
            ax1.set_title(f'{stock_name} ({stock_code}) K线图', fontsize=14, fontweight='bold')
            ax1.set_ylabel('价格')
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # 2. 成交量
            ax2 = axes[1]
            colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' 
                     for i in range(len(df))]
            ax2.bar(df.index, df['volume'], color=colors, alpha=0.6)
            ax2.set_ylabel('成交量')
            ax2.grid(True, alpha=0.3)
            
            # 3. MACD
            ax3 = axes[2]
            ax3.plot(df.index, df['macd'], label='MACD', color='blue', linewidth=1)
            ax3.plot(df.index, df['macd_signal'], label='Signal', color='orange', linewidth=1)
            
            # MACD柱状图
            macd_hist = df['macd_hist']
            colors = ['red' if h >= 0 else 'green' for h in macd_hist]
            ax3.bar(df.index, macd_hist, color=colors, alpha=0.6)
            
            ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax3.set_ylabel('MACD')
            ax3.legend(loc='upper left')
            ax3.grid(True, alpha=0.3)
            
            # 4. RSI
            ax4 = axes[3]
            ax4.plot(df.index, df['rsi14'], color='purple', linewidth=1.5)
            ax4.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='超买线(70)')
            ax4.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='超卖线(30)')
            ax4.fill_between(df.index, 30, 70, alpha=0.1, color='gray')
            ax4.set_ylabel('RSI(14)')
            ax4.set_ylim(0, 100)
            ax4.legend(loc='upper left')
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"  ✅ K线图已保存: {output_path}")
            return True
        except Exception as e:
            print(f"  ⚠️ K线图生成失败: {e}")
            return False
    
    @staticmethod
    def generate_fund_flow_chart(stock_code: str, stock_name: str, output_path: str):
        """生成资金流向趋势图"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            import akshare as ak
            
            # 获取近10日资金流向
            df = ak.stock_individual_fund_flow(symbol=stock_code, 
                                               market="sh" if stock_code.startswith('6') else "sz")
            
            if len(df) == 0:
                return False
            
            # 取最近10日
            df = df.head(10).sort_values('日期')
            
            fig, axes = plt.subplots(2, 1, figsize=(14, 10))
            
            # 1. 主力/散户资金流向
            ax1 = axes[0]
            
            dates = df['日期'].values
            main_flow = df['主力净流入-净额'].values / 10000  # 万元
            retail_flow = df['小单净流入-净额'].values / 10000
            
            x = range(len(dates))
            width = 0.35
            
            bars1 = ax1.bar([i - width/2 for i in x], main_flow, width, 
                           label='主力净流入', color='red', alpha=0.7)
            bars2 = ax1.bar([i + width/2 for i in x], retail_flow, width,
                           label='散户净流入', color='blue', alpha=0.7)
            
            ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax1.set_title(f'{stock_name} ({stock_code}) 资金流向趋势', fontsize=14, fontweight='bold')
            ax1.set_ylabel('净流入 (万元)')
            ax1.set_xticks(x)
            ax1.set_xticklabels(dates, rotation=45)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. 大单分布
            ax2 = axes[1]
            
            # 计算各类单净流入
            super_large = df['超大单净流入-净额'].values / 10000
            large = df['大单净流入-净额'].values / 10000
            medium = df['中单净流入-净额'].values / 10000
            small = df['小单净流入-净额'].values / 10000
            
            ax2.bar(x, super_large, label='超大单', color='red', alpha=0.7)
            ax2.bar(x, large, bottom=super_large, label='大单', color='orange', alpha=0.7)
            ax2.bar(x, medium, bottom=super_large+large, label='中单', color='yellow', alpha=0.7)
            ax2.bar(x, small, bottom=super_large+large+medium, label='小单', color='green', alpha=0.7)
            
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax2.set_title('订单类型分布', fontsize=14, fontweight='bold')
            ax2.set_ylabel('净流入 (万元)')
            ax2.set_xticks(x)
            ax2.set_xticklabels(dates, rotation=45)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"  ✅ 资金流向图已保存: {output_path}")
            return True
        except Exception as e:
            print(f"  ⚠️ 资金流向图生成失败: {e}")
            return False


if __name__ == "__main__":
    # 测试预测
    from stock_analyzer import StockAnalyzer
    
    analyzer = StockAnalyzer()
    df = analyzer.get_stock_data("300054", days=60)
    df = analyzer.calculate_indicators(df)
    
    predictor = TrendPredictor()
    predictions = predictor.predict_trend(df, days=5)
    print("预测结果:")
    print(json.dumps(predictions, ensure_ascii=False, indent=2))
    
    strategy = predictor.optimize_strategy(df, predictions, {})
    print("\n策略优化:")
    print(json.dumps(strategy, ensure_ascii=False, indent=2))
