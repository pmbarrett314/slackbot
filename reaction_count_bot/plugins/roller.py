import random

from plugins.message_handler import MessageHandler


class Roller(MessageHandler):
    def __init__(self, bot):
        super().__init__(bot)
        self.add_message_hanlder(self.roll_dice, "roll (?P<number>\d*)d(?P<size>\d*)", address=True)
        self.add_message_hanlder(self.flip_coin, "flip a coin", address=True)

    def roll_dice(self, match_object, message_object):
        rolls = []
        number_of_dice = int(match_object.group("number"))
        die_size = int(match_object.group("size"))
        channel = message_object.channel
        sender = message_object.sender_id

        if not 0 <= number_of_dice < 1000:
            self.bot.dm("no", sender)
            return
        if not die_size > 0:
            self.bot.dm("no", sender)

        for _ in range(number_of_dice):
            rolls.append(random.randint(1, die_size))
        score = sum(rolls)
        message = "{}: {}".format(rolls, score)

        if len(message) > 100000:
            if len(str(score)) < 100000:
                self.bot.dm("Total: {}".format(str(score)), sender)
            return

        if len(message) > 1000:
            self.bot.dm(message, sender)
            if len(str(score)) < 1000:
                self.bot.say_in_channel("Total: {}".format(str(score)), channel)
            return

        self.bot.say_in_channel(message, channel)

    def flip_coin(self, match_object, message_object):
        heads = "heads"
        tails = "tails"

        channel = message_object.channel


        flip = random.choice([heads, tails])

        self.bot.say_in_channel(flip, channel)