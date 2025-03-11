import os
from mistralai import Mistral
import discord

MISTRAL_MODEL = "mistral-large-latest"
SYSTEM_PROMPT = """
Is this message asking for a youtube link to be transcribed to MIDI or to be converted to sheet music?

If it is asking for a song to be transcribed to MIDI, respond with {"type": "MIDI", "youtube_link": <youtube_link>}.
If it is asking for a song to be converted to sheet music, respond with {"type": "SHEET_MUSIC", "youtube_link": <youtube_link>}.

Otherwise, respond with {"type": "none"}.
"""


class MistralAgent:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

        self.client = Mistral(api_key=MISTRAL_API_KEY)

    async def run(self, message: discord.Message):
        # The simplest form of an agent
        # Send the message's content to Mistral's API and return Mistral's response

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message.content},
        ]

        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )

        return response.choices[0].message.content
