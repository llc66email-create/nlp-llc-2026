"""
状态管理模块 - 实时跟踪故事世界状态
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from copy import deepcopy

@dataclass
class Character:
    """角色类"""
    name: str
    location: str
    status: str  # "alive", "dead", "missing", etc.
    attributes: Dict[str, Any] = field(default_factory=dict)
    relationships: Dict[str, str] = field(default_factory=dict)  # 角色名->关系
    inventory: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Location:
    """地点类"""
    name: str
    description: str
    accessible: bool = True
    characters_present: List[str] = field(default_factory=list)
    objects: List[str] = field(default_factory=list)
    connections: Dict[str, str] = field(default_factory=dict)  # 地点名->连接
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Item:
    """物品类"""
    name: str
    owner: Optional[str]
    location: str
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return asdict(self)

@dataclass
class PlotNode:
    """剧情节点"""
    node_id: str
    title: str
    description: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    parent_nodes: List[str] = field(default_factory=list)
    child_nodes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return asdict(self)

class GameState:
    """故事游戏状态管理器"""
    
    def __init__(self):
        self.characters: Dict[str, Character] = {}
        self.locations: Dict[str, Location] = {}
        self.items: Dict[str, Item] = {}
        self.plot_nodes: Dict[str, PlotNode] = {}
        self.current_location: Optional[str] = None
        self.current_plot_node: Optional[str] = None
        self.player_character: Optional[str] = None
        self.interaction_history: List[Dict[str, Any]] = []
        self.world_variables: Dict[str, Any] = {}
        self.timestamp: str = datetime.now().isoformat()
        self._history_snapshots: List[Dict[str, Any]] = []
    
    def add_character(self, character: Character):
        """添加角色"""
        self.characters[character.name] = character
    
    def add_location(self, location: Location):
        """添加地点"""
        self.locations[location.name] = location
    
    def add_item(self, item: Item):
        """添加物品"""
        self.items[item.name] = item
    
    def add_plot_node(self, plot_node: PlotNode):
        """添加剧情节点"""
        self.plot_nodes[plot_node.node_id] = plot_node
    
    def move_character(self, character_name: str, location_name: str):
        """移动角色到新地点"""
        if character_name not in self.characters:
            raise ValueError(f"角色 {character_name} 不存在")
        if location_name not in self.locations:
            raise ValueError(f"地点 {location_name} 不存在")
        
        # 从旧地点移除
        old_location = self.characters[character_name].location
        if old_location in self.locations:
            self.locations[old_location].characters_present.remove(character_name)
        
        # 添加到新地点
        self.characters[character_name].location = location_name
        if character_name not in self.locations[location_name].characters_present:
            self.locations[location_name].characters_present.append(character_name)
    
    def update_character_status(self, character_name: str, status: str, details: Dict[str, Any] = None):
        """更新角色状态"""
        if character_name not in self.characters:
            raise ValueError(f"角色 {character_name} 不存在")
        
        self.characters[character_name].status = status
        if details:
            self.characters[character_name].attributes.update(details)
    
    def add_item_to_character(self, character_name: str, item_name: str):
        """将物品给予角色"""
        if character_name not in self.characters:
            raise ValueError(f"角色 {character_name} 不存在")
        if item_name not in self.items:
            raise ValueError(f"物品 {item_name} 不存在")
        
        item = self.items[item_name]
        item.owner = character_name
        if item_name not in self.characters[character_name].inventory:
            self.characters[character_name].inventory.append(item_name)
    
    def advance_plot_node(self, new_node_id: str):
        """推进剧情到新节点"""
        old_node = self.current_plot_node
        self.current_plot_node = new_node_id
        
        if new_node_id in self.plot_nodes:
            if old_node and old_node in self.plot_nodes:
                self.plot_nodes[old_node].child_nodes.append(new_node_id)
            self.plot_nodes[new_node_id].parent_nodes.append(old_node)
    
    def record_interaction(self, user_input: str, intent: str, entities: List[str], 
                          response: str, plot_node: str, consistency_check: bool = True):
        """记录交互"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "intent": intent,
            "entities": entities,
            "response": response,
            "plot_node": plot_node,
            "consistency_check": consistency_check,
            "state_snapshot": self.get_state_snapshot()
        }
        self.interaction_history.append(interaction)
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """获取当前状态快照"""
        return {
            "timestamp": datetime.now().isoformat(),
            "current_location": self.current_location,
            "current_plot_node": self.current_plot_node,
            "player_character": self.player_character,
            "characters": {name: char.to_dict() for name, char in self.characters.items()},
            "locations": {name: loc.to_dict() for name, loc in self.locations.items()},
            "items": {name: item.to_dict() for name, item in self.items.items()},
            "world_variables": deepcopy(self.world_variables)
        }
    
    def save_snapshot(self):
        """保存当前状态快照"""
        self._history_snapshots.append(self.get_state_snapshot())
    
    def get_character_info(self, character_name: str) -> Optional[Dict[str, Any]]:
        """获取角色信息"""
        if character_name in self.characters:
            return self.characters[character_name].to_dict()
        return None
    
    def get_location_info(self, location_name: str) -> Optional[Dict[str, Any]]:
        """获取地点信息"""
        if location_name in self.locations:
            return self.locations[location_name].to_dict()
        return None
    
    def get_world_context(self) -> Dict[str, Any]:
        """获取基于当前位置的世界上下文"""
        context = {
            "current_location": self.current_location,
            "player_character": self.player_character,
            "nearby_characters": [],
            "available_items": [],
            "accessible_locations": []
        }
        
        if self.current_location in self.locations:
            loc = self.locations[self.current_location]
            context["location_description"] = loc.description
            context["nearby_characters"] = loc.characters_present
            context["available_items"] = loc.objects
            context["accessible_locations"] = list(loc.connections.values())
        
        return context
    
    def get_recent_history(self, max_length: int = 10) -> List[Dict[str, Any]]:
        """获取最近的交互历史"""
        return self.interaction_history[-max_length:]
    
    def reset(self):
        """重置状态"""
        self.characters.clear()
        self.locations.clear()
        self.items.clear()
        self.plot_nodes.clear()
        self.interaction_history.clear()
        self.world_variables.clear()
        self._history_snapshots.clear()
        self.current_location = None
        self.current_plot_node = None
        self.player_character = None
    
    def to_json(self) -> str:
        """序列化为JSON"""
        return json.dumps(self.get_state_snapshot(), ensure_ascii=False, indent=2)
