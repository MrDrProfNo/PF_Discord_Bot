import discord
from discord.ext import commands
from discord import Message, Emoji, User, Guild, TextChannel, CategoryChannel, \
    DMChannel, Embed
import sys
import os
import unicodedata as ud
from message_sequences.message_sequence_example import MessageSequenceTest
from message_sequences.new_game_sequence import NewGameSequence
from message import UserMessageStates, MessageSequence
from unicode_constants import UNICODE_FORWARD_ARROW, UNICODE_1, \
    START_GAME_EMOJI, UNICODE_2, UNICODE_3, UNICODE_4, UNICODE_5, UNICODE_6, \
    UNICODE_0
from db.property_constants import CREATE_GAME_CHANNEL, JOIN_GAME_CHANNEL, \
    GAME_CATEGORY_PROPERTY_NAME
from db.dbfacade import DatabaseFacade
from db.model import Game
import random


intent = discord.Intents().all()

bot = commands.Bot(command_prefix='!', intent=intent)

# message sequence related code
message_states = UserMessageStates()


CONNECTION_STRING = os.getenv("DATABASE_URL")
BOT_TOKEN = os.getenv("TOKEN")

# some command line args provided
if len(sys.argv) > 1:

    # setting up the database connection string
    if len(sys.argv) == 3:
        BOT_TOKEN = sys.argv[1]
        database = DatabaseFacade(connection_string=sys.argv[2])
    else:
        print(
            "Incorrect number of args; requires connection string in position 2"
        )
        exit()
# no command line args provided
elif len(sys.argv) == 1:

    # establish that a connection string is available
    if CONNECTION_STRING is None:
        # getenv failed
        print(
            "No command line args, and connection string environment variable"
            " missing"
        )
        exit()
    else:
        # getenv found something; will crash later if invalid token.
        database = DatabaseFacade(connection_string=CONNECTION_STRING)


    # establish that a bot token is available.
    if BOT_TOKEN is None:
        # getenv failed
        print(
            "No command line args, and bot token environment variable missing"
        )
        exit()


async def is_admin(context: commands.Context):
    user: discord.Member = context.author
    user_permissions: discord.Permissions = user.permissions_in(context.channel)
    user_role_names = [role.name for role in iter(user.roles)]

    return user_permissions.administrator or ("admin" in user_role_names)


@bot.event
async def on_connect():
    print("Connected")


@bot.event
async def on_ready():
    print("Ready")


@bot.event
async def on_disconnect():
    print("Disconnect")


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    print("-" * 20 + "reaction received" + "-" * 20)
    print("REACTION:")
    print("emoji:", str(reaction.emoji))
    print("uni-emoji:", ud.name(reaction.emoji[0]))
    print("num reactions:", str(reaction.count))
    print("I reacted:", str(reaction.me))
    print("message ID:", str(reaction.message.id))
    print("react by USER:")
    print("username:", str(user.display_name))
    print("user is bot:", str(user.bot))


