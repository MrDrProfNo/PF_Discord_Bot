from message import MessageSequence
from typing import Callable, Union, List
from discord import User, Embed, Message, Emoji
from unicode_constants import UNICODE_1, UNICODE_2, UNICODE_3
import unicodedata


class NewGameSequence(MessageSequence):

    def __init__(self, user: User):
        super().__init__(user)
        self.starter = self.initial_message

        self.platform_choice = None

    async def initial_message(self) -> None:
        title = "New Game!"
        desc = "What platform are you playing on?" \
               "\n:one: PC" \
               "\n:two: PS4" \
               "\n:three: XBOX"

        initial_embed = Embed()
        initial_embed.title = title
        initial_embed.description = desc

        initial_message = await self.user.send(embed=initial_embed)

        self.current_message = initial_message

        await initial_message.add_reaction(UNICODE_1)
        await initial_message.add_reaction(UNICODE_2)
        await initial_message.add_reaction(UNICODE_3)

    async def platform_handler(self, message: Message):
        reactions = self.get_reactions_added(message)
        if len(reactions) != 1:
            return
        else:
            platform_choice: Emoji = reactions[0].emoji
            if platform_choice.name == UNICODE_1:
                self.platform_choice = "PC"
            elif platform_choice.name == UNICODE_2:
                self.platform_choice = "PS4"
            elif platform_choice.name == UNICODE_3:
                self.platform_choice = "XBOX"
            else:
                return

        # TODO: set up next message based on dread's reply, pass handler
