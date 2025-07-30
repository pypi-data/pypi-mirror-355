import os
from pathlib import Path
import requests
from tqdm import tqdm

BASE_URL = "https://github.com/bharadwajakarsh/stads_adaptive_sampler/releases/download/microscope-video-data"
DEFAULT_SAVE_DIR = Path.home() / ".stads_data"

VIDEO_URLS = {
    "dendrites_one.mp4": f"{BASE_URL}/dendrites_one.mp4",
    "nucleation_one.mp4": f"{BASE_URL}/nucleation_one.mp4",
}


def _download_with_progress(url: str, dest_path: Path):
    """
    Download a file from url to dest_path showing a progress bar with requests + tqdm.
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise error if bad status

    total_size_in_bytes = int(response.headers.get('content-length', 0))
    chunk_size = 1024  # 1 KB

    with open(dest_path, 'wb') as file, tqdm(
        total=total_size_in_bytes, unit='B', unit_scale=True, desc=dest_path.name
    ) as progress_bar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                file.write(chunk)
                progress_bar.update(len(chunk))


def download_video(filename: str, force: bool = False) -> Path:
    if filename not in VIDEO_URLS:
        raise ValueError(f"Unknown video: {filename}")

    url = VIDEO_URLS[filename]
    dest_path = DEFAULT_SAVE_DIR / filename
    os.makedirs(DEFAULT_SAVE_DIR, exist_ok=True)

    if dest_path.exists() and not force:
        return dest_path

    print(f"Downloading {filename} from {url}...")
    _download_with_progress(url, dest_path)
    return dest_path
