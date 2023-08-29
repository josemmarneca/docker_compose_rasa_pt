import json
import logging

import requests
from sanic import Blueprint, response
from typing import Text, Any, Dict

from rasa.core.channels.channel import UserMessage, OutputChannel, InputChannel, CollectingOutputChannel

logger = logging.getLogger(__name__)


class CustomBot(OutputChannel):
    @classmethod
    def name(cls):
        return "custom"

    def __init__(self, user, password, server_url):
        from .lib.customChat import CustomChat
        logger.info("__init__  custom chat")
        self.customChat = CustomChat(user, password, server_url=server_url)

    async def send_text_message(self, recipient_id: Text, message: Dict[Text, Any],
                                **kwargs: dict) -> None:
        """Messages handler."""
        # Define the API endpoint where you want to send the message
        api_endpoint = self.customChat.server_url
        logger.info("Loging recipient_id ---> {0}".format(recipient_id))
        logger.info("Loging message ---> {0}".format(message))
        logger.info("Loging kwargs ---> {0}".format(kwargs))

        # Prepare the payload for the API request
        payload = {
            "recipient_id": recipient_id,
            "message": message,  # Assuming the message is a text message
        }
        logger.info("Loging payload ---> {0}".format(payload))
        logger.info("Loging api_endpoint ---> {0}".format(api_endpoint))

        # Send the POST request to the API
        response = requests.post(api_endpoint, json=payload)

        if response.status_code == 200:
            logger.info("Message sent successfully")
        else:
            logger.info("Failed to send message: {0}", response.text)

    async def send_image_url(self, recipient_id, image_url):
        image_attachment = [{
            "image_url": image_url,
            "collapsed": False,
        }]

        return self.customChat.chat_post_message(None,
                                                room_id=recipient_id,
                                                attachments=image_attachment)

    async def send_attachment(self, recipient_id, attachment, message=""):
        return self.customChat.chat_post_message(None,
                                                room_id=recipient_id,
                                                attachments=[attachment])

    @staticmethod
    def _convert_to_rocket_buttons(buttons):
        return [{"text": b['title'],
                 "msg": b['payload'],
                 "type": "button",
                 "msg_in_chat_window": True}
                for b in buttons]

    async def send_text_with_buttons(self, recipient_id, message, buttons,
                                     **kwargs):
        # implementation is based on
        # https://github.com/custom/Rocket.Chat/pull/11473
        # should work in rocket chat >= 0.69.0
        button_attachment = [
            {"actions": self._convert_to_rocket_buttons(buttons)}]

        return self.rocket.chat_post_message(message,
                                             room_id=recipient_id,
                                             attachments=button_attachment)

    async def send_custom_message(self, recipient_id, elements):
        return self.rocket.chat_post_message(None,
                                             room_id=recipient_id,
                                             attachments=elements)


class CustomInput(InputChannel):
    """custom input addons implementation."""

    @classmethod
    def name(cls):
        logger.info("customInput - name  cls ")
        return "custom"

    @classmethod
    def from_credentials(cls, credentials):
        logger.info("customInput - from_credentials()  from_credentials ")
        if not credentials:
            cls.raise_missing_credentials_exception()

        return cls(credentials.get("user"),
                   credentials.get("password"),
                   credentials.get("server_url"))

    def __init__(self, user: Text, password: Text, server_url: Text) -> None:

        self.user = user
        self.password = password
        self.server_url = server_url

    async def send_message(self, text, sender_name, recipient_id,
                           on_new_message):
        logger.info("send msg")
        if sender_name != self.user:
            output_channel = CustomBot(
                self.user, self.password, self.server_url)

            user_msg = UserMessage(text, output_channel, recipient_id,
                                   input_channel=self.name())
            await on_new_message(user_msg)

    def blueprint(self, on_new_message):
        custom_webhook = Blueprint('custom_webhook', __name__)

        @custom_webhook.route("/", methods=['GET'])
        async def health(request):
            return response.json({"status": "ok"})

        @custom_webhook.route("/webhook", methods=['GET', 'POST'])
        async def webhook(request):
          
            output = request.json
            logger.info("webhook request : {0}".format(json.dumps(output)))
            if output:
                messages_list = output.get("messages", None)
                logger.info("messages_list: {0}".format(messages_list))
                if messages_list:
                    message = messages_list[0].get("message", None)
                    logger.info("text: {0}".format(message))
                    sender_name = messages_list[0].get("username", None)
                    logger.info("sender_name: {0}".format(sender_name))
                else:
                    message = output.get("message", None)
                    logger.info("text: {0}".format(message))
                    sender_name = output.get("username", None)
                    logger.info("sender_name: {0}".format(sender_name))
                recipient_id = output.get("_id", None)
                room_id = output.get("roomId", None)

                logger.info("message: {0}".format(message))
                logger.info("recipient_id: {0}".format(recipient_id))
                logger.info("room_id: {0}".format(room_id))

                await self.send_message(message, sender_name, room_id, on_new_message)

            return response.text("")

        return custom_webhook