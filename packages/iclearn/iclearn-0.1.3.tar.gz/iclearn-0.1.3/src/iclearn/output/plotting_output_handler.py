"""
This module allows for plotting results during a session
"""

from pathlib import Path
import logging
import matplotlib.pyplot as plt
import numpy as np

from .output_handler import OutputHandler

from iclearn.data import Dataloader
from iclearn.model import MetricsCache

logger = logging.getLogger(__name__)


class PlottingOutputHandler(OutputHandler):
    def __init__(
        self,
        result_dir: Path = Path(),
        num_images: int = 20,
        num_columns: int = 4,
        grid_size: tuple = (10, 10),
    ):
        super().__init__(result_dir)

        self.num_images = num_images
        self.num_columns = num_columns
        self.grid_size = grid_size
        self.pre_epoch_image_path = "pre_epochs"
        self.after_infer_image_path = "after_infer"
        self.figure_infos = [
            {
                "key": "iou",
                "label": "IoU",
                "title": "Mean Intersection Over Union",
            },
            {
                "key": "pa",
                "label": "Pixel Accuracy",
                "title": "Pixel Accuracy",
            },
            {
                "key": "loss",
                "label": "Loss",
                "title": "Loss Value",
            },
        ]

    def plot_dataset_sample(self, dataloader: Dataloader, output_path: Path):
        """Plot a sample grid of training images from the dataloader."""

        dataset = dataloader.get_dataset("train")
        num_samples = min(self.num_images, len(dataset))
        num_rows = (num_samples + self.num_columns - 1) // self.num_columns

        fig = plt.figure(figsize=self.grid_size)

        # Loop through the dataset samples and display them
        for idx in range(num_samples):
            data, mask = dataset[idx]
            ax = fig.add_subplot(num_rows, self.num_columns, idx + 1)

            if data.shape[0] == 3:
                plot_data = np.transpose(data, (1, 2, 0))
            else:
                plot_data = data
            ax.imshow(plot_data)
            ax.set_title(f"Sample {idx + 1}")

        # Save the plot
        plot_name = "dataset_sample"
        output_file = output_path / f"{plot_name}.svg"
        plt.savefig(output_file)
        logger.info(f"Plot saved to {output_file}")

    def plot_inference_predictions(
        self, predictions: list, metrics: MetricsCache, output_path: Path
    ):
        """Plot input images alongside their ground truth and predicted masks."""
        num_samples = min(self.num_images, len(predictions))
        num_rows = num_samples
        # input, ground truth, prediction
        num_cols = 3

        figsize = (self.grid_size[0], num_rows)
        fig, axs = plt.subplots(num_rows, num_cols, figsize=figsize)

        # Force axs into 2D so that indexing stays consistent (axs[row, col])
        if num_rows == 1:
            axs = np.expand_dims(axs, 0)

        # For each sample, plot input, ground truth, prediction
        for idx in range(num_samples):
            image, true_mask, pred_mask = predictions[idx]

            axs[idx, 0].imshow(image)
            axs[idx, 0].set_title("Input")
            axs[idx, 0].axis("off")

            axs[idx, 1].imshow(true_mask, cmap="gray")
            axs[idx, 1].set_title("Ground Truth")
            axs[idx, 1].axis("off")

            axs[idx, 2].imshow(pred_mask, cmap="gray")
            axs[idx, 2].set_title("Prediction")
            axs[idx, 2].axis("off")

        # Save the plot
        plot_name = "inference_predictions"
        output_file = output_path / f"{plot_name}.svg"
        plt.tight_layout()
        plt.savefig(output_file)
        logger.info(f"Inference predictions plot saved to {output_file}")

    def plot_metrics(self, metrics: MetricsCache, output_path: Path):
        """Plot individual metric values."""

        for fig_info in self.figure_infos:
            key = fig_info["key"]
            label = fig_info["label"]
            title = fig_info["title"]

            value = metrics.stage_results[key]
            # Create a bar chart for the metric
            fig, ax = plt.subplots()
            ax.bar([label], [value])
            ax.set_title(title)
            ax.set_ylabel(label)

            # Save the plot
            output_file = output_path / f"{key}_metric.svg"
            plt.savefig(output_file)
            logger.info(f"Metric plot for '{key}' saved to {output_file}")

    def on_before_epochs(self, num_epochs: int, dataloader: Dataloader):
        logger.info("Plotting dataset sample")
        output_path = self.result_dir / self.pre_epoch_image_path
        output_path.mkdir(parents=True, exist_ok=True)

        self.plot_dataset_sample(dataloader, output_path)

    def on_after_infer(self, stage: str, predictions: list, metrics: MetricsCache):
        logger.info("Plotting after inference")
        output_path = self.result_dir / self.after_infer_image_path
        output_path.mkdir(parents=True, exist_ok=True)

        self.plot_inference_predictions(predictions, metrics, output_path)
        self.plot_metrics(metrics, output_path)
