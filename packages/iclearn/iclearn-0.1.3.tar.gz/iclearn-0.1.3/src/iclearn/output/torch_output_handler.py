"""
This module supports output handling
"""

import logging
from pathlib import Path

import torch
from torch.utils.tensorboard import SummaryWriter

from .output_handler import OutputHandler

logger = logging.getLogger(__name__)


class TorchOutputHandler(OutputHandler):
    def __init__(
        self,
        result_dir: Path,
    ) -> None:
        super().__init__(result_dir)

        self.writer = SummaryWriter(result_dir / "tensorboard")

    def on_epoch_end(self, metrics):
        super().on_epoch_end(metrics)

        for key, value in metrics.items():
            self.writer.add_scalar(key, value, self.epoch_count)

    def save_model(self, model):
        """
        Write the model to the given path
        """

        torch.save(
            model.model,
            f"{self.result_dir}/best_model.pt",
        )
