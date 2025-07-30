"""
This module supports output handling
"""

import logging
from pathlib import Path
import time
import os

from iclearn.data import Dataloader
from iclearn.model import MetricsCache, Model

logger = logging.getLogger(__name__)


class OutputHandler:
    """
    Base class to support generating output at set times
    during the training and inference process.
    """

    def __init__(self, result_dir: Path = Path()) -> None:
        self.result_dir = result_dir

        self.num_epochs: int = 0
        self.epoch_count: int = 0

        self.num_batches: int = 0
        self.batch_count: int = 0

        self.start_time: int = 0
        self.epoch_start_time: int = 0

        self.current_stage: str = ""

    def get_elapsed_time(self, start_time=None):
        """
        Function to measure elapsed time
        """

        if start_time:
            return time.time() - start_time
        return time.time()

    def on_before_epochs(self, num_epochs: int, _: Dataloader):
        self.num_epochs = num_epochs
        self.start_time = self.get_elapsed_time()
        self.epoch_count = 0

        save_path = self.result_dir / "results"
        os.makedirs(save_path, exist_ok=True)

    def on_after_epochs(self):
        self.epoch_count = 0
        self.batch_count = 0

    def on_epoch_start(self, num_batches: int):
        self.epoch_count += 1
        self.batch_count = 0
        self.epoch_start_time = self.get_elapsed_time()
        self.num_batches = num_batches
        self.current_stage = "train"

    def on_epoch_end(self, _metrics: MetricsCache):
        self.current_stage = ""

    def on_batch_start(self):
        self.batch_count += 1

    def on_batch_end(self, _metrics: MetricsCache):
        pass

    def on_validation_start(self, num_batches: int):
        self.batch_count = 0
        self.num_batches = num_batches

    def on_before_infer(self):
        self.batch_count = 0

    def on_after_infer(self, _stage, _predictions, _metrics: MetricsCache):
        pass

    def save_model(self, _model: Model):
        """
        Write the model to the given path
        """
