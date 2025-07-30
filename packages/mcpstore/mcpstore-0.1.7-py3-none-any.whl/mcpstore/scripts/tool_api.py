from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
from mcpstore.core.store import McpStore
from mcpstore.core.models.tool import (
    ToolExecutionRequest, ToolExecutionResponse,
    ToolInfo, ToolsResponse
)
from mcpstore.scripts.deps import get_store
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/tools", response_model=ToolsResponse)
async def list_tools(
    agent_id: Optional[str] = None,
    client_id: Optional[str] = None,
    store: McpStore = Depends(get_store)
):
    """获取工具列表"""
    return store.list_tools()

@router.post("/tools/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    request: ToolExecutionRequest,
    store: McpStore = Depends(get_store)
):
    """执行工具"""
    return await store.execute_tool(request) 
