from fastapi import Request
import logging
import json
import time
import uuid
from typing import Any, Dict
from mcpstore.config.settings import get_settings

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    def __init__(self):
        self.settings = get_settings()
        
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """清理请求头中的敏感信息"""
        sanitized = headers.copy()
        sensitive_fields = ['authorization', 'x-api-key', 'cookie']
        
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '***'
                
        return sanitized
        
    def _get_request_body(self, request: Request) -> Dict[str, Any]:
        """获取请求体（如果可用）"""
        try:
            return request.json()
        except:
            return {}
            
    async def log_request(self, request: Request, call_next):
        """记录请求信息和响应"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # 准备请求信息
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "headers": self._sanitize_headers(dict(request.headers)),
            "client_host": request.client.host if request.client else None,
        }
        
        logger.info(f"Request received: {json.dumps(request_info)}")
        
        try:
            # 执行请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = (time.time() - start_time) * 1000
            
            # 记录响应信息
            response_info = {
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time_ms": round(process_time, 2)
            }
            
            if response.status_code >= 400:
                logger.error(f"Request failed: {json.dumps(response_info)}")
            else:
                logger.info(f"Request completed: {json.dumps(response_info)}")
                
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            error_info = {
                "request_id": request_id,
                "error": str(e),
                "process_time_ms": round(process_time, 2)
            }
            logger.error(f"Request error: {json.dumps(error_info)}", exc_info=True)
            raise 
