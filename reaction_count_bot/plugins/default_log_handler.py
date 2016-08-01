import pprint

from slack_bot.bot_plugin import BotPlugin
from slack_bot.slack_messages import parse_slack_message


class DefaultLogHandler(BotPlugin):
    def __init__(self, bot):
        super().__init__(bot)

        self.add_rtm_handler(self.on_reconnect, "reconnect_url")
        self.add_rtm_handler(self.on_presence_change, "presence_change")
        self.add_rtm_handler(self.on_user_typing, "user_typing")
        self.add_rtm_handler(self.on_message, "message")
        self.add_rtm_handler(self.on_reaction_added, "reaction_added")
        self.add_rtm_handler(self.on_reaction_removed, "reaction_removed")

    def on_reconnect(self, event):
        self.bot.log.debug("on_reconnect: {}".format(pprint.pformat(event)))

    def on_presence_change(self, event):
        self.bot.log.debug("on_presence_change: {}".format(pprint.pformat(event)))
        user_name = self.bot.slack_client.get_user_name(event["user"])
        self.bot.log.info("User {} ({}) is now {}".format(user_name, event["user"], event["presence"]))

    def on_user_typing(self, event):
        self.bot.log.debug("on_user_typing: {}".format(pprint.pformat(event)))
        user_name = self.bot.slack_client.get_user_name(event["user"])
        channel_name = self.bot.slack_client.get_channel_name(event["channel"])
        self.bot.log.debug(
            "User {} ({}) is typing in {} ({})...".format(user_name, event["user"], channel_name, event["channel"]))

    def on_message(self, event):
        self.bot.log.debug("on_message: {}".format(pprint.pformat(event)))

        message_object = parse_slack_message(event)

        if not message_object.has_text:
            return
        sender = message_object.sender_id
        if sender == self.bot.bot_id:
            return
        user_name = self.bot.slack_client.get_user_name(sender)
        channel_name = self.bot.slack_client.get_channel_name(message_object.channel)
        text = message_object.text
        self.bot.log.info("({}) {}: {}".format(channel_name, user_name, text))

    def on_reaction_added(self, event):
        self.bot.log.debug("on_reaction_added: {}".format(pprint.pformat(event)))

    def on_reaction_removed(self, event):
        self.bot.log.debug("on_reaction_removed: {}".format(pprint.pformat(event)))
