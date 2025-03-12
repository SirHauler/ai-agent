from pydub import AudioSegment
from youtube.download import download_audio
import os
import demucs.separate

class AudioProcessor:
    def __init__(self):
        pass

    def trim_audio(self, youtube_link: str, start_time: int, end_time: int, audio_path = None):
        if audio_path is None:
            audio_file_path = download_audio(youtube_link)
        else:
            audio_file_path = audio_path

        audio_file_name = os.path.basename(audio_file_path)
        output_file_path = os.path.join(os.getcwd(), "uploads", f"{start_time}_{end_time}_{audio_file_name}")
        audio = AudioSegment.from_file(audio_file_path)
        trimmed_audio = audio[start_time * 1000 : end_time * 1000]
        trimmed_audio.export(output_file_path, format="mp3")
        return output_file_path
    
    def stem_seperation(self, youtube_link: str, audio_path: str, instrument: str):
        if audio_path is None:
            audio_file_path = download_audio(youtube_link)
        else:
            audio_file_path = audio_path

    
        # run through stem seperation model demucs
        demucs.separate.main(["--mp3", "-n", "htdemucs_6s", audio_file_path])

        # get the output file path
        base_name = os.path.splitext(os.path.basename(audio_file_path))[0]
        output_file_path = os.path.join(os.getcwd(), "separated", "htdemucs_6s", base_name, f"{instrument}.mp3")

        # return the output file path
        return output_file_path

