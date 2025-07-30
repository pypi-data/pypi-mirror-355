import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm

# Constants
BASE_URL = "https://github.com/bharadwajakarsh/stads_adaptive_sampler/releases/download/microscope-video-data"
DEFAULT_SAVE_DIR = Path.home() / ".stads_data"

VIDEO_URLS = {
    "dendrites_one.mp4": f"{BASE_URL}/dendrites_one.mp4",
    "nucleation_one.mp4": f"{BASE_URL}/nucleation_one.mp4",
}

# Secure token loader
def get_github_token():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.stderr.write(
            "[ERROR] Environment variable GITHUB_TOKEN is not set.\n"
            "Please set it before running:\n"
            "  export GITHUB_TOKEN='your_token_here'\n"
        )
        sys.exit(1)
    return token

# Authenticated downloader with progress bar
def download_with_auth(url: str, dest_path: Path):
    token = get_github_token()
    headers = {"Authorization": f"token {token}"}

    response = requests.get(url, headers=headers, stream=True)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        sys.stderr.write(f"[ERROR] Failed to download {url}:\n  {e}\n")
        sys.exit(1)

    total = int(response.headers.get("content-length", 0))
    chunk_size = 1024 * 1024  # 1 MB

    with open(dest_path, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, desc=dest_path.name
    ) as pbar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

# Public function for use in package
def download_video(filename: str, force: bool = False) -> Path:
    if filename not in VIDEO_URLS:
        raise ValueError(f"Unknown video: {filename}")

    url = VIDEO_URLS[filename]
    dest_path = DEFAULT_SAVE_DIR / filename
    os.makedirs(DEFAULT_SAVE_DIR, exist_ok=True)

    if dest_path.exists() and not force:
        return dest_path

    print(f"[INFO] Downloading {filename} from {url} ...")
    download_with_auth(url, dest_path)
    return dest_path
