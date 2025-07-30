# 字符串基本操作示例

# 1. 字符串拼接
greeting = "Hello" + " " + "World"  # 使用加号连接字符串
print(greeting)  # 输出: Hello World

# 2. 字符串重复
echo = "Echo " * 3  # 使用乘号重复字符串
print(echo)  # 输出: Echo Echo Echo

# 3. 字符串切片
text = "LangGraph"
# 提取前4个字符(索引0到3)
print(text[0:4])  # 输出: Lang
# 提取最后5个字符(从倒数第5个到末尾)
print(text[-5:])  # 输出: Graph

# 4. f-string格式化
name = "Alice"
age = 30
# 使用f-string插入变量值
print(f"My name is {name}, and I am {age} years old.")  # 输出带变量的完整句子

# 5. 字符串查找
text = "LangGraph is a powerful framework."
# 查找子串位置(返回起始索引)
print(text.find("powerful"))  # 输出: 13
# 检查子串是否存在(返回布尔值)
print("Graph" in text)  # 输出: True

# 6. 字符串分割与合并
# 按空格分割为列表
words = text.split(" ")  # 输出: ['LangGraph', 'is', 'a', 'powerful', 'framework.']
# 将列表用空格合并为字符串
sentence = " ".join(words)  # 输出原始字符串

# 7. 字符串大小写转换
text = "LangGraph"
print(text.upper())  # 全大写: LANGGRAPH
print(text.lower())  # 全小写: langgraph
print(text.title())  # 标题格式: Langgraph