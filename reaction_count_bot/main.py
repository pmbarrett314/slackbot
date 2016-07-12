import logging
import os
from bot import EmojiCountBot
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

    file_handler = logging.handlers.RotatingFileHandler(os.path.join(log_folder, "log.txt"), maxBytes=(1024**2)/2)
    file_handler.setLevel(logging.INFO)

    warning_file_handler = logging.handlers.RotatingFileHandler(os.path.join(log_folder, "errors.txt"), maxBytes=(1024**2)/2)
    warning_file_handler.setLevel(logging.WARNING)

    debug_file_handler = logging.handlers.RotatingFileHandler(os.path.join(log_folder, "debug.txt"), maxBytes=(1024**2)/2)
    debug_file_handler.setLevel(logging.DEBUG)

    logging.basicConfig(level=logging.DEBUG, handlers=[console_handler, file_handler, warning_file_handler, debug_file_handler])

if __name__ == "__main__":
    set_up_logging()
    EmojiCountBot(get_api_key()).run(reset_data=False)