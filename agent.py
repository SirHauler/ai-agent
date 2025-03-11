import os
from mistralai import Mistral
import discord
import json
from youtube.download import download_audio
from transcribe.audio2midi import audio2midi
from transcribe.midi2score import midi2score
from audio.audio_processor import AudioProcessor
MISTRAL_MODEL = "mistral-large-latest"
SYSTEM_PROMPT = """
You are a helpful audio and music assistant. 
You can be provided with a youtube link. 
Your responses will be a list of requests such as: 
[{"type": "MIDI", "youtube_link": <youtube_link>}, {"type": "SHEET_MUSIC", "youtube_link": <youtube_link>}]
where there could be 1 to many items in the list.

Your responses should be in the form of a JSON list. Do not include ``` or ```json at the beginning or end of your response.

You are given a message from a user and you need to check if the user is asking for any of the following:

1. If it is asking for a song to be transcribed to MIDI, add {"type": "MIDI", "youtube_link": <youtube_link>} to the list. 
2. If it is asking for a song to be converted to sheet music, add {"type": "SHEET_MUSIC", "youtube_link": <youtube_link>} to the list.
3. If it is asking for a song to be trimmed with a specific start and end time, add {"type": "TRIM", "youtube_link": <youtube_link>, "start_time": <start_time>, "end_time": <end_time>} to the list. 
If instead it is asking for a specific length set the start time to 0 and the end time to the length of the song. The start and end time should be in terms of seconds.

If none of the above respond add {"type": "none"} to the list.

Lastly before, returning your response, order the list based on the type of request. TRIM should be first if it exists, and the rest can be in any order.
"""


class MistralAgent:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

        self.client = Mistral(api_key=MISTRAL_API_KEY)

        self.audio_processor = AudioProcessor()

        self.audio_path = None

    def handle_message(self, message: str):
        print("Handling message...", message)
        
        json_list = json.loads(message)

        results = []

        for obj in json_list:
            if obj["type"] == "none":
                return "I'm sorry, I don't understand that request."

            if obj["type"] == "MIDI":
                midi_path = self.transcribe_to_midi(obj["youtube_link"])
                results.append(("MIDI: ", midi_path))

            if obj["type"] == "SHEET_MUSIC":
                midi_file_path = self.transcribe_to_midi(obj["youtube_link"])
                music_xml_path = self.convert_to_sheet_music(midi_file_path)
                results.append(("Sheet music: ", music_xml_path))
            
            if obj["type"] == "TRIM":
                audio_path = self.audio_processor.trim_audio(obj["youtube_link"], obj["start_time"], obj["end_time"])
                self.audio_path = audio_path
                results.append(("Trimmed audio: ", audio_path))

        return results
                

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

        # convert the audio to midi
        midi_file_path = audio2midi(audio_file_path)

        # then route to the midi2score model
        return midi_file_path
        

    def convert_to_sheet_music(self, midi_file_path: str):
        # first download the audio from the youtube link
        try:
            music_xml_file_path = midi2score(midi_file_path)
        except Exception as e:
            print("Error converting to sheet music:", e)
            return "I'm sorry, I couldn't convert the MIDI file to sheet music."

        return music_xml_file_path