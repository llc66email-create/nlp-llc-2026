"""
故事推进系统 - 定义章节任务、完成条件和验证管道
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class TaskStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StoryTask:
    """单个故事任务"""

    task_id: str
    title: str
    description: str
    trigger_keywords: List[str]
    completion_keywords: List[str]
    prerequisites: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.NOT_STARTED
    unlocks: List[str] = field(default_factory=list)
    chapter: str = ""
    completion_feedback: str = ""
    is_main: bool = True
    chapter_no: int = 1
    quest_no: int = 1


MAIN_QUEST_TEMPLATE = {
    1: [
        ("抵达节点", "前往章节关键地点并建立行动基线", ["前往", "进入", "抵达", "到达", "出发"]),
        ("情报收集", "与关键人物交谈并收集第一批线索", ["交谈", "询问", "调查", "打听", "线索"]),
        ("环境侦查", "侦查现场、找出风险与可用资源", ["侦查", "观察", "检查", "搜索", "勘察"]),
        ("获取工具", "准备本章推进必须的道具或法术", ["准备", "获取", "借用", "学习", "拿到"]),
        ("突破障碍", "解决一个阻碍主线推进的显性难题", ["破解", "解开", "突破", "绕过", "通过"]),
        ("协同作战", "与盟友协作执行关键步骤", ["合作", "配合", "一起", "支援", "联手"]),
        ("核心行动", "执行本章核心目标行动", ["执行", "实施", "行动", "推进", "完成步骤"]),
        ("危机处理", "应对反制并稳定局面", ["应对", "防御", "处理", "反击", "稳住"]),
        ("章节收束", "确认阶段成果并进入下一章", ["总结", "汇报", "确认", "完成", "进入下一章"]),
    ],
    2: [
        ("确定目标", "明确本章主目标与行动窗口", ["明确目标", "确定", "制定", "确认", "计划"]),
        ("资源盘点", "检查可用资源与限制条件", ["盘点", "检查", "整理", "统计", "评估"]),
        ("路线规划", "拟定安全路线与备选方案", ["规划", "路线", "方案", "备选", "路径"]),
        ("潜入准备", "压低暴露风险，完成潜入准备", ["潜入", "伪装", "隐蔽", "掩护", "静默"]),
        ("第一触点", "接触目标区域并验证情报", ["接触", "试探", "验证", "确认情报", "探路"]),
        ("中段推进", "排除干扰，推进至关键位置", ["推进", "清理", "排除", "进入深处", "前进"]),
        ("关键决策", "做出影响后续走向的决定", ["决定", "选择", "权衡", "判断", "拍板"]),
        ("目标达成", "落实决策并达成本章主目标", ["达成", "落实", "实现", "办到", "拿下"]),
        ("信息回传", "向盟友回传结果并衔接下一章", ["回报", "回传", "同步", "汇合", "衔接"]),
    ],
    3: [
        ("异动发现", "发现异常并确认威胁类型", ["异常", "异动", "发现", "侦测", "识别"]),
        ("风险分级", "评估威胁优先级", ["评估", "分级", "优先", "风险", "判断"]),
        ("证据固定", "记录关键证据用于后续行动", ["记录", "取证", "固定", "保存", "证据"]),
        ("请求支援", "向可靠对象请求支援", ["请求", "支援", "援助", "联系", "召集"]),
        ("行动部署", "将任务分配到人", ["部署", "分配", "安排", "指派", "组织"]),
        ("执行突进", "执行高风险推进动作", ["突进", "冲锋", "突击", "切入", "抢占"]),
        ("局势扭转", "在对抗中夺回主动", ["扭转", "夺回", "反制", "压制", "逆转"]),
        ("稳态恢复", "恢复战术稳态并封堵漏洞", ["恢复", "封堵", "稳态", "补位", "加固"]),
        ("结案归档", "形成结论并推进主线", ["结案", "归档", "结论", "收尾", "推进"]),
    ],
    4: [
        ("议题开启", "开启本章核心议题", ["开启", "提出", "讨论", "议题", "启动"]),
        ("利益协调", "协调角色立场与利益冲突", ["协调", "沟通", "说服", "平衡", "安抚"]),
        ("证据比对", "比对情报排除伪线索", ["比对", "核对", "排查", "筛选", "剔除"]),
        ("路径试探", "试探性推进并验证可行性", ["试探", "验证", "可行", "尝试", "探测"]),
        ("风险对冲", "准备失败后的兜底方案", ["兜底", "备份", "对冲", "预案", "冗余"]),
        ("主行动发起", "正式发起主行动", ["发起", "启动行动", "实施", "执行", "动手"]),
        ("中段修正", "根据反馈修正行动", ["修正", "调整", "优化", "更改", "改进"]),
        ("成果锁定", "锁定本章成果防止回滚", ["锁定", "确认成果", "固化", "稳住", "保全"]),
        ("章节完成", "完成章节并切换下一章", ["章节完成", "完成本章", "进入下章", "收官", "结束"]),
    ],
    5: [
        ("线索汇总", "汇总此前章节关键线索", ["汇总", "整理线索", "串联", "回顾", "复盘"]),
        ("目标拆解", "把大目标拆成可执行小目标", ["拆解", "分解", "细化", "步骤", "子任务"]),
        ("难点预演", "提前预演最可能失败的环节", ["预演", "演练", "模拟", "推演", "试跑"]),
        ("角色分工", "明确每位角色的职责", ["分工", "职责", "负责", "岗位", "安排"]),
        ("正式执行", "按分工推进行动", ["执行", "推进", "落实", "按计划", "行动"]),
        ("突发应急", "处理突发事件并维持节奏", ["突发", "应急", "处理", "稳定", "止损"]),
        ("关键突破", "突破本章最难节点", ["突破", "攻克", "拿下", "解锁", "达成"]),
        ("成果交付", "交付阶段成果给盟友", ["交付", "提交", "汇报", "反馈", "递交"]),
        ("前线转场", "将战场重心转入下一章", ["转场", "转移", "前往", "接续", "衔接"]),
    ],
    6: [
        ("危机预警", "识别即将到来的重大危机", ["预警", "警报", "危机", "识别", "发现"]),
        ("防线勘定", "确认防线与薄弱点", ["防线", "薄弱点", "勘定", "布防", "排布"]),
        ("资源调度", "调度人员和关键物资", ["调度", "调配", "分发", "资源", "补给"]),
        ("先手行动", "发起先手以争夺主动", ["先手", "抢先", "先发", "压制", "夺先"]),
        ("强压推进", "在压力下维持推进", ["强压", "推进", "顶住", "坚持", "稳推"]),
        ("反制关键点", "反制敌方关键动作", ["反制", "阻止", "打断", "干扰", "压制"]),
        ("守住节点", "守住本章战略节点", ["守住", "固守", "防守", "保卫", "护住"]),
        ("转守为攻", "把局面转为主动进攻", ["转守为攻", "反攻", "推进战线", "压上", "反推"]),
        ("阶段凯旋", "确立阶段胜势", ["胜势", "凯旋", "赢下", "奠定", "扩大优势"]),
    ],
    7: [
        ("最终前夜", "完成大战前夜的最终准备", ["前夜", "准备", "检查", "确认", "待命"]),
        ("关键会谈", "与关键盟友统一战略", ["会谈", "统一", "战略", "协商", "定案"]),
        ("信号确认", "确认开战信号与撤离规则", ["信号", "确认", "规则", "口令", "联络"]),
        ("先遣行动", "派出先遣队试探敌情", ["先遣", "试探", "侦察", "探查", "前出"]),
        ("阵地构筑", "构筑与加固阵地", ["构筑", "加固", "布置", "架设", "巩固"]),
        ("开战应对", "应对首轮冲击", ["开战", "首轮", "应对", "迎击", "接战"]),
        ("稳住中线", "稳住中路核心战线", ["中线", "稳住", "守住", "顶住", "支援"]),
        ("突围协同", "协同友军完成关键突围", ["突围", "协同", "掩护", "接应", "突破"]),
        ("战线续命", "保住战线进入下一阶段", ["续命", "保住", "延续", "坚持", "顶住到底"]),
    ],
    8: [
        ("决战布局", "确定决战阶段的总布局", ["布局", "决战", "部署", "总攻", "安排"]),
        ("目标校准", "校准优先目标与节奏", ["校准", "优先", "目标", "节奏", "排序"]),
        ("火力组织", "组织火力与支援链", ["火力", "支援", "组织", "链路", "保障"]),
        ("诱敌牵制", "牵制敌方主力", ["诱敌", "牵制", "拖住", "引开", "吸引"]),
        ("深位行动", "执行深入敌后的关键行动", ["深入", "敌后", "渗透", "潜入", "突破"]),
        ("摧毁节点", "摧毁敌方关键节点", ["摧毁", "破坏", "拔除", "击毁", "瓦解"]),
        ("撤离回收", "完成撤离并回收队伍", ["撤离", "回收", "撤回", "集合", "归队"]),
        ("胜负手", "打出决定性胜负手", ["胜负手", "决定性", "关键一击", "翻盘", "定胜"]),
        ("通往终章", "完成终章前最后衔接", ["终章", "最后准备", "进入终章", "衔接", "就位"]),
    ],
}

SIDE_QUEST_TEMPLATE = {
    1: [
        ("帮助同学", "帮助一位同学解决困难", ["帮助同学", "帮忙", "协助", "援手", "解围"]),
        ("隐藏物品", "发现章节中的隐藏物品", ["寻找", "隐藏", "发现物品", "拾取", "找到"]),
        ("额外情报", "获取一条非主线情报", ["额外情报", "旁支线索", "打听", "偷听", "记录"]),
        ("声望事件", "完成提升声望的小事件", ["声望", "善举", "表扬", "奖励", "贡献"]),
    ],
    2: [
        ("图书馆检索", "在图书馆补全背景信息", ["图书馆", "检索", "查阅", "文献", "资料"]),
        ("补给筹备", "准备额外补给", ["补给", "准备物资", "采购", "收集材料", "储备"]),
        ("同伴支援", "协助同伴完成小目标", ["支援同伴", "协助队友", "帮赫敏", "帮罗恩", "帮哈利"]),
        ("隐秘观察", "在不暴露情况下观察敌情", ["隐秘观察", "潜伏", "监视", "跟踪", "记录动向"]),
    ],
    3: [
        ("设施修复", "修复受损设施", ["修复", "维护", "补强", "加固", "修理"]),
        ("物资回收", "回收散落资源", ["回收", "搜集", "拾回", "清点", "搬运"]),
        ("心理安抚", "安抚受惊同伴", ["安抚", "鼓励", "稳定情绪", "劝慰", "支持"]),
        ("战报整理", "整理并提交战报", ["战报", "整理", "记录", "汇编", "上报"]),
    ],
    4: [
        ("密道排查", "排查并标记安全密道", ["密道", "排查", "标记", "探路", "安全路线"]),
        ("防御试验", "试验一项防御法术或机关", ["试验", "防御法术", "机关", "演示", "测试"]),
        ("救援任务", "救援一名陷入困境的角色", ["救援", "营救", "解救", "带离", "护送"]),
        ("战术复盘", "完成一次战术复盘", ["复盘", "战术", "总结", "反思", "优化方案"]),
    ],
}

ROLE_CHAPTER_TITLES = {
    "Harry Potter": [
        "第一章·预兆与召唤（哈利）",
        "第二章·潜入与侦察（哈利）",
        "第三章·暗潮与反制（哈利）",
        "第四章·联盟与抉择（哈利）",
        "第五章·追踪与突破（哈利）",
        "第六章·防线与代价（哈利）",
        "第七章·开战前夜（哈利）",
        "第八章·决战前线（哈利）",
        "第九章·霍格沃茨保卫战（哈利正面对抗）",
    ],
    "Hermione Granger": [
        "第一章·知识与预警（赫敏）",
        "第二章·推理与布局（赫敏）",
        "第三章·证据与行动（赫敏）",
        "第四章·策略与组织（赫敏）",
        "第五章·破解与突进（赫敏）",
        "第六章·守护与应变（赫敏）",
        "第七章·战前统筹（赫敏）",
        "第八章·密室前夜（赫敏）",
        "第九章·霍格沃茨保卫战（赫敏毁魂器行动）",
    ],
    "Ron Weasley": [
        "第一章·家人与誓言（罗恩）",
        "第二章·侦察与勇气（罗恩）",
        "第三章·压力与成长（罗恩）",
        "第四章·协同与信任（罗恩）",
        "第五章·突围与坚持（罗恩）",
        "第六章·防守与担当（罗恩）",
        "第七章·战前集结（罗恩）",
        "第八章·密室突入（罗恩）",
        "第九章·霍格沃茨保卫战（罗恩毁魂器行动）",
    ],
    "Albus Dumbledore": [
        "第一章·校长的预判（邓布利多）",
        "第二章·全局部署（邓布利多）",
        "第三章·危机指挥（邓布利多）",
        "第四章·秩序与抉择（邓布利多）",
        "第五章·防线联动（邓布利多）",
        "第六章·攻守平衡（邓布利多）",
        "第七章·精神动员（邓布利多）",
        "第八章·总攻前奏（邓布利多）",
        "第九章·霍格沃茨保卫战（邓布利多统筹防御）",
    ],
}

ROLE_FOCUS = {
    "Harry Potter": "你需要以核心作战者身份推进剧情。",
    "Hermione Granger": "你需要以策略与知识核心身份推进剧情。",
    "Ron Weasley": "你需要以协同突击与执行者身份推进剧情。",
    "Albus Dumbledore": "你需要以总指挥与精神引导者身份推进剧情。",
}

CHAPTER9_ROLE_MAIN = {
    "Harry Potter": [
        ("集结凤凰社", "在城堡集结凤凰社与盟友", ["集结", "凤凰社", "盟友", "集合", "召集"]),
        ("疏散学生", "组织低年级学生撤离", ["疏散", "撤离", "护送", "安全区", "转移"]),
        ("守住主楼梯", "在主楼梯挡住第一波冲击", ["守住", "主楼梯", "抵挡", "防线", "顶住"]),
        ("夺回庭院", "反攻庭院并夺回通道", ["反攻", "庭院", "夺回", "清场", "推进"]),
        ("突破封锁", "突破食死徒封锁前往禁林边界", ["突破", "封锁", "禁林", "突进", "冲破"]),
        ("直面伏地魔", "在战场中心直面伏地魔", ["伏地魔", "正面对抗", "决斗", "直面", "对峙"]),
        ("稳住士气", "在混战中稳住盟军士气", ["士气", "鼓舞", "稳住", "号召", "坚持"]),
        ("终极决斗", "完成终极决斗的关键反制", ["终极", "决斗", "反制", "破解", "最后一击"]),
        ("赢得战争", "击败伏地魔，赢得霍格沃茨保卫战", ["赢得战争", "击败伏地魔", "战争胜利", "通关", "胜利"]),
    ],
    "Hermione Granger": [
        ("校验情报", "校验毁魂器相关线索与行动窗口", ["校验", "毁魂器", "线索", "确认", "推理"]),
        ("密室入口", "定位并开启密室入口", ["密室", "入口", "开启", "蛇佬腔", "定位"]),
        ("突破防护", "破解密室与毁魂器外围防护", ["破解", "防护", "咒文", "解咒", "突破"]),
        ("取得利器", "取得可摧毁毁魂器的关键工具", ["取得", "利器", "毒牙", "关键工具", "拿到"]),
        ("摧毁毁魂器", "摧毁关键毁魂器并回传战报", ["摧毁", "毁魂器", "成功", "完成破坏", "回传"]),
        ("回援主战场", "从密室撤离并回援主战场", ["回援", "主战场", "撤离", "归队", "支援"]),
        ("战场协调", "基于情报引导盟军调整战术", ["协调", "战术调整", "引导", "指挥", "更新情报"]),
        ("封堵反扑", "封堵敌方反扑通道", ["封堵", "反扑", "通道", "阻断", "封锁"]),
        ("赢得战争", "协助终局击败伏地魔，赢得战争", ["赢得战争", "击败伏地魔", "战争胜利", "通关", "胜利"]),
    ],
    "Ron Weasley": [
        ("战前补给", "完成战前补给与队伍整编", ["补给", "整编", "分发", "集合", "准备"]),
        ("协助密室定位", "协助定位密室通路", ["密室", "定位", "通路", "寻找", "追踪"]),
        ("强攻开路", "为赫敏强攻开路", ["强攻", "开路", "掩护", "清除", "突破"]),
        ("护送进入", "护送队友进入密室区域", ["护送", "进入", "密室区域", "掩护前进", "护卫"]),
        ("摧毁毁魂器", "与赫敏协作摧毁毁魂器", ["摧毁", "毁魂器", "协作", "成功", "完成破坏"]),
        ("回到前线", "快速回到霍格沃茨前线", ["回到前线", "归队", "冲回", "支援", "集合"]),
        ("稳定防区", "稳定关键防区并阻击敌军", ["稳定防区", "阻击", "防守", "守住", "顶住"]),
        ("总攻协同", "协同哈利发起总攻", ["总攻", "协同", "支援哈利", "推进", "配合"]),
        ("赢得战争", "协助终局击败伏地魔，赢得战争", ["赢得战争", "击败伏地魔", "战争胜利", "通关", "胜利"]),
    ],
    "Albus Dumbledore": [
        ("全域布防", "完成城堡全域布防与职责分配", ["布防", "全域", "分配", "部署", "安排"]),
        ("精神动员", "对师生进行战前精神动员", ["动员", "鼓舞", "演讲", "号召", "坚定"]),
        ("护盾启动", "启动城堡防护屏障", ["护盾", "屏障", "启动", "防护", "结界"]),
        ("战线调度", "根据敌情实时调度战线", ["调度", "战线", "调兵", "指挥", "调整"]),
        ("危机转移", "将最危险火力从学生区转移", ["转移", "危机", "火力", "疏导", "保护"]),
        ("核心指令", "下达总反攻核心指令", ["核心指令", "总反攻", "下令", "反攻", "命令"]),
        ("稳定军心", "在混战中稳定军心", ["稳定军心", "稳住", "鼓舞", "秩序", "坚持"]),
        ("决战统筹", "统筹最终决战各线协同", ["统筹", "决战", "协同", "总览", "协调"]),
        ("赢得战争", "完成终局统筹并赢得霍格沃茨保卫战", ["赢得战争", "击败伏地魔", "战争胜利", "通关", "胜利"]),
    ],
}


def _build_character_tasks(character_name: str) -> Dict[str, StoryTask]:
    chapter_titles = ROLE_CHAPTER_TITLES[character_name]
    tasks: Dict[str, StoryTask] = {}

    for chapter_no in range(1, 10):
        chapter_title = chapter_titles[chapter_no - 1]
        main_template = CHAPTER9_ROLE_MAIN[character_name] if chapter_no == 9 else MAIN_QUEST_TEMPLATE[chapter_no]
        side_template = SIDE_QUEST_TEMPLATE[chapter_no % 4 or 4]

        for quest_no, (title, desc, keywords) in enumerate(main_template, start=1):
            task_id = f"{character_name}_c{chapter_no}_m{quest_no}"
            prereq: List[str] = []
            if chapter_no == 1 and quest_no > 1:
                prereq = [f"{character_name}_c1_m{quest_no - 1}"]
            elif chapter_no > 1 and quest_no == 1:
                prereq = [f"{character_name}_c{chapter_no - 1}_m9"]
            elif chapter_no > 1 and quest_no > 1:
                prereq = [f"{character_name}_c{chapter_no}_m{quest_no - 1}"]

            tasks[task_id] = StoryTask(
                task_id=task_id,
                title=f"主线{chapter_no}-{quest_no} {title}",
                description=f"{desc}。{ROLE_FOCUS[character_name]}",
                trigger_keywords=keywords,
                completion_keywords=keywords,
                prerequisites=prereq,
                chapter=chapter_title,
                completion_feedback=f"✅ {chapter_title}：已完成主线{quest_no} - {title}",
                is_main=True,
                chapter_no=chapter_no,
                quest_no=quest_no,
            )

        chapter_gate = [] if chapter_no == 1 else [f"{character_name}_c{chapter_no - 1}_m9"]
        for side_no, (title, desc, keywords) in enumerate(side_template, start=1):
            side_id = f"{character_name}_c{chapter_no}_s{side_no}"
            tasks[side_id] = StoryTask(
                task_id=side_id,
                title=f"支线{chapter_no}-{side_no} {title}",
                description=desc,
                trigger_keywords=keywords,
                completion_keywords=keywords,
                prerequisites=chapter_gate,
                chapter=chapter_title,
                completion_feedback=f"🌟 {chapter_title}：已完成支线 - {title}",
                is_main=False,
                chapter_no=chapter_no,
                quest_no=side_no,
            )

    return tasks


CHARACTER_CAMPAIGNS = {
    name: _build_character_tasks(name) for name in ROLE_CHAPTER_TITLES
}


class StoryProgressTracker:
    """追踪故事推进进度"""

    def __init__(self, character_name: str = "Harry Potter"):
        self.character_name: str = ""
        self.tasks: Dict[str, StoryTask] = {}
        self.completed_task_ids: List[str] = []
        self.active_chapter_no: int = 1
        self.active_chapter: str = ""
        self.set_character(character_name)

    def set_character(self, character_name: str) -> None:
        if character_name not in CHARACTER_CAMPAIGNS:
            character_name = "Harry Potter"

        self.character_name = character_name
        self.tasks = deepcopy(CHARACTER_CAMPAIGNS[character_name])
        self.completed_task_ids = []
        self.active_chapter_no = 1
        self.active_chapter = ROLE_CHAPTER_TITLES[character_name][0]

    def _task_match(self, task: StoryTask, user_input: str) -> bool:
        text = user_input.strip().lower()
        if not text:
            return False

        words = task.trigger_keywords + task.completion_keywords
        return any(kw.lower() in text for kw in words)

    def _prerequisites_met(self, task: StoryTask) -> bool:
        return all(pid in self.completed_task_ids for pid in task.prerequisites)

    def _get_recommended_main_task(self) -> Optional[StoryTask]:
        for chapter_no in range(1, 10):
            for quest_no in range(1, 10):
                task_id = f"{self.character_name}_c{chapter_no}_m{quest_no}"
                task = self.tasks.get(task_id)
                if task and task.status != TaskStatus.COMPLETED:
                    if self._prerequisites_met(task):
                        return task
                    return None
        return None

    def _get_available_side_tasks(self, chapter_no: int) -> List[StoryTask]:
        result: List[StoryTask] = []
        for side_no in range(1, 5):
            task_id = f"{self.character_name}_c{chapter_no}_s{side_no}"
            task = self.tasks.get(task_id)
            if not task or task.status == TaskStatus.COMPLETED:
                continue
            if self._prerequisites_met(task):
                result.append(task)
        return result

    def _complete_task(self, task: StoryTask) -> None:
        task.status = TaskStatus.COMPLETED
        if task.task_id not in self.completed_task_ids:
            self.completed_task_ids.append(task.task_id)

    def _recompute_active_chapter(self) -> None:
        recommended = self._get_recommended_main_task()
        if recommended:
            self.active_chapter_no = recommended.chapter_no
            self.active_chapter = recommended.chapter
            return

        self.active_chapter_no = 9
        self.active_chapter = ROLE_CHAPTER_TITLES[self.character_name][8]

    def check_and_update(self, user_input: str, narrative: str) -> List[str]:
        """
        根据玩家输入检查任务完成。
        主线仅判定当前推荐任务，确保顺序推进；
        支线仅在当前章节可触发。
        """
        del narrative  # 任务推进仅依据玩家动作语义关键词
        newly_completed: List[str] = []

        recommended_main = self._get_recommended_main_task()
        if recommended_main and self._task_match(recommended_main, user_input):
            self._complete_task(recommended_main)
            newly_completed.append(recommended_main.completion_feedback)

        self._recompute_active_chapter()
        for side_task in self._get_available_side_tasks(self.active_chapter_no):
            if self._task_match(side_task, user_input):
                self._complete_task(side_task)
                newly_completed.append(side_task.completion_feedback)

        self._recompute_active_chapter()

        final_main = self.tasks.get(f"{self.character_name}_c9_m9")
        if final_main and final_main.status == TaskStatus.COMPLETED:
            ending_msg = "🏆 第9章第9主线已完成：霍格沃茨保卫战胜利，游戏通关。"
            if ending_msg not in newly_completed:
                newly_completed.append(ending_msg)

        return newly_completed

    def get_progress_summary(self) -> Dict:
        total_main = 81
        total_side = 36

        done_main = sum(1 for t in self.tasks.values() if t.is_main and t.status == TaskStatus.COMPLETED)
        done_side = sum(1 for t in self.tasks.values() if not t.is_main and t.status == TaskStatus.COMPLETED)

        recommended = self._get_recommended_main_task()
        if recommended:
            recommended_payload = {
                "task_id": recommended.task_id,
                "title": recommended.title,
                "description": recommended.description,
                "keywords": recommended.trigger_keywords[:5],
            }
            chapter_main_done = sum(
                1
                for i in range(1, 10)
                if self.tasks[f"{self.character_name}_c{recommended.chapter_no}_m{i}"].status == TaskStatus.COMPLETED
            )
        else:
            recommended_payload = None
            chapter_main_done = 9

        side_candidates = self._get_available_side_tasks(self.active_chapter_no)
        next_tasks = []
        if recommended:
            next_tasks.append(recommended.title)
        for side_task in side_candidates[:2]:
            next_tasks.append(side_task.title)

        return {
            "character": self.character_name,
            "current_chapter": self.active_chapter,
            "chapter_number": self.active_chapter_no,
            "chapter_main_progress": f"{chapter_main_done}/9",
            "main_progress": f"{done_main}/{total_main}",
            "side_progress": f"{done_side}/{total_side}",
            "completed_tasks": [self.tasks[tid].title for tid in self.completed_task_ids],
            "recommended_task": recommended_payload,
            "next_tasks": next_tasks,
            "is_game_completed": done_main >= total_main,
        }

    def get_campaign_overview(self) -> Dict:
        chapters: List[Dict] = []
        for chapter_no in range(1, 10):
            chapter_title = ROLE_CHAPTER_TITLES[self.character_name][chapter_no - 1]
            mains = []
            sides = []

            for main_no in range(1, 10):
                task = self.tasks[f"{self.character_name}_c{chapter_no}_m{main_no}"]
                mains.append(
                    {
                        "task_id": task.task_id,
                        "title": task.title,
                        "description": task.description,
                        "completion_keywords": task.completion_keywords,
                    }
                )

            for side_no in range(1, 5):
                task = self.tasks[f"{self.character_name}_c{chapter_no}_s{side_no}"]
                sides.append(
                    {
                        "task_id": task.task_id,
                        "title": task.title,
                        "description": task.description,
                        "completion_keywords": task.completion_keywords,
                    }
                )

            chapters.append(
                {
                    "chapter_number": chapter_no,
                    "chapter_title": chapter_title,
                    "main_quests": mains,
                    "side_quests": sides,
                }
            )

        return {
            "character": self.character_name,
            "chapters": chapters,
            "rules": {
                "main": "每章9个主线，必须按顺序完成",
                "side": "每章4个支线，仅可在当前章节触发",
                "finale": "第9章第9主线完成即通关",
            },
        }

    def get_hint_for_next_task(self) -> Optional[str]:
        recommended = self._get_recommended_main_task()
        if not recommended:
            return "【任务提示】全部主线任务已完成，霍格沃茨保卫战胜利。"
        return f"【任务提示】当前推荐主线：{recommended.title}；目标：{recommended.description}"


class StoryValidationPipeline:
    """故事验证管道 - 生成后对文本进行约束校验"""

    def __init__(self):
        from story_weaver.constraint_engine import ConstraintEngine

        self.constraint_engine = ConstraintEngine()

    def validate_and_refine(
        self,
        generated_text: str,
        player_character: str,
        location: str,
        current_book,
    ) -> Tuple[str, bool, list]:
        """
        验证生成文本，返回 (精炼后的文本, 是否通过, 违规列表)
        如果存在违规，在文本开头添加提醒（不强制丢弃，保留叙事流畅度）
        """
        is_valid, violations = self.constraint_engine.validate_story_segment(
            generated_text, player_character, location, current_book
        )
        if is_valid:
            return generated_text, True, []

        refined = generated_text
        return refined, False, violations

    def generate_constraint_context(
        self,
        character: str,
        location: str,
        current_book,
        completed_tasks: List[str],
    ) -> str:
        """生成注入提示词的约束上下文"""
        return self.constraint_engine.build_constraint_context(
            character=character,
            location=location,
            current_book=current_book,
            completed_tasks=completed_tasks,
        )
