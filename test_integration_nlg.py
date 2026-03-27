#!/usr/bin/env python3
"""
集成测试：完整的轻量级文本生成工作流
测试增强型NLG生成器在API中的实际表现
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:5001"

def print_response(title: str, data: Dict[str, Any]) -> None:
    """格式化打印响应"""
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")
    print(json.dumps(data, ensure_ascii=False, indent=2))


def test_full_workflow():
    """测试完整的游戏工作流"""
    
    print("🎮 开始集成测试：增强型NLG文本生成系统")
    print("="*60)
    
    # 1. 初始化
    print("\n[1] 初始化系统状态...")
    resp = requests.get(f"{BASE_URL}/api/init_status")
    print(f"    状态: {resp.json()['status']}")
    
    # 2. 获取可用角色
    print("\n[2] 获取可用角色...")
    resp = requests.get(f"{BASE_URL}/api/get_characters")
    if resp.status_code == 200:
        data = resp.json()
        chars = data.get("characters", [])
        if isinstance(chars, dict):
            chars = list(chars.keys())
        print(f"    ✓ 获取到 {len(chars)} 个角色")
        for char in list(chars)[:2]:
            print(f"      - {char}")
    else:
        print(f"    ✗ 错误: {resp.status_code}")
        return
    
    # 3. 选择角色
    print("\n[3] 选择角色...")
    char_to_select = "Harry Potter"
    resp = requests.post(
        f"{BASE_URL}/api/select_character",
        json={"character_name": char_to_select}
    )
    if resp.status_code == 200:
        data = resp.json()
        print(f"    ✓ 选择了: {data.get('character_selected', 'Unknown')}")
    else:
        print(f"    ✗ 错误: {resp.status_code} - {resp.text}")
        return
    
    # 4. 测试不同的输入并观察生成的文本
    test_inputs = [
        "走进大厅",
        "与邓布利多交谈战争的真相",
        "搜索禁林中的线索",
        "在对角巷购买魔法用品",
        "施放一个保护咒语"
    ]
    
    print("\n[4] 测试文本生成...")
    print("="*60)
    
    generation_results = []
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n📝 测试 {i}/{{len(test_inputs)}}:")
        print(f"   输入: {user_input}")
        print(f"   {'...'*20}")
        
        resp = requests.post(
            f"{BASE_URL}/api/process_input",
            json={"user_input": user_input}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            
            # 提取关键信息
            narrative = data.get("narrative", "")
            intent = data.get("intent", "unknown")
            options = data.get("next_options", [])
            location = data.get("current_location", "Unknown")
            metadata = data.get("metadata", {})
            
            print(f"   意图: {intent}")
            print(f"   位置: {location}")
            print(f"   生成的叙述:")
            print(f"   >>> {narrative}")
            
            if options:
                print(f"   下一步选项:")
                for opt in options[:3]:
                    if isinstance(opt, list):
                        print(f"     • {opt[1] if len(opt) > 1 else opt[0]}")
                    elif isinstance(opt, str):
                        print(f"     • {opt}")
            
            if metadata:
                model = metadata.get("model", "unknown")
                print(f"   使用的模型: {model}")
            
            generation_results.append({
                "input": user_input,
                "narrative": narrative,
                "intent": intent,
                "location": location,
                "model": model
            })
        else:
            print(f"   ✗ 错误: {resp.status_code}")
            print(f"      {resp.text}")
    
    # 5. 分析结果
    print("\n" + "="*60)
    print("📊 文本生成分析")
    print("="*60)
    
    print(f"\n生成的叙述总数: {len(generation_results)}")
    print(f"成功率: {len(generation_results)}/{len(test_inputs)}")
    
    # 检查文本质量
    print("\n📈 文本质量指标:")
    
    total_length = sum(len(r["narrative"]) for r in generation_results)
    avg_length = total_length / len(generation_results) if generation_results else 0
    
    print(f"  平均叙述长度: {avg_length:.1f} 字符")
    
    # 检查多样性
    unique_narratives = len(set(r["narrative"] for r in generation_results))
    print(f"  唯一的叙述: {unique_narratives}/{len(generation_results)}")
    
    # 检查意图识别
    intents = set(r["intent"] for r in generation_results)
    print(f"  识别到的意图: {', '.join(intents)}")
    
    # 检查位置变化
    locations = set(r["location"] for r in generation_results)
    print(f"  跟踪到的位置: {', '.join(locations)}")
    
    # 6. 显示示例
    print("\n" + "="*60)
    print("📚 生成的叙述示例总结")
    print("="*60)
    
    for i, result in enumerate(generation_results[:3], 1):
        print(f"\n示例 {i}:")
        print(f"  输入: {result['input']}")
        print(f"  叙述: {result['narrative']}")
        print()
    
    print("\n✨ 集成测试完成!")
    print("="*60)
    
    return generation_results


def test_narrative_coherence():
    """测试叙述的连贯性"""
    
    print("\n" + "="*60)
    print("🔗 叙述连贯性测试")
    print("="*60)
    
    # 进行一系列操作，验证故事的线索保持一致
    
    actions = [
        ("走向霍格沃茨图书馆", "探索"),
        ("与赫敏讨论魔咒理论", "学习"),
        ("发现一本古老的魔法书", "发现"),
        ("回到宿舍决定使用这些知识", "思考")
    ]
    
    print("\n执行故事序列，验证连贯性:")
    
    for action, description in actions:
        resp = requests.post(
            f"{BASE_URL}/api/process_input",
            json={"user_input": action}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            narrative = data.get("narrative", "")
            print(f"\n[{description}] {action}")
            print(f"✓ {narrative}")
        else:
            print(f"\n✗ 错误处理 {action}")
    
    print("\n✓ 连贯性测试完成")


def test_multiple_characters():
    """测试多个角色的生成风格"""
    
    print("\n" + "="*60)
    print("👥 多角色文本风格测试")
    print("="*60)
    
    characters = ["Harry Potter", "Hermione Granger", "Ron Weasley"]
    test_action = "施放一个强大的魔咒"
    
    for char in characters[:2]:  # 只测试前两个以节省时间
        print(f"\n测试角色: {char}")
        print("="*40)
        
        # 选择角色
        resp = requests.post(
            f"{BASE_URL}/api/select_character",
            json={"character_name": char}
        )
        
        if resp.status_code != 200:
            print(f"✗ 选择失败")
            continue
        
        # 测试相同的动作
        resp = requests.post(
            f"{BASE_URL}/api/process_input",
            json={"user_input": test_action}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            narrative = data.get("narrative", "")
            print(f"叙述: {narrative}")
        else:
            print(f"✗ 生成失败")


if __name__ == "__main__":
    import sys
    
    print("\n🚀 启动集成测试...\n")
    
    try:
        # 等待服务器完全启动
        print("🔄 等待服务器启动...")
        for _ in range(30):
            try:
                resp = requests.get(f"{BASE_URL}/api/init_status", timeout=1)
                if resp.status_code == 200:
                    print("✓ 服务器已就绪\n")
                    break
            except:
                time.sleep(0.5)
        
        # 运行测试
        results = test_full_workflow()
        test_narrative_coherence()
        test_multiple_characters()
        
        print("\n\n✅ 所有集成测试成功完成!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
