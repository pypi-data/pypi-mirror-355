# 导入必要的库
from typing_extensions import TypedDict  # 用于定义类型化的字典
from langgraph.graph import StateGraph, START, END  # LangGraph核心组件
from langchain_core.runnables.graph import MermaidDrawMethod  # 图形可视化方法
import os  # 文件系统操作
import subprocess  # 系统命令执行
import sys  # 系统相关功能
import random  # 随机数生成


# 定义状态结构，使用TypedDict确保类型安全
class HelloWorldState(TypedDict):
    greeting: str  # 存储问候消息的字段


# 定义节点处理函数
def hello_world_node(state: HelloWorldState):
    # 在原有问候语前添加"Hello World"
    state["greeting"] = "Hello World, " + state["greeting"]
    return state  # 返回修改后的状态


# 初始化图构建器，指定状态类型
builder = StateGraph(HelloWorldState)
# 添加名为"greet"的节点，关联处理函数
builder.add_node("greet", hello_world_node)

# 定义执行流程的边(连接关系)
builder.add_edge(START, "greet")  # 从START连接到greet节点
builder.add_edge("greet", END)  # 从greet节点连接到END

# 编译图结构
graph = builder.compile()
# 执行图，传入初始状态
result = graph.invoke({"greeting": "from LangGraph!"})

# 输出执行结果
print(result)  # 预期输出: {'greeting': 'Hello World, from LangGraph!'}

# 生成图的Mermaid格式可视化PNG
mermaid_png = graph.get_graph(xray=1).draw_mermaid_png(draw_method=MermaidDrawMethod.API)

# 确保输出目录存在
output_folder = "."  # 当前目录
os.makedirs(output_folder, exist_ok=True)

# 生成随机文件名并保存图像
filename = os.path.join(output_folder, f"graph_{random.randint(1, 100000)}.png")
with open(filename, 'wb') as f:  # 二进制写入模式
    f.write(mermaid_png)  # 写入图像数据

# 根据操作系统自动打开图像文件
if sys.platform.startswith('darwin'):  # macOS系统
    subprocess.call(('open', filename))
elif sys.platform.startswith('linux'):  # Linux系统
    subprocess.call(('xdg-open', filename))
elif sys.platform.startswith('win'):  # Windows系统
    os.startfile(filename)
