import asyncio
from pathlib import Path
from typing import TypedDict, List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_deepseek import ChatDeepSeek
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

# Initialize the LLM
llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key="sk-fb3e53f786974df3b400a99808b64141",
    openai_api_base="https://api.deepseek.com/chat/completions",
)

# Get the current file path and parent directory
current_path = Path(__file__).resolve()
print("当前文件绝对路径：", current_path)
parent_dir = current_path.parent.parent.parent.parent
print("上级目录：", parent_dir)


# Define the state for the graph
class AgentState(TypedDict):
    messages: List[Dict[str, Any]]


# Define the agent node
async def agent_node(state: AgentState) -> AgentState:
    messages = state["messages"]
    last_message = messages[-1]

    # Prepare the prompt for the LLM
    system_prompt = """You are a helpful assistant that can use tools to answer questions.
    Available tools:
    - math: For mathematical calculations
    - weather: For weather information

    If the query requires a tool, respond with a JSON object like:
    {"tool": "tool_name", "input": {"param1": "value1", ...}}

    If no tool is needed, provide the answer directly as a string."""

    response = await llm.ainvoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": last_message["content"]}
    ])

    # Parse the LLM response
    content = response.content
    try:
        import json
        tool_call = json.loads(content)
        if isinstance(tool_call, dict) and "tool" in tool_call:
            messages.append({"role": "assistant", "content": "", "tool_calls": [tool_call]})
        else:
            messages.append({"role": "assistant", "content": content})
    except json.JSONDecodeError:
        messages.append({"role": "assistant", "content": content})

    return {"messages": messages}


# Define the tool node
async def tool_node(state: AgentState, tools: List[Any]) -> AgentState:
    messages = state["messages"]
    last_message = messages[-1]

    if "tool_calls" in last_message:
        tool_call = last_message["tool_calls"][0]
        tool_name = tool_call["tool"]

        # Find the appropriate tool
        for tool in tools:
            if tool.name == tool_name:
                try:
                    result = await tool.ainvoke(tool_call["input"])
                    messages.append({"role": "tool", "content": str(result), "tool_call_id": tool_name})
                except Exception as e:
                    messages.append({"role": "tool", "content": f"Error: {str(e)}", "tool_call_id": tool_name})
                break
        else:
            messages.append({"role": "tool", "content": f"Error: Tool {tool_name} not found", "tool_call_id": tool_name})
    else:
        # No tool call, proceed to final response
        pass

    return {"messages": messages}


# Define the response node
async def response_node(state: AgentState) -> AgentState:
    messages = state["messages"]
    tool_results = [msg for msg in messages if msg["role"] == "tool"]

    if tool_results:
        # Combine tool results into a final response
        final_prompt = """Based on the tool results and the conversation history, provide a final answer to the user's query."""
        response = await llm.ainvoke([
            {"role": "system", "content": final_prompt},
            *messages
        ])
        messages.append({"role": "assistant", "content": response.content})

    return {"messages": messages}


# Define the routing logic
def should_continue(state: AgentState) -> str:
    messages = state["messages"]
    last_message = messages[-1]

    if "tool_calls" in last_message:
        return "tool"
    elif any(msg["role"] == "tool" for msg in messages):
        return "response"
    else:
        return END


# Build the graph
async def build_graph(tools: List[Any]) -> CompiledStateGraph:
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tool", lambda state: tool_node(state, tools))
    workflow.add_node("response", response_node)

    # Define edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tool": "tool",
            END: END
        }
    )
    workflow.add_edge("tool", "response")
    workflow.add_edge("response", END)

    return workflow.compile()


# Main execution
async def main():
    client = MultiServerMCPClient(
        {
            "math": {
                "command": rf"{parent_dir}\.venv\Scripts\python.exe",
                "args": [rf"{current_path.parent}\math.py"],
                "transport": "stdio",
            },
            "weather": {
                "url": "http://127.0.0.1:8000/mcp",
                "transport": "streamable_http",
            }
        }
    )

    tools = await client.get_tools()
    logger.info(f"tools: {len(tools)}")

    # Build the custom graph
    graph = await build_graph(tools)

    # Test math query
    print(f"{'>' * 10}")
    math_response = await graph.ainvoke(
        {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]}
    )
    print("Math Response:", math_response["messages"][-1]["content"])
    print(f"{'<' * 10}")

    # Test weather query
    print(f"{'>' * 10}")
    weather_response = await graph.ainvoke(
        {"messages": [{"role": "user", "content": "what is the weather in nyc?"}]}
    )
    print("Weather Response:", weather_response["messages"][-1]["content"])
    print(f"{'<' * 10}")


# Run the async function
if __name__ == "__main__":
    asyncio.run(main())
