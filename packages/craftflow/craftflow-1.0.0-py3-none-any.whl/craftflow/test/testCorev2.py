from typing import Any
from craftflow.core import FlowContext, FlowNode, Workflow, FlowBuilder


class StartNode(FlowNode):
    def process(self, ctx: FlowContext) -> Any:
        print("StartNode processing")
        ctx["status"] = "started"
        return "next"


class MiddleNode(FlowNode):
    def process(self, ctx: FlowContext) -> Any:
        print("MiddleNode processing")
        ctx["status"] = "in_progress"
        return "next"


class EndNode(FlowNode):
    def process(self, ctx: FlowContext) -> Any:
        print("EndNode processing")
        ctx["status"] = "finished"
        return "end"


# 创建节点实例
start = StartNode()
middle = MiddleNode()
end = EndNode()

# 创建构建器
builder = FlowBuilder()


# 使用 [] 操作符添加节点
builder["start"] = start     # 调用 __setitem__
builder["middle"] = middle   # 自动设置节点名
builder["end"] = end

# 设置起始节点
builder.start(start)

# 连接节点
start.connect(middle)
middle.connect(end)


# 构建工作流
workflow = builder.build("MyWorkflow")

# 创建上下文
ctx = FlowContext()

# 执行工作流
workflow.run(ctx)

# 查看执行轨迹
print("\nExecution Trace:")
for step in ctx.get_trace():
    print(f"{step['step']}. {step['node']} - Result: {step['result']}")