"""轮次触发器 - 每隔N轮对话自动调用MCP工具"""

from typing import List, Dict, Any
from config.logger import setup_logging


TAG = __name__


class RoundTrigger:
    """单个触发器配置"""

    def __init__(self, config: Dict[str, Any], func_handler, logger, default_enabled=False):
        self.enabled = config.get("enabled", default_enabled)  # 支持默认启用
        self.interval = config.get("interval", 5)  # 每隔几轮触发
        self.tool_name = config.get("tool_name", "")
        self.tool_args = config.get("tool_args", {})
        self.current_round = 0
        self.func_handler = func_handler
        self.logger = logger

        if self.enabled:
            self.logger.bind(tag=TAG).info(
                f"  触发器: 每 {self.interval} 轮调用 '{self.tool_name}'"
            )

    def should_trigger(self) -> bool:
        """检查是否达到触发条件"""
        if not self.enabled or self.interval <= 0:
            return False
        self.current_round += 1
        return self.current_round % self.interval == 0


class RoundTriggerManager:
    """轮次触发管理器 - 支持多个独立间隔的触发器"""

    def __init__(self, config: Dict[str, Any], func_handler):
        """
        Args:
            config: auto_mcp_triggers 配置项（列表格式）
            func_handler: UnifiedToolHandler 实例
        """
        self.triggers: List[RoundTrigger] = []
        self.func_handler = func_handler
        self.logger = setup_logging()

        # 支持两种配置格式：
        # 1. 列表格式: [{"enabled": true, "interval": 3, "tool_name": "A"}, ...]
        # 2. 旧格式（单个）: {"enabled": true, "interval": 5, "tool_name": "xxx"}

        if isinstance(config, list):
            # 新格式：多个触发器，列表中每个触发器默认启用
            for trigger_config in config:
                trigger = RoundTrigger(trigger_config, func_handler, self.logger, default_enabled=True)
                self.triggers.append(trigger)
        elif isinstance(config, dict):
            triggers_list = config.get("triggers", [])
            if triggers_list and isinstance(triggers_list, list):
                # 新格式：dict with triggers list
                for trigger_config in triggers_list:
                    trigger = RoundTrigger(trigger_config, func_handler, self.logger, default_enabled=True)
                    self.triggers.append(trigger)
            elif config.get("enabled", False):
                # 旧格式：单个触发器（向后兼容）
                trigger = RoundTrigger(config, func_handler, self.logger)
                self.triggers.append(trigger)

        if self.triggers:
            self.logger.bind(tag=TAG).info(
                f"轮次触发管理器已启用，共 {len(self.triggers)} 个触发器"
            )

    def on_ai_response(self) -> List[RoundTrigger]:
        """
        每次AI回复后调用，增加所有触发器计数并返回达到条件的触发器
        Returns:
            需要触发的触发器列表
        """
        triggered = []
        for trigger in self.triggers:
            if trigger.should_trigger():
                triggered.append(trigger)
                self.logger.bind(tag=TAG).info(
                    f"轮次触发: 第 {trigger.current_round} 轮，调用 '{trigger.tool_name}'"
                )
        return triggered

    async def trigger_all(self):
        """执行所有达到条件的触发器"""
        triggered_triggers = self.on_ai_response()
        for trigger in triggered_triggers:
            await self._execute_trigger(trigger)

    async def _execute_trigger(self, trigger: RoundTrigger):
        """执行单个触发器"""
        try:
            if not self.func_handler.has_tool(trigger.tool_name):
                self.logger.bind(tag=TAG).warning(
                    f"工具 '{trigger.tool_name}' 不存在，跳过"
                )
                return

            self.logger.bind(tag=TAG).info(
                f"执行触发: 调用工具 '{trigger.tool_name}'，参数: {trigger.tool_args}"
            )

            result = await self.func_handler.tool_manager.execute_tool(
                trigger.tool_name, trigger.tool_args
            )

            self.logger.bind(tag=TAG).info(
                f"触发完成: '{trigger.tool_name}' 返回: {result}"
            )

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"触发执行失败: {e}")

    def reset_all(self):
        """重置所有触发器计数"""
        for trigger in self.triggers:
            trigger.current_round = 0