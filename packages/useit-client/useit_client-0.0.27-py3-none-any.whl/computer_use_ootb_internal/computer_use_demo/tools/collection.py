"""Collection classes for managing multiple tools."""

from typing import Any

from anthropic.types.beta import BetaToolUnionParam

from .base import (
    BaseAnthropicTool,
    ToolError,
    ToolFailure,
    ToolResult,
)


class ToolCollection:
    """A collection of anthropic-defined tools."""

    def __init__(self, *tools: BaseAnthropicTool):
        self._tools_by_name = {tool.name: tool for tool in tools}

    def to_params(
        self,
    ) -> list[BetaToolUnionParam]:
        return [tool.to_params() for tool in self._tools_by_name.values()]

    def run(self, name: str, tool_input: dict[str, Any]) -> ToolResult | ToolError:
        tool = self._tools_by_name.get(name)
        if not tool:
            return ToolError(output=f"Unknown tool: {name}", action_base_type="error")

        try:
            return tool(**tool_input)
        except ToolError as e:
            return e
        except Exception as e:
            return ToolError(
                output=f"Tool {name} failed with exception: {e}",
                action_base_type="error",
            )
