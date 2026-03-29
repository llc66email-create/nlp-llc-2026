# 约束系统集成指南

## 问题背景
你提出的问题非常重要：**仅有训练数据不足以支持角色扮演**。你需要：

1. **能力约束**（Ability Constraints）
   - 示例：Harry不能在第5册前使用幻影移形（Apparition）
   - 实现：`CharacterAbilityTracker` 追踪每个角色在各个时间点学会的技能

2. **地点约束**（Location Constraints）
   - 示例：在Hogwarts内不能无限制地伤害同学
   - 示例：在禁林不能单独进入（学生必须有许可或陪同）
   - 实现：`LocationConstraint` 定义每个地点的规则

3. **时间约束**（Temporal Constraints）
   - 示例：不能在Book 4提到销毁Horcruxes（这在Book 6才开始）
   - 实现：`TemporalConstraint` 管理事件序列和因果关系

## 系统架构

```
模型生成文本
    ↓
约束引擎检查 (ConstraintEngine)
    ↓
[违规] → 验证管道修正 (ValidationPipeline) → 修正建议
[合理] → 直接使用
```

## 快速开始

### 1. 检查一个生成的故事是否合理：

```python
from story_weaver.constraint_engine import ConstraintEngine, TimelineBook

engine = ConstraintEngine()

is_valid, violations = engine.validate_story_segment(
    segment="哈利使用幻影移形离开了Hogwarts。",
    character="哈利",
    location="Hogwarts",
    current_book=TimelineBook.BOOK_1  # 第一册
)

if not is_valid:
    print("❌ 冲突:", [v.reason for v in violations])
else:
    print("✅ 这个故事片段是合理的")
```

### 2. 在模型推理前增强提示词：

```python
from story_weaver.validation_pipeline import ConstraintAwarenessPrompt

# 原始提示词
prompt = "哈利正在思考如何击败黑魔王..."

# 增强版本（告诉模型当前约束）
enhanced_prompt = ConstraintAwarenessPrompt.augment_prompt(
    original_prompt=prompt,
    character="哈利",
    location="Hogwarts",
    current_book=TimelineBook.BOOK_5,
    constraints=[
        "Harry还不知道Horcruxes的所有信息",
        "不能使用还未学过的咒语"
    ]
)

# 使用enhanced_prompt调用模型
# model_output = model.generate(enhanced_prompt)
```

### 3. 在生成后验证和修正：

```python
from story_weaver.validation_pipeline import StoryValidationPipeline

pipeline = StoryValidationPipeline()

# 模型生成的文本
generated = "哈利走进禁林独自在那里等待，使用火焰咒消灭了所有摄魂怪。"

# 验证和自动修正
refined, is_valid, violations = pipeline.validate_and_refine(
    generated_text=generated,
    player_character="哈利",
    location="禁林",
    current_book=TimelineBook.BOOK_3
)

# 生成报告
report = pipeline.generate_validation_report(generated, refined, violations, is_valid)
print(report)
```

## 核心约束规则详解

### 能力约束 (CharacterAbilityTracker)

每个角色在不同的书籍阶段学会不同的技能：

| 角色 | 技能 | 学会时间 | 备注 |
|------|------|--------|------|
| 哈利 | 守护神咒 | Book 3 | Lupin教《Protection from Dementors》|
| 哈利 | 无声咒 | Book 5 | D.A.课程 |
| 哈利 | 幻影移形 | Book 6 | 暑假预备课程 |
| 赫敏 | 时间转换器 | Book 3 | Dumbledore给的，仅Book 3 |
| 赫敏 | 幻影移形 | Book 6 | 与Harry同时 |
| 罗恩 | 幻影移形 | Book 6 | 与Harry同时 |
| 邓布利多 | 所有技能 | Book 1 | 故事开始时已精通 |

**添加新技能的方法：**

```python
engine.ability_tracker.add_learned_skill(
    character="哈利",
    skill_point=SkillLearnedPoint(
        skill_name="新年级防护咒",
        book=TimelineBook.BOOK_6,
        chapter=5,
        character="哈利",
        description="Harry learns a new protection spell in Book 6"
    )
)
```

### 地点约束 (LocationConstraint)

```python
LOCATION_RULES = {
    "霍格沃茨": {
        "forbidden_actions": [
            {"action": "使用幻影移形", "reason": "Hogwarts有反幻影移形的魔法"},
            {"action": "故意伤害同学", "reason": "校规禁止"}
        ],
        "danger_level": "low"
    },
    "禁林": {
        "forbidden_actions": [
            {"action": "学生独自前往", "reason": "太危险"}
        ],
        "danger_level": "critical",
        "requires_permission": True
    }
}
```

