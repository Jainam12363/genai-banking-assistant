from langchain_core.messages import HumanMessage, ToolMessage

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from graph.state import AgentGraphState

from graph.nodes import (
    privacy_input_node,
    privacy_output_node,
    router_node,
    banking_agent_node,
    web_research_agent_node,
    create_banking_tool_node,
    route_after_banking_agent,
    route_after_banking_tools
)

from agents.banking_agent import get_banking_tools

from services.checkpoint_service import (
    create_checkpointer
)


_checkpointer_context = create_checkpointer()

_checkpointer = (
    _checkpointer_context.__enter__()
)


def route_after_router(
    state: AgentGraphState
):
    """
    Return the destination selected by the Router.
    """

    return state["route"]


def action_confirmation_node(
    state: AgentGraphState
) -> dict:
    """
    Stop the banking workflow while a state-changing
    action waits for user confirmation.
    """

    return {
        "pending_action": state.get("pending_action")
    }


def create_agent_graph():
    """
    Build and compile the complete V2
    multi-agent LangGraph workflow.
    """

    builder = StateGraph(
        AgentGraphState
    )

    builder.add_node(
        "privacy_input",
        privacy_input_node
    )

    builder.add_node(
        "router",
        router_node
    )

    builder.add_node(
        "banking_agent",
        banking_agent_node
    )

    builder.add_node(
        "web_research_agent",
        web_research_agent_node
    )

    builder.add_node(
        "privacy_output",
        privacy_output_node
    )

    builder.add_node(
        "tools",
        create_banking_tool_node()  #this will return the privacy aware banking tool node instead of the original banking tool node
    )

    builder.add_node(
        "action_confirmation",
        action_confirmation_node
    )

    builder.add_edge(
        START,
        "privacy_input"
    )

    builder.add_edge(
        "privacy_input",
        "router"
    )

    builder.add_conditional_edges(
        "router",
        route_after_router,
        {
            "banking": "banking_agent",
            "web": "web_research_agent"
        }
    )

    builder.add_conditional_edges(
        "banking_agent",
        route_after_banking_agent,
        {
            "tools": "tools",
            "end": "privacy_output"
        }
    )

    builder.add_conditional_edges(
        "tools",
        route_after_banking_tools,
        {
            "banking_agent": "banking_agent",
            "confirmation": "action_confirmation"
        }
    )

    builder.add_edge(
        "action_confirmation",
        END
    )

    builder.add_edge(
        "web_research_agent",
        "privacy_output"
    )

    return builder.compile(
        checkpointer=_checkpointer
    )


def get_pending_action(thread_id: str):
    """
    Retrieve the pending state-changing action for a conversation.
    """

    if not thread_id or not thread_id.strip():
        return None

    graph = create_agent_graph()

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    state = graph.get_state(config)

    if not state or not state.values:
        return None

    return state.values.get(
        "pending_action"
    )


def confirm_pending_action(thread_id: str):
    """
    Execute the pending state-changing action after
    explicit user confirmation and resume the graph.
    """

    if not thread_id or not thread_id.strip():
        return {
            "success": False,
            "error": "Thread ID cannot be empty."
        }

    graph = create_agent_graph()

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    state = graph.get_state(config)

    if not state or not state.values:
        return {
            "success": False,
            "error": "Conversation state not found."
        }

    pending_action = state.values.get(
        "pending_action"
    )

    if not pending_action:
        return {
            "success": False,
            "error": "No pending action requires confirmation."
        }

    tool_name = pending_action.get(
        "tool_name"
    )

    arguments = pending_action.get(
        "arguments",
        {}
    )

    tool_call_id = pending_action.get(
        "tool_call_id"
    )

    if not tool_name or not tool_call_id:
        return {
            "success": False,
            "error": "Invalid pending action."
        }

    # ---------------------------------------------------------
    # Find the exact MCP-backed banking action tool
    # ---------------------------------------------------------

    banking_tools = get_banking_tools()

    selected_tool = None

    for tool in banking_tools:

        if tool.name == tool_name:
            selected_tool = tool
            break

    if selected_tool is None:
        return {
            "success": False,
            "error": (
                f"Action tool '{tool_name}' "
                "is not available."
            )
        }

    # ---------------------------------------------------------
    # Execute the action ONLY after confirmation
    # ---------------------------------------------------------

    try:

        tool_result = selected_tool.invoke(
            arguments
        )

    except Exception as exc:

        print(
            f"Confirmed action failed: "
            f"{type(exc).__name__}: {exc}"
        )

        return {
            "success": False,
            "error": "The requested action could not be completed."
        }

    # ---------------------------------------------------------
    # Add the tool result to the checkpointed conversation
    # ---------------------------------------------------------

    tool_message = ToolMessage(
        content=str(tool_result),
        tool_call_id=tool_call_id
    )

    graph.update_state(
        config,
        {
            "messages": [
                tool_message
            ],
            "pending_action": None
        },
        as_node="tools"
    )

    # ---------------------------------------------------------
    # Do not send the completed action back through the
    # Banking Agent. The action has already been executed
    # after explicit user confirmation.
    # ---------------------------------------------------------

    return {
        "success": True,
        "result": {
            "messages": [
                {
                    "type": "ai",
                    "content": (
                        f"✅ The requested action "
                        f"**{tool_name.replace('_', ' ')}** "
                        f"was completed successfully."
                    )
                }
            ]
        }
    }


