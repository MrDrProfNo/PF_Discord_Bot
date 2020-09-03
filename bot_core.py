import discord
from discord.ext import commands
import sys
from unicode_constants import UNICODE_FORWARD_ARROW, UNICODE_1, \
    UNICODE_2, UNICODE_3, UNICODE_4, UNICODE_5


bot = commands.Bot(command_prefix='!')


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
