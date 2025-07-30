# 导入必要的库和模块
from langgraph.graph import StateGraph, START, END  # 工作流图核心组件
from typing_extensions import TypedDict  # 类型化字典支持
from display_graph import display_graph  # 图形可视化工具


# 定义状态结构
class GreetingState(TypedDict):
    """工作流状态容器，存储问候消息"""
    greeting: str  # 存储问候消息的键


# 定义预处理节点（标准化问候语）
def normalize_greeting_node(state):
    """将问候语转换为小写格式"""
    state["greeting"] = state["greeting"].lower()  # 标准化为小写
    return state  # 返回更新后的状态


# 定义"Hi"问候节点
def hi_greeting_node(state):
    """处理包含'hi'的问候语"""
    state["greeting"] = "Hi there, " + state["greeting"]  # 添加友好问候前缀
    return state


# 定义标准问候节点
def regular_greeting_node(state):
    """处理普通问候语"""
    state["greeting"] = "Hello, " + state["greeting"]  # 添加标准问候前缀
    return state


# 定义条件选择函数
def choose_greeting_node(state):
    """根据问候语内容选择分支路径"""
    return "hi_greeting" if "hi" in state["greeting"] else "regular_greeting"


# 初始化工作流图
builder = StateGraph(GreetingState)  # 创建图构建器
builder.add_node("normalize_greeting", normalize_greeting_node)  # 添加标准化节点
builder.add_node("hi_greeting", hi_greeting_node)  # 添加Hi问候节点
builder.add_node("regular_greeting", regular_greeting_node)  # 添加标准问候节点

# 构建工作流路径
builder.add_edge(START, "normalize_greeting")  # 开始→标准化节点
builder.add_conditional_edges(  # 条件分支
    source="normalize_greeting",  # 源节点
    path=choose_greeting_node,  # 条件判断函数
    path_map=["hi_greeting", "regular_greeting"]  # 可能的分支目标
)
builder.add_edge("hi_greeting", END)  # Hi问候→结束
builder.add_edge("regular_greeting", END)  # 标准问候→结束

# 编译并运行工作流
graph = builder.compile()  # 编译图结构
display_graph(graph)  # 可视化工作流

# 测试用例
result = graph.invoke({"greeting": "HI THERe!"})  # 测试包含"Hi"的问候
print(result)  # 预期输出: {'greeting': 'Hi there, hi there!'}

result = graph.invoke({"greeting": "Good morning!"})  # 测试普通问候
print(result)  # 预期输出: {'greeting': 'Hello, good morning!'}
