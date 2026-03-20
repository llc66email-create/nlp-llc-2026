"""
互动日志系统 - 记录多轮交互
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

class InteractionLogger:
    """互动日志记录器"""
    
    def __init__(self, log_dir: Path):
        """初始化日志记录器"""
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前会话日志
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.log_dir / f"session_{self.session_id}.jsonl"
        
        # 统计信息
        self.stats = defaultdict(int)
        self.interaction_count = 0
    
    def log_interaction(self, 
                       user_input: str,
                       intent: str,
                       entities: List[str],
                       nlu_confidence: float,
                       retrieved_segments: List[str],
                       response: str,
                       next_options: List[str],
                       game_state: Dict,
                       consistency_check: bool,
                       response_time: float):
        """记录单轮交互"""
        
        interaction_log = {
            "interaction_id": self.interaction_count,
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "nlu": {
                "intent": intent,
                "entities": entities,
                "confidence": nlu_confidence
            },
            "rag": {
                "retrieved_segments": retrieved_segments,
                "segment_count": len(retrieved_segments)
            },
            "response": response,
            "next_options": next_options,
            "game_state": {
                "current_location": game_state.get("current_location"),
                "player_character": game_state.get("player_character"),
                "characters_near": len(game_state.get("nearby_characters", []))
            },
            "consistency": {
                "check_passed": consistency_check
            },
            "performance": {
                "response_time_seconds": response_time
            }
        }
        
        # 写入JSONL文件
        with open(self.session_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(interaction_log, ensure_ascii=False) + '\n')
        
        # 更新统计
        self.stats["total_interactions"] += 1
        self.stats[f"intent_{intent}"] += 1
        if consistency_check:
            self.stats["consistency_passed"] += 1
        else:
            self.stats["consistency_failed"] += 1
        
        self.interaction_count += 1
    
    def log_error(self, error_type: str, error_message: str, 
                 context: Optional[Dict] = None):
        """记录错误"""
        error_log = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        
        error_file = self.log_dir / f"error_{self.session_id}.log"
        with open(error_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(error_log, ensure_ascii=False) + '\n')
        
        self.stats["errors"] += 1
    
    def log_state_change(self, change_type: str, details: Dict):
        """记录状态变化"""
        state_log = {
            "timestamp": datetime.now().isoformat(),
            "change_type": change_type,
            "details": details
        }
        
        state_file = self.log_dir / f"state_changes_{self.session_id}.jsonl"
        with open(state_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(state_log, ensure_ascii=False) + '\n')
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        return {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "total_interactions": self.stats["total_interactions"],
            "consistency_checks": {
                "passed": self.stats.get("consistency_passed", 0),
                "failed": self.stats.get("consistency_failed", 0)
            },
            "intent_distribution": {
                k.replace("intent_", ""): v 
                for k, v in self.stats.items() 
                if k.startswith("intent_")
            },
            "errors": self.stats.get("errors", 0)
        }
    
    def save_session_summary(self):
        """保存会话摘要"""
        summary = self.get_session_summary()
        summary_file = self.log_dir / f"summary_{self.session_id}.json"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load_session_logs(session_file: Path) -> List[Dict]:
        """加载会话日志"""
        logs = []
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        return logs
    
    @staticmethod
    def analyze_session(session_file: Path) -> Dict[str, Any]:
        """分析会话"""
        logs = InteractionLogger.load_session_logs(session_file)
        
        if not logs:
            return {"error": "No logs found"}
        
        analysis = {
            "total_interactions": len(logs),
            "average_response_time": sum(log["performance"]["response_time_seconds"] for log in logs) / len(logs),
            "consistency_rate": sum(1 for log in logs if log["consistency"]["check_passed"]) / len(logs),
            "average_nlu_confidence": sum(log["nlu"]["confidence"] for log in logs) / len(logs),
            "most_common_intent": max(
                set(log["nlu"]["intent"] for log in logs),
                key=lambda x: sum(1 for log in logs if log["nlu"]["intent"] == x)
            ),
            "total_unique_locations": len(set(log["game_state"]["current_location"] for log in logs)),
        }
        
        return analysis


class ReplaySystem:
    """回放系统 - 重放之前的交互"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
    
    def list_sessions(self) -> List[str]:
        """列出所有会话"""
        sessions = []
        for file in self.log_dir.glob("session_*.jsonl"):
            session_id = file.stem.replace("session_", "")
            sessions.append(session_id)
        return sorted(sessions, reverse=True)
    
    def load_session(self, session_id: str) -> List[Dict]:
        """加载特定会话"""
        session_file = self.log_dir / f"session_{session_id}.jsonl"
        return InteractionLogger.load_session_logs(session_file)
    
    def replay_session(self, session_id: str) -> Dict:
        """回放会话并生成摘要"""
        logs = self.load_session(session_id)
        
        if not logs:
            return {"error": f"Session {session_id} not found"}
        
        summary = {
            "session_id": session_id,
            "total_interactions": len(logs),
            "interactions": []
        }
        
        for i, log in enumerate(logs):
            summary["interactions"].append({
                "round": i + 1,
                "user_input": log["user_input"],
                "intent": log["nlu"]["intent"],
                "response_preview": log["response"][:100] + "...",
                "location": log["game_state"]["current_location"]
            })
        
        return summary
