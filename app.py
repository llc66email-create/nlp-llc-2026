"""
Story Weaver Web演示界面
"""
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import json
from pathlib import Path
import traceback
import threading
import time
import logging

from story_weaver.core import StoryWeaver
from config import SystemConfig

# 禁用 Flask 和 Werkzeug 的日志
logging.getLogger('flask').setLevel(logging.ERROR)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__, template_folder='web_interface/templates', static_folder='web_interface/static')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.jinja_env.auto_reload = True
CORS(app)

# 全局Story Weaver实例和初始化状态
weaver = None
initialization_thread = None
initialization_complete = False
initialization_error = None

def initialize_app_background():
    """在后台线程中初始化应用"""
    global weaver, initialization_complete, initialization_error
    try:
        print("[后台初始化] 开始初始化 Story Weaver 系统...")
        start_time = time.time()
        weaver = StoryWeaver()
        elapsed = time.time() - start_time
        initialization_complete = True
        print(f"[后台初始化] ✓ Story Weaver 初始化完成（耗时: {elapsed:.1f}秒）")
    except Exception as e:
        initialization_error = str(e)
        print(f"[后台初始化] ✗ 初始化错误: {e}")
        traceback.print_exc()

def ensure_initialized():
    """确保应用已初始化"""
    global initialization_thread, weaver, initialization_complete
    
    # 如果还没有启动初始化线程，启动它
    if initialization_thread is None:
        print("[主线程] 启动后台初始化线程...")
        initialization_thread = threading.Thread(target=initialize_app_background, daemon=True)
        initialization_thread.start()
    
    return initialization_complete, weaver, initialization_error

@app.route('/')
def index():
    """主页"""
    # 启动后台初始化（如果还没启动）
    ensure_initialized()
    return render_template('index.html')

@app.route('/api/init_status', methods=['GET'])
def init_status():
    """获取初始化状态"""
    is_complete, _, error = ensure_initialized()
    return jsonify({
        "status": "complete" if is_complete else "initializing",
        "error": error
    }), 200

