# Import necessary libraries
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
import os

# Step 1: Load the API key from .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


# Step 2: Define the tool to get weather information
@tool
def get_weather(location: str):
    """Fetch the current weather for a specific location."""
    weather_data = {
        "San Francisco": "It's 60 degrees and foggy.",
        "New York": "It's 90 degrees and sunny.",
        "London": "It's 70 degrees and cloudy."
    }
    return weather_data.get(location, "Weather information is unavailable for this location.")


# Step 3: Initialize the LLM (OpenAI's GPT-4o-mini model) and bind the tool
tool_node = ToolNode([get_weather], handle_tool_errors=False)
model = ChatOpenAI(model="gpt-4o-mini", api_key=api_key).bind_tools([get_weather])


# Step 4: Function to handle user queries and process LLM + tool results
def call_llm(state: MessagesState):
    messages = state["messages"]
    # The LLM will decide if it should invoke a tool based on the user input
    response = model.invoke(messages[-1].content)

    # If the LLM generates a tool call, handle it
    if response.tool_calls:
        tool_result = tool_node.invoke({"messages": [response]})
        # Append the tool's output to the response message
        tool_message = tool_result["messages"][-1].content
        response.content += f"\nTool Result: {tool_message}"

    return {"messages": [response]}


# Step 5: Create the LangGraph workflow
workflow = StateGraph(MessagesState)

# Step 6: Add the LLM node to the workflow
workflow.add_node("call_llm", call_llm)

# Step 7: Define edges to control the flow (LLM -> End)
workflow.add_edge(START, "call_llm")
workflow.add_edge("call_llm", END)

# Step 8: Compile the workflow
app = workflow.compile()


# Step 9: Function to interact with the agent continuously
def interact_with_agent():
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Ending the conversation.")
            break

        # Prepare the user input for processing
        input_message = {
            "messages": [("human", user_input)]
        }

        # Process the input through the workflow and return the response
        for chunk in app.stream(input_message, stream_mode="values"):
            chunk["messages"][-1].pretty_print()


# Step 10: Start interacting with the AI agent
interact_with_agent()
