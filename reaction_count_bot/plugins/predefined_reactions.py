from plugins.message_handler import MessageHandler


class PredefinedReactions(MessageHandler):

    def __init__(self, bot):
        super().__init__(bot)
        self.giphy_reactions = dict()

    def get_message_handlers(self):
        message_handlers = super().get_message_handlers()
        message_handlers["/giphy.*".format(self.bot.bot_id)].append(self.handle_giphy)
        return message_handlers

    def handle_giphy(self, match_object, message_object):
        channel = message_object.channel
        sender = message_object.sender_id
        timestamp = message_object.timestamp
        print(self.giphy_reactions)
        if sender in self.giphy_reactions:
            self.bot.add_reaction_to_message(self.giphy_reactions[sender], channel, timestamp)
