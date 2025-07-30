import logging

from .machine_learning_model import StoppingCriterion as StoppingCriterionModel
from .metrics_cache import MetricsCache


logger = logging.getLogger(__name__)


class StoppingCriterion:
    """
    This class can be used to terminate a machine learning run
    either after a batch or an epoch
    """

    def __init__(self) -> None:
        self.batch_count: int = 0

    def on_epoch_start(self):
        self.batch_count = 0

    def on_validation_start(self):
        self.batch_count = 0

    def on_before_infer(self):
        self.batch_count = 0

    def on_batch_start(self):
        pass

    def on_epoch_end(self, _: MetricsCache) -> tuple[bool, bool]:
        return False, False

    def on_batch_end(self) -> bool:
        self.batch_count += 1
        return False


class TrainingStartStoppingCriterion(StoppingCriterion):
    """
    Bails out of the testing at the beginning of the training.
    Useful for testing the functionality of StoppingCriterion itself.
    """

    def on_epoch_start(self):
        raise RuntimeError("Exiting the training before any epoch.")


class MaxBatchCountStoppingCriterion(StoppingCriterion):
    """
    This class might be useful for testing or troubleshooting codes
    as it bails out of the batch loop early.
    """

    def __init__(self, max_count: int):
        super().__init__()
        self.max_count = max_count

    def on_batch_end(self):
        if self.max_count == 0:
            return False
        self.batch_count += 1
        return self.batch_count == self.max_count


class NonDecreasingEarlyStoppingCriterion(StoppingCriterion):
    """
    This class decides when a model training run should stop
    """

    def __init__(self, threshold: int = 7):
        super().__init__()
        self.threshold = threshold
        self.best_result: float = -1.0
        self.decreasing_count: int = 1
        self.num_epochs_without_improvement: int = 0

    def on_epoch_end(self, metrics_cache: MetricsCache) -> tuple[bool, bool]:
        """
        Given a result, decide whether to save the model and/or stop
        further computation
        """

        should_save_model = False
        should_finish_run = False

        if "loss" not in metrics_cache.stage_results:
            return should_save_model, should_finish_run

        result = metrics_cache.stage_results["loss"]

        if result < self.best_result:
            logger.info("Loss decreased from %0.3f to %0.3f", self.best_result, result)
            self.decreasing_count += 1
            if self.decreasing_count % 2 == 0:
                should_save_model = True
        elif result > self.best_result:
            self.num_epochs_without_improvement += 1
            logger.info(
                "Loss did not decrease for %s epoch(s)",
                self.num_epochs_without_improvement,
            )
            if self.num_epochs_without_improvement == self.threshold:
                logger.info("Stopping training as loss didn't decrease")
                should_finish_run = True
        self.best_result = result
        return should_save_model, should_finish_run


def load_stopping_conditions(
    configs: list[StoppingCriterionModel],
) -> list[StoppingCriterion]:

    stopping: list[StoppingCriterion] = []
    for config in configs:
        if config.name == "NonDecreasingEarlyStoppingCriterion":
            if "threshold" in config.params:
                stopping.append(
                    NonDecreasingEarlyStoppingCriterion(config.params["threshold"])
                )
            else:
                stopping.append(NonDecreasingEarlyStoppingCriterion())
        if config.name == "MaxBatchCountStoppingCriterion":
            stopping.append(
                MaxBatchCountStoppingCriterion(config.params["num_batches"])
            )

    return stopping
