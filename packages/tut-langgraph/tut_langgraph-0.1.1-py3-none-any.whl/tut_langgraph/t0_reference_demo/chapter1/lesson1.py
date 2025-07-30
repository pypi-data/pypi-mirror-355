# lesson1.py
# 导入必要的库
import random  # 用于生成随机数
import subprocess  # 用于调用系统命令
import sys  # 用于系统相关操作
from typing_extensions import TypedDict  # 用于定义类型化的字典
from langgraph.graph import StateGraph, START, END  # LangGraph的核心组件
from langchain_core.runnables.graph import MermaidDrawMethod  # 用于图形可视化
import os  # 用于文件和目录操作


# 定义状态结构，使用TypedDict确保类型安全
class HelloWorldState(TypedDict):
    greeting: str  # 这个键将存储问候消息


# 定义节点函数，处理状态数据
def hello_world_node(state: HelloWorldState):
    # 在原有问候语前添加"Hello World"
    state["greeting"] = "Hello World, " + state["greeting"]
    return state  # 返回修改后的状态


# 初始化图构建器，指定状态类型
builder = StateGraph(HelloWorldState)
# 添加名为"greet"的节点，关联hello_world_node函数
builder.add_node("greet", hello_world_node)

# 定义执行流程的边(连接)
builder.add_edge(START, "greet")  # 连接START节点到"greet"节点
builder.add_edge("greet", END)  # 连接"greet"节点到END节点

# 编译图并执行
graph = builder.compile()
# 调用图，传入初始状态
result = graph.invoke({"greeting": "from LangGraph!"})
print(result)  # 打印结果

# 生成图的Mermaid格式可视化PNG
mermaid_png = graph.get_graph(xray=1).draw_mermaid_png(draw_method=MermaidDrawMethod.API)

# 创建输出目录(如果不存在)
output_folder = "."  # 当前目录
os.makedirs(output_folder, exist_ok=True)  # 确保目录存在

# 生成随机文件名并保存PNG图像
filename = os.path.join(output_folder, f"graph_{random.randint(1, 100000)}.png")
with open(filename, 'wb') as f:
    f.write(mermaid_png)  # 写入文件

# 根据操作系统自动打开生成的图像文件
if sys.platform.startswith('darwin'):  # macOS
    subprocess.call(('open', filename))
elif sys.platform.startswith('linux'):  # Linux
    subprocess.call(('xdg-open', filename))
elif sys.platform.startswith('win'):  # Windows
    os.startfile(filename)
