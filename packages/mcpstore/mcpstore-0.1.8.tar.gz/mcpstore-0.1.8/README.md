# MCPStore

## 项目背景与价值

在当前的智能体开发生态中，工具管理和集成往往是一个复杂而繁琐的问题。每开发一个新的智能体或 LangChain，都需要重新配置和维护 MCP（Model Control Protocol）相关的设置，这不仅增加了开发成本，还容易导致配置不一致和维护困难的问题。

MCPStore 正是为解决这个痛点而生。它提供了一个中心化的工具管理解决方案，使得智能体开发者可以：
- 🎯 专注于业务逻辑，而不是工具集成
- 🛒 像"购物"一样轻松地订阅和管理所需的工具
- 🔄 统一管理和复用工具配置
- 📦 一次配置，多处使用

通过 MCPStore，我们将 MCP 的复杂性封装在一个易用的接口之后，让智能体的工具调用变得如同在"商店"中选购一样简单。

## 特性

- 🚀 简单易用的 API 接口
- 🛠 灵活的服务注册机制
- 🔌 插件化的工具管理
- 🌐 支持 Web API 和实例化对象两种使用方式
- 💡 智能的工具订阅和管理
- 🔄 内置健康检查机制
- 🔗 计划支持与 LangChain 无缝集成

## 安装

```bash
pip install mcpstore
```

## 快速开始

### 1. 通过实例化对象使用

```python
from mcpstore.core.store import McpStore
from mcpstore.core.orchestrator import MCPOrchestrator
from mcpstore.core.registry import ServiceRegistry
from mcpstore.plugins.json_mcp import MCPConfig

# 初始化核心组件
registry = ServiceRegistry()
orchestrator = MCPOrchestrator({
    "timing": {
        "heartbeat_interval_seconds": 60,
        "heartbeat_timeout_seconds": 180,
        "http_timeout_seconds": 10,
        "command_timeout_seconds": 10
    }
}, registry)
mcp_config = MCPConfig()
store = McpStore(orchestrator, mcp_config)

# 注册服务
store_response = await store.register_json_service()

# 获取工具列表
tools = store.list_tools()
```

### 2. 通过 Web API 使用

启动 Web 服务：
```bash
python -m mcpstore.cli.web
```

API 端点示例：
- POST /register_service - 注册服务
- GET /list_tools - 获取工具列表
- POST /execute_tool - 调用工具
- GET /list_services - 获取服务列表
- GET /health - 健康检查

## 核心概念

### Store（商店）
- Store 是整个系统的核心，负责管理所有服务和工具
- 提供服务注册、工具调用等核心功能
- 支持健康检查和状态监控

### Service（服务）
- 可以通过 JSON 配置注册的功能单元
- 每个服务可以提供多个工具
- 支持服务状态监控和健康检查

### Agent（智能体）
- 使用 Store 服务的客户端
- 可以选择性订阅所需的服务和工具
- 通过 client_id 进行身份识别和权限管理

### Tool（工具）
- 具体的功能实现单元
- 支持参数配置和结果返回
- 可以被多个 Agent 复用

## 项目结构

```
mcpstore/
├── core/          # 核心功能模块
├── data/          # 数据存储相关
├── scripts/       # 实用脚本工具
├── cli/           # 命令行工具
├── plugins/       # 插件扩展模块
├── config/        # 配置管理
└── __init__.py    # 包初始化文件
```

## 配置说明

MCPStore 使用 JSON 格式的配置文件来管理服务和工具。配置文件示例：

```json
{
    "services": {
        "weather_service": {
            "tools": ["get_weather", "get_air_quality"],
            "config": {
                "api_key": "your_api_key"
            }
        }
    }
}
```

## 使用场景

1. **智能体工具管理**
   - 为智能体提供工具订阅和管理
   - 简化工具调用流程
   - 统一管理工具权限

2. **服务集成平台**
   - 统一管理多个服务
   - 提供服务健康监控
   - 支持服务动态注册

3. **API 网关**
   - 提供统一的 API 接口
   - 管理服务调用
   - 监控服务状态

## 开发计划

- [ ] 支持与 LangChain 的无缝集成
- [ ] 增强服务监控和告警功能
- [ ] 添加更多预置工具和服务
- [ ] 优化性能和可扩展性
- [ ] 完善文档和示例

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

[许可证类型]

## 联系方式

[联系方式信息]

## 为什么选择 MCPStore？

### 开发痛点
- 🔧 传统方式下，每个智能体都需要独立维护 MCP 配置
- 📝 重复的工具集成工作占用大量开发时间
- 🔍 工具版本和配置的不一致性难以管理
- 🔀 多个智能体使用相同工具时配置冗余

### MCPStore 的解决方案
- 🏪 提供"商店"式的工具管理体验
- 🎯 一次配置，多处复用
- 🔄 统一的版本控制和配置管理
- 🛡️ 集中化的权限和访问控制
- 📊 统一的监控和管理界面

### 使用效果
- ⚡ 显著减少工具集成时间
- 🎯 降低维护成本
- 💡 提高开发效率
- 🔐 更好的安全性和可控性

## 典型应用场景

### 1. 智能体快速开发
当你需要开发一个新的智能体时，不再需要从零开始配置工具链：
```python
from mcpstore.core.store import McpStore

# 初始化 store
store = McpStore()

# 注册所需服务
agent_id = await store.register_json_service(service_names=['weather', 'maps', 'search'])

# 直接开始使用工具
tools = store.list_tools(agent_id)
```

### 2. LangChain 集成
计划中的 LangChain 集成将使工具管理更加简单：
```python
from mcpstore.integrations.langchain import MCPStoreLangChainTools

# 将 store 转换为 LangChain 工具
tools = MCPStoreLangChainTools.from_store(store, agent_id)

# 在 LangChain 中使用
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)
```
