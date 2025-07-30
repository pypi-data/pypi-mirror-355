import pathlib

import pyarrow.dataset as ds
from matplotlib import pyplot as plt

from .inference import Inference


class ImageGenerator:
    def __init__(
        self,
        encoder: Inference,
        decoder: Inference,
        data_directory: str,
        output_folder: str = "output",
        batch_size: int = 256,
        figsize_in_pixel: tuple[int, int] = (1600, 1200),
        dpi: int = 200,
        legend: bool = True,
    ):
        """Generates images of data.

        Args:
            encoder (Inference): Function that encodes the data.
            decoder (Inference): Function that decodes the data.
            data_directory (str): The directory containing the data.
            output_folder (str, optional): The output folder. Defaults to "output".
            batch_size (int, optional): The batch size to use. Defaults to 256.
            figsize_in_pixel (tuple[int, int], optional): Size of the figure in pixels (w, h).
            Defaults to (800, 600).
            dpi (int, optional): Dots per inch. Defaults to 200.
            legend (bool, optional): Whether to show the legend. Defaults to True.
        """

        self.encoder = encoder
        self.decoder = decoder
        self.data_directory = data_directory
        self.output_folder = output_folder
        self.batch_size = batch_size
        self.figsize = (
            float(figsize_in_pixel[0]) / dpi,
            float(figsize_in_pixel[1]) / dpi,
        )
        self.dpi = dpi
        self.legend = legend

        pathlib.Path(self.output_folder).mkdir(parents=True, exist_ok=True)
        self.dataset = ds.dataset(self.data_directory, format="parquet")

        # Reshape the data if the shape is stored in the metadata.
        metadata_shape = b"flux_shape"
        self.shape = None
        if self.dataset.schema.metadata and metadata_shape in self.dataset.schema.metadata:
            shape_string = self.dataset.schema.metadata[metadata_shape].decode("utf8")
            shape = shape_string.replace("(", "").replace(")", "").split(",")
            self.shape = tuple(map(int, shape))

    def __call__(self):
        for batch in self.dataset.to_batches(batch_size=self.batch_size):
            flux = batch["flux"].flatten().to_numpy()
            if self.shape:
                flux = flux.reshape(-1, *self.shape)

            if flux.shape[0] != 256:
                print(f"Skipping batch with shape {flux.shape}")
                continue

            # Normalize
            # norm = lambda x: (x - x.min()) / (x.max() - x.min())
            # norm(flux)
            flux = flux.copy()
            for i, x in enumerate(flux):
                flux[i] = (x - x.min()) / (x.max() - x.min())

            latent_position = self.encoder(flux)
            recon = self.decoder(latent_position)

            for idx, (f, r) in enumerate(zip(flux, recon)):
                plt.figure(figsize=self.figsize, dpi=self.dpi)
                plt.plot(f[0], label="Original")
                plt.plot(r[0], label="Reconstructed")
                if self.legend:
                    plt.legend(loc="upper right")
                plt.savefig(f"{self.output_folder}/{batch['source_id'][idx]}.jpg")
                plt.close()