def cancel_pending_action(thread_id: str):
    """
    Cancel the pending state-changing action without
    executing it.
    """

    if not thread_id or not thread_id.strip():
        return {
            "success": False,
            "error": "Thread ID cannot be empty."
        }

    graph = create_agent_graph()

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    state = graph.get_state(config)

    if not state or not state.values:
        return {
            "success": False,
            "error": "Conversation state not found."
        }

    pending_action = state.values.get(
        "pending_action"
    )

    if not pending_action:
        return {
            "success": False,
            "error": "No pending action to cancel."
        }

    tool_call_id = pending_action.get(
        "tool_call_id"
    )

    if not tool_call_id:
        return {
            "success": False,
            "error": "Invalid pending action."
        }

    # Add an internal tool result so the previous
    # tool call is completed without executing it.
    cancellation_message = ToolMessage(
        content="Action cancelled by the user.",
        tool_call_id=tool_call_id
    )

    graph.update_state(
        config,
        {
            "messages": [
                cancellation_message
            ],
            "pending_action": None
        },
        as_node="tools"
    )

    return {
        "success": True
    }



def invoke_agent_graph(
    user_message: str,
    thread_id: str
) -> dict:
    """
    Invoke the complete V2 multi-agent graph.
    """

    try:

        if not user_message or not user_message.strip():

            return {
                "success": False,
                "error": "User message cannot be empty."
            }

        if not thread_id or not thread_id.strip():

            return {
                "success": False,
                "error": "Thread ID cannot be empty."
            }

        graph = create_agent_graph()

        initial_state: AgentGraphState = {
            "messages": [
                HumanMessage(
                    content=user_message
                )
            ],
            "route": "banking",
            "token_mapping": {}
        }

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        result = graph.invoke(
            initial_state,
            config=config
        )

        return {
            "success": True,
            "result": result
        }

    except Exception as exc:

        print(
            f"Multi-Agent Graph error: "
            f"{type(exc).__name__}: {exc}"
        )

        return {
            "success": False,
            "error": (
                "The Multi-Agent Graph could "
                "not complete the request."
            )
        }


def get_agent_conversation_history(thread_id: str):
    """
    Retrieve the conversation history for a given thread ID.
    """
    graph = create_agent_graph()

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    state_snapshot = graph.get_state(config)

    values = state_snapshot.values

    messages = values.get("messages", [])
    token_mapping = values.get("token_mapping", {})

    history = []

    for message in messages:
        message_type = getattr(message, "type", None)
        content = getattr(message, "content", "")

        # Ignore empty AI messages generated during tool calls
        if not content:
            continue

        # Only return messages that should be visible to the user
        if message_type == "human":
            role = "user"

        elif message_type == "ai":
            role = "assistant"

        else:
            continue

        # Restore anonymized values for conversation display
        if token_mapping and isinstance(content, str):
            for token, original_value in token_mapping.items():
                content = content.replace(token, original_value)

        history.append({
            "role": role,
            "content": content
        })

    return {
        "success": True,
        "messages": history
    }



