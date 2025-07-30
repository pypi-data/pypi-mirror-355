# 多智能体系统模拟框架

class Agent:
    """智能体基类，代表具有能力和关系的个体"""

    def __init__(self, name, capabilities):
        """初始化智能体
        Args:
            name: 智能体名称
            capabilities: 能力列表，如['talk','walk']
        """
        self.name = name
        self.capabilities = capabilities  # 能力集合
        self.relationships = {}  # 关系映射表

    def add_relationship(self, other_agent, relationship_type):
        """添加与其他智能体的关系
        Args:
            other_agent: 目标智能体对象
            relationship_type: 关系类型字符串
        """
        self.relationships[other_agent.name] = relationship_type

    def interact(self, other_agent, action):
        """与其他智能体交互
        Args:
            other_agent: 交互目标对象
            action: 尝试执行的动作
        """
        if action in self.capabilities:
            print(f"{self.name}与{other_agent.name}进行{action}交互")
        else:
            print(f"{self.name}不具备{action}能力")

    def __str__(self):
        """可视化智能体信息"""
        return f"智能体[{self.name}] 能力: {', '.join(self.capabilities)}"


class Environment:
    """多智能体环境容器"""

    def __init__(self):
        self.agents = {}  # 智能体字典 {name: agent_obj}

    def add_agent(self, agent):
        """添加智能体到环境
        Args:
            agent: Agent类实例
        """
        if agent.name not in self.agents:
            self.agents[agent.name] = agent
        else:
            print(f"智能体{agent.name}已存在")

    def simulate_interaction(self, agent1_name, agent2_name, action):
        """模拟两个智能体的交互
        Args:
            agent1_name: 发起方智能体名
            agent2_name: 接收方智能体名
            action: 交互动作
        """
        if agent1_name in self.agents and agent2_name in self.agents:
            self.agents[agent1_name].interact(
                self.agents[agent2_name], action)
        else:
            print("智能体不存在")

    def __str__(self):
        """可视化环境状态"""
        agent_info = "\n".join([str(agent) for agent in self.agents.values()])
        return f"环境包含智能体:\n{agent_info}"


# === 示例用法 ===
env = Environment()  # 创建环境

# 创建两个具有不同能力的智能体
agent1 = Agent("Alice", ["talk", "walk"])  # 能交谈和行走
agent2 = Agent("Bob", ["talk", "run"])  # 能交谈和奔跑

# 添加到环境
env.add_agent(agent1)
env.add_agent(agent2)

# 建立双向朋友关系
agent1.add_relationship(agent2, "friend")
agent2.add_relationship(agent1, "friend")

# 模拟交互
env.simulate_interaction("Alice", "Bob", "talk")  # 成功交互
env.simulate_interaction("Alice", "Bob", "run")  # 失败交互

# 打印智能体信息
print(agent1)
print(agent2)
