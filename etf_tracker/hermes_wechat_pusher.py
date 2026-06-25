#!/usr/bin/env python3
"""
Hermes 微信通道推送模块
使用 Hermes 内置的微信通道发送 ETF 投资规划报告
"""

import os
import json
import urllib.request
from datetime import datetime
from typing import Optional

class HermesWeChatPusher:
    """使用 Hermes 微信通道发送消息"""
    
    def __init__(self):
        """初始化微信推送器"""
        # 从 Hermes 配置中读取微信配置
        self.config = self._load_hermes_config()
        self.weixin_config = self.config.get('platforms', {}).get('weixin', {})
        self.token = self.weixin_config.get('token', '')
        self.account_id = self.weixin_config.get('extra', {}).get('account_id', '')
        self.base_url = self.weixin_config.get('extra', {}).get('base_url', 'https://ilinkai.weixin.qq.com')
        
        if not self.token:
            print("⚠️ 未找到微信配置，请检查 Hermes 配置")
    
    def _load_hermes_config(self) -> dict:
        """加载 Hermes 配置文件"""
        import yaml
        config_path = os.path.expanduser('~/.hermes/config.yaml')
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️ 读取 Hermes 配置失败: {e}")
            return {}
    
    def send_message(self, content: str, msg_type: str = "text") -> bool:
        """
        发送消息到微信
        
        Args:
            content: 消息内容
            msg_type: 消息类型 (text/markdown)
        """
        if not self.token:
            print("❌ 微信未配置，无法发送消息")
            return False
        
        try:
            # 构建消息数据
            data = {
                "msgtype": msg_type,
                "content": content
            }
            
            # 使用 Hermes API 发送消息
            # 注意：这里使用 Hermes 的内部 API 或 webhook
            url = f"{self.base_url}/api/message/send"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read().decode('utf-8'))
            
            if result.get('errcode') == 0:
                print("✅ 微信消息发送成功")
                return True
            else:
                print(f"❌ 发送失败: {result}")
                return False
                
        except Exception as e:
            print(f"❌ 发送异常: {e}")
            return False
    
    def send_report_summary(self, report_path: str, etf_name: str, etf_code: str,
                           score: float, signal: str, action: str) -> bool:
        """发送报告摘要到微信"""
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
        except Exception as e:
            print(f"读取报告失败: {e}")
            return False
        
        # 构建摘要消息
        summary = f"""📊 {etf_name} ({etf_code}) 日报

📅 日期: {datetime.now().strftime('%Y-%m-%d')}
📈 综合评分: {score}/100
🎯 信号状态: {signal}
💡 操作建议: {action}

---

{report_content[:1000]}...

---

💡 完整报告请查看 GitHub 仓库
"""
        
        return self.send_message(summary, "markdown")


def send_daily_report(report_path: str, etf_name: str = "稀土ETF嘉实",
                      etf_code: str = "516150", score: float = 0,
                      signal: str = "", action: str = "") -> bool:
    """
    发送每日报告到微信的便捷函数
    """
    pusher = HermesWeChatPusher()
    return pusher.send_report_summary(report_path, etf_name, etf_code, score, signal, action)


if __name__ == "__main__":
    # 测试推送
    pusher = HermesWeChatPusher()
    pusher.send_message("🚀 ETF 跟踪系统测试消息\n\n如果您收到这条消息，说明 Hermes 微信推送配置成功！")
