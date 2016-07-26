from slack_bot.bot_plugin import BotPlugin
from slack_bot.slack_messages import parse_slack_message


class DefaultLogHandler(BotPlugin):

    def __init__(self, bot):
        self.bot = bot

    def get_rtm_handlers(self):
        event_handlers = super().get_rtm_handlers()
        event_handlers["reconnect_url"].append(self.on_reconnect)
        event_handlers["presence_change"].append(self.on_presence_change)
        event_handlers["user_typing"].append(self.on_user_typing)
        event_handlers["message"].append(self.on_message)
        event_handlers["reaction_added"].append(self.on_reaction_added)
        event_handlers["reaction_removed"].append(self.on_reaction_removed)
        return event_handlers

    def on_reconnect(self, event):
        self.bot.log.debug("on_reconnect: {}".format(event))

    def on_presence_change(self, event):
        self.bot.log.debug("on_presence_change: {}".format(event))
        user_name = self.bot.slack_client.get_user_name(event["user"])
        self.bot.log.info("User {} ({}) is now {}".format(user_name, event["user"], event["presence"]))

    def on_user_typing(self, event):
        self.bot.log.debug("on_user_typing: {}".format(event))
        user_name = self.bot.slack_client.get_user_name(event["user"])
        channel_name = self.bot.slack_client.get_channel_name(event["channel"])
        self.bot.log.debug("User {} ({}) is typing in {} ({})...".format(user_name, event["user"], channel_name, event["channel"]))

    def on_message(self, event):
        self.bot.log.debug("on_message: {}".format(event))

        message_object = parse_slack_message(event)

        user_name = self.bot.slack_client.get_user_name(message_object.sender_id)
        channel_name = self.bot.slack_client.get_channel_name(message_object.channel)
        text = message_object.text
        self.bot.log.info("({}) {}: {}".format(channel_name, user_name, text))

    def on_reaction_added(self, event):
        self.bot.log.debug("on_reaction_added: {}".format(event))

    def on_reaction_removed(self, event):
        self.bot.log.debug("on_reaction_removed: {}".format(event))
