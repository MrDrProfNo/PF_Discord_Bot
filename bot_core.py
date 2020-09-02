import discord
from discord.ext import commands
import sys

bot = commands.Bot(command_prefix='!')

bot_token = sys.argv[1]

print("Using bot_token: " + bot_token)

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
        await context.send("args received but not yet processed")

    message_embed = discord.Embed()

    message_embed.title = ":tools: CREATE GAME"

    message_embed.description = \
        "React below :arrow_forward: and we'll start setting up your game\nMake sure your DMs are on"

    message_embed.set_thumbnail(
        url="https://i.imgur.com/J6wmi3U.png%22%7D,%22color%22:4886754%7D"
    )

    await context.send(embed=message_embed)


bot.run(bot_token)
