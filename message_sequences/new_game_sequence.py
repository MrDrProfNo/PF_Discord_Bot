from message import MessageSequence
from typing import Callable, Union, List
from discord import User, Embed, Message, Emoji
from unicode_constants import UNICODE_1, UNICODE_2, UNICODE_3
import unicodedata


class NewGameSequence(MessageSequence):

    def __init__(self, user: User):
        super().__init__(user)
        self.starter = self.initial_message

        # PC, XBOX, or PS4
        self.platform_choice: str = None

        # Number of teams in this game
        self.team_count: int = None

        # Number of players on a team
        self.team_size: int = None

        # Written description of the game
        self.game_description: str = None

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

        self.pass_handler(self.platform_handler)

    @MessageSequence.requires_reaction
    async def platform_handler(self, message: Message):
        reactions = self.get_reactions_added(message)
        if len(reactions) != 1:
            return
        else:
            platform_choice: Emoji = reactions[0].emoji

            # emojis are coming through as type str, the same representation
            # I give them in, so equality comparisons work.
            if platform_choice == UNICODE_1:
                self.platform_choice = "PC"
            elif platform_choice == UNICODE_2:
                self.platform_choice = "PS4"
            elif platform_choice == UNICODE_3:
                self.platform_choice = "XBOX"
            else:
                return

        await self.team_count_message()
        self.pass_handler(self.team_count_handler)
        return

    async def team_count_message(self):
        title = "How many teams will there be?"
        desc = "(type the number of teams. Use '0' for FFA. Max 12 teams.)"

        team_count_embed = Embed()
        team_count_embed.title = title
        team_count_embed.description = desc

        msg = await self.user.send(embed=team_count_embed)
        self.current_message = msg

    @MessageSequence.requires_message
    async def team_count_handler(self, message: Message):
        try:
            team_count = int(message.content)
        except ValueError as e:
            await self.user.send(
                content="'{}' is not a number".format(message.content)
            )
            return

        if 2 <= team_count <= 12 or team_count == 0:
            self.team_count = team_count
        else:
            await self.user.send(
                content="Number of teams must be between 2 and 12"
            )
            return


        if team_count > 0:
            await self.team_size_message()
            self.pass_handler(self.team_size_handler)
        # FFA games don't have to specify team sizes
        else:
            await self.game_description_message()
            self.pass_handler(self.game_description_handler)

    async def team_size_message(self):
        title = "How many players on each team?"
        max_team_size = 12 // self.team_count
        desc = "(with {0} teams, teams can have at most {1} players)".format(
            self.team_count,
            max_team_size
        )

        team_size_embed = Embed()
        team_size_embed.title = title
        team_size_embed.description = desc

        msg = await self.user.send(embed=team_size_embed)
        self.current_message = msg

    @MessageSequence.requires_message
    async def team_size_handler(self, message: Message):
        try:
            team_size = int(message.content)
        except ValueError as e:
            await self.user.send(
                content="{} is not a number".format(message.content)
            )
            return

        max_team_size = 12 // self.team_count
        if not 0 < team_size <= max_team_size:
            await self.user.send("Team size must be between 1 and {}".format(
                max_team_size
            ))
            return

        else:
            self.team_size = team_size

        await self.game_description_message()
        self.pass_handler(self.game_description_handler)

    async def game_description_message(self):
        title = "Game Info"
        desc = "Please enter any info about your game that you'd like other" \
               " players to see. Things like custom rules, world settings, etc." \
               "\nOnly text in the next message you send will be accepted. Use" \
               "Shift+Enter if multiple lines are required."

        description_embed = Embed()
        description_embed.title = title
        description_embed.description = desc

        msg = await self.user.send(embed=description_embed)
        self.current_message = msg

    @MessageSequence.requires_message
    async def game_description_handler(self, message: Message):
        self.game_description = message.content

        # TODO: replace this with actual game setup instead of echoing their
        #  input.
        await self.game_summary_temp()
        self.pass_handler(None)

    async def game_summary_temp(self):
        """
        Temporary summary of the game for debug purposes. Instead of doing this,
        the program should store the game in the db and write the game to
        whatever channel games are going in.
        :return:
        """

        # should be formatting text like 2v2v2v2 in a 2-player/4-team game
        teams_string = ((str(self.team_size) + "v")
                        * (self.team_count - 1)
                        + str(self.team_size))

        title = "Summary of Game (end of sequence)"
        desc = "Teams: {0}\nDescription: {1}".format(
            teams_string,
            self.game_description
        )

        summary_embed = Embed()
        summary_embed.title = title
        summary_embed.description = desc

        msg = await self.user.send(embed=summary_embed)
        self.current_message = msg

    async def user_confirm_description_message(self, description: str):
        # TODO: Implement a "you wrote this; please confirm" message?
        pass
