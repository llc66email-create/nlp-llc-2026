"""
Story Weaver 系统配置文件
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()
load_dotenv(PROJECT_ROOT / ".env")

# 模型配置
class ModelConfig:
    # NLU模型
    INTENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
    ENTITY_MODEL = "dslim/bert-base-multilingual-cased-ner-hrl"
    
    # NLG模型配置 - 动态故事推进
    TEXT_GENERATION_MODEL = "uer/gpt2-chinese-cluecorpussmall"  # 有效中文轻量GPT2模型
    USE_OPENAI_API = True  # 默认使用 DeepSeek API 后端
    OPENAI_API_MODEL = "deepseek-chat"

    # 本地微调LoRA模型配置
    USE_FINETUNED_MODEL = False  # 设为True以启用本地微调模型
    FINETUNED_MODEL_PATH = PROJECT_ROOT / "models" / "qwen2_5_1_5b_lora"  # LoRA适配器路径
    FINETUNED_BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"  # 基础模型名称（需要网络或本地缓存）

    # 推理速度配置（针对Colab T4 / 无GPU环境优化）
    # T4实测：Qwen2.5-1.5B float16 约 40-50 tok/s → 60 tokens ≈ 1.5s
    FAST_MAX_NEW_TOKENS = 60    # 首次响应token上限，控制生成约2秒
    USE_4BIT_QUANTIZATION = False  # 启用4-bit量化（需bitsandbytes，可省显存但略慢）
    USE_FLASH_ATTENTION = False    # 启用flash-attention2（需单独安装，可提速20-30%）

    # Colab 远程模型 API 配置
    # 运行 Colab notebook 第七步后，将打印的 trycloudflare.com 地址填入 .env:
    #   COLAB_MODEL_URL=https://xxxx.trycloudflare.com
    # 或直接在此处硬编码（临时调试用）
    USE_COLAB_REMOTE = False      # 已切回 DeepSeek API，关闭远程 Colab 模型
    COLAB_MODEL_URL = os.environ.get('COLAB_MODEL_URL', '')  # 优先从环境变量读取
    COLAB_TIMEOUT_FAST = 3.5      # /generate 接口超时(秒)
    COLAB_TIMEOUT_SLOW = 30.0     # /two_stage 接口超时(秒)

    # NLG配置
    USE_LLM_GENERATION = True  # ✓ 启用动态LLM生成（带约束）
    # 这个系统会用约束提示词确保故事始终在HP宇宙内

    
    # 嵌入模型
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # 语言
    LANGUAGE = "zh"  # 中文

# 数据库配置
class DataConfig:
    # 知识库路径
    KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "data" / "knowledge_base"
    CHARACTER_GRAPH_PATH = KNOWLEDGE_BASE_PATH / "character_graph.json"
    PLOT_SEGMENTS_PATH = KNOWLEDGE_BASE_PATH / "plot_segments.json"
    CONSISTENCY_RULES_PATH = KNOWLEDGE_BASE_PATH / "consistency_rules.json"
    WORLD_STATE_PATH = KNOWLEDGE_BASE_PATH / "world_state.json"
    
    # RAG索引
    RAG_INDEX_PATH = PROJECT_ROOT / "data" / "rag_index"

# 系统配置
class SystemConfig:
    # 性能
    MAX_RESPONSE_TIME = 2.0  # 秒
    BATCH_SIZE = 32
    
    # 置信度阈值
    INTENT_CONFIDENCE_THRESHOLD = 0.7
    ENTITY_CONFIDENCE_THRESHOLD = 0.6
    
    # RAG配置
    RAG_TOP_K = 5  # 检索最相关的K个片段
    
    # 多轮交互
    MAX_HISTORY_LENGTH = 10  # 保留最近10轮对话
    
    # 日志
    LOG_DIR = PROJECT_ROOT / "logs"
    INTERACTION_LOG_FILE = LOG_DIR / "interactions.jsonl"
    ERROR_LOG_FILE = LOG_DIR / "errors.log"
    
    # Web接口
    WEB_HOST = "0.0.0.0"
    WEB_PORT = 5001
    DEBUG_MODE = False

# 故事背景配置
class StoryConfig:
    # 故事设定：哈利波特
    UNIVERSE = "Harry Potter"
    SETTING = "Wizarding World"
    
    # 故事参数
    MAX_GENERATED_OPTIONS = 3  # 生成的选项数
    RESPONSE_LENGTH = "medium"  # short, medium, long
    
    # 初始故事点
    INITIAL_SCENE = "Hogwarts Castle, Great Hall"
    INITIAL_TIME_PERIOD = "During Harry's Fifth Year"

# 创建必要的目录
def setup_directories():
    """创建必要的导出目录"""
    system_config = SystemConfig()
    system_config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    data_config = DataConfig()
    data_config.KNOWLEDGE_BASE_PATH.mkdir(parents=True, exist_ok=True)
    data_config.RAG_INDEX_PATH.mkdir(parents=True, exist_ok=True)

# 初始化时执行
if __name__ != "__main__":
    setup_directories()
