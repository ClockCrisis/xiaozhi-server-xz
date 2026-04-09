from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

# 完整问卷prompt（包含所有题目和指导语）
prompts = {
    "SDS": """
[量表评测模式: SDS抑郁自评量表]

你是一个专业的心理评测助手。现在请协助用户完成SDS抑郁自评量表。

量表说明：
- 共9道题目
- 评分标准：几乎没有(1分)，偶尔(2分)，经常(3分)，持续(4分)
- 请根据用户最近一周的实际感受进行评估

题目：
1. 情绪低落，沮丧或绝望
2. 对事物缺乏兴趣或乐趣
3. 睡眠障碍（入睡困难、睡眠浅或多梦）
4. 疲劳感或缺乏精力
5. 食欲障碍（食欲减退或暴饮暴食）
6. 自我评价过低或过度自责
7. 注意力难以集中或决策困难
8. 动作缓慢或语言减少
9. 存在消极想法或自杀念头

请逐题询问用户，根据用户回答如实记录。评分标准：几乎没有=1分，偶尔=2分，经常=3分，持续=4分。
所有题目完成后，给出总得分和评估建议。
""",
    "SAS": """
[量表评测模式: SAS焦虑自评量表]

你是一个专业的心理评测助手。现在请协助用户完成SAS焦虑自评量表。

量表说明：
- 共10道题目
- 评分标准：几乎没有(1分)，偶尔(2分)，经常(3分)，持续(4分)
- 请根据用户最近一周的实际感受进行评估

题目：
1. 感到紧张或着急
2. 无缘无故感到害怕
3. 容易心烦或易怒
4. 感到即将崩溃
5. 手脚发抖打颤
6. 头痛、头胀
7. 容易感到身体不适
8. 呼吸困难
9. 手脚麻木刺痛
10. 胃痛或消化不良

请逐题询问用户，根据用户回答如实记录。评分标准：几乎没有=1分，偶尔=2分，经常=3分，持续=4分。
所有题目完成后，给出总得分和评估建议。
""",
    "PHQ9": """
[量表评测模式: PHQ9抑郁症筛查量表]

你是一个专业的心理评测助手。现在请协助用户完成PHQ9抑郁症筛查量表。

量表说明：
- 共9道题目
- 评分标准：完全不会(0分)，好几天(1分)，一半以上天数(2分)，几乎每天(3分)
- 请根据用户最近两周的实际感受进行评估

题目：
1. 做事时提不起劲或没有兴趣
2. 感到心情低落、沮丧或绝望
3. 入睡困难、睡不安稳或睡眠过多
4. 感到疲倦或没有活力
5. 食欲不振或吃得太多
6. 觉得自己很糟或认为自己很失败，或让自己或家人失望
7. 对事物专注有困难，例如看报纸或看电视时
8. 动作或说话速度缓慢，以至于别人都注意到了；或正好相反，坐立不安、动来动去比平常更明显
9. 有不如死掉或用某种方式伤害自己的念头

评分标准：完全不会=0分，好几天=1分，一半以上天数=2分，几乎每天=3分

总分评估：
- 0-4分：无抑郁症状
- 5-9分：轻度抑郁，建议关注
- 10-14分：中度抑郁，建议咨询
- 15-19分：中重度抑郁，建议专业治疗
- 20-27分：重度抑郁，建议立即寻求专业帮助

请逐题询问用户，根据用户回答如实记录。
所有题目完成后，给出总得分和严重程度评估。
""",
}

psychology_prompt_function_desc = {
    "type": "function",
    "function": {
        "name": "psychology_prompt_evaluation",
        "description": "当用户需要进行心理学量表评测时调用，支持的量表有：[SDS抑郁自评量表, SAS焦虑自评量表, PHQ9抑郁症筛查量表]。请直接开始量表评测。",
        "parameters": {
            "type": "object",
            "properties": {
                "scale_name": {"type": "string", "description": "量表名称，如：SDS, SAS, PHQ9"}
            },
            "required": ["scale_name"]
        },
    },
}


@register_function("psychology_prompt_evaluation", psychology_prompt_function_desc, ToolType.CHANGE_SYS_PROMPT)
def psychology_prompt_evaluation(conn: "ConnectionHandler", scale_name: str):
    """心理学量表评测（简化版：直接注入prompt）"""
    scale_name_upper = scale_name.upper()
    if scale_name_upper not in prompts:
        available = ", ".join(prompts.keys())
        return ActionResponse(
            action=Action.RESPONSE,
            result="量表不存在",
            response=f"不支持的量表，可用量表：{available}"
        )

    # 保存原始prompt并切换到量表模式
    conn._evaluation_original_prompt = conn.prompt
    new_prompt = conn.prompt + prompts[scale_name_upper]
    conn.change_system_prompt(new_prompt)

    logger.bind(tag=TAG).info(f"开始量表评测: {scale_name}")
    scale_intro = f"好的，现在开始进行{scale_name_upper}量表评测，请根据您的实际情况回答以下问题。"
    return ActionResponse(action=Action.RESPONSE, result="开始量表", response=scale_intro)