@bot.event
async def on_message(message: discord.Message):
    print(message.content, ":", len(message.content))
    if not message.author.bot:
        author_name = message.author.name
        channel: discord.TextChannel = message.channel

        if type(channel) == discord.TextChannel:
            channel_name = channel.name
        else:
            channel_name = "DM"

        content = message.content
        print("{0}({1}): {2}".format(
            author_name,
            channel_name,
            content
        ))

        message_sequence: MessageSequenceTest \
            = message_states.get_user_sequence(message.author)

        if message_sequence is not None:
            await message_sequence.run_next_handler(message)

    # overriding on_message stops the bot from processing @bot.command()
    # functions. So we have to call this instead if we want messages to be
    # correctly as interpreted as commands.
    await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    user = bot.get_user(payload.user_id)

    # DEBUG output, enable if needed.
    # print("RAW reaction received")
    # print("From user:", user.name, "(" + str(payload.user_id) + ")")
    # print("reaction:", payload.emoji)
    # print("emoji name:", payload.emoji.name)
    # print("emoji id:", payload.emoji.id)
    # print(payload.emoji.name, "?=", UNICODE_1, ":", payload.emoji.name == UNICODE_1)
    # print("payload channel: {}".format(payload.channel_id))

    guild: Guild = bot.get_guild(payload.guild_id)

    # Looks like all possible send targets inherit from Messageable, and EITHER
    # GuildChannel or PrivateChannel (all 3 of which are in discord.abc)
    channel: discord.TextChannel = bot.get_channel(payload.channel_id)
    print(f"channel: {channel}")
    message: Message = await channel.fetch_message(payload.message_id)

    if not user.bot:

        create_game_prop = DatabaseFacade.get_property(
            property_name=CREATE_GAME_CHANNEL
        )

        # if the above evaluated true, then channel should have a name
        # attribute at this point.
        create_game_channel_name = create_game_prop.value

        join_game_prop = DatabaseFacade.get_property(
            property_name=JOIN_GAME_CHANNEL
        )

        join_game_channel_name = join_game_prop.value

        if type(channel) == DMChannel:
            print("checked as DMChannel")
            message_sequence: MessageSequenceTest \
                = message_states.get_user_sequence(user)

            # if the user has a sequence with the bot already...
            if message_sequence is not None:
                # pass the message along to the sequence's handler
                await message_sequence.run_next_handler(message)
                return
            # otherwise... just ignore them I think?
            else:
                return
        # this is the message the bot put in the create a game channel
        elif channel.name == create_game_channel_name:
            print("checked as a create game message")
            reactions = message.reactions
            for reaction in reactions:
                try:
                    await message.remove_reaction(reaction.emoji, user)
                except Exception as e:
                    print(f"ERROR: While removing reaction, got exception of "
                          f"type {type(e)}")

            new_game_sequence = NewGameSequence(user, guild)
            await message_states.add_user_sequence(user, new_game_sequence)
            await new_game_sequence.start_sequence()
        elif channel.name == join_game_channel_name:
            print("checked as a join game message")
            # reaction was added on a message in the games channel
            game: Game = DatabaseFacade.get_game_by_message_did(
                str(message.id)
            )

            user_as_player = DatabaseFacade.get_player_by_did(str(user.id))
            if game is not None:
                DatabaseFacade.add_player_to_game(game.id, user_as_player)
                game_channel: TextChannel = bot.get_channel(int(game.channel_id))
                await game_channel.set_permissions(
                    user,
                    read_messages=True
                )

                if game.is_full():
                    print("game is full, clearing all messages")
                    await message.clear_reactions()
            else:
                print(f"Game not found with message_did: {message.id}")

        # this should become a check against all of the game's private channel
        # messages, which I'll probably build team swapping into
        elif channel.category.name == DatabaseFacade.get_property(
                GAME_CATEGORY_PROPERTY_NAME
        ).value:
            print("CHECKED as a channel in the game category")
            if message.author.bot:
                game: Game = DatabaseFacade.get_game_by_game_message_did(
                    str(message.id)
                )

                user_as_player = DatabaseFacade.get_player_by_did(str(user.id))

                emoji_name = payload.emoji.name
                print("")
                if emoji_name == UNICODE_0:
                    team_number = 0
                elif emoji_name == UNICODE_1:
                    team_number = 1
                elif emoji_name == UNICODE_2:
                    team_number = 2
                elif emoji_name == UNICODE_3:
                    team_number = 3
                elif emoji_name == UNICODE_4:
                    team_number = 4
                elif emoji_name == UNICODE_5:
                    team_number = 5
                elif emoji_name == UNICODE_6:
                    team_number = 6
                else:
                    print(f"React with bad emoji: {emoji_name}")
                    try:
                        await message.remove_reaction(payload.emoji, user)
                    except Exception as e:
                        print(
                            f"ERROR: While removing reaction, got exception of "
                            f"type {type(e)}")

                    return

                if DatabaseFacade.add_player_to_team(
                    game.id,
                    team_number,
                    user_as_player
                ):
                    await channel.send(
                        content=f"{user.display_name} joined team "
                        f"{team_number}"
                    )
                else:
                    await channel.send(
                        content=f"Could not add {user.display_name} to team "
                        f"{team_number}: team is full or does not exist."
                    )

                try:
                    await message.remove_reaction(payload.emoji, user)
                except Exception as e:
                    print(f"ERROR: While removing reaction, got exception of "
                          f"type {type(e)}")


        else:
            print("CHECKED as other message")



