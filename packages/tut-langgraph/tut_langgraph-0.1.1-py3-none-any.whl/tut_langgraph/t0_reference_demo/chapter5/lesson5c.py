from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage


# Define a tool to get the weather for a city
@tool
def get_weather(location: str):
    """Fetch the current weather for a specific location."""
    weather_data = {
        "San Francisco": "It's 60 degrees and foggy.",
        "New York": "It's 90 degrees and sunny.",
        "London": "It's 70 degrees and cloudy.",
        "Nairobi": "It's 27 degrees celsius and sunny."
    }
    return weather_data.get(location, "Weather information is unavailable for this location.")


message_with_single_tool_call = AIMessage(
    content="",
    tool_calls=[
        {
            "name": "get_weather",
            "args": {"location": "Nairobi"},
            "id": "tool_call_id",
            "type": "tool_call",
        }
    ],
)
tools = [get_weather]
tool_node = ToolNode(tools)

result = tool_node.invoke({"messages": [message_with_single_tool_call]})
print(result)
