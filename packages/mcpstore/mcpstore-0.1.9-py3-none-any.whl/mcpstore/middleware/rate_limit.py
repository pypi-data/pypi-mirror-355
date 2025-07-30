import time
import logging
from typing import Dict, List
from mcpstore.errors.exceptions import MCPStoreException, ErrorCode
from mcpstore.config.settings import get_settings

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, requests: int = None, period: int = None):
        settings = get_settings()
        self.requests = requests or settings.RATE_LIMIT_REQUESTS
        self.period = period or settings.RATE_LIMIT_PERIOD
        self._requests: Dict[str, List[float]] = {}
        
    def _clean_old_requests(self, client_id: str, now: float):
        """清理过期的请求记录"""
        if client_id in self._requests:
            self._requests[client_id] = [
                t for t in self._requests[client_id]
                if now - t < self.period
            ]
    
    async def check_rate_limit(self, client_id: str) -> bool:
        """检查是否超过速率限制"""
        now = time.time()
        
        # 初始化客户端请求记录
        if client_id not in self._requests:
            self._requests[client_id] = []
            
        # 清理过期请求
        self._clean_old_requests(client_id, now)
        
        # 检查请求数量
        if len(self._requests[client_id]) >= self.requests:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            raise MCPStoreException(
                code=ErrorCode.RATE_LIMITED,
                message=f"Rate limit of {self.requests} requests per {self.period} seconds exceeded",
                status_code=429,
                details={
                    "limit": self.requests,
                    "period": self.period,
                    "client_id": client_id
                }
            )
            
        # 记录新请求
        self._requests[client_id].append(now)
        return True
        
    def get_remaining_requests(self, client_id: str) -> int:
        """获取剩余可用请求数"""
        now = time.time()
        self._clean_old_requests(client_id, now)
        current_requests = len(self._requests.get(client_id, []))
        return max(0, self.requests - current_requests) 
