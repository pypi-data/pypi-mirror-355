# 导入必要的类型和库
from typing_extensions import TypedDict  # 用于定义类型化字典
from langgraph.graph import StateGraph, START, END  # LangGraph核心组件


# 定义状态结构
class HelloWorldState(TypedDict):
    """工作流状态容器"""
    message: str  # 存储消息内容的键


# 定义节点处理函数
def hello_world_node(state: HelloWorldState):
    """节点处理逻辑：在消息后追加'Hello World'"""
    state["message"] += "Hello World"  # 修改状态中的消息内容
    return state  # 返回更新后的状态


# 初始化图构建器
graph_builder = StateGraph(HelloWorldState)  # 创建指定状态类型的图构建器

# 添加节点到图中
graph_builder.add_node("hello_world", hello_world_node)  # 注册名为"hello_world"的节点

# 定义执行流程的边(连接关系)
"""图的边定义"""
graph_builder.add_edge(START, "hello_world")  # 从开始节点连接到hello_world节点
graph_builder.add_edge("hello_world", END)  # 从hello_world节点连接到结束节点

# 编译并执行图
"""图编译和执行"""
graph = graph_builder.compile()  # 编译图结构
result = graph.invoke({"message": "Hi! "})  # 执行图并传入初始状态

# 输出执行结果
print(result)  # 预期输出: {'message': 'Hi! Hello World'}
