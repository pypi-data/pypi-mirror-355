"""
MCPStore API 路由
提供所有 HTTP API 端点，保持与 MCPStore 核心方法的一致性
"""

from fastapi import APIRouter, Depends, Request
from mcpstore.core.models import *
from mcpstore.errors.exceptions import MCPStoreException, ErrorCode
from mcpstore.config.settings import get_settings
from typing import Optional, List, Dict, Any, Union
import logging
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)
router = APIRouter()

# 依赖注入
async def get_store(request: Request):
    """获取 store 实例"""
    if not hasattr(request.app.state, "store"):
        raise MCPStoreException(
            code=ErrorCode.CONFIGURATION_ERROR,
            message="Store not initialized",
            status_code=500
        )
    return request.app.state.store

async def get_client_id(request: Request) -> str:
    """获取客户端ID"""
    if not hasattr(request.state, "client_id"):
        raise MCPStoreException(
            code=ErrorCode.UNAUTHORIZED,
            message="Client not authenticated",
            status_code=401
        )
    return request.state.client_id

@asynccontextmanager
async def tool_execution_context():
    """工具执行上下文管理器"""
    settings = get_settings()
    try:
        yield
    except asyncio.TimeoutError:
        raise MCPStoreException(
            code=ErrorCode.TOOL_EXECUTION_ERROR,
            message="Tool execution timeout",
            status_code=504
        )
    except Exception as e:
        raise MCPStoreException(
            code=ErrorCode.TOOL_EXECUTION_ERROR,
            message=str(e),
            status_code=500
        )

# Store 级别操作
@router.post("/for_store/add_service")
async def store_add_service(
    request: Request,
    payload: Optional[RegisterRequestUnion] = None,
    store = Depends(get_store),
    client_id: str = Depends(get_client_id)
):
    """Store 级别注册服务"""
    try:
        async with asyncio.timeout(get_settings().REQUEST_TIMEOUT):
            context = await store.for_store(client_id)
            result = await context.add_service(payload)
            return {
                "success": True,
                "data": result,
                "request_id": request.state.request_id
            }
    except Exception as e:
        logger.error(f"Store add_service failed: {e}", exc_info=True)
        raise MCPStoreException(
            code=ErrorCode.INTERNAL_ERROR,
            message="Failed to add service",
            details={"error": str(e)}
        )

@router.get("/for_store/list_services")
async def store_list_services(
    request: Request,
    store = Depends(get_store),
    client_id: str = Depends(get_client_id)
):
    """Store 级别获取服务列表"""
    try:
        async with asyncio.timeout(get_settings().REQUEST_TIMEOUT):
            context = await store.for_store(client_id)
            result = await context.list_services()
            return {
                "success": True,
                "data": result,
                "request_id": request.state.request_id
            }
    except Exception as e:
        logger.error(f"Store list_services failed: {e}", exc_info=True)
        raise MCPStoreException(
            code=ErrorCode.INTERNAL_ERROR,
            message="Failed to list services",
            details={"error": str(e)}
        )

@router.get("/for_store/list_tools")
async def store_list_tools(
    request: Request,
    store = Depends(get_store),
    client_id: str = Depends(get_client_id)
):
    """Store 级别获取工具列表"""
    try:
        async with asyncio.timeout(get_settings().REQUEST_TIMEOUT):
            context = await store.for_store(client_id)
            result = await context.list_tools()
            return {
                "success": True,
                "data": result,
                "request_id": request.state.request_id
            }
    except Exception as e:
        logger.error(f"Store list_tools failed: {e}", exc_info=True)
        raise MCPStoreException(
            code=ErrorCode.INTERNAL_ERROR,
            message="Failed to list tools",
            details={"error": str(e)}
        )

