"""
MCPStore 使用示例
展示如何使用新的基于上下文的 API
"""

import asyncio
from mcpstore.core.store import MCPStore
from mcpstore.core.orchestrator import MCPOrchestrator
from mcpstore.core.registry import ServiceRegistry
from mcpstore.plugins.json_mcp import MCPConfig

async def main():
    print("\n===== MCPStore 使用示例 (新版API) =====\n")

    # === 1. 初始化 ===
    print("1. 初始化 MCPStore")
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
    store = MCPStore(orchestrator, mcp_config)
    print("   ✓ 初始化完成")

    # === 2. 商店级别操作 ===
    print("\n2. 商店级别操作示例")
    
    # 2.1 使用链式调用
    print("\n2.1 链式调用方式")
    all_services = await store.for_store().list_services()
    print(f"   ✓ 获取到 {len(all_services)} 个服务")
    
    await store.for_store().add_service(['weather', 'maps'])
    print("   ✓ 添加服务成功")
    
    # 2.2 保存上下文重用
    print("\n2.2 保存上下文重用")
    store_ctx = store.for_store()
    services = await store_ctx.list_services()
    tools = await store_ctx.list_tools()
    health = store_ctx.check_services()
    print(f"   ✓ 商店共有 {len(services)} 个服务, {len(tools)} 个工具")
    print(f"   ✓ 服务健康状态: {health}")

    # === 3. Agent级别操作 ===
    print("\n3. Agent级别操作示例")
    
    # 3.1 链式调用
    print("\n3.1 链式调用方式")
    agent_id = "test_agent_123"
    agent_services = await store.for_agent(agent_id).list_services()
    print(f"   ✓ Agent订阅了 {len(agent_services)} 个服务")
    
    await store.for_agent(agent_id).add_service(['news'])
    print("   ✓ Agent订阅新服务成功")
    
    # 3.2 保存上下文重用
    print("\n3.2 保存上下文重用")
    agent_ctx = store.for_agent(agent_id)
    my_services = await agent_ctx.list_services()
    my_tools = await agent_ctx.list_tools()
    my_health = agent_ctx.check_services()
    print(f"   ✓ Agent可用服务: {len(my_services)}")
    print(f"   ✓ Agent可用工具: {len(my_tools)}")
    print(f"   ✓ Agent服务健康状态: {my_health}")

    # === 4. 工具使用 ===
    print("\n4. 工具使用示例")
    result = await store.use_tool('get_weather', {'city': '北京'})
    print(f"   ✓ 工具调用结果: {result}")

    print("\n===== 示例完成 =====")

if __name__ == "__main__":
    asyncio.run(main()) 
