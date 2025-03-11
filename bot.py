import os
import discord
import logging

from discord.ext import commands
from dotenv import load_dotenv
from agent import MistralAgent

PREFIX = "!"

# Setup logging
logger = logging.getLogger("discord")

# Load the environment variables
load_dotenv()

# Create the bot with all intents
# The message content and members intent must be enabled in the Discord Developer Portal for the bot to work.
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Import the Mistral agent from the agent.py file
agent = MistralAgent()


# Get the token from the environment variables
token = os.getenv("DISCORD_TOKEN")


@bot.event
async def on_ready():
    """
    Called when the client is done preparing the data received from Discord.
    Prints message on terminal when bot successfully connects to discord.

    https://discordpy.readthedocs.io/en/latest/api.html#discord.on_ready
    """
    logger.info(f"{bot.user} has connected to Discord!")

    # Send a welcome message to the channel
    await bot.get_channel(1348019812374417491).send("Hello! I'm the Music Bot. I can help you transcribe music from YouTube videos to MIDI, sheet music, and more. Type `!help` to see the available commands.")
        


@bot.event
async def on_message(message: discord.Message):
    """
    Called when a message is sent in any channel the bot can see.

    https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message
    """
    # Don't delete this line! It's necessary for the bot to process commands.
    await bot.process_commands(message)

    # Ignore messages from self or other bots to prevent infinite loops.
    if message.author.bot or message.content.startswith("!"):
        return

    # Process the message with the agent you wrote
    # Open up the agent.py file to customize the agent
    logger.info(f"Processing message from {message.author}: {message.content}")

    # reply to the user with an initial message
    await message.reply("Got it! Give me a moment to work on your requests...")

    response = await agent.run(message) # a list of tuples ("message", "file_path")

    for res, file_path in response:
        if file_path and (file_path.endswith(".mp3") or file_path.endswith(".mid") or file_path.endswith(".musicxml")):
            try: 
                print(f"Sending file: {file_path}, with message: {res}")
                # file_path = os.path.join(os.getcwd(), file_path)
                await message.reply(res, file=discord.File(file_path))
            except Exception as e:
                logger.error(f"Error sending file: {e}")
        else:
            # Send the response back to the channel
            await message.reply(res)


# Commands


# This example command is here to show you how to add commands to the bot.
# Run !ping with any number of arguments to see the command in action.
# Feel free to delete this if your project will not need commands.
@bot.command(name="ping", help="Pings the bot.")
async def ping(ctx, *, arg=None):
    if arg is None:
        await ctx.send("Pong!")
    else:
        await ctx.send(f"Pong! Your argument was {arg}")

@bot.command(name="help", help="Shows the list of available commands and features")
async def help_command(ctx):
    help_text = """
**🎵 Music Transcription Bot Help 🎵**

This bot can help you with music transcription and audio processing tasks.

**Commands:**
`!help` - Shows this help message
`!ping` - Check if the bot is responsive

**Features:**
1. **MIDI Conversion**
   Simply share a YouTube link and ask for MIDI conversion
   Example: "Can you convert this to MIDI: [youtube link]"

2. **Sheet Music Generation**
   Share a YouTube link to get sheet music
   Example: "Create sheet music for this: [youtube link]"

3. **Audio Trimming**
   Trim audio from YouTube videos by specifying start and end times
   Example: "Trim this video from 1:30 to 2:45: [youtube link]"

You can combine multiple requests in a single message!
"""
    await ctx.send(help_text)

# Start the bot, connecting it to the gateway
bot.run(token)
