from typing import Annotated, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


def merge_token_mappings(
    existing: dict[str, str],
    new: dict[str, str]
) -> dict[str, str]:
    """
    Merge existing privacy token mappings with
    mappings created during the current turn.
    """

    return {
        **existing,
        **new
    }


class AgentGraphState(TypedDict):

    messages: Annotated[
        list[AnyMessage],
        add_messages
    ]

    route: Literal[
        "banking",
        "web"
    ]

    token_mapping: Annotated[
        dict[str, str],
        merge_token_mappings
    ]

    pending_action: dict | None