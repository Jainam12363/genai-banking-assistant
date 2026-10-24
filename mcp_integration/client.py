import anyio

from mcp import Client, StdioServerParameters


SERVER = StdioServerParameters(
    command="python",
    args=[
        "-m",
        "mcp_integration.server"
    ]
)


async def get_mcp_tools():
    """
    Connect to the MCP server and discover
    all available MCP tools.
    """

    async with Client(SERVER) as client:

        result = await client.list_tools()

        return result.tools


async def call_mcp_tool(
    tool_name: str,
    arguments: dict
):
    """
    Connect to the MCP server and execute
    an MCP tool.
    """

    async with Client(SERVER) as client:

        result = await client.call_tool(
            tool_name,
            arguments
        )

        return result


async def main():

    print("\nConnecting to MCP server...")

    tools = await get_mcp_tools()

    print("\nDiscovered MCP tools:")

    for tool in tools:
        print(
            f"- {tool.name}"
        )

    print(
        f"\nTotal tools discovered: {len(tools)}"
    )

    print("\nTesting MCP tool call...")

    result = await call_mcp_tool(
        "calculate_banking",
        {
            "calculation_type": "emi",
            "principal": 500000,
            "annual_rate": 8.5,
            "tenure_months": 60
        }
    )

    print("\nMCP tool result:")

    for content in result.content:
        print(content)


if __name__ == "__main__":
    anyio.run(main)