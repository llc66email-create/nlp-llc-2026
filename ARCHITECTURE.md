# Story Weaver — 项目架构文档

> 基于哈利波特宇宙的中文互动叙事游戏系统

---

## 项目定位

玩家扮演经典角色做出选择，AI 根据输入动态推进故事，同时强制约束故事内容不偏离原著设定。

---

## 整体架构

```
用户输入 (Web界面)
    ↓
Flask API (app.py)  →  端口 5001
    ↓
StoryWeaver 核心 (story_weaver/core.py)
    ↓
┌──────────────┬──────────────┬──────────────┬──────────────┐
│   NLU引擎    │   RAG检索    │  约束引擎    │  一致性检查  │
│ (意图+实体)  │ (情节片段)   │ (时间线约束) │  (状态矛盾)  │
└──────┬───────┴──────┬───────┴──────┬───────┴──────────────┘
       └──────────────┴──────────────┘
                      ↓
               NLG生成引擎（DeepSeek API）
                      ↓
             故事文本 + 下一步选项
```

---

## 目录结构

```
nlp-llc-2026/
├── app.py                          # Flask Web 入口
├── config.py                       # 全局配置（模型/路径/参数）
├── wsgi.py                         # Gunicorn 入口
├── run.sh                          # 启动脚本
├── requirements.txt
├── data/
│   └── knowledge_base/
│       ├── character_graph.json    # 角色关系图谱
│       ├── plot_segments.json      # RAG 情节片段库
│       ├── consistency_rules.json  # 一致性检查规则
│       └── world_state.json        # 初始世界状态
├── story_weaver/
│   ├── core.py                     # 主系统，整合所有模块
│   ├── constraint_engine.py        # 原著约束引擎
│   ├── validation_pipeline.py      # 章节任务推进追踪
│   ├── nlu/
│   │   └── intent_extractor.py     # 意图识别 + 实体抽取
│   ├── nlg/
│   │   ├── generator.py            # NLG 生成引擎（主）
│   │   └── enhanced_generator.py   # 增强型本地生成器
│   ├── rag/
│   │   └── retriever.py            # RAG 检索系统
│   ├── consistency/
│   │   └── checker.py              # 一致性检查器
│   ├── state_management/
│   │   └── game_state.py           # 游戏状态管理
│   └── logging/                    # 交互日志
└── web_interface/
    ├── templates/index.html         # 前端页面
    └── static/                      # CSS / JS
```

---

## 核心模块说明

### 1. `app.py` — Web 入口层

- **框架**：Flask + CORS，监听 `0.0.0.0:5001`
- **启动机制**：后台线程异步初始化 `StoryWeaver`，主线程立即响应 HTTP（避免启动阻塞）

**关键 API 端点：**

| 路由 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 渲染前端页面 |
| `/api/init_status` | GET | 查询系统初始化状态 |
| `/api/get_characters` | GET | 获取可选角色列表 |
| `/api/select_character` | POST | 选择角色 |
| `/api/start_game` | POST | 开始新游戏 |
| `/api/process_input` | POST | 处理玩家输入，返回故事推进 |
| `/api/campaign_overview` | GET | 获取章节任务概览 |

---

### 2. `story_weaver/core.py` — 主系统

`StoryWeaver` 类负责整合所有子模块，处理完整的一次用户交互流程：

```
用户输入
  → NLU 意图识别
  → RAG 检索相关情节片段
  → 约束引擎验证行动合法性
  → NLG 生成故事文本
  → 一致性检查
  → 更新 GameState
  → 记录日志
  → 返回响应
```

**可选角色：** 哈利·波特 / 赫敏·格兰杰 / 罗恩·韦斯莱 / 邓布利多

---

### 3. `story_weaver/nlu/intent_extractor.py` — NLU 引擎

**作用：** 理解玩家输入的意图和关键实体。

**意图类型（14 类）：**

| 分类 | 意图 |
|------|------|
| 导航 | `MOVE` / `LOOK` / `EXAMINE` |
| 互动 | `TALK` / `INTERACT` / `CAST_SPELL` |
| 物品 | `TAKE` / `DROP` / `USE` / `GIVE` |
| 信息 | `QUERY` / `INVENTORY` / `STATUS` |
| 其他 | `UNKNOWN` / `CLARIFY` |

**实现逻辑：**
1. 关键词映射表快速匹配意图
2. BERT NER 模型（`dslim/bert-base-multilingual-cased-ner-hrl`）提取角色/地点实体
3. 置信度低于阈值（默认 0.7）时触发澄清请求

---

### 4. `story_weaver/rag/retriever.py` — RAG 检索系统

**作用：** 为 NLG 提供与当前场景最相关的原著情节片段作为上下文。

**数据来源：** `data/knowledge_base/plot_segments.json`

