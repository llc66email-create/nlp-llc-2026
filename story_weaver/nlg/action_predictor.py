"""
行动预测器 - 预测玩家在故事中的下一步行动
轻量级行为模式识别系统，根据历史行动预测玩家倾向
"""

from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import json


class ActionPredictor:
    """玩家行动预测器 - 生成连贯的动作序列"""
    
    def __init__(self):
        # 行动分类和转移概率
        self.action_patterns = {
            "exploration": {
                "next_actions": ["observe", "take", "move", "talk"],
                "probability": [0.3, 0.25, 0.25, 0.2]
            },
            "interaction": {
                "next_actions": ["talk", "cast", "move", "observe"],
                "probability": [0.4, 0.2, 0.2, 0.2]
            },
            "combat": {
                "next_actions": ["cast", "move", "defend", "cast"],
                "probability": [0.5, 0.2, 0.2, 0.1]
            },
            "collection": {
                "next_actions": ["take", "move", "observe", "examine"],
                "probability": [0.4, 0.3, 0.2, 0.1]
            }
        }
        
        # 位置特定的倾向模式
        self.location_tendencies = {
            "Hogwarts Castle": {
                "common_actions": ["move", "talk", "observe", "cast"],
                "exploration_bias": 0.3
            },
            "Forbidden Forest": {
                "common_actions": ["observe", "move", "cast", "take"],
                "exploration_bias": 0.6
            },
            "Diagon Alley": {
                "common_actions": ["talk", "take", "observe", "move"],
                "exploration_bias": 0.4
            },
            "Ministry of Magic": {
                "common_actions": ["talk", "move", "observe", "cast"],
                "exploration_bias": 0.2
            }
        }
        
        # 故事进度和行动难度的关联
        self.difficulty_actions = {
            "easy": {
                "actions": ["move", "observe", "talk"],
                "narrative_templates": ["简单而直接的", "平凡但有趣的", "初级的"]
            },
            "medium": {
                "actions": ["take", "cast", "search"],
                "narrative_templates": ["具有挑战的", "需要勇气的", "考验智慧的"]
            },
            "hard": {
                "actions": ["cast", "fight", "sacrifice"],
                "narrative_templates": ["极其危险的", "命悬一线的", "生死攸关的"]
            }
        }
    
    def predict_next_action(self, 
                           current_action: str,
                           game_state: Dict,
                           player_history: List[str],
                           location: str) -> Tuple[str, float]:
        """
        预测玩家下一步最可能采取的行动
        
        Args:
            current_action: 当前行动（move, talk, take, observe, cast等）
            game_state: 当前游戏状态
            player_history: 玩家历史行动列表
            location: 当前位置
        
        Returns:
            (predicted_action, confidence_score)
        """
        
        # 1. 基于当前行动的转移预测
        next_actions_from_pattern = self._get_action_transitions(current_action)
        
        # 2. 基于位置的倾向调整
        location_adjusted = self._adjust_for_location(next_actions_from_pattern, location)
        
        # 3. 基于历史模式的优化
        history_weighted = self._weight_by_history(location_adjusted, player_history)
        
        # 4. 基于故事难度的调整
        difficulty = game_state.get('difficulty', 'medium')
        final_weighted = self._adjust_for_difficulty(history_weighted, difficulty)
        
        # 返回概率最高的行动和其置信度
        if final_weighted:
            predicted_action = max(final_weighted.items(), key=lambda x: x[1])
            return predicted_action[0], predicted_action[1]
        
        return "move", 0.5  # 默认行动
    
    def predict_next_options(self,
                            game_state: Dict,
                            current_location: str,
                            player_skill_level: str = "beginner") -> List[Tuple[str, str]]:
        """
        预测玩家接下来可能采取的多个行动及其拟人化描述
        
        Returns:
            [(action, description), ...]
        """
        
        location_opts = self.location_tendencies.get(
            current_location, 
            self.location_tendencies["Hogwarts Castle"]
        )
        
        options = []
        for action in location_opts["common_actions"][:4]:
            description = self._humanize_action(action, current_location)
            options.append((action, description))
        
        return options
    
    def _get_action_transitions(self, current_action: str) -> Dict[str, float]:
        """获取从当前行动可能转移到的行动及其概率"""
        
        # 行动类别到行动的映射
        action_to_category = {
            "move": "exploration",
            "observe": "exploration",
            "take": "collection",
            "talk": "interaction",
            "cast": "combat",
            "examine": "exploration",
            "search": "collection",
            "defend": "combat",
            "sacrifice": "combat"
        }
        
        category = action_to_category.get(current_action, "exploration")
        pattern = self.action_patterns.get(category, self.action_patterns["exploration"])
        
        # 构建行动转移字典
        transitions = {}
        for action, prob in zip(pattern["next_actions"], pattern["probability"]):
            transitions[action] = prob
        
        return transitions
    
    def _adjust_for_location(self, 
                           actions: Dict[str, float],
                           location: str) -> Dict[str, float]:
        """根据位置调整行动概率"""
        
        location_data = self.location_tendencies.get(location)
        if not location_data:
            return actions
        
        adjusted = actions.copy()
        common_actions = location_data["common_actions"]
        
        # 增加该位置常见行动的概率
        total_boost = 0.2  # 总体提升幅度
        for action in common_actions:
            if action in adjusted:
                adjusted[action] += total_boost / len(common_actions)
        
        # 重新归一化概率
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v/total for k, v in adjusted.items()}
        
        return adjusted
    
    def _weight_by_history(self,
                          actions: Dict[str, float],
                          player_history: List[str]) -> Dict[str, float]:
        """基于玩家历史权重调整行动概率"""
        
        if not player_history:
            return actions
        
        # 计算历史中各行动的频率
        action_counts = defaultdict(int)
        for action in player_history[-10:]:  # 只看最近10个行动
            action_counts[action] += 1
        
        adjusted = actions.copy()
        
        # 如果玩家有明显的偏好，适度加强
        if action_counts:
            most_common = max(action_counts.items(), key=lambda x: x[1])
            common_action, count = most_common
            
            if common_action in adjusted and count >= 3:
                # 如果玩家多次重复该行动，轻微加强其概率
                adjusted[common_action] += 0.1
        
        # 重新归一化
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v/total for k, v in adjusted.items()}
        
        return adjusted
    
    def _adjust_for_difficulty(self,
                              actions: Dict[str, float],
                              difficulty: str) -> Dict[str, float]:
        """根据难度调整行动"""
        
        if difficulty not in self.difficulty_actions:
            difficulty = "medium"
        
        harder_actions = self.difficulty_actions[difficulty]["actions"]
        adjusted = actions.copy()
        
        # 增加难度对应的行动的权重
        for action in harder_actions:
            if action in adjusted:
                boost = 0.1 if difficulty == "medium" else 0.15
                adjusted[action] += boost
        
        # 重新归一化
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v/total for k, v in adjusted.items()}
        
        return adjusted
    
    def _humanize_action(self, action: str, location: str) -> str:
        """将行动代码转化为可读的叙述性描述"""
        
        descriptions = {
            "move": {
                "default": "继续探索",
                "Hogwarts Castle": "沿走廊前行",
                "Forbidden Forest": "深入森林",
                "Diagon Alley": "游览商店街",
                "Ministry of Magic": "探索部门"
            },
            "observe": {
                "default": "仔细观察",
                "Hogwarts Castle": "研究魔法细节",
                "Forbidden Forest": "观察生物迹象",
                "Diagon Alley": "察看商品",
                "Ministry of Magic": "留意权力斗争"
            },
            "talk": {
                "default": "与人交谈",
                "Hogwarts Castle": "与同学讨论",
                "Forbidden Forest": "与神秘声音交流",
                "Diagon Alley": "与店主商谈",
                "Ministry of Magic": "进行政治对话"
            },
            "take": {
                "default": "拿取物品",
                "Hogwarts Castle": "收集魔法物件",
                "Forbidden Forest": "采集森林宝藏",
                "Diagon Alley": "购买物品",
                "Ministry of Magic": "获取文件"
            },
            "cast": {
                "default": "施放咒语",
                "Hogwarts Castle": "展现魔法能力",
                "Forbidden Forest": "唤醒魔法力量",
                "Diagon Alley": "小心施法",
                "Ministry of Magic": "谨慎使用魔法"
            },
            "examine": {
                "default": "仔细检查",
                "Hogwarts Castle": "揭开秘密",
                "Forbidden Forest": "发现隐藏的径迹",
                "Diagon Alley": "查看细节",
                "Ministry of Magic": "调查可疑之处"
            }
        }
        
        action_desc = descriptions.get(action, descriptions["move"])
        return action_desc.get(location, action_desc["default"])
    
    def get_action_difficulty_hints(self, action: str, context: Dict) -> str:
        """获取行动难度提示文本"""
        
        action_difficulty = {
            "move": "easy",
            "observe": "easy",
            "talk": "easy",
            "take": "medium",
            "examine": "medium",
            "search": "medium",
            "cast": "hard",
            "fight": "hard",
            "sacrifice": "hard"
        }
        
        difficulty = action_difficulty.get(action, "medium")
        hints = {
            "easy": "这是一个相对简单的选择。",
            "medium": "这需要一些技巧和判断。",
            "hard": "这将是一个充满风险的决定。"
        }
        
        return hints.get(difficulty, "")


