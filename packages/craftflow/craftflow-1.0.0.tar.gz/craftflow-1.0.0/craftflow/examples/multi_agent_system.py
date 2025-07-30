import asyncio
import time
import random
from craftflow import FlowContext, TaskNode, Workflow, ToolRegistry
from craftflow.nodes import AgentNode, MCPNode, ParallelNode
from typing import List, Dict, Any


class ResearchTools:
    """研究工具集"""

    @staticmethod
    def search_web(query: str) -> List[Dict]:
        """网页搜索工具"""
        time.sleep(0.1)
        return [
            {"title": f"{query} 的搜索结果1", "snippet": f"这是关于{query}的第一个搜索结果摘要"},
            {"title": f"{query} 的搜索结果2", "snippet": f"这是关于{query}的第二个搜索结果摘要"}
        ]

    @staticmethod
    def search_knowledge_base(query: str) -> List[str]:
        """知识库搜索工具"""
        time.sleep(0.05)
        return [
            f"知识库条目1: {query} 的定义",
            f"知识库条目2: {query} 的历史发展"
        ]

    @staticmethod
    def analyze_sentiment(text: str) -> Dict[str, float]:
        """情感分析工具"""
        time.sleep(0.05)
        return {
            "positive": random.uniform(0.3, 0.9),
            "negative": random.uniform(0.1, 0.4),
            "neutral": random.uniform(0.1, 0.5)
        }

    @staticmethod
    def summarize_text(texts: List[str]) -> str:
        """文本摘要工具"""
        time.sleep(0.1)
        return f"摘要: 这是对{len(texts)}个文本的综合摘要"

    @staticmethod
    def generate_report(data: Dict) -> str:
        """报告生成工具"""
        time.sleep(0.2)
        return f"报告标题: {data.get('title', '未命名报告')}\n\n主要内容:\n{data.get('content', '无内容')}"