@router.get("/for_store/check_services")
async def store_check_services(
    request: Request,
    store = Depends(get_store),
    client_id: str = Depends(get_client_id)
):
    """Store 级别健康检查"""
    try:
        async with asyncio.timeout(get_settings().REQUEST_TIMEOUT):
            context = await store.for_store(client_id)
            result = await context.check_services()
            return {
                "success": True,
                "data": result,
                "request_id": request.state.request_id
            }
    except Exception as e:
        logger.error(f"Store check_services failed: {e}", exc_info=True)
        raise MCPStoreException(
            code=ErrorCode.INTERNAL_ERROR,
            message="Failed to check services",
            details={"error": str(e)}
        )

@router.post("/for_store/use_tool")
async def store_use_tool(
    request: Request,
    tool_request: ToolExecutionRequest,
    store = Depends(get_store),
    client_id: str = Depends(get_client_id)
):
    """Store 级别使用工具"""
    try:
        async with tool_execution_context():
            async with asyncio.timeout(get_settings().TOOL_EXECUTION_TIMEOUT):
                if not tool_request.tool_name or not isinstance(tool_request.args, dict):
                    raise MCPStoreException(
                        code=ErrorCode.VALIDATION_ERROR,
                        message="Invalid tool request format",
                        status_code=400
                    )
                    
                context = await store.for_store(client_id)
                result = await context.use_tool(
                    tool_request.tool_name,
                    tool_request.args
                )
                return {
                    "success": True,
                    "data": result,
                    "request_id": request.state.request_id
                }
    except Exception as e:
        logger.error(f"Store use_tool failed: {e}", exc_info=True)
        raise MCPStoreException(
            code=ErrorCode.TOOL_EXECUTION_ERROR,
            message="Tool execution failed",
            details={"error": str(e)}
        )

# Agent 级别操作
@router.post("/for_agent/{agent_id}/add_service")
async def agent_add_service(
    request: Request,
    agent_id: str,
    payload: Optional[RegisterRequestUnion] = None,
    store = Depends(get_store),
    client_id: str = Depends(get_client_id)
):
    """Agent 级别注册服务"""
    try:
        if not agent_id or not isinstance(agent_id, str):
            raise MCPStoreException(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invalid agent_id",
                status_code=400
            )
            
        async with asyncio.timeout(get_settings().REQUEST_TIMEOUT):
            context = await store.for_agent(agent_id, client_id)
            result = await context.add_service(payload)
            return {
                "success": True,
                "data": result,
                "request_id": request.state.request_id
            }
    except Exception as e:
        logger.error(f"Agent add_service failed: {e}", exc_info=True)
        raise MCPStoreException(
            code=ErrorCode.INTERNAL_ERROR,
            message="Failed to add service",
            details={"error": str(e)}
        )

@router.get("/for_agent/{agent_id}/list_services")
async def agent_list_services(
    request: Request,
    agent_id: str,
    store = Depends(get_store),
    client_id: str = Depends(get_client_id)
):
    """Agent 级别获取服务列表"""
    try:
        if not agent_id or not isinstance(agent_id, str):
            raise MCPStoreException(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invalid agent_id",
                status_code=400
            )
            
        async with asyncio.timeout(get_settings().REQUEST_TIMEOUT):
            context = await store.for_agent(agent_id, client_id)
            result = await context.list_services()
            return {
                "success": True,
                "data": result,
                "request_id": request.state.request_id
            }
    except Exception as e:
        logger.error(f"Agent list_services failed: {e}", exc_info=True)
        raise MCPStoreException(
            code=ErrorCode.INTERNAL_ERROR,
            message="Failed to list services",
            details={"error": str(e)}
        )

@router.get("/for_agent/{agent_id}/list_tools")
async def agent_list_tools(
    request: Request,
    agent_id: str,
    store = Depends(get_store),
    client_id: str = Depends(get_client_id)
):
    """Agent 级别获取工具列表"""
    try:
        if not agent_id or not isinstance(agent_id, str):
            raise MCPStoreException(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invalid agent_id",
                status_code=400
            )
            
        async with asyncio.timeout(get_settings().REQUEST_TIMEOUT):
            context = await store.for_agent(agent_id, client_id)
            result = await context.list_tools()
            return {
                "success": True,
                "data": result,
                "request_id": request.state.request_id
            }
    except Exception as e:
        logger.error(f"Agent list_tools failed: {e}", exc_info=True)
        raise MCPStoreException(
            code=ErrorCode.INTERNAL_ERROR,
            message="Failed to list tools",
            details={"error": str(e)}
        )

