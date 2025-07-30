import uvicorn
import typer
import asyncio
import sys
from typing_extensions import Annotated
from mcpstore.scripts.app import app  # 导入 app 对象
import logging

# 导入独立运行模式
from mcpstore.cli.standalone import run_standalone

# Set up logging for the CLI itself
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
cli_logger = logging.getLogger("cli_main")


app_cli = typer.Typer(no_args_is_help=True)

@app_cli.callback()
def callback():
    """
    MCP Store Command Line Interface.
    """
    cli_logger.info("【第4步】Typer 回调函数已执行，准备分发子命令。")
    pass

@app_cli.command()
def api(
    host: Annotated[
        str, typer.Option(help="The host to bind to.")
    ] = "0.0.0.0",
    port: Annotated[
        int, typer.Option(help="The port to bind to.")
    ] = 18611,
    reload: Annotated[
        bool,
        typer.Option(
            help="Enable auto-reloading.",
        ),
    ] = False,
):
    """启动 mcpstore API 服务"""
    cli_logger.info(f"【第5步】Typer 已成功匹配到 'api' 命令。")
    cli_logger.info(f"    - 接收到参数 Host: {host}")
    cli_logger.info(f"    - 接收到参数 Port: {port}")
    cli_logger.info(f"    - 接收到参数 Reload: {reload}")
    cli_logger.info("【第6步】CLI 任务完成，准备将控制权移交给 Uvicorn。")
    uvicorn.run("mcpstore.scripts.app:app", host=host, port=port, reload=reload)

@app_cli.command()
def standalone(
    config: Annotated[
        str, typer.Option("--config", "-c", help="MCP配置文件路径")
    ] = None,
    debug: Annotated[
        bool, typer.Option("--debug", "-d", help="启用调试模式")
    ] = False,
    service: Annotated[
        str, typer.Option("--service", "-s", help="要连接的特定服务名称")
    ] = None,
    test_node: Annotated[
        str, typer.Option("--test-node", "-t", help="直接测试指定的Node.js脚本路径")
    ] = None,
):
    """在独立模式下运行MCP服务注册"""
    cli_logger.info(f"Typer 已成功匹配到 'standalone' 命令。")
    cli_logger.info(f"    - 接收到参数 Config: {config}")
    cli_logger.info(f"    - 接收到参数 Debug: {debug}")
    cli_logger.info(f"    - 接收到参数 Service: {service}")
    cli_logger.info(f"    - 接收到参数 Test Node: {test_node}")
    
    # 在Windows平台上设置事件循环策略
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        cli_logger.info("已设置Windows ProactorEventLoop策略")
    
    # 运行独立模式
    exit_code = asyncio.run(run_standalone(
        config_path=config,
        debug=debug,
        service_name=service,
        test_node_path=test_node
    ))
    
    # 根据退出码退出
    if exit_code != 0:
        cli_logger.error("独立模式运行失败")
        sys.exit(exit_code)
    else:
        cli_logger.info("独立模式运行成功")

def main():
    cli_logger.info("【第3步】Typer 主应用已启动，准备解析命令行参数。")
    app_cli()

if __name__ == "__main__":
    cli_logger.info("【第1步】命令行入口 (__name__ == '__main__') 已触发。")
    cli_logger.info("【第2步】即将调用 main() 函数。")
    main() 
