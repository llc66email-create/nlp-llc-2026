"""
NLU模块 - 自然语言理解（意图识别、实体抽取、澄清）
"""
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re
from transformers import pipeline
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# 下载必要的NLTK数据
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

class Intent(Enum):
    """预定义的意图"""
    # 导航相关
    MOVE = "move"
    LOOK = "look"
    EXAMINE = "examine"
    
    # 互动相关
    TALK = "talk"
    INTERACT = "interact"
    CAST_SPELL = "cast_spell"
    
    # 物品相关
    TAKE = "take"
    DROP = "drop"
    USE = "use"
    GIVE = "give"
    
    # 信息相关
    QUERY = "query"
    INVENTORY = "inventory"
    STATUS = "status"
    
    # 其他
    UNKNOWN = "unknown"
    CLARIFY = "clarify"

@dataclass
class Entity:
    """实体数据类"""
    type: str  # character, location, item, spell, action
    value: str
    confidence: float
    start_pos: int
    end_pos: int

@dataclass
class IntentResult:
    """意图识别结果"""
    intent: Intent
    confidence: float
    entities: List[Entity]
    raw_input: str
    requires_clarification: bool = False
    clarification_message: Optional[str] = None

class NLUEngine:
    """自然语言理解引擎"""
    
    # 意图关键词映射
    INTENT_KEYWORDS = {
        Intent.MOVE: ["go to", "move", "walk", "head", "travel", "explore"],
        Intent.LOOK: ["look", "see", "observe", "notice", "watch"],
        Intent.EXAMINE: ["examine", "check", "inspect", "read", "study"],
        Intent.TALK: ["talk", "speak", "say", "ask", "tell", "chat"],
        Intent.INTERACT: ["interact", "touch", "open", "close", "use"],
        Intent.CAST_SPELL: ["cast", "spell", "hex", "curse", "charm"],
        Intent.TAKE: ["take", "grab", "pick up", "get", "obtain"],
        Intent.DROP: ["drop", "leave", "put down", "discard"],
        Intent.USE: ["use", "apply", "wield"],
        Intent.GIVE: ["give", "hand", "pass", "offer"],
        Intent.QUERY: ["who", "what", "where", "when", "why", "how"],
        Intent.INVENTORY: ["inventory", "items", "backpack", "check items"],
        Intent.STATUS: ["status", "health", "condition"],
    }
    
    # 实体类型特征词
    ENTITY_PATTERNS = {
        "character": {
            "keywords": ["Harry", "Hermione", "Ron", "Dumbledore", "Snape", "Voldemort", "Lucius", "Draco"],
            "pattern": None
        },
        "location": {
            "keywords": ["Hogwarts", "Diagon Alley", "Forbidden Forest", "Chamber of Secrets", 
                        "Great Hall", "Common Room", "Potions Dungeon", "Gryffindor Tower"],
            "pattern": None
        },
        "spell": {
            "keywords": ["Expelliarmus", "Stupefy", "Avada Kedavra", "Crucio", "Obliviate"],
            "pattern": r"[A-Z][a-z]+\s+[A-Z][a-z]+"
        },
        "item": {
            "keywords": ["wand", "potion", "book", "key", "map", "letter", "Horcrux"],
            "pattern": None
        },
        "action": {
            "keywords": ["run", "hide", "flee", "attack", "defend", "protect"],
            "pattern": None
        }
    }
    
    def __init__(self, confidence_threshold: float = 0.6):
        """初始化NLU引擎"""
        self.confidence_threshold = confidence_threshold
        
        # 禁用Transformers模型（太耗时）
        # try:
        #     self.zero_shot_classifier = pipeline(
        #         "zero-shot-classification",
        #         model="facebook/bart-large-mnli"
        #     )
        # except Exception as e:
        #     print(f"警告: 无法加载零样本分类器: {e}")
        #     self.zero_shot_classifier = None
        
        self.zero_shot_classifier = None
        
        # 停用词
        self.stop_words = set()
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            pass
    
    def process(self, user_input: str) -> IntentResult:
        """处理用户输入并返回意图结果"""
        user_input = user_input.strip()
        
        # 提取实体
        entities = self._extract_entities(user_input)
        
        # 识别意图
        intent, confidence = self._classify_intent(user_input, entities)
        
        # 检查是否需要澄清
        requires_clarification = confidence < self.confidence_threshold
        clarification_message = None
        
        if requires_clarification:
            clarification_message = self._generate_clarification(user_input, intent, entities)
        
        return IntentResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            raw_input=user_input,
            requires_clarification=requires_clarification,
            clarification_message=clarification_message
        )
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """从文本中提取实体"""
        entities = []
        text_lower = text.lower()
        
        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            # 基于关键词的提取
            for keyword in patterns["keywords"]:
                pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                for match in pattern.finditer(text):
                    entity = Entity(
                        type=entity_type,
                        value=match.group(),
                        confidence=0.9,
                        start_pos=match.start(),
                        end_pos=match.end()
                    )
                    # 避免重复
                    if not any(e.value == entity.value and e.type == entity.type for e in entities):
                        entities.append(entity)
            
            # 基于正则表达式的提取
            if patterns["pattern"]:
                regex = re.compile(patterns["pattern"])
                for match in regex.finditer(text):
                    entity = Entity(
                        type=entity_type,
                        value=match.group(),
                        confidence=0.7,
                        start_pos=match.start(),
                        end_pos=match.end()
                    )
                    if not any(e.value == entity.value and e.type == entity.type for e in entities):
                        entities.append(entity)
        
        return sorted(entities, key=lambda e: e.start_pos)
    
    def _classify_intent(self, text: str, entities: List[Entity]) -> Tuple[Intent, float]:
        """分类意图"""
        text_lower = text.lower()
        intent_scores: Dict[Intent, float] = {}
        
        # 基于关键词匹配计算分数
        for intent_type, keywords in self.INTENT_KEYWORDS.items():
            score = 0.0
            matches = 0
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1.0
                    matches += 1
            
            # 基于匹配次数正规化分数
            if matches > 0:
                intent_scores[intent_type] = min(1.0, score / max(len(keywords) * 0.5, 1))
            else:
                intent_scores[intent_type] = 0.0
        
        # 使用零样本分类进行增强（如果可用）
        if self.zero_shot_classifier is not None:
            try:
                candidate_labels = [intent.value for intent in Intent if intent != Intent.UNKNOWN]
                result = self.zero_shot_classifier(text, candidate_labels, multi_class=True)
                
                for label, score in zip(result['labels'], result['scores']):
                    try:
                        intent_enum = Intent[label.upper().replace(" ", "_")]
                        # 融合分数
                        intent_scores[intent_enum] = max(
                            intent_scores.get(intent_enum, 0.0),
                            score * 0.7  # 给予较低的权重
                        )
                    except KeyError:
                        pass
            except Exception:
                pass
        
        # 获取最高分的意图
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
        else:
            best_intent = Intent.UNKNOWN
            confidence = 0.0
        
        return best_intent, confidence
    
    def _generate_clarification(self, user_input: str, intent: Intent, 
                               entities: List[Entity]) -> str:
        """生成澄清问题"""
        clarifications = {
            Intent.MOVE: "我理解你想移动。请问你想去哪里？",
            Intent.TALK: "你想和谁交谈？请提供更多细节。",
            Intent.CAST_SPELL: "你想施放哪个咒语？",
            Intent.TAKE: "你想拿什么物品？",
            Intent.USE: "你想使用什么？",
            Intent.QUERY: "你想了解什么？请提供更具体的问题。",
            Intent.UNKNOWN: "对不起，我不太理解。你能重新表述一下吗？"
        }
        
        return clarifications.get(intent, "我需要更多信息。请提供更多细节。")
    
    def get_entity_by_type(self, entities: List[Entity], entity_type: str) -> Optional[Entity]:
        """获取特定类型的第一个实体"""
        for entity in entities:
            if entity.type == entity_type:
                return entity
        return None
    
    def get_entities_by_type(self, entities: List[Entity], entity_type: str) -> List[Entity]:
        """获取特定类型的所有实体"""
        return [e for e in entities if e.type == entity_type]


# 用于测试的快速方法
def test_nlu():
    """测试NLU引擎"""
    nlu = NLUEngine()
    
    test_inputs = [
        "Go to Hogwarts",
        "Talk to Harry Potter",
        "Cast Expelliarmus",
        "Look around",
        "Take the Horcrux"
    ]
    
    for user_input in test_inputs:
        result = nlu.process(user_input)
        print(f"\n输入: {user_input}")
        print(f"意图: {result.intent.value} (信度: {result.confidence:.2f})")
        print(f"实体: {[(e.type, e.value) for e in result.entities]}")
        if result.requires_clarification:
            print(f"澄清: {result.clarification_message}")

if __name__ == "__main__":
    test_nlu()
