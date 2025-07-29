from typing import Dict, List

from flowcept.configs import AGENT
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import TextContent

MCP_HOST = AGENT.get("mcp_host", "0.0.0.0")
MCP_PORT = AGENT.get("mcp_port", 8000)

MCP_URL = f"http://{MCP_HOST}:{MCP_PORT}/mcp"


def run_tool(tool_name: str, kwargs: Dict = None) -> List[TextContent]:
    """
    Run a tool using an MCP client session via a local streamable HTTP connection.

    This function opens an asynchronous connection to a local MCP server,
    initializes a session, and invokes a specified tool with optional arguments.
    The tool's response content is returned as a list of `TextContent` objects.

    Parameters
    ----------
    tool_name : str
        The name of the tool to call within the MCP framework.
    kwargs : Dict, optional
        A dictionary of keyword arguments to pass as input to the tool. Defaults to None.

    Returns
    -------
    List[TextContent]
        A list of `TextContent` objects returned by the tool execution.

    Notes
    -----
    This function uses `asyncio.run`, so it must not be called from an already-running
    event loop (e.g., inside another async function in environments like Jupyter).
    """
    import asyncio

    async def _run():
        async with streamablehttp_client(MCP_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=kwargs)
                return result.content

    return asyncio.run(_run())
