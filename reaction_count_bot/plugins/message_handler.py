import logging
import re
from collections import defaultdict

from slack_bot.bot_plugin import BotPlugin
from slack_bot.slack_messages import parse_slack_message


class MessageHandler(BotPlugin):
    def __init__(self, bot):
        super().__init__()
        self.log = logging.getLogger("MessageHandler")
        self.bot = bot

    def get_rtm_handlers(self):
        event_handlers = super().get_rtm_handlers()
        event_handlers["message"].append(self.handle_message)
        return event_handlers

    def get_message_handlers(self):
        return defaultdict(list)

    def handle_message(self, event):
        message_object = parse_slack_message(event)
        if message_object is not None and message_object.has_text:
            for pattern in self.get_message_handlers():
                match_object = re.search(pattern, message_object.text)
                if match_object is not None:
                    for handler in self.get_message_handlers()[pattern]:
                        handler(match_object, message_object)
