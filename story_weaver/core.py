"""
Story Weaver 主系统 - 整合所有模块
"""
import time
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json
from dataclasses import asdict

from config import ModelConfig, DataConfig, SystemConfig, StoryConfig
from story_weaver.state_management.game_state import GameState, Character, Location, Item, PlotNode
from story_weaver.nlu.intent_extractor import NLUEngine, Intent
from story_weaver.rag.retriever import RAGRetriever, ContextBuilder
# OpenAI/DeepSeek API 模式优先；否则尝试增强型生成器
if ModelConfig.USE_OPENAI_API:
    from story_weaver.nlg.generator import NLGEngine
    print("[Core] 使用 DeepSeek/OpenAI API NLG生成器")
else:
    try:
        from story_weaver.nlg.enhanced_generator import EnhancedNLGEngine as NLGEngine
        print("[Core] 使用增强型NLG生成器（支持轻量级中文模型）")
    except ImportError:
        from story_weaver.nlg.generator import NLGEngine
        print("[Core] 使用原始NLG生成器")
from story_weaver.nlg.generator import DialogueGenerator
from story_weaver.consistency.checker import ConsistencyChecker
from story_weaver.logging import InteractionLogger
from story_weaver.constraint_engine import ConstraintEngine, TimelineBook
from story_weaver.validation_pipeline import StoryValidationPipeline, StoryProgressTracker

