FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 下载NLTK数据
RUN python -m nltk.downloader punkt stopwords

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "app.py"]
