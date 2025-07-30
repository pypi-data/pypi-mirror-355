from .read_images import get_frames_from_mp4
from .video_downloader import download_video

SIGMA = 4
KERNEL_SIZE = int(SIGMA * 3) + 1

def safe_download(video_name):
    try:
        path = download_video(video_name)
        return path
    except Exception as e:
        print(f"Error downloading {video_name}: {e}")
        return None

# Download and load dendrites video
dendrites_path = safe_download("dendrites_one.mp4")
if dendrites_path:
    DENDRITES_VIDEO = get_frames_from_mp4(str(dendrites_path), 1000)
else:
    DENDRITES_VIDEO = None  # or handle fallback

# Download and load nucleation video
nucleation_path = safe_download("nucleation_one.mp4")
if nucleation_path:
    NUCLEATION_VIDEO = get_frames_from_mp4(str(nucleation_path), 600)
else:
    NUCLEATION_VIDEO = None  # or handle fallback
