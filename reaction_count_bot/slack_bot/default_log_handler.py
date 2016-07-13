from slack_bot.bot_plugin import BotPlugin


class DefaultLogHandler(BotPlugin):

    def __init__(self, bot):
        self.bot = bot

    def get_rtm_handlers(self):
        event_handlers = super().get_rtm_handlers()
        event_handlers.append(("reconnect_url", self.on_reconnect))
        event_handlers.append(("presence_change", self.on_presence_change))
        event_handlers.append(("user_typing", self.on_user_typing))
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
