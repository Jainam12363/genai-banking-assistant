from privacy.resolver import resolve_token


def resolve_tool_arguments(
    arguments: dict,
    token_mapping: dict[str, str]
) -> dict:
    """
    Resolve privacy tokens inside tool arguments.
    """

    resolved_arguments = {}

    for key, value in arguments.items():

        if isinstance(value, str):

            resolved_arguments[key] = resolve_token(
                value,
                token_mapping
            )

        else:

            resolved_arguments[key] = value

    return resolved_arguments

