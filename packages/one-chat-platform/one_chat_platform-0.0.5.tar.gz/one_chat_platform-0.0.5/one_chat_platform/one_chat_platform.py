from .message_sender import MessageSender


class OneChatPlatform:
    def __init__(self, authorization_token: str):
        self.message_sender = MessageSender(authorization_token)

    def send_message(
        self, to: str, bot_id: str, message: str, custom_notification: str = None
    ):
        return self.message_sender.send_message(
            to, bot_id, message, custom_notification
        )