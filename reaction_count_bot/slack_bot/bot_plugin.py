from collections import defaultdict


class BotPlugin(object):
    def __init__(self):
        self.startup_handlers = set()
        self.rtm_handlers = defaultdict(set)
        self.exit_handlers = set()

    def add_startup_handler(self, method):
        self.startup_handlers.add(method)

    def add_exit_handler(self, method):
        self.exit_handlers.add(method)

    def add_rtm_handler(self, method, event):
        self.rtm_handlers[event] = method

    def get_rtm_handlers(self):
        return self.rtm_handlers

    def get_startup_handlers(self):
        return self.startup_handlers

    def get_exit_handlers(self):
        return self.exit_handlers
