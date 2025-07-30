from pydantic import BaseSettings, Field
from typing import Dict, Optional
from enum import Enum
import os

class Environment(str, Enum):
    DEV = "development"
    PROD = "production"
    TEST = "testing"

class AppSettings(BaseSettings):
    ENV: Environment = Field(default=Environment.DEV)
    DEBUG: bool = Field(default=False)
    
    # 服务配置
    SERVICE_NAME: str = "mcpstore"
    VERSION: str = "1.0.0"
    
    # 安全配置
    API_KEY_HEADER: str = "X-API-Key"
    SECRET_KEY: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    
    # 超时配置
    TOOL_EXECUTION_TIMEOUT: int = 30  # seconds
    REQUEST_TIMEOUT: int = 10  # seconds
    
    # 路径配置
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CONFIG_PATH: str = os.path.join(BASE_DIR, "data", "mcp.json")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

_settings = None

def get_settings() -> AppSettings:
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings 
