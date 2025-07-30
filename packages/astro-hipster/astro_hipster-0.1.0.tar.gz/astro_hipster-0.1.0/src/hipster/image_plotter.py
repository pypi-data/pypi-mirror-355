import numpy as np


class ImagePlotter:
    def __init__(
        self,
        flip: bool = False,
    ):
        """Plot a 2D image

        Args:
            flip (bool, optional): Flip the image. Defaults to False.
        """
        self.figsize_in_pixel = None
        self.flip = flip

    def __call__(self, data: np.ndarray) -> np.ndarray:
        # Store the size of the image for the HiPS property file
        self.figsize_in_pixel = data.shape[1]

        data = np.clip(data.transpose(1, 2, 0), 0, 1) * 255
        data = data.astype(np.uint8)

        if self.flip:
            data = np.fliplr(data)

        return data
