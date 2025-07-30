import numpy as np


class Range:
    def __init__(self, start: int, stop: int, step: int):
        """
        Initialize the Range class with start, stop, and step values.

        Args:
            start (int): The starting value of the range.
            stop (int): The stopping value of the range.
            step (int): The step size for the range.
        """
        self.start = start
        self.stop = stop
        self.step = step

    def to_numpy(self) -> np.ndarray:
        """
        Generate an array of evenly spaced values within the specified range.

        Returns:
            np.ndarray: An array of evenly spaced values from start to stop.
        """
        return np.arange(self.start, self.stop, self.step)
