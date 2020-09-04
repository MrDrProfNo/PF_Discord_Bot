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
        self.starter = None

        # array to be filled with function references, which take EITHER a
        # message OR a Reaction.
        self.response_handlers: List[Union[Callable[[Message], None],
                                           Callable[[RawReactionActionEvent], None]]] = []

        # the current handler, element of self.response_handlers. Handlers are
        # expected to pass control to next handlers when they terminate using
        # the pass_handler() function.
        self.current_handler: Union[Callable[[Message], None],
                                    Callable[[RawReactionActionEvent], None]] = None

    def pass_handler(self) -> None:
        """
        Whatever the current handler is, move on to the next one.
        Handlers MUST call this method when they're finished
        :return: None
        """

        # Starter function works a bit differently and can't be included in the
        # list, so just special case for continuing after it
        if self.current_handler is None:
            self.current_handler = self.response_handlers[0]
            return

        # get the position of the current handler in the list.
        pos = self.response_handlers.index(self.current_handler)

        # if we're at the end of the handlers...
        if pos > len(self.response_handlers):

            # condition flags end of handler
            self.current_handler = None
        else:

            # move to the next handler, thus advancing the message chain.
            self.current_handler = self.response_handlers[pos + 1]

    async def run_next_handler(self, arg: Union[Message, RawReactionActionEvent]):
        if self.current_handler:
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
        await message_sequence.start_sequence(user)

    def get_user_sequence(self, user: User):
        if user.id in self.user_message_states.keys():
            return self.user_message_states[user.id]
        else:
            return None
