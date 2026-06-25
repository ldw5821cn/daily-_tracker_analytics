#!/bin/bash
# ETF 每日报告定时任务脚本
# 添加到 crontab: 0 18 * * 1-5 /home/zhihu/etf_tracker/run_daily.sh

set -e

cd /home/zhihu/etf_tracker

# 记录日志
LOG_FILE="/home/zhihu/etf_tracker/logs/daily_$(date +%Y%m%d).log"
mkdir -p logs

echo "========================================" | tee -a "$LOG_FILE"
echo "📊 ETF 日报生成任务启动" | tee -a "$LOG_FILE"
echo "⏰ 时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 运行报告生成
python3 etf_tracker.py 2>&1 | tee -a "$LOG_FILE"

# 发送微信通知（如果配置了 WEBHOOK）
if [ -f ".env" ]; then
    source .env
    if [ -n "$WECHAT_WEBHOOK_URL" ]; then
        LATEST_REPORT=$(ls -t reports/*.md | head -1)
        SUMMARY=$(sed -n '1,50p' "$LATEST_REPORT")
        curl -s "$WECHAT_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"msgtype\": \"markdown\", \"markdown\": {\"content\": \"📊 ETF日报 $(date +%Y-%m-%d)\\n\\n$SUMMARY\"}}" 2>&1 | tee -a "$LOG_FILE"
    fi
fi

echo "✅ 任务完成" | tee -a "$LOG_FILE"
