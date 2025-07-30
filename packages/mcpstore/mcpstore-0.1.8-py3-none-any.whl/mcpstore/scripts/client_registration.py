import json
import logging
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from mcpstore.scripts.deps import get_store
from mcpstore.core.store import McpStore
from mcpstore.scripts.models import ClientRegistrationRequest, ServiceRegistrationStatus, ClientRegistrationResponse

router = APIRouter()
logger = logging.getLogger(__name__)

def generate_agent_id() -> str:
    """生成agent_id"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:8]
    return f"agent_{timestamp}_{random_suffix}"

def generate_client_id(agent_id: str, index: int) -> str:
    """根据agent_id生成client_id"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{agent_id}_client_{index}_{timestamp}"

def save_client_configs(configs: Dict[str, Any]):
    """保存客户端配置到文件"""
    config_dir = "configs"
    os.makedirs(config_dir, exist_ok=True)
    
    # 保存client_services.json
    client_services_path = os.path.join(config_dir, "client_services.json")
    with open(client_services_path, "w") as f:
        json.dump(configs, f, indent=2)

def save_agent_clients(agent_id: str, client_ids: List[str]):
    """保存agent和client的关系到文件"""
    config_dir = "configs"
    agent_clients_path = os.path.join(config_dir, "agent_clients.json")
    
    # 读取现有配置
    agent_clients = {}
    if os.path.exists(agent_clients_path):
        with open(agent_clients_path, "r") as f:
            agent_clients = json.load(f)
    
    # 更新配置
    agent_clients[agent_id] = client_ids
    
    # 保存配置
    with open(agent_clients_path, "w") as f:
        json.dump(agent_clients, f, indent=2)

def load_client_configs() -> Dict[str, Any]:
    """加载客户端配置"""
    config_dir = "configs"
    client_services_path = os.path.join(config_dir, "client_services.json")
    
    if os.path.exists(client_services_path):
        with open(client_services_path, "r") as f:
            return json.load(f)
    return {}

def load_agent_clients() -> Dict[str, List[str]]:
    """加载agent和client的关系"""
    config_dir = "configs"
    agent_clients_path = os.path.join(config_dir, "agent_clients.json")
    
    if os.path.exists(agent_clients_path):
        with open(agent_clients_path, "r") as f:
            return json.load(f)
    return {}

@router.post("/register_clients", response_model=ClientRegistrationResponse)
async def register_clients(client_configs: Dict[str, Any], store: McpStore = Depends(get_store)):
    try:
        return store.register_clients(client_configs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
