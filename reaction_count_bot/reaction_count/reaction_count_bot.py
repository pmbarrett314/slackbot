from slack_bot.message_handler import MessageHandler
import logging
from reaction_count.reaction_counter import EmojiCounter


class ReactionCountBot(MessageHandler):

    def __init__(self, bot, reset_data=False):
        super().__init__(bot)
        self.bot = bot
        self.log = logging.getLogger("ReactionCountBot")
        self.emoji_counter = EmojiCounter(self.bot.slack_client)
        self.reset_data = reset_data

    def get_rtm_handlers(self):
        event_handlers = super().get_rtm_handlers()
        event_handlers["reaction_added"].append(self.on_reaction_added)
        event_handlers["reaction_removed"].append(self.on_reaction_removed)
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
        message_handlers["\<@({})\>:? score \<@(.*)\>".format(self.bot.bot_id)].append(self.handle_score_request)
        message_handlers["\<@({})\>:? score me".format(self.bot.bot_id)].append(self.handle_score_me)
        message_handlers["\<@({})\>:? score all".format(self.bot.bot_id)].append(self.handle_score_all)
        message_handlers["\<@({})\>:? upvote :(.*):".format(self.bot.bot_id)].append(self.handle_upvote)
        message_handlers["\<@({})\>:? downvote :(.*):".format(self.bot.bot_id)].append(self.handle_downvote)
        message_handlers["\<@({})\>:? log_votes".format(self.bot.bot_id)].append(self.handle_log_votes)
        message_handlers["\<@({})\>:? list votes".format(self.bot.bot_id)].append(self.handle_list_votes)
        message_handlers["\<@({})\>:? list detailed votes".format(self.bot.bot_id)].append(self.handle_list_votes_detail)
        message_handlers["\(╯°□°\）╯︵ ┻(━*)┻"].append(self.handle_table_flip)
        message_handlers["\<@({})\>:? say \"(.*)\" in \<#(.*)\>".format(self.bot.bot_id)].append(self.handle_say)
        message_handlers["\<@({})\>:? dm \"(.*)\" to \<@(.*)\>".format(self.bot.bot_id)].append(self.handle_dm)
        message_handlers["\<@({})\>:? tally :(.*):".format(self.bot.bot_id)].append(self.handle_tally)

        return message_handlers

    def handle_tally(self, match_object, message_object):
        reaction = match_object.group(2)
        ups = len(self.emoji_counter.upvotes[reaction])
        downs = len(self.emoji_counter.downvotes[reaction])
        message = ":{}: Up: {} Down: {} Total: {}".format(reaction, ups, downs, ups-downs)
        channel = message_object.channel

        self.bot.say_in_channel(message, channel)

    def handle_list_votes(self, match_object, message_object):
        message = ""
        message+="Up:\n"
        for u in self.emoji_counter.upvotes.items():
            if len(u[1]) > 0:
                message += "\t:{}:: {}\n".format(u[0], len(u[1]))
        message+="Down:\n"
        for d in self.emoji_counter.downvotes.items():
            if len(d[1]) > 0:
                message += "\t:{}:: {}\n".format(d[0], len(d[1]))
        self.bot.dm(message, message_object.sender_id)

    def handle_list_votes_detail(self, match_object, message_object):
        message = ""
        message+="Up:\n"
        for vote in self.emoji_counter.upvotes.items():
            if len(vote[1]) > 0:
                message += "\t:{}:: (".format(vote[0], len(vote[1]))
                for user in vote[1]:
                    message += "<@{}> ".format(user)
                message += ")\n"
        message+="Down:\n"
        for vote in self.emoji_counter.downvotes.items():
            if len(vote[1]) > 0:
                message += "\t:{}:: (".format(vote[0], len(vote[1]))
                for user in vote[1]:
                    message += "<@{}> ".format(user)
                message += ")\n"
        self.bot.dm(message, message_object.sender_id)


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

    def handle_dm(self, match_object, message_object):
        message = match_object.group(2)
        user = match_object.group(3)
        self.bot.dm(message, user)

    def handle_table_flip(self, match_object, message_object):
        message = "┬{}┬ノ(ಠ_ಠノ)".format("─" * len(match_object.group(1)))
        channel = message_object.channel
        self.bot.say_in_channel(message, channel)

    def handle_log_votes(self, match_object, message_object):
        self.emoji_counter.log_votes()

    def on_reaction_added(self, event):
        self.log.debug(event)

        if "item_user" in event:
            item_user = event["item_user"]
        else:
            return

        user = event["user"]
        reaction = event["reaction"]
        ts = event["event_ts"]
        item_ts = event["item"]["ts"]

        self.log.info("{} reacted to {}'s post at at {} with {}".format(self.bot.slack_client.get_user_name(user), self.bot.slack_client.get_user_name(item_user), item_ts, reaction))
        self.emoji_counter.add_score(item_user, reaction, ts)

    def on_reaction_removed(self, event):
        self.log.debug(event)

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
