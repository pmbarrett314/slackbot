from plugins.message_handler import MessageHandler


class PredefinedReactions(MessageHandler):
    def __init__(self, bot):
        super().__init__(bot)

        self.giphy_reactions = dict()

        self.add_message_hanlder(self.handle_giphy, "/giphy.*")

    def handle_giphy(self, match_object, message_object):
        channel = message_object.channel
        sender = message_object.sender_id
        timestamp = message_object.timestamp
        if sender in self.giphy_reactions:
            self.bot.add_reaction_to_message(self.giphy_reactions[sender], channel, timestamp)
