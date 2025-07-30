import time
import warnings
import copy
from typing import Any, Dict, List, Optional


class FlowContext(dict):
    """增强型数据共享上下文，支持数据追踪和工具调用"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._execution_path = []  # 执行路径追踪
        self._tool_calls = []  # 工具调用记录
        self._current_step = 0  # 当前步骤计数器

    def set(self, action: str = "next", **kwargs):
        """
        批量设置上下文数据并返回指定动作名

        :param action: 下一步动作名，例如 'next', 'high', 'low'
        :param kwargs: 要设置的键值对
        :return: 指定的动作名字符串
        """
        self.update(kwargs)
        return action

    def track(self, node: str, result: Any):
        """记录节点执行结果"""
        self._current_step += 1
        self._execution_path.append({
            'step': self._current_step,
            'node': node,
            'timestamp': time.time(),
            'result': result
        })
        return result

    def log_tool(self, tool_name: str, params: dict, result: Any):
        """记录工具调用"""
        self._tool_calls.append({
            'tool': tool_name,
            'params': params,
            'result': result,
            'timestamp': time.time(),
            'step': self._current_step
        })
        return result

    def get_trace(self) -> List[Dict]:
        """获取执行轨迹"""
        return copy.deepcopy(self._execution_path)

    def get_tool_logs(self) -> List[Dict]:
        """获取工具调用日志"""
        return copy.deepcopy(self._tool_calls)

    def __str__(self):
        return f"FlowContext(data={len(self)} keys, trace={len(self._execution_path)} steps, tools={len(self._tool_calls)} calls)"


class FlowNode:
    """工作流节点基类"""

    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.next_nodes: Dict[str, 'FlowNode'] = {}  # 动作->节点映射
        self.params: Dict[str, Any] = {}

    def set_params(self, **kwargs) -> 'FlowNode':
        """设置节点参数"""
        self.params.update(kwargs)
        return self

    def connect(self, node: 'FlowNode', action: str = "next") -> 'FlowNode':
        """连接到下一个节点"""
        if action in self.next_nodes:
            warnings.warn(f"覆盖 '{action}' 动作的连接")
        self.next_nodes[action] = node
        return node

    def process(self, ctx: FlowContext) -> Any:
        """节点处理逻辑（子类实现）"""
        raise NotImplementedError("子类必须实现 process 方法")

    def run(self, ctx: FlowContext) -> str:
        """执行节点并返回下一步动作"""
        # 执行节点逻辑
        result = self.process(ctx)

        # 记录到上下文
        ctx.track(self.name, result)

        # 返回动作类型
        if result in self.next_nodes:
            return result
        return "next" if "next" in self.next_nodes else "end"

    # 操作符重载
    def __rshift__(self, other: 'FlowNode') -> 'FlowNode':
        """操作符重载: node1 >> node2"""
        return self.connect(other)

    def __sub__(self, action: str) -> '_FlowTransition':
        """操作符重载: node - 'action' >> node2"""
        return _FlowTransition(self, action)


class _FlowTransition:
    """条件转移辅助类"""

    def __init__(self, source: FlowNode, action: str):
        self.source = source
        self.action = action

    def __rshift__(self, target: FlowNode) -> FlowNode:
        """操作符重载: (node - 'action') >> node2"""
        return self.source.connect(target, self.action)


class Workflow(FlowNode):
    """工作流控制器"""

    def __init__(self,
                 start_node: FlowNode,
                 name: str = "Workflow"):
        super().__init__(name)
        self.start_node = start_node

    def process(self, ctx: FlowContext) -> Any:
        """执行整个工作流"""
        current = self.start_node
        result = None

        while current:
            # 执行当前节点
            action = current.run(ctx)

            # 获取下一个节点
            if action in current.next_nodes:
                current = current.next_nodes[action]
            else:
                current = None

        return result


class FlowBuilder:
    """工作流构建器（DSL工具）"""

    def __init__(self):
        self.nodes = {}
        self.start_node = None

    def add_node(self, node: FlowNode) -> 'FlowBuilder':
        """添加节点到工作流"""
        self.nodes[node.name] = node
        return self

    def start(self, node: FlowNode) -> 'FlowBuilder':
        """设置起始节点"""
        self.start_node = node
        return self

    def build(self, name: str = "Workflow") -> Workflow:
        """构建工作流"""
        if not self.start_node:
            raise ValueError("未设置起始节点")
        return Workflow(self.start_node, name)

    # 快捷操作符
    def __setitem__(self, name: str, node: FlowNode) -> 'FlowBuilder':
        """通过名称添加节点: builder['name'] = node, 重载[]操作符，允许使用builder['name'] = node的方式添加节点。"""
        if node.name != name:
            node.name = name
        return self.add_node(node)
