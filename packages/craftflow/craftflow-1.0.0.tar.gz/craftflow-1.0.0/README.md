# CraftFlow

CraftFlow is a powerful workflow orchestration framework designed for building complex processing pipelines, including RAG systems, multi-agent collaborations, and data processing workflows.

![CraftFlow Logo](images/logo.jpg) <!-- 可选：添加一个logo -->

## Features

- 🚀 **Asynchronous Processing**: Native support for async tasks
- ⚡ **Parallel Execution**: Execute tasks in parallel
- 🔍 **RAG System Support**: Built-in components for Retrieval-Augmented Generation
- 🧠 **MCP Decision Nodes**: Multi-Conditional Path decision making
- 🛠️ **Tool Integration**: Unified tool registry and invocation system
- 🤖 **Agent System**: Support for single and multi-agent collaboration
- 📊 **Execution Tracing**: Detailed trace of workflow execution

## 🛠️ Flow Chart
The overall technical flowchart is shown below, covering the entire lifecycle from input to output.

![CraftFlow Logo](images/mermaid.png)



## 💿 Installation

```bash
pip install craftflow
```

## 🏁Quick Start

### RAG System Example

```python
from craftflow.examples import rag_system

# Run a simple RAG workflow
rag_system.run_rag_example()
```

### Multi-Agent System

```python
from craftflow.examples import multi_agent_system

# Run a multi-agent collaboration workflow
multi_agent_system.run_multi_agent_example()
```

## 🔑Core Concepts

### FlowContext
The data sharing context that tracks execution history and tool calls.

### FlowNode
Base class for all workflow nodes. Various node types include:
- `TaskNode`: Synchronous task node
- `AsyncTaskNode`: Asynchronous task node
- `ToolNode`: Tool invocation node
- `MCPNode`: Multi-Conditional Path decision node
- `AgentNode`: Agent encapsulation node
- `ParallelNode`: Parallel execution node
- `BatchNode`: Batch processing node

### ToolRegistry
Central registry for managing tools and their metadata.

## ⚙️Documentation

Full documentation is available at [CraftFlow Docs](craftflow/docs/guide.md)

## 📂 Examples & Templates (Developing)

Explore more examples in the [examples directory](craftflow/examples/):
- `rag_system.py`: Full RAG workflow
- `multi_agent_system.py`: Multi-agent collaboration system


## 💡 Future Work
- Intelligent Scheduling & Optimization: Leverage historical execution metrics to dynamically allocate resources and optimize task ordering.

- Multi-Level Nested Workflows: Support complex hierarchical workflows with dependencies and parallel sub-flows across multiple levels.

- Visual Monitoring & Debugging: Provide a real-time graphical interface for inspecting workflow state, logs, and performance metrics.

- Enhanced Fault Tolerance & Rollback: Implement automatic error detection, compensation, and rollback mechanisms for robust recovery.

- Plugin Architecture: Offer a plugin system to allow community-built custom nodes, connectors, and tool integrations.

## 🤝 Contributing

Contributions are welcome! Please read our [Contribution Guidelines](CONTRIBUTING.md) before submitting pull requests.

## 📜 License

CraftFlow is released under the [MIT License](LICENSE).