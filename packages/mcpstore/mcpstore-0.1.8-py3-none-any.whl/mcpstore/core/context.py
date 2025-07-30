"""
MCPStore Context Module
提供 MCPStore 的上下文管理功能
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from mcpstore.core.models.tool import ToolExecutionRequest, ToolExecutionResponse
from mcpstore.core.models.service import (
    ServiceInfo, AddServiceRequest, ServiceConfigUnion,
    URLServiceConfig, CommandServiceConfig, MCPServerConfig
)

@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    status: str
    description: str
    tools: List[str]

@dataclass
class ToolInfo:
    """工具信息"""
    name: str
    description: str
    parameters: Dict[str, Any]

class ContextType(Enum):
    """上下文类型"""
    STORE = "store"
    AGENT = "agent"

class MCPStoreContext:
    """
    MCPStore上下文类
    负责处理具体的业务操作，维护操作的上下文环境
    """
    def __init__(self, store: 'MCPStore', agent_id: Optional[str] = None):
        self._store = store
        self._agent_id = agent_id
        self._context_type = ContextType.STORE if agent_id is None else ContextType.AGENT
        
        # 扩展预留
        self._metadata: Dict[str, Any] = {}
        self._config: Dict[str, Any] = {}
        self._cache: Dict[str, Any] = {}

    # === 核心服务接口 ===
    async def list_services(self) -> List[ServiceInfo]:
        """
        列出服务列表
        - store上下文：聚合 main_client 下所有 client_id 的服务
        - agent上下文：聚合 agent_id 下所有 client_id 的服务
        """
        if self._context_type == ContextType.STORE:
            return await self._store.list_services()
        else:
            return await self._store.list_services(self._agent_id, agent_mode=True)

    async def add_service(self, config: Union[ServiceConfigUnion, List[str], None] = None) -> bool:
        """
        增强版的服务添加方法，支持多种配置格式：
        1. URL方式：
           await add_service({
               "name": "weather",
               "url": "https://weather-api.example.com/mcp",
               "transport": "streamable-http"
           })
        
        2. 本地命令方式：
           await add_service({
               "name": "assistant",
               "command": "python",
               "args": ["./assistant_server.py"],
               "env": {"DEBUG": "true"}
           })
        
        3. MCPConfig字典方式：
           await add_service({
               "mcpServers": {
                   "weather": {
                       "url": "https://weather-api.example.com/mcp"
                   }
               }
           })
        
        4. 服务名称列表方式（从现有配置中选择）：
           await add_service(['weather', 'assistant'])
        
        5. 无参数方式（仅限Store上下文）：
           await add_service()  # 注册所有服务
        
        所有新添加的服务都会同步到 mcp.json 配置文件中。
        """
        agent_id = self._agent_id or self._store.client_manager.main_client_id
        
        # 处理不同的输入格式
        if config is None:
            # Store模式下的全量注册
            if self._context_type == ContextType.STORE:
                print("[INFO][add_service] STORE模式-全量注册所有服务")
                resp = await self._store.register_json_service()
                print(f"[INFO][add_service] 注册结果: {resp}")
                return bool(resp and resp.service_names)
            else:
                print("[WARN][add_service] AGENT模式-未指定服务配置")
                return False
                
        # 处理服务名称列表
        if isinstance(config, list):
            if not config:
                print("[WARN][add_service] 服务名称列表为空")
                return False
                
            print(f"[INFO][add_service] 注册指定服务: {config}")
            resp = await self._store.register_json_service(
                client_id=agent_id,
                service_names=config
            )
            print(f"[INFO][add_service] 注册结果: {resp}")
            return bool(resp and resp.service_names)
            
        # 处理字典格式的配置
        if isinstance(config, dict):
            # 转换为标准格式
            if "mcpServers" in config:
                # 已经是MCPConfig格式
                mcp_config = config
            else:
                # 单个服务配置，需要转换为MCPConfig格式
                service_name = config.get("name")
                if not service_name:
                    print("[ERROR][add_service] 服务配置缺少name字段")
                    return False
                    
                mcp_config = {
                    "mcpServers": {
                        service_name: {k: v for k, v in config.items() if k != "name"}
                    }
                }
            
            # 更新配置文件
            try:
                # 1. 加载现有配置
                current_config = self._store.config.load_config()
                
                # 2. 合并新配置
                for name, service_config in mcp_config["mcpServers"].items():
                    current_config["mcpServers"][name] = service_config
                
                # 3. 保存更新后的配置
                self._store.config.save_config(current_config)
                
                # 4. 注册服务
                resp = await self._store.register_json_service(
                    client_id=agent_id,
                    service_names=list(mcp_config["mcpServers"].keys())
                )
                print(f"[INFO][add_service] 注册结果: {resp}")
                return bool(resp and resp.service_names)
                
            except Exception as e:
                print(f"[ERROR][add_service] 更新配置文件失败: {e}")
                return False
        
        print(f"[ERROR][add_service] 不支持的配置格式: {type(config)}")
        return False

    async def list_tools(self) -> List[ToolInfo]:
        """
        列出工具列表
        - store上下文：聚合 main_client 下所有 client_id 的工具
        - agent上下文：聚合 agent_id 下所有 client_id 的工具
        """
        if self._context_type == ContextType.STORE:
            return await self._store.list_tools()
        else:
            return await self._store.list_tools(self._agent_id, agent_mode=True)

    async def check_services(self) -> dict:
        """
        异步健康检查，store/agent上下文自动判断
        - store上下文：聚合 main_client 下所有 client_id 的服务健康状态
        - agent上下文：聚合 agent_id 下所有 client_id 的服务健康状态
        """
        if self._context_type.name == 'STORE':
            return await self._store.get_health_status()
        elif self._context_type.name == 'AGENT':
            return await self._store.get_health_status(self._agent_id, agent_mode=True)
        else:
            print(f"[ERROR][check_services] 未知上下文类型: {self._context_type}")
            return {}

    async def get_service_info(self, name: str) -> Any:
        """
        获取服务详情，支持 store/agent 上下文
        - store上下文：在 main_client 下的所有 client 中查找服务
        - agent上下文：在指定 agent_id 下的所有 client 中查找服务
        """
        if not name:
            return {}
            
        if self._context_type == ContextType.STORE:
            print(f"[INFO][get_service_info] STORE模式-在main_client中查找服务: {name}")
            return await self._store.get_service_info(name)
        elif self._context_type == ContextType.AGENT:
            print(f"[INFO][get_service_info] AGENT模式-在agent({self._agent_id})中查找服务: {name}")
            return await self._store.get_service_info(name, self._agent_id)
        else:
            print(f"[ERROR][get_service_info] 未知上下文类型: {self._context_type}")
            return {}

    async def use_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        使用工具，支持 store/agent 上下文
        - store上下文：在 main_client 下的所有 client 中查找并使用工具
        - agent上下文：在指定 agent_id 下的所有 client 中查找并使用工具
        
        Args:
            tool_name: 工具名称，格式为 service_toolname
            args: 工具参数
            
        Returns:
            Any: 工具执行结果
        """
        # 从工具名称中提取服务名称
        if "_" not in tool_name:
            raise ValueError(f"Invalid tool name format: {tool_name}. Expected format: service_toolname")
        
        if self._context_type == ContextType.STORE:
            print(f"[INFO][use_tool] STORE模式-在main_client中使用工具: {tool_name}")
            request = ToolExecutionRequest(
                tool_name=tool_name,
                args=args
            )
        else:
            print(f"[INFO][use_tool] AGENT模式-在agent({self._agent_id})中使用工具: {tool_name}")
            request = ToolExecutionRequest(
                tool_name=tool_name,
                args=args,
                agent_id=self._agent_id
            )
            
        return await self._store.process_tool_request(request)

    # === 上下文信息 ===
    @property
    def context_type(self) -> ContextType:
        """获取上下文类型"""
        return self._context_type

    @property
    def agent_id(self) -> Optional[str]:
        """获取当前agent_id"""
        return self._agent_id 
