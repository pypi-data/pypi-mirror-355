from craftflow.core import FlowNode, FlowContext, FlowBuilder, Workflow
from typing import Any
import time

# 定义几个简单的节点类
class InputNode(FlowNode):
    def __init__(self):
        super().__init__("InputNode")

    def process(self, ctx: FlowContext) -> Any:
        # 设置输入值
        ctx["input_value"] = 42
        return "next"


class ProcessNode(FlowNode):
    def __init__(self):
        super().__init__("ProcessNode")

    def process(self, ctx: FlowContext) -> Any:
        # 获取输入值并处理
        input_value = ctx["input_value"]
        processed_value = input_value * 2

        # 记录处理结果
        ctx["processed_value"] = processed_value

        # 使用特定动作跳转
        if processed_value > 50:
            return "high"
        else:
            return "low"


class HighValueNode(FlowNode):
    def __init__(self):
        super().__init__("HighValueNode")

    def process(self, ctx: FlowContext) -> Any:
        # 处理高值情况
        value = ctx["processed_value"]
        formatted_value = f"High Value: {value}"

        # 记录格式化结果
        ctx["formatted_value"] = formatted_value

        return "next"


class LowValueNode(FlowNode):
    def __init__(self):
        super().__init__("LowValueNode")

    def process(self, ctx: FlowContext) -> Any:
        # 处理低值情况
        value = ctx["processed_value"]
        formatted_value = f"Low Value: {value}"

        # 记录格式化结果
        ctx["formatted_value"] = formatted_value

        return "next"


class OutputNode(FlowNode):
    def __init__(self):
        super().__init__("OutputNode")

    def process(self, ctx: FlowContext) -> Any:
        # 输出最终结果
        print(f"Final Result: {ctx['formatted_value']}")

        return "end"


# 测试工作流
def test_workflow():
    # 创建节点实例
    input_node = InputNode()
    process_node = ProcessNode()
    high_value_node = HighValueNode()
    low_value_node = LowValueNode()
    output_node = OutputNode()

    # 构建工作流
    workflow = (
        FlowBuilder()
            .add_node(input_node)
            .add_node(process_node)
            .add_node(high_value_node)
            .add_node(low_value_node)
            .add_node(output_node)
            .start(input_node)
    )

    # 连接节点
    input_node.connect(process_node)
    process_node.connect(high_value_node, "high").connect(output_node)
    process_node.connect(low_value_node, "low").connect(output_node)

    # 或者使用操作符更简洁地连接
    # (input_node >> process_node - "high" >> high_value_node >> output_node)
    # (process_node - "low" >> low_value_node >> output_node)

    # 创建上下文并运行工作流
    context = FlowContext()
    workflow.build().run(context)

    # 输出执行轨迹
    print("\nExecution Path:")
    for step in context.get_trace():
        print(f"{step['step']}. {step['node']} ({time.ctime(step['timestamp'])})")

        # 输出最终上下文
        print("\nFinal Context:")
        print(dict(context))


if __name__ == "__main__":
    test_workflow()