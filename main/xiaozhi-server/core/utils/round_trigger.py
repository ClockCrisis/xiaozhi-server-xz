"""轮次触发器 - 每隔N轮对话自动调用MCP工具"""

from typing import Optional, Dict, Any
from config.logger import setup_logging


TAG = __name__


class RoundTrigger:
    """每隔N轮对话触发MCP工具调用"""

    def __init__(self, config: Dict[str, Any], func_handler):
        """
        Args:
            config: auto_mcp_trigger 配置项
            func_handler: UnifiedToolHandler 实例
        """
        self.enabled = config.get("enabled", False)
        self.interval = config.get("interval", 5)  # 每隔几轮触发
        self.tool_name = config.get("tool_name", "")
        self.tool_args = config.get("tool_args", {})
        self.current_round = 0
        self.func_handler = func_handler
        self.logger = setup_logging()

        if self.enabled:
            self.logger.bind(tag=TAG).info(
                f"轮次触发器已启用: 每 {self.interval} 轮调用 MCP 工具 '{self.tool_name}'"
            )

    def on_ai_response(self) -> bool:
        """
        每次AI回复后调用，增加计数并检查是否达到触发条件
        Returns:
            True if trigger condition is met
        """
        if not self.enabled:
            return False

        self.current_round += 1
        should_trigger = self.current_round % self.interval == 0

        if should_trigger:
            self.logger.bind(tag=TAG).info(
                f"轮次触发: 当前第 {self.current_round} 轮，达到间隔 {self.interval}，将调用 MCP 工具 '{self.tool_name}'"
            )

        return should_trigger

    async def trigger(self):
        """执行MCP工具调用"""
        if not self.enabled or not self.tool_name:
            return

        try:
            if not self.func_handler.has_tool(self.tool_name):
                self.logger.bind(tag=TAG).warning(
                    f"工具 '{self.tool_name}' 不存在，跳过触发"
                )
                return

            self.logger.bind(tag=TAG).info(
                f"执行轮次触发: 调用工具 '{self.tool_name}'，参数: {self.tool_args}"
            )

            # 通过 func_handler 执行工具调用
            result = await self.func_handler.tool_manager.execute_tool(
                self.tool_name, self.tool_args
            )

            self.logger.bind(tag=TAG).info(
                f"轮次触发完成: 工具 '{self.tool_name}' 返回结果: {result}"
            )

        except Exception as e:
            self.logger.bind(tag=TAG).error(
                f"轮次触发执行失败: {e}"
            )

    def reset(self):
        """重置计数器"""
        self.current_round = 0