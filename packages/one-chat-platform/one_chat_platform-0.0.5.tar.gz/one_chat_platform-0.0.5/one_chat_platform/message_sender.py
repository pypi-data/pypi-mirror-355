# one_chat_platform/message_sender.py

import requests
import json

class MessageSender:
    def __init__(self, authorization_token: str):
        self.base_url = "https://one-platform.one.th/chat/api/v1/chatbot-api/message"
        self.headers = {
            "Authorization": f"Bearer {authorization_token}",
            "Content-Type": "application/json",
        }

    def send_message(
        self, to: str, message: str, custom_notification: str = None, *args
    ) -> dict:
        payload = {"to": to, "type": "text", "message": message}
        if custom_notification:
            payload["custom_notification"] = custom_notification

        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)

            if response.status_code == 200:
                return json.dumps(response.json(), indent=4)
            else:
                raise Exception(f"Request failed with status {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            return {"status": "fail", "message": f"Request failed: {str(e)}"}