
from langchain_groq import ChatGroq

from config import (
    GROQ_API_KEY,
    LLM_MODEL
)

from agents.prompts import (
    WEB_RESEARCH_AGENT_SYSTEM_PROMPT
)

from mcp_integration.langchain_tools import get_mcp_langchain_tools


MAX_AGENT_TOKENS = 700


def create_llm():
    """
    Create the LLM used by the Web Research Agent.
    """

    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=LLM_MODEL,
        temperature=0,
        max_tokens=MAX_AGENT_TOKENS
    )


def get_web_tools():
    """
    Discover and return the MCP-backed tools used by the Web Research Agent.
    The Web Research Agent has access to exactly one official-source
    web-search tool.
    """

    tools = get_mcp_langchain_tools()

    return [
        tool for tool in tools
        if tool.name == "search_official_web"
    ]

def create_web_research_agent():
    return create_llm()


def extract_final_response(result: dict) -> str:
    """
    Extract the final textual response from
    the agent result.
    """

    messages = result.get(
        "messages",
        []
    )

    for message in reversed(messages):

        content = getattr(
            message,
            "content",
            ""
        )

        if isinstance(content, str) and content.strip():

            return content.strip()

    return ""


def invoke_web_research_agent(user_message: str):
    try:
        if not user_message or not user_message.strip():
            return {
                "success": False,
                "error": "User message cannot be empty."
            }

        llm = create_llm()
        tool = get_web_tools()[0]

        # ---------------------------------------------------------
        # STEP 1: Ask the LLM to generate exactly one search query
        # ---------------------------------------------------------
        search_llm = llm.bind_tools([tool])

        first_response = search_llm.invoke([
            {
                "role": "system",
                "content": WEB_RESEARCH_AGENT_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_message.strip()
            }
        ])

        tool_calls = first_response.tool_calls

        if not tool_calls:
            return {
                "success": False,
                "error": "The Web Research Agent did not generate a search request."
            }

        tool_call = tool_calls[0]

        if tool_call["name"] != "search_official_web":
            return {
                "success": False,
                "error": "The Web Research Agent requested an unsupported tool."
            }

        search_arguments = tool_call["args"]

        # ---------------------------------------------------------
        # STEP 2: Execute exactly one official-source search
        # ---------------------------------------------------------
        tool_result = tool.invoke(search_arguments)

        # ---------------------------------------------------------
        # STEP 3: Ask the LLM for the final answer WITHOUT tools
        # ---------------------------------------------------------
        final_response = llm.invoke([
            {
                "role": "system",
                "content": WEB_RESEARCH_AGENT_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": (
                    f"User question:\n{user_message.strip()}\n\n"
                    f"Official search results:\n{tool_result}\n\n"
                    "Using ONLY the official search results above, "
                    "provide the final answer to the user's question. "
                    "Do not perform another search."
                )
            }
        ])

        answer = final_response.content

        if not answer or not answer.strip():
            return {
                "success": False,
                "error": "The Web Research Agent returned an empty response."
            }

        return {
            "success": True,
            "response": answer.strip()
        }

    except Exception as e:
        print(
            f"Web Research Agent error: {type(e).__name__}: {e}"
        )

        return {
            "success": False,
            "error": "The Web Research Agent could not complete the request."
        }