import discord
from discord.ext import commands
from discord import Message, Emoji, User, Guild, TextChannel, CategoryChannel, \
    DMChannel
import sys
import unicodedata
from message_sequences.message_sequence_example import MessageSequenceTest
from message_sequences.new_game_sequence import NewGameSequence
from message import UserMessageStates, MessageSequence
from unicode_constants import UNICODE_FORWARD_ARROW, UNICODE_1, START_GAME_EMOJI
from db.property_constants import CREATE_GAME_CHANNEL, JOIN_GAME_CHANNEL
from db.dbfacade import DatabaseFacade
from db.model import Game

bot = commands.Bot(command_prefix='!')

# message sequence related code
message_states = UserMessageStates()

# db related code
if len(sys.argv) == 3:
    database = DatabaseFacade(connection_string=sys.argv[2])
else:
    print("Incorrect number of args; requires connection string in position 2")
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
    print("uni-emoji:", unicodedata.name(reaction.emoji[0]))
    print("num reactions:", str(reaction.count))
    print("I reacted:", str(reaction.me))
    print("message ID:", str(reaction.message.id))
    print("react by USER:")
    print("username:", str(user.display_name))
    print("user is bot:", str(user.bot))


@bot.event
async def on_message(message: discord.Message):
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
            print("CHECKED as DMChannel")
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
            print("CHECKED as a create game message")
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
            print("CHECKED as a join game message")
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
            else:
                print(f"Game not found with message_did: {message.id}")

        # this should become a check against all of the game's private channel
        # messages, which I'll probably build team swapping into
        elif channel.category_id is not None:
            print("CHECKED as a channel in a category")
            pass

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
    as_unicode = "\\N{" + unicodedata.name(emoji[0]) + "}"
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
async def game(context: commands.Context, game_id: str):
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
async def test(context: commands.Context):
    DatabaseFacade.add_player_to_game()


def main():
    if len(sys.argv) < 2:
        print(
            "Bot token must be passed as command line argument.\nIf you don't "
            "have the bot token yet, ask MrNo"
        )
        exit()

    bot_token = sys.argv[1]

    print("Using bot_token: " + bot_token)

    bot.run(bot_token)


if __name__ == '__main__':
    main()
