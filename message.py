from discord import Message, RawReactionActionEvent, User
from typing import List, Callable, Union


class MessageSequence:

    def __init__(self):
        """
        Initializes a sequence. This is all just assigning variables needed for
        the Sequences that inherit from this one, and leaving them empty; their
        respective constructors should fill variables as needed.
        """

        print("reached MessageSequence __init__()")

        # the message sent to user to start the sequence
        self.starter: Callable[[User], None] = None

        # the current handler. Handlers are expected to pass control to next
        # handlers when they terminate using the pass_handler() function.
        self.current_handler: Union[Callable[[Message], None],
                                    Callable[[RawReactionActionEvent], None]] \
            = None

        self.current_message: Message = None

        # if this is a PM, the User involved (can be set via the Starter)
        self.user = None

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

    async def run_next_handler(self, arg: Union[Message, RawReactionActionEvent])\
            -> None:
        if self.current_handler is not None:
            await self.current_handler(arg)
        else:
            print("Sequence has no more messages")

    async def start_sequence(self, user: User):
        if not self.current_handler:
            await self.starter(user)

    async def is_started(self):
        return self.current_handler is None


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
