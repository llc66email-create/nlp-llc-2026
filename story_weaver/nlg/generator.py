"""
NLG模块 - 动态故事推进系统 v2
关键特性：
1. 约束提示词 - 确保内容在哈利波特宇宙
2. 动态生成 - 根据用户输入推进故事
3. 状态跟踪 - 记录故事进展
4. 智能回退 - LLM失败时有高质量模板
"""

from typing import List, Dict, Optional
import json
from dataclasses import dataclass
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import random

@dataclass
class NarrativeResponse:
    """叙事响应"""
    main_narrative: str
    next_options: List[str]
    state_updates: Dict[str, str]
    metadata: Dict


class NLGEngine:
    """动态故事生成引擎"""
    
    def __init__(self, model_name: str = "distilgpt2", use_llm: bool = True):
        self.model_name = model_name
        self.use_llm = use_llm
        self.tokenizer = None
        self.model = None
        self.device = "cpu"
        
        # 哈利波特宇宙约束
        self.hp_constraints = {
            "forbidden": ["宇航员", "火箭", "计算机", "汽车", "飞机"],
            "locations": ["霍格沃茨", "禁林", "对角巷", "魔法部", "格林戈茨"],
            "characters": ["哈利", "赫敏", "罗恩", "邓布利多", "斯内普"]
        }
        
        if self.use_llm:
            self._load_model()
    
    def _load_model(self):
        """加载LLM"""
        try:
            print(f"[NLG] 加载动态故事生成模型: {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, 
                trust_remote_code=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            self.model.eval()
            print(f"[NLG] ✓ 模型已加载")
        except Exception as e:
            print(f"[NLG] ⚠️ 加载失败: {e}，使用模板模式")
            self.use_llm = False
    
    def generate_narrative(self, 
                          user_action: str,
                          game_state: Dict,
                          retrieved_segments: List[Dict],
                          intent: str,
                          entities: List[Dict]) -> NarrativeResponse:
        """生成动态故事"""
        
        # 使用约束提示词生成故事
        narrative = self._generate_dynamic_story(
            user_action=user_action,
            game_state=game_state,
            intent=intent
        )
        
        # 生成选项
        options = self._generate_options(game_state, intent)
        
        # 生成状态更新
        state_updates = self._extract_state_changes(user_action, intent)
        
        # 元数据
        metadata = {
            "model": "动态故事推进",
            "intent": intent,
            "is_constrained": True
        }
        
        return NarrativeResponse(
            main_narrative=narrative,
            next_options=options,
            state_updates=state_updates,
            metadata=metadata
        )
    
    def _generate_dynamic_story(self, user_action: str, game_state: Dict, 
                               intent: str) -> str:
        """生成动态推进的故事"""
        
        character = game_state.get('player_character', '巫师')
        location = game_state.get('current_location', '霍格沃茨')
        
        # 如果有LLM，使用约束生成
        if self.use_llm and self.model and self.tokenizer:
            story = self._llm_generate_with_constraints(
                user_action, character, location, intent
            )
            if story:
                return story
        
        # 回退到模板
        return self._template_generate_story(
            user_action, character, location, intent
        )
    
    def _llm_generate_with_constraints(self, user_action: str, character: str,
                                       location: str, intent: str) -> Optional[str]:
        """使用约束提示词的LLM生成"""
        try:
            # 构建约束提示
            prompt = f"""【哈利波特故事叙述】
角色: {character}
位置: {location}
行动: {user_action}

请生成一个50-80字的故事片段。要求：
✓ 严格遵守哈利波特设定
✓ 推进故事情节
✓ 与用户行动相关
✗ 禁止提及现实事物：宇航员、计算机、汽车等

故事开始："""
            
            inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=80,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            story = text[len(prompt):].strip()
            
            # 检查禁止词
            for forbidden in self.hp_constraints["forbidden"]:
                if forbidden.lower() in story.lower():
                    print(f"[NLG] 检测到禁止词，使用模板")
                    return None
            
            # 获取第一句完整句子
            if "。" in story:
                story = story.split("。")[0] + "。"
            
            if 20 < len(story) < 200:
                print(f"[NLG] ✓ 动态生成: {story[:60]}...")
                return story
            
            return None
            
        except Exception as e:
            print(f"[NLG] 生成失败: {e}")
            return None
    
    def _template_generate_story(self, user_action: str, character: str,
                                location: str, intent: str) -> str:
        """模板回退生成"""
        
        templates = {
            "move": [
                f"{character}在{location}中缓缓前行，脚步声在空气中回荡。",
                f"周围的魔法气息变得更加浓厚，引导着{character}前进。",
                f"{character}推开一扇古老的门，发现了{location}的新区域。"
            ],
            "talk": [
                f"一个熟悉的身影出现，与{character}开始了一场意味深长的对话。",
                f"{character}的话语在{location}中引起了意外的反应。",
                f"对话进行得比预期更加深入和有趣。"
            ],
            "take": [
                f"{character}小心翼翼地拿起物品，感受到魔力的涌动。",
                f"这件物品在{location}中闪闪发光，等待着被发现。",
                f"得到这件物品的瞬间，一切似乎重新燃起了希望。"
            ],
            "observe": [
                f"{character}仔细观察{location}，发现了隐藏的细节。",
                f"观察越深入，{location}的秘密越来越清晰。",
                f"你注意到其他人都忽视了的关键线索。"
            ],
            "cast": [
                f"{character}在{location}中挥动魔杖，魔咒在空气中闪耀。",
                f"魔法能量在{character}周围凝聚，准备释放强大的力量。",
                f"咒语的效果超出了{character}的预期。"
            ]
        }
        
        story_list = templates.get(intent, templates["move"])
        return random.choice(story_list)
    
    def _generate_options(self, game_state: Dict, intent: str) -> List[str]:
        """生成下一步选项"""
        location = game_state.get('current_location', '霍格沃茨')
        
        location_options = {
            "Hogwarts Castle": [
                "前往魔咒课教室",
                "走向公共休息室",
                "进入图书馆",
                "上楼到塔楼"
            ],
            "Forbidden Forest": [
                "深入森林探索",
                "返回城堡",
                "寻找神奇生物",
                "收集魔法植物"
            ],
            "Diagon Alley": [
                "进入魔杖店",
                "访问古灵阁",
                "逛书店",
                "购买魔药材料"
            ]
        }
        
        default_options = [
            "继续探索",
            "与人交谈",
            "观察周围",
            "尝试魔法"
        ]
        
        return location_options.get(location, default_options)
    
    def _extract_state_changes(self, user_action: str, intent: str) -> Dict[str, str]:
        """提取需要更新的游戏状态"""
        changes = {
            "action_performed": intent,
            "timestamp": str(__import__('time').time())
        }
        
        # 检查位置变化
        locations = ["禁林", "对角巷", "霍格沃茨", "魔法部"]
        for loc in locations:
            if loc in user_action:
                changes["location"] = loc
                break
        
        return changes


class DialogueGenerator:
    """对话生成器（为了兼容性）"""
    def __init__(self):
        pass
    
    def generate_dialogue(self, context: Dict) -> str:
        """生成对话"""
        return "嗯...我不确定如何回应那个。"