@bot.command()
async def echo(context: commands.Context, *args):
    output_string = ""
    for arg in args:
        output_string += arg + " "
    if output_string == "":
        pass
    else:
        await context.send(content=output_string)


@bot.command()
@commands.check(is_admin)
async def scrims(context: commands.Context, *args):
    if len(args) > 0:
        await context.send("'!scrims' command does not accept arguments")
        return

    message_embed = discord.Embed()

    message_embed.title = ":tools: CREATE GAME"

    message_embed.description = \
        "React below :arrow_forward: and we'll start setting up your game" \
        "\n*Make sure your DMs are on*"

    message_embed.set_thumbnail(
        url="https://i.imgur.com/J6wmi3U.png%22%7D,%22color%22:4886754%7D"
    )

    message_embed.colour = discord.Colour.from_rgb(74, 144, 226)

    # context.send returns a Message for the content it just sent
    msg = await context.send(embed=message_embed)

    # Message objects can be manipulated in a variety of ways for interaction
    # with users
    await msg.add_reaction(UNICODE_FORWARD_ARROW)

    # TODO: message ID will come in useful later when tracking which message
    #  was reacted to.
    print("Message ID: " + str(msg.id))


@bot.command()
async def uni(context: commands.Context, emoji, *args):
    as_unicode = ""
    for character in emoji:
        as_unicode += "\\N{" + ud.name(character) + "}"
    reply_string = emoji + ": " + as_unicode

    await context.send(content=reply_string)


@bot.command()
@commands.check(is_admin)
async def demo(context: commands.Context, *args):
    if len(args) > 0:
        await context.send(content="demo accepts no arguments")
        return
    print("started demo")

    user: User = context.message.author
    message_sequence: MessageSequence = message_states.get_user_sequence(user)
    if message_sequence:
        await context.send(
            "Overwriting previous MessageSequence, which was: "
            + "Finished" if await message_sequence.is_finished() else "Not Finished"
        )
    message_sequence = MessageSequenceTest(user)

    await message_states.add_user_sequence(user, message_sequence)
    await message_sequence.start_sequence()


@bot.command()
@commands.check(is_admin)
async def newgame(context: commands.Context, *args):
    if len(args) > 0:
        await context.send(content="newgame accepts no arguments")
        return

    print("started newgame")

    user: User = context.message.author
    message_sequence: MessageSequence = message_states.get_user_sequence(user)
    if message_sequence:
        await context.send(
            "Overwriting previous MessageSequence, which was: "
            + "Finished" if message_sequence.is_finished() else "Not Finished"
        )
    message_sequence = NewGameSequence(user, context.guild)

    await message_states.add_user_sequence(user, message_sequence)
    await message_sequence.start_sequence()


@bot.command()
async def showgame(context: commands.Context, game_id: str):
    try:
        game_id = int(game_id)
    except ValueError:
        await context.send("usage: !game <game_id>")
        return

    retrieved_game = DatabaseFacade.get_game_by_id(game_id)
    await context.send("Game loaded:\n" + str(retrieved_game))
    return


@bot.command()
async def category(context: commands.Context, category_name: str, *args):
    guild: Guild = context.guild
    await guild.create_category(name=category_name)


@bot.command()
async def channel(context: commands.Context, channel_name: str,
                  category_name: str = None, *args):
    guild: Guild = context.guild

    if category_name is not None:
        target_category: CategoryChannel = discord.utils.find(
            lambda cat: cat.name == category_name,
            guild.categories
        )

        await guild.create_text_channel(
            name=channel_name,
            category=target_category,
            reason="test channel for PF_Discord_Bot"
        )
    else:
        await guild.create_text_channel(
            name=channel_name
        )