**你的具体例子：**
- "哈利在Hogwarts打达利" → ❌ 违反校规（forbidden_action）
- "哈利在对角巷与陌生人对抗" → ✅ 允许（对角巷是公共区域）

### 时间约束 (TemporalConstraint)

事件必须按正确的顺序发生：

```python
EVENT_SEQUENCE = {
    "分院仪式": {"book": TimelineBook.BOOK_1, "chapter": 7},
    "学年开始": {"book": TimelineBook.BOOK_1, "chapter": 5},
    "击败黑魔王": {"book": TimelineBook.BOOK_7, "chapter": 30},
    "摧毁所有Horcruxes": {"book": TimelineBook.BOOK_7, "chapter": 28}
}

# 事件依赖关系
EVENT_DEPENDENCIES = {
    "击败黑魔王": ["摧毁所有Horcruxes", "获得老魔杖控制权"],
    "摧毁玛瑞姆露项链": ["进入Gringotts"]
}
```

## 与现有系统的集成

你已经有：
- `GameState` - 追踪角色位置、状态
- `ConsistencyChecker` - 检查一致性
- `Character Graph` - 角色关系图

**建议的集成方式：**

```python
class IntegratedGameEngine:
    def __init__(self):
        self.game_state = GameState()
        self.constraint_engine = ConstraintEngine()
        self.validation_pipeline = StoryValidationPipeline()
        self.consistency_checker = ConsistencyChecker()
    
    def process_player_action(self, action: str, player_char: str) -> str:
        """处理玩家动作"""
        
        # 1. 约束检查
        is_valid, violations = self.constraint_engine.validate_story_segment(
            action, player_char, 
            self.game_state.current_location,
            self.game_state.current_timeline
        )
        
        if not is_valid:
            return f"❌ 动作不允许: {violations[0].reason}"
        
        # 2. 一致性检查
        consistency_ok = self.consistency_checker.check_consistency(
            {"action": action}, self.game_state
        )
        
        if not consistency_ok:
            return "❌ 与历史事实矛盾"
        
        # 3. 生成故事（调用模型）
        # prompt = create_enhanced_prompt(action, self.game_state)
        # generated = model.generate(prompt)
        
        # 4. 对生成的故事进行验证
        # refined, valid, violations = self.validation_pipeline.validate_and_refine(...)
        
        return refined if valid else generated
```

## 性能考虑

如果实时验证较慢，可以使用两策略：

**策略1：约束感知的模型提示**（推荐）
```
在提示词中包含约束信息，让模型直接生成合理的文本
→ 减少需要修正的比例
→ 更快的响应时间
```

**策略2：批量验证**
```
生成多个候选文本，验证所有候选
→ 选择第一个通过验证的
→ 如果都失败，则使用修正版本
```

## 如何扩展

### 添加新的位置约束：

```python
LocationConstraint.LOCATION_RULES["对角巷"] = {
    "forbidden_actions": [
        {"action": "公开使用黑魔法", "reason": "Muggle可能看到"}
    ],
    "danger_level": "low"
}
```

### 添加新的时间约束：

```python
TemporalConstraint.EVENT_SEQUENCE["新事件"] = {
    "book": TimelineBook.BOOK_6,
    "chapter": 15
}
```

### 添加新的角色技能：

```python
engine.ability_tracker.abilities["哈利"]["新咒语"] = SkillLearnedPoint(
    skill_name="新咒语",
    book=TimelineBook.BOOK_6,
    chapter=10,
    character="哈利",
    description="Description here"
)
```

## 总结：你需要的三层验证

```
┌─────────────────────────────────────────────┐
│  第1层：输入验证                              │
│  ↓ 用户提供的动作是否符合约束？                │
│  ConstraintEngine.validate_story_segment()  │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│  第2层：模型生成验证                          │
│  ↓ 模型生成的故事是否符合约束？                │
│  ValidationPipeline.validate_and_refine()   │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│  第3层：一致性检查                            │
│  ↓ 故事与历史事实是否矛盾？                    │
│  ConsistencyChecker.check_consistency()     │
└─────────────────────────────────────────────┘
```

**答案：仅有109条训练数据是不够的！** 你还需要这个约束系统来确保故事的逻辑性和合理性。