**检索逻辑：**
- 当前采用**关键字匹配**模式（快速响应）
- 预留了 **FAISS + SentenceTransformer** 向量语义检索接口（可按需启用）
- 默认召回 `top_k=5` 最相关片段

---

### 5. `story_weaver/nlg/generator.py` — NLG 生成引擎

**作用：** 生成动态故事文本和下一步玩家选项。

**生成模式（优先级顺序）：**

| 优先级 | 模式 | 条件 |
|--------|------|------|
| 1 | DeepSeek API（`deepseek-chat`） | 设置 `DEEPSEEK_API_KEY` 环境变量 |
| 2 | 本地 GPT-2 中文模型 | `uer/gpt2-chinese-cluecorpussmall` |
| 3 | 模板兜底 | API 不可用时自动回退 |

**约束注入：** 向 LLM 注入 System Prompt，禁止出现宇航员/计算机等现代词汇，强制角色以中文对话，确保内容留在哈利波特宇宙内。

---

### 6. `story_weaver/constraint_engine.py` — 约束引擎

**作用：** 防止故事出现与原著矛盾的情节，三层约束：

| 约束层 | 说明 | 示例 |
|--------|------|------|
| **能力约束** | 角色是否已习得某魔法 | 哈利在第3册第8章才会守护神咒 |
| **地点约束** | 该地点在当前时间线是否可访问 | — |
| **时间约束** | 基于 `TimelineBook`（1-7册）判断事件是否可发生 | — |

**数据结构：** `CharacterAbilityTracker` 精确记录每个角色每项技能的习得册数和章节，`can_use_skill()` 方法对外提供校验接口。

---

### 7. `story_weaver/consistency/checker.py` — 一致性检查器

**作用：** 检测故事状态的逻辑矛盾，避免前后不一致。

**规则类型：** `character_state` / `location_state` / `temporal` / `logical`

**实现：** 维护 `fact_base` 事实库，新事件提交前与历史事实比对，违规时生成 `ConsistencyViolation` 记录。

---

### 8. `story_weaver/validation_pipeline.py` — 故事推进追踪

**作用：** 定义章节任务结构，追踪玩家推进进度。

**任务结构：** 支持 4 章模板，每章固定 9 个主线任务，从「情报收集」→「核心行动」→「章节收束」线性推进。

**触发机制：** 通过关键词匹配判断玩家输入是否触发/完成当前任务。

---

### 9. `story_weaver/state_management/game_state.py` — 游戏状态管理

**维护的状态对象：**

| 对象 | 字段 |
|------|------|
| `Character` | 位置、生命状态、属性、角色关系、背包 |
| `Location` | 连通地点、在场角色、物品列表 |
| `Item` | 归属者、所在地点、属性 |
| `PlotNode` | 剧情节点树（父子节点、分支） |

**其他功能：** 状态快照（存档/读档）、交互历史记录、世界变量键值存储。

---

## 数据层

```
data/knowledge_base/
├── character_graph.json    # 角色关系图谱（NPC位置、关系、属性）
├── plot_segments.json      # RAG 情节片段库（检索上下文用）
├── consistency_rules.json  # 一致性规则（JSON 格式规则集）
└── world_state.json        # 初始世界状态（地点连通、初始角色位置）
```

---

## 技术栈

| 层次 | 技术 |
|------|------|
| Web 服务 | Flask + Flask-CORS，端口 5001 |
| NLU 意图 | 关键词规则 + DistilBERT |
| NLU 实体 | BERT NER（multilingual） |
| RAG 检索 | 关键字匹配（FAISS 向量检索预留） |
| 嵌入模型 | `sentence-transformers/all-MiniLM-L6-v2` |
| NLG 生成 | DeepSeek API（`deepseek-chat`）/ 本地 GPT-2 |
| 约束规则 | Python 枚举 + 数据类（无外部依赖） |
| 配置管理 | `config.py` 统一管理所有模型/路径/参数 |
| 日志 | JSON Lines 格式，存于 `logs/` |

---

## 配置说明

关键配置项位于 `config.py`：

```python
# 切换生成模式
ModelConfig.USE_OPENAI_API = True       # 使用 DeepSeek API
ModelConfig.OPENAI_API_MODEL = "deepseek-chat"

# API 密钥（通过环境变量注入）
# export DEEPSEEK_API_KEY=your_key

# NLU 置信度阈值
SystemConfig.INTENT_CONFIDENCE_THRESHOLD = 0.7

# 对话历史长度
SystemConfig.MAX_HISTORY_LENGTH = 10

# Web 端口
SystemConfig.WEB_PORT = 5001
```

---

## 启动方式

```bash
# 直接启动（Flask 开发服务器）
python app.py

# 生产模式（Gunicorn）
bash run.sh
```

启动后访问：`http://localhost:5001`
