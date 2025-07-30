from abc import ABC, abstractmethod

from hipster.html_generator import HTMLGenerator


class Task(ABC):
    def __init__(self, name, root_path: str = "", title: str = "") -> None:
        """Base class for all tasks.
        Args:
            name (str): The name of the task.
        """
        super().__init__()
        self.name = name
        self.root_path = root_path
        self.title = title

    @abstractmethod
    def execute(self) -> None:
        """Execute the task."""

    @abstractmethod
    def register(self, html_generator: HTMLGenerator) -> None:
        """Register the task with the HTML generator.
        Args:
            html_generator (HTMLGenerator): The HTML generator instance.
        """
