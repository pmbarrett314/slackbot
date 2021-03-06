from slackclient import SlackClient
import logging
import time
import pprint
from slack_bot.slack_objects import SlackChannel, SlackDM, SlackMPIM, SlackGroup, SlackUser, UnknownBot
from slack_bot.slack_messages import parse_slack_message, NoChannelException


class MySlackClient(SlackClient):

    def __init__(self, api_key):
        super(MySlackClient, self).__init__(api_key)

        self.log = logging.getLogger("my_slack_client")

        self.users = dict()
        self.channels = dict()
        self.dms = dict()
        self.dms_by_user = dict()
        self.groups = dict()
        self.mpims = dict()

    def api_call(self, *args, **kwargs):
        response = super().api_call(*args, **kwargs)
        if "ok" in response and response["ok"]:
            self.log.debug(pprint.pformat(response))
        else:
            self.log.warning(pprint.pformat(response))
        return response

    def connect(self):
        if not self.rtm_connect():
            raise Exception("Unable to connect to rtm socket")
        self.check_for_hello()

    def check_for_hello(self):
        for _ in range(10):
            for event in self.rtm_read():
                if event["type"] == "hello":
                    self.log.info("Connected successfully\n")
                    return
                else:
                    self.log.error("received unexpected message while waiting for hello: {}".format(event))
            time.sleep(1)
        raise Exception("Unable to connect to RTM")

    def fetch_updated_list(self, slack_class):
        self.log.info("Fetching {}s from server...".format(slack_class.slack_class_name))
        resp = self.api_call(slack_class.slack_api_method)
        if not resp["ok"]:
            raise Exception("Unable to call {}".format(slack_class.slack_api_method))

        return_dict = dict()
        for item in resp[slack_class.response_list_key]:
            return_dict[item["id"]] = slack_class(item, self)
        self.log.info("Done Fetching {}s.".format(slack_class.slack_class_name))
        return return_dict

    def update_all_data(self):
        self.update_users()
        self.update_channels()
        self.log.info("\n")

    def update_users(self):
        self.users = self.fetch_updated_list(SlackUser)

    def update_channels(self):
        self.update_dms()
        self.update_groups()
        self.update_mpims()
        self.update_just_channels()

    def update_just_channels(self):
        self.channels = self.fetch_updated_list(SlackChannel)

    def update_groups(self):
        self.groups = self.fetch_updated_list(SlackGroup)

    def update_mpims(self):
        self.mpims = self.fetch_updated_list(SlackMPIM)

    def update_dms(self):
        self.dms = self.fetch_updated_list(SlackDM)
        self.dms_by_user = self.update_dms_by_user()

    def update_dms_by_user(self):
        dms_by_user = dict()
        for dm in self.dms.values():
            if dm.user in dms_by_user:
                self.log.warning("{} already in dms by user".format(self.get_user_name(dm.user)))
            dms_by_user[dm.user] = dm
        return dms_by_user

    def get_users(self):
        self.update_users()
        return self.users.keys()

    def get_just_channels(self):
        self.update_just_channels()
        return self.channels.keys()

    def get_object(self, object_id, update_method, object_dict):
        try:
            return object_dict[object_id]
        except KeyError:
            update_method()
            return object_dict[object_id]

    def get_user(self, user_id):
        if user_id[0] == "B":
            return UnknownBot()
        else:
            return self.get_object(user_id, self.update_users, self.users)

    def get_just_channel(self, channel_id):
        return self.get_object(channel_id, self.update_just_channels, self.channels)

    def get_group(self, group_id):
        return self.get_object(group_id, self.update_groups, self.groups)

    def get_mpim(self, mpim_id):
        return self.get_object(mpim_id, self.update_mpims, self.mpims)

    def get_dm(self, dm_id):
        return self.get_object(dm_id, self.update_dms, self.dms)

    def get_dm_for_user(self, user_id):
        try:
            return self.dms_by_user[user_id]
        except KeyError:
            self.update_dms()
            try:
                return self.dms_by_user[user_id]
            except KeyError:
                dm_id = self.open_dm_to_user(user_id)
                self.update_dms()
                return dm_id

    def open_dm_to_user(self, user_id):
        resp = self.api_call("im.open", user=user_id)
        if not resp["ok"]:
            raise Exception(str(resp))
        else:
            return resp["channel"]["id"]

    def get_user_name(self, user_id):
        return self.get_user(user_id).name

    def get_channel_name(self, channel_id):
        return self.get_channel(channel_id).name

    def get_channel(self, channel_id):
        if channel_id[0] == "C":
            return self.get_just_channel(channel_id)
        elif channel_id[0] == "D":
            return self.get_dm(channel_id)
        elif channel_id[0] == "G":
            try:
                return self.get_group(channel_id)
            except:
                try:
                    return self.get_mpim(channel_id)
                except:
                    raise Exception("Group/ MPIM with ID {} does not exist")
        else:
            raise Exception("This ID is not a valid type of channel")

    def get_new_messages_since_timestamp(self, timestamp, only_reacted_to=False):
        messages = []
        message_objects = []
        for channel in self.get_just_channels():
            resp = self.api_call("channels.history", channel=channel, latest="1700000000.000000", oldest=timestamp)
            if not resp["ok"]:
                raise Exception(str(resp))
            else:
                for message in messages:
                    message["channel"] = channel
                messages.extend(resp["messages"])
            while resp["has_more"]:
                resp = self.api_call("channels.history", channel=channel, latest=messages[-1]["ts"], oldest=timestamp)
                if not resp["ok"]:
                    raise Exception(str(resp))
                else:
                    for message in messages:
                        message["channel"] = channel
                    messages.extend(resp["messages"])
        for message in messages:
            if not only_reacted_to or "reactions" in message:
                try:
                    message_object = parse_slack_message(message)
                except NoChannelException:
                    continue
                if message_object is not None:
                    message_objects.append(message_object)
        return message_objects

    def get_unique_reacted_messages(self):
        unique_items = set()
        items = []

        for user in self.get_users():
            resp = self.api_call("reactions.list", user=user)
            if "items" in resp:
                items.extend(resp["items"])
            if "paging" in resp:
                paging = resp["paging"]
                while paging["page"] < paging["pages"]:
                    resp = self.api_call("reactions.list", user=user, page=paging["page"]+1)
                    paging = resp["paging"]
                    items.extend(resp["items"])
            self.log.debug("{} {}".format(self.get_user(user).name, len(items)))

        for item in items:
            message_object = None
            if item["type"] == "message":
                message = item["message"]
                if "channel" not in message:
                    message["channel"] = None
                message_object = parse_slack_message(message)
            if message_object is not None:
                unique_items.add(message_object)
        return unique_items

    def get_latest_timestamp(self):
        self.log.debug("get_ltest_timestamp")
        latest_ts = "0"
        for channel in self.get_just_channels():
            resp = self.api_call("channels.history", channel=channel, count=1)
            self.log.debug(resp)
            if not resp["ok"]:
                raise Exception(str(resp))
            else:
                if resp["messages"]:
                    ts = resp["messages"][0]["ts"]
                    if ts > latest_ts:
                        latest_ts = ts
        return latest_ts
