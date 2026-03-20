"""
RAG模块 - 检索增强生成系统
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json
import numpy as np
from pathlib import Path
try:
    import faiss
except ImportError:
    faiss = None

from sentence_transformers import SentenceTransformer

@dataclass
class RetrievedSegment:
    """检索到的情节片段"""
    segment_id: str
    content: str
    relevance_score: float
    source: str  # "plot", "character", "setting", "event"
    tags: List[str]

class RAGRetriever:
    """RAG检索系统"""
    
    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """初始化RAG系统 - 延迟加载模型"""
        self.embedding_model_name = embedding_model
        self.embedding_model = None  # 延迟初始化
        self.embeddings = None
        self.segments = []
        self.index = None
        self.segment_map = {}
    
    def initialize_from_knowledge_base(self, knowledge_base_path: Path):
        """从知识库初始化RAG系统"""
        plot_segments_path = knowledge_base_path / "plot_segments.json"
        
        if plot_segments_path.exists():
            with open(plot_segments_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                segments = data.get("segments", [])
                
                for segment in segments:
                    self.add_segment(
                        segment_id=segment.get("id", ""),
                        content=segment.get("content", ""),
                        source=segment.get("source", "plot"),
                        tags=segment.get("tags", [])
                    )
                
                # 构建索引
                self.build_index()
    
    def add_segment(self, segment_id: str, content: str, source: str = "plot", 
                   tags: List[str] = None):
        """添加情节片段"""
        if tags is None:
            tags = []
        
        self.segments.append({
            "id": segment_id,
            "content": content,
            "source": source,
            "tags": tags
        })
        self.segment_map[segment_id] = len(self.segments) - 1
    
    def build_index(self):
        """构建FAISS索引用于快速相似度搜索"""
        if not self.segments:
            return
        
        # 跳过嵌入生成（为了快速响应）
        # 如果需要真正的语义搜索，取消注释以下代码
        
        # if self.embedding_model is None:
        #     self.embedding_model = SentenceTransformer(self.embedding_model_name)
        # 
        # contents = [seg["content"] for seg in self.segments]
        # embeddings = self.embedding_model.encode(contents)
        # self.embeddings = embeddings
        #
        # if faiss is not None:
        #     dimension = embeddings.shape[1]
        #     self.index = faiss.IndexFlatL2(dimension)
        #     self.index.add(embeddings.astype('float32'))
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedSegment]:
        """检索最相关的片段"""
        if not self.segments:
            return []
        
        # 简单的关键字匹配检索
        query_lower = query.lower()
        scored_segments = []
        
        for seg in self.segments:
            content_lower = seg["content"].lower()
            tags_lower = [tag.lower() for tag in seg.get("tags", [])]
            
            # 计算相关度分数
            score = 0.0
            
            # 关键词匹配
            for word in query_lower.split():
                if len(word) > 2:  # 忽略短词
                    if word in content_lower:
                        score += 0.3
                    if word in tags_lower:
                        score += 0.7
            
            if score > 0:
                scored_segments.append((score, seg))
        
        # 按分数排序并返回前top_k
        scored_segments.sort(key=lambda x: x[0], reverse=True)
        
        retrieved = []
        for score, seg in scored_segments[:top_k]:
            retrieved.append(RetrievedSegment(
                segment_id=seg["id"],
                content=seg["content"],
                relevance_score=min(score / 10.0, 1.0),
                source=seg.get("source", "plot"),
                tags=seg.get("tags", [])
            ))
        
        # 如果没有找到匹配，保留原来的一些随机片段
        if not retrieved:
            import random
            sample_size = min(top_k // 2, len(self.segments))
            if sample_size > 0:
                selected = random.sample(self.segments, sample_size)
                for seg in selected:
                    retrieved.append(RetrievedSegment(
                        segment_id=seg["id"],
                        content=seg["content"],
                        relevance_score=0.3,
                        source=seg.get("source", "plot"),
                        tags=seg.get("tags", [])
                    ))
        
        return retrieved
    
    def add_segment(self, segment_id: str, content: str, source: str = "interaction", 
                   tags: List[str] = None) -> str:
        """添加新的片段到索引（用于存储NLG生成的内容）"""
        if tags is None:
            tags = []
        
        new_segment = {
            "id": segment_id,
            "content": content,
            "source": source,
            "tags": tags
        }
        
        self.segments.append(new_segment)
        self.segment_map[segment_id] = len(self.segments) - 1
        
        return segment_id
    
    def retrieve_by_tags(self, tags: List[str], top_k: int = 5) -> List[Dict]:
        """按标签检索片段"""
        matching_segments = [
            (i, seg) for i, seg in enumerate(self.segments)
            if any(tag in seg["tags"] for tag in tags)
        ]
        
        # 限制返回数量
        return [seg for _, seg in matching_segments[:top_k]]
    
    def retrieve_by_source(self, source: str) -> List[Dict]:
        """按来源检索片段"""
        return [seg for seg in self.segments if seg["source"] == source]
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))


class ContextBuilder:
    """上下文构建器 - 基于RAG结果构建故事上下文"""
    
    def __init__(self, retriever: RAGRetriever):
        self.retriever = retriever
    
    def build_narrative_context(self, user_input: str, game_state: Dict, top_k: int = 5) -> str:
        """构建叙事上下文"""
        retrieved = self.retriever.retrieve(user_input, top_k=top_k)
        
        context_parts = []
        
        # 添加当前状态信息
        if game_state.get("current_location"):
            context_parts.append(f"当前位置: {game_state['current_location']}")
        
        if game_state.get("player_character"):
            context_parts.append(f"玩家角色: {game_state['player_character']}")
        
        # 添加检索到的相关片段
        if retrieved:
            context_parts.append("\n相关剧情片段:")
            for i, segment in enumerate(retrieved, 1):
                context_parts.append(f"  {i}. [{segment.source}] {segment.content[:100]}...")
        
        return "\n".join(context_parts)
    
    def build_generation_prompt(self, user_input: str, game_state: Dict, 
                               intent: str, retrieved_segments: List[RetrievedSegment]) -> str:
        """构建用于文本生成的提示"""
        prompt_parts = [
            f"背景: 哈利波特宇宙",
            f"当前位置: {game_state.get('current_location', '未知')}",
            f"玩家角色: {game_state.get('player_character', '未知')}",
            f"用户意图: {intent}",
            f"用户输入: {user_input}",
            "\n相关背景:",
        ]
        
        for segment in retrieved_segments[:3]:  # 只用最相关的3个片段
            prompt_parts.append(f"- {segment.content}")
        
        prompt_parts.append("\n请生成一个连贯的、符合哈利波特背景的叙事响应。")
        
        return "\n".join(prompt_parts)
