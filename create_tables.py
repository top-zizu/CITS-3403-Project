# pip install yt-dlp
import yt_dlp

CHANNEL_URL = "https://www.youtube.com/@KaiStoneYoutube/videos"

def seconds_to_hms(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"

ydl_opts = {
    "quiet": True,
    "extract_flat": False,
    "ignoreerrors": True,
    "playlistend": None,
}

total_seconds = 0
video_count = 0

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(CHANNEL_URL, download=False)

    for entry in info.get("entries", []):
        if not entry:
            continue

        duration = entry.get("duration")
        title = entry.get("title", "Untitled")

        if duration:
            total_seconds += duration
            video_count += 1
            print(f"{seconds_to_hms(duration):>12}  {title}")

print("\n---")
print(f"Videos counted: {video_count}")
print(f"Total runtime: {seconds_to_hms(total_seconds)}")
print(f"Total minutes: {total_seconds / 60:.2f}")
print(f"Total hours: {total_seconds / 3600:.2f}")