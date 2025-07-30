import asyncio
import time
from craftflow.core import FlowContext, FlowBuilder, Workflow
from craftflow.nodes import TaskNode, AsyncToolNode, AsyncTaskNode, AgentNode


# 定义异步工具函数
async def async_multiplier(x: int) -> int:
    """异步工具：乘法器"""
    print(f"[AsyncTool] Multiplying {x} by 3...")
    await asyncio.sleep(0.5)  # 模拟异步操作
    return x * 3


# 定义异步任务函数
async def async_adder(ctx: FlowContext, params: dict) -> int:
    """异步任务：加法器"""
    # 从上下文获取值（注意：主工作流和Agent工作流使用的键不同）
    value = ctx.get("value", ctx.get("squared", 0))
    increment = params.get("increment", 1)  # 从节点参数获取增量值
    print(f"[AsyncTask] Adding {increment} to {value}...")
    await asyncio.sleep(0.3)  # 模拟异步操作
    result = value + increment
    # 将结果保存到上下文，键名根据工作流不同而变化
    if "value" in ctx:
        ctx["added"] = result  # 主工作流
    else:
        ctx["agent_output"] = result  # Agent工作流
    return result


# 定义Agent内部工作流的工具函数
async def async_square(x: int) -> int:
    """异步工具：平方计算"""
    print(f"[AgentTool] Squaring {x}...")
    await asyncio.sleep(0.4)
    return x ** 2


# 创建Agent内部工作流
def build_agent_workflow() -> Workflow:
    """构建Agent内部工作流"""
    builder = FlowBuilder()

    # 定义Agent内部节点
    input_mapper = TaskNode(
        lambda ctx, _: ctx.set(input_value=ctx["agent_input"]),
        name="AgentInputMapper"
    )

    tool_node = AsyncToolNode(
        async_square,
        input_map=lambda ctx: {"x": ctx["input_value"]},
        output_key="squared",  # 将结果保存到上下文的"squared"键
        name="AgentSquareTool"
    )

    # 创建AsyncTaskNode并设置参数
    task_node = AsyncTaskNode(
        async_adder,
        name="AgentAdderTask"
    )
    task_node.set_params(increment=5)  # 使用set_params方法设置参数

    # 连接节点
    input_mapper >> tool_node >> task_node

    # 构建工作流
    builder.add_node(input_mapper).add_node(tool_node).add_node(task_node)
    builder.start(input_mapper)
    return builder.build(name="SquareAndAddAgent")


# 主工作流构建
def main_workflow():
    # 创建构建器
    builder = FlowBuilder()

    # 创建Agent内部工作流
    agent_workflow = build_agent_workflow()

    # 定义主工作流节点
    input_node = TaskNode(
        lambda ctx, _: ctx.set(value=4) or "next",
        name="MainInput"
    )

    async_tool_node = AsyncToolNode(
        async_multiplier,
        input_map=lambda ctx: {"x": ctx["value"]},
        output_key="multiplied",  # 将结果保存到上下文的"multiplied"键
        name="MainMultiplier"
    )

    # 创建AsyncTaskNode并设置参数
    async_task_node = AsyncTaskNode(
        async_adder,
        name="MainAdder"
    )
    async_task_node.set_params(increment=10)  # 使用set_params方法设置参数

    agent_node = AgentNode(
        agent_workflow,
        input_map=lambda ctx: {"agent_input": ctx["added"]},  # 使用"added"键的值作为Agent输入
        output_key="agent_result",
        name="SquareAgent"
    )

    result_node = TaskNode(
        lambda ctx, _: print(f"\nFinal Result: {ctx['agent_result']}"),
        name="ResultPrinter"
    )

    # 添加节点到构建器
    builder.add_node(input_node)
    builder.add_node(async_tool_node)
    builder.add_node(async_task_node)
    builder.add_node(agent_node)
    builder.add_node(result_node)

    # 连接节点
    input_node >> async_tool_node >> async_task_node >> agent_node >> result_node

    # 设置起始节点并构建工作流
    builder.start(input_node)
    workflow = builder.build(name="MainWorkflow")

    # 创建上下文并运行工作流
    context = FlowContext()
    workflow.run(context)

    # 打印执行跟踪
    print("\nExecution Trace:")
    for step in context.get_trace():
        print(f"{step['step']}. {step['node']} => {step['result']}")

    # 打印工具调用日志
    print("\nTool Calls:")
    for call in context.get_tool_logs():
        print(f"- {call['tool']}: params={call['params']}, result={call['result']}")


if __name__ == "__main__":
    start_time = time.time()
    print("Starting workflow execution...")
    main_workflow()
    print(f"\nTotal execution time: {time.time() - start_time:.2f} seconds")