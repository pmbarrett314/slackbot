import logging
import os
from reaction_count.reaction_count_bot import ReactionCountBot
from slack_bot.default_log_handler import DefaultLogHandler
from slack_bot.slack_bot import Bot
import coloredlogs

def get_api_key():
    with open(os.path.join("..", "private", ".apikey"), "r") as keyfile:
        return keyfile.read().strip()

def set_up_logging():
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    color_formatter = coloredlogs.ColoredFormatter(fmt="%(asctime)s %(name)s %(levelname)s %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(color_formatter)
    console_handler.setLevel(logging.INFO)

    log_folder = (os.path.join("..", "log"))

    file_handler = logging.handlers.RotatingFileHandler(os.path.join(log_folder, "log.txt"), maxBytes=(1024**2) / 2, backupCount=1)
    file_handler.setLevel(logging.INFO)

    warning_file_handler = logging.handlers.RotatingFileHandler(os.path.join(log_folder, "errors.txt"), maxBytes=(1024**2) / 2, backupCount=1)
    warning_file_handler.setLevel(logging.WARNING)

    debug_file_handler = logging.handlers.RotatingFileHandler(os.path.join(log_folder, "debug.txt"), maxBytes=(1024**2) / 2, backupCount=1)
    debug_file_handler.setLevel(logging.DEBUG)

    logging.basicConfig(level=logging.DEBUG, handlers=[console_handler, file_handler, warning_file_handler, debug_file_handler])

if __name__ == "__main__":
    set_up_logging()
    bot = Bot(get_api_key())
    plugin = ReactionCountBot(bot, reset_data=False)
    plugin2 = DefaultLogHandler(bot)
    bot.register_plugin(plugin)
    bot.register_plugin(plugin2)

    bot.run()
