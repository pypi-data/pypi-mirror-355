import numpy as np
from .config import DENDRITES_VIDEO, NUCLEATION_VIDEO


class Microscope:

    def __init__(self, groundTruthName):

        self.SUPPORTED_GROUND_TRUTHS = {"dendrites": DENDRITES_VIDEO, "nucleation": NUCLEATION_VIDEO}
        self.groundTruthVideo = self.SUPPORTED_GROUND_TRUTHS[groundTruthName]

    def sample_image(self, yCoords, xCoords, imageShape, frameNumber):

        frame = self.groundTruthVideo[frameNumber]

        if imageShape[0] > frame.shape[0] or imageShape[1] > frame.shape[1]:
            raise ValueError(
                f"imageShape {imageShape} exceeds frame dimensions {frame.shape}"
            )

        frameCropped = frame[:imageShape[0], :imageShape[1]]
        sampledImage = np.zeros(imageShape, dtype=frame.dtype)

        if np.any(yCoords >= imageShape[0]) or np.any(xCoords >= imageShape[1]):
            raise IndexError("Provided coordinates exceed imageShape bounds.")

        sampledImage[yCoords, xCoords] = frameCropped[yCoords, xCoords]
        return sampledImage
