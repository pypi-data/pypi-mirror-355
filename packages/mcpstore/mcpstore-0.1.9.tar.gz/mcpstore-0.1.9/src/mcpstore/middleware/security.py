from fastapi import Request
from mcpstore.errors.exceptions import MCPStoreException, ErrorCode
from mcpstore.config.settings import get_settings
import jwt
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    def __init__(self):
        self.settings = get_settings()
        
    async def authenticate(self, request: Request) -> str:
        """验证请求的API密钥并返回client_id"""
        api_key = request.headers.get(self.settings.API_KEY_HEADER)
        
        if not api_key:
            logger.warning("Missing API key in request")
            raise MCPStoreException(
                code=ErrorCode.UNAUTHORIZED,
                message="API key is required",
                status_code=401
            )
            
        try:
            payload = jwt.decode(
                api_key,
                self.settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            client_id = payload.get("client_id")
            
            if not client_id:
                raise MCPStoreException(
                    code=ErrorCode.UNAUTHORIZED,
                    message="Invalid API key format",
                    status_code=401
                )
                
            return client_id
            
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid API key: {str(e)}")
            raise MCPStoreException(
                code=ErrorCode.UNAUTHORIZED,
                message="Invalid API key",
                status_code=401
            )
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            raise MCPStoreException(
                code=ErrorCode.INTERNAL_ERROR,
                message="Authentication failed",
                status_code=500
            ) 
