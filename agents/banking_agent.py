from langchain.agents import create_agent
from langchain_groq import ChatGroq

from config import (
    GROQ_API_KEY,
    LLM_MODEL
)

from agents.prompts import (
    BANKING_AGENT_SYSTEM_PROMPT
)

from mcp_integration.langchain_tools import (
    get_mcp_langchain_tools
)


def create_llm():
    """
    Create and return the LLM used by the Banking Agent.
    """

    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=LLM_MODEL,
        temperature=0
    )


def get_banking_tools():
    """
    Discover and return the MCP-backed tools used by the Banking Agent.

    """

    tools = get_mcp_langchain_tools()

    banking_tool_names = {
        # Read-only banking tools
        "get_account",
        "get_transactions",
        "get_customer",
        "get_support_tickets",
        "calculate_banking",

        # State-changing banking tools
        "freeze_account",
        "unfreeze_account",
        "update_customer_phone",
        "update_customer_email",
        "block_card",
        "unblock_card",
        "create_support_ticket",
        "update_support_ticket",
    }

    return [
        tool for tool in tools
        if tool.name in banking_tool_names
    ]


def create_banking_agent():
    """
    Create and return the Banking Agent.

    The agent receives:
    - an LLM
    - MCP-backed tools
    - a system prompt

    The LLM decides when a tool should be used.
    """

    llm = create_llm()

    tools = get_banking_tools()

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=BANKING_AGENT_SYSTEM_PROMPT
    )

    return agent


def invoke_banking_agent(
    user_message: str
):
    """
    Send a user message to the Banking Agent
    and return the agent result.
    """

    try:

        if not user_message or not user_message.strip():

            return {
                "success": False,
                "error": "User message cannot be empty."
            }

        agent = create_banking_agent()

        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            }
        )

        return {
            "success": True,
            "result": result
        }

    except Exception as exc:

        print(
            f"Banking Agent error: "
            f"{type(exc).__name__}: {exc}"
        )

        return {
            "success": False,
            "error": (
                "The Banking Agent could not "
                "complete the request."
            )
        }


def create_banking_llm_with_tools():
    """
    Create the Banking LLM and bind the MCP-backed
    tools so that it can generate tool calls.

    The tools are executed separately by LangGraph.
    """

    llm = create_llm()

    tools = get_banking_tools()

    return llm.bind_tools(
        tools
    )