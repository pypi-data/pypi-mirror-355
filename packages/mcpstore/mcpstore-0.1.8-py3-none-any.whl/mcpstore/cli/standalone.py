#!/usr/bin/env python
"""
独立运行MCP服务注册与连接
不依赖FastAPI，可直接从命令行启动
"""

import asyncio
import logging
import os
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# 导入必要的模块
try:
    # 尝试直接导入(相对导入)
    from mcpstore.core.orchestrator import MCPOrchestrator
    from mcpstore.core.registry import ServiceRegistry
    from mcpstore.plugins.json_mcp import MCPConfig
    from mcpstore.core.models.service import TransportType
except ImportError:
    # 尝试从src导入(绝对导入)
    from src.mcpstore.core.orchestrator import MCPOrchestrator
    from src.mcpstore.core.registry import ServiceRegistry
    from src.mcpstore.plugins.json_mcp import MCPConfig
    from src.mcpstore.core.models.service import TransportType

from fastmcp import Client
from fastmcp.client.transports import (
    StdioTransport,
    NodeStdioTransport,
    PythonStdioTransport
)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class MCPStandalone:
    """MCP独立运行模式"""
    
    def __init__(self, config_path: str = None, debug: bool = False):
        """
        初始化MCP独立运行模式
        
        Args:
            config_path: MCP配置文件路径，默认使用标准路径
            debug: 是否启用调试模式
        """
        # 设置日志级别
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            # 启用所有相关日志
            loggers = [
                'fastmcp', 'mcp', 'httpx', 'asyncio',
                'mcp.client.stdio', 'mcp.client.transports',
                'mcpstore'
            ]
            for logger_name in loggers:
                logging.getLogger(logger_name).setLevel(logging.DEBUG)
        
        # 创建配置对象
        self.config = {
            "timing": {
                "heartbeat_interval_seconds": 60,
                "heartbeat_timeout_seconds": 180,
                "reconnection_interval_seconds": 60,
                "http_timeout_seconds": 10,
                "command_timeout_seconds": 10
            }
        }
        
        # 创建MCP配置
        self.mcp_config = MCPConfig(json_path=config_path)
        
        # 创建服务注册表
        self.registry = ServiceRegistry()
        
        # 创建编排器
        self.orchestrator = MCPOrchestrator(self.config, self.registry)
        self.orchestrator.mcp_config = self.mcp_config
    
    async def register_services(self) -> Dict[str, Any]:
        """
        注册MCP配置中的所有服务
        
        Returns:
            注册结果字典
        """
        config = self.mcp_config.load_config()
        logger.info(f"加载了MCP配置: {len(config.get('mcpServers', {}))}个服务")
        
        results = await self.orchestrator.register_json_services(config)
        
        # 输出结果摘要
        total_success = results.get("total_success", 0)
        total_failure = results.get("total_failure", 0)
        logger.info(f"服务注册完成: 成功 {total_success}, 失败 {total_failure}")
        
        # 如果有成功的服务，打印服务和工具信息
        if total_success > 0:
            print("\n=== 已注册的服务和工具 ===")
            for service_name, service_result in results.get("services", {}).items():
                if service_result.get("status") == "success":
                    print(f"服务: {service_name}")
                    
                    # 获取该服务的工具列表
                    tools = self.registry.get_tools_for_service(service_name)
                    if tools:
                        print(f"  工具 ({len(tools)}):")
                        for tool_name in tools:
                            print(f"    - {tool_name}")
                    print()
        
        return results
    
    async def connect_service(self, service_name: str) -> bool:
        """
        连接到指定的MCP服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            连接是否成功
        """
        # 获取服务配置
        service_config = self.mcp_config.get_service_config(service_name)
        
        if not service_config:
            logger.error(f"服务 '{service_name}' 不存在于配置中")
            return False
        
        logger.info(f"尝试连接服务: {service_name}")
        
        # 根据服务类型选择连接方法
        if "url" in service_config:
            # URL服务，使用HTTP连接
            success, client = await self.orchestrator.is_service_healthy(service_name, service_config)
            if success:
                logger.info(f"成功连接到URL服务: {service_name}")
                async with client:
                    tools = await client.list_tools()
                    logger.info(f"获取到 {len(tools)} 个工具")
                    for tool in tools:
                        logger.info(f"  工具: {tool.name}")
                return True
            else:
                logger.error(f"连接URL服务失败: {service_name}")
                return False
        elif "command" in service_config:
            # Studio服务，使用connect_studio_service方法
            success, client, tool_definitions = await self.orchestrator.connect_studio_service(
                service_name, service_config
            )
            if success:
                logger.info(f"成功连接到Studio服务: {service_name}")
                logger.info(f"获取到 {len(tool_definitions)} 个工具")
                for tool in tool_definitions:
                    logger.info(f"  工具: {tool.get('name')}")
                return True
            else:
                logger.error(f"连接Studio服务失败: {service_name}")
                return False
        else:
            logger.error(f"未知的服务类型: {service_name}")
            return False

    async def test_direct_node_transport(self, script_path: str, env: Optional[Dict[str, str]] = None) -> bool:
        """
        直接测试NodeStdioTransport
        
        Args:
            script_path: Node.js脚本路径
            env: 环境变量
            
        Returns:
            测试是否成功
        """
        try:
            logger.info(f"直接测试NodeStdioTransport: {script_path}")
            
            # 默认环境变量
            if env is None:
                env = {'DEBUG': '*'}
            
            # 使用NodeStdioTransport
            transport = NodeStdioTransport(
                command_args=[script_path],
                env=env
            )
            
            logger.info("创建Client...")
            client = Client(transport)
            
            logger.info("尝试连接...")
            async with client:
                logger.info("连接成功！")
                
                # 尝试列出工具
                logger.info("列出工具...")
                tools = await client.list_tools()
                logger.info(f"成功连接，找到 {len(tools)} 个工具")
                
                for tool in tools:
                    logger.info(f"  工具: {tool.name}: {tool.description}")
                
                return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            import traceback
            traceback.print_exc()
            return False


