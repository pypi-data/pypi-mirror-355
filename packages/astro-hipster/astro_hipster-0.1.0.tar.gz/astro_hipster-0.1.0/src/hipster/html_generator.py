import os
from dataclasses import dataclass

from jinja2 import Environment, FileSystemLoader


class HTMLGenerator:
    def __init__(
        self,
        root_path: str,
        url: str = "http://localhost:8083",
        title: str = "HiPSter",
        aladin_lite_version: str = "latest",
    ) -> None:
        """
        Initialize the HTMLGenerator with the URL and title.
        Args:
            url (str): The URL of the HiPS server.
            title (str): The title of the HiPS data.
            aladin_lite_version (str): The version of Aladin Lite to use.
        """
        self.root_path = root_path
        self.url = url
        self.title = title
        self._aladin_lite_version = aladin_lite_version
        self._image_layers = []
        self._votables = []
        self._catalogs = []

        self._environment = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

    @dataclass
    class ImageLayer:
        hips_id: str
        hips_name: str
        hips_url: str
        hips_max_order: int

    def add_image_layer(self, image_layer: ImageLayer) -> None:
        """Add an image layer to the HTML page.
        Args:
            layer (str): The image layer to add.
        """
        self._image_layers.append(image_layer)

    @dataclass
    class VOTable:
        url: str
        name: str
        color: str
        shape: str
        size: int

    def add_votable(self, votable: VOTable) -> None:
        """Add a VOTable layer to the HTML page.
        Args:
            layer (str): The VOTable layer to add.
        """
        self._votables.append(votable)

    def generate(self) -> None:
        """Generate the HTML page for the HiPS data."""
        print("Generating HTML page...")

        template = self._environment.get_template("index.html")
        html = template.render(
            title=self.title,
            image_layers=self._image_layers,
            votables=self._votables,
            catalogs=self._catalogs,
            aladin_lite_version=self._aladin_lite_version,
        )
        os.makedirs(self.root_path, exist_ok=True)
        with open(os.path.join(self.root_path, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
