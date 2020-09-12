from message import MessageSequence
from discord import Message, User, Embed, Reaction
from typing import List, Callable, Union
import unicode_constants


class MessageSequenceTest(MessageSequence):

    def __init__(self):
        super().__init__()
        self.value_1 = None
        self.value_2 = None
        self.value_3 = None
        self.starter = self.initial_message

    async def initial_message(self, user: User):

        self.user = user

        starter_embed = Embed()
        starter_embed.title = "starter title"
        starter_embed.description = "starter description"

        starter_msg = await user.send(embed=starter_embed)
        await starter_msg.add_reaction(unicode_constants.UNICODE_FORWARD_ARROW)
        self.current_message = starter_msg
        self.pass_handler(self.handler_one)

    @MessageSequence.requires_reaction
    async def handler_one(self, message: Message):
        print("invoked handler_one")
        added_reactions: List[Reaction] \
            = MessageSequence.get_reactions_added(message)
        if len(added_reactions) == 0:
            print("ERROR: no reactions on message")
            return

        self.value_1 = added_reactions[0].emoji

        await self.message_one(self.user)

        self.pass_handler(self.handler_two)

    @MessageSequence.requires_reaction
    async def handler_two(self, message: Message):
        added_reactions: List[Reaction] \
            = MessageSequence.get_reactions_added(message)
        if len(added_reactions) == 0:
            print("ERROR: no reactions on message")
            return
        self.value_2 = added_reactions[0].emoji

        await self.message_text(self.user)

        self.pass_handler(self.handler_text)

    @MessageSequence.requires_reaction
    async def handler_three(self, message: Message):
        added_reactions: List[Reaction] \
            = MessageSequence.get_reactions_added(message)
        if len(added_reactions) == 0:
            print("ERROR: no reactions on message")
            return
        self.value_3 = added_reactions[0].emoji

        await self.message_final(self.user)
        self.pass_handler(None)

    @MessageSequence.requires_message
    async def handler_text(self, message: Message):
        self.value_3 = message.content
        await self.message_final(self.user)
        self.pass_handler(None)

    async def message_one(self, user: User):
        embed = Embed()
        embed.title = "message 1 title"
        embed.description = "message 1 description"

        msg = await user.send(embed=embed)
        await msg.add_reaction(unicode_constants.UNICODE_FORWARD_ARROW)
        self.current_message = msg

    async def message_two(self, user: User):
        embed = Embed()
        embed.title = "message 2 title"
        embed.description = "message 2 description"

        msg = await user.send(embed=embed)
        print("sent message 2")
        await msg.add_reaction(unicode_constants.UNICODE_1)
        await msg.add_reaction(unicode_constants.UNICODE_2)
        await msg.add_reaction(unicode_constants.UNICODE_3)
        print("added reactions to message 2")
        self.current_message = msg

    async def message_three(self, user: User):
        embed = Embed()
        embed.title = "message 3 title"
        embed.description = "message 3 description"

        msg = await user.send(embed=embed)
        await msg.add_reaction(unicode_constants.UNICODE_4)
        await msg.add_reaction(unicode_constants.UNICODE_5)

        self.current_message = msg

    async def message_text(self, user: User):
        msg = await user.send(content="send me a message!")
        self.current_message = msg

    async def message_final(self, user: User):
        final_string = "Reached end of message chain; restart bot to try again" \
                      "\nYou chose the emojis: " \
                      "{0}, {1}, {2}".format(
                        self.value_1,
                        self.value_2,
                        self.value_3
                        )

        msg = await user.send(content=final_string)

        self.current_message = msg
