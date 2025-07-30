import json

from langchain_community.agent_toolkits.json.base import create_json_agent
from langchain_community.agent_toolkits.json.toolkit import JsonToolkit
from langchain_community.tools.json.tool import JsonSpec
from langchain_deepseek import ChatDeepSeek

json_data = {
    "people": [
        {
            "name": "Alice",
            "age": 30,
            "city": "New York",
            "hobbies": ["reading", "painting"],
            "is_student": False
        },
        {
            "name": "Bob",
            "age": 25,
            "city": "San Francisco",
            "hobbies": ["coding", "gaming"],
            "is_student": True
        },
        {
            "name": "Charlie",
            "age": 35,
            "city": "Chicago",
            "hobbies": ["hiking", "photography"],
            "is_student": False
        }
    ],
    "company": {
        "name": "TechCorp",
        "founded": 2010,
        "employees": 500,
        "departments": ["Engineering", "Marketing", "Sales"]
    }
}

llm = ChatDeepSeek(model="deepseek-chat", api_key="sk-fb3e53f786974df3b400a99808b64141")

# 创建 JSON 规范
json_spec = JsonSpec(dict_=json_data, max_value_length=4000)
# 创建 JSON 工具包
json_toolkit = JsonToolkit(spec=json_spec)
# 创建 JSON Agent
json_agent = create_json_agent(
    llm=llm,
    toolkit=json_toolkit,
    verbose=True
)


# 执行查询
def query_json_agent(question):
    print(f"\n查询: {question}")
    # 使用 invoke 替代 run 方法
    response = json_agent.invoke({"input": question})
    print(f"回答: {response['output']}")


# 示例查询
queries = [
    "people 列表中有多少人?",
    "找出所有居住在 'San Francisco' 的人",
    "列出 company 的所有部门",
    "所有 hobby 包含 'coding' 的人",
    "将所有 is_student 为 True 的人的 age 加 1，然后返回更新后的 people 列表"
]

# 执行所有查询
for query in queries:
    query_json_agent(query)


# 从文件加载 JSON 数据
def process_json_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    # 使用文件中的数据创建新的 JSON Agent
    file_spec = JsonSpec(dict_=data, max_value_length=4000)
    file_toolkit = JsonToolkit(spec=file_spec)
    file_agent = create_json_agent(
        llm=llm,
        toolkit=file_toolkit,
        verbose=True
    )

    # 执行查询
    result = file_agent.invoke({"input": "总结这个 JSON 数据的主要内容"})
    return result["output"]

# 示例: 处理外部 JSON 文件
# result = process_json_file("data.json")
# print(f"\n文件分析结果: {result}")
