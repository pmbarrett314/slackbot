from plugins.message_handler import MessageHandler

class Commands(MessageHandler):

    def __init__(self, bot):
        super().__init__(bot)

        self.add_message_hanlder(self.handle_say, "say \"(?P<message>.*)\" in \<#(?P<channel>.*)\>", address=True)
        self.add_message_hanlder(self.handle_dm, "dm \"(?P<message>.*)\" to \<@(?P<user_id>.*)\>", address=True)
        self.add_message_hanlder(self.handle_set_topic, "set the topic in \<#(?P<channel>.*)\> to \"(?P<topic>.*)\"", address=True)

    def handle_set_topic(self, match_object, message_object):
        channel = match_object.group("channel")
        topic = match_object.group("topic")
        self.bot.set_topic(channel, topic)

    def handle_say(self, match_object, message_object):
        message = match_object.group("message")
        channel = match_object.group("channel")
        self.bot.say_in_channel(message, channel)

    def handle_dm(self, match_object, message_object):
        message = match_object.group("message")
        user = match_object.group("user_id")
        self.bot.dm(message, user)
