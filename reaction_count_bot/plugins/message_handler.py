import logging
import re
from collections import defaultdict

from slack_bot.bot_plugin import BotPlugin
from slack_bot.slack_messages import parse_slack_message


class MessageHandler(BotPlugin):
    def __init__(self, bot):
        super().__init__(bot)
        self.message_handlers = defaultdict(set)
        self.add_rtm_handler(self.handle_message, "message")

    def add_message_hanlder(self, handler_method, message_regex):
        self.message_handlers[message_regex].add(handler_method)

    def get_message_handlers(self):
        return self.message_handlers

    def handle_message(self, event):
        message_object = parse_slack_message(event)
        if message_object is not None and message_object.has_text:
            print(self.get_message_handlers())
            for pattern in self.get_message_handlers():
                match_object = re.search(pattern, message_object.text)
                if match_object is not None:
                    for handler in self.get_message_handlers()[pattern]:
                        handler(match_object, message_object)
