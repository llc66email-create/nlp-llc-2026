"""
增强型NLG生成器 v3 - 集成轻量级中文模型和动作预测
特性：
- 支持多种轻量级中文模型（distilgpt2-chinese, tiny-llama等）
- 集成动作预测系统为故事提供连贯性
- 改进的中文文本生成策略
- 故事一致性检查
"""

from typing import List, Dict, Optional, Tuple
import json
import random
from dataclasses import dataclass
from abc import ABC, abstractmethod
import torch

# 导入现有的预测器
try:
    from .action_predictor import ActionPredictor, NarrativeCoherence
except ImportError:
    ActionPredictor = None
    NarrativeCoherence = None


@dataclass
class NarrativeResponse:
    """叙事响应"""
    main_narrative: str
    next_options: List[Tuple[str, str]]  # [(action, description), ...]
    next_predicted_action: Optional[Tuple[str, float]]  # (action, confidence)
    state_updates: Dict[str, str]
    metadata: Dict


class TextGenerationBackend(ABC):
    """文本生成后端抽象基类"""
    
    @abstractmethod
    def generate(self, prompt: str, max_length: int = 60, **kwargs) -> Optional[str]:
        pass


class DistilGPT2Backend(TextGenerationBackend):
    """DistilGPT2后端（用于测试/备用）"""
    
    def __init__(self, use_chinese_version: bool = True):
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            model_name = "distilgpt2-chinese" if use_chinese_version else "distilgpt2"
            
            print(f"[NLG] 加载DistilGPT2后端: {model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            self.model.eval()
            print(f"[NLG] ✓ DistilGPT2后端已加载")
        except Exception as e:
            print(f"[NLG] ✗ DistilGPT2后端加载失败: {e}")
            self.model = None
    
    def generate(self, prompt: str, max_length: int = 60, **kwargs) -> Optional[str]:
        """使用DistilGPT2生成文本"""
        
        if not self.model:
            return None
        
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=max_length,
                    temperature=kwargs.get("temperature", 0.7),
                    top_p=kwargs.get("top_p", 0.85),
                    top_k=kwargs.get("top_k", 40),
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    attention_mask=torch.ones_like(inputs)
                )
            
            # 提取生成的文本
            generated_ids = outputs[0][inputs.shape[-1]:]
            text = self.tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
            
            # 清理文本
            if text and not self._is_garbage_output(text):
                # 提取第一句完整的句子
                if "。" in text:
                    text = text.split("。")[0] + "。"
                elif "，" in text:
                    text = text.split("，")[0] + "，"
                
                if 10 < len(text) < 200:
                    return text
            
            return None
            
        except Exception as e:
            print(f"[NLG] DistilGPT2生成错误: {e}")
            return None
    
    def _is_garbage_output(self, text: str) -> bool:
        """检测是否为垃圾输出"""
        # 检查重复字符
        if len(text) > 5:
            last_chars = text[-5:]
            if len(set(last_chars)) == 1:
                return True
        
        # 检查重复模式
        for i in range(0, len(text) - 3, 2):
            pattern = text[i:i+2]
            if len(pattern) == 2 and text.count(pattern) > 3:
                return True
        
        # 检查全是符号
        symbols_only = text
        for sym in ["：", "·", "。", "，", "、", "-"]:
            symbols_only = symbols_only.replace(sym, "")
        
        return len(symbols_only) < 2


