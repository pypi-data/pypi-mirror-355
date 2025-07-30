import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables.graph import MermaidDrawMethod, CurveStyle

from display_graph import display_graph


# Define tools
def product_info(product_name: str) -> str:
    """Fetch product information."""
    product_catalog = {
        "iPhone 20": "The latest iPhone features an A15 chip and improved camera.",
        "MacBook": "The new MacBook has an M2 chip and a 14-inch Retina display.",
    }
    return product_catalog.get(product_name, "Sorry, product not found.")


# Initialize the memory saver for single-thread memory
checkpointer = MemorySaver()

# Initialize the language model
llm = ChatOpenAI(model="gpt-4o-mini")

# Create the ReAct agent with the memory saver
graph = create_react_agent(model=llm, tools=[product_info], checkpointer=checkpointer)

# Visualise the graph
display_graph(graph, file_name=os.path.basename(__file__))

# Set up thread configuration to simulate single-threaded memory
config = {"configurable": {"thread_id": "thread-1"}}

# User input: initial inquiry
inputs = {"messages": [("user", "Hi, I'm James. Tell me about the new iPhone 20.")]}
messages = graph.invoke(inputs, config=config)
for message in messages["messages"]:
    message.pretty_print()

# User input: repeated inquiry (memory recall)
inputs2 = {"messages": [("user", "Tell me more about the iPhone 20.")]}
messages2 = graph.invoke(inputs2, config=config)
for message in messages2["messages"]:
    message.pretty_print()