@bot.command()
async def pchannel(context: commands.Context, channel_name: str,
                    category_name: str = None, *args):

    guild: Guild = context.guild

    if category_name is not None:
        target_category: CategoryChannel = discord.utils.find(
            lambda cat: cat.name == category_name,
            guild.categories
        )

        new_channel: TextChannel = await guild.create_text_channel(
            name=channel_name,
            category=target_category,
            reason="test channel for PF_Discord_Bot"
        )

        await new_channel.set_permissions(context.author, read_messages=True)
    else:

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            context.author: discord.PermissionOverwrite(read_messages=True)
        }
        await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites
        )


@bot.command()
@commands.check(is_admin)
async def prop(context: commands.Context, prop_name: str, prop_value: str=None):
    if prop_value is None:
        prop = DatabaseFacade.get_property(prop_name)
        if prop is not None:
            await context.send(
                content=f"Value: {prop.value}"
            )
        else:
            await context.send(f"Property undefined: {prop_name}")
    else:
        DatabaseFacade.set_property(prop_name, prop_value)
        await context.send(
            content=f"set property {prop_name} to {prop_value}"
        )


@bot.command()
async def leave(context: commands.Context, *args):
    channel_did = str(context.channel.id)
    game: Game = DatabaseFacade.get_game_by_channel_did(channel_did)
    if game is not None:
        if len(args) > 0:
            await context.send("Usage: !leave")
            return
        player_did = str(context.author.id)
        leaver = DatabaseFacade.get_player_by_did(player_did=player_did)

        if leaver.id == game.creator_id:
            await context.send("The creator cannot leave the game; use !delete"
                               " to remove the game instead.")
            return

        DatabaseFacade.remove_player_from_game(game.id, leaver)

        game_channel_id: int = int(game.channel_id)

        game_channel: TextChannel = bot.get_channel(game_channel_id)

        await game_channel.set_permissions(
            context.author,
            read_messages=False
        )

        print("leave functioned properly so far....")

        await context.send(
            content=f"User {context.author.name} has left the game"
        )

        print("sent message on channel", context.channel.id)

        return


@bot.command()
async def kick(context: commands.Context, mentioned: User, *args):
    channel_did = str(context.channel.id)
    game: Game = DatabaseFacade.get_game_by_channel_did(channel_did)
    if game is not None:
        if len(args) > 0:
            await context.send("usage: !kick <@user>\nCan only be used by the"
                               " creator of the game")
            return
        else:

            caller_did = str(context.author.id)
            caller = DatabaseFacade.get_player_by_did(caller_did)

            if caller.id != game.creator_id:
                await context.send("!kick can only be used by the creator.")
                return

            mentioned_did = str(mentioned.id)
            kicked = DatabaseFacade.get_player_by_did(mentioned_did)

            if kicked.id == game.creator.id:
                await context.send(
                    "!kick cannot be used to remove the creator"
                )
                return

            success = DatabaseFacade.remove_player_from_game(game.id, kicked)

            if not success:
                await context.send(
                    f"Cannot kick user {mentioned.name}; user is not in game"
                )
                return

            game_channel: TextChannel = bot.get_channel(context.channel.id)

            await game_channel.set_permissions(
                mentioned,
                read_messages=False
            )

            await context.send(
                content=f"User {mentioned.name} has been kicked."
            )


