from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Dict, Any, Optional, List
from mcpstore.core.store import McpStore
from mcpstore.scripts.models import (
    RegisterRequestUnion, JsonRegistrationResponse, JsonUpdateRequest, JsonConfigResponse,
    ServiceRegistrationResult
)
from mcpstore.scripts.deps import get_store
import logging
import time
import json
import os
from mcpstore.scripts.client_registration import load_client_configs, load_agent_clients

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=Dict[str, str])
async def register_service(
    payload: RegisterRequestUnion,
    agent_id: Optional[str] = None,
    store: McpStore = Depends(get_store)
):
    return await store.register_service(payload, agent_id)

@router.post("/register/json", response_model=JsonRegistrationResponse)
async def register_json_service(
    client_id: Optional[str] = None,
    service_names: Optional[List[str]] = None,
    store: McpStore = Depends(get_store)
):
    return await store.register_json_service(client_id, service_names)

@router.put("/register/json", response_model=JsonRegistrationResponse)
async def update_json_service(
    payload: JsonUpdateRequest,
    store: McpStore = Depends(get_store)
):
    return await store.update_json_service(payload)

@router.get("/register/json", response_model=JsonConfigResponse)
async def get_json_config(
    client_id: Optional[str] = None,
    store: McpStore = Depends(get_store)
):
    return store.get_json_config(client_id)

@router.get("/health", response_model=Dict[str, Any])
async def get_health_status(store: McpStore = Depends(get_store)):
    return await store.get_health_status()

@router.get("/service_info", response_model=Dict[str, Any])
async def get_service_info(name: str, store: McpStore = Depends(get_store)):
    return store.get_service_info(name)

@router.get("/services")
async def list_services(store: McpStore = Depends(get_store)):
    return store.list_services()

@router.get("/tools")
async def list_tools(store: McpStore = Depends(get_store)):
    return store.list_tools()

