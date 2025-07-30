import asyncio
from pathlib import Path

from langchain_deepseek import ChatDeepSeek
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key="sk-fb3e53f786974df3b400a99808b64141",
    # openai_api_base="https://api.deepseek.com/v1",
    openai_api_base="https://api.deepseek.com/chat/completions",
)

current_path = Path(__file__).resolve()
print("当前文件绝对路径：", current_path)

parent_dir = current_path.parent.parent.parent.parent
print("上级目录：", parent_dir)


async def main():
    client = MultiServerMCPClient(
        {
            "math": {
                "command": rf"{parent_dir}\.venv\Scripts\python.exe",
                "args": [rf"{current_path.parent}\math.py"],
                "transport": "stdio",
            },
            "weather": {
                # 确保你的天气服务器在8000端口上运行
                "url": "http://127.0.0.1:8000/mcp",
                "transport": "streamable_http",
            }
        }
    )

    tools = await client.get_tools()
    agent = create_react_agent(
        model=llm,
        tools=tools
    )
    print(f"{'>' * 10}")
    math_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]}
    )
    print("Math Response:", math_response)
    print(f"{'<' * 10}")

    print(f"{'>' * 10}")
    weather_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what is the weather in nyc?"}]}
    )
    print("Weather Response:", weather_response)
    print(f"{'<' * 10}")


# 运行异步函数
if __name__ == "__main__":
    asyncio.run(main())
