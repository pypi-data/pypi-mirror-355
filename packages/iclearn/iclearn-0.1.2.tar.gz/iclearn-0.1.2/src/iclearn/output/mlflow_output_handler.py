"""
This module supports output handling via ml flow
"""

import logging
import pickle

import mlflow

from .output_handler import OutputHandler

logger = logging.getLogger(__name__)


class MlFlowOutputHandler(OutputHandler):
    def on_epoch_end(self, metrics):
        super().on_epoch_end(metrics)

        # if self.use_tensorboard:
        # self.tb_writer.add_scalar(msg, scalar, epoch_count)
        self.log_step_results(metrics, self.epoch_count)

    def on_after_infer(self, stage, predictions, metrics):
        super().on_after_infer(stage, predictions, metrics)
        self.log_dict_results(stage, metrics)

    def log_dict_results(self, prefix, results):
        for key, value in results:
            mlflow.log_metric(f"{prefix}_{key}", value)

    def log_step_results(self, results, step: int):
        """
        Log results to file and if present, mlflow
        """
        for outer_key, values in results.items():
            for metric_key, metric_value in values.item():
                mlflow.log_metric(f"{outer_key}_{metric_key}", metric_value, step=step)

    def save_model(self, model):
        """
        Write the model to the given path
        """

        mlflow.pytorch.log_model(
            model.model, artifact_path="pytorch-model", pickle_module=pickle
        )
