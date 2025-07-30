from typing import Dict, List, Callable
from .core import FlowNode


class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self.tools = {}

    def register(self, name: str = None, tool: Callable = None, is_async: bool = False, description: str = None):
        """注册工具（支持装饰器和直接调用两种方式）"""

        def decorator(tool_func: Callable):
            nonlocal name, description
            name = name or tool_func.__name__
            description = description or tool_func.__doc__ or "无描述"

            self.tools[name] = {
                'function': tool_func,
                'async': is_async,
                'description': description
            }
            return tool_func

        if tool is not None:  # 直接调用方式
            return decorator(tool)
        else:  # 装饰器方式
            return decorator

    def get(self, name: str) -> dict:
        """获取工具信息"""
        return self.tools.get(name)

    def create_node(self, tool_name: str, input_map: Callable = None, output_key: str = None) -> FlowNode:
        """创建工具节点"""
        from .nodes import ToolNode, AsyncToolNode

        tool_info = self.get(tool_name)
        if not tool_info:
            raise ValueError(f"工具 '{tool_name}' 未注册")

        if tool_info['async']:
            return AsyncToolNode(
                tool_info['function'],
                input_map=input_map,
                output_key=output_key,
                name=tool_name
            )
        else:
            return ToolNode(
                tool_info['function'],
                input_map=input_map,
                output_key=output_key,
                name=tool_name
            )

    def list_tools(self) -> List[Dict]:
        """获取所有工具列表"""
        return [{
            'name': name,
            'description': info['description'],
            'async': info['async']
        } for name, info in self.tools.items()]
