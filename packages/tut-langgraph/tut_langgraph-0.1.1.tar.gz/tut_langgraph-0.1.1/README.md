# LangChain & LangGraph 学习项目

## 核心概念

### LangChain
LangChain 是一个用于构建基于语言模型应用的框架，主要功能包括：
- **组件化架构**：提供模块化组件（LLMs、记忆、索引等）
- **链式调用**：将多个组件连接成工作流（Chains）
- **记忆功能**：支持对话历史管理
- **数据增强**：可与外部数据源集成（Retrieval-Augmented Generation）
- **工具集成**：支持调用外部API和工具

### LangGraph
LangGraph 是建立在LangChain之上的框架，专注于：
- **状态机模型**：基于状态转换的流程控制
- **循环工作流**：支持多轮对话和复杂流程
- **分布式执行**：可扩展的分布式任务处理
- **可视化调试**：提供流程可视化工具

## API参考
langchain api
https://python.langchain.com/api_reference/reference.html

langgraph api
https://langchain-ai.github.io/langgraph/concepts/why-langgraph/

## 安装
```bash
uv build
```

## 技术栈

### 核心框架
- LangChain (v0.3.25+)
- LangGraph (v0.4.8+)

### 主要模块
- **语言模型集成**:
  - [x] langchain-openai (OpenAI接口)
  - [x] langchain-google-genai (Google Gemini接口)
  - [x] langchain-deepseek (DeepSeek模型)
  - [x] langchain-nvidia-ai-endpoints (NVIDIA接口)

- **数据连接器**:
  - [x] langchain-chroma (向量数据库)
  - [x] langchain-community (社区贡献连接器)
  - [x] psycopg2-binary (PostgreSQL连接)

- **工具扩展**:
  - [x] yfinance (金融数据)
  - [x] arxiv (学术论文)
  - [x] Faker (测试数据生成)

- **部署与监控**:
  - [x] Flask + Flask-SocketIO (Web服务)
  - [x] Gradio (快速UI构建)
  - [x] watchdog (文件监控)
  - [x] loguru (日志记录)
