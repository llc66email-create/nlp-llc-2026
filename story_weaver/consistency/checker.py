"""
一致性维护模块 - 检测并避免与历史事实矛盾
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import re
from pathlib import Path

@dataclass
class ConsistencyRule:
    """一致性规则"""
    rule_id: str
    rule_type: str  # "character_state", "location_state", "temporal", "logical"
    description: str
    conditions: Dict
    consequences: List[str]
    priority: int = 1

@dataclass
class ConsistencyViolation:
    """一致性违反"""
    violation_id: str
    rule_id: str
    severity: str  # "low", "medium", "high"
    description: str
    conflicting_states: List[Dict]
    timestamp: str

class ConsistencyChecker:
    """一致性检查器"""
    
    def __init__(self, rules_path: Optional[Path] = None):
        """初始化一致性检查器"""
        self.rules: Dict[str, ConsistencyRule] = {}
        self.violation_history: List[ConsistencyViolation] = []
        self.fact_base: Dict[str, Dict] = {}
        
        if rules_path:
            self.load_rules_from_file(rules_path)
    
    def load_rules_from_file(self, rules_path: Path):
        """从文件加载规则"""
        if rules_path.exists():
            with open(rules_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
                for rule in rules_data.get("rules", []):
                    self.add_rule(
                        rule_id=rule.get("id", ""),
                        rule_type=rule.get("type", ""),
                        description=rule.get("description", ""),
                        conditions=rule.get("conditions", {}),
                        consequences=rule.get("consequences", []),
                        priority=rule.get("priority", 1)
                    )
    
    def add_rule(self, rule_id: str, rule_type: str, description: str,
                conditions: Dict, consequences: List[str], priority: int = 1):
        """添加一致性规则"""
        rule = ConsistencyRule(
            rule_id=rule_id,
            rule_type=rule_type,
            description=description,
            conditions=conditions,
            consequences=consequences,
            priority=priority
        )
        self.rules[rule_id] = rule
    
    def record_fact(self, fact_id: str, fact_type: str, entity: str, 
                   attribute: str, value: str, timestamp: Optional[str] = None):
        """记录事实到事实库"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        fact_key = f"{entity}_{attribute}"
        
        if fact_key not in self.fact_base:
            self.fact_base[fact_key] = {
                "entity": entity,
                "attribute": attribute,
                "history": []
            }
        
        self.fact_base[fact_key]["history"].append({
            "fact_id": fact_id,
            "value": value,
            "timestamp": timestamp,
            "type": fact_type
        })
    
    def check_consistency(self, proposed_action: Dict, game_state: Dict) -> Tuple[bool, Optional[ConsistencyViolation]]:
        """检查提议的动作是否与历史事实一致"""
        violations = []
        
        # 检查所有规则
        for rule_id, rule in self.rules.items():
            violation = self._check_rule(rule, proposed_action, game_state)
            if violation:
                violations.append(violation)
        
        if violations:
            # 按优先级排序，返回最严重的违反
            violations.sort(key=lambda v: {"high": 3, "medium": 2, "low": 1}.get(v.severity, 0), reverse=True)
            return False, violations[0]
        
        return True, None
    
    def _check_rule(self, rule: ConsistencyRule, proposed_action: Dict, 
                   game_state: Dict) -> Optional[ConsistencyViolation]:
        """检查单个规则"""
        rule_type = rule.rule_type
        
        if rule_type == "character_state":
            return self._check_character_state_rule(rule, proposed_action, game_state)
        elif rule_type == "location_state":
            return self._check_location_state_rule(rule, proposed_action, game_state)
        elif rule_type == "temporal":
            return self._check_temporal_rule(rule, proposed_action, game_state)
        elif rule_type == "logical":
            return self._check_logical_rule(rule, proposed_action, game_state)
        
        return None
    
    def _check_character_state_rule(self, rule: ConsistencyRule, proposed_action: Dict,
                                   game_state: Dict) -> Optional[ConsistencyViolation]:
        """检查角色状态规则"""
        character = proposed_action.get("character")
        if not character:
            return None
        
        # 检查历史事实
        fact_key = f"{character}_status"
        if fact_key in self.fact_base:
            history = self.fact_base[fact_key]["history"]
            if history:
                last_state = history[-1]["value"]
                
                # 检查禁止的状态转换
                forbidden_transitions = rule.conditions.get("forbidden_transitions", {})
                current_state = proposed_action.get("new_status")
                
                if last_state in forbidden_transitions:
                    if current_state in forbidden_transitions[last_state]:
                        violation = ConsistencyViolation(
                            violation_id=f"v_{rule.rule_id}_{datetime.now().timestamp()}",
                            rule_id=rule.rule_id,
                            severity="high",
                            description=f"无效的状态转换: {last_state} -> {current_state}",
                            conflicting_states=[
                                {"character": character, "old_status": last_state},
                                {"character": character, "new_status": current_state}
                            ],
                            timestamp=datetime.now().isoformat()
                        )
                        self.violation_history.append(violation)
                        return violation
        
        return None
    
    def _check_location_state_rule(self, rule: ConsistencyRule, proposed_action: Dict,
                                  game_state: Dict) -> Optional[ConsistencyViolation]:
        """检查地点状态规则"""
        location = proposed_action.get("location")
        if not location:
            return None
        
        # 检查地点的可达性
        accessible_condition = rule.conditions.get("must_be_accessible", False)
        
        # 这里应该检查地点在游戏状态中的可达性
        locations = game_state.get("locations", {})
        
        if location in locations:
            if accessible_condition and not locations[location].get("accessible", True):
                violation = ConsistencyViolation(
                    violation_id=f"v_{rule.rule_id}_{datetime.now().timestamp()}",
                    rule_id=rule.rule_id,
                    severity="medium",
                    description=f"无法访问不可达的地点: {location}",
                    conflicting_states=[
                        {"location": location, "accessible": False}
                    ],
                    timestamp=datetime.now().isoformat()
                )
                self.violation_history.append(violation)
                return violation
        
        return None
    
    def _check_temporal_rule(self, rule: ConsistencyRule, proposed_action: Dict,
                            game_state: Dict) -> Optional[ConsistencyViolation]:
        """检查时间一致性规则"""
        # 检查提议的动作是否违反时间逻辑
        temporal_constraints = rule.conditions.get("constraints", [])
        
        for constraint in temporal_constraints:
            constraint_type = constraint.get("type")
            
            if constraint_type == "event_sequence":
                # 检查事件顺序
                required_event = constraint.get("required_event")
                if required_event:
                    # 检查必需事件是否在历史中发生过
                    fact_found = False
                    for fact_id, fact_data in self.fact_base.items():
                        for history_item in fact_data.get("history", []):
                            if required_event in fact_id:
                                fact_found = True
                                break
                    
                    if not fact_found:
                        violation = ConsistencyViolation(
                            violation_id=f"v_{rule.rule_id}_{datetime.now().timestamp()}",
                            rule_id=rule.rule_id,
                            severity="high",
                            description=f"违反事件顺序: 必需事件 {required_event} 未发生",
                            conflicting_states=[
                                {"missing_event": required_event}
                            ],
                            timestamp=datetime.now().isoformat()
                        )
                        self.violation_history.append(violation)
                        return violation
        
        return None
    
    def _check_logical_rule(self, rule: ConsistencyRule, proposed_action: Dict,
                           game_state: Dict) -> Optional[ConsistencyViolation]:
        """检查逻辑规则"""
        logical_conditions = rule.conditions.get("conditions", [])
        
        for condition in logical_conditions:
            # 检查逻辑条件
            if_statement = condition.get("if")
            then_statement = condition.get("then")
            
            # 简单的逻辑检查
            if if_statement and then_statement:
                # 这里可以进行更复杂的逻辑推理
                pass
        
        return None
    
    def get_permissible_actions(self, character: str, current_state: Dict) -> List[str]:
        """获取给定角色的允许操作"""
        permissible = []
        
        fact_key = f"{character}_status"
        if fact_key in self.fact_base:
            history = self.fact_base[fact_key]["history"]
            if history:
                current_status = history[-1]["value"]
                
                # 根据规则确定允许的动作
                for rule in self.rules.values():
                    if rule.rule_type == "character_state":
                        forbidden = rule.conditions.get("forbidden_transitions", {}).get(current_status, [])
                        allowed = rule.consequences
                        
                        for action in allowed:
                            if action not in forbidden:
                                permissible.append(action)
        
        return list(set(permissible))
    
    def get_violation_history(self, limit: int = 10) -> List[ConsistencyViolation]:
        """获取违反历史"""
        return self.violation_history[-limit:]
    
    def clear_violations(self):
        """清除违反历史"""
        self.violation_history.clear()