def stream_final_agent_response(
    user_message: str,
    thread_id: str
):
    """
    Stream the final assistant response progressively.

    Banking Agent:
        Streams AIMessageChunk tokens.

    Web Research Agent:
        The agent internally runs its own tool-calling flow,
        so its final response is captured from the outer graph
        node update.

    Privacy tokens are resolved before being shown to the user.
    """

    if not user_message or not user_message.strip():
        return

    if not thread_id or not thread_id.strip():
        return

    graph = create_agent_graph()

    initial_state: AgentGraphState = {
        "messages": [
            HumanMessage(
                content=user_message
            )
        ],
        "route": "banking",
        "token_mapping": {}
    }

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    buffer = ""

    # Prevent the Web Research response from being emitted
    # more than once.
    web_response_emitted = False

    def process_stream_buffer(
        text: str,
        token_mapping: dict
    ):
        nonlocal buffer

        buffer += text
        output = ""

        while True:

            start = buffer.find("[")

            if start == -1:
                output += buffer
                buffer = ""
                break

            output += buffer[:start]

            end = buffer.find("]", start)

            if end == -1:
                buffer = buffer[start:]
                break

            token = buffer[start:end + 1]

            if token in token_mapping:
                output += token_mapping[token]
            else:
                output += token

            buffer = buffer[end + 1:]

            if not buffer:
                break

        return output

    # We need both:
    #
    # messages -> normal LLM token streaming
    # updates  -> final result returned by the Web Research Agent
    #
    for stream_mode, stream_data in graph.stream(
        initial_state,
        config=config,
        stream_mode=["messages", "updates"]
    ):

        # ---------------------------------------------------------
        # 1. Normal AI message streaming
        # ---------------------------------------------------------

        if stream_mode == "messages":

            message_chunk, metadata = stream_data

            if type(message_chunk).__name__ != "AIMessageChunk":
                continue

            content = getattr(
                message_chunk,
                "content",
                ""
            )

            if not content:
                continue

            node_name = metadata.get(
                "langgraph_node"
            )

            if node_name not in {
                "banking_agent",
                "web_research_agent"
            }:
                continue

            if getattr(
                message_chunk,
                "tool_calls",
                None
            ):
                continue

            if not isinstance(content, str):
                continue

            # For Web Research Agent, the final response is
            # handled through the "updates" stream below.
            # Therefore, do not emit it here.
            if node_name == "web_research_agent":
                continue

            state_snapshot = graph.get_state(
                config
            )

            token_mapping = state_snapshot.values.get(
                "token_mapping",
                {}
            )

            safe_text = process_stream_buffer(
                content,
                token_mapping
            )

            if safe_text:
                yield safe_text

        # ---------------------------------------------------------
        # 2. Outer graph node updates
        # ---------------------------------------------------------

        elif stream_mode == "updates":

            # Web Research response has already been emitted.
            if web_response_emitted:
                continue

            updates = stream_data

            if not isinstance(updates, dict):
                continue

            web_update = updates.get(
                "web_research_agent"
            )

            if not web_update:
                continue

            messages = web_update.get(
                "messages",
                []
            )

            if not messages:
                continue

            # Find the final AI message returned by the
            # Web Research Agent.
            final_message = None

            for message in reversed(messages):

                if type(message).__name__ != "AIMessage":
                    continue

                content = getattr(
                    message,
                    "content",
                    ""
                )

                if (
                    isinstance(content, str)
                    and content.strip()
                ):
                    final_message = message
                    break

            if final_message is None:
                continue

            content = final_message.content

            state_snapshot = graph.get_state(
                config
            )

            token_mapping = state_snapshot.values.get(
                "token_mapping",
                {}
            )

            safe_text = process_stream_buffer(
                content,
                token_mapping
            )

            if safe_text:
                web_response_emitted = True
                yield safe_text

    # -------------------------------------------------------------
    # Flush remaining buffered text
    # -------------------------------------------------------------

    if buffer:

        state_snapshot = graph.get_state(
            config
        )

        token_mapping = state_snapshot.values.get(
            "token_mapping",
            {}
        )

        final_text = process_stream_buffer(
            "",
            token_mapping
        )

        if final_text:
            yield final_text