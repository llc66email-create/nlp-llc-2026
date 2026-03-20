# 快速启动指南

## 一键启动

### 方式1：使用Python直接运行（推荐）

```bash
# 1. 进入项目目录
cd /workspaces/nlp2026

# 2. 安装依赖（首次）
pip install -r requirements.txt

# 3. 运行Web服务
python app.py

# 4. 打开浏览器访问
# http://localhost:5000
```

### 方式2：使用Docker

```bash
# 1. 构建镜像
docker build -t story-weaver .

# 2. 运行容器
docker run -p 5000:5000 story-weaver

# 3. 打开浏览器
# http://localhost:5000
```

### 方式3：使用Docker Compose

```bash
# 1. 启动服务
docker-compose up

# 2. 打开浏览器
# http://localhost:5000
```

---

## 命令行测试

### 运行单个模块测试

```bash
# 测试所有模块
python test_system.py

# 测试特定模块
python test_system.py --module nlu
python test_system.py --module state
python test_system.py --module rag
python test_system.py --module nlg
python test_system.py --module consistency
python test_system.py --module full
```

### 运行核心系统

```bash
python -m story_weaver.core
```

---

## Python API使用

```python
from story_weaver.core import StoryWeaver

# 初始化
weaver = StoryWeaver()

# 开始游戏
weaver.start_new_game()

# 处理用户输入
response = weaver.process_user_input("Go to Forbidden Forest")

# 生成的响应包含：
# - narrative: 故事叙述
# - next_options: 下一步选项
# - intent: 识别的意图
# - consistency_check: 一致性检查结果
# - response_time: 响应时间

print(response['narrative'])
print(response['next_options'])

# 保存游戏
weaver.save_game("my_save")

# 查询游戏状态
status = weaver.get_game_status()

# 结束会话
summary = weaver.end_session()
```

---

## Web API调用

### 启动游戏

```bash
curl -X POST http://localhost:5000/api/start_game
```

### 发送用户输入

```bash
curl -X POST http://localhost:5000/api/process_input \
  -H "Content-Type: application/json" \
  -d '{"input": "Go to Forbidden Forest"}'
```

### 获取游戏状态

```bash
curl http://localhost:5000/api/game_status
```

### 保存游戏

```bash
curl -X POST http://localhost:5000/api/save_game \
  -H "Content-Type: application/json" \
  -d '{"save_name": "my_save"}'
```

### 查看交互历史

```bash
curl http://localhost:5000/api/interaction_history
```

### 获取世界上下文

```bash
curl http://localhost:5000/api/world_context
```

---

## 项目配置

### 调整性能参数 (config.py)

```python
# 最大响应时间
SystemConfig.MAX_RESPONSE_TIME = 2.0

# RAG检索结果数
SystemConfig.RAG_TOP_K = 5

# 保留的历史记录数
SystemConfig.MAX_HISTORY_LENGTH = 10

# 置信度阈值
SystemConfig.INTENT_CONFIDENCE_THRESHOLD = 0.7

# Web服务端口
SystemConfig.WEB_PORT = 5000
```

### 更换模型 (config.py)

```python
# 意图识别模型
ModelConfig.INTENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"

# 嵌入模型
ModelConfig.EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# 文本生成模型
ModelConfig.TEXT_GENERATION_MODEL = "gpt2"
```

---

## 常见问题

### Q: 模型下载很慢怎么办？
A: 首次运行会自动下载预训练模型（约1-2GB），建议使用VPN或代理加速。

### Q: 如何修改故事背景？
A: 编辑 `data/knowledge_base/` 中的JSON文件：
  - `plot_segments.json` - 情节片段
  - `character_graph.json` - 角色信息
  - `consistency_rules.json` - 规则定义
  - `world_state.json` - 世界定义

### Q: 如何添加新的意图？
A: 在 `story_weaver/nlu/intent_extractor.py` 中：
  1. 在 Intent 枚举中添加新意图
  2. 在 INTENT_KEYWORDS 中添加关键词
  3. 在 _generate_clarification 中添加澄清消息

### Q: 响应时间太长怎么办？
A: 
  1. 减少 `RAG_TOP_K` 参数
  2. 使用更小的嵌入模型
  3. 打开GPU加速（如果可用）

### Q: 如何启用GPU加速？
A: PyTorch会自动检测GPU，确保：
  1. CUDA已安装
  2. torch版本支持GPU
  3. 足够的显存（建议≥2GB）

---

## 项目文件结构

```
nlp2026/
├── 核心系统
│   ├── config.py - 全局配置
│   ├── app.py - Flask Web应用
│   ├── story_weaver/core.py - 主系统
│   ├── init_project.py - 初始化脚本
│   ├── test_system.py - 测试脚本
│   ├── requirements.txt - 依赖列表
│   ├── Dockerfile - Docker镜像
│   └── docker-compose.yml - 容器编排
│
├── 模块代码
│   └── story_weaver/
│       ├── nlu/ - NLU模块
│       ├── state_management/ - 状态管理
│       ├── rag/ - RAG检索
│       ├── nlg/ - NLG生成
│       ├── consistency/ - 一致性维护
│       └── logging/ - 日志系统
│
├── 数据知识库
│   └── data/knowledge_base/
│       ├── plot_segments.json - 情节库
│       ├── character_graph.json - 角色图谱
│       ├── consistency_rules.json - 规则
│       └── world_state.json - 世界状态
│
├── Web界面
│   └── web_interface/
│       ├── templates/
│       │   └── index.html - HTML页面
│       └── static/
│           ├── css/style.css - 样式表
│           └── js/main.js - 前端脚本
│
├── 文档
│   ├── README.md - 项目文档
│   └── QUICKSTART.md - 此文件
│
└── 日志和数据
    └── logs/ - 交互日志目录
```

---

## 调试和监控

### 启用调试模式

在 Web页面右下角有"调试"按钮，可以查看：
- 识别的意图
- 意图置信度
- 响应时间
- 一致性检查结果

### 查看日志

```bash
# 查看所有交互日志
ls logs/

# 分析特定会话
cat logs/session_*.jsonl | jq '.'

# 查看错误日志
cat logs/error_*.log
```

### 监控性能

系统会自动记录每次响应时间，Web界面实时显示。

---

## 许可和许可证

MIT License - 详见项目根目录LICENSE文件

---

**祝你在哈利波特的魔法世界中冒险愉快！** 🪄✨