@router.get("/for_agent/{agent_id}/check_services")
async def agent_check_services(
    request: Request,
    agent_id: str,
    store = Depends(get_store),
    client_id: str = Depends(get_client_id)
):
    """Agent 级别健康检查"""
    try:
        if not agent_id or not isinstance(agent_id, str):
            raise MCPStoreException(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invalid agent_id",
                status_code=400
            )
            
        async with asyncio.timeout(get_settings().REQUEST_TIMEOUT):
            context = await store.for_agent(agent_id, client_id)
            result = await context.check_services()
            return {
                "success": True,
                "data": result,
                "request_id": request.state.request_id
            }
    except Exception as e:
        logger.error(f"Agent check_services failed: {e}", exc_info=True)
        raise MCPStoreException(
            code=ErrorCode.INTERNAL_ERROR,
            message="Failed to check services",
            details={"error": str(e)}
        )

@router.post("/for_agent/{agent_id}/use_tool")
async def agent_use_tool(
    request: Request,
    agent_id: str,
    tool_request: ToolExecutionRequest,
    store = Depends(get_store),
    client_id: str = Depends(get_client_id)
):
    """Agent 级别使用工具"""
    try:
        if not agent_id or not isinstance(agent_id, str):
            raise MCPStoreException(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invalid agent_id",
                status_code=400
            )
            
        async with tool_execution_context():
            async with asyncio.timeout(get_settings().TOOL_EXECUTION_TIMEOUT):
                if not tool_request.tool_name or not isinstance(tool_request.args, dict):
                    raise MCPStoreException(
                        code=ErrorCode.VALIDATION_ERROR,
                        message="Invalid tool request format",
                        status_code=400
                    )
                    
                context = await store.for_agent(agent_id, client_id)
                result = await context.use_tool(
                    tool_request.tool_name,
                    tool_request.args
                )
                return {
                    "success": True,
                    "data": result,
                    "request_id": request.state.request_id
                }
    except Exception as e:
        logger.error(f"Agent use_tool failed: {e}", exc_info=True)
        raise MCPStoreException(
            code=ErrorCode.TOOL_EXECUTION_ERROR,
            message="Tool execution failed",
            details={"error": str(e)}
        )

# 通用服务信息查询
@router.get("/services/{name}", response_model=APIResponse)
async def get_service_info(
    name: str,
    agent_id: Optional[str] = None
):
    """获取服务信息，支持 Store/Agent 上下文"""
    try:
        if agent_id:
            agent_id = validate_agent_id(agent_id)
            result = await store.for_agent(agent_id).get_service_info(name)
        else:
            result = await store.for_store().get_service_info(name)
        return APIResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Get service info failed: {e}")
        return APIResponse(success=False, message=str(e))

# 配置管理
@router.get("/config", response_model=APIResponse)
async def get_config(agent_id: Optional[str] = None):
    """获取配置，支持 Store/Agent 上下文"""
    try:
        if agent_id:
            agent_id = validate_agent_id(agent_id)
            result = store.get_json_config(agent_id)
        else:
            result = store.get_json_config()
        return APIResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Get config failed: {e}")
        return APIResponse(success=False, message=str(e))

@router.put("/config", response_model=APIResponse)
async def update_config(payload: JsonUpdateRequest):
    """更新配置"""
    try:
        if not payload.config:
            raise ValueError("Config is required")
        result = await store.update_json_service(payload)
        return APIResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"Update config failed: {e}")
        return APIResponse(success=False, message=str(e)) 
