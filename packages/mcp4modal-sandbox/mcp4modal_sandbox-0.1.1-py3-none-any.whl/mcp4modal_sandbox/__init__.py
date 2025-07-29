import click 
import asyncio 
from typing import List
from dotenv import load_dotenv

from mcp4modal_sandbox.backend.mcp_server import MCPServer
from mcp4modal_sandbox.settings import MCPServerSettings


@click.command()
@click.option("--app_name", type=str, help="The name of the Modal app namespace")
@click.option("--mcp_host", type=str, default="0.0.0.0", help="The host of the MCP server", envvar="MCP_HOST")
@click.option("--mcp_port", type=int, default=8000, help="The port of the MCP server", envvar="MCP_PORT")
@click.option("--modal_token_id", type=str, help="The token id of the modal", envvar="MODAL_TOKEN_ID")
@click.option("--modal_token_secret", type=str, help="The token secret of the modal", envvar="MODAL_TOKEN_SECRET")
@click.option("--transport", type=click.Choice(['stdio', 'streamable-http', 'sse']), default='stdio', help="The transport to use for the MCP server")
@click.option("--preloaded_secrets", "-s", type=str, multiple=True, help="The secrets to preload into the sandbox", default=None)
@click.option("--max_workers", type=int, default=64, help="The maximum number of workers(threads) to use for the MCP server", envvar="MAX_WORKERS")
def main(
    app_name: str, 
    mcp_host: str, 
    mcp_port: int, 
    modal_token_id: str, 
    modal_token_secret: str, 
    transport: str = 'stdio',
    preloaded_secrets: List[str] = None,
    max_workers: int = 64):


    mcp_settings = MCPServerSettings(
        mcp_host=mcp_host,
        mcp_port=mcp_port,
        modal_token_id=modal_token_id,
        modal_token_secret=modal_token_secret
    )
    async def run_loop():
        mcp_server = MCPServer(app_name, mcp_settings, preloaded_secrets, max_workers)
        async with mcp_server as mcp:
            await mcp.run_mcp(transport)
    asyncio.run(run_loop())


if __name__ == "__main__":
    load_dotenv()
    main()
