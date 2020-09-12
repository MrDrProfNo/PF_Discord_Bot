from discord import Message, User, Reaction, DMChannel
from discord.abc import Messageable
from typing import List, Callable, Union


class MessageSequence:

    def __init__(self):
        """
        Initializes a sequence. This is all just assigning variables needed for
        the Sequences that inherit from this one, and leaving them empty; their
        respective constructors should fill variables as needed.
        """

        # the message sent to user to start the sequence
        self.starter: Callable[[User], None] = None

        # the current handler. Handlers are expected to pass control to next
        # handlers when they terminate using the pass_handler() function.
        self.current_handler: Callable[[Message], None] = None

        # field for use by handlers; in theory, the most recent message the
        # sequence had sent.
        self.current_message: Message = None

        # if this is a PM, the User involved (can be set via the Starter)
        self.user: User = None

        # TODO: if there need to be message sequences in public channels, the
        #  channel would be stored here.

    def pass_handler(self, next_handler: Callable) -> None:
        """
        Passes the control of the sequence on to the next handler function.
        Handlers MUST pass control to the next handler when they finish. If a
        handler is the last one, it can pass None instead.
        :return: None
        """
        self.current_handler = next_handler

    async def run_next_handler(self, arg: Message) -> None:
        if self.current_handler is not None:
            await self.current_handler(arg)
        else:
            print("Sequence has no more messages")

    async def start_sequence(self, user: User):
        if not self.current_handler:
            await self.starter(user)

    async def is_started(self):
        return self.current_handler is None

    @staticmethod
    def requires_reaction(handler):
        """
        A decorator for handler functions that enforces the passed message as
        the most recent message sent. Any other message is ignored
        :param handler: the function that this decorates
        :return: copy of function decorated with internal_call
        """

        async def internal_call(self, message: Message):

            # if the message is the last one this bot sent (assuming that the
            # last handler updated self.current_message properly)...
            if self.current_message.id == message.id:
                # I am invoking a non-static method from an object of type
                # MessageSequence from within a static method of the same
                # class, explicitly passing "self" - an instance of type
                # MessageSequence - and then the rest of that method's args
                #
                # I'm honestly having a hard time understanding why this
                # works.
                return await handler(self, message)
            else:
                # print to console for debugging purposes, and ignore the call.
                print("invoked handler with wrong message; content follows:\n{}"
                      .format(message.content))
                return
        return internal_call

    @staticmethod
    def requires_message(handler):
        """
        A decorator for handler functions that enforces the passed message is
        NOT the most recent message; for use when the user reply is expected
        to be text, not emoji reaction.
        :param handler:
        :return:
        """
        async def internal_call(self, message: Message):

            channel: Messageable = message.channel
            hist_list = await channel.history(limit=1).flatten()

            if len(hist_list) != 1:
                print("error in getting channel history; got {} messages"
                      .format(len(hist_list)))
            else:
                most_recent_message: Message = hist_list[0]
                if message.id == self.current_message.id:
                    print("reaction to current message received on non-reaction"
                          " handler: {}".format(self.user.display_name))
                elif not isinstance(message.channel, DMChannel):
                    # received new message, but it's in the wrong channel
                    pass
                elif most_recent_message.id == message.id:
                    return await handler(self, message)
                else:
                    return

        return internal_call

    @staticmethod
    def get_reactions_added(message: Message) -> List[Reaction]:
        """
        Returns a list of Reaction objects for each Reaction that has count > 1;
        as long as this is only used in private channels, it should guarantee
        that all Reactions returned were reacted to by the target user; any that
        they add would have a count of 1, as would any the bot added which the
        user has not reacted to.

        :param message: Message to check reactions for.
        :return: list of Reactions to the message.
        """
        message_reactions: List[Reaction] = message.reactions
        added_reactions: List[Reaction] = []
        for reaction in message_reactions:
            if reaction.count > 1:
                added_reactions.append(reaction)

        return added_reactions


class UserMessageStates:

    def __init__(self):
        self.user_message_states = {}

    async def add_user_sequence(self, user: User, message_sequence: MessageSequence):
        print("Added new message sequence {0} for user {1}, and started it."
              .format(str(type(message_sequence)), user.name))
        self.user_message_states[user.id] = message_sequence

    def get_user_sequence(self, user: User):
        if user.id in self.user_message_states.keys():
            return self.user_message_states[user.id]
        else:
            return None
