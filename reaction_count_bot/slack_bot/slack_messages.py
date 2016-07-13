import logging
import pprint


def parse_slack_message(message_json):
    log = logging.getLogger("slack_messages")
    message_object = None
    if "subtype" in message_json:
        if message_json["subtype"] == "bot_message":
            message_object = BotMessage(message_json)
        elif message_json["subtype"] == "me_message":
            message_object = MeMessage(message_json)
        elif message_json["subtype"] == "channel_topic":
            message_object = ChannelTopicMessage(message_json)
        elif message_json["subtype"] == "channel_join":
            message_object = ChannelJoinMessage(message_json)
        elif message_json["subtype"] == "pinned_message":
            message_object = PinnedMessage(message_json)
        elif message_json["subtype"] == "pinned_item":
            message_object = PinnedItem(message_json)
        elif message_json["subtype"] == "file_mention":
            message_object = FileMention(message_json)
        elif message_json["subtype"] == "file_share":
            message_object = FileShare(message_json)
        elif message_json["subtype"] == "message_changed":
            message_object = MessageChanged(message_json)
        else:
            log.warn(message_json)
    elif "user" in message_json:
        message_object = OrdinaryMessage(message_json)
    else:
        log.warn(message_json)
    return message_object


class SlackMessage(object):

    def __init__(self, message_json):
        self.timestamp = message_json["ts"]
        if "reactions" in message_json:
            self.reactions = message_json["reactions"]
            self.has_reactions = True
        else:
            self.has_reactions = False

        if "text" in message_json:
            if message_json["text"] is None:
                self.has_text = False
            else:
                self.has_text = True
                self.text = message_json["text"]
        else:
            raise Exception("Message has no text {}".format(pprint.pformat(message_json)))

        if "channel" in message_json:
            self.channel = message_json["channel"]
        else:
            raise Exception("Message has no channel {}".format(pprint.pformat(message_json)))

        self.message_json = message_json
        if "user" in message_json:
            self.sender_id = message_json["user"]
        else:
            raise Exception("Message has no user {}".format(pprint.pformat(message_json)))

    def __hash__(self):
        return hash(self.sender_id + self.timestamp)


class BotMessage(SlackMessage):

    def __init__(self, message_json):
        message_json["user"] = message_json["bot_id"]
        self.bot_id = message_json["bot_id"]

        super().__init__(message_json)


class MeMessage(SlackMessage):
    pass


class ChannelJoinMessage(SlackMessage):
    pass


class ChannelTopicMessage(SlackMessage):
    pass


class PinnedMessage(SlackMessage):
    pass


class PinnedItem(SlackMessage):
    pass


class OrdinaryMessage(SlackMessage):
    pass


class FileMention(SlackMessage):
    pass


class FileShare(SlackMessage):
    pass


class MessageChanged(SlackMessage):
    def __init__(self, message_json):
        message_json["text"] = None
        if "edited" in message_json["message"]:
            message_json["user"] = message_json["message"]["edited"]["user"]
        else:
            message_json["user"] = message_json["message"]["user"]
        super().__init__(message_json)

