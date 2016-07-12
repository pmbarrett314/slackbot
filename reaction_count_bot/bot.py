import re
import time
from my_slack_client import MySlackClient
from slack_messages import parse_slack_message
from emoji_counter import EmojiCounter
import logging
import logging.handlers
import signal
import sys
from collections import defaultdict

BOT_NAME = 'paulbot'


class EmojiCountBot():

    def __init__(self, apikey):
        self.log = logging.getLogger("paulbot")

        self.slack_client = MySlackClient(apikey)
        self.should_continue_running = True

        self.bot_name = None
        self.bot_id = None
        self.team_name = None
        self.team_id = None
        self.url = None

        self.message_handlers = defaultdict(list)

        self.emoji_counter = EmojiCounter(self.slack_client)

    def exit_handler(self, signal, frame):
        self.log.info("\nExiting...")
        self.emoji_counter.dump_data()
        sys.exit(0)

    def run(self, reset_data=False):
        signal.signal(signal.SIGINT, self.exit_handler)

        self.slack_client.connect()
        self.test_auth()
        self.slack_client.update_all_data()
        self.emoji_counter.prep(reset_data=reset_data)
        self.register_handlers()
        self.main_loop()

    def main_loop(self):
        while self.should_continue_running:
            for event in self.slack_client.rtm_read():
                try:
                    self.process(event)
                except Exception:
                    self.log.exception("Recieved exception:")
            time.sleep(0.1)

    def test_auth(self):
        resp = self.slack_client.api_call("auth.test")
        self.log.debug(("auth.test response: {}".format(str(resp))))

        if "ok" not in resp:
            raise Exception("auth.test returned invalid message: {}".format(resp))
        elif resp['ok']:
            self.bot_name = resp["user"]
            self.bot_id = resp["user_id"]
            self.team_name = resp["team"]
            self.team_id = resp["team_id"]
            self.url = resp["url"]
            self.log.info("Bot ID for '{}' is {}\n".format(self.bot_name, self.bot_id))
        else:
            raise Exception("auth.test returned error: {}".format(resp))

    def process(self, event):
        self.log.debug("process: {}".format(event))
        event_type = event["type"]
        if event_type == "presence_change":
            self.on_presence_change(event)
        elif event_type == "user_typing":
            self.on_user_typing(event)
        elif event_type == "reconnect_url":
            self.on_reconnect(event)
        elif event_type == "message":
            self.on_message(event)
        elif event_type == "reaction_added":
            self.on_reaction_added(event)
        elif event_type == "reaction_removed":
            self.on_reaction_removed(event)
        else:
            self.log.warning("{}".format(str(event)))

    def on_message(self, msg):
        self.log.debug("on_message: {}".format(msg))
        message_object = parse_slack_message(msg)
        if message_object is not None and message_object.has_text:
            for pattern in self.message_handlers:
                match_object = re.search(pattern, message_object.text)
                if match_object is not None:
                    for handler in self.message_handlers[pattern]:
                        handler(match_object, message_object)
            user_name = self.slack_client.get_user_name(message_object.sender_id)
            channel_name = self.slack_client.get_channel_name(message_object.channel)
            text = message_object.text
            self.log.info("({}) {}: {}".format(channel_name, user_name, text))

    def register_handler(self, regex_pattern, handler_function):
        self.message_handlers[regex_pattern].append(handler_function)

    def register_handlers(self):
        self.register_handler("\(╯°□°\）╯︵ ┻(━*)┻", self.handle_table_flip)
        self.register_handler("\<@({})\>:? score \<@(.*)\>".format(self.bot_id), self.handle_score_request)
        self.register_handler("\<@({})\>:? score me".format(self.bot_id), self.handle_score_me)
        self.register_handler("\<@({})\>:? upvote :(.*):".format(self.bot_id), self.handle_upvote)
        self.register_handler("\<@({})\>:? downvote :(.*):".format(self.bot_id), self.handle_downvote)
        self.register_handler("\<@({})\>:? say \"(.*)\" in \<#(.*)\>".format(self.bot_id), self.handle_say)
        self.register_handler("\<@({})\>:? log_votes".format(self.bot_id), self.handle_log_votes)

    def handle_log_votes(self, match_object, message_object):
        self.emoji_counter.log_votes()

    def say_in_channel(self, message, channel):
        self.slack_client.api_call("chat.postMessage", text=message, channel=channel, as_user=True)

    def handle_say(self, match_object, message_object):
        message = match_object.group(2)
        channel = match_object.group(3)
        self.say_in_channel(message, channel)

    def handle_table_flip(self, match_object, message_object):
        message = "┬{}┬ノ(ಠ_ಠノ)".format("─" * len(match_object.group(1)))
        channel = message_object.channel
        self.say_in_channel(message, channel)

    def handle_score_request(self, match_object, message_object):
        user = match_object.group(2)
        user_name = self.slack_client.get_user_name(user)
        score = self.emoji_counter.score(user)
        self.log.info("Score for: {}: {}".format(user_name, score))
        message = "Score for <@{}> is {}".format(user, score)
        channel = message_object.channel
        self.say_in_channel(message, channel)

    def handle_score_me(self, match_object, message_object):
        user = message_object.sender_id
        user_name = self.slack_client.get_user_name(user)
        score = self.emoji_counter.score(user)
        self.log.info("Score for: {}: {}".format(user_name, score))
        message = "Score for <@{}> is {}".format(user, score)
        channel = message_object.channel
        self.say_in_channel(message, channel)

    def handle_upvote(self, match_object, message_object):
        user = message_object.sender_id
        reaction = match_object.group(2)
        self.log.info("Upvote: {} {}".format(self.slack_client.get_user_name(user), reaction))
        self.emoji_counter.upvote(user, reaction)

    def handle_downvote(self, match_object, message_object):
        user = message_object.sender_id
        reaction = match_object.group(2)
        self.log.info("Downvote: {} {}".format(self.slack_client.get_user_name(user), reaction))
        self.emoji_counter.downvote(user, reaction)

    def on_mention(self, msg):
        self.log.info("Mention: {}".format(str(msg)))

    def on_address(self, msg):
        self.log.info("Address: {}".format(str(msg)))

    def on_reconnect(self, event):
        self.log.debug("on_reconnect: {}".format(event))

    def on_presence_change(self, event):
        self.log.debug("on_presence_change: {}".format(event))
        user_name = self.slack_client.get_user_name(event["user"])
        self.log.info("User {} ({}) is now {}".format(user_name, event["user"], event["presence"]))

    def on_user_typing(self, event):
        self.log.debug("on_user_typing: {}".format(event))
        user_name = self.slack_client.get_user_name(event["user"])
        channel_name = self.slack_client.get_channel_name(event["channel"])
        self.log.debug("User {} ({}) is typing in {} ({})...".format(user_name, event["user"], channel_name, event["channel"]))

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
