import logging
import os
import sys
import time
import uuid
import json # for pretty printing
from fastapi import Request
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from mcpstore.scripts.exception_handlers import validation_exception_handler

from mcpstore.scripts.deps import app_state
from plugins.json_mcp import MCPConfig
from core.registry import ServiceRegistry
from core.orchestrator import MCPOrchestrator
from core.store import McpStore
from core.client_manager import ClientManager
from core.session_manager import SessionManager
from mcpstore.scripts import service_api, client_api, tool_api
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("mcp_service.log")])
logger = logging.getLogger(__name__)
logger.info("【第8步】Uvicorn 正在导入 app.py 文件。")

async def lifespan(app: FastAPI):
    logger.info("【第10步】FastAPI 的 lifespan 已启动，开始初始化核心组件。")

    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mcp.json")
    mcp_config_handler = MCPConfig(config_path)
    logger.info(f"    - MCPConfig 实例已创建，配置文件路径: {config_path}")

    config = mcp_config_handler.load_config()
    logger.info("    - 配置文件 mcp.json 已加载。")
    logger.info(f"    - 加载的配置内容: \n{json.dumps(config, indent=2, ensure_ascii=False)}")

    registry = ServiceRegistry()
    logger.info("    - ServiceRegistry 实例已创建。")

    orchestrator = MCPOrchestrator(config=config, registry=registry)
    logger.info("    - MCPOrchestrator 实例已创建。")

    store = McpStore(orchestrator=orchestrator, config=mcp_config_handler)
    logger.info("    - McpStore 实例已创建，聚合了所有核心组件。")
    logger.info("【第11步】所有核心组件的唯一实例已创建完毕。")

    logger.info("    - 准备调用 orchestrator.setup()")
    await orchestrator.setup()
    logger.info("    - orchestrator.setup() 已完成。")

    # logger.info("    - 准备调用 orchestrator.start_monitoring()")
    # await orchestrator.start_monitoring()
    # logger.info("    - orchestrator.start_monitoring() 已完成，后台健康检查等任务已启动。")

    # logger.info("    - 准备调用 orchestrator.register_json_services()，注册 mcp.json 中的服务。")
    # registration_results = await orchestrator.register_json_services(config, client_id="main_client")
    # logger.info("    - orchestrator.register_json_services() 已完成。")
    # logger.info(f"    - 服务注册结果: \n{json.dumps(registration_results, indent=2, ensure_ascii=False)}")

    app_state["store"] = store
    logger.info("    - 唯一的 McpStore 实例已存入 app_state。")
    logger.info("【第12步】应用启动流程 (lifespan) 即将完成，准备移交控制权。")

    try:
        yield
        logger.info("Lifespan 正常结束，应用即将关闭。")
    finally:
        logger.info("Application shutdown: Cleaning up resources...")
        orch = app_state.get("orchestrator")
        if orch:
            await orch.stop_main_client()
            await orch.cleanup()
        app_state.clear()
        logger.info("Application shutdown complete.")

# 创建应用实例
app = FastAPI(lifespan=lifespan)
logger.info("【第9步】FastAPI 应用实例 'app' 已创建。")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(service_api.router, tags=["services"])
app.include_router(client_api.router, tags=["clients"])
app.include_router(tool_api.router, tags=["tools"])

# 注册异常处理
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log incoming requests, processing time, and status.
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Request received - ID: {request_id}, Method: {request.method}, Path: {request.url.path}")
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Request finished - ID: {request_id}, "
            f"Status: {response.status_code}, Duration: {process_time:.2f}ms"
        )
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"Request failed - ID: {request_id}, "
            f"Error: {e}, Duration: {process_time:.2f}ms",
            exc_info=True
        )
        raise 
