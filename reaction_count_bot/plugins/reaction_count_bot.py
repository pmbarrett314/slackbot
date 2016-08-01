import logging

from plugins.message_handler import MessageHandler
from plugins.reaction_counter import EmojiCounter


class ReactionCountBot(MessageHandler):
    def __init__(self, bot, reset_data=False):
        super().__init__(bot)
        self.bot = bot
        self.log = logging.getLogger("ReactionCountBot")
        self.emoji_counter = EmojiCounter(self.bot.slack_client)
        self.reset_data = reset_data

        self.add_rtm_handler(self.on_reaction_added, "reaction_added")
        self.add_rtm_handler(self.on_reaction_removed, "reaction_removed")

        self.add_startup_handler(self.prep_data)

        self.add_exit_handler(self.dump_data)

        self.add_message_hanlder(self.handle_score_request, "score \<@(?P<user_id>.*)\>", address=True)
        self.add_message_hanlder(self.handle_score_me, "score me", address=True)
        self.add_message_hanlder(self.handle_score_all, "score all", address=True)
        self.add_message_hanlder(self.handle_upvote, "upvote :(?P<reaction>.*):", address=True)
        self.add_message_hanlder(self.handle_downvote, "downvote :(?P<reaction>.*):", address=True)
        self.add_message_hanlder(self.handle_log_votes, "log_votes", address=True)
        self.add_message_hanlder(self.handle_list_votes, "list votes", address=True)
        self.add_message_hanlder(self.handle_list_votes_detail, "list detailed votes", address=True)
        self.add_message_hanlder(self.handle_table_flip, "\(╯°□°\）╯︵ ┻(━*)┻")
        self.add_message_hanlder(self.handle_say, "say \"(?P<message>.*)\" in \<#(?P<channel>.*)\>", address=True)
        self.add_message_hanlder(self.handle_dm, "dm \"(?P<message>.*)\" to \<@(?P<user_id>.*)\>", address=True)
        self.add_message_hanlder(self.handle_tally, "tally :(?P<reaction>.*):", address=True)
        self.add_message_hanlder(self.help, "help", address=True)


    def prep_data(self):
        self.emoji_counter.prep(reset_data=self.reset_data)

    def dump_data(self):
        self.emoji_counter.dump_data()


    def help(self, match_object, message_object):
        sender = message_object.sender_id
        commands = ["score (me, all, @<user_name>)", "(up, down)vote :<reaction>:", "list [detailed] votes",
                    "tally :<reaction>:", "roll <number>d<number>"]
        message = "I can speak in #bot and DM, so don't spam main with me.\nCommands ('()': choose one, '[]': optional, <>: replace with what's described):\n"
        for command in commands:
            message += ("\t{}\n".format(command))

        self.bot.dm(message, sender)

    def handle_tally(self, match_object, message_object):
        reaction = match_object.group("reaction")
        ups = len(self.emoji_counter.upvotes[reaction])
        downs = len(self.emoji_counter.downvotes[reaction])
        message = ":{}: Up: {} Down: {} Total: {}".format(reaction, ups, downs, ups - downs)
        channel = message_object.channel

        self.bot.say_in_channel(message, channel)

    def handle_list_votes(self, match_object, message_object):
        message = ""
        message += "Up:\n"
        for u in self.emoji_counter.upvotes.items():
            if len(u[1]) > 0:
                message += "\t:{}:: {}\n".format(u[0], len(u[1]))
        message += "Down:\n"
        for d in self.emoji_counter.downvotes.items():
            if len(d[1]) > 0:
                message += "\t:{}:: {}\n".format(d[0], len(d[1]))
        self.bot.dm(message, message_object.sender_id)

    def handle_list_votes_detail(self, match_object, message_object):
        message = ""
        message += "Up:\n"
        for vote in self.emoji_counter.upvotes.items():
            if len(vote[1]) > 0:
                message += "\t:{}:: (".format(vote[0], len(vote[1]))
                for user in vote[1]:
                    message += "<@{}> ".format(user)
                message += ")\n"
        message += "Down:\n"
        for vote in self.emoji_counter.downvotes.items():
            if len(vote[1]) > 0:
                message += "\t:{}:: (".format(vote[0], len(vote[1]))
                for user in vote[1]:
                    message += "<@{}> ".format(user)
                message += ")\n"
        self.bot.dm(message, message_object.sender_id)

    def handle_score_request(self, match_object, message_object):
        user = match_object.group("user_id")
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

    def handle_score_all(self, match_object, message_object):
        scores = []
        for user in self.bot.slack_client.get_users():
            score = self.emoji_counter.score(user)
            scores.append((user, score))
        scores.sort(key=lambda x: x[1])
        message = "Scores:\n"
        for score in scores:
            message += "\t{}: {}\n".format(self.bot.slack_client.get_user_name(score[0]), score[1])
        user = message_object.sender_id
        self.bot.dm(message, user)

    def handle_upvote(self, match_object, message_object):
        user = message_object.sender_id
        reaction = match_object.group("reaction")
        self.log.info("Upvote: {} {}".format(self.bot.slack_client.get_user_name(user), reaction))
        self.emoji_counter.upvote(user, reaction)

    def handle_downvote(self, match_object, message_object):
        user = message_object.sender_id
        reaction = match_object.group("reaction")
        self.log.info("Downvote: {} {}".format(self.bot.slack_client.get_user_name(user), reaction))
        self.emoji_counter.downvote(user, reaction)

    def handle_say(self, match_object, message_object):
        message = match_object.group("message")
        channel = match_object.group("channel")
        self.bot.say_in_channel(message, channel)

    def handle_dm(self, match_object, message_object):
        message = match_object.group("message")
        user = match_object.group("user_id")
        self.bot.dm(message, user)

    def handle_table_flip(self, match_object, message_object):
        message = "┬{}┬ノ(ಠ_ಠノ)".format("─" * len(match_object.group(1)))
        channel = message_object.channel
        self.bot.say_in_channel(message, channel)

    def handle_log_votes(self, match_object, message_object):
        self.emoji_counter.log_votes()

    def on_reaction_added(self, event):
        if "item_user" in event:
            item_user = event["item_user"]
        else:
            return

        user = event["user"]
        reaction = event["reaction"]
        ts = event["event_ts"]
        item_ts = event["item"]["ts"]

        self.log.info("{} reacted to {}'s post at at {} with {}".format(self.bot.slack_client.get_user_name(user),
                                                                        self.bot.slack_client.get_user_name(item_user),
                                                                        item_ts, reaction))
        self.emoji_counter.add_score(item_user, reaction, ts)

    def on_reaction_removed(self, event):
        if "item_user" in event:
            item_user = event["item_user"]
        else:
            return

        user = event["user"]
        reaction = event["reaction"]
        ts = event["event_ts"]
        item_ts = event["item"]["ts"]

        self.log.info("{} reacted to {}'s post at at {} with {}".format(user, item_user, item_ts, reaction))
        self.emoji_counter.remove_score(item_user, reaction, ts)