# 为Typer命令行创建的异步执行函数
async def run_standalone(config_path: str = None, 
                        debug: bool = False,
                        service_name: str = None,
                        test_node_path: str = None) -> int:
    """
    运行独立模式的异步函数
    
    Args:
        config_path: 配置文件路径
        debug: 是否启用调试模式
        service_name: 要测试的服务名称
        test_node_path: 要测试的Node.js脚本路径
        
    Returns:
        退出码：0表示成功，1表示失败
    """
    # 设置Windows事件循环策略
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        logger.info("已设置Windows ProactorEventLoop策略")
    
    # 创建MCP独立运行实例
    mcp = MCPStandalone(config_path=config_path, debug=debug)
    
    # 执行相应的操作
    if test_node_path:
        # 直接测试Node.js脚本
        success = await mcp.test_direct_node_transport(test_node_path)
        return 0 if success else 1
    elif service_name:
        # 连接特定服务
        success = await mcp.connect_service(service_name)
        return 0 if success else 1
    else:
        # 注册所有服务
        results = await mcp.register_services()
        return 0 if results.get("total_success", 0) > 0 else 1


# 为兼容直接调用而保留的main函数
async def main():
    """传统命令行参数的主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='MCP独立运行模式')
    parser.add_argument('--config', '-c', help='MCP配置文件路径')
    parser.add_argument('--debug', '-d', action='store_true', help='启用调试模式')
    parser.add_argument('--service', '-s', help='要连接的特定服务名称')
    parser.add_argument('--test-node', '-t', help='直接测试指定的Node.js脚本路径')
    
    args = parser.parse_args()
    
    # 调用共享的异步执行函数
    exit_code = await run_standalone(
        config_path=args.config,
        debug=args.debug,
        service_name=args.service,
        test_node_path=args.test_node
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main()) 
