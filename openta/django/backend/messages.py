# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Response messages."""

ERROR = "error"
WARNING = "warning"
INFO = "info"
SUCCESS = "success"


def error(content):
    return message_(content, ERROR)


def warning(content):
    return message_(content, WARNING)


def info(content):
    return message_(content, INFO)


def success(content):
    return message_(content, SUCCESS)


def message_(content, level="info"):
    """Create response message.

    Args:
        content (str): Message content.
        level (str): Message urgency level. One of messages.{ERROR, WARNING, INFO, SUCCESS}.

    Returns:
        tuple: Message tuple.

    """
    return (level, content)


def embed_messages(messages):
    """Create dict suitable for a Response.

    Args:
        messages (list(tuple)): List of messages.

    Returns:
        dict: Dict suitable for serialization in a Response call.

    """
    return dict(messages=messages)
