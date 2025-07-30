"""
消息图示例代码
演示如何使用LangGraph创建包含chatbot和search节点的消息处理流程
"""

# 导入必要的消息类型和图构建器
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph.message import MessageGraph

# 初始化消息图构建器
builder = MessageGraph()

"""
定义chatbot节点
该节点接收用户消息并返回AI响应，包含工具调用信息
"""
builder.add_node(
    "chatbot",
    lambda messages: [
        AIMessage(
            # AI生成的问候语
            content="Hello!",
            # 指定要调用的工具信息
            tool_calls=[
                {
                    "id": "123",
                    "name": "search",
                    "args": {"query": "X"},
                },
            ]
        )
    ],
)

"""
定义search节点
模拟执行搜索工具并返回结果
"""
builder.add_node(
    "search",
    lambda messages: [
        ToolMessage(
            content="Searching...",
            tool_call_id="123",
        )
    ]
)

# 配置图的工作流程
builder.set_entry_point("chatbot")  # 设置起始节点
builder.add_edge("chatbot", "search")  # 连接节点
builder.set_finish_point("search")  # 设置结束节点

# 执行图并打印结果
result = builder.compile().invoke([
    HumanMessage(content="Hi here, Can you search for X?")
])
print(result)
