from discord import Message, User, Reaction, DMChannel
from discord.abc import Messageable
from typing import List, Callable, Union


class MessageSequence:
    """
    Class representing a sequence of text or emoji interactions that a user can
    have via DM with the bot. This class is abstract; extend it and use its
    methods to implement your own message sequences. For an example of such a
    sequence, see message_sequence_example.py.

    USAGE (read in full):

    Subclasses must implement the constructor __init__(self, user: User), and
    call this class' constructor with the same user, in order for the sequence
    to work. Subclass must also initialize self.starter to a function that takes
    no arguments and starts a DM with the user.

    self.user must not be altered.

    Each handler is expected to deal with the user's response to a previous
    DM, and then send a new DM. Communication with the user can be done through
    self.user.

    Users are permitted to reply to messages via Emoji reaction to the last
    message the bot sent, or via DM to the bot. See the requires_message and
    requires_reaction for ways to enforce a user reply of a specific type.

    self.current_message is used to track the message the user should be
    reacting to; if a new message is sent, you will likely want to update it.

    When a handler is finished processing user reply to the previous message,
    it should call pass_handler() to give control of the next reply to another
    function. If this is not done, the same handler will be called in response
    to the message that it sent. This can be useful if multiple responses to
    a single message are required, such as if multiple reactions need to be
    selected by the user before they can proceed.
    """

    def __init__(self, user: User):
        """
        Initializes a sequence. This is all just assigning variables needed for
        the Sequences that inherit from this one, and leaving them empty; their
        respective constructors should fill variables as needed.
        """

        # the message sent to user to start the sequence
        self.starter: Callable[[], None] = None

        # the current handler. Handlers are expected to pass control to next
        # handlers when they terminate using the pass_handler() function.
        self.current_handler: Callable[[Message], None] = None

        # field for use by handlers; in theory, the most recent message the
        # sequence had sent.
        self.current_message: Message = None

        # if this is a PM, the User involved (can be set via the Starter)
        self.user: User = user

        # TODO: if there need to be message sequences in public channels, the
        #  channel would be stored here instead of a User.

    def pass_handler(self, next_handler: Union[Callable, None]) -> None:
        """
        Passes the control of the sequence on to the next handler function.
        Handlers MUST pass control to the next handler when they finish. If a
        handler is the last one, it can pass None instead to indicate the end
        of the sequence.
        :return: None
        """
        self.current_handler = next_handler

    async def run_next_handler(self, msg: Message) -> None:
        """
        Runs the next handler if possible using the passed Message; depending on
        decorators used by the handler, it may reject the message and return
        before executing. See requires_reaction and requires_message.

        :param msg: the Message to give to the handler
        :return: None
        """
        if self.current_handler is not None:
            await self.current_handler(msg)
        else:
            print("Sequence has no more messages")

    async def start_sequence(self):
        """
        If the sequence has not been started, start it with the passed User.

        :param user: User to start message sequence with; this object will store
        and communicate with the user via DM.
        :return: None
        """
        if not self.current_handler:
            await self.starter()

    async def is_started(self) -> bool:
        """
        Returns boolean whether the message has been started. Usage is not
        required.

        :return: True if the message has been started, False otherwise.
        """
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
            """
            locally defined function is part of making a decorator.
            :param self: MessageSequence, required to allow calling on specific
            MessageSequence in a static context.

            :param message: Message the bot is answering; this function's checks
            guarantee context for it, so no context is guaranteed at this point.

            :return: handler, decorated with this function.
            """

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

        :param handler: the function that this decorates
        :return: copy of function decorated with internal_call
        """
        async def internal_call(self, message: Message):
            """
            locally defined function is part of making a decorator.
            :param self: MessageSequence, required to allow calling on specific
            MessageSequence in a static context.

            :param message: Message the bot is answering; this function's checks
            guarantee context for it, so no context is guaranteed at this point.

            :return: handler, decorated with this function.
            """

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
    """
    Class wrapping a dictionary mapping Users to MessageSequences.

    A user may only have one active MessageSequence at a time. Starting a new
    one overwrites any old ones.
    """

    def __init__(self):
        self.user_message_states = {}

    async def add_user_sequence(self, user: User, message_sequence: MessageSequence):
        """
        Link the User to the new MessageSequence. If a previous sequence exists,
        the new one will overwrite it.
        :param user: User to link the sequence to
        :param message_sequence: MessageSequence to link to user.
        :return:
        """
        print("Added new message sequence {0} for user {1}, and started it."
              .format(str(type(message_sequence)), user.name))
        self.user_message_states[user.id] = message_sequence

    def get_user_sequence(self, user: User):
        if user.id in self.user_message_states.keys():
            return self.user_message_states[user.id]
        else:
            return None
