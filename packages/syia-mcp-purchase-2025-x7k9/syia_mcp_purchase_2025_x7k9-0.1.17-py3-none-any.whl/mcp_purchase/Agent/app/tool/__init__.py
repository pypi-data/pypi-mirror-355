from ...app.tool.base import BaseTool
from ...app.tool.terminate import Terminate
from ...app.tool.create_chat_completion import CreateChatCompletion
from ...app.tool.tool_collection import ToolCollection


__all__ = [
    "BaseTool",
    "Terminate",
    "CreateChatCompletion",
    "ToolCollection"
]


# Add a mapping of tool names to their classes
__tool_name_map__ = {
    # Tool names mapped to their classes
    "terminate": Terminate,
    "create_chat_completion": CreateChatCompletion
}