# 参考链接：
# https://langchain-ai.github.io/langgraph/tutorials/get-started/1-build-basic-chatbot/#3-add-a-node

from typing import Annotated
import os
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from IPython.display import Image, display

# 目前使用的是DeepSeek模型+ChatOpenAI会报错，不清楚是不是模型侧的问题。后续研究下
# llm = ChatOpenAI(
#     model="deepseek-chat",
#     api_key="sk-fb3e53f786974df3b400a99808b64141",
#     base_url="https://api.deepseek.com/chat/completions",
# )


# 测试通过，可以使用DeepSeek模型
llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key="sk-fb3e53f786974df3b400a99808b64141",
    # openai_api_base="https://api.deepseek.com/chat/completions",
)


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()

try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass


def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break
