#!/usr/bin/env python3
"""
测试增强型NLG生成器和动作预测系统
演示轻量级文本生成和叙述连贯性检查
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_enhanced_nlg():
    """测试增强型NLG生成器"""
    
    print("=" * 60)
    print("🎯 测试增强型NLG生成器和动作预测系统")
    print("=" * 60)
    
    # 1. 初始化NLG生成器
    print("\n[1] 初始化NLG生成器...")
    from story_weaver.nlg.enhanced_generator import EnhancedNLGEngine
    
    nlg_engine = EnhancedNLGEngine(
        backend="template",  # 使用快速的模板后端
        enable_action_prediction=True,
        enable_coherence_check=True
    )
    print("✓ NLG生成器已初始化")
    
    # 2. 初始化动作预测器
    print("\n[2] 初始化动作预测器...")
    from story_weaver.nlg.action_predictor import ActionPredictor, NarrativeCoherence
    
    action_predictor = ActionPredictor()
    coherence_checker = NarrativeCoherence()
    print("✓ 动作预测器已初始化")
    
    # 3. 测试场景
    test_scenarios = [
        {
            "user_action": "走进黑魔法防御课教室",
            "game_state": {
                "player_character": "哈利·波特",
                "current_location": "Hogwarts Castle",
                "round": 1,
                "difficulty": "medium"
            },
            "intent": "move"
        },
        {
            "user_action": "与邓布利多讨论魔法的本质",
            "game_state": {
                "player_character": "赫敏·格兰杰",
                "current_location": "Hogwarts Castle",
                "round": 3,
                "difficulty": "medium"
            },
            "intent": "talk"
        },
        {
            "user_action": "深入禁林寻找神奇生物",
            "game_state": {
                "player_character": "哈利·波特",
                "current_location": "Forbidden Forest",
                "round": 5,
                "difficulty": "hard"
            },
            "intent": "move"
        },
        {
            "user_action": "在对角巷购买稀有的魔法书籍",
            "game_state": {
                "player_character": "赫敏·格兰杰",
                "current_location": "Diagon Alley",
                "round": 4,
                "difficulty": "low"
            },
            "intent": "take"
        }
    ]
    
    # 4. 运行测试
    print("\n" + "=" * 60)
    print("🎬 运行叙事生成测试")
    print("=" * 60)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📖 测试场景 {i}:")
        print(f"  角色: {scenario['game_state']['player_character']}")
        print(f"  位置: {scenario['game_state']['current_location']}")
        print(f"  玩家行动: {scenario['user_action']}")
        print(f"  意图: {scenario['intent']}")
        print()
        
        # 生成叙述
        response = nlg_engine.generate_narrative(
            user_action=scenario['user_action'],
            game_state=scenario['game_state'],
            retrieved_context=None,
            intent=scenario['intent']
        )
        
        print(f"  📝 生成的叙述:")
        print(f"     {response.main_narrative}")
        print()
        
        # 显示下一步选项
        print(f"  🎯 可用的下一步选项:")
        for action, description in response.next_options[:3]:
            print(f"     • [{action}] {description}")
        print()
        
        # 显示预测的动作
        if response.next_predicted_action:
            action, confidence = response.next_predicted_action
            print(f"  🔮 预测的下一步动作: [{action}] (置信度: {confidence:.1%})")
        print()
        
        # 显示元数据
        print(f"  📊 元数据:")
        print(f"     后端模型: {response.metadata.get('model', 'unknown')}")
        print(f"     上下文片段: {response.metadata.get('context_segments', 0)}")
    
    # 5. 测试动作预测
    print("\n" + "=" * 60)
    print("🔮 动作预测能力演示")
    print("=" * 60)
    
    print("\n测试场景：玩家在禁林中的行动序列")
    
    game_state = {
        "current_location": "Forbidden Forest",
        "player_character": "哈利·波特",
        "round": 5
    }
    
    player_history = ["move", "observe", "move", "talk"]
    
    for _ in range(3):
        current_action = player_history[-1] if player_history else "move"
        predicted_action, confidence = action_predictor.predict_next_action(
            current_action,
            game_state,
            player_history,
            "Forbidden Forest"
        )
        
        print(f"\n  过去的行动: {' → '.join(player_history)}")
        print(f"  预测的下一步: [{predicted_action}] (置信度: {confidence:.1%})")
        
        # 模拟玩家采取该行动
        player_history.append(predicted_action)
    
    # 6. 测试叙述连贯性
    print("\n" + "=" * 60)
    print("✅ 叙述连贯性检查")
    print("=" * 60)
    
    current_narrative = "哈利·波特在城堡走廊中前进，感受到了一种陌生的魔法气息。"
    previous_narrative = "他谨慎地从大厅走出来，思考着最近发生的奇异事件。"
    
    is_coherent, explanation = coherence_checker.validate_narrative_flow(
        current_narrative,
        previous_narrative,
        "move",
        game_state
    )
    
    print(f"\n  前一叙述: {previous_narrative}")
    print(f"  当前叙述: {current_narrative}")
    print(f"  连贯性检查: {explanation}")
    
    # 7. 性能统计
    print("\n" + "=" * 60)
    print("📈 系统信息")
    print("=" * 60)
    print(f"\n  模型后端: {type(nlg_engine.backend).__name__}")
    print(f"  动作预测: 已启用")
    print(f"  连贯性检查: 已启用")
    print(f"  生成的叙述总数: {len(nlg_engine.narrative_history)}")
    print(f"  玩家行动历史: {len(nlg_engine.player_action_history)}")
    
    print("\n✨ 测试完成！")
    print("=" * 60)


def test_action_prediction_patterns():
    """测试动作预测的模式识别"""
    
    print("\n" + "=" * 60)
    print("🧠 高级动作预测模式测试")
    print("=" * 60)
    
    from story_weaver.nlg.action_predictor import ActionPredictor
    
    predictor = ActionPredictor()
    
    # 测试不同位置的倾向
    locations = ["Hogwarts Castle", "Forbidden Forest", "Diagon Alley", "Ministry of Magic"]
    
    for location in locations:
        print(f"\n📍 {location}")
        
        game_state = {"current_location": location, "difficulty": "medium"}
        options = predictor.predict_next_options(game_state, location)
        
        print("  推荐的下一步行动:")
        for action, description in options:
            print(f"    • {description} [{action}]")


if __name__ == "__main__":
    print("\n🚀 启动增强型NLG系统测试\n")
    
    try:
        test_enhanced_nlg()
        test_action_prediction_patterns()
        
        print("\n\n✅ 所有测试成功完成!")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
