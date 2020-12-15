from message import MessageSequence
from discord import User, Embed, Message, Emoji, Guild, TextChannel
from discord.utils import find
from unicode_constants import UNICODE_1, UNICODE_2, UNICODE_3, \
    UNICODE_FORWARD_ARROW, UNICODE_0, UNICODE_4, UNICODE_5, UNICODE_6
from db.dbfacade import DatabaseFacade
from db.property_constants import GAME_CATEGORY_PROPERTY_NAME, JOIN_GAME_CHANNEL
from db.model import Game
from game_modes import GameMode
import unicodedata as ud


class NewGameSequence(MessageSequence):

    def __init__(self, user: User, guild: Guild):
        super().__init__(user)
        self.starter = self.initial_message

        # PC, XBOX, or PS4
        self.platform_choice: str = None

        # Number of teams in this game
        self.team_count: int = None

        # Number of players on a team
        self.team_size: int = None

        self.mode_str: str = None

        # Written description of the game
        self.game_description: str = None

        self.guild_reference: Guild = guild

        self.game: Game = None

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
            print(f"Comparing {[ud.name(char) + ' ' for char in platform_choice]} to {UNICODE_1}")
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
        desc = "(type the number of teams. Use '0' for FFA. Max 4 teams.)"

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

        if 2 <= team_count <= 4 or team_count == 0:
            self.team_count = team_count
        else:
            await self.user.send(
                content="Number of teams must be between 2 and 4"
            )
            return

        if team_count > 0:
            await self.team_size_message()
            self.pass_handler(self.team_size_handler)
        # FFA games don't have to specify team sizes
        else:
            self.mode_str = "FFA"
            await self.ffa_player_count_message()
            self.pass_handler(self.ffa_player_count_handler)

    async def team_size_message(self):
        title = "How many players on each team?"
        max_team_size = 8 // self.team_count
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

        max_team_size = 8 // self.team_count
        if not 0 < team_size <= max_team_size:
            await self.user.send("Team size must be between 1 and {}".format(
                max_team_size
            ))
            return

        else:
            self.team_size = team_size

        self.mode_str = ((str(self.team_size) + "v")
                         * (self.team_count - 1)
                         + str(self.team_size))

        await self.team_assignment_message()
        self.pass_handler(self.team_assignment_handler)

    async def team_assignment_message(self):
        title = "Random or Fixed Teams"
        description = ("Select team assignment:"
                       "\n:one: Fixed"
                       "\n:two: Random")

        assign_embed = Embed()
        assign_embed.title = title
        assign_embed.description = description

        msg = await self.user.send(embed=assign_embed)
        self.current_message = msg
        await msg.add_reaction(UNICODE_1)
        await msg.add_reaction(UNICODE_2)

    @MessageSequence.requires_reaction
    async def team_assignment_handler(self, message: Message):
        reactions: list = MessageSequence.get_reactions_added(message)
        if len(reactions) > 1:
            print("Too many reactions to message")
            return
        # case should never trigger due to requires_reaction
        elif len(reactions) == 0:
            print("No reaction provided to message")
            return
        else:
            reaction = reactions[0]
            emoji = reaction.emoji
            if emoji == UNICODE_1:
                self.mode_str += " Fixed Teams"
            elif emoji == UNICODE_2:
                self.mode_str += " Random Teams"
            else:
                print(f"invalid reaction: {str(emoji)}")
                return

            await self.game_description_message()
            self.pass_handler(self.game_description_handler)

    async def ffa_player_count_message(self):
        title = "Number of Players"
        desc = "Enter the number of players in your FFA game"

        player_count_embed = Embed()
        player_count_embed.title = title
        player_count_embed.description = desc

        self.current_message = await self.user.send(embed=player_count_embed)

    @MessageSequence.requires_message
    async def ffa_player_count_handler(self, message: Message):
        try:
            player_count = int(message.content)
        except ValueError as e:
            await self.user.send(f"{message.content} is not a number.")
            return

        if 0 < player_count <= 8:
            self.team_size = player_count
            await self.game_description_message()
            self.pass_handler(self.game_description_handler)

        else:
            await self.user.send(f"Number of players must be between 2 and 8")
            return


    async def game_description_message(self):
        title = "Game Info"
        desc = "Please enter any info about your game that you'd like other" \
               " players to see. Things like custom rules, world settings, etc." \
               "\nOnly text in the next message you send will be accepted. Use" \
               " Shift+Enter if multiple lines are required."

        description_embed = Embed()
        description_embed.title = title
        description_embed.description = desc

        msg = await self.user.send(embed=description_embed)
        self.current_message = msg

    @MessageSequence.requires_message
    async def game_description_handler(self, message: Message):
        self.game_description = message.content

        await self.user_confirm_message()

        self.pass_handler(self.user_confirm_handler)

    async def user_confirm_message(self):
        confirm_embed = Embed()

        confirm_embed.title = "Confirm Game Setup"

        confirm_embed.description = (
            f"Mode: {self.mode_str}\n"
            + f"Platform: {self.platform_choice}\n"
            + f"Description: {self.game_description}\n"
            + "React :one: to accept, :two: to restart"
        )

        msg = await self.user.send(embed=confirm_embed)
        self.current_message = msg

        await msg.add_reaction(UNICODE_1)
        await msg.add_reaction(UNICODE_2)

    @MessageSequence.requires_reaction
    async def user_confirm_handler(self, message: Message):
        reactions = MessageSequence.get_reactions_added(message)

        # case should never trigger due to requires_reaction
        if len(reactions) == 0:
            print("No reaction provided to message")
            return
        elif len(reactions) > 1:
            print("ERROR: Too many reactions added")
            return
        else:
            emoji: Emoji = reactions[0].emoji

            if emoji == UNICODE_1:
                # TODO: Add game message in public channel, and pass instead of
                #  empty string
                target_mode = None
                for mode in GameMode:
                    if mode.value[3] == self.mode_str:
                        target_mode = mode

                if target_mode is not None:
                    print(f"found a mode with modestring {self.mode_str}")
                    if target_mode.value[3] == "FFA":
                        self.game = DatabaseFacade.add_game(
                            str(self.user.id),
                            self.platform_choice,
                            target_mode.value,
                            "",
                            max_size=self.team_size
                        )
                    else:
                        self.game = DatabaseFacade.add_game(
                            str(self.user.id),
                            self.platform_choice,
                            target_mode.value,
                            "",
                        )

                    await self.create_game_channel()

                    await self.game_public_message()

                else:
                    print(f"Unrecognized mode: {self.mode_str}")
                    return None

            elif emoji == UNICODE_2:

                # wipe all data collected
                self.starter = self.initial_message
                self.platform_choice: str = None
                self.team_count: int = None
                self.team_size: int = None
                self.mode_str: str = None
                self.game_description: str = None
                self.game: Game = None

                # reset to first message
                await self.initial_message()

    async def create_game_channel(self):
        game_category = DatabaseFacade.get_property(
            GAME_CATEGORY_PROPERTY_NAME
        )

        print(f"Searching for category: {game_category.value}")

        game_id: str = str(self.game.id)
        game_category = find(
            lambda cat: cat.name == game_category.value,
            self.guild_reference.categories
        )

        print("Game categories: ")
        for category in self.guild_reference.categories:
            print(category.name)

        channel: TextChannel = await self.guild_reference.create_text_channel(
            name=f"Game-{game_id}",
            category=game_category
        )

        DatabaseFacade.update_game(
            self.game.id,
            channel_did=str(channel.id)
        )

        await channel.set_permissions(
            self.user,
            read_messages=True
        )
        await self.game_channel_message(channel)

    async def game_channel_message(self, channel):
        game_summary_embed = Embed()

        game_summary_embed.title = ("-" * 20) + f"Game {self.game.id} Summary" \
            + ("-" * 20)

        max_players = self.game.teams[0].size
        game_summary_embed.description = (
                f"Created by: {self.user.mention}\n"
                + f"Mode: {self.mode_str} "
                + (f"({max_players})" if self.mode_str == "FFA" else "") + "\n"
                + f"Platform: {self.platform_choice}\n"
                + f"Description: {self.game_description}\n"
                + ("" if self.game.mode.name == "FFA" or self.game.randomize_teams
                   else f"React to join a team (team 0 = no team)")
        )

        game_summary_msg = await channel.send(embed=game_summary_embed)

        DatabaseFacade.update_game(
            self.game.id,
            game_message_did=str(game_summary_msg.id)
        )

        team_emoji = [UNICODE_0, UNICODE_1, UNICODE_2, UNICODE_3, UNICODE_4,
                       UNICODE_5, UNICODE_6]

        if self.game.randomize_teams:
            pass
        else:
            for team in self.game.teams:
                emoji = team_emoji[team.number]
                await game_summary_msg.add_reaction(emoji)

    async def game_public_message(self):

        game_summary_embed = Embed()

        game_summary_embed.title = ("-" * 20) + f"Game {self.game.id} Summary" \
                                   + ("-" * 20)

        max_players = self.game.teams[0].size
        game_summary_embed.description = (
                "React to join!\n"
                + f"Created by: {self.user.mention}\n"
                + f"Mode: {self.mode_str} "
                + (f"({max_players})" if self.mode_str == "FFA" else "") + "\n"
                + f"Platform: {self.platform_choice}\n"
                + f"Platform: {self.platform_choice}\n"
                + f"Description: {self.game_description}\n"
        )

        channel_prop = DatabaseFacade.get_property(JOIN_GAME_CHANNEL)
        channel_name = channel_prop.value

        channel: TextChannel = find(
            lambda channel: channel.name == channel_name,
            self.guild_reference.channels
        )

        game_message = await channel.send(embed=game_summary_embed)

        DatabaseFacade.update_game(
            self.game.id,
            message_did=str(game_message.id)
        )
        await game_message.add_reaction(UNICODE_FORWARD_ARROW)
