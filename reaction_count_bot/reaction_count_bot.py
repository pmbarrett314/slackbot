from message_handler import MessageHandler
import logging
from emoji_counter import EmojiCounter

class ReactionCountBot(MessageHandler):
    def __init__(self, bot, reset_data=False):
        super().__init__(bot)
        self.bot = bot
        self.bot_id = bot.bot_id
        self.log = logging.getLogger("ReactionCountBot")
        self.emoji_counter = EmojiCounter(self.bot.slack_client)
        self.reset_data = reset_data

    def get_rtm_handlers(self):
        event_handlers = super().get_rtm_handlers()
        event_handlers.append(("reaction_added", self.on_reaction_added))
        event_handlers.append(("reaction_removed", self.on_reaction_removed))
        return event_handlers

    def get_startup_handlers(self):
        startup_handlers = []
        startup_handlers.append(self.prep_data)
        return startup_handlers

    def get_exit_handlers(self):
        exit_handlers = []
        exit_handlers.append(self.dump_data)
        return exit_handlers

    def prep_data(self):
        self.emoji_counter.prep(reset_data=self.reset_data)

    def dump_data(self):
        self.emoji_counter.dump_data()

    def get_message_handlers(self):
        message_handlers = super().get_message_handlers()
        message_handlers["\<@({})\>:? score \<@(.*)\>".format(self.bot_id)].append(self.handle_score_request)
        message_handlers["\<@({})\>:? score me".format(self.bot_id)].append(self.handle_score_me)
        message_handlers["\<@({})\>:? upvote :(.*):".format(self.bot_id)].append(self.handle_upvote)
        message_handlers["\<@({})\>:? downvote :(.*):".format(self.bot_id)].append(self.handle_downvote)
        message_handlers["\<@({})\>:? log_votes".format(self.bot_id)].append(self.handle_log_votes)
        message_handlers["\(╯°□°\）╯︵ ┻(━*)┻"].append(self.handle_table_flip)
        message_handlers["\<@({})\>:? say \"(.*)\" in \<#(.*)\>".format(self.bot_id)].append(self.handle_say)

        return message_handlers

    def handle_score_request(self, match_object, message_object):
        user = match_object.group(2)
        user_name = self.bot.slack_client.get_user_name(user)
        score = self.emoji_counter.score(user)
        self.log.info("Score for: {}: {}".format(user_name, score))
        message = "Score for <@{}> is {}".format(user, score)
        channel = message_object.channel
        self.bot.say_in_channel(message, channel)

    def handle_score_me(self, match_object, message_object):
        user = message_object.sender_id
        user_name = self.bot.slack_client.get_user_name(user)
        score = self.emoji_counter.score(user)
        self.log.info("Score for: {}: {}".format(user_name, score))
        message = "Score for <@{}> is {}".format(user, score)
        channel = message_object.channel
        self.bot.say_in_channel(message, channel)

    def handle_upvote(self, match_object, message_object):
        user = message_object.sender_id
        reaction = match_object.group(2)
        self.log.info("Upvote: {} {}".format(self.bot.slack_client.get_user_name(user), reaction))
        self.emoji_counter.upvote(user, reaction)

    def handle_downvote(self, match_object, message_object):
        user = message_object.sender_id
        reaction = match_object.group(2)
        self.log.info("Downvote: {} {}".format(self.bot.slack_client.get_user_name(user), reaction))
        self.emoji_counter.downvote(user, reaction)

    def handle_say(self, match_object, message_object):
        message = match_object.group(2)
        channel = match_object.group(3)
        self.bot.say_in_channel(message, channel)

    def handle_table_flip(self, match_object, message_object):
        message = "┬{}┬ノ(ಠ_ಠノ)".format("─" * len(match_object.group(1)))
        channel = message_object.channel
        self.bot.say_in_channel(message, channel)

    def handle_log_votes(self, match_object, message_object):
        self.emoji_counter.log_votes()

    def on_reaction_added(self, event):
        self.log.info(event)

        if "item_user" in event:
            item_user = event["item_user"]
        else:
            return
        reaction = event["reaction"]
        ts = event["event_ts"]
        self.emoji_counter.add_score(item_user, reaction, ts)

    def on_reaction_removed(self, event):
        self.log.info(event)

        if "item_user" in event:
            item_user = event["item_user"]
        else:
            return
        reaction = event["reaction"]
        ts = event["event_ts"]
        self.emoji_counter.remove_score(item_user, reaction, ts)