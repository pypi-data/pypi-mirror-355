import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from display_graph import display_graph


# Define tools
def product_info(product_name: str) -> str:
    """Fetch product information."""
    product_catalog = {
        "iPhone": "The latest iPhone features an A15 chip and improved camera.",
        "MacBook": "The new MacBook has an M2 chip and a 14-inch Retina display.",
    }
    return product_catalog.get(product_name, "Sorry, product not found.")


def check_stock(product_name: str) -> str:
    """Check product stock availability."""
    stock_data = {
        "iPhone": "In stock.",
        "MacBook": "Out of stock.",
    }
    return stock_data.get(product_name, "Stock information unavailable.")


# Initialize the memory saver for single-thread memory
checkpointer = MemorySaver()

# Initialize the language model
llm = ChatOpenAI(model="gpt-4o-mini")

# Create the ReAct agent with tools and memory
tools = [product_info, check_stock]
graph = create_react_agent(model=llm, tools=tools, checkpointer=checkpointer)

# Visualise the graph
display_graph(graph, file_name=os.path.basename(__file__))

# Set up thread configuration for single-thread memory
config = {"configurable": {"thread_id": "thread-3"}}

# User input: initial inquiry about product information
inputs = {"messages": [("user", "Tell me about the new iPhone.")]}
messages = graph.invoke(inputs, config=config)
for message in messages["messages"]:
    print(message.content)

# User input: follow-up inquiry about stock availability (memory recall and dynamic decision-making)
inputs2 = {"messages": [("user", "Is the iPhone in stock?")]}
messages2 = graph.invoke(inputs2, config=config)
for message in messages2["messages"]:
    print(message.content)
