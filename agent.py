import os
from mistralai import Mistral
import discord
import json
from youtube.download import download_audio
import os 

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

    def handle_message(self, message: str):
        print("Handling message...", message)
        obj = json.loads(message)

        if obj["type"] == "none":
            return "I'm sorry, I don't understand that request."

        if obj["type"] == "MIDI":
            return self.transcribe_to_midi(obj["youtube_link"])

        if obj["type"] == "SHEET_MUSIC":
            return self.convert_to_sheet_music(obj["youtube_link"])

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

        return self.handle_message(response.choices[0].message.content)

    def transcribe_to_midi(self, youtube_link: str):
        # first download the audio from the youtube link
        try:
            audio_file_path = download_audio(youtube_link)
        except Exception as e:
            print("Error downloading audio:", e)
            return "I'm sorry, I couldn't download the audio from the youtube link."

        print("Transcribing to MIDI...", audio_file_path)

        # basename of the audio file
        audio_filename = os.path.basename(audio_file_path)
        print("Audio filename:", audio_filename)

        # then route to the midi2score model
        return audio_file_path
        

    def convert_to_sheet_music(self, youtube_link: str):
        # first download the audio from the youtube link
        download_audio(youtube_link)

        # then convert the audio to sheet music
        # use the openai api to convert the audio to sheet music
        # return the sheet music
