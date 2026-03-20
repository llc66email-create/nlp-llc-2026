#!/bin/bash
# 优化的服务器启动脚本

set -e

echo "======================================"
echo "Story Weaver 服务器启动脚本"
echo "======================================"

# 设置工作目录
cd /workspaces/nlp2026

# 清理旧进程
echo "清理旧的 Python 进程..."
pkill -f "python.*app\.py" || true
sleep 2

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo "激活虚拟环境..."
    source .venv/bin/activate
fi

# 启动选项
HOST="0.0.0.0"
PORT="5000"
WORKERS="2"
TIMEOUT="120"
WORKER_CLASS="sync"

# 检查是否安装了 gunicorn
if command -v gunicorn &> /dev/null; then
    echo "检测到 Gunicorn，使用 Gunicorn 启动..."
    gunicorn \
        --workers $WORKERS \
        --worker-class $WORKER_CLASS \
        --bind "$HOST:$PORT" \
        --timeout $TIMEOUT \
        --access-logfile - \
        --error-logfile - \
        wsgi:app
else
    echo "使用 Flask 开发服务器启动..."
    python app.py
fi
