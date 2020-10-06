import discord
from discord.ext import commands
from discord import Message
import sys
import unicodedata
from message_sequences.message_sequence_example import MessageSequenceTest
from message import UserMessageStates
from unicode_constants import UNICODE_FORWARD_ARROW
from db.dbfacade import DatabaseFacade

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
    print("RAW reaction received")
    user = bot.get_user(payload.user_id)
    print("From user:", user.name, "(" + str(payload.user_id) + ")")

    # Looks like all possible send targets inherit from Messageable, and EITHER
    # GuildChannel or PrivateChannel (all 3 of which are in discord.abc)
    print("payload channel: {}".format(payload.channel_id))
    channel: discord.abc.Messageable = bot.get_channel(payload.channel_id)
    message: Message = await channel.fetch_message(payload.message_id)

    if not user.bot:
        message_sequence: MessageSequenceTest \
            = message_states.get_user_sequence(user)

        # if the user has a sequence with the bot already...
        if message_sequence is not None:
            # pass the message along to the sequence's handler
            await message_sequence.run_next_handler(message)
        # no sequence with bot yet...
        else:
            message_sequence = MessageSequenceTest(user)

            await message_states.add_user_sequence(user, message_sequence)
            await message_sequence.start_sequence()


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
async def reg(context: commands.Context, *args):
    print("reg invoked")
    user = context.message.author
    user_did = str(user.id)
    database.add_user(user.name, user_did)

def main():
    if len(sys.argv) < 2:
        print(
            "Bot token must be passed as command line argument.\nIf you don't "
            "have the bot token yet, ask MrNo")
        exit()

    bot_token = sys.argv[1]

    print("Using bot_token: " + bot_token)

    bot.run(bot_token)


if __name__ == '__main__':
    main()
