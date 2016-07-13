class SlackObject(object):

    def __init__(self, object_json, slack_client):
        self.object_json = object_json


class SlackUser(SlackObject):

    slack_api_method = "users.list"
    slack_class_name = "User"
    response_list_key = "members"

    def __init__(self, object_json, slack_client):
        super().__init__(object_json, slack_client)
        self.name = object_json["name"]



class UnknownBot():

    def __init__(self):
        self.name = "Unknown_bot"


class SlackChannel(SlackObject):

    slack_api_method = "channels.list"
    slack_class_name = "Channel"
    response_list_key = "channels"

    def __init__(self, object_json, slack_client):
        super().__init__(object_json, slack_client)
        self.name = "#{}".format(object_json["name"])


class SlackMPIM(SlackObject):

    slack_api_method = "mpim.list"
    slack_class_name = "MPIM"
    response_list_key = "groups"

    def __init__(self, object_json, slack_client):
        super().__init__(object_json, slack_client)
        self.name = object_json["name"]


class SlackGroup(SlackObject):

    slack_api_method = "groups.list"
    slack_class_name = "Group"
    response_list_key = "groups"

    def __init__(self, object_json, slack_client):
        super().__init__(object_json, slack_client)
        self.name = "#{}".format(object_json["name"])


class SlackDM(SlackObject):

    slack_api_method = "im.list"
    slack_class_name = "DM"
    response_list_key = "ims"

    def __init__(self, object_json, slack_client):
        super().__init__(object_json, slack_client)
        self.user = slack_client.get_user(object_json["user"])
        self.user_name = self.user.name
        self.name = "DM with {}".format(self.user_name)
        self.id = object_json["id"]
