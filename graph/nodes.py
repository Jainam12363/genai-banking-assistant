from langgraph.prebuilt import (
    ToolNode,
    tools_condition
)

from langchain_core.messages import ToolMessage, AIMessage

from privacy import (
    process_text,
    resolve_tool_arguments,
    process_agent_response,
    anonymize_with_existing_mapping
)

from graph.state import AgentGraphState

from agents.banking_agent import (
    create_banking_llm_with_tools,
    get_banking_tools
)

from agents.web_research_agent import (
    create_web_research_agent,
    invoke_web_research_agent
)

from graph.router import (
    classify_intent
)


ACTION_TOOL_NAMES = {
    "freeze_account",
    "unfreeze_account",
    "update_customer_phone",
    "update_customer_email",
    "block_card",
    "unblock_card",
    "create_support_ticket",
    "update_support_ticket",
}



def router_node(
    state: AgentGraphState
) -> dict:
    """
    Classify the user's request and store the
    selected route in the graph state.
    """

    route = classify_intent(
        state["messages"]
    )

    return {
        "route": route
    }


def banking_agent_node(
    state: AgentGraphState
) -> dict:
    """
    Execute the Banking LLM inside the LangGraph workflow.

    The LLM can generate banking tool calls, but the tools
    themselves are executed by the separate privacy-aware
    banking tool node.
    """

    llm = create_banking_llm_with_tools()

    response = llm.invoke(
        state["messages"]
    )

    return {
        "messages": [response]
    }

def web_research_agent_node(state):
    """
    Execute the Web Research Agent using the anonymized
    user query from the graph state.
    """

    messages = state.get("messages", [])

    if not messages:
        return {
            "messages": []
        }

    # The latest message is the anonymized user query.
    user_message = messages[-1].content

    result = invoke_web_research_agent(
        user_message
    )

    if not result.get("success"):
        response = result.get(
            "error",
            "The Web Research Agent could not complete the request."
        )
    else:
        response = result.get(
            "response",
            ""
        )

    return {
        "messages": [
            AIMessage(
                content=response
            )
        ]
    }


def create_banking_tool_node():
    """
    Create a privacy-aware banking tool node.

    Read-only tools execute immediately.

    State-changing action tools do NOT execute immediately.
    Instead, their requested action is stored in graph state so
    the UI can ask the user for confirmation first.
    """

    tools = get_banking_tools()

    tool_map = {
        tool.name: tool
        for tool in tools
    }

    def banking_tool_node(
        state: AgentGraphState
    ) -> dict:
        """
        Execute read-only tools immediately.

        For action tools:
        - Resolve anonymized arguments.
        - Store the proposed action in pending_action.
        - Do NOT execute the tool.
        """

        messages = state["messages"]

        if not messages:
            return {
                "messages": []
            }

        last_message = messages[-1]

        tool_calls = getattr(
            last_message,
            "tool_calls",
            []
        )

        if not tool_calls:
            return {
                "messages": []
            }

        tool_messages = []

        for tool_call in tool_calls:

            tool_name = tool_call["name"]

            tool = tool_map.get(
                tool_name
            )

            if tool is None:

                tool_messages.append(
                    ToolMessage(
                        content=(
                            f"Unknown banking tool: "
                            f"{tool_name}"
                        ),
                        tool_call_id=tool_call["id"]
                    )
                )

                continue

            arguments = tool_call.get(
                "args",
                {}
            )

            # Resolve anonymized PII tokens before
            # processing the tool request.
            resolved_arguments = (
                resolve_tool_arguments(
                    arguments,
                    state.get(
                        "token_mapping",
                        {}
                    )
                )
            )

            # -----------------------------------------------------
            # STATE-CHANGING ACTION
            # -----------------------------------------------------

            if tool_name in ACTION_TOOL_NAMES:

                return {
                    "pending_action": {
                        "tool_name": tool_name,
                        "arguments": resolved_arguments,
                        "tool_call_id": tool_call["id"],
                        "action_type": tool_name
                    }
                }

            # -----------------------------------------------------
            # READ-ONLY TOOL
            # -----------------------------------------------------

            try:

                result = tool.invoke(
                    resolved_arguments
                )

                tool_result = str(
                    result
                )

                # Never expose real PII from the MCP
                # tool result back to the LLM.
                safe_tool_result = (
                    anonymize_with_existing_mapping(
                        tool_result,
                        state.get(
                            "token_mapping",
                            {}
                        )
                    )
                )

                tool_messages.append(
                    ToolMessage(
                        content=safe_tool_result,
                        tool_call_id=tool_call["id"]
                    )
                )

            except Exception as exc:

                tool_messages.append(
                    ToolMessage(
                        content=(
                            "Banking MCP tool execution "
                            "failed: "
                            f"{type(exc).__name__}"
                        ),
                        tool_call_id=tool_call["id"]
                    )
                )

        return {
            "messages": tool_messages
        }

    return banking_tool_node


def route_after_banking_agent(
    state: AgentGraphState
):
    """
    Decide whether the Banking Agent wants to
    execute a banking tool or finish.
    """

    route = tools_condition(state)

    if route == "tools":
        return "tools"

    return "end"


def route_after_banking_tools(
    state: AgentGraphState
):
    """
    Decide what to do after the banking tool node.

    If a state-changing action is pending, route to
    the confirmation node.

    Otherwise continue to the Banking Agent.
    """

    if state.get("pending_action"):
        return "confirmation"

    return "banking_agent"


def privacy_input_node(
    state: AgentGraphState
) -> dict:
    """
    Detect and anonymize PII in the user's latest message
    before the message reaches the Router or an AI agent.
    """

    messages = state["messages"]

    existing_mapping = state.get(
        "token_mapping",
        {}
    )

    if not messages:

        return {
            "token_mapping": existing_mapping
        }

    user_message = messages[-1]

    content = user_message.content

    if not isinstance(content, str):

        return {
            "token_mapping": existing_mapping
        }

    privacy_result = process_text(
        content
    )

    print("\n" + "=" * 60)
    print("🔐 PRIVACY INPUT")
    print("=" * 60)
    print(f"Original Query   : {content}")
    print(f"Anonymized Query : {privacy_result.anonymized_text}")
    print(f"PII Detected     : {len(privacy_result.entities)} entity/entities")
    print("=" * 60)

    user_message.content = (
        privacy_result.anonymized_text
    )

    combined_mapping = {
        **existing_mapping,
        **privacy_result.token_mapping
    }

    return {
        "messages": [
            user_message
        ],
        "token_mapping": combined_mapping
    }


def privacy_output_node(
    state: AgentGraphState
) -> dict:
    """
    Validate and de-anonymize the final agent response
    before it is returned to the user.
    """

    messages = state["messages"]

    if not messages:

        return {
            "messages": []
        }

    last_message = messages[-1]

    content = last_message.content

    if not isinstance(content, str):

        return {
            "messages": messages
        }

    final_response = process_agent_response(
        content,
        state.get(
            "token_mapping",
            {}
        )
    )

    print("\n" + "=" * 60)
    print("🔓 PRIVACY OUTPUT")
    print("=" * 60)
    print(f"Agent Response  : {content}")
    print(f"Final Response  : {final_response}")
    print("=" * 60)

    last_message.content = final_response

    return {
        "messages": messages
    }