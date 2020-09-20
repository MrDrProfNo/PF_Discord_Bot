import discord
from discord.ext import commands
import sys
import unicodedata
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine


# this value obtained using:
# import unicodedata
# unicodedata.name('▶')
# where ▶ was obtained by escaping the first colon of the emoji text code, and
# copy-pasting the resultant output.
UNICODE_FORWARD_ARROW = "\N{BLACK RIGHT-POINTING TRIANGLE}"

bot = commands.Bot(command_prefix='!')
Base = declarative_base()
engine = create_engine('sqlite:///:memory:', echo=True)
Session = sessionmaker(bind=engine)
session = Session()


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

    # don't send to bots.
    if not user.bot:
        print("sent message to:", user.name)
        await user.send(content="You reacted to me with {0}!".format(reaction))


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    print("RAW reaction received")
    user = bot.get_user(payload.user_id)
    print("From user:", user.name, "(" + str(payload.user_id) + ")")
    print("")
    emoji = payload.emoji
    if not user.bot:
        print("sent message to:", user.name)
        await user.send(
            content="You reacted to an *old* message of mine with {0}"
            .format(str(emoji))
        )


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
