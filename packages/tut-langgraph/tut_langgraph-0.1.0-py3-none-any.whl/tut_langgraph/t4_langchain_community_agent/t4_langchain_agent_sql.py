from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_deepseek import ChatDeepSeek

db = SQLDatabase.from_uri("sqlite:///student_database.db")
llm = ChatDeepSeek(model="deepseek-chat", api_key="sk-fb3e53f786974df3b400a99808b64141")
agent_executor = create_sql_agent(llm, db=db, agent_type="tool-calling", verbose=True)
result = agent_executor.invoke({"input": "韩刚的手机号是多少？大学物理最高成绩是多少？"})
print(result)