class Qwen25LoRABackend(TextGenerationBackend):
    """Qwen2.5-1.5B-Instruct + LoRA微调后端（支持4-bit量化 & 2秒响应控制）"""

    def __init__(
        self,
        lora_path: str,
        base_model: str = "Qwen/Qwen2.5-1.5B-Instruct",
        use_4bit: bool = False,
        fast_max_tokens: int = 60,
    ):
        """
        Args:
            lora_path:       LoRA适配器目录路径
            base_model:      基础模型名称或本地路径
            use_4bit:        是否使用4-bit量化（需bitsandbytes）
            fast_max_tokens: 首次响应的最大新token数，控制生成时间
                             T4 float16约40-50 tok/s → 60 tokens ≈ 1.5s
        """
        self.model = None
        self.tokenizer = None
        self.fast_max_tokens = fast_max_tokens
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
            from peft import PeftModel

            self.tokenizer = AutoTokenizer.from_pretrained(
                lora_path, trust_remote_code=True
            )

            # 构建量化配置
            if use_4bit and self.device == "cuda":
                print("[NLG] 使用4-bit量化加载基础模型（节省显存）...")
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
                base = AutoModelForCausalLM.from_pretrained(
                    base_model,
                    quantization_config=bnb_config,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
            else:
                dtype = torch.float16 if self.device == "cuda" else torch.float32
                print(f"[NLG] 加载基础模型: {base_model} (dtype={dtype}) ...")
                base = AutoModelForCausalLM.from_pretrained(
                    base_model,
                    torch_dtype=dtype,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
                base.to(self.device)

            print(f"[NLG] 加载LoRA适配器: {lora_path} ...")
            self.model = PeftModel.from_pretrained(base, lora_path)
            self.model.eval()
            print(f"[NLG] ✓ Qwen2.5-LoRA后端已加载 | device={self.device} | fast_max_tokens={fast_max_tokens}")
        except Exception as e:
            print(f"[NLG] ✗ Qwen2.5-LoRA后端加载失败: {e}")
            self.model = None

    def generate(self, prompt: str, max_length: int = None, **kwargs) -> Optional[str]:
        """
        使用Qwen2.5-LoRA生成文本。
        max_length 若为 None，则自动使用 fast_max_tokens（约2秒）。
        """
        if not self.model:
            return None
        max_new_tokens = max_length if max_length is not None else self.fast_max_tokens
        try:
            messages = [{"role": "user", "content": prompt}]
            text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=kwargs.get("temperature", 0.8),
                    top_p=kwargs.get("top_p", 0.9),
                    do_sample=True,
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            input_len = inputs["input_ids"].shape[-1]
            generated_ids = outputs[0][input_len:]
            result = self.tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
            return result if result else None
        except Exception as e:
            print(f"[NLG] Qwen2.5-LoRA生成错误: {e}")
            return None


class ColabRemoteBackend(TextGenerationBackend):
    """通过 HTTP 调用 Colab 上的 FastAPI 推理服务。
    支持两个接口：
      POST /generate    — 快速单次生成（2秒内）
      POST /two_stage   — 高质量双阶段生成（钩子 + 续写）
    """

    def __init__(self, base_url: str, timeout_fast: float = 3.5, timeout_slow: float = 30.0):
        """
        Args:
            base_url:     Colab cloudflared 公网地址，如 https://xxx.trycloudflare.com
            timeout_fast: /generate 接口超时秒数
            timeout_slow: /two_stage 接口超时秒数
        """
        import requests as _req
        self._requests = _req
        self.base_url = base_url.rstrip('/')
        self.timeout_fast = timeout_fast
        self.timeout_slow = timeout_slow
        self._available = self._check_health()

    def _check_health(self) -> bool:
        try:
            r = self._requests.get(f"{self.base_url}/health", timeout=5)
            if r.status_code == 200:
                print(f"[NLG] ✓ Colab 远程模型在线: {self.base_url}")
                return True
        except Exception as e:
            print(f"[NLG] ✗ Colab 远程模型不可达: {e}")
        return False

    @property
    def available(self) -> bool:
        return self._available

    def generate(self, prompt: str, max_length: int = 60, **kwargs) -> Optional[str]:
        """调用 /generate 接口，适合 2 秒内快速回答场景。"""
        if not self._available:
            return None
        try:
            resp = self._requests.post(
                f"{self.base_url}/generate",
                json={"prompt": prompt, "max_new_tokens": max_length},
                timeout=self.timeout_fast,
            )
            resp.raise_for_status()
            return resp.json().get("text", "").strip() or None
        except Exception as e:
            print(f"[NLG] Colab /generate 调用失败: {e}")
            return None

    def two_stage_generate(self, prompt: str,
                           hook_max_tokens: int = 24,
                           full_max_tokens: int = 220) -> Optional[Dict]:
        """调用 /two_stage 接口，返回 {'hook': ..., 'full_text': ..., 'hook_latency_sec': ...}。"""
        if not self._available:
            return None
        try:
            resp = self._requests.post(
                f"{self.base_url}/two_stage",
                json={
                    "prompt": prompt,
                    "hook_max_tokens": hook_max_tokens,
                    "full_max_tokens": full_max_tokens,
                },
                timeout=self.timeout_slow,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[NLG] Colab /two_stage 调用失败: {e}")
            return None


class EnhancedTemplateBackend(TextGenerationBackend):
    """增强型模板后端 - 动态组合模板生成连贯叙述"""
    
    def __init__(self):
        self.templates = self._build_template_database()
        self.connectors = self._build_connectors()
        self.intensity_levels = {
            "low": ["轻微的", "小小的", "一丝"],
            "medium": ["明显的", "相当的", "显著的"],
            "high": ["强烈的", "巨大的", "极度"]
        }
    
    def generate(self, prompt: str, max_length: int = 60, **kwargs) -> Optional[str]:
        """动态生成模板文本"""
        # 从prompt中提取关键信息
        context = kwargs.get("context", {})
        action = context.get("action", "move")
        location = context.get("location", "Hogwarts Castle")
        intensity = context.get("intensity", "medium")
        
        return self._compose_dynamic_narrative(action, location, intensity)
    
    def _build_template_database(self) -> Dict:
        """构建分层式模板数据库"""
        return {
            "Hogwarts Castle": {
                "opening": [
                    "霍格沃茨城堡的{intensifier}魔法",
                    "古老的城堡在{intensifier}舞动",
                    "{character}感受到{intensifier}的魔力"
                ],
                "action_bridge": {
                    "move": "继续沿走廊前进，",
                    "talk": "与周围的魔法师进行对话，",
                    "take": "发现并收集了魔法物品，",
                    "observe": "仔细观察周围的细节，",
                    "cast": "释放了强大的魔法，"
                },
                "consequence": [
                    "这改变了接下来发生的一切。",
                    "新的可能性开始浮现。",
                    "故事向新的方向发展。",
                    "命运之书翻过了新的一页。"
                ]
            },
            "Forbidden Forest": {
                "opening": [
                    "禁林中传来{intensifier}的声音，",
                    "{character}踏入了{intensifier}的魔法领地，",
                    "森林中蕴含着{intensifier}的能量"
                ],
                "action_bridge": {
                    "move": "向森林深处迈进，",
                    "talk": "与森林的古老灵魂进行交流，",
                    "take": "收集森林赐予的珍贵物品，",
                    "observe": "发现了隐藏在树根间的秘密，",
                    "cast": "让魔法与自然的力量相融合，"
                },
                "consequence": [
                    "自然的力量作出了回应。",
                    "森林向你敞开了新的通路。",
                    "你与这片古老的土地达成了共识。",
                    "魔法的平衡发生了细微的改变。"
                ]
            },
            "Diagon Alley": {
                "opening": [
                    "对角巷中充满了{intensifier}的魔法气息，",
                    "{character}在{intensifier}的商业氛围中穿行，",
                    "闪烁的光芒照亮了{intensifier}的交易"
                ],
                "action_bridge": {
                    "move": "在繁华的街道中穿梭，",
                    "talk": "与有影响力的商人进行交涉，",
                    "take": "发现了罕见的魔法商品，",
                    "observe": "察觉到了商业世界的隐秘一角，",
                    "cast": "展示了{character}的魔法实力，"
                },
                "consequence": [
                    "你的名声在魔法社区中传开了。",
                    "新的交易机会出现了。",
                    "你建立了重要的联系。",
                    "魔法市场对你有了新的认识。"
                ]
            },
            "Ministry of Magic": {
                "opening": [
                    "魔法部中政治的{intensifier}漩涡",
                    "{character}进入了权力的{intensifier}中枢，",
                    "官僚体制的{intensifier}压力扑面而来"
                ],
                "action_bridge": {
                    "move": "在部门间小心地穿行，",
                    "talk": "进行了一场{intensifier}的政治对话，",
                    "take": "获得了关键的文件证据，",
                    "observe": "发现了权力斗争的深层秘密，",
                    "cast": "在严格控制的环境中施放了魔法，"
                },
                "consequence": [
                    "我成为了某些人的目标。",
                    "信息的力量为我打开了新门。",
                    "政治的天平开始倾斜。",
                    "我的决定将影响魔法界的未来。"
                ]
            }
        }
    
    def _build_connectors(self) -> Dict:
        """构建故事连接词和过渡句"""
        return {
            "cause_effect": ["因此", "所以", "这导致了", "结果是"],
            "surprise": ["令人惊讶的是", "出人意料地", "突然间", "没想到"],
            "continuity": ["继续", "接着", "随后", "然后"],
            "revelation": ["真相是", "实际上", "隐藏的是", "secret is"]
        }
    
    def _compose_dynamic_narrative(self, action: str, location: str, intensity: str) -> str:
        """动态组合模板创建叙述"""
        
        if location not in self.templates:
            location = "Hogwarts Castle"
        
        templates = self.templates[location]
        
        # 获取强度级别的修饰词
        intensifier = random.choice(self.intensity_levels.get(intensity, self.intensity_levels["medium"]))
        
        # 组合各部分
        opening = random.choice(templates["opening"]).format(
            intensifier=intensifier,
            character="我"
        )
        
        bridge = templates["action_bridge"].get(action, templates["action_bridge"]["move"])
        bridge = bridge.format(intensifier=intensifier)
        
        consequence = random.choice(templates["consequence"])
        
        # 组合为完整叙述
        narrative = f"{opening}{bridge}{consequence}"
        follow_up = random.choice([
            "随后，更多的情节开始层层展开。",
            "接着，一种新的危险感在空气中弥漫。",
            "这一刻，我意识到故事才刚刚开始走向深处。",
            "很快，一段更复杂的剧情在眼前展开。"
        ])
        narrative = f"{narrative} {follow_up}"
        
        return narrative


class EnhancedNLGEngine:
    """增强型NLG引擎 - 集成轻量级模型和动作预测"""
    
    def __init__(self, 
                 backend: str = "template",
                 enable_action_prediction: bool = True,
                 enable_coherence_check: bool = True):
        """
        初始化增强型生成引擎
        
        Args:
            backend: "template"|"distilgpt2"|"qwen25_lora"|"colab_remote"|"auto"
            enable_action_prediction: 是否启用动作预测
            enable_coherence_check: 是否启用连贯性检查
        """
        
        self.backend = self._init_backend(backend)
        self.action_predictor = ActionPredictor() if enable_action_prediction else None
        self.coherence_checker = NarrativeCoherence() if enable_coherence_check else None
        
        # 故事历史跟踪
        self.narrative_history = []
        self.player_action_history = []
        
        # HP宇宙约束
        self.hp_constraints = {
            "forbidden_words": ["宇航员", "火箭", "计算机", "汽车"],
            "mandatory_locations": ["霍格沃茨", "禁林", "对角巷", "魔法部"],
            "key_characters": ["哈利", "赫敏", "罗恩", "邓布利多"]
        }
    
    def generate_narrative(self,
                          user_action: str,
                          game_state: Dict,
                          retrieved_context: Optional[List[Dict]] = None,
                          intent: str = "move") -> NarrativeResponse:
        """
        生成增强型叙述响应
        
        Args:
            user_action: 用户输入的行动描述
            game_state: 当前游戏状态字典
            retrieved_context: RAG检索到的上下文
            intent: 识别到的意图（move, talk, take等）
        
        Returns:
            NarrativeResponse 对象
        """
        
        character = game_state.get('player_character', '巫师')
        location = game_state.get('current_location', 'Hogwarts Castle')
        round_num = game_state.get('round', 1)
        
        print(f"\n[NLG] 生成第{round_num}轮叙述 | 位置: {location} | 意图: {intent}")
        
        # 1. 生成主叙述
        narrative = self._generate_main_narrative(
            user_action, character, location, intent, 
            retrieved_context, game_state
        )
        
        # 2. 生成下一步选项
        next_options = self._generate_next_options(game_state, location, intent)
        
        # 3. 预测下一个行动
        next_predicted = None
        if self.action_predictor:
            action, confidence = self.action_predictor.predict_next_action(
                intent, game_state, self.player_action_history, location
            )
            next_predicted = (action, confidence)
        
        # 4. 提取状态变化
        state_updates = self._extract_state_changes(user_action, intent, location)
        
        # 5. 收集元数据
        metadata = {
            "model": type(self.backend).__name__,
            "intent": intent,
            "coherence_validated": self.coherence_checker is not None,
            "action_predicted": next_predicted is not None,
            "context_segments": len(retrieved_context) if retrieved_context else 0
        }
        
        # 6. 更新历史
        self.narrative_history.append(narrative)
        self.player_action_history.append(intent)
        
        return NarrativeResponse(
            main_narrative=narrative,
            next_options=next_options,
            next_predicted_action=next_predicted,
            state_updates=state_updates,
            metadata=metadata
        )
    
    def _init_backend(self, backend: str) -> TextGenerationBackend:
        """初始化文本生成后端"""

        if backend == "colab_remote":
            print("[NLG] 尝试使用 Colab 远程后端")
            try:
                from config import ModelConfig
                base_url = getattr(ModelConfig, "COLAB_MODEL_URL", "").strip()
                timeout_fast = float(getattr(ModelConfig, "COLAB_TIMEOUT_FAST", 3.5))
                timeout_slow = float(getattr(ModelConfig, "COLAB_TIMEOUT_SLOW", 30.0))
            except Exception:
                base_url = ""
                timeout_fast = 3.5
                timeout_slow = 30.0

            if not base_url:
                print("[NLG] COLAB_MODEL_URL 未配置，回退到模板后端")
                return EnhancedTemplateBackend()

            remote_backend = ColabRemoteBackend(
                base_url=base_url,
                timeout_fast=timeout_fast,
                timeout_slow=timeout_slow,
            )
            if remote_backend.available:
                return remote_backend

            print("[NLG] Colab远程后端不可用，回退到模板后端")
            return EnhancedTemplateBackend()

        elif backend == "qwen25_lora":
            print("[NLG] 尝试使用Qwen2.5-LoRA后端")
            try:
                from config import ModelConfig
                lora_path = str(ModelConfig.FINETUNED_MODEL_PATH)
                base_model = ModelConfig.FINETUNED_BASE_MODEL
                use_4bit = getattr(ModelConfig, "USE_4BIT_QUANTIZATION", False)
                fast_max_tokens = getattr(ModelConfig, "FAST_MAX_NEW_TOKENS", 60)
            except Exception:
                import os
                lora_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    "models", "qwen2_5_1_5b_lora"
                )
                base_model = "Qwen/Qwen2.5-1.5B-Instruct"
                use_4bit = False
                fast_max_tokens = 60
            qwen_backend = Qwen25LoRABackend(
                lora_path, base_model,
                use_4bit=use_4bit,
                fast_max_tokens=fast_max_tokens,
            )
            if qwen_backend.model:
                return qwen_backend
            print("[NLG] Qwen2.5-LoRA加载失败，回退到模板后端")
            return EnhancedTemplateBackend()

        elif backend == "template":
            print("[NLG] 使用增强型模板后端")
            return EnhancedTemplateBackend()
        
        elif backend == "distilgpt2":
            print("[NLG] 尝试使用DistilGPT2后端")
            dgpt2 = DistilGPT2Backend(use_chinese_version=True)
            if dgpt2.model:
                return dgpt2
            # 如果失败，fallback到template
            print("[NLG] DistilGPT2加载失败，回退到模板后端")
            return EnhancedTemplateBackend()
        
        else:  # "auto"
            print("[NLG] 自动选择后端...")
            try:
                from config import ModelConfig
                use_colab_remote = bool(getattr(ModelConfig, "USE_COLAB_REMOTE", False))
                colab_url = str(getattr(ModelConfig, "COLAB_MODEL_URL", "")).strip()
                use_finetuned = bool(getattr(ModelConfig, "USE_FINETUNED_MODEL", False))
            except Exception:
                use_colab_remote = False
                colab_url = ""
                use_finetuned = False

            if use_colab_remote and colab_url:
                remote_backend = self._init_backend("colab_remote")
                if not isinstance(remote_backend, EnhancedTemplateBackend):
                    print("[NLG] ✓ 使用 Colab 远程后端")
                    return remote_backend

            if use_finetuned:
                qwen_backend = self._init_backend("qwen25_lora")
                if not isinstance(qwen_backend, EnhancedTemplateBackend):
                    print("[NLG] ✓ 使用 Qwen2.5-LoRA 本地后端")
                    return qwen_backend

            try:
                dgpt2 = DistilGPT2Backend(use_chinese_version=True)
                if dgpt2.model:
                    print("[NLG] ✓ 使用DistilGPT2后端")
                    return dgpt2
            except Exception as e:
                print(f"[NLG] DistilGPT2不可用: {e}")
            
            print("[NLG] ✓ 使用增强型模板后端")
            return EnhancedTemplateBackend()
    
    def _generate_main_narrative(self,
                                user_action: str,
                                character: str,
                                location: str,
                                intent: str,
                                retrieved_context: Optional[List[Dict]],
                                game_state: Dict) -> str:
        """生成主叙述"""
        
        # 确定强度级别（基于游戏进度）
        round_num = game_state.get('round', 1)
        if round_num < 3:
            intensity = "low"
        elif round_num < 8:
            intensity = "medium"
        else:
            intensity = "high"
        
        # 构建生成上下文
        context = {
            "action": intent,
            "location": location,
            "intensity": intensity,
            "character": character,
            "round": round_num
        }

        # 远程后端可选走高质量双阶段接口。
        if hasattr(self.backend, "two_stage_generate"):
            try:
                staged = self.backend.two_stage_generate(
                    prompt=f"{character}在{location}。动作：{user_action}。",
                    hook_max_tokens=24,
                    full_max_tokens=220,
                )
                if staged and staged.get("full_text"):
                    return staged["full_text"].strip()
            except Exception as e:
                print(f"[NLG] two_stage调用失败，回退单次生成: {e}")
        
        # 使用后端生成
        prompt = f"{character}在{location}。动作：{user_action}。"
        narrative = self.backend.generate(
            prompt,
            max_length=160,
            context=context,
            temperature=0.75
        )
        
        if not narrative:
            # 备用方案
            narrative = self._fallback_narrative(intent, location, character)
        
        # 验证连贯性
        if self.coherence_checker and self.narrative_history:
            is_coherent, explanation = self.coherence_checker.validate_narrative_flow(
                narrative, self.narrative_history[-1], intent, game_state
            )
            print(f"[Coherence] {explanation}")
        
        return narrative
    
    def _fallback_narrative(self, intent: str, location: str, character: str) -> str:
        """备用叙述生成"""
        
        fallback_templates = {
            "move": f"我在{location}中前进，寻找下一个冒险。",
            "talk": f"我与{location}中的某人进行了有意义的对话。",
            "take": f"我发现了一件有趣的物品，并小心地收了起来。",
            "observe": f"我观察到{location}中隐没的细节，获得了新的洞察。",
            "cast": f"我释放了魔法，{location}中的力量做出了回应。",
            "examine": f"我仔细检查周围，发现了值得注意的东西。"
        }
        
        return fallback_templates.get(intent, f"我在{location}采取了行动。")
    
    def _generate_next_options(self, game_state: Dict, location: str, current_intent: str) -> List[Tuple[str, str]]:
        """生成下一步选项"""
        
        if self.action_predictor:
            return self.action_predictor.predict_next_options(
                game_state, location
            )
        
        # 备用选项
        default_options = [
            ("move", "继续探索"),
            ("talk", "与人交谈"),
            ("observe", "仔细观察"),
            ("cast", "施放魔法")
        ]
        
        return default_options
    
    def _extract_state_changes(self, user_action: str, intent: str, location: str) -> Dict:
        """提取需要更新的游戏状态"""
        
        changes = {
            "last_action": intent,
            "last_location": location
        }
        
        # 检查位置变化
        location_keywords = {
            "Hogwarts Castle": ["霍格沃茨", "城堡", "走廊"],
            "Forbidden Forest": ["禁林", "森林"],
            "Diagon Alley": ["对角巷", "街道"],
            "Ministry of Magic": ["魔法部", "权力"]
        }
        
        for loc, keywords in location_keywords.items():
            if any(kw in user_action for kw in keywords):
                changes["current_location"] = loc
                break
        
        return changes


# 为了兼容性保留原始接口
NLGEngine = EnhancedNLGEngine
