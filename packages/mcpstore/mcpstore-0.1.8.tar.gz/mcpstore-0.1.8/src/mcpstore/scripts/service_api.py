from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Dict, Any, Optional, List
from mcpstore.core.store import McpStore
from mcpstore.core.models.service import (
    RegisterRequestUnion, JsonRegistrationResponse, JsonUpdateRequest, JsonConfigResponse,
    ServiceRegistrationResult, ServicesResponse, ServiceInfoResponse
)
from mcpstore.scripts.deps import get_store
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=Dict[str, str])
async def register_service(
    payload: RegisterRequestUnion,
    agent_id: Optional[str] = None,
    store: McpStore = Depends(get_store)
):
    """注册服务"""
    return await store.register_service(payload, agent_id)

@router.post("/register/json", response_model=JsonRegistrationResponse)
async def register_json_service(
    client_id: Optional[str] = None,
    service_names: Optional[List[str]] = None,
    store: McpStore = Depends(get_store)
):
    """批量注册服务"""
    return await store.register_json_service(client_id, service_names)

@router.put("/register/json", response_model=JsonRegistrationResponse)
async def update_json_service(
    payload: JsonUpdateRequest,
    store: McpStore = Depends(get_store)
):
    """更新服务配置"""
    return await store.update_json_service(payload)

@router.get("/register/json", response_model=JsonConfigResponse)
async def get_json_config(
    client_id: Optional[str] = None,
    store: McpStore = Depends(get_store)
):
    """获取JSON配置
    
    Args:
        client_id: 客户端ID，若为 main_client 则查询主客户端配置，否则查询普通客户端配置
        
    Returns:
        JsonConfigResponse: 包含客户端配置的响应
    """
    try:
        return store.get_json_config(client_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health", response_model=Dict[str, Any])
async def get_health_status(store: McpStore = Depends(get_store)):
    """获取服务健康状态"""
    return await store.get_health_status()

@router.get("/service_info", response_model=ServiceInfoResponse)
async def get_service_info(name: str, store: McpStore = Depends(get_store)):
    """获取服务信息
    
    Args:
        name: 服务名称
        
    Returns:
        ServiceInfoResponse: 包含服务详细信息的响应
    """
    try:
        return await store.get_service_info(name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/services", response_model=ServicesResponse)
async def list_services(store: McpStore = Depends(get_store)):
    """获取所有服务列表"""
    return await store.list_services() 
