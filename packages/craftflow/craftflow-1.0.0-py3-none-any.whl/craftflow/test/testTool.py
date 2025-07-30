import asyncio
import time
from craftflow.core import FlowContext, FlowBuilder, Workflow
from craftflow.nodes import TaskNode, MCPNode, AgentNode, BatchNode
from typing import Callable


# 修复后的 ToolRegistry 类
class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self.tools = {}

    def register(self, name: str = None, is_async: bool = False, description: str = None):
        """注册工具的装饰器"""

        def decorator(tool: Callable):
            nonlocal name, description
            name = name or tool.__name__
            description = description or tool.__doc__ or "无描述"

            self.tools[name] = {
                'function': tool,
                'async': is_async,
                'description': description
            }
            return tool

        return decorator

    def get(self, name: str) -> dict:
        """获取工具信息"""
        return self.tools.get(name)

    def create_node(self, tool_name: str, input_map: Callable = None, output_key: str = None) -> 'FlowNode':
        """创建工具节点"""
        from craftflow.nodes import ToolNode, AsyncToolNode

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

    def list_tools(self) -> list:
        """获取所有工具列表"""
        return [{
            'name': name,
            'description': info['description'],
            'async': info['async']
        } for name, info in self.tools.items()]


# 创建工具注册中心
tool_registry = ToolRegistry()


# 注册同步工具（使用装饰器语法）
@tool_registry.register(name="multiplier", description="数字乘法器")
def multiplier(x: int, factor: int = 2) -> int:
    """将输入数字乘以指定因子"""
    print(f"[工具] 将 {x} 乘以 {factor}")
    time.sleep(0.2)  # 模拟耗时操作
    return x * factor


# 注册异步工具（使用装饰器语法）
@tool_registry.register(name="async_square", is_async=True, description="异步平方计算")
async def async_square(x: int) -> int:
    """计算数字的平方"""
    print(f"[异步工具] 计算 {x} 的平方")
    await asyncio.sleep(0.3)  # 模拟异步操作
    return x ** 2


# 注册另一个工具（使用装饰器语法）
@tool_registry.register(name="increment", description="数字增量器")
def increment(x: int, step: int = 1) -> int:
    """增加数字的值"""
    print(f"[工具] 将 {x} 增加 {step}")
    return x + step


# 创建Agent内部工作流
def build_agent_workflow() -> Workflow:
    """构建Agent内部工作流：计算平方并增加5"""
    builder = FlowBuilder()

    # 创建工具节点
    square_node = tool_registry.create_node(
        "async_square",
        input_map=lambda ctx: {"x": ctx["agent_input"]},
        output_key="squared",
    )

    increment_node = tool_registry.create_node(
        "increment",
        input_map=lambda ctx: {"x": ctx["squared"]},
        output_key="agent_output",  # 修改输出键名
    )
    increment_node.set_params(step=5)  # 设置增量参数

    # 结果节点 - 确保返回数值而不是字符串
    result_node = TaskNode(
        lambda ctx, _: ctx.get("agent_output"),
        name="AgentResult"
    )

    # 连接节点
    square_node >> increment_node >> result_node

    # 构建工作流
    builder.add_node(square_node).add_node(increment_node).add_node(result_node)
    builder.start(square_node)
    return builder.build(name="SquareAndIncrementAgent")


# 主工作流构建
def main_workflow():
    # 创建构建器
    builder = FlowBuilder()

    # 创建Agent内部工作流
    agent_workflow = build_agent_workflow()

    # 定义主工作流节点
    input_node = TaskNode(
        lambda ctx, _: ctx.set(value=4) or "next",
        name="输入节点"
    )

    # 使用工具注册中心创建工具节点
    multiplier_node = tool_registry.create_node(
        "multiplier",
        input_map=lambda ctx: {"x": ctx["value"]},
        output_key="multiplied",
    )
    multiplier_node.set_params(factor=3)  # 设置乘法因子

    # 创建Agent节点
    agent_node = AgentNode(
        agent_workflow,
        input_map=lambda ctx: {"agent_input": ctx["multiplied"]},
        output_key="agent_result",
        name="平方计算Agent"
    )

    # 条件分支节点 - 添加类型检查
    condition_node = MCPNode([
        lambda ctx, _: "high" if isinstance(ctx.get("agent_result"), (int, float)) and ctx[
            "agent_result"] > 50 else "low",
        lambda ctx, _: "even" if isinstance(ctx.get("agent_result"), (int, float)) and ctx[
            "agent_result"] % 2 == 0 else "odd"
    ], default_action="default", name="条件分支")

    # 分支处理节点
    high_node = TaskNode(
        lambda ctx, _: print("结果大于50"),
        name="高值分支"
    )

    low_node = TaskNode(
        lambda ctx, _: print("结果小于等于50"),
        name="低值分支"
    )

    even_node = TaskNode(
        lambda ctx, _: print("结果是偶数"),
        name="偶数分支"
    )

    odd_node = TaskNode(
        lambda ctx, _: print("结果是奇数"),
        name="奇数分支"
    )

    # 批处理节点
    batch_node = BatchNode(
        agent_node,  # 使用Agent节点作为批处理器
        input_field="batch_data",
        output_field="batch_results",
        name="批处理"
    )

    result_node = TaskNode(
        lambda ctx, _: print(f"\n最终结果: {ctx['agent_result']}"),
        name="结果输出"
    )

    # 添加节点到构建器
    builder.add_node(input_node)
    builder.add_node(multiplier_node)
    builder.add_node(agent_node)
    builder.add_node(condition_node)
    builder.add_node(high_node)
    builder.add_node(low_node)
    builder.add_node(even_node)
    builder.add_node(odd_node)
    builder.add_node(batch_node)
    builder.add_node(result_node)

    # 连接节点
    input_node >> multiplier_node >> agent_node >> condition_node
    condition_node.connect(high_node, "high")
    condition_node.connect(low_node, "low")
    condition_node.connect(even_node, "even")
    condition_node.connect(odd_node, "odd")
    condition_node >> result_node

    # 设置起始节点并构建工作流
    builder.start(input_node)
    workflow = builder.build(name="主工作流")

    return workflow


def run_workflow():
    # 创建上下文
    context = FlowContext()

    # 添加批处理数据 - 暂时注释掉以简化调试
    # context["batch_data"] = [10, 20, 30]

    # 创建并运行工作流
    workflow = main_workflow()
    workflow.run(context)

    # 打印执行跟踪
    print("\n执行路径:")
    for step in context.get_trace():
        print(f"{step['step']}. {step['node']} => {step['result']}")

    # 打印工具调用日志
    print("\n工具调用记录:")
    for call in context.get_tool_logs():
        print(f"- {call['tool']}: 参数={call['params']}, 结果={call['result']}")

    # 打印批处理结果 - 暂时注释掉
    # print("\n批处理结果:")
    # for i, result in enumerate(context["batch_results"]):
    #     print(f"项目 {i + 1}: 结果={result['agent_result']}")


if __name__ == "__main__":
    start_time = time.time()
    print("开始执行工作流...")
    run_workflow()
    print(f"\n总执行时间: {time.time() - start_time:.2f} 秒")

    # 打印所有注册的工具
    print("\n注册的工具列表:")
    for tool in tool_registry.list_tools():
        print(f"- {tool['name']}: {tool['description']} (异步: {'是' if tool['async'] else '否'})")