@bot.command()
async def delete(context: commands.Context, *args):
    channel_did = str(context.channel.id)
    game: Game = DatabaseFacade.get_game_by_channel_did(channel_did)
    if game is not None:
        if len(args) > 0:
            await context.send("usage: !delete")
            return
        else:

            caller_did = str(context.author.id)
            caller = DatabaseFacade.get_player_by_did(caller_did)

            join_game_message_id = int(game.message_did)
            print(f"looking for join message with id {join_game_message_id}")

            join_game_channel_prop = DatabaseFacade.get_property(
                JOIN_GAME_CHANNEL
            )

            join_game_channel = discord.utils.find(
                lambda channel: channel.name == join_game_channel_prop.value,
                context.guild.text_channels
            )
            print(f"got join channel with name {join_game_channel.name}")

            join_game_message = await join_game_channel.fetch_message(
                join_game_message_id
            )

            if caller.id != game.creator_id:
                await context.send("Only the creator can delete a game")
                return

            DatabaseFacade.delete_game_by_id(game.id)

            print(f"deleting channel {context.channel.name}")
            await context.channel.delete()

            print(f"join_game_message has id")
            await join_game_message.delete()
            return


@bot.command()
async def teams(context: commands.Context):
    game: Game = DatabaseFacade.get_game_by_channel_did(str(context.channel.id))
    if game is not None:
        reply = f"#######Game {game.id}#######\n"
        if len(game.teams) == 1:
            reply += "FFA Games do not have teams"
        elif game.randomize_teams:
            reply += (
                f"Teams will be randomized when the game is started (use"
                f" {bot.command_prefix}start to start it)")
        else:
            for team in game.teams[1:]:
                if team.number == 0:
                    reply += "Undecided:\n"
                else:
                    reply += f"Team {team.number}:\n"

                for player in team.players:
                    user: User = await bot.fetch_user(int(player.did))
                    reply += f" - {user.display_name}\n"

        await context.send(reply)
    else:
        await context.send("This channel no longer has an associated game")


@bot.command()
async def start(context: commands.Context):
    game: Game = DatabaseFacade.get_game_by_channel_did(str(context.channel.id))
    if game.player_number != game.teams[0].size:
        await context.send("Cannot start game until game is full "
                           f"(current: {game.player_number}, "
                           f"needed: {game.teams[0].size})")
        # return
    elif game is not None:
        DatabaseFacade.start_game(game.id)

    start_embed = Embed()
    start_embed.title = "Starting game..."
    start_embed.description = (
            f"Game begun at {game.started_at} with teams:"
    )
    print("counting teams: ", len(game.teams))

    if game.teams_available:
        if game.randomize_teams:
            for team in game.teams[1:]:
                empty_slots = team.size - len(team.players)
                if empty_slots > len(game.teams[0].players):
                    await context.send(f"ERROR: Insufficient number of players "
                                       f"to fill teams; ran out on team "
                                       f"{team.number}")
                players = random.sample(game.teams[0].players, k=empty_slots)
                for player in players:
                    print(f"adding player {player.id} to team {team.number}")
                    DatabaseFacade.add_player_to_team(
                        game.id,
                        team.number,
                        player
                    )
        else:
            if sum([len(team.players) for team in game.teams[1:]])<len(game.teams[0]):
                await context.send("All players must be in a team before game can"
                                   " begin")
                return

        for team in game.teams[1:]:
            print("Players:", team.players, ":", int(team.players[0].did))
            player_names = [
                await bot.fetch_user(int(player.did)).name for player in team.players
            ]

            if len(player_names) > 0:
                player_string = "\n".join(player_names)
            else:
                player_string = "(no players)"
            start_embed.add_field(
                name=f"Team {team.number}",
                value=f"{player_string}",
                inline=False
            )
    else:
        player_names = [
            await bot.fetch_user(int(player.did)).name
            for player
            in game.teams[0].players
        ]
        if len(player_names) > 0:
            player_string = "\n".join(player_names)
        else:
            player_string = "(no players)"
        start_embed.add_field(
            name="Randomized teams",
            value=f"Players:\n {player_string}",
            inline=False
        )

    await context.send(embed=start_embed)


@bot.command()
async def test(context: commands.Context, arg: str):
    user: User = await bot.fetch_user(int(arg))
    await context.send(str(user))


def main():

    print("Using bot_token: " + BOT_TOKEN)

    bot.run(BOT_TOKEN)


if __name__ == '__main__':
    main()
