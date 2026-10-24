import asyncio
import json
import threading

from langchain_core.tools import StructuredTool
from pydantic import create_model

from mcp import Client

from mcp_integration.client import SERVER


def _run_async(coroutine):
    """
    Run an async coroutine from synchronous code.
    """

    try:
        asyncio.get_running_loop()

    except RuntimeError:
        return asyncio.run(coroutine)

    result = {}
    error = {}

    def runner():
        try:
            result["value"] = asyncio.run(
                coroutine
            )
        except Exception as exc:
            error["value"] = exc

    thread = threading.Thread(
        target=runner
    )

    thread.start()
    thread.join()

    if "value" in error:
        raise error["value"]

    return result.get("value")


async def _call_mcp_tool(
    tool_name: str,
    arguments: dict
):
    """
    Call an MCP tool through the MCP client.
    """

    async with Client(SERVER) as client:

        result = await client.call_tool(
            tool_name,
            arguments
        )

        return result


def call_mcp_tool(
    tool_name: str,
    arguments: dict
):
    """
    Synchronous wrapper around the asynchronous
    MCP tool call.
    """

    result = _run_async(
        _call_mcp_tool(
            tool_name,
            arguments
        )
    )

    contents = []

    for content in result.content:

        text = getattr(
            content,
            "text",
            None
        )

        if text is not None:
            contents.append(text)

    if not contents:
        return {}

    combined = "\n".join(
        contents
    )

    try:
        return json.loads(
            combined
        )

    except json.JSONDecodeError:
        return combined


def _python_type_from_schema(
    schema: dict
):
    """
    Convert a simple JSON schema type
    into a Python type.
    """

    schema_type = schema.get(
        "type",
        "string"
    )

    if schema_type == "integer":
        return int

    if schema_type == "number":
        return float

    if schema_type == "boolean":
        return bool

    return str


def create_mcp_langchain_tool(
    mcp_tool
):
    """
    Convert an MCP tool definition into
    a LangChain StructuredTool.
    """

    input_schema = (
        mcp_tool.input_schema
        or {}
    )

    properties = input_schema.get(
        "properties",
        {}
    )

    required = set(
        input_schema.get(
            "required",
            []
        )
    )

    fields = {}

    for field_name, field_schema in properties.items():

        python_type = _python_type_from_schema(
            field_schema
        )

        if field_name in required:

            fields[field_name] = (
                python_type,
                ...
            )

        else:

            default = field_schema.get(
                "default",
                None
            )

            fields[field_name] = (
                python_type,
                default
            )

    args_schema = create_model(
        f"{mcp_tool.name}Input",
        **fields
    )

    def execute(**kwargs):

        return call_mcp_tool(
            mcp_tool.name,
            kwargs
        )

    return StructuredTool.from_function(
        func=execute,
        name=mcp_tool.name,
        description=mcp_tool.description
        or f"MCP tool: {mcp_tool.name}",
        args_schema=args_schema
    )


async def discover_mcp_langchain_tools():
    """
    Discover all MCP tools and convert them
    into LangChain tools.
    """

    async with Client(SERVER) as client:

        result = await client.list_tools()

        return [
            create_mcp_langchain_tool(
                tool
            )
            for tool in result.tools
        ]


def get_mcp_langchain_tools():
    """
    Synchronous entry point for discovering
    all MCP-backed LangChain tools.
    """

    return _run_async(
        discover_mcp_langchain_tools()
    )


if __name__ == "__main__":

    tools = get_mcp_langchain_tools()

    print("\nMCP → LangChain tools:")

    for tool in tools:

        print(
            f"- {tool.name}"
        )