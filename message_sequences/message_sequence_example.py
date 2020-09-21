from message import MessageSequence
from discord import Message, User, Embed, Reaction
from typing import List
import unicode_constants


class MessageSequenceTest(MessageSequence):

    def __init__(self, user: User):
        super().__init__(user)
        self.value_1 = None
        self.value_2 = None
        self.value_3 = None
        self.starter = self.initial_message

    async def initial_message(self):
        """
        the starter message; sent to the user to mark the beginning of the
        new sequence. An emoji is attached for demonstration, but should not
        cause the bot to respond.

        :return: None
        """
        msg = "This is an example of a MessageSequence. Type anything to " \
              "continue. Note that reacting to the emoji below does nothing; " \
              "the next handler enforces a Message reply."

        starter_embed = Embed()
        starter_embed.title = "An Example MessageSequence"
        starter_embed.description = msg

        starter_msg = await self.user.send(embed=starter_embed)
        await starter_msg.add_reaction(unicode_constants.UNICODE_FORWARD_ARROW)
        self.current_message = starter_msg
        self.pass_handler(self.handle_text_reply)

    @MessageSequence.requires_message
    async def handle_text_reply(self, message: Message):
        """
        Invoked only if the user types something. Gives them a message to react
        to and passes control of the sequence to the next handler.

        :param message: a message sent to you by the user, enforced by
        requires_message

        :return: None
        """

        msg_title = "The \"response to user message\" message"
        msg_description = "You said: \"{}\"".format(message.content) + \
            "\nReact to 2 of this message's emoji to continue..."

        # creating an embed
        react_embed = Embed()
        react_embed.title = msg_title
        react_embed.description = msg_description

        msg = await self.user.send(embed=react_embed)

        # remember to set this, otherwise it'll be looking for reactions to
        # the previous message you set.
        self.current_message = msg

        # this is how reactions are added to the message you just sent. In this
        # case, the codes for 1/2/3/4 are used.
        await msg.add_reaction(unicode_constants.UNICODE_1)
        await msg.add_reaction(unicode_constants.UNICODE_2)
        await msg.add_reaction(unicode_constants.UNICODE_3)
        await msg.add_reaction(unicode_constants.UNICODE_4)

        self.pass_handler(self.handler_react_reply)

    @MessageSequence.requires_reaction
    async def handler_react_reply(self, message: Message):
        added_reactions: List[Reaction] \
            = MessageSequence.get_reactions_added(message)
        if len(added_reactions) != 2:
            # if there's no
            return
        else:
            msg_title = "The \"reaction to a reaction\" message"
            msg_description = "You reacted with {0} and {1}. This concludes " \
                              "this MessageSequence." \
                .format(
                    added_reactions[0],
                    added_reactions[1]
                )

            final_embed = Embed()
            final_embed.title = msg_title
            final_embed.description = msg_description

            msg = await self.user.send(embed=final_embed)
            self.current_message = msg

            self.pass_handler(None)
