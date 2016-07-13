from collections import Counter, defaultdict
import logging
import pickle
import os


class EmojiCounter():

    def __init__(self, slack_client):
        self.slack_client = slack_client

        self.positives = set(["thumbsdown", "plus1"])
        self.negatives = set(["thumbsdown", "nsfw", "fu"])

        self.upvotes = defaultdict(set)
        self.downvotes = defaultdict(set)

        self.log = logging.getLogger("emoji_counter")

        self.latest_timestamp = "0"
        self.counts = defaultdict(Counter)

        self.data_file = os.path.join("..", "data", "data.bin")
        self.ts_file = os.path.join("..", "data", "latest_ts.txt")

    def prep(self, reset_data=False):
        if not reset_data:
            self.read_data()

        if self.latest_timestamp == "0":
            self.count_user_reactions()
        else:
            self.get_new_messages_since_offline()
        self.dump_data()

    def score(self, user_id):
        score = 0
        for reaction in self.counts[user_id]:
            upvotes = len(self.upvotes[reaction])
            downvotes = len(self.downvotes[reaction])
            reaction_score = 0 if upvotes == downvotes else 1 if upvotes > downvotes else -1
            score += reaction_score * self.counts[user_id][reaction]

        return score

    def upvote(self, user_id, reaction):
        self.log.debug("{} upvoted {}".format(user_id, reaction))
        self.downvotes[reaction].discard(user_id)
        self.upvotes[reaction].add(user_id)
        self.log.debug(self.upvotes)

    def downvote(self, user_id, reaction):
        self.log.debug("{} downvoted {}".format(user_id, reaction))
        self.upvotes[reaction].discard(user_id)
        self.downvotes[reaction].add(user_id)
        self.log.debug(self.downvotes)

    def add_score(self, item_user, reaction, timestamp):
        self.counts[item_user][reaction] += 1
        self.log.info("{} now has {} {}".format(self.slack_client.get_user_name(item_user), self.counts[item_user][reaction], reaction))
        self.log.debug("{} {}".format(self.slack_client.get_user_name(item_user), self.counts[item_user]))
        self.latest_timestamp = timestamp

    def remove_score(self, item_user, reaction, timestamp):
        self.counts[item_user][reaction] -= 1
        self.log.info("{} now has {} {}".format(self.slack_client.get_user_name(item_user), self.counts[item_user][reaction], reaction))
        self.log.debug("{} {}".format(self.slack_client.get_user_name(item_user), self.counts[item_user]))
        self.latest_timestamp = timestamp

    def log_votes(self):
        self.log.info([u for u in self.upvotes.items() if len(u[1]) > 0])
        self.log.info([d for d in self.downvotes.items() if len(d[1]) > 0])

    def print_data(self):
        tot = 0
        for user in self.counts:
            self.log.info("{}: {}".format(self.slack_client.get_user(user).name, sum(self.counts[user].values())))
            tot += sum(self.counts[user].values())
        self.log.info("\t\t\t" + str(tot))

    def dump_data(self):
        with open(self.data_file, "wb") as f:
            pickle.dump((self.counts, self.upvotes, self.downvotes), f)
        with open(self.ts_file, "w") as f:
            f.write(self.latest_timestamp)

    def read_data(self):
        self.log.info("Reading data from file...")
        with open(self.data_file, "rb") as f:
            file_contents = f.read()
        if len(file_contents) > 0:
            file_tup = pickle.loads(file_contents)
            self.counts.update(file_tup[0])
            self.upvotes.update(file_tup[1])
            self.downvotes.update(file_tup[2])
        with open(self.ts_file, "r") as f:
            self.latest_timestamp = f.read().strip()
        self.log.info("Finished reading data.")

    def get_new_messages_since_offline(self):
        self.log.info("Getting new messages...")
        message_objects = self.slack_client.get_new_messages_since_timestamp(self.latest_timestamp, only_reacted_to=True)
        for message_object in message_objects:
            for reaction in message_object.reactions:
                self.counts[message_object.sender_id][reaction["name"]] += reaction["count"]

        if message_objects:
            self.latest_timestamp = message_objects[0].timestamp
        self.log.debug(self.counts)
        self.log.info("Finished getting new messages.")

    def count_user_reactions(self):
        self.log.info("Counting all user reactions...")
        unique_items = self.slack_client.get_unique_reacted_messages()

        for message_object in unique_items:
            for reaction in message_object.reactions:
                self.counts[message_object.sender_id][reaction["name"]] += reaction["count"]
        self.latest_timestamp = self.slack_client.get_latest_timestamp()

        self.log.debug(self.counts)
        self.log.debug(str(len(unique_items)))
        self.log.info("Finished counting all reactions.")
