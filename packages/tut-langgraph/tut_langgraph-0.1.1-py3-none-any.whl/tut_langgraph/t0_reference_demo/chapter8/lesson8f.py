import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import requests

from display_graph import display_graph


# Define the mock APIs for demand and competitor pricing
def get_demand_data(product_id: str) -> dict:
    """Mock demand API to get demand data for a product."""
    # In real use, replace with an actual API call
    return {"product_id": product_id, "demand_level": "high"}


def get_competitor_pricing(product_id: str) -> dict:
    """Mock competitor pricing API."""
    # In real use, replace with an actual API call
    return {"product_id": product_id, "competitor_price": 95.0}


# List of tools for the agent to call
tools = [get_demand_data, get_competitor_pricing]

# Define the agent using the ReAct pattern
model = ChatOpenAI(model="gpt-4")

# Create the ReAct agent with tools for demand and competitor pricing
graph = create_react_agent(model, tools=tools)

# Visualise the graph
display_graph(graph, file_name=os.path.basename(__file__))

# Define the initial state of the agent
initial_messages = [
    ("system", "You are an AI agent that dynamically adjusts product prices based on market demand and competitor prices."),
    ("user", "What should be the price for product ID '12345'?")
]

# Stream agent responses and decisions
inputs = {"messages": initial_messages}

# Simulate the agent reasoning, acting (calling tools), and observing
for state in graph.stream(inputs, stream_mode="values"):
    message = state["messages"][-1]  # Get the latest message in the interaction
    if isinstance(message, tuple):
        print(message)
    else:
        message.pretty_print()  # Print the response from the agent
