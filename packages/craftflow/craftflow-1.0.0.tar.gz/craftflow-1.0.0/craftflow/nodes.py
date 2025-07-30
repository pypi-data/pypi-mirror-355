import asyncio
import time
import copy
from typing import Any, Dict, List, Callable, Coroutine, Optional
from .core import FlowContext, FlowNode, Workflow


class TaskNode(FlowNode):
    """任务节点（支持重试）"""

    def __init__(self,
                 task: Callable[[FlowContext, Dict], Any],
                 name: Optional[str] = None,
                 retries: int = 0,
                 delay: float = 0,
                 output_key: Optional[str] = None):  # 新增 output_key 参数
        super().__init__(name or task.__name__)
        self.task = task
        self.retries = retries
        self.delay = delay
        self.output_key = output_key  # 保存 output_key

    def process(self, ctx: FlowContext) -> Any:
        """执行任务（带重试机制）"""
        for attempt in range(self.retries + 1):
            try:
                result = self.task(ctx, self.params)
                if self.output_key:
                    ctx[self.output_key] = result  # 将结果保存到上下文
                return result
            except Exception as e:
                if attempt == self.retries:
                    raise e
                if self.delay > 0:
                    time.sleep(self.delay)


class AsyncTaskNode(FlowNode):
    """异步任务节点"""

    def __init__(self,
                 task: Callable[[FlowContext, Dict], Coroutine],
                 name: Optional[str] = None,
                 retries: int = 0,
                 delay: float = 0):
        super().__init__(name or task.__name__)
        self.task = task
        self.retries = retries
        self.delay = delay

    async def async_process(self, ctx: FlowContext) -> Any:
        """异步执行任务"""
        for attempt in range(self.retries + 1):
            try:
                return await self.task(ctx, self.params)
            except Exception as e:
                if attempt == self.retries:
                    raise e
                if self.delay > 0:
                    await asyncio.sleep(self.delay)

    def process(self, ctx: FlowContext) -> Any:
        """同步接口调用异步方法"""
        return asyncio.run(self.async_process(ctx))


class ToolNode(TaskNode):
    """工具调用节点"""

    def __init__(self,
                 tool: Callable,
                 input_map: Callable[[FlowContext], dict] = None,
                 output_key: str = None,
                 name: Optional[str] = None):
        """
        工具调用节点

        :param tool: 要调用的工具函数
        :param input_map: 从上下文映射工具参数的函数
        :param output_key: 结果保存到上下文的键名
        """
        super().__init__(self._execute_tool, name or tool.__name__)
        self.tool = tool
        self.input_map = input_map or (lambda ctx: {})
        self.output_key = output_key

    def _execute_tool(self, ctx: FlowContext, params: dict) -> Any:
        """执行工具调用并记录"""
        # 准备工具参数
        tool_params = {**self.input_map(ctx), **params}

        # 调用工具
        result = self.tool(**tool_params)

        # 记录工具调用
        ctx.log_tool(self.name, tool_params, result)

        # 保存结果到上下文
        if self.output_key:
            ctx[self.output_key] = result

        return result


class AsyncToolNode(AsyncTaskNode):
    """异步工具调用节点"""

    def __init__(self,
                 tool: Callable,
                 input_map: Callable[[FlowContext], dict] = None,
                 output_key: str = None,
                 name: Optional[str] = None):
        """
        异步工具调用节点

        :param tool: 要调用的异步工具函数
        :param input_map: 从上下文映射工具参数的函数
        :param output_key: 结果保存到上下文的键名
        """
        super().__init__(self._execute_tool_async, name or tool.__name__)
        self.tool = tool
        self.input_map = input_map or (lambda ctx: {})
        self.output_key = output_key

    async def _execute_tool_async(self, ctx: FlowContext, params: dict) -> Any:
        """执行异步工具调用并记录"""
        # 准备工具参数
        tool_params = {**self.input_map(ctx), **params}

        # 调用工具
        result = await self.tool(**tool_params)

        # 记录工具调用
        ctx.log_tool(self.name, tool_params, result)

        # 保存结果到上下文
        if self.output_key:
            ctx[self.output_key] = result

        return result


class MCPNode(FlowNode):
    """多条件路径节点 (Multi-Conditional Path)"""

    def __init__(self,
                 conditions: List[Callable[[FlowContext, Dict], str]],
                 default_action: str = "default",
                 name: str = "MCP"):
        """
        多条件路径节点

        :param conditions: 条件函数列表，返回动作名
        :param default_action: 默认动作名
        """
        super().__init__(name)
        self.conditions = conditions
        self.default_action = default_action

    def process(self, ctx: FlowContext) -> str:
        """评估所有条件，返回第一个匹配的动作名"""
        for condition in self.conditions:
            action = condition(ctx, self.params)
            if action and action in self.next_nodes:
                return action
        return self.default_action


class AgentNode(FlowNode):
    """Agent节点（封装完整工作流）"""

    def __init__(self,
                 agent_workflow: Workflow,
                 input_map: Callable[[FlowContext], dict] = None,
                 output_key: str = None,
                 name: Optional[str] = None):
        """
        Agent节点

        :param agent_workflow: Agent内部工作流
        :param input_map: 输入映射函数
        :param output_key: 结果保存键名
        """
        super().__init__(name or agent_workflow.name)
        self.agent_workflow = agent_workflow
        self.input_map = input_map or (lambda ctx: {})
        self.output_key = output_key

    def process(self, ctx: FlowContext) -> Any:
        """执行Agent工作流"""
        # 创建Agent上下文
        agent_ctx = FlowContext(self.input_map(ctx))

        # 执行Agent工作流
        result = self.agent_workflow.run(agent_ctx)

        # 保存结果
        if self.output_key:
            ctx[self.output_key] = result

        # 合并上下文数据
        ctx.update(agent_ctx)

        return result


# class ParallelNode(FlowNode):
#     """并行处理节点"""
#
#     def __init__(self,
#                  nodes: List[FlowNode],
#                  name: str = "Parallel"):
#         super().__init__(name)
#         self.nodes = nodes
#
#     def process(self, ctx: FlowContext) -> List[Any]:
#         """并行执行所有子节点"""
#         return [node.run(ctx) for node in self.nodes]

class ParallelNode(FlowNode):
    def __init__(self,
                 nodes: List[FlowNode],
                 name: str = "Parallel",
                 action_on_complete: str = "next"):
        super().__init__(name)
        self.nodes = nodes
        self.action_on_complete = action_on_complete

    def process(self, ctx: FlowContext) -> str:
        results = [node.run(ctx) for node in self.nodes]
        ctx[self.name + "_results"] = results  # 可选：记录结果
        return self.action_on_complete


class BatchNode(FlowNode):
    """批处理节点"""

    def __init__(self,
                 node: FlowNode,
                 input_field: str = "batch",
                 output_field: str = "results",
                 name: str = "BatchProcessor"):
        super().__init__(name)
        self.node = node
        self.input_field = input_field
        self.output_field = output_field

    def process(self, ctx: FlowContext) -> List[Any]:
        """处理批量数据"""
        batch_data = ctx.get(self.input_field, [])
        results = []

        for item in batch_data:
            # 为每个项目创建新上下文
            item_ctx = FlowContext(copy.deepcopy(ctx))
            item_ctx["item"] = item

            # 执行处理节点
            self.node.run(item_ctx)
            results.append(item_ctx)

        # 保存结果
        ctx[self.output_field] = results
        return results


