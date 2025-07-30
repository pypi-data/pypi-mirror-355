# 1. 基础异常处理示例
def check_age(age):
    """年龄验证函数"""
    if age < 0:
        raise ValueError("Age cannot be negative")  # 抛出数值异常
    elif age < 18:
        print("Not eligible to vote")  # 未成年提示
    else:
        print("Eligible to vote")  # 成年提示


# 捕获ValueError异常
try:
    check_age(-5)  # 触发负数异常
except ValueError as e:
    print(e)  # 输出异常信息: Age cannot be negative

# 2. 多异常处理示例
try:
    number = int(input("Enter a number: "))  # 可能触发ValueError
    result = 10 / number  # 可能触发ZeroDivisionError
except ValueError:
    print("You must enter a valid integer.")  # 输入非数字处理
except ZeroDivisionError:
    print("You can't divide by zero.")  # 除零处理
else:
    print(f"Result: {result}")  # 无异常时执行
finally:
    print("Execution completed.")  # 无论是否异常都会执行

# 3. 异常链示例
try:
    number = int(input("Enter a number: "))
    result = 10 / number
except ZeroDivisionError as e:
    raise RuntimeError("Failed to divide") from e  # 包装原始异常

# 4. LangGraph节点中的异常处理
from langgraph import Graph, Node


class APIRequestNode(Node):
    def run(self):
        """节点执行方法"""
        try:
            data = self.make_request()  # 可能抛出TimeoutError/ValueError
            self.send_output(data)
        except TimeoutError:
            self.send_output("The request timed out.")  # 超时处理
        except ValueError as e:
            self.send_output(f"Invalid data: {e}")  # 数据异常处理
        finally:
            self.log("Request completed.")  # 最终日志记录


# 构建图并添加节点
graph = Graph()
node = APIRequestNode()
graph.add_node(node)
