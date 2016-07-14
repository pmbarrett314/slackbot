from collections import defaultdict

class BotPlugin(object):

    def get_rtm_handlers(self):
        return defaultdict(list)

    def get_startup_handlers(self):
        return []

    def get_exit_handlers(self):
        return []