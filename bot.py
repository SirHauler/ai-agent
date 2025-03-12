import os
import discord
import logging
import subprocess
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

    MESSAGE = """
    🎵 Hello! I'm the Songscription Bot! 🤖 I'm here to help you with all your music transcription needs! 

    I can:
    🎹 Convert YouTube videos to MIDI files
    📝 Generate sheet music from videos (You can upload a video)
    ✂️ Trim audio clips
    🔍 Search for songs on YouTube
    🎼 Separate audio into stems

    Example Ask: 

    "Create sheet music for this song: https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    OR 
    "Search for a performance of Fur Elise and provide me sheet music"
    OR 
    "Trim this audio from 1:30 to 2:45: https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    OR
    "Separate this audio and give me the vocals"


    Type `!help` to see all available commands!

    Powered by https://songscription.ai for professional-grade MIDI and sheet music generation 🎼
    (songscription's models are custom trained by myself and a few friends!)
    """

    # Send a welcome message to the channel
    await bot.get_channel(1348019812374417491) \
        .send(MESSAGE)
        


@bot.event
async def on_message(message: discord.Message):
    """
    Called when a message is sent in any channel the bot can see.

    https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message
    """
    # Don't delete this line! It's necessary for the bot to process commands.
    await bot.process_commands(message)

    message_history = ""

    # Ignore messages from self or other bots to prevent infinite loops.
    if message.author.bot or message.content.startswith("!"):
        return
    
    if message.attachments:
        for attachment in message.attachments:
            file_name = attachment.filename
            file_path = os.path.join(os.getcwd(), 'uploads', file_name)

            if file_name.endswith(".mp4"):
                # convert to mp3
                file_path = os.path.join(os.getcwd(), 'uploads', file_name.replace(".mp4", ".mp3"))
                subprocess.run(["ffmpeg", "-i", attachment.url, file_path])
            else:
                await attachment.save(file_path)

            agent.last_audio_path = file_path
            agent.songs.append({"youtube_link": None,"file_path": file_path, "name": file_name})
        message_history += f"----Uploaded file: {file_name}---\n"
    # Process the message with the agent you wrote
    # Open up the agent.py file to customize the agent
    logger.info(f"Processing message from {message.author}: {message.content}")

    # reply to the user with an initial message
    await message.reply("Got it! Give me a moment to work on your requests...")

    # message_history = []
    # async for msg in message.channel.history(limit=2):
    #     message_history.append(msg.content)


    response = await agent.run(message, message_history) # a list of tuples ("message", "file_path")

    for res, file_path in response:
        if isinstance(file_path, dict): 
            # convert the dict to a string
            reply = res + "\n" + file_path["url"]
            await message.reply(reply)
        elif file_path and (file_path.endswith(".mp3") or file_path.endswith(".wav") or file_path.endswith(".mid") or file_path.endswith(".musicxml")):
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
        Simply share a YouTube link and ask for MIDI conversion or upload an audio file to get MIDI
        Example: "Can you convert this to MIDI: [youtube link]"

        2. **Sheet Music Generation**
        Share a YouTube link to get sheet music or upload an audio file to get sheet music
        Example: "Create sheet music for this: [youtube link]"

        3. **Audio Trimming**
        Trim audio from YouTube videos by specifying start and end times
        Example: "Trim this video from 1:30 to 2:45: [youtube link]"

        You can combine multiple requests in a single message!
"""
    await ctx.send(help_text)

# Start the bot, connecting it to the gateway
bot.run(token)
