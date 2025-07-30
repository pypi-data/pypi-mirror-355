# 导入必要的库
import os  # 用于文件和目录操作
import subprocess  # 用于调用系统命令
import sys  # 用于系统相关操作
from langchain_core.runnables.graph import MermaidDrawMethod  # 用于图形可视化
import random  # 用于生成随机数


def display_graph(graph, output_folder="output"):
    """
    可视化LangGraph图结构并自动打开生成的图片

    参数:
        graph: 要可视化的LangGraph图对象
        output_folder: 图片输出目录(默认为"output")
    """
    # 将图转换为Mermaid格式的PNG图片
    mermaid_png = graph.get_graph(xray=1).draw_mermaid_png(draw_method=MermaidDrawMethod.API)

    # 创建输出目录(如果不存在)
    output_folder = "."  # 当前目录
    os.makedirs(output_folder, exist_ok=True)  # 确保目录存在

    # 生成随机文件名并保存PNG图像
    filename = os.path.join(output_folder, f"graph_{random.randint(1, 100000)}.png")
    with open(filename, 'wb') as f:  # 以二进制写入模式打开文件
        f.write(mermaid_png)  # 写入图像数据

    # 根据操作系统自动打开生成的图像文件
    if sys.platform.startswith('darwin'):  # macOS系统
        subprocess.call(('open', filename))  # 使用open命令打开
    elif sys.platform.startswith('linux'):  # Linux系统
        subprocess.call(('xdg-open', filename))  # 使用xdg-open命令打开
    elif sys.platform.startswith('win'):  # Windows系统
        os.startfile(filename)  # 使用系统关联程序打开