class CollaborationTools:
    """协作工具集"""

    @staticmethod
    def assign_task(task: str, agents: List[str]) -> Dict[str, List[str]]:
        """任务分配工具"""
        time.sleep(0.05)
        assignments = {}
        parts = task.split()
        per_agent = max(1, len(parts) // len(agents))

        for i, agent in enumerate(agents):
            start = i * per_agent
            end = (i + 1) * per_agent if i < len(agents) - 1 else len(parts)
            assignments[agent] = " ".join(parts[start:end])

        return assignments

    @staticmethod
    def merge_results(results: Dict[str, Any]) -> str:
        """结果合并工具"""
        time.sleep(0.1)
        merged = "合并结果:\n"
        for agent, result in results.items():
            merged += f"## {agent}的贡献:\n{result}\n\n"
        return merged

    @staticmethod
    def resolve_conflict(conflicting_data: Dict[str, Any]) -> Any:
        """冲突解决工具"""
        time.sleep(0.1)
        # 简单投票机制
        values = list(conflicting_data.values())
        return max(set(values), key=values.count)

    @staticmethod
    def coordinate_agents(agents: List[str], task: str) -> Dict[str, Any]:
        """Agent协调工具"""
        time.sleep(0.1)
        return {agent: f"{agent}已接受任务: {task}" for agent in agents}


def build_research_agent(tools: ToolRegistry) -> Workflow:
    """构建研究Agent工作流"""
    start = TaskNode(
        lambda ctx, p: print(f"研究Agent开始: {ctx.get('research_topic', '未知主题')}"),
        name="研究开始"
    )

    # 知识检索节点
    knowledge_search = tools.create_node(
        "knowledge_search",
        input_map=lambda ctx: {"query": ctx["research_topic"]},
        output_key="knowledge_results",
        name="知识检索"
    )

    # 网络搜索节点
    web_search = tools.create_node(
        "web_search",
        input_map=lambda ctx: {"query": ctx["research_topic"]},
        output_key="web_results",
        name="网络搜索"
    )

    # 结果合并节点
    merge_node = TaskNode(
        lambda ctx, p: {
            "knowledge": ctx.get("knowledge_results", []),
            "web": ctx.get("web_results", [])
        },
        name="结果合并",
        output_key="research_data"
    )

    # 摘要生成节点
    summarize_node = TaskNode(
        lambda ctx, p: tools.create_node(
            "summarize",
            input_map=lambda ctx: {"texts": [
                item["snippet"] if isinstance(item, dict) else item
                for item in ctx["research_data"]["knowledge"] + ctx["research_data"]["web"]
            ]},
            output_key="summary"
        ).run(ctx),
        name="生成摘要"
    )

    # 报告生成节点
    report_node = TaskNode(
        lambda ctx, p: tools.create_node(
            "generate_report",
            input_map=lambda ctx: {
                "title": f"关于'{ctx['research_topic']}'的研究报告",
                "content": f"摘要:\n{ctx['summary']}"
            },
            output_key="research_report"
        ).run(ctx),
        name="生成报告"
    )

    # 构建连接
    start >> knowledge_search >> merge_node >> summarize_node >> report_node
    start >> web_search >> merge_node

    return Workflow(start, "ResearchAgent")


def build_analysis_agent(tools: ToolRegistry) -> Workflow:
    """构建分析Agent工作流"""
    start = TaskNode(
        lambda ctx, p: print(f"分析Agent开始: {ctx.get('analysis_task', '未知任务')}"),
        name="分析开始"
    )

    # 数据收集节点
    collect_node = TaskNode(
        lambda ctx, p: ctx.get("input_data", {}),
        name="数据收集",
        output_key="collected_data"
    )

    # 数据分析节点
    analysis_node = TaskNode(
        lambda ctx, p: {
            "insights": f"基于{len(ctx['collected_data'])}条数据的分析洞察",
            "trends": "识别出的主要趋势",
            "anomalies": "检测到的异常点"
        },
        name="数据分析",
        output_key="analysis_results"
    )

    # 报告生成节点
    report_node = TaskNode(
        lambda ctx, p: tools.create_node(
            "generate_report",
            input_map=lambda ctx: {
                "title": "数据分析报告",
                "content": f"洞察:\n{ctx['analysis_results']['insights']}"
            },
            output_key="analysis_report"
        ).run(ctx),
        name="生成报告"
    )

    # 构建连接
    start >> collect_node >> analysis_node >> report_node

    return Workflow(start, "AnalysisAgent")


def build_writing_agent(tools: ToolRegistry) -> Workflow:
    """构建写作Agent工作流"""
    start = TaskNode(
        lambda ctx, p: print(f"写作Agent开始: {ctx.get('writing_task', '未知任务')}"),
        name="写作开始"
    )

    # 材料收集节点
    collect_node = TaskNode(
        lambda ctx, p: ctx.get("input_materials", []),
        name="材料收集",
        output_key="collected_materials"
    )

    # 内容生成节点
    content_node = TaskNode(
        lambda ctx, p: {
            "part1": f"第一部分内容: 基于{ctx['collected_materials'][0]}",
            "part2": f"第二部分内容: 基于{ctx['collected_materials'][1]}"
        },
        name="生成内容",
        output_key="content"
    )

    # 最终报告节点
    report_node = TaskNode(
        lambda ctx, p: tools.create_node(
            "generate_report",
            input_map=lambda ctx: {
                "title": "最终文档",
                "content": "\n".join(ctx["content"].values())
            },
            output_key="final_document"
        ).run(ctx),
        name="生成文档"
    )

    # 构建连接
    start >> collect_node >> content_node >> report_node

    return Workflow(start, "WritingAgent")


def build_coordinator_agent(tools: ToolRegistry, agents: Dict[str, Workflow]) -> Workflow:
    """构建协调Agent工作流"""
    start = TaskNode(
        lambda ctx, p: print(f"协调Agent开始: 项目 '{ctx.get('project_name', '未知项目')}'"),
        name="协调开始"
    )

    # 任务分解节点
    decompose_node = TaskNode(
        lambda ctx, p: [
            "研究阶段",
            "分析阶段",
            "写作阶段"
        ],
        name="任务分解",
        output_key="phases"
    )

    # 任务分配节点
    assign_node = TaskNode(
        lambda ctx, p: tools.create_node(
            "assign_task",
            input_map=lambda ctx: {
                "task": ctx["project_task"],
                "agents": list(agents.keys())
            },
            output_key="assignments"
        ).run(ctx),
        name="任务分配"
    )

    # 研究阶段节点
    research_phase = AgentNode(
        agents["ResearchAgent"],
        input_map=lambda ctx: {
            "research_topic": ctx["assignments"]["ResearchAgent"]
        },
        output_key="research_output",
        name="执行研究"
    )

    # 分析阶段节点
    analysis_phase = AgentNode(
        agents["AnalysisAgent"],
        input_map=lambda ctx: {
            "analysis_task": ctx["assignments"]["AnalysisAgent"],
            "input_data": ctx["research_output"]["research_data"]
        },
        output_key="analysis_output",
        name="执行分析"
    )

    # 写作阶段节点
    writing_phase = AgentNode(
        agents["WritingAgent"],
        input_map=lambda ctx: {
            "writing_task": ctx["assignments"]["WritingAgent"],
            "input_materials": [
                ctx["research_output"]["research_report"],
                ctx["analysis_output"]["analysis_report"]
            ]
        },
        output_key="writing_output",
        name="执行写作"
    )

    # 结果合并节点
    merge_node = TaskNode(
        lambda ctx, p: tools.create_node(
            "merge_results",
            input_map=lambda ctx: {
                "results": {
                    "ResearchAgent": ctx["research_output"]["research_report"],
                    "AnalysisAgent": ctx["analysis_output"]["analysis_report"],
                    "WritingAgent": ctx["writing_output"]["final_document"]
                }
            },
            output_key="merged_results"
        ).run(ctx),
        name="合并结果"
    )

    # 最终报告节点
    final_report = TaskNode(
        lambda ctx, p: tools.create_node(
            "generate_report",
            input_map=lambda ctx: {
                "title": f"项目 '{ctx['project_name']}' 最终报告",
                "content": ctx["merged_results"]
            },
            output_key="final_report"
        ).run(ctx),
        name="生成最终报告"
    )

    # 构建连接
    start >> decompose_node >> assign_node
    assign_node >> research_phase >> analysis_phase >> writing_phase
    writing_phase >> merge_node >> final_report

    return Workflow(start, "CoordinatorAgent")


def run_multi_agent_example():
    """运行多Agent协作示例"""
    # 创建工具注册中心
    tools = ToolRegistry()

    # 注册工具
    tools.register("web_search", ResearchTools.search_web, description="网页搜索工具")
    tools.register("knowledge_search", ResearchTools.search_knowledge_base, description="知识库搜索工具")
    tools.register("summarize", ResearchTools.summarize_text, description="文本摘要工具")
    tools.register("generate_report", ResearchTools.generate_report, description="报告生成工具")
    tools.register("assign_task", CollaborationTools.assign_task, description="任务分配工具")
    tools.register("merge_results", CollaborationTools.merge_results, description="结果合并工具")

    # 构建各个Agent
    agents = {
        "ResearchAgent": build_research_agent(tools),
        "AnalysisAgent": build_analysis_agent(tools),
        "WritingAgent": build_writing_agent(tools)
    }

    # 构建协调Agent
    coordinator = build_coordinator_agent(tools, agents)

    # 创建项目上下文
    project_context = FlowContext({
        "project_name": "人工智能对社会的影响研究",
        "project_task": "研究人工智能对社会各方面的影响，分析数据，撰写报告"
    })

    print("\n" + "=" * 60)
    print("启动多Agent协作系统")
    print("=" * 60)
    print(f"项目: {project_context['project_name']}")
    print(f"任务: {project_context['project_task']}")
    print("-" * 60)

    # 执行协作工作流
    start_time = time.time()
    coordinator.run(project_context)
    elapsed = time.time() - start_time

    # 显示结果
    print("\n" + "=" * 60)
    print("项目执行完成")
    print("=" * 60)
    print(f"总执行时间: {elapsed:.2f}秒")

    # 显示最终报告
    final_report = project_context.get("final_report", "无最终报告")
    print("\n最终报告:")
    print("-" * 60)
    print(final_report)
    print("-" * 60)

    # 显示工具调用记录
    tool_logs = project_context.get_tool_logs()
    if tool_logs:
        print("\n工具调用记录:")
        for log in tool_logs:
            print(f"- [{log['step']}] {log['tool']}: 参数={log['params']}")


if __name__ == "__main__":
    run_multi_agent_example()