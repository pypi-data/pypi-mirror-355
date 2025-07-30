import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from display_graph import display_graph


# Define tools
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b


def divide(a: int, b: int) -> float:
    """Divide a and b.

    Args:
        a: first int
        b: second int
    """
    return a / b


tools = [add, multiply]

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o-mini")

# Create the ReAct agent
graph = create_react_agent(model=llm, tools=tools)

# Visualise the graph
display_graph(graph, file_name=os.path.basename(__file__))

# User input
inputs = {"messages": [("user", "Add 32 and 4. Multiply the result by 2 and divide by 4.")]}

# Run the ReAct agent
messages = graph.invoke(inputs)
for message in messages["messages"]:
    message.pretty_print()