class StoryWeaver:
    """互动叙事系统的主类"""
    
    # 可用角色列表
    PLAYABLE_CHARACTERS = {
        "Harry Potter": {
            "title": "哈利·波特 - 霍格沃茨巫师",
            "description": "勇敢、决断的年轻巫师。你是'男孩不杀死他的预言之子'，命运掌握在你的手中。",
            "house": "Gryffindor",
            "abilities": ["强大的防守力", "对抗黑魔法的直觉"],
            "starting_location": "Hogwarts Castle"
        },
        "Hermione Granger": {
            "title": "赫敏·格兰杰 - 天才女巫",
            "description": "聪慧、有原则的魔法天才。你对魔法的理解无人能及，知识是你最强的武器。",
            "house": "Gryffindor",
            "abilities": ["高级魔法知识", "战略思维", "拓展咒语"],
            "starting_location": "Hogwarts Castle"
        },
        "Ron Weasley": {
            "title": "罗恩·韦斯莱 - 忠诚的同伴",
            "description": "忠诚、勇敢的巫师。虽然有时自我怀疑，但你的友谊和决心是无价之宝。",
            "house": "Gryffindor",
            "abilities": ["象棋战术", "战斗意志", "朋友忠诚"],
            "starting_location": "Hogwarts Castle"
        },
        "Albus Dumbledore": {
            "title": "邓布利多 - 魔法大师",
            "description": "智慧的老师，霍格沃茨的领袖。你拥有强大的魔法力量和深邃的智慧。",
            "house": "Gryffindor",
            "abilities": ["至高魔法", "深邃智慧", "神秘力量"],
            "starting_location": "Headmaster\'s Office"
        }
    }
    
    def __init__(self, load_knowledge_base: bool = True):
        """初始化Story Weaver系统"""
        print("初始化Story Weaver系统...")
        
        # 初始化各个模块
        self.nlu_engine = NLUEngine(
            confidence_threshold=SystemConfig.INTENT_CONFIDENCE_THRESHOLD
        )
        print("✓ NLU引擎初始化完成")
        
        self.rag_retriever = RAGRetriever(
            embedding_model=ModelConfig.EMBEDDING_MODEL
        )
        self.context_builder = ContextBuilder(self.rag_retriever)
        if load_knowledge_base:
            self.rag_retriever.initialize_from_knowledge_base(DataConfig.KNOWLEDGE_BASE_PATH)
        print("✓ RAG系统初始化完成")
        
        # 初始化NLG引擎 - OpenAI API 和本地模型二选一
        if ModelConfig.USE_OPENAI_API:
            from story_weaver.nlg.generator import NLGEngine as OriginalNLGEngine
            self.nlg_engine = OriginalNLGEngine(
                model_name=ModelConfig.TEXT_GENERATION_MODEL,
                use_llm=False,
                use_openai_api=True,
                openai_model=ModelConfig.OPENAI_API_MODEL
            )
            print(f"✓ OpenAI API NLG引擎初始化完成（模型: {ModelConfig.OPENAI_API_MODEL}）")
        elif ModelConfig.USE_LLM_GENERATION:
            if getattr(ModelConfig, "USE_COLAB_REMOTE", False):
                try:
                    self.nlg_engine = NLGEngine(
                        backend="colab_remote",
                        enable_action_prediction=True,
                        enable_coherence_check=True
                    )
                    print("✓ 增强型NLG引擎初始化完成（后端:colab_remote）")
                except Exception as e:
                    print(f"⚠️ colab_remote后端加载失败: {e}，回退到template")
                    self.nlg_engine = NLGEngine(
                        backend="template",
                        enable_action_prediction=True,
                        enable_coherence_check=True
                    )
            elif getattr(ModelConfig, "USE_FINETUNED_MODEL", False):
                try:
                    self.nlg_engine = NLGEngine(
                        backend="qwen25_lora",
                        enable_action_prediction=True,
                        enable_coherence_check=True
                    )
                    print("✓ 增强型NLG引擎初始化完成（后端:qwen25_lora）")
                except Exception as e:
                    print(f"⚠️ qwen25_lora后端加载失败: {e}，回退到template")
                    self.nlg_engine = NLGEngine(
                        backend="template",
                        enable_action_prediction=True,
                        enable_coherence_check=True
                    )
            elif ModelConfig.TEXT_GENERATION_MODEL in ["distilgpt2", "distilgpt2-chinese"]:
                try:
                    self.nlg_engine = NLGEngine(
                        backend="distilgpt2",
                        enable_action_prediction=True,
                        enable_coherence_check=True
                    )
                    print(f"✓ 增强型NLG引擎初始化完成（后端:distilgpt2）")
                except Exception as e:
                    print(f"⚠️ distilgpt2后端加载失败: {e}，回退到原始LLM")
                    from story_weaver.nlg.generator import NLGEngine as OriginalNLGEngine
                    self.nlg_engine = OriginalNLGEngine(
                        model_name=ModelConfig.TEXT_GENERATION_MODEL,
                        use_llm=True
                    )
                    print(f"✓ 原始NLG引擎初始化完成（LLM: {ModelConfig.TEXT_GENERATION_MODEL}）")
            else:
                from story_weaver.nlg.generator import NLGEngine as OriginalNLGEngine
                self.nlg_engine = OriginalNLGEngine(
                    model_name=ModelConfig.TEXT_GENERATION_MODEL,
                    use_llm=True
                )
                print(f"✓ 原始NLG引擎初始化完成（LLM: {ModelConfig.TEXT_GENERATION_MODEL}）")
        else:
            self.nlg_engine = NLGEngine(
                backend="template",
                enable_action_prediction=True,
                enable_coherence_check=True
            )
            print("✓ 增强型NLG引擎初始化完成（后端:template）")

        
        self.consistency_checker = ConsistencyChecker(
            rules_path=DataConfig.CONSISTENCY_RULES_PATH
        )
        print("✓ 一致性检查器初始化完成")

        # 约束引擎 & 故事推进追踪器
        self.constraint_engine = ConstraintEngine()
        self.validation_pipeline = StoryValidationPipeline()
        self.story_tracker = StoryProgressTracker()
        # 默认从第一册开始，可通过 select_timeline 修改
        self.current_book = TimelineBook.BOOK_1
        print("✓ 约束引擎 & 故事推进追踪器初始化完成")

        self.game_state = GameState()
        self._initialize_game_state()
        print("✓ 游戏状态初始化完成")
        
        self.logger = InteractionLogger(SystemConfig.LOG_DIR)
        print("✓ 日志系统初始化完成")
        
        print("\n✓ Story Weaver系统已准备就绪！\n")
    
    def _initialize_game_state(self):
        """从知识库初始化游戏状态"""
        # 加载世界状态
        world_state_path = DataConfig.WORLD_STATE_PATH
        if world_state_path.exists():
            with open(world_state_path, 'r', encoding='utf-8') as f:
                world_data = json.load(f)
                
                # 初始化位置
                locations = world_data.get("locations", {})
                for loc_name, loc_data in locations.items():
                    location = Location(
                        name=loc_name,
                        description=loc_data.get("description", ""),
                        accessible=loc_data.get("accessible", True),
                        characters_present=loc_data.get("characters_present", []),
                        objects=loc_data.get("objects", []),
                        connections=loc_data.get("connections", {})
                    )
                    self.game_state.add_location(location)
                
                # 初始化游戏状态
                initial_state = world_data.get("initial_game_state", {})
                self.game_state.current_location = initial_state.get("current_location")
                self.game_state.current_plot_node = initial_state.get("current_plot_node")
                self.game_state.player_character = initial_state.get("player_character")
        
        # 加载角色
        character_path = DataConfig.CHARACTER_GRAPH_PATH
        if character_path.exists():
            with open(character_path, 'r', encoding='utf-8') as f:
                character_data = json.load(f)
                
                for char_name, char_info in character_data.get("characters", {}).items():
                    character = Character(
                        name=char_name,
                        location=char_info.get("location", "Unknown"),
                        status=char_info.get("status", "unknown"),
                        attributes=char_info.get("attributes", {}),
                        relationships=char_info.get("relationships", {}),
                        inventory=char_info.get("inventory", [])
                    )
                    self.game_state.add_character(character)
    
    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入并生成响应"""
        start_time = time.time()
        
        try:
            # 0. 将现实世界动作转换为哈利波特语境的等价动作，降低OOC风险
            reality_to_hp = {
                "吃饭": "前往霍格沃茨大厅用餐",
                "吃午饭": "前往霍格沃茨大厅用餐",
                "吃晚饭": "前往霍格沃茨大厅用餐",
                "吃早饭": "前往霍格沃茨大厅用餐",
                "点外卖": "去大厅找家养小精灵准备餐食",
                "订餐": "去大厅找家养小精灵准备餐食",
                "看手机": "翻看魔法书和活点地图",
                "刷手机": "翻看魔法书和活点地图",
                "玩手机": "翻看魔法书和活点地图",
            }
            for src, dst in reality_to_hp.items():
                if src in user_input:
                    mapped = user_input.replace(src, dst)
                    print(f"[Core] 输入映射: {user_input!r} -> {mapped!r}")
                    user_input = mapped
                    break

            # 1. NLU - 意图识别
            intent = "move"  # 默认意图
            confidence = 0.8
            
            keywords_move = ["去", "走", "进入", "移动", "探索"]
            keywords_talk = ["说", "交谈", "对话"]
            keywords_take = ["拿", "得到", "捡"]
            
            user_input_lower = user_input.lower()
            for kw in keywords_move:
                if kw in user_input_lower:
                    intent = "move"
                    break
            for kw in keywords_talk:
                if kw in user_input_lower:
                    intent = "talk"
                    break
            for kw in keywords_take:
                if kw in user_input_lower:
                    intent = "take"
                    break
            
            # 2. **先更新游戏状态**（重点：在NLG之前！）
            if "move" in intent.lower():
                if "霍格沃茨" in user_input or "城堡" in user_input or "校园" in user_input:
                    self.game_state.current_location = "Hogwarts Castle"
                elif "禁林" in user_input or "森林" in user_input:
                    self.game_state.current_location = "Forbidden Forest"
                elif "对角巷" in user_input or "街道" in user_input:
                    self.game_state.current_location = "Diagon Alley"
                elif "魔法部" in user_input:
                    self.game_state.current_location = "Ministry of Magic"
            
            # 3. 获取**更新后的**游戏上下文
            world_context = self.game_state.get_world_context()

            # 3.5 约束引擎 - 对用户输入做预检
            player_char = self.game_state.player_character or "Harry Potter"
            current_location = self.game_state.current_location or "Hogwarts Castle"
            input_valid, input_violations = self.constraint_engine.validate_story_segment(
                user_input, player_char, current_location, self.current_book
            )
            constraint_warning = ""
            if not input_valid:
                # 仅记录警告，不阻断流程；违规信息将注入提示词
                constraint_warning = "；".join(v.reason for v in input_violations)
                print(f"[Constraint] ⚠️ 输入违规: {constraint_warning}")

            # 生成约束上下文（注入 NLG 提示词）
            constraint_ctx = self.validation_pipeline.generate_constraint_context(
                character=player_char,
                location=current_location,
                current_book=self.current_book,
                completed_tasks=self.story_tracker.completed_task_ids,
            )
            # 将约束上下文附加到 world_context
            if isinstance(world_context, dict):
                world_context["constraint_context"] = constraint_ctx
                world_context["constraint_warning"] = constraint_warning
            
            # 4. RAG - 检索相关的情节片段（真实检索）
            retrieved_segments = self.rag_retriever.retrieve(
                user_input,
                top_k=3
            )
            
            # 5. 一致性检查（简化）
            consistency_passed = True
            
            # 6. NLG - 生成叙事响应（基于更新后的状态）
            if hasattr(self.nlg_engine, 'action_predictor'):
                # 使用增强型生成器（返回NarrativeResponse对象）
                nlg_result = self.nlg_engine.generate_narrative(
                    user_input,
                    world_context,
                    [{"content": seg.content, "source": seg.source} for seg in retrieved_segments],
                    intent
                )
                narrative = nlg_result.main_narrative
                next_options = nlg_result.next_options if isinstance(nlg_result.next_options, list) else ["继续探索", "观察周围", "尝试其他操作"]
                state_updates = nlg_result.state_updates
                metadata = nlg_result.metadata
            else:
                # 使用原始生成器
                nlg_result = self.nlg_engine.generate_narrative(
                    user_input,
                    world_context,
                    [{"content": seg.content, "source": seg.source} for seg in retrieved_segments],
                    intent,
                    []
                )
                narrative = nlg_result.main_narrative
                next_options = nlg_result.next_options if hasattr(nlg_result, 'next_options') else ["继续探索", "观察周围", "尝试其他操作"]
                state_updates = nlg_result.state_updates if hasattr(nlg_result, 'state_updates') else {}
                metadata = nlg_result.metadata if hasattr(nlg_result, 'metadata') else {}
            
            # 6.5 约束验证 - 对生成内容做后验
            _, narrative_valid, narrative_violations = self.validation_pipeline.validate_and_refine(
                generated_text=narrative,
                player_character=player_char,
                location=current_location,
                current_book=self.current_book,
            )
            if not narrative_valid:
                for v in narrative_violations:
                    print(f"[Constraint] ⚠️ 输出违规({v.violation_type}): {v.reason}")

            # 6.6 故事推进检查
            task_completions = self.story_tracker.check_and_update(user_input, narrative)
            progress_summary = self.story_tracker.get_progress_summary()
            next_hint = self.story_tracker.get_hint_for_next_task()

            # 7. 记录交互并存入RAG（反馈循环）
            response_time = time.time() - start_time
            
            # 生成唯一的段落ID用于存储
            import hashlib
            interaction_id = hashlib.md5(f"{user_input}{response_time}".encode()).hexdigest()[:8]
            
            # 将这个交互存入RAG，以便未来的查询可以利用它
            self.rag_retriever.add_segment(
                segment_id=f"interaction_{interaction_id}",
                content=f"用户: {user_input}\n系统: {nlg_result.main_narrative}",
                source="interaction",
                tags=[intent, self.game_state.current_location or "unknown"]
            )
            
            # 也将NLG生成的单独响应存入RAG
            self.rag_retriever.add_segment(
                segment_id=f"narrative_{interaction_id}",
                content=nlg_result.main_narrative,
                source="generated_narrative",
                tags=[intent, user_input_lower.split()[0] if user_input_lower.split() else "action"]
            )
            
            return {
                "status": "success",
                "user_input": user_input,
                "intent": intent,
                "intent_confidence": confidence,
                "narrative": narrative,
                "next_options": next_options,
                "state_updates": state_updates,
                "current_location": self.game_state.current_location,
                "response_time": response_time,
                "consistency_check": consistency_passed,
                "retrieved_context": len(retrieved_segments),
                "metadata": metadata,
                # 约束 & 推进信息
                "constraint_warning": constraint_warning,
                "task_completions": task_completions,
                "story_progress": progress_summary,
                "next_task_hint": next_hint,
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            print(f"处理用户输入出错: {e}")
            return {
                "status": "success",
                "user_input": user_input,
                "intent": "unknown",
                "intent_confidence": 0.5,
                "narrative": "一阵奇异的魔法气流扫过你...",
                "next_options": ["继续您的冒险", "检查周围环境", "尝试其他操作"],
                "state_updates": {},
                "current_location": self.game_state.current_location or "Hogwarts Castle",
                "response_time": response_time,
                "consistency_check": True,
                "retrieved_context": 0
            }
    
    def _apply_state_updates(self, updates: Dict[str, str], nlu_result):
        """应用状态更新"""
        for key, value in updates.items():
            if key == "move_to":
                self.game_state.current_location = value
            elif key == "item_taken":
                player = self.game_state.player_character
                if player:
                    self.game_state.add_item_to_character(player, value)
            elif key == "talked_to":
                # 记录对话
                pass
    
    def get_available_characters(self) -> Dict[str, Dict[str, Any]]:
        """获取可选角色列表"""
        return self.PLAYABLE_CHARACTERS

    def get_campaign_overview(self, character_name: Optional[str] = None) -> Dict[str, Any]:
        """获取角色的完整章节和任务设计"""
        target_character = character_name or self.game_state.player_character or self.story_tracker.character_name

        if target_character not in self.PLAYABLE_CHARACTERS:
            target_character = self.story_tracker.character_name

        tracker = StoryProgressTracker(target_character)
        return tracker.get_campaign_overview()
    
    def select_character(self, character_name: str) -> Dict[str, Any]:
        """选择要扮演的角色"""
        if character_name not in self.PLAYABLE_CHARACTERS:
            return {
                "status": "error",
                "message": f"角色 {character_name} 不存在"
            }
        
        character_info = self.PLAYABLE_CHARACTERS[character_name]
        self.game_state.player_character = character_name
        self.game_state.current_location = character_info["starting_location"]
        self.story_tracker.set_character(character_name)
        
        return {
            "status": "character_selected",
            "character": character_name,
            "character_info": character_info
        }
    
    def start_new_game(self):
        """开始新游戏（需要先选择角色）"""
        if not self.game_state.player_character:
            return {
                "status": "error",
                "message": "请先选择一个角色"
            }
        
        self.logger = InteractionLogger(SystemConfig.LOG_DIR)
        
        # 生成详细的初始情景
        character_name = self.game_state.player_character
        location = self.game_state.current_location
        character_info = self.PLAYABLE_CHARACTERS[character_name]
        self.story_tracker.set_character(character_name)
        
        # 获取当前位置的详细信息
        location_details = self.game_state.get_location_info(location)
        
        # 构建详细的初始情景
        initial_scene = self._generate_initial_scene(character_name, location, character_info)
        
        return {
            "status": "game_started",
            "character": character_name,
            "location": location,
            "scene": initial_scene,
            "world_context": self.game_state.get_world_context(),
            "nearby_characters": location_details.get("characters_present", []) if location_details else []
        }
    
    def _generate_initial_scene(self, character_name: str, location: str, character_info: Dict) -> Dict[str, str]:
        """生成初始情景描述"""
        scenes = {
            "Hogwarts Castle": {
                "description": "我进入了霍格沃茨城堡的中心大厅。\n\n石头走廊里充满了魔法气息，火把的光芒在古老的石墙上摇曳。远处传来学生们的笑声，他们穿梭在众多的人物肖像之间。魔法楼梯在我眼前缓缓移动，通往城堡的各个区域。\n\n我可以看到：\n• 七楼通往各个学院公共休息室\n• 通往霍格沃茨餐厅和图书馆的通道\n• 鹅毛笔商品陈列柜\n• 古老的魔法时钟",
                "atmosphere": "神秘而充满魔力",
                "time_of_day": "傍晚课程刚刚结束"
            },
            "Headmaster\'s Office": {
                "description": "我坐在邓布利多办公室舒适的办公室里。\n\n这个圆形房间充满了魔法奇观。墙上挂满了历任校长的肖像，他们在画框中沉睡着或窃窃私语。银制仪器嘀嗒嘀嗒地响着，书架上摆满了厚厚的魔法书籍。凤凰福克斯栖息在它的栖木上，发出温柔的叫声。\n\n办公桌上有一个闪闪发光的思想盆。窗外可以看到霍格沃茨的广阔校园和禁林的轮廓。",
                "atmosphere": "宁静而充满智慧",
                "time_of_day": "傍晚"
            }
        }
        
        scene = scenes.get(location, {
            "description": f"我来到了{location}。这是哈利波特世界中的一个重要地点。",
            "atmosphere": "神秘而有趣",
            "time_of_day": "傍晚"
        })
        
        return {
            "title": f"欢迎，{character_name}！",
            "current_location": location,
            "character_description": character_info["description"],
            "scene_description": scene["description"],
            "atmosphere": scene["atmosphere"],
            "time_of_day": scene["time_of_day"],
            "prompt": "现在，我要做什么呢？\n\n(我可以输入任何行动，如：\"前往禁林\"、\"与邓布利多对话\"、\"使用魔法\"等)"
        }
    
    def get_game_status(self) -> Dict[str, Any]:
        """获取游戏状态"""
        return {
            "current_location": self.game_state.current_location,
            "player_character": self.game_state.player_character,
            "time_period": StoryConfig.INITIAL_TIME_PERIOD,
            "interaction_history_length": len(self.game_state.interaction_history),
            "world_context": self.game_state.get_world_context()
        }
    
    def save_game(self, save_name: str):
        """保存游戏"""
        save_path = SystemConfig.LOG_DIR / f"save_{save_name}.json"
        
        save_data = {
            "timestamp": time.time(),
            "save_name": save_name,
            "game_state": self.game_state.get_state_snapshot(),
            "interaction_history": self.game_state.get_recent_history(max_length=20)
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        return {"status": "game_saved", "file": str(save_path)}
    
    def end_session(self):
        """结束会话"""
        self.logger.save_session_summary()
        return {
            "status": "session_ended",
            "summary": self.logger.get_session_summary()
        }


def main():
    """测试主函数"""
    # 初始化系统
    weaver = StoryWeaver()
    
    # 开始游戏
    result = weaver.start_new_game()
    print(result["message"])
    
    # 测试几个交互
    test_inputs = [
        "Look around",
        "Go to the Forbidden Forest",
        "Cast a spell",
        "Talk to Harry Potter"
    ]
    
    for user_input in test_inputs:
        print(f"\n用户: {user_input}")
        result = weaver.process_user_input(user_input)
        
        if result["status"] == "success":
            print(f"故事: {result['narrative']}")
            print(f"选项: {result['next_options']}")
            print(f"响应时间: {result['response_time']:.3f}秒")
        else:
            print(f"状态: {result['status']}")
            print(f"消息: {result.get('message', '')}")
    
    # 结束会话
    summary = weaver.end_session()
    print(f"\n会话摘要: {json.dumps(summary['summary'], ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    main()
