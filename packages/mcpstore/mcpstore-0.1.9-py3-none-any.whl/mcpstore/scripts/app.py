"""
MCPStore API 服务
提供 HTTP API 服务入口
"""

import logging
import logging.config
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mcpstore.config.settings import get_settings
from mcpstore.middleware.security import SecurityMiddleware
from mcpstore.middleware.rate_limit import RateLimiter
from mcpstore.middleware.logging import RequestLoggingMiddleware
from mcpstore.errors.handlers import (
    mcp_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from mcpstore.errors.exceptions import MCPStoreException
from mcpstore.core.store import McpStore
from .api import router

# 配置日志
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
})

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()
    logger.info(f"Starting MCPStore in {settings.ENV} environment")
    
    # 初始化存储
    try:
        store = await McpStore.create(
            config_path=settings.CONFIG_PATH,
            environment=settings.ENV
        )
        app.state.store = store
        logger.info("Store initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize store: {e}", exc_info=True)
        raise MCPStoreException(
            code="CONFIGURATION_ERROR",
            message="Failed to initialize store",
            details={"error": str(e)}
        )
    
    # 初始化限流器
    app.state.rate_limiter = RateLimiter(
        requests=settings.RATE_LIMIT_REQUESTS,
        period=settings.RATE_LIMIT_PERIOD
    )
    
    # 初始化安全中间件
    app.state.security = SecurityMiddleware()
    
    # 启动监控
    try:
        await store.start_monitoring()
        logger.info("Monitoring started successfully")
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}", exc_info=True)
        # 继续运行，但记录错误
    
    yield
    
    # 清理资源
    try:
        await store.cleanup()
        logger.info("Store cleanup completed")
    except Exception as e:
        logger.error(f"Failed to cleanup store: {e}", exc_info=True)

# 创建应用实例
app = FastAPI(
    title="MCPStore API",
    description="MCPStore HTTP API Service",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    return await RequestLoggingMiddleware().log_request(request, call_next)

# 添加限流中间件
@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if not get_settings().RATE_LIMIT_ENABLED:
        return await call_next(request)
        
    client_id = request.state.client_id
    await app.state.rate_limiter.check_rate_limit(client_id)
    return await call_next(request)

# 添加认证中间件
@app.middleware("http")
async def authenticate(request: Request, call_next):
    client_id = await app.state.security.authenticate(request)
    request.state.client_id = client_id
    return await call_next(request)

# 注册路由
app.include_router(router, prefix="/api")

# 注册错误处理
app.exception_handler(MCPStoreException)(mcp_exception_handler)
app.exception_handler(ValueError)(validation_exception_handler)
app.exception_handler(Exception)(generic_exception_handler)

@app.on_event("startup")
async def startup():
    """应用启动时的初始化"""
    logger.info("MCPStore API service starting up...")

@app.on_event("shutdown")
async def shutdown():
    """应用关闭时的清理"""
    logger.info("MCPStore API service shutting down...") 
