"""
This module supports calculating a storing metrics given a model
prediction and ground truth.
"""

from typing import Any, Callable

from .metrics_cache import MetricsCache


class Metrics:
    """
    Holds calculators and a cache for metrics calculated during model training
    """

    def __init__(
        self, loss_func: Any, num_classes: int = 0, sync_func: Callable | None = None
    ) -> None:
        """
        :param Any loss_func: A function to return a loss item
        :param int num_classes: Number of classes in classification problems
        :param Callable | None sync_func: Function to sync results
        in a distributed setting
        """

        self.metric_funcs: dict = {}
        self.num_classes = num_classes
        self.loss_func = loss_func
        self.loss_item = None
        self.cache = MetricsCache(sync_func)

    def reset(self, sync_func: Callable | None = None):
        self.cache = MetricsCache(sync_func)

    def calculate(self, prediction, ground_truth):
        """
        Given the prediction and ground truth calculate
        the metrics and cache them
        """

        if self.loss_item is not None:
            self.cache.on_batch_item("loss", self.loss_item)

        for key, calc_func in self.metric_funcs.items():
            self.cache.on_batch_item(key, calc_func(prediction, ground_truth))

    def calculate_loss(self, pred, gt):
        """
        Calculate the loss using the loss function
        and provided prediction and ground truth.

        This method should also set the loss item
        member.
        """
        loss = self.loss_func(pred, gt)
        self.loss_item = loss.item()
        return loss

    def on_before_epochs(self):
        """
        Method is called before any epochs
        """
        self.cache.on_before_epochs()

    def on_epoch_start(self):
        """
        Method is called at the start on an epoch
        """
        self.cache.on_epoch_start()

    def on_epoch_end(self):
        """
        Method is called at the end of an epoch
        """
        self.cache.on_epoch_end()

    def on_batch_start(self):
        self.cache.on_batch_start()

    def on_batch_end(self, prediction, ground_truth):
        """
        Method is called at the end of a batch
        """
        self.calculate(prediction, ground_truth)
        self.cache.on_batch_end()

    def on_before_infer(self):
        self.cache.on_before_infer()

    def on_validation_start(self):
        self.cache.on_validation_start()

    def get_stage_result(self, key: str):
        return self.cache.stage_results[self.cache.active_stage][key]
