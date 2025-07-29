# one_chat_platform/__init__.py

from .one_chat_platform import OneChatPlatform

ONE_CHAT_PLATFORM_INSTANCE = None
DEFAULT_TO = None


def init(authorization_token: str, to: str = None):
    global ONE_CHAT_PLATFORM_INSTANCE, DEFAULT_TO
    ONE_CHAT_PLATFORM_INSTANCE = OneChatPlatform(authorization_token)
    DEFAULT_TO = to


def send_message(
    token: str = None,
    to: str = None,
    message: str = None,
    custom_notification: str = None,
):
    global ONE_CHAT_PLATFORM_INSTANCE, DEFAULT_TO
    if token:
        ONE_CHAT_PLATFORM_INSTANCE = OneChatPlatform(token)
    elif ONE_CHAT_PLATFORM_INSTANCE is None:
        raise Exception(
            "OneChat is not initialized. Call init(token, to, bot_id) first."
        )

    to = to or DEFAULT_TO

    if not to:
        raise ValueError(
            "Both 'to' must be provided either during initialization or when calling this method."
        )

    return ONE_CHAT_PLATFORM_INSTANCE.send_message(to, message, custom_notification)
