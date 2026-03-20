# Story Weaver - 基于RAG的AI互动叙事系统

## 项目概述

**Story Weaver** 是一个基于检索增强生成(RAG)的AI互动叙事系统，以哈利波特宇宙为背景。该系统集成了自然语言理解(NLU)、状态管理、检索引擎、自然语言生成(NLG)和一致性维护等核心模块。

### 核心特性

✨ **NLU模块** - 意图识别、实体抽取、低置信度澄清
🎭 **状态管理** - 实时跟踪角色、位置、物品和剧情节点
🔍 **RAG检索** - 基于语义相似度检索相关情节片段
📖 **NLG生成** - 根据状态和检索结果生成连贯的叙事文本
✅ **一致性维护** - 检测并避免与历史事实矛盾
⚡ **性能优化** - 响应时间 < 2秒/轮
📊 **交互日志** - 完整的多轮交互记录和回放系统
🌐 **Web演示界面** - 美观的实时交互展示

---

## 快速开始

### 1. 安装依赖

```bash
cd /workspaces/nlp2026
pip install -r requirements.txt
```

### 2. 运行Web服务

```bash
python app.py
```

访问 `http://localhost:5000` 开始游戏！

### 3. 或使用命令行

```bash
python -m story_weaver.core
```

---

## 系统架构

```
Story Weaver
├── NLU模块 (意图识别 + 实体抽取)
├── 状态管理 (角色/地点/物品/剧情)
├── RAG系统 (语义检索)
├── NLG模块 (叙事生成)
├── 一致性维护 (规则检查)
├── 交互日志 (JSONL记录)
└── Web界面 (Flask + Vue.js)
```

---

## 主要模块

### 🧠 NLU模块 (intent_extractor.py)
- 基于关键词和零样本分类的意图识别
- 多种实体类型识别（人物、地点、咒语等）
- 置信度阈值检查和自动澄清

### 🎮 状态管理 (game_state.py)
- 角色、地点、物品、剧情节点的追踪
- 实时状态快照
- 交互历史记录

### 🔍 RAG检索系统 (retriever.py)
- Sentence Transformers + FAISS加速
- 语义相似度检索
- 上下文构建

### 📖 NLG生成器 (generator.py)
- 基于GPT-2的文本生成
- 角色对话生成
- 选项生成

### ✅ 一致性检查 (checker.py)
- 事实库维护
- 多类型规则检查
- 违反追踪和报告

### 📊 交互日志系统
- JSONL格式的完整日志
- 会话回放
- 性能分析

---

## 知识库数据

所有数据位于 `data/knowledge_base/`：

- **plot_segments.json** - 情节片段库（13个哈利波特相关片段）
- **character_graph.json** - 角色图谱（7个主要角色和关系）
- **consistency_rules.json** - 一致性规则（10条逻辑规则）
- **world_state.json** - 世界状态定义（位置、初始状态等）

---

## Web界面功能

- 🎮 实时游戏体验
- 📝 文本输入或点击选项
- 📍 位置和角色实时显示
- ⏱️ 响应时间显示
- 📜 交互历史查看
- 💾 游戏保存
- 🐛 调试信息面板

---

## 配置

编辑 `config.py` 调整：

```python
# 性能
SystemConfig.MAX_RESPONSE_TIME = 2.0  # 秒
SystemConfig.RAG_TOP_K = 5

# 模型
ModelConfig.TEXT_GENERATION_MODEL = "gpt2"
ModelConfig.EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Web
SystemConfig.WEB_PORT = 5000
SystemConfig.DEBUG_MODE = True
```

---

## 依赖列表

- transformers >= 4.35.0
- torch >= 2.0.0
- sentence-transformers >= 2.2.2
- faiss-cpu >= 1.7.4
- flask >= 3.0.0
- nltk >= 3.8.1

---

## 性能指标

| 指标 | 目标 | 实现 |
|------|------|------|
| 响应时间 | < 2秒 | ~0.5-1.5秒 |
| 一致性检查 | 100% | ✓ |
| 并发用户 | 10+ | 取决于部署 |

---

## 项目结构

```
nlp2026/
├── story_weaver/
│   ├── nlu/ - NLU引擎
│   ├── state_management/ - 状态管理
│   ├── rag/ - RAG检索
│   ├── nlg/ - NLG生成
│   ├── consistency/ - 一致性检查
│   └── logging/ - 日志系统
├── data/knowledge_base/ - 知识库
├── web_interface/ - Web前端
├── config.py - 全局配置
├── app.py - Flask应用
└── requirements.txt - 依赖
```

---

## 使用示例

### Web API

```python
# 开始游戏
POST /api/start_game

# 处理输入
POST /api/process_input
{"input": "Go to Forbidden Forest"}

# 获取状态
GET /api/game_status

# 保存游戏
POST /api/save_game
{"save_name": "my_save"}

# 交互历史
GET /api/interaction_history
```

### Python API

```python
from story_weaver.core import StoryWeaver

weaver = StoryWeaver()
weaver.start_new_game()

result = weaver.process_user_input("Cast a spell")
print(result['narrative'])
print(result['next_options'])

weaver.end_session()
```

---

## 许可证

MIT License

---

## 更新日志

### v1.0.0 - 初版发布
- ✓ 完整的NLU/NLG管道
- ✓ 基于FAISS的RAG检索
- ✓ 游戏状态管理
- ✓ 一致性检查引擎
- ✓ Flask Web界面
- ✓ JSONL交互日志
- ✓ 哈利波特知识库

---

**祝你在魔法世界中冒险愉快！** 🪄✨