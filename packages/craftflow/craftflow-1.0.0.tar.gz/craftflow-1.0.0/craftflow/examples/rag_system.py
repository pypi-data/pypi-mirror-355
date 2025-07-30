import asyncio
import time
import random
from craftflow import FlowContext, TaskNode, Workflow, ToolRegistry, FlowBuilder
from craftflow.nodes import AgentNode, MCPNode
from typing import List, Dict


class DemoKnowledgeBase:
    """模拟知识库"""

    def __init__(self):
        self.data = {
            "人工智能": "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学。",
            "机器学习": "机器学习是人工智能的一个分支，它使计算机系统能够从数据中学习并改进其性能，而无需明确编程。",
            "深度学习": "深度学习是机器学习的一个子领域，它使用多层神经网络来模拟人脑的学习过程，特别擅长处理图像、语音和自然语言。",
            "大语言模型": "大语言模型（LLM）是一种基于深度学习的人工智能模型，通过在大规模文本数据上训练，能够生成类似人类的文本。"
        }

    def search(self, query: str) -> List[str]:
        """知识库搜索工具"""
        time.sleep(0.1)
        results = []
        for term, definition in self.data.items():
            if query.lower() in term.lower() or query.lower() in definition.lower():
                results.append(f"{term}: {definition}")
        return results


class WebSearchEngine:
    """模拟搜索引擎"""

    def __init__(self):
        self.cache = {}

    async def search(self, query: str) -> List[Dict]:
        """网页搜索工具（异步）"""
        await asyncio.sleep(0.2)

        if query not in self.cache:
            self.cache[query] = [
                {"title": f"{query} 的搜索结果1", "snippet": f"这是关于{query}的第一个搜索结果摘要"},
                {"title": f"{query} 的搜索结果2", "snippet": f"这是关于{query}的第二个搜索结果摘要"},
                {"title": f"{query} 的搜索结果3", "snippet": f"这是关于{query}的第三个搜索结果摘要"}
            ]
        return self.cache[query]


class LLMService:
    """模拟大语言模型服务"""

    def __init__(self):
        self.prompts = {}

    async def generate(self, prompt: str, model: str = "gpt-4") -> str:
        """LLM生成工具（异步）"""
        await asyncio.sleep(0.3)

        if prompt not in self.prompts:
            self.prompts[prompt] = f"{model}响应：这是关于'{prompt}'的详细回答。模型认为这是用户查询的一个全面解释。"
        return self.prompts[prompt]


