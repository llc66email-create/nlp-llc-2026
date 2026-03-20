"""
Story Weaver 系统测试脚本
"""
import sys
import time
from pathlib import Path

def test_nlu():
    """测试NLU模块"""
    print("\n" + "=" * 60)
    print("测试 NLU 模块")
    print("=" * 60)
    
    from story_weaver.nlu.intent_extractor import NLUEngine
    
    nlu = NLUEngine(confidence_threshold=0.6)
    
    test_cases = [
        "Go to Hogwarts",
        "Talk to Harry Potter",
        "Cast Expelliarmus",
        "Look around",
        "Take the Horcrux",
    ]
    
    for user_input in test_cases:
        print(f"\n输入: {user_input}")
        result = nlu.process(user_input)
        print(f"  意图: {result.intent.value} (信度: {result.confidence:.3f})")
        print(f"  实体: {[(e.type, e.value) for e in result.entities]}")
        if result.requires_clarification:
            print(f"  澄清: {result.clarification_message}")

def test_state_management():
    """测试状态管理"""
    print("\n" + "=" * 60)
    print("测试 状态管理 模块")
    print("=" * 60)
    
    from story_weaver.state_management.game_state import (
        GameState, Character, Location, Item, PlotNode
    )
    
    state = GameState()
    
    # 创建位置
    hogwarts = Location(
        name="Hogwarts Castle",
        description="A magical school",
        accessible=True
    )
    state.add_location(hogwarts)
    
    # 创建角色
    harry = Character(
        name="Harry Potter",
        location="Hogwarts Castle",
        status="alive"
    )
    state.add_character(harry)
    
    # 创建物品
    wand = Item(
        name="Magic Wand",
        owner="Harry Potter",
        location="Hogwarts Castle"
    )
    state.add_item(wand)
    
    print("\n✓ 位置已添加")
    print(f"  - {state.get_location_info('Hogwarts Castle')['name']}")
    
    print("\n✓ 角色已添加")
    print(f"  - {state.get_character_info('Harry Potter')['name']}")
    
    print("\n✓ 物品已添加")
    print(f"  - {state.items['Magic Wand'].name}")
    
    # 测试移动
    forest = Location(
        name="Forbidden Forest",
        description="A dark forest",
        accessible=True
    )
    state.add_location(forest)
    
    state.move_character("Harry Potter", "Forbidden Forest")
    print("\n✓ 角色已移动到禁林")
    
    # 获取快照
    snapshot = state.get_state_snapshot()
    print(f"\n✓ 状态快照生成")
    print(f"  - 当前位置: {snapshot['current_location']}")

def test_rag():
    """测试RAG系统"""
    print("\n" + "=" * 60)
    print("测试 RAG 检索系统")
    print("=" * 60)
    
    from story_weaver.rag.retriever import RAGRetriever
    from config import DataConfig
    
    retriever = RAGRetriever()
    retriever.initialize_from_knowledge_base(DataConfig.KNOWLEDGE_BASE_PATH)
    
    print(f"\n✓ 知识库已加载 ({len(retriever.segments)} 个片段)")
    
    queries = [
        "Harry meets Dumbledore",
        "Forbidden Forest danger",
        "Diagon Alley shopping"
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        results = retriever.retrieve(query, top_k=3)
        for i, segment in enumerate(results, 1):
            print(f"  {i}. [{segment.source}] {segment.content[:50]}... (相似度: {segment.relevance_score:.3f})")

def test_nlg():
    """测试NLG模块"""
    print("\n" + "=" * 60)
    print("测试 NLG 生成模块")
    print("=" * 60)
    
    from story_weaver.nlg.generator import NLGEngine, DialogueGenerator
    
    nlg = NLGEngine()
    print("✓ NLG引擎已初始化")
    
    dialogue = DialogueGenerator()
    print("✓ 对话生成器已初始化")
    
    # 测试对话生成
    test_characters = ["Harry", "Hermione", "Ron", "Dumbledore"]
    print("\n对话生成示例:")
    for char in test_characters:
        dialogue_text = dialogue.generate_dialogue(char, "battle", "determined")
        print(f"  {char}: {dialogue_text}")

def test_consistency():
    """测试一致性检查"""
    print("\n" + "=" * 60)
    print("测试 一致性检查 模块")
    print("=" * 60)
    
    from story_weaver.consistency.checker import ConsistencyChecker
    from config import DataConfig
    
    checker = ConsistencyChecker(rules_path=DataConfig.CONSISTENCY_RULES_PATH)
    
    print(f"✓ 一致性检查器已初始化 ({len(checker.rules)} 个规则)")
    
    # 记录一个事实
    checker.record_fact(
        fact_id="fact_001",
        fact_type="character_status",
        entity="Harry Potter",
        attribute="status",
        value="alive"
    )
    
    print("\n✓ 事实已记录: Harry Potter is alive")
    
    # 检查一致性
    action = {
        "character": "Harry Potter",
        "action": "move",
        "new_status": "alive"
    }
    
    is_valid, violation = checker.check_consistency(action, {})
    print(f"\n✓ 一致性检查: {'通过' if is_valid else '失败'}")

def test_full_system():
    """测试完整系统"""
    print("\n" + "=" * 60)
    print("测试 完整系统集成")
    print("=" * 60)
    
    from story_weaver.core import StoryWeaver
    
    print("\n初始化Story Weaver系统...")
    weaver = StoryWeaver()
    
    print("\n开始新游戏...")
    weaver.start_new_game()
    
    print("\n处理用户输入...")
    test_inputs = [
        "Look around",
        "Go to Forbidden Forest",
        "Talk to Dumbledore"
    ]
    
    for user_input in test_inputs:
        print(f"\n用户: {user_input}")
        
        start_time = time.time()
        result = weaver.process_user_input(user_input)
        response_time = result.get('response_time', 0)
        
        if result['status'] == 'success':
            print(f"故事: {result['narrative'][:100]}...")
            print(f"选项: {result['next_options']}")
            print(f"响应时间: {response_time:.3f}秒")
        else:
            print(f"状态: {result['status']}")
            print(f"消息: {result.get('message', '')}")
    
    print("\n结束会话...")
    summary = weaver.end_session()
    print(f"共交互: {summary['summary']['total_interactions']} 轮")
    print(f"一致性检查: {summary['summary']['consistency_checks']}")

def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print(" " * 20 + "Story Weaver 系统测试")
    print("=" * 80)
    
    tests = [
        ("NLU模块", test_nlu),
        ("状态管理", test_state_management),
        ("RAG检索", test_rag),
        ("NLG生成", test_nlg),
        ("一致性检查", test_consistency),
        ("完整系统", test_full_system)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"\n✓ {test_name} 测试通过")
        except Exception as e:
            failed += 1
            print(f"\n✗ {test_name} 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Story Weaver 系统测试")
    parser.add_argument(
        "--module",
        choices=["nlu", "state", "rag", "nlg", "consistency", "full", "all"],
        default="all",
        help="要测试的模块"
    )
    
    args = parser.parse_args()
    
    tests_map = {
        "nlu": test_nlu,
        "state": test_state_management,
        "rag": test_rag,
        "nlg": test_nlg,
        "consistency": test_consistency,
        "full": test_full_system,
        "all": run_all_tests
    }
    
    try:
        if args.module == "all":
            success = run_all_tests()
        else:
            tests_map[args.module]()
            success = True
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    sys.exit(0 if success else 1)
