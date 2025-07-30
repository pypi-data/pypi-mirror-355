"""
MCPStore CLI模块
提供命令行界面功能
"""

try:
    # 尝试直接导入
    from mcpstore.cli.standalone import MCPStandalone
except ImportError:
    # 尝试从src导入
    from src.mcpstore.cli.standalone import MCPStandalone

__all__ = ["MCPStandalone"] 
