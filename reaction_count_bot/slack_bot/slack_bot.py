import time
from slack_bot.my_slack_client import MySlackClient
import logging
import logging.handlers
import pprint
import signal
import sys
from collections import defaultdict

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

        rtm_handlers = plugin.get_rtm_handlers()
        for message_type in rtm_handlers:
            self.rtm_event_handlers[message_type].extend(rtm_handlers[message_type])
        for handler in plugin.get_exit_handlers():
            self.exit_handlers.append(handler)

    def exit_handler(self, signal, frame):
        self.log.warning("\nExiting...")
        for handler in self.exit_handlers:
            handler()
        sys.exit(0)

    def set_up_exit(self):
        signal.signal(signal.SIGINT, self.exit_handler)

    def run(self):
        self.set_up_exit()

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
            self.log.warning("{}".format(pprint.pformat(event)))

    def say_in_channel(self, message, channel, log=True):
        if log:
            channel_name = self.slack_client.get_channel_name(channel)
            self.log.info('Said "{}" in {} ({})'.format(message, channel_name, channel))
        self.slack_client.api_call("chat.postMessage", text=message, channel=channel, as_user=True)

    def dm(self, message, user, log=True):
        channel = self.slack_client.get_dm_for_user(user)
        
        if log:
            user_name = self.slack_client.get_user_name(user)

            self.log.info('DMed {} to {} ({}), channel: {}'.format(message, user_name, user, channel))
        
        self.say_in_channel(message, channel, log=False)

    def add_reaction_to_message(self, reaction, channel, timestamp):
        return self.slack_client.api_call("reactions.add", name= reaction, channel=channel, timestamp=timestamp)
