import discord
from discord.ext import commands
import sys
import unicodedata


# this value obtained using:
# import unicodedata
# unicodedata.name('▶')
# where ▶ was obtained by escaping the first colon of the emoji text code, and
# copy-pasting the resultant output.
UNICODE_FORWARD_ARROW = "\N{BLACK RIGHT-POINTING TRIANGLE}"


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


@bot.command()
async def echo(context: commands.Context, *args):
    print(context)
    print(args)
    await context.send("args: " + str(args) + "\n", embed="test")


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