@app.route('/api/get_characters', methods=['GET'])
def get_characters():
    """获取可选角色列表（快速端点，不等待完整初始化）"""
    try:
        is_complete, weaver_instance, error = ensure_initialized()
        
        # 如果已初始化，返回实际角色
        if is_complete and weaver_instance:
            characters = weaver_instance.get_available_characters()
            return jsonify({
                "status": "success",
                "characters": characters,
                "initialized": True
            }), 200
        
        # 否则返回预定义的角色列表（快速响应）
        if error:
            return jsonify({
                "status": "error",
                "error": "系统初始化出错: " + error,
                "initialized": False
            }), 500
        
        # 返回预定义角色，告诉前端还在初始化中
        default_characters = {
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
                "starting_location": "Headmaster's Office"
            }
        }
        
        return jsonify({
            "status": "success",
            "characters": default_characters,
            "initialized": False,
            "message": "系统正在初始化中，请稍候..."
        }), 200
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/campaign_overview', methods=['GET'])
def campaign_overview():
    """获取角色完整章节与任务配置"""
    try:
        is_complete, weaver_instance, error = ensure_initialized()

        if not is_complete:
            return jsonify({
                "status": "error",
                "message": "系统还在初始化中，请稍候再试",
                "initialized": False
            }), 202

        if error or not weaver_instance:
            return jsonify({
                "status": "error",
                "message": "系统初始化出错: " + (error or "Unknown error")
            }), 500

        character_name = request.args.get('character_name', '').strip() or None
        result = weaver_instance.get_campaign_overview(character_name)
        return jsonify({"status": "success", "campaign": result}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/select_character', methods=['POST'])
def select_character():
    """选择角色"""
    try:
        is_complete, weaver_instance, error = ensure_initialized()
        
        if not is_complete:
            return jsonify({
                "status": "error",
                "message": "系统还在初始化中，请稍候再试",
                "initialized": False
            }), 202  # 202 Accepted - 请求已接受，但还在处理
        
        if error or not weaver_instance:
            return jsonify({
                "status": "error",
                "message": "系统初始化出错: " + (error or "Unknown error")
            }), 500
        
        data = request.json
        character_name = data.get('character_name', '').strip()
        
        if not character_name:
            return jsonify({"error": "Character name is required"}), 400
        
        result = weaver_instance.select_character(character_name)
        return jsonify(result), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/start_game', methods=['POST'])
def start_game():
    """开始新游戏"""
    try:
        is_complete, weaver_instance, error = ensure_initialized()
        
        if not is_complete:
            return jsonify({
                "status": "error",
                "message": "系统还在初始化中，请稍候再试",
                "initialized": False
            }), 202
        
        if error or not weaver_instance:
            return jsonify({
                "status": "error",
                "message": "系统初始化出错: " + (error or "Unknown error")
            }), 500
        
        result = weaver_instance.start_new_game()
        return jsonify(result), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/process_input', methods=['POST'])
def process_input():
    """处理用户输入"""
    try:
        is_complete, weaver_instance, error = ensure_initialized()
        
        if not is_complete:
            return jsonify({
                "status": "error",
                "message": "系统还在初始化中，请稍候再试",
                "initialized": False
            }), 202
        
        if error or not weaver_instance:
            return jsonify({
                "status": "error",
                "message": "系统初始化出错: " + (error or "Unknown error")
            }), 500
        
        data = request.json
        user_input = data.get('input', '').strip()
        
        if not user_input:
            return jsonify({"error": "Input cannot be empty"}), 400
        
        result = weaver_instance.process_user_input(user_input)
        return jsonify(result), 200
    
    except Exception as e:
        print(f"处理错误: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/process_input_stream', methods=['POST'])
def process_input_stream():
    """流式处理用户输入：先给短回应，再给完整结果。"""
    try:
        is_complete, weaver_instance, error = ensure_initialized()

        if not is_complete:
            return jsonify({
                "status": "error",
                "message": "系统还在初始化中，请稍候再试",
                "initialized": False
            }), 202

        if error or not weaver_instance:
            return jsonify({
                "status": "error",
                "message": "系统初始化出错: " + (error or "Unknown error")
            }), 500

        data = request.json or {}
        user_input = data.get('input', '').strip()
        if not user_input:
            return jsonify({"error": "Input cannot be empty"}), 400

        def _sse(event_name: str, payload: dict) -> str:
            return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

        @stream_with_context
        def event_stream():
            # 告知前端已开始处理
            yield _sse("status", {"stage": "started"})

            # 先尝试生成一句短回应（不改状态）
            try:
                backend = getattr(getattr(weaver_instance, "nlg_engine", None), "backend", None)
                quick_text = None
                if backend and hasattr(backend, "generate"):
                    game_state = getattr(weaver_instance, "game_state", None)
                    player_character = getattr(game_state, "player_character", None) or "Harry Potter"
                    current_location = getattr(game_state, "current_location", None) or "Hogwarts Castle"

                    # 用 RAG 提供一小段相关上下文，降低短回复偏离世界观的概率
                    rag_context = ""
                    try:
                        retriever = getattr(weaver_instance, "rag_retriever", None)
                        if retriever and hasattr(retriever, "retrieve"):
                            segs = retriever.retrieve(user_input, top_k=2)
                            ctx_lines = []
                            for seg in segs:
                                content = getattr(seg, "content", "")
                                if content:
                                    ctx_lines.append(content[:80])
                            if ctx_lines:
                                rag_context = " | ".join(ctx_lines)
                    except Exception:
                        rag_context = ""

                    quick_prompt = (
                        "你是哈利波特魔法世界叙事引擎。"
                        "请仅用中文、第一人称\"我\"输出一句即时叙事。"
                        "禁止现代世界助手口吻（如预订、客服、系统提示），"
                        "禁止出现与哈利波特世界无关的现实科技词汇。\n"
                        f"当前角色：{player_character}\n"
                        f"当前地点：{current_location}\n"
                        f"玩家行动：{user_input}\n"
                        f"相关背景：{rag_context or '无'}\n"
                        "即时回应（仅一句，不超过30字）："
                    )
                    quick_text = backend.generate(quick_prompt, max_length=30)

                    # 轻量后验过滤：若命中现代助手话术，则用规则兜底句
                    bad_markers = [
                        "预订", "餐厅", "稍等一下", "我会帮你", "客服", "订单", "app", "AI助手"
                    ]
                    if quick_text and any(marker in quick_text for marker in bad_markers):
                        quick_text = f"我在{current_location}先稳住心神，朝大厅方向快步而去。"
                if quick_text:
                    yield _sse("quick", {"text": quick_text})
            except Exception as e:
                yield _sse("warn", {"message": f"quick阶段失败: {e}"})

            # 再执行完整主流程（会更新状态）
            try:
                result = weaver_instance.process_user_input(user_input)
                yield _sse("final", result)
            except Exception as e:
                yield _sse("error", {"message": str(e)})
                return

            yield _sse("done", {"ok": True})

        headers = {
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
        return Response(event_stream(), mimetype='text/event-stream', headers=headers)
    except Exception as e:
        print(f"流式处理错误: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/game_status', methods=['GET'])
def game_status():
    """获取游戏状态"""
    try:
        is_complete, weaver_instance, error = ensure_initialized()
        
        if not is_complete:
            return jsonify({"status": "initializing"}), 202
        
        if error or not weaver_instance:
            return jsonify({"error": "System initialization failed"}), 500
        
        status = weaver_instance.get_game_status()
        return jsonify(status), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/save_game', methods=['POST'])
def save_game():
    """保存游戏"""
    try:
        is_complete, weaver_instance, error = ensure_initialized()
        
        if not is_complete:
            return jsonify({"error": "System is initializing"}), 202
        
        if error or not weaver_instance:
            return jsonify({"error": "System initialization failed"}), 500
        
        data = request.json
        save_name = data.get('save_name', 'autosave')
        result = weaver_instance.save_game(save_name)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/end_session', methods=['POST'])
def end_session():
    """结束会话"""
    try:
        is_complete, weaver_instance, error = ensure_initialized()
        
        if not is_complete:
            return jsonify({"error": "System is initializing"}), 202
        
        if error or not weaver_instance:
            return jsonify({"error": "System initialization failed"}), 500
        
        result = weaver_instance.end_session()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/interaction_history', methods=['GET'])
def interaction_history():
    """获取交互历史"""
    try:
        is_complete, weaver_instance, error = ensure_initialized()
        
        if not is_complete:
            return jsonify({"history": []}), 202
        
        if error or not weaver_instance:
            return jsonify({"error": "System initialization failed"}), 500
        
        history = weaver_instance.game_state.get_recent_history(max_length=20)
        return jsonify({"history": history}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/world_context', methods=['GET'])
def world_context():
    """获取世界上下文"""
    try:
        is_complete, weaver_instance, error = ensure_initialized()
        
        if not is_complete:
            return jsonify({"context": {}}), 202
        
        if error or not weaver_instance:
            return jsonify({"error": "System initialization failed"}), 500
        
        context = weaver_instance.game_state.get_world_context()
        return jsonify(context), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """404处理"""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """500处理"""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print(f"[Story Weaver] 服务器启动 - http://{SystemConfig.WEB_HOST}:{SystemConfig.WEB_PORT}")
    app.run(
        host=SystemConfig.WEB_HOST,
        port=SystemConfig.WEB_PORT,
        debug=SystemConfig.DEBUG_MODE,
        use_reloader=False
    )
