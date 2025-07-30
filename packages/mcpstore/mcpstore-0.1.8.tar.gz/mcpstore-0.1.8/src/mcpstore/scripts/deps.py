from typing import Dict, Any
from mcpstore.core.store import McpStore
from fastapi import HTTPException

# 全局应用状态
app_state: Dict[str, Any] = {}

def get_store() -> McpStore:
    store = app_state.get("store")
    if store is None:
        raise HTTPException(status_code=503, detail="Service not ready (Store not initialized)")
    return store
