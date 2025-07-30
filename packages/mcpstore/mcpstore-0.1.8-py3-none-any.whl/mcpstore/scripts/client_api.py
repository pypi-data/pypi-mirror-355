from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
from mcpstore.core.store import McpStore
from mcpstore.core.models.client import ClientRegistrationRequest, ClientRegistrationResponse
from mcpstore.scripts.deps import get_store
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register_clients", response_model=ClientRegistrationResponse)
async def register_clients(
    request: ClientRegistrationRequest,
    store: McpStore = Depends(get_store)
):
    """注册客户端"""
    return await store.register_clients(request) 
