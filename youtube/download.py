import yt_dlp

def download_audio(video_url):
    # Options for downloading best audio and converting it to MP3
    ydl_opts = {
        'format': 'bestaudio/best',  # Select the best available audio quality
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # Use ffmpeg to extract audio
            'preferredcodec': 'mp3',       # Convert to MP3 format
            'preferredquality': '192',     # Set the audio quality (in kbps)
        }],
        'outtmpl': 'uploads/%(id)s.%(ext)s',    # Output filename template: video title with appropriate extension
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url)
        audio_file_path = 'uploads/' + info_dict.get('id', None) + '.mp3'
        
    return audio_file_path