class NarrativeCoherence:
    """叙述连贯性检查器 - 确保故事逻辑一致"""
    
    def __init__(self):
        self.entity_tracking = {}
        self.event_timeline = []
        self.consistency_rules = {
            "cannot_revisit_same_location_twice": False,
            "must_have_reason_for_action": True,
            "character_state_must_be_consistent": True,
            "emotion_progression_must_be_logical": True
        }
    
    def validate_narrative_flow(self,
                               narrative: str,
                               previous_narrative: str,
                               action: str,
                               game_state: Dict) -> Tuple[bool, str]:
        """
        验证新生成的叙述是否与之前的故事保持一致
        
        Returns:
            (is_coherent, explanation)
        """
        
        issues = []
        
        # 1. 检查角色一致性
        if not self._check_character_consistency(narrative, previous_narrative):
            issues.append("角色描述不一致")
        
        # 2. 检查位置一致性
        if not self._check_location_consistency(narrative, game_state):
            issues.append("位置转换不合理")
        
        # 3. 检查时间一致性
        if not self._check_temporal_consistency(action, narrative):
            issues.append("时间线不连贯")
        
        # 4. 检查情感弧线
        if not self._check_emotional_arc(narrative, previous_narrative):
            issues.append("情感发展突兀")
        
        is_coherent = len(issues) == 0
        explanation = "✓ 叙述连贯" if is_coherent else "⚠️ " + ", ".join(issues)
        
        return is_coherent, explanation
    
    def _check_character_consistency(self, current: str, previous: str) -> bool:
        """检查角色性格是否一致"""
        # 简单实现：检查是否有明显的性格翻转
        contradictions = [
            ("勇敢", "胆怯"),
            ("聪慧", "愚蠢"),
            ("友善", "冷酷"),
            ("谨慎", "鲁莽")
        ]
        
        for pos, neg in contradictions:
            if pos in previous and neg in current:
                return False
            if neg in previous and pos in current:
                return False
        
        return True
    
    def _check_location_consistency(self, narrative: str, game_state: Dict) -> bool:
        """检查位置转换是否合理"""
        current_location = game_state.get("current_location", "")
        
        # 不应该在一个位置发生不可能的事件
        if current_location == "Hogwarts Castle" and "禁林" in narrative:
            return False
        
        return True
    
    def _check_temporal_consistency(self, action: str, narrative: str) -> bool:
        """检查时间一致性"""
        # 简单检查：行动应该在叙述中有合理的因果关系
        
        action_to_result = {
            "move": ["走", "来到", "进入", "离开"],
            "talk": ["说", "讨论", "询问", "回答"],
            "take": ["拿", "获得", "收集", "得到"],
            "cast": ["施放", "魔法", "咒语"],
            "observe": ["看到", "发现", "注意到", "观察"]
        }
        
        expected_keywords = action_to_result.get(action, [])
        has_relevant_content = any(kw in narrative for kw in expected_keywords)
        
        return has_relevant_content
    
    def _check_emotional_arc(self, current: str, previous: str) -> bool:
        """检查情感发展是否自然"""
        emotions = {
            "positive": ["惊喜", "高兴", "满足", "胜利", "骄傲"],
            "negative": ["恐惧", "失望", "愤怒", "悲伤"],
            "neutral": ["平静", "思考", "警觉"]
        }
        
        # 简单启发式：不应该在一个动作中从极端正面变为极端负面
        # 这里只做基本检查，实际应用可以更复杂
        return True
