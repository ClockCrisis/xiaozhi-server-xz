from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()


# ==================== 量表题目 ====================

SDS_QUESTIONS = [
    "1. 情绪低落，沮丧或绝望（评分：1=几乎没有，2=偶尔，3=经常，4=持续）",
    "2. 对事物缺乏兴趣或乐趣（评分：1=几乎没有，2=偶尔，3=经常，4=持续）",
    "3. 入睡困难、睡不安稳或睡眠过多（评分：1=几乎没有，2=偶尔，3=经常，4=持续）",
    "4. 感到疲倦或没有活力（评分：1=几乎没有，2=偶尔，3=经常，4=持续）",
    "5. 食欲不振或吃得太多（评分：1=几乎没有，2=偶尔，3=经常，4=持续）",
    "6. 自我评价过低或过度自责（评分：1=几乎没有，2=偶尔，3=经常，4=持续）",
    "7. 注意力难以集中或决策困难（评分：1=几乎没有，2=偶尔，3=经常，4=持续）",
    "8. 动作缓慢或说话速度缓慢（评分：1=几乎没有，2=偶尔，3=经常，4=持续）",
    "9. 有不如死掉或用某种方式伤害自己的念头（评分：1=几乎没有，2=偶尔，3=经常，4=持续）",
]


# ==================== 存储量表状态 ====================

# key: conn_id, value: {"index": int, "answers": list}
_scale_states: Dict[int, Dict] = {}


# ==================== Function 描述 ====================

psychology_scale_function_desc = {
    "type": "function",
    "function": {
        "name": "psychology_scale_evaluation",
        "description": "当用户需要进行心理学量表评测时调用。当前支持SDS抑郁自评量表。",
        "parameters": {
            "type": "object",
            "properties": {
                "scale_name": {"type": "string", "description": "量表名称，如：SDS"},
                "user_response": {"type": "string", "description": "用户对当前问题的回答（1-4分）"}
            },
            "required": ["scale_name"]
        },
    },
}


# ==================== 量表评测函数 ====================

@register_function("psychology_scale_evaluation", psychology_scale_function_desc, ToolType.CHANGE_SYS_PROMPT)
def psychology_scale_evaluation(conn: "ConnectionHandler", scale_name: str, user_response: str = None):
    """
    心理学量表评测 - 最小可行版

    多轮询问流程：
    1. 第一次调用：scale_name="SDS", user_response=None → 返回第1题
    2. 后续调用：scale_name="SDS", user_response="2" → 返回第2题
    3. 第9题回答后：返回评测结果
    """
    scale_name = scale_name.upper()
    if scale_name != "SDS":
        return ActionResponse(
            action=Action.RESPONSE,
            result="不支持的量表",
            response="当前仅支持SDS量表"
        )

    conn_id = id(conn)

    # ========== 第一次调用：初始化 ==========
    if conn_id not in _scale_states:
        _scale_states[conn_id] = {"index": 0, "answers": []}
        logger.bind(tag=TAG).info(f"开始SDS量表评测，连接ID: {conn_id}")
        return ActionResponse(
            action=Action.RESPONSE,
            result="开始量表",
            response=f"欢迎进行SDS抑郁自评量表，共{len(SDS_QUESTIONS)}道题。\n请根据您最近一周的实际感受作答。\n\n{SDS_QUESTIONS[0]}"
        )

    # ========== 后续调用：记录回答并返回下一题 ==========
    state = _scale_states[conn_id]

    # 记录用户回答
    if user_response:
        state["answers"].append(user_response)

    # 返回下一题
    state["index"] += 1
    if state["index"] < len(SDS_QUESTIONS):
        return ActionResponse(
            action=Action.RESPONSE,
            result="下一题",
            response=f"已记录。\n{SDS_QUESTIONS[state['index']]}"
        )

    # ========== 评测完成：计算并返回结果 ==========
    answers = state["answers"]
    total = sum(int(a) for a in answers if str(a).isdigit())
    avg = total / len(answers) if answers else 0

    # 清除状态
    del _scale_states[conn_id]

    # 计算评估建议
    if avg <= 1.5:
        suggestion = "无抑郁症状，继续保持"
    elif avg <= 2.5:
        suggestion = "轻度抑郁，建议适当关注心理健康"
    elif avg <= 3.5:
        suggestion = "中度抑郁，建议咨询心理医生"
    else:
        suggestion = "重度抑郁，建议立即寻求专业帮助"

    result = f"SDS量表评测完成！\n总得分：{total}分\n评估：{suggestion}\n感谢您的作答！"
    logger.bind(tag=TAG).info(f"SDS量表完成，总得分：{total}")

    return ActionResponse(action=Action.RESPONSE, result="量表完成", response=result)