def build_rag_workflow(tools: ToolRegistry) -> Workflow:
    """构建 RAG 工作流"""
    builder = FlowBuilder()

    # 1. 定义所有节点 - 确保所有节点返回字符串动作名
    start_node = TaskNode(
        lambda ctx, p: print(f"开始处理查询: {ctx['query']}") or "next",
        name="开始"
    )

    # 知识库搜索节点 - 使用 create_node 创建的工具节点会自动处理返回值
    knowledge_search = tools.create_node(
        "knowledge_search",
        input_map=lambda ctx: {"query": ctx["query"]},
        output_key="knowledge_results"
    )

    web_search = tools.create_node(
        "web_search",
        input_map=lambda ctx: {"query": ctx["query"]},
        output_key="web_results"
    )

    # 策略决策节点 - 返回字符串动作名
    def search_strategy(ctx, params):
        query = ctx["query"]
        if len(query) < 10:
            return "simple"
        elif "最新" in query or "新闻" in query:
            return "web_only"
        return "full"

    strategy_node = MCPNode(
        [search_strategy],
        name="搜索策略"
    )

    # 结果合并节点 - 返回 "next" 而不是列表
    def merge_results(ctx, params):
        knowledge = ctx.get("knowledge_results", [])
        web = ctx.get("web_results", [])
        combined = knowledge + web
        unique_results = []
        seen = set()
        for result in combined:
            if isinstance(result, dict):
                key = result.get("title", str(result))
            else:
                key = result
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        ctx["merged_results"] = unique_results
        return "next"  # 返回动作名而不是数据

    merge_node = TaskNode(merge_results, name="结果合并")

    # 简单搜索路径 - 返回 "next" 而不是数据
    def simple_search(ctx, params):
        ctx["selected_results"] = ctx["knowledge_results"][:2]
        return "next"  # 返回动作名而不是数据

    simple_search_node = TaskNode(simple_search, name="简单搜索")

    # 网页搜索路径 - 返回 "next" 而不是数据
    def web_only_search(ctx, params):
        ctx["selected_results"] = ctx["web_results"][:3]
        return "next"  # 返回动作名而不是数据

    web_only_search_node = TaskNode(web_only_search, name="网页搜索")

    # 完整搜索路径 - 返回 "next" 而不是数据
    def full_search(ctx, params):
        ctx["selected_results"] = ctx["merged_results"][:4]
        return "next"  # 返回动作名而不是数据

    full_search_node = TaskNode(full_search, name="完整搜索")

    # LLM生成节点 - 使用 create_node 创建的工具节点会自动处理返回值
    def build_prompt(ctx, params):
        query = ctx["query"]
        context = ctx["selected_results"]
        if isinstance(context[0], dict):
            context_str = "\n".join([f"{item['title']}: {item['snippet']}" for item in context])
        else:
            context_str = "\n".join(context)
        return f"基于以下信息回答问题:\n{context_str}\n\n问题: {query}"

    llm_node = tools.create_node(
        "llm_generate",
        input_map=build_prompt,
        output_key="final_answer"
    )

    # 结果输出节点 - 返回 "end" 动作名
    result_node = TaskNode(
        lambda ctx, p: print(f"最终答案: {ctx['final_answer']}") or "end",
        name="结果输出"
    )

    # 2. 添加所有节点
    nodes = [
        start_node,
        knowledge_search,
        web_search,
        strategy_node,
        merge_node,
        simple_search_node,
        web_only_search_node,
        full_search_node,
        llm_node,
        result_node
    ]

    for node in nodes:
        builder.add_node(node)

    # 3. 构建连接关系
    start_node >> strategy_node

    # 简单路径
    strategy_node - "simple" >> knowledge_search
    knowledge_search >> simple_search_node >> llm_node >> result_node

    # 网页路径
    strategy_node - "web_only" >> web_search
    web_search >> web_only_search_node >> llm_node >> result_node

    # 完整路径
    strategy_node - "full" >> knowledge_search >> merge_node
    strategy_node - "full" >> web_search >> merge_node
    merge_node >> full_search_node >> llm_node >> result_node

    # 4. 设置起始节点
    builder.start(start_node)

    return builder.build(name="RAGWorkflow")

def run_rag_example():
    """运行 RAG 工作流示例"""
    # 创建工具注册中心
    tools = ToolRegistry()

    # 初始化模拟服务
    kb = DemoKnowledgeBase()
    web = WebSearchEngine()
    llm = LLMService()

    # 注册工具
    tools.register("knowledge_search", kb.search, description="知识库搜索工具")
    tools.register("web_search", web.search, is_async=True, description="网页搜索工具（异步）")
    tools.register("llm_generate", llm.generate, is_async=True, description="LLM生成工具（异步）")

    # 构建RAG工作流
    rag_workflow = build_rag_workflow(tools)

    # 测试查询
    queries = [
        "什么是人工智能？",
        "机器学习的最新进展",
        "大语言模型在自然语言处理中的应用",
        "深度学习和机器学习的区别"
    ]

    for query in queries:
        print("\n" + "=" * 60)
        print(f"处理查询: {query}")
        print("-" * 60)

        # 创建上下文
        ctx = FlowContext({"query": query})

        # 执行工作流
        start_time = time.time()
        rag_workflow.run(ctx)
        elapsed = time.time() - start_time

        # 显示结果
        print(f"\n处理时间: {elapsed:.2f}秒")
        print(f"最终答案: {ctx['final_answer']}")

        # 显示工具调用
        tool_logs = ctx.get_tool_logs()
        if tool_logs:
            print("\n工具调用记录:")
            for log in tool_logs:
                print(f"- [{log['step']}] {log['tool']}: {log['result']}")


if __name__ == "__main__":
    run_rag_example()