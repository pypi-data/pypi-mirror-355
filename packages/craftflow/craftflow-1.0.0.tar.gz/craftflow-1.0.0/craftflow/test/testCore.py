import sys
import os

# 获取当前脚本的上两级目录（flowcraft）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


from typing import Any
from craftflow.core import FlowContext, FlowNode, Workflow
# -------------------------
# Step 1: 定义几个具体的 FlowNode 子类
# -------------------------

class LoginNode(FlowNode):
    def process(self, ctx: FlowContext) -> Any:
        username = self.params.get("username")
        password = self.params.get("password")

        if username == "admin" and password == "123456":
            return "success"
        else:
            return "fail"

class SendEmailNode(FlowNode):
    def process(self, ctx: FlowContext) -> Any:
        email = self.params.get("email")
        print(f"[{self.name}] 正在发送邮件到 {email}")
        ctx["email_sent"] = True
        return "next"

class LogFailureNode(FlowNode):
    def process(self, ctx: FlowContext) -> Any:
        print(f"[{self.name}] 登录失败，记录日志")
        ctx["login_failed"] = True
        return "end"


# -------------------------
# Step 2: 实例化节点并连接起来
# -------------------------

login_node = LoginNode(name="LoginNode").set_params(username="admin", password="123456")
send_email_node = SendEmailNode(name="SendEmailNode").set_params(email="admin@example.com")
log_failure_node = LogFailureNode(name="LogFailureNode")

(login_node - 'success') >> send_email_node
(login_node - 'fail') >> log_failure_node

workflow = Workflow(start_node=login_node)

# -------------------------
# Step 3: 创建上下文并运行流程
# -------------------------

ctx = FlowContext()
workflow.process(ctx)

# -------------------------
# Step 4: 打印结果与轨迹信息
# -------------------------

print("\n=== 上下文数据 ===")
print(dict(ctx))

print("\n=== 执行轨迹 ===")
for step in ctx.get_trace():
    print(step)

print("\n=== 工具调用日志 ===")
for tool_call in ctx.get_tool_logs():
    print(tool_call)