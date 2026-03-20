"""
WSGI 入口点 - 用于生产环境
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import app

if __name__ == '__main__':
    app.run()
