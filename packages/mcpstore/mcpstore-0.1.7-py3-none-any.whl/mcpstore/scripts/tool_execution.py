from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List, Dict
from mcpstore.core.store import McpStore
from mcpstore.scripts.models import ToolExecutionRequest, ToolExecutionResponse, ContentUnion, ContentType, Content, TextContent, ImageContent, JsonContent, BinaryContent
from mcpstore.scripts.deps import get_store

router = APIRouter()

@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(request: ToolExecutionRequest, store: McpStore = Depends(get_store)):
    try:
        return await store.execute_tool(
            service_name=request.service_name,
            tool_name=request.tool_name,
            parameters=request.parameters,
            agent_id=getattr(request, "agent_id", None)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_result_item(item: Any) -> List[ContentUnion]:
    """处理单个结果项，转换为适当的内容类型"""
    if isinstance(item, str):
        return [TextContent(text=item)]
    elif isinstance(item, bytes):
        return [BinaryContent(data=item)]
    elif isinstance(item, dict):
        return [JsonContent(data=item)]
    elif isinstance(item, (list, tuple)):
        results = []
        for sub_item in item:
            results.extend(process_result_item(sub_item))
        return results
    else:
        # 尝试转换为字符串
        return [TextContent(text=str(item))] 
