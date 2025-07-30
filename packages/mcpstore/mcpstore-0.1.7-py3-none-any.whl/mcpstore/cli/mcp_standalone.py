#!/usr/bin/env python
"""
MCP独立运行入口点
可以直接运行: python -m src.mcpstore.cli.mcp_standalone
"""

import asyncio
import sys
from src.mcpstore.cli.standalone import main

if __name__ == "__main__":
    # 在Windows平台上设置事件循环策略
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行主函数
    asyncio.run(main()) 
