import sys
from .read_images import get_frames_from_mp4
from .video_downloader import download_video

SIGMA = 4
KERNEL_SIZE = int(SIGMA * 3) + 1

def safe_download(video_name: str):
    try:
        path = download_video(video_name)
        return path
    except Exception as e:
        print(f"[ERROR] Failed to download {video_name}: {e}", file=sys.stderr)
        return None

# Download and load dendrites video
dendrites_path = safe_download("dendrites_one.mp4")
if dendrites_path:
    DENDRITES_VIDEO = get_frames_from_mp4(str(dendrites_path), 1000)
else:
    DENDRITES_VIDEO = None
    print("[WARN] DENDRITES_VIDEO is not available.", file=sys.stderr)

# Download and load nucleation video
nucleation_path = safe_download("nucleation_one.mp4")
if nucleation_path:
    NUCLEATION_VIDEO = get_frames_from_mp4(str(nucleation_path), 600)
else:
    NUCLEATION_VIDEO = None
    print("[WARN] NUCLEATION_VIDEO is not available.", file=sys.stderr)

# Optional: raise if both fail
if DENDRITES_VIDEO is None and NUCLEATION_VIDEO is None:
    raise RuntimeError("Neither video could be downloaded — check GITHUB_TOKEN or internet access.")
