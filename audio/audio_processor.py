from pydub import AudioSegment
from youtube.download import download_audio
import os 

class AudioProcessor:
    def __init__(self):
        pass

    def trim_audio(self, youtube_link: str, start_time: int, end_time: int):
        audio_file_path = download_audio(youtube_link)
        audio_file_name = os.path.basename(audio_file_path)
        output_file_path = os.path.join(os.getcwd(), "uploads", f"{start_time}_{end_time}_{audio_file_name}")
        audio = AudioSegment.from_file(audio_file_path)
        trimmed_audio = audio[start_time * 1000 : end_time * 1000]
        trimmed_audio.export(output_file_path, format="mp3")
        return output_file_path
