from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ToolInfo(BaseModel):
    name: str
    description: str
    service_name: str
    client_id: Optional[str] = None
    inputSchema: Optional[Dict[str, Any]] = None

class ToolsResponse(BaseModel):
    tools: List[ToolInfo]
    total_tools: int

class ToolExecutionRequest(BaseModel):
    tool_name: str
    args: Dict[str, Any]
    agent_id: Optional[str] = None
    client_id: Optional[str] = None

class ToolExecutionResponse(BaseModel):
    success: bool
    result: Any
    error: Optional[str] = None 
