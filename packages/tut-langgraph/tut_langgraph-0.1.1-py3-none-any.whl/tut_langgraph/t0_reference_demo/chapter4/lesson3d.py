# 导入类型定义和工作流构建组件
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 定义用户状态结构
class UserState(TypedDict):
    """用户状态容器，包含会员状态和消息内容"""
    is_premium: bool  # 是否付费会员标识
    message: str  # 消息内容


# === 节点函数定义 ===
def greet_user(state: UserState):
    """初始问候节点：设置基础欢迎语"""
    state["message"] = "Welcome!"
    return state


def premium_greeting(state: UserState):
    """付费会员专属问候"""
    state["message"] += " Thank you for being a premium user!"
    return state


def regular_greeting(state: UserState):
    """普通用户问候"""
    state["message"] += " Enjoy your time here!"
    return state


def check_subscription(state: UserState):
    """条件判断节点：根据会员状态路由流程"""
    return "premium_greeting" if state["is_premium"] else "regular_greeting"


# === 工作流构建 ===
graph_builder = StateGraph(UserState)
graph_builder.set_entry_point("greet_user")  # 设置入口节点

# 添加所有节点
graph_builder.add_node("greet_user", greet_user)
graph_builder.add_node("check_subscription", check_subscription)  # 条件判断节点
graph_builder.add_node("premium_greeting", premium_greeting)
graph_builder.add_node("regular_greeting", regular_greeting)

# 构建工作流路径
graph_builder.add_edge(START, "greet_user")  # 开始 → 初始问候
graph_builder.add_conditional_edges(
    "greet_user",  # 源节点
    check_subscription,  # 条件判断函数
    ["premium_greeting", "regular_greeting"]  # 可能的分支目标
)
graph_builder.add_edge("premium_greeting", END)  # 付费路径结束
graph_builder.add_edge("regular_greeting", END)  # 普通路径结束

# === 执行验证 ===
graph = graph_builder.compile()

# 测试付费用户路径
premium_result = graph.invoke({"is_premium": True, "message": ""})
print(premium_result)  # 输出付费用户专属问候

# 测试普通用户路径
regular_result = graph.invoke({"is_premium": False, "message": ""})
print(regular_result)  # 输出普通用户问候
