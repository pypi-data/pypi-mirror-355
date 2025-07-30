import asyncio
from craftflow.core import FlowContext, FlowBuilder
from craftflow.nodes import TaskNode, ToolNode, AsyncToolNode, MCPNode


def simple_tool(x: int) -> int:
    print(f"Running tool with x={x}")
    return x * 2


async def async_tool(x: int) -> int:
    print(f"Running async tool with x={x}")
    await asyncio.sleep(0.1)
    return x * 3


def map_input(ctx):
    return {"x": ctx["input_value"]}


# 构建工作流
builder = FlowBuilder()

# 定义节点
input_node = TaskNode(lambda ctx, _: ctx.set(input_value=5) or "next", name="Input")
tool_node = ToolNode(simple_tool, input_map=map_input, output_key="result", name="ToolA")
async_tool_node = AsyncToolNode(async_tool, input_map=map_input, output_key="async_result", name="ToolB")

# 条件判断
condition_node = MCPNode([
    lambda ctx, _: "high" if ctx["result"] > 8 else "low"
], default_action="low", name="Decision")

# 不同分支
high_node = TaskNode(lambda ctx, _: print("High branch"), name="HighBranch")
low_node = TaskNode(lambda ctx, _: print("Low branch"), name="LowBranch")

# 连接节点
builder \
    .add_node(input_node) \
    .add_node(tool_node) \
    .add_node(async_tool_node) \
    .add_node(condition_node) \
    .add_node(high_node) \
    .add_node(low_node) \
    .start(input_node)

# 设置连接关系
input_node >> tool_node >> async_tool_node >> condition_node
condition_node.connect(high_node, "high").connect(low_node, "low")

# 构建并运行工作流
workflow = builder.build()
context = FlowContext()
workflow.run(context)

# 查看结果
print("\nFinal Context:")
for k, v in context.items():
    print(f"{k}: {v}")

print("\nExecution Trace:")
for step in context.get_trace():
    print(f"{step['step']}. {step['node']} => {step['result']}")