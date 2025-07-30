import uvicorn
import typer
import asyncio
import sys
import os
from typing_extensions import Annotated
from rich.console import Console
from rich.table import Table
from rich import print as rich_print
from mcpstore.scripts.app import app
import logging
from datetime import datetime

# 设置日志记录
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = f"mcpstore_{datetime.now().strftime('%Y%m%d')}.log"
LOG_DIR = "logs"

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, LOG_FILE), encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
cli_logger = logging.getLogger("mcpstore_cli")

# 创建Rich控制台对象
console = Console()

# 创建Typer应用
app_cli = typer.Typer(
    name="MCPStore",
    help="MCPStore Command Line Interface",
    no_args_is_help=True
)

# 创建run子命令组
run_cli = typer.Typer(help="运行不同模式的MCPStore服务")
app_cli.add_typer(run_cli, name="run")

def version_callback(value: bool):
    """版本信息回调"""
    if value:
        console.print("[bold green]MCPStore[/bold green] version [bold]1.0.0[/bold]")
        raise typer.Exit()

@app_cli.callback()
def global_options(
    version: Annotated[
        bool,
        typer.Option("--version", "-v", help="显示版本信息", callback=version_callback)
    ] = False,
):
    """
    MCPStore - 多功能服务管理平台

    支持API模式、Help模式和Web模式（开发中）
    """
    pass

@run_cli.command("api")
def run_api(
    host: Annotated[
        str, typer.Option(help="绑定的主机地址")
    ] = "0.0.0.0",
    port: Annotated[
        int, typer.Option(help="绑定的端口号")
    ] = 18611,
    reload: Annotated[
        bool,
        typer.Option(help="启用自动重载")
    ] = False,
    log_level: Annotated[
        str,
        typer.Option(
            help="日志级别",
            case_sensitive=False
        )
    ] = "info",
    workers: Annotated[
        int,
        typer.Option(help="工作进程数")
    ] = 1,
):
    """启动 MCPStore API 服务"""
    try:
        cli_logger.info("正在启动API服务...")
        cli_logger.info(f"配置信息: Host={host}, Port={port}, Reload={reload}, LogLevel={log_level}, Workers={workers}")
        
        # 显示启动信息
        console.print(f"""
[bold green]MCPStore API服务[/bold green]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[bold]主机地址:[/bold] {host}
[bold]端口号:[/bold] {port}
[bold]自动重载:[/bold] {'启用' if reload else '禁用'}
[bold]日志级别:[/bold] {log_level.upper()}
[bold]工作进程:[/bold] {workers}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
        
        # 启动Uvicorn服务器
        uvicorn.run(
            "mcpstore.scripts.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level.lower(),
            workers=workers
        )
    except Exception as e:
        cli_logger.error(f"启动API服务时发生错误: {str(e)}")
        raise typer.Exit(1)

@run_cli.command("web")
def run_web(
    host: Annotated[
        str, typer.Option(help="绑定的主机地址")
    ] = "0.0.0.0",
    port: Annotated[
        int, typer.Option(help="绑定的端口号")
    ] = 18612,
    dev: Annotated[
        bool,
        typer.Option(help="启用开发模式")
    ] = False,
):
    """启动 MCPStore Web 界面 (开发中)"""
    console.print("""
[yellow]Web模式正在开发中...[/yellow]

计划功能:
• 图形化服务管理界面
• 实时服务状态监控
• 工具调用可视化
• 配置文件在线编辑
• 用户权限管理
    """)
    raise typer.Exit()

@app_cli.command()
def help(
    topic: Annotated[
        str,
        typer.Argument(help="帮助主题", show_default=False)
    ] = None
):
    """显示帮助信息"""
    topics = {
        "api": {
            "title": "API模式使用说明",
            "content": [
                ("启动API服务", "mcpstore run api"),
                ("指定端口启动", "mcpstore run api --port 8000"),
                ("启用自动重载", "mcpstore run api --reload"),
                ("设置日志级别", "mcpstore run api --log-level debug"),
                ("多进程模式", "mcpstore run api --workers 4")
            ]
        },
        "web": {
            "title": "Web模式使用说明 (开发中)",
            "content": [
                ("启动Web界面", "mcpstore run web"),
                ("指定端口启动", "mcpstore run web --port 8080"),
                ("开发模式启动", "mcpstore run web --dev")
            ]
        },
        "config": {
            "title": "配置说明",
            "content": [
                ("配置文件位置", "src/mcpstore/data/mcp.json"),
                ("服务配置", "在mcp.json中配置服务信息"),
                ("工具配置", "在mcp.json中配置工具信息"),
                ("日志配置", "在logs目录下查看日志文件")
            ]
        }
    }

    if topic is None:
        # 显示所有可用主题
        table = Table(title="MCPStore帮助主题")
        table.add_column("主题", style="cyan")
        table.add_column("描述", style="green")
        
        for t in topics.keys():
            table.add_row(t, topics[t]["title"])
        
        console.print(table)
        return

    if topic.lower() not in topics:
        console.print(f"[red]错误: 未知的帮助主题 '{topic}'[/red]")
        return

    # 显示特定主题的帮助信息
    selected_topic = topics[topic.lower()]
    table = Table(title=selected_topic["title"])
    table.add_column("说明", style="cyan")
    table.add_column("示例", style="green")
    
    for item in selected_topic["content"]:
        table.add_row(item[0], item[1])
    
    console.print(table)

def main():
    """CLI主入口函数"""
    try:
        cli_logger.info("MCPStore CLI启动")
        app_cli()
    except Exception as e:
        cli_logger.error(f"CLI执行错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
