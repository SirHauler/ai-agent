import os
from mistralai import Mistral
import discord
import json
from youtube.download import download_audio
from transcribe.audio2midi import audio2midi
from transcribe.midi2score import midi2score, score2pdf
from audio.audio_processor import AudioProcessor
from youtube.search import search_youtube
from prompts import SELECT_SONG_PROMPT
MISTRAL_MODEL = "mistral-large-latest"
SYSTEM_PROMPT = """
You are a helpful audio and music assistant. 
You can be provided with a youtube link. 
Your responses will be a list of requests such as: 
[{"type": "MIDI", "youtube_link": <youtube_link>}, {"type": "SHEET_MUSIC", "youtube_link": <youtube_link>}]
where there could be 1 to many items in the list.

Your responses should be in the form of a JSON list. Do not include ``` or ```json at the beginning or end of your response.

If you are asked to do something, and no audio file, youtube link, or link is referenced, return 'none' for <youtube_link> in the JSON list.

You are given a message from a user and you need to check if the user is asking for any of the following:

1. If it is asking for a song to be transcribed to MIDI, add {"type": "MIDI", "youtube_link": <youtube_link>, "file_path": <file_path>} to the list. If there is no file path, replace <file_path> with "none".
2. If it is asking for a song to be converted to sheet music, add {"type": "SHEET_MUSIC", "youtube_link": <youtube_link>, "file_path": <file_path>} to the list. If there is no file path, replace <file_path> with "none".
3. If it is asking for a song to be trimmed with a specific start and end time, add {"type": "TRIM", "youtube_link": <youtube_link>, "start_time": <start_time>, "end_time": <end_time>} to the list. If there is no file path, replace <file_path> with "none".
If instead it is asking for a specific length set the start time to 0 and the end time to the length of the song. The start and end time should be in terms of seconds.
4. If it asking to search for a song, add {"type": "SEARCH", "query": <query>} to the list. Do not include 
this if the user provides a youtube link.
5. If it is asking to separate the audio into stems, add {"type": "STEM_SEPARATION", "youtube_link": <youtube_link>, "file_path": <file_path>, "instrument": <instrument>} to the list.
By default, the <instrument> should be "vocals" otherwise choose from the following: "drums", "bass", "other", "piano" or "guitar". If no file path is provided, replace <file_path> with "none".

If none of the above apply, respond with {"type": "none"} to the list.

A list of songs is provided to you wrapped in --- at the beginning and end. It is a JSON list of songs.
When deciding what to put in place of the <youtube_link> or <file_path> in the JSON list, consider this list and choose
the song that is most relevant to the user's request.

If a SEARCH is present, all of the <youtube_link>s should be 'none'

Lastly before, returning your response, order the list based on the type of request. 
SEARCH should be first if it exists, then TRIM, and the rest can be in any order.
"""


class MistralAgent:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

        self.client = Mistral(api_key=MISTRAL_API_KEY)

        self.audio_processor = AudioProcessor()

        self.message_history = []

        self.youtube_to_audio_path = {}

        self.last_audio_path = None

        self.songs = []

    async def handle_message(self, message: str, original_message: discord.Message):
        print("Handling message...", message)
        json_list = json.loads(message)

        results = []

        for obj in json_list:
            if obj["type"] == "none":
                return "I'm sorry, I don't understand that request."

            if obj["type"] == "MIDI":
                await original_message.reply(f"Working on transcribing to MIDI...")
                audio_path = self.get_cached_audio_path(obj["youtube_link"], obj["file_path"])
                midi_file_path = self.transcribe_to_midi(obj["youtube_link"], audio_path)
                self.songs.append({"youtube_link": obj["youtube_link"], "file_path": midi_file_path, "name": ""})
                results.append(("MIDI: ", midi_file_path))

            if obj["type"] == "SHEET_MUSIC":
                await original_message.reply(f"Working on converting to sheet music...this could take ~1 minute...")
                audio_path = self.get_cached_audio_path(obj["youtube_link"], obj["file_path"])
                midi_file_path = self.transcribe_to_midi(obj["youtube_link"], audio_path)
                music_xml_path = self.convert_to_sheet_music(midi_file_path)
                # pdf_file_path = score2pdf(music_xml_path)
                # results.append(("PDF of sheet music: ", pdf_file_path))
                self.songs.append({"youtube_link": obj["youtube_link"], "file_path": music_xml_path, "name": ""})
                results.append(("Editable sheet music: ", music_xml_path))
            
            if obj["type"] == "TRIM":
                await original_message.reply(f"Working on trimming audio...")
                audio_path = self.get_cached_audio_path(obj["youtube_link"], "none")
                audio_path = self.audio_processor.trim_audio(obj["youtube_link"], obj["start_time"], obj["end_time"], audio_path)
                self.youtube_to_audio_path[obj["youtube_link"]] = audio_path
                self.last_audio_path = audio_path
                self.songs.append({"youtube_link": obj["youtube_link"], "file_path": audio_path, "name": ""})
                results.append(("Trimmed audio: ", audio_path))

            if obj["type"] == "SEARCH":
                search_results = search_youtube(obj["query"])
                if 'url' in search_results:
                    self.last_audio_path = download_audio(search_results['url'])
                    self.youtube_to_audio_path[search_results['url']] = self.last_audio_path
                print("Search results: ", search_results)
                self.songs.append({"youtube_link": search_results['url'], "file_path": None, "name": obj["query"]})
                await original_message.reply(f"Working on searching for {obj['query']}...")
                results.append(("Search results: ", search_results))

            if obj["type"] == "STEM_SEPARATION":
                await original_message.reply(f"Working on separating the audio into {obj['instrument']}...(takes ~30 seconds)")
                audio_path = self.get_cached_audio_path(obj["youtube_link"], obj["file_path"])
                audio_path = self.audio_processor.stem_seperation(obj["youtube_link"], audio_path, obj["instrument"])

                self.youtube_to_audio_path[obj["youtube_link"]] = audio_path
                self.last_audio_path = audio_path

                self.songs.append({"youtube_link": obj["youtube_link"], "file_path": audio_path, "name": obj["instrument"]})
                results.append((f"Stem separation for {obj['instrument']}: ", audio_path))

        return results
                

    async def run(self, message: discord.Message, message_history: str):
        # The simplest form of an agent
        # Send the message's content to Mistral's API and return Mistral's response

        songs_string = json.dumps(self.songs)

        # put --- at the beginning and end of the songs_string
        songs_string = "---" + songs_string + "---"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message_history},
            {"role": "user", "content": songs_string},
            {"role": "user", "content": message.content},
        ]

        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )

        # also ask the LLM what is the most relevant song to the user's request
        # and return that song



        return await self.handle_message(response.choices[0].message.content, message)

    def transcribe_to_midi(self, youtube_link: str, audio_path: str):
        # first download the audio from the youtube link
        try:
            audio_file_path = download_audio(youtube_link) if audio_path is None else audio_path
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
    
    def get_cached_audio_path(self, youtube_link: str, file_path: str):
        if file_path == "none":
            if youtube_link in self.youtube_to_audio_path:
                return self.youtube_to_audio_path[youtube_link]
            elif youtube_link == "none":
                return self.last_audio_path
            else:
                return None
        else:
            return file_path
