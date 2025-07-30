# 导入langgraph库中的START和StateGraph
from langgraph.graph import START, StateGraph


# 定义一个节点函数，接收状态和配置参数
def add_func_node(state):
    # 返回更新后的状态，x值加1，y值加2
    return {"x": state["x"] + 1, "y": state["y"] + 2}


# 创建一个状态图构建器，使用字典作为状态类型
builder = StateGraph(dict)
# 将节点函数添加到图中，节点名称为"add_func_node"
builder.add_node(add_func_node)
# 添加从START节点到"add_func_node"节点的边
builder.add_edge(START, "add_func_node")
# 编译图
graph = builder.compile()
# 调用图并打印结果，初始状态为x=1, y=2
print(graph.invoke({"x": 1, "y": 2}))
