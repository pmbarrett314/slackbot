from bot import BotPlugin
from slack_messages import parse_slack_message
from collections import defaultdict


import re
import logging

class MessageHandler(BotPlugin):
    def __init__(self, bot):
        super().__init__()
        self.log = logging.getLogger("MessageHandler")
        self.bot = bot


    def get_rtm_handlers(self):
        event_handlers = []
        event_handlers.append(("message", self.handle_message))
        return event_handlers

    def get_message_handlers(self):
        return defaultdict(list)

    def handle_message(self, msg):
        self.log.debug("on_message: {}".format(msg))
        message_object = parse_slack_message(msg)
        if message_object is not None and message_object.has_text:
            for pattern in self.get_message_handlers():
                match_object = re.search(pattern, message_object.text)
                if match_object is not None:
                    for handler in self.get_message_handlers()[pattern]:
                        handler(match_object, message_object)
            user_name = self.bot.slack_client.get_user_name(message_object.sender_id)
            channel_name = self.bot.slack_client.get_channel_name(message_object.channel)
            text = message_object.text
            self.log.info("({}) {}: {}".format(channel_name, user_name, text))