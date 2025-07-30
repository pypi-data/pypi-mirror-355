import importlib.resources
from .read_images import get_frames_from_mp4


# Now load the reference frames
SIGMA = 4
KERNEL_SIZE = int(SIGMA * 3) + 1

with importlib.resources.path("stads.ground_truth", "dendrites_one.mp4") as video_path:
    DENDRITES_VIDEO = get_frames_from_mp4(str(video_path), 1000)
with importlib.resources.path("stads.ground_truth", "nucleation_one.mp4") as video_path:
    NUCLEATION_VIDEO = get_frames_from_mp4(str(video_path), 1000)
