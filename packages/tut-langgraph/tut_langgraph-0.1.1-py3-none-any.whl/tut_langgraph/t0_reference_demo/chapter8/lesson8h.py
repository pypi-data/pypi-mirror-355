from typing import (
    Annotated,
    Sequence,
    TypedDict,
)
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import json
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig


# Define the state for product recommendation
class RecommendationState(TypedDict):
    user_id: str  # User identifier
    preference: str  # User's current preference (e.g., genre, category)
    reasoning: str  # Reasoning process from LLM
    recommendation: str  # Final product recommendation
    memory: dict  # User memory to store preferences
    messages: Annotated[Sequence[BaseMessage], add_messages]


from langchain_core.tools import tool


# Tool function: Recommend a product based on the user's preference
@tool
def recommend_product(preference: str) -> str:
    """Recommend a product based on the user's preferences."""
    product_db = {
        "science": "I recommend 'A Brief History of Time' by Stephen Hawking.",
        "technology": "I recommend 'The Innovators' by Walter Isaacson.",
        "fiction": "I recommend 'The Alchemist' by Paulo Coelho."
    }
    return product_db.get(preference, "I recommend exploring our latest products!")


from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage, SystemMessage

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o-mini")
tools = [recommend_product]
llm = llm.bind_tools(tools)


# Tool function: Update the user's memory with the latest preference
def update_memory(state: RecommendationState):
    # Store the user's preference in the memory
    state["memory"][state["user_id"]] = state["preference"]
    return state


# Tool node to handle product recommendation
tools_by_name = {tool.name: tool for tool in tools}


def tool_node(state: RecommendationState):
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
        outputs.append(
            ToolMessage(
                content=json.dumps(tool_result),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": outputs}


# LLM reasoning node to process user input and generate product recommendations
def call_model(state: RecommendationState, config: RunnableConfig):
    system_prompt = SystemMessage(
        content=f"You are a helpful assistant for recommending a product based on the user's preference."
    )
    response = llm.invoke([system_prompt] + state["messages"] + [("user", state["preference"])], config)
    return {"messages": [response]}


# Conditional function to determine whether to call the tool or end
def should_continue(state: RecommendationState):
    last_message = state["messages"][-1]
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"


from langgraph.graph import StateGraph, END, START

workflow = StateGraph(RecommendationState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_node("update_memory", update_memory)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "end": END,
    },
)
workflow.add_edge("tools", "update_memory")
workflow.add_edge("update_memory", "agent")

# Compile the graph
graph = workflow.compile()

# Initialize the agent's state with the user's preference and memory
initial_state = {"messages": [("user", "I'm looking for a book.")], "user_id": "user1", "preference": "science", "memory": {}, "reasoning": ""}

# Run the agent
result = graph.invoke(initial_state)

# Display the final result
print(f"Reasoning: {result['reasoning']}")
print(f"Product Recommendation: {result['messages'][-1].content}")
print(f"Updated Memory: {result['memory']}")


# Helper function to print the conversation
def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()


# Run the agent
print_stream(graph.stream(initial_state, stream_mode="values"))
