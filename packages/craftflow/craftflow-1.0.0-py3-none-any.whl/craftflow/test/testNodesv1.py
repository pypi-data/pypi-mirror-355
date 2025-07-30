import time
from craftflow.core import FlowContext, FlowBuilder
from craftflow.nodes import TaskNode, ParallelNode, BatchNode


# 示例工具函数
def add_one(ctx: FlowContext, params: dict) -> str:
    value = params.get("value", 0)
    result = value + 1
    ctx["add_one_result"] = result
    print(f"add_one({value}) = {result}")
    return "next"

def multiply_by_two(ctx: FlowContext, params: dict) -> str:
    value = params.get("value", 0)
    result = value * 2
    ctx["multiply_result"] = result
    print(f"multiply_by_two({value}) = {result}")
    return "next"

def square(ctx: FlowContext, params: dict) -> str:
    value = params.get("value", 0)
    result = value ** 2
    ctx["square_result"] = result
    print(f"square({value}) = {result}")
    return "next"


def process_item(ctx: FlowContext, params: dict) -> str:
    item = ctx["item"]
    result = f"processed_{item}"
    print(f"Processing item: {item} => {result}")
    ctx["processed"] = result
    return "next"


# 构建并行工作流
def build_parallel_workflow():
    # 创建3个任务节点
    node1 = TaskNode(add_one, name="AddOne").set_params(value=1)
    node2 = TaskNode(multiply_by_two, name="MultiplyByTwo").set_params(value=5)
    node3 = TaskNode(square, name="Square").set_params(value=3)

    # 创建并行节点
    parallel_node = ParallelNode([node1, node2, node3], name="ParallelTasks")

    # 构建工作流
    builder = FlowBuilder()
    builder.start(parallel_node)

    workflow = builder.build()
    return workflow


# 构建批处理工作流
def build_batch_workflow():
    # 创建一个处理单个项目的节点
    task_node = TaskNode(process_item, name="ProcessItem")

    # 创建批处理节点
    batch_node = BatchNode(
        node=task_node,
        input_field="items",
        output_field="results",
        name="BatchProcessor"
    )

    # 构建工作流
    builder = FlowBuilder()
    builder.start(batch_node)

    workflow = builder.build()
    return workflow


# 测试并行节点
def test_parallel_node():
    print("\n=== Testing ParallelNode ===")
    workflow = build_parallel_workflow()

    context = FlowContext()
    result = workflow.run(context)

    # 从上下文中获取结果
    parallel_results = context["ParallelTasks_results"]
    add_one_result = context["add_one_result"]
    multiply_result = context["multiply_result"]
    square_result = context["square_result"]

    print("\nFinal Context:", dict(context))
    print("Parallel Results:", parallel_results)

    assert add_one_result == 2, f"add_one 应该等于 2，实际为 {add_one_result}"
    assert multiply_result == 10, f"multiply_by_two 应该等于 10，实际为 {multiply_result}"
    assert square_result == 9, f"square 应该等于 9，实际为 {square_result}"
    print("\n✅ 所有测试通过！")

# 测试批处理节点
def test_batch_node():
    print("\n=== Testing BatchNode ===")
    workflow = build_batch_workflow()

    context = FlowContext(items=["apple", "banana", "cherry"])
    result = workflow.run(context)

    print("\nFinal Context:", dict(context))
    print("Batch Results:", result)

    results = context["results"]
    assert isinstance(results, list), "结果应为列表"
    assert len(results) == 3, "应有3个处理结果"

    for i, item_ctx in enumerate(results):
        assert isinstance(item_ctx, FlowContext), "每个结果应为 FlowContext 实例"
        assert "processed" in item_ctx, "上下文中缺少 processed 字段"
        assert item_ctx["processed"] == f"processed_{context['items'][i]}", "处理结果错误"


# 主测试函数
if __name__ == "__main__":
    test_parallel_node()
    test_batch_node()
    print("\n✅ 所有测试通过！")