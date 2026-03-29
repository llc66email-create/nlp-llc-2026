"""
约束引擎 - 确保故事逻辑符合哈利波特原著设定
三层验证：能力约束 / 地点约束 / 时间约束
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class TimelineBook(Enum):
    """哈利波特时间轴 - 对应各册"""
    BOOK_1 = 1   # 魔法石
    BOOK_2 = 2   # 密室
    BOOK_3 = 3   # 阿兹卡班囚徒
    BOOK_4 = 4   # 火焰杯
    BOOK_5 = 5   # 凤凰社
    BOOK_6 = 6   # 混血王子
    BOOK_7 = 7   # 死亡圣器


@dataclass
class ConstraintViolation:
    """约束违规记录"""
    violation_type: str       # 'ability' | 'location' | 'temporal'
    character: str
    reason: str
    suggestion: str           # 推荐的合规替代描述


@dataclass
class SkillLearnedPoint:
    """角色技能学习节点"""
    skill_name: str
    book: TimelineBook
    chapter: int
    character: str
    description: str


class CharacterAbilityTracker:
    """角色能力跟踪器 - 记录各角色在各节点的可用技能"""

    # {角色: {技能名: SkillLearnedPoint}}
    ABILITIES: Dict[str, Dict[str, SkillLearnedPoint]] = {
        "哈利": {
            "守护神咒": SkillLearnedPoint("守护神咒", TimelineBook.BOOK_3, 8, "哈利", "Lupin教授教授的对抗摄魂怪的光明咒语"),
            "无声咒": SkillLearnedPoint("无声咒", TimelineBook.BOOK_5, 18, "哈利", "D.A.训练中学会"),
            "幻影移形": SkillLearnedPoint("幻影移形", TimelineBook.BOOK_6, 3, "哈利", "暑假预备课程学会"),
            "钻心剜地咒": SkillLearnedPoint("钻心剜地咒", TimelineBook.BOOK_5, 35, "哈利", "被逼到极限时首次使用"),
            "缴械咒": SkillLearnedPoint("缴械咒", TimelineBook.BOOK_2, 11, "哈利", "对抗赫敏时学会"),
            "除你武器": SkillLearnedPoint("除你武器", TimelineBook.BOOK_2, 11, "哈利", "哈利标志性咒语"),
        },
        "赫敏": {
            "时间转换器": SkillLearnedPoint("时间转换器", TimelineBook.BOOK_3, 1, "赫敏", "仅第三册，邓布利多授权"),
            "幻影移形": SkillLearnedPoint("幻影移形", TimelineBook.BOOK_6, 3, "赫敏", "与哈利同期学习"),
            "扩展咒": SkillLearnedPoint("扩展咒", TimelineBook.BOOK_4, 9, "赫敏", "用于魔法口袋和帐篷内部"),
            "混淆咒": SkillLearnedPoint("混淆咒", TimelineBook.BOOK_5, 15, "赫敏", "D.A.训练"),
        },
        "罗恩": {
            "幻影移形": SkillLearnedPoint("幻影移形", TimelineBook.BOOK_6, 3, "罗恩", "与哈利同期学习"),
            "除你武器": SkillLearnedPoint("除你武器", TimelineBook.BOOK_2, 11, "罗恩", "标准防御咒语"),
        },
        "邓布利多": {
            # 邓布利多从故事开始就精通所有咒语
            "所有魔法": SkillLearnedPoint("所有魔法", TimelineBook.BOOK_1, 1, "邓布利多", "霍格沃茨有史以来最伟大的巫师"),
        },
        "斯内普": {
            "无言咒": SkillLearnedPoint("无言咒", TimelineBook.BOOK_1, 1, "斯内普", "暗黑艺术大师"),
            "幻影移形": SkillLearnedPoint("幻影移形", TimelineBook.BOOK_1, 1, "斯内普", "成年巫师基本能力"),
            "钻心剜地咒": SkillLearnedPoint("钻心剜地咒", TimelineBook.BOOK_1, 1, "斯内普", "发明者"),
        },
    }

    def can_use_skill(self, character: str, skill: str, current_book: TimelineBook) -> Tuple[bool, str]:
        """
        检查角色在当前时间节点是否能使用某技能。
        返回 (是否允许, 原因说明)
        """
        char_key = self._normalize_character(character)
        if char_key not in self.ABILITIES:
            return True, "角色未被约束，允许使用"

        if "所有魔法" in self.ABILITIES[char_key]:
            return True, "该角色精通所有咒语"

        # 标准化技能名
        skill_key = self._normalize_skill(skill, char_key)
        if skill_key is None:
            return True, "未列管的技能，默认允许"

        learned = self.ABILITIES[char_key].get(skill_key)
        if learned is None:
            return True, "未列管的技能，默认允许"

        if current_book.value >= learned.book.value:
            return True, f"已在第{learned.book.value}册学会"
        else:
            return False, (f"{character}在第{current_book.value}册还未学会{skill_key}，"
                           f"该技能要到第{learned.book.value}册才学会")

    def _normalize_character(self, name: str) -> str:
        mapping = {
            "harry": "哈利", "harry potter": "哈利", "哈利·波特": "哈利",
            "hermione": "赫敏", "hermione granger": "赫敏", "赫敏·格兰杰": "赫敏",
            "ron": "罗恩", "ron weasley": "罗恩", "罗恩·韦斯莱": "罗恩",
            "dumbledore": "邓布利多", "albus dumbledore": "邓布利多", "阿不思·邓布利多": "邓布利多",
            "snape": "斯内普", "severus snape": "斯内普", "西弗勒斯·斯内普": "斯内普",
        }
        return mapping.get(name.lower(), name)

    def _normalize_skill(self, skill: str, char_key: str) -> Optional[str]:
        """模糊匹配技能名"""
        if char_key not in self.ABILITIES:
            return None
        for key in self.ABILITIES[char_key]:
            if key in skill or skill in key:
                return key
        return None

    def add_learned_skill(self, character: str, skill_point: SkillLearnedPoint):
        char_key = self._normalize_character(character)
        if char_key not in self.ABILITIES:
            self.ABILITIES[char_key] = {}
        self.ABILITIES[char_key][skill_point.skill_name] = skill_point


class LocationConstraint:
    """地点约束规则"""

    LOCATION_RULES: Dict[str, Dict] = {
        "霍格沃茨": {
            "aliases": ["hogwarts", "hogwarts castle", "城堡", "学校", "魔法学校"],
            "forbidden_actions": [
                {"keywords": ["幻影移形", "移形", "瞬移"], "reason": "霍格沃茨有反幻影移形魔法屏障，无法在校内使用"},
                {"keywords": ["故意伤害同学", "攻击同学", "伤害学生"], "reason": "校规禁止攻击同学"},
                {"keywords": ["使用魔法骑扫帚离开"], "reason": "离开需要经过正规出口"},
            ],
            "danger_level": "low",
            "requires_permission": False,
        },
        "禁林": {
            "aliases": ["forbidden forest", "黑暗森林", "森林深处"],
            "forbidden_actions": [
                {"keywords": ["学生独自前往", "单独进入", "独自进入禁林", "一个人去禁林"],
                 "reason": "学生单独进入禁林违反校规，需要教师陪同或特殊许可"},
            ],
            "danger_level": "critical",
            "requires_permission": True,
            "permission_note": "需要教师陪同或Professor Dumbledore特殊许可",
        },
        "对角巷": {
            "aliases": ["diagon alley", "角巷"],
            "forbidden_actions": [
                {"keywords": ["公开使用黑魔法", "使用不饶咒", "阿瓦达"],
                 "reason": "麻瓜可能在场，公开黑魔法会暴露魔法界"},
            ],
            "danger_level": "low",
            "requires_permission": False,
        },
        "魔法部": {
            "aliases": ["ministry of magic", "ministry", "部"],
            "forbidden_actions": [
                {"keywords": ["未成年巫师使用魔法", "未成年使用魔法"],
                 "reason": "未成年人在魔法部使用魔法需要特殊授权"},
            ],
            "danger_level": "medium",
            "requires_permission": True,
            "permission_note": "需要预约或紧急事务授权",
        },
        "平台九又四分之三": {
            "aliases": ["9¾站台", "九又四分之三站台", "king's cross"],
            "forbidden_actions": [],
            "danger_level": "low",
            "requires_permission": False,
        },
        "格林戈茨": {
            "aliases": ["gringotts", "巫师银行", "银行"],
            "forbidden_actions": [
                {"keywords": ["盗窃", "偷窃", "未经授权进入金库"],
                 "reason": "格林戈茨有精灵和龙守护，非法闯入极度危险"},
            ],
            "danger_level": "high",
            "requires_permission": True,
            "permission_note": "需要账户钥匙或书面授权",
        },
    }

    def check_action(self, action: str, location: str) -> Tuple[bool, Optional[str]]:
        """
        检查在指定地点是否能执行该动作。
        返回 (是否允许, 违规原因)
        """
        loc_key = self._normalize_location(location)
        if loc_key is None:
            return True, None

        rules = self.LOCATION_RULES[loc_key]
        for rule in rules["forbidden_actions"]:
            for kw in rule["keywords"]:
                if kw in action:
                    return False, rule["reason"]
        return True, None

    def _normalize_location(self, location: str) -> Optional[str]:
        location_lower = location.lower()
        for key, info in self.LOCATION_RULES.items():
            if key in location or location_lower in [a.lower() for a in info.get("aliases", [])]:
                return key
            if location_lower == key.lower():
                return key
        return None

    def get_danger_level(self, location: str) -> str:
        key = self._normalize_location(location)
        if key:
            return self.LOCATION_RULES[key].get("danger_level", "unknown")
        return "unknown"

    @classmethod
    def add_location_rule(cls, location: str, rule: Dict):
        if location not in cls.LOCATION_RULES:
            cls.LOCATION_RULES[location] = {"aliases": [], "forbidden_actions": [], "danger_level": "low", "requires_permission": False}
        cls.LOCATION_RULES[location]["forbidden_actions"].append(rule)


class TemporalConstraint:
    """时间/事件顺序约束"""

    # 关键事件发生的时间节点
    EVENT_SEQUENCE: Dict[str, Dict] = {
        "分院仪式": {"book": TimelineBook.BOOK_1, "chapter": 7},
        "学年开始": {"book": TimelineBook.BOOK_1, "chapter": 5},
        "发现魔法石": {"book": TimelineBook.BOOK_1, "chapter": 16},
        "击败蛇怪": {"book": TimelineBook.BOOK_2, "chapter": 17},
        "发现小天狼星无罪": {"book": TimelineBook.BOOK_3, "chapter": 19},
        "三强争霸赛": {"book": TimelineBook.BOOK_4, "chapter": 12},
        "伏地魔复活": {"book": TimelineBook.BOOK_4, "chapter": 33},
        "邓布利多军成立": {"book": TimelineBook.BOOK_5, "chapter": 16},
        "邓布利多之死": {"book": TimelineBook.BOOK_6, "chapter": 27},
        "了解魂器": {"book": TimelineBook.BOOK_6, "chapter": 17},
        "摧毁所有魂器": {"book": TimelineBook.BOOK_7, "chapter": 31},
        "击败黑魔王": {"book": TimelineBook.BOOK_7, "chapter": 36},
    }

    # 事件依赖：触发条件必须先满足
    EVENT_DEPENDENCIES: Dict[str, List[str]] = {
        "击败黑魔王": ["摧毁所有魂器", "了解魂器"],
        "摧毁魂器": ["了解魂器"],
        "救出小天狼星": ["发现小天狼星无罪"],
    }

    # 各册禁用的关键词（避免时间线混乱）
    BOOK_FORBIDDEN_MENTIONS: Dict[TimelineBook, List[str]] = {
        TimelineBook.BOOK_1: ["魂器", "幻影移形", "死亡圣器", "哈利的父母死亡", "邓布利多死了"],
        TimelineBook.BOOK_2: ["魂器", "幻影移形", "死亡圣器", "邓布利多死了"],
        TimelineBook.BOOK_3: ["幻影移形", "魂器", "邓布利多死了"],
        TimelineBook.BOOK_4: ["幻影移形", "邓布利多死了"],
        TimelineBook.BOOK_5: ["邓布利多死了"],
    }

    def check_mention(self, text: str, current_book: TimelineBook) -> Tuple[bool, Optional[str]]:
        """检查文本中是否提及了当前时间节点不应知道的事"""
        forbidden = self.BOOK_FORBIDDEN_MENTIONS.get(current_book, [])
        for term in forbidden:
            if term in text:
                return False, f'第{current_book.value}册中不应提及"{term}"（时间线超前）'
        return True, None

    def event_is_possible(self, event: str, current_book: TimelineBook) -> Tuple[bool, str]:
        """检查某事件在当前时间节点是否可能发生"""
        info = self.EVENT_SEQUENCE.get(event)
        if info is None:
            return True, "未列管的事件，默认允许"
        if current_book.value >= info["book"].value:
            return True, "事件在当前时间节点已可发生"
        return False, f"该事件（{event}）要到第{info['book'].value}册才会发生"


class ConstraintEngine:
    """统一约束引擎 - 整合三层约束检查"""

    def __init__(self):
        self.ability_tracker = CharacterAbilityTracker()
        self.location_constraint = LocationConstraint()
        self.temporal_constraint = TemporalConstraint()

    def validate_story_segment(
        self,
        segment: str,
        character: str,
        location: str,
        current_book: TimelineBook = TimelineBook.BOOK_1,
    ) -> Tuple[bool, List[ConstraintViolation]]:
        """
        全面验证一段故事内容。
        返回 (是否通过, 违规列表)
        """
        violations: List[ConstraintViolation] = []

        # 1. 地点约束
        ok, reason = self.location_constraint.check_action(segment, location)
        if not ok:
            violations.append(ConstraintViolation(
                violation_type="location",
                character=character,
                reason=reason,
                suggestion=f"改为在{location}内符合规则的合理行动"
            ))

        # 2. 时间约束
        ok, reason = self.temporal_constraint.check_mention(segment, current_book)
        if not ok:
            violations.append(ConstraintViolation(
                violation_type="temporal",
                character=character,
                reason=reason,
                suggestion="将该内容改为当前时间节点合理的情节"
            ))

        # 3. 能力约束 - 检测常见咒语关键词
        spell_keywords = {
            "幻影移形": "幻影移形",
            "守护神咒": "守护神咒",
            "无声咒": "无声咒",
            "钻心剜地咒": "钻心剜地咒",
            "时间转换器": "时间转换器",
        }
        for term, skill in spell_keywords.items():
            if term in segment:
                ok, reason = self.ability_tracker.can_use_skill(character, skill, current_book)
                if not ok:
                    violations.append(ConstraintViolation(
                        violation_type="ability",
                        character=character,
                        reason=reason,
                        suggestion=f"在第{current_book.value}册中，{character}还未学会此技能，请使用已学习的咒语"
                    ))

        return len(violations) == 0, violations

    def build_constraint_context(
        self,
        character: str,
        location: str,
        current_book: TimelineBook,
        completed_tasks: List[str],
    ) -> str:
        """生成可注入提示词的约束上下文摘要"""
        ability_tracker = self.ability_tracker
        char_key = ability_tracker._normalize_character(character)
        
        lines = [
            f"【当前时间轴】第{current_book.value}册",
            f"【当前地点约束】",
        ]

        # 地点规则
        loc_key = self.location_constraint._normalize_location(location)
        if loc_key and loc_key in LocationConstraint.LOCATION_RULES:
            rules = LocationConstraint.LOCATION_RULES[loc_key]
            if rules["forbidden_actions"]:
                lines.append(f"  在{location}内禁止：")
                for rule in rules["forbidden_actions"]:
                    lines.append(f"    - {rule['reason']}")
            if rules.get("requires_permission"):
                lines.append(f"  注意：{rules.get('permission_note', '需要许可')}")

        # 角色能力
        lines.append(f"【{character}当前可用技能（第{current_book.value}册）】")
        if char_key in CharacterAbilityTracker.ABILITIES:
            available = []
            for skill, sp in CharacterAbilityTracker.ABILITIES[char_key].items():
                if current_book.value >= sp.book.value:
                    available.append(skill)
            if available:
                lines.append(f"  已学会：{', '.join(available)}")
            else:
                lines.append(f"  仅掌握基础魔法（如漂浮咒、除你武器等入学前咒语）")

        # 时间禁止词
        forbidden_mentions = TemporalConstraint.BOOK_FORBIDDEN_MENTIONS.get(current_book, [])
        if forbidden_mentions:
            lines.append(f"【当前时间节点禁止提及】{', '.join(forbidden_mentions)}")

        # 故事推进状态
        if completed_tasks:
            lines.append(f"【已完成任务】{', '.join(completed_tasks)}")

        return "\n".join(lines)
