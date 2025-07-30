# 导入必要的库
from typing_extensions import TypedDict  # 用于定义类型化的字典
from langgraph.graph import StateGraph, START, END  # LangGraph核心组件
from langchain_core.runnables.graph import MermaidDrawMethod  # 图形可视化方法
from display_graph import display_graph  # 自定义的图形显示工具


# 定义状态结构
class HelloWorldState(TypedDict):
    greeting: str  # 存储问候消息的字段


# 定义感叹号节点函数
def exclamation_node(state: HelloWorldState):
    state["greeting"] += "!"  # 在字符串末尾添加感叹号
    return state


# 定义问候节点函数
def hello_world_node(state: HelloWorldState):
    state["greeting"] = "Hello World, " + state["greeting"]  # 添加问候前缀
    return state


# 初始化图构建器
builder = StateGraph(HelloWorldState)
builder.add_node("greet", hello_world_node)  # 添加问候节点

# 构建执行流程
builder.add_edge(START, "greet")  # 从开始节点连接到问候节点
builder.add_node("exclaim", exclamation_node)  # 添加感叹号节点
builder.add_edge("greet", "exclaim")  # 问候节点连接到感叹号节点
builder.add_edge("exclaim", END)  # 感叹号节点连接到结束节点

# 编译并执行图
graph = builder.compile()
result = graph.invoke({"greeting": "from LangGraph!"})

# 输出结果
print(result)  # 预期输出: {'greeting': 'Hello World, from LangGraph!!'}

# 可视化图形
display_graph(graph)  # 调用自定义函数显示图形
