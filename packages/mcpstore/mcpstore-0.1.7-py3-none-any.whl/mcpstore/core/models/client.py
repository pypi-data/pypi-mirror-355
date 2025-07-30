from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ClientRegistrationRequest(BaseModel):
    client_id: Optional[str] = None
    service_names: Optional[List[str]] = None

class ClientRegistrationResponse(BaseModel):
    client_id: str
    service_names: List[str]
    config: Dict[str, Any] 
