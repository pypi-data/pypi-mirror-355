"""
This module supports the generation of tabular output
"""

import logging
from pathlib import Path
import csv

from iclearn.model import MetricsCache
from .output_handler import OutputHandler

logger = logging.getLogger(__name__)


class TabularMetricsOutputHandler(OutputHandler):
    """
    Outputs loss/time results in a CSV format.
    """

    def __init__(self, result_dir: Path, filename: str = "tabular_metrics.csv"):
        """
        Create the lists that store the CSV information.
        """
        super().__init__(result_dir)

        # Path to the .csv
        self.path_to_file = result_dir / filename

        # Stores the information
        self.epoch_list: list = []
        self.epoch_loss: list = []
        self.epoch_time: list = []

        # For the batch loss
        self.batch_labels: list = []
        self.batch_loss: list = []

    def on_epoch_start(self, num_batches):
        """
        Iterates epoch count.
        Creates the batch labels as required on first epoch.
        """
        super().on_epoch_start(num_batches)
        self.epoch_list.append(self.epoch_count)
        self.epoch_start_time = self.get_elapsed_time()

        if self.epoch_count == 1:
            for i in range(num_batches):
                self.batch_labels.append(f"Batch {i} Loss")

    def on_batch_end(self, metrics: MetricsCache):
        """
        Records each batch's loss.
        """
        super().on_batch_end(metrics)

        loss = metrics.batch_last_results["loss"]
        self.batch_loss.append(float(loss))

    def on_epoch_end(self, metrics: MetricsCache):
        """
        Records time taken.
        Records overall epoch training loss.
        """
        super().on_epoch_end(metrics)

        self.epoch_end_time = self.get_elapsed_time(self.epoch_start_time)
        self.epoch_time.append(self.epoch_end_time)
        self.epoch_loss.append(
            metrics.stage_results["train"]["loss"][self.epoch_count - 1]
        )

    def on_after_epochs(self):
        """
        Creates CSV at the end of training.
        """
        header = ["Epoch", "Average Epoch Loss", "Time Taken (i/s)"]
        header[1:1] = self.batch_labels

        num_batches = len(self.batch_labels)
        csv_matrix = self.divide_batch_loss_list(num_batches)

        with open(self.path_to_file.__str__(), "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(csv_matrix)

    def divide_batch_loss_list(self, num_batches: int):
        """
        Creates the overall CSV file structure.
        Uses the stored information over the training session.
        """
        csv_matrix: list = []

        for i in range(self.num_epochs):
            # Frist column: Epoch
            temp_csv_matrix = [self.epoch_list[i]]
            for j in range(0, num_batches):
                batch = self.batch_loss[(i * num_batches) + (j)]
                # Append each batch's loss
                temp_csv_matrix.append(batch)
            # Add the epoch loss column
            temp_csv_matrix.append(self.epoch_loss[i])
            # Add the time taken column
            temp_csv_matrix.append(self.epoch_time[i])

            # Append that entire row's information
            csv_matrix.append(temp_csv_matrix)

        return csv_matrix
