import asyncio
from .mcp_instance import mcp
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from . import tools
from . import utils

tools.register_tools()


def get_server_config():
    return InitializationOptions(
        server_name="mcp_shippalm",
        server_version="1.0.0",
        capabilities=mcp.get_capabilities(
            notification_options=NotificationOptions(resources_changed=True),
            experimental_capabilities={},
        ),
    )

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            get_server_config()
        )

if __name__ == "__main__":
    asyncio.run(main())
