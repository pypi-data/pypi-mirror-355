# 导入类型定义和工作流构建组件
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# === 状态类型定义 ===
class OverallState(TypedDict):
    """主状态容器，包含完整处理流程中的中间状态"""
    partial_message: str  # 中间处理结果
    user_input: str  # 保留原始输入
    message_output: str  # 最终输出占位


class InputState(TypedDict):
    """输入状态，仅包含用户初始输入"""
    user_input: str


class OutputState(TypedDict):
    """输出状态，仅包含最终处理结果"""
    message_output: str


class PrivateState(TypedDict):
    """私有中间状态，用于节点间特定数据传递"""
    private_message: str


# === 节点函数定义 ===
def add_world(state: InputState) -> OverallState:
    """节点1：在输入后追加' World'"""
    partial_message = state["user_input"] + " World"
    print(f"节点1处理: 将'{state['user_input']}'转换为'{partial_message}'")
    return {
        "partial_message": partial_message,
        "user_input": state["user_input"],  # 透传原始输入
        "message_output": ""  # 初始化输出
    }


def add_exclamation(state: OverallState) -> PrivateState:
    """节点2：在中间结果后追加'!'"""
    private_message = state["partial_message"] + "!"
    print(f"节点2处理: 将'{state['partial_message']}'转换为'{private_message}'")
    return {"private_message": private_message}


def finalize_message(state: PrivateState) -> OutputState:
    """节点3：生成最终输出结果"""
    message_output = state["private_message"]
    print(f"节点3处理: 最终输出消息'{message_output}'")
    return {"message_output": message_output}


# === 工作流构建 ===
builder = StateGraph(
    OverallState,  # 主状态类型
    input=InputState,  # 显式声明输入类型
    output=OutputState  # 显式声明输出类型
)

# 添加三个处理节点
builder.add_node("add_world", add_world)
builder.add_node("add_exclamation", add_exclamation)
builder.add_node("finalize_message", finalize_message)

# 构建线性执行流
builder.add_edge(START, "add_world")  # 开始 → 节点1
builder.add_edge("add_world", "add_exclamation")  # 节点1 → 节点2
builder.add_edge("add_exclamation", "finalize_message")  # 节点2 → 节点3
builder.add_edge("finalize_message", END)  # 节点3 → 结束

# === 执行验证 ===
graph = builder.compile()  # 编译工作流
result = graph.invoke({"user_input": "Hello"})  # 执行并传入初始输入
print(result)  # 输出: {'message_output': 'Hello World!'}
