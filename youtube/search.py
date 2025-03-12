import yt_dlp

def search_youtube(query: str, max_results: int = 10, max_duration: int = 300):
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'default_search': 'ytsearch' + str(max_results),
        'skip_download': True,
        'extract_flat': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
        
        if 'entries' not in search_results:
            return None  # No results found
        
        for video in search_results['entries']:
            if video and video.get('duration') and video['duration'] <= max_duration:
                return {
                    "title": video["title"],
                    "url": video["url"],
                    "duration": video["duration"]
                }
