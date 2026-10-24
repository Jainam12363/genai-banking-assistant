from typing import Literal

from langchain_core.messages import AnyMessage


def classify_intent(
    messages: list[AnyMessage]
) -> Literal["banking", "web"]:
    """
    Classify the user's request as either
    a banking request or a web research request.
    """

    if not messages:
        return "banking"

    last_message = messages[-1]

    content = last_message.content

    if not isinstance(content, str):
        return "banking"

    text = content.lower().strip()

    banking_phrases = [
        "account",
        "balance",
        "transaction",
        "transactions",
        "customer",
        "complaint",
        "ticket",
        "loan",
        "emi",
        "beneficiary",
        "card",
        "cards",
        "branch",
        "interest",
        "payment history",
        "account status",
        "account details"
    ]

    web_phrases = [
        "latest news",
        "latest update",
        "latest updates",
        "recent news",
        "recent developments",
        "current news",
        "what is happening",
        "rbi",
        "npci",
        "upi",
        "repo rate",
        "banking industry",
        "digital banking",
        "industry trends",
        "market news"
    ]

    for phrase in banking_phrases:

        if phrase in text:
            return "banking"

    for phrase in web_phrases:

        if phrase in text:
            return "web"

    web_time_words = [
        "latest",
        "recent",
        "today",
        "current",
        "news",
        "developments",
        "guidelines",
        "announcement",
        "announcements"
    ]

    for word in web_time_words:

        if word in text:
            return "web"

    return "banking"