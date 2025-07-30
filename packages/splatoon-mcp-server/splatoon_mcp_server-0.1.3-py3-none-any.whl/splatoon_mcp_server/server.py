import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from .config import Settings
# 初始化日志和服务器
logger = logging.getLogger("splatoon-mcp-server")
logger.setLevel(logging.INFO)
server = Server("splatoon-mcp-server")
settings = Settings()
# 定义工具
tools = [
    Tool(
        name="hello_world",
        description="返回简单的问候语",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "要问候的人的姓名",
                    "default": "duang"
                }
            },
            "required": ["name"]
        }
    )
]

@server.list_tools()
async def list_tools():
    """列出所有可用工具"""
    return tools

@server.call_tool()
async def call_tool(name: str, arguments):
    """处理工具调用请求"""
    logger.info(f"收到工具调用请求：name={name}, arguments={arguments}")

    if name == "hello_world":
        name = arguments["name"]
        return [TextContent(text=f"你好，{name}！")]
    
    return [TextContent(text=f"未知工具：{name}")]

async def main():
    """主函数"""
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            capabilities=server.get_capabilities()
        )

async def main():
    """Run the server async context."""
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            InitializationOptions(
                server_name=settings.APP_NAME,
                server_version=settings.APP_VERSION,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(resources_changed=True),
                    experimental_capabilities={},
                ),
            ),
        )