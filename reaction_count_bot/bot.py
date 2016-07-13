import re
import time
from my_slack_client import MySlackClient
import logging
import logging.handlers
import signal
import sys
from collections import defaultdict

BOT_NAME = 'paulbot'


class Bot():

    def __init__(self, apikey):
        self.log = logging.getLogger("paulbot")

        self.slack_client = MySlackClient(apikey)
        self.should_continue_running = True

        self.bot_name = None
        self.bot_id = None
        self.team_name = None
        self.team_id = None
        self.url = None

        self.startup_handlers = []
        self.rtm_event_handlers = defaultdict(list)
        self.exit_handlers = []

    def register_plugin(self, plugin):
        for handler in plugin.get_startup_handlers():
            self.startup_handlers.append(handler)
        for handler in plugin.get_rtm_handlers():
            self.rtm_event_handlers[handler[0]].append(handler[1])
        for handler in plugin.get_exit_handlers():
            self.exit_handlers.append(handler)

    def exit_handler(self, signal, frame):
        self.log.warning("\nExiting...")
        for handler in self.exit_handlers:
            handler()
        sys.exit(0)

    def run(self):
        signal.signal(signal.SIGINT, self.exit_handler)

        self.slack_client.connect()
        self.test_auth()
        self.slack_client.update_all_data()

        for handler in self.startup_handlers:
            handler()

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

        if self.rtm_event_handlers[event_type]:
            for handler in self.rtm_event_handlers[event_type]:
                handler(event)
        else:
            self.log.warning("{}".format(str(event)))

    def say_in_channel(self, message, channel):
        self.slack_client.api_call("chat.postMessage", text=message, channel=channel, as_user=True)

    def dm(self, message, user):
        channel = self.slack_client.get_dm_for_user(user)
        self.say_in_channel(message, channel)


class BotPlugin(object):

    def get_rtm_handlers(self):
        return []

    def get_startup_handlers(self):
        return []

    def get_exit_handlers(self):
        return []
