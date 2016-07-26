from slack_bot.message_handler import MessageHandler
import random


class Roller(MessageHandler):

    def get_message_handlers(self):
        message_handlers = super().get_message_handlers()
        message_handlers["\<@({})\>:? roll (\d*)d(\d*)".format(self.bot.bot_id)].append(self.roll_dice)
        return message_handlers

    def roll_dice(self, match_object, message_object):
        rolls = []
        number_of_dice = int(match_object.group(2))
        die_size = int(match_object.group(3))
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
