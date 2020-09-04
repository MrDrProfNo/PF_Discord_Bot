from message import MessageSequence
from discord import Message, RawReactionActionEvent, User, Embed
from typing import List, Callable, Union
import unicode_constants


class MessageSequenceTest(MessageSequence):

    def __init__(self):
        super().__init__()
        self.value_1 = None
        self.value_2 = None
        self.value_3 = None
        self.starter = self.starter_message
        self.response_handlers.append(self.handler_one)
        self.response_handlers.append(self.handler_two)
        self.response_handlers.append(self.handler_three)

    async def handler_one(self, reaction: RawReactionActionEvent):
        self.value_1 = reaction.emoji

        await self.message_one(reaction.user_id)

        self.pass_handler()

    async def handler_two(self, reaction: RawReactionActionEvent):
        self.value_2 = reaction.emoji

        await self.message_two(reaction.user_id)

        self.pass_handler()

    async def handler_three(self, reaction: RawReactionActionEvent):
        self.value_3 = reaction.emoji

        await self.message_three(reaction.user_id)

        self.pass_handler()

    async def starter_message(self, user: User):
        starter_embed = Embed()
        starter_embed.title = "starter title"
        starter_embed.description = "starter description"

        starter_msg = await user.send(embed=starter_embed)
        await starter_msg.add_reaction(unicode_constants.UNICODE_FORWARD_ARROW)

        self.pass_handler()

    async def message_one(self, user: User):
        embed = Embed()
        embed.title = "message 1 title"
        embed.description = "message 1 description"

        msg = await user.send(embed=embed)
        await msg.add_reaction(unicode_constants.UNICODE_FORWARD_ARROW)

    async def message_two(self, user: User):
        embed = Embed()
        embed.title = "message 2 title"
        embed.description = "message 2 description"

        msg = await user.send(embed=embed)
        await msg.add_reaction(unicode_constants.UNICODE_1)
        await msg.add_reaction(unicode_constants.UNICODE_2)
        await msg.add_reaction(unicode_constants.UNICODE_3)

    async def message_three(self, user: User):
        embed = Embed()
        embed.title = "message 3 title"
        embed.description = "message 3 description"

        msg = await user.send(embed=embed)
        await msg.add_reaction(unicode_constants.UNICODE_4)
        await msg.add_reaction(unicode_constants.UNICODE_5)

    def message_final(self, user: User):
        final_string = "Reached end of message chain; restart bot to try again" \
                      "\nYou chose the emojis: " \
                      "{0}, {1}, {2}".format(
                        self.value_1,
                        self.value_2,
                        self.value_3
                        )

        user.send(content=final_string)
