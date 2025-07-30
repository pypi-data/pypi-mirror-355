from pathlib import Path
import typing

from iccore.system.process import Process

from .metrics import Metrics
from .stopping_criteria import StoppingCriterion


class Model:
    """
    Simple representation of a machine learning model, collects model related
    things like the optimizer and metrics calculator together.
    """

    def __init__(
        self,
        metrics: Metrics,
        model: typing.Any | None = None,
        model_path: Path | None = None,
        optimizer=None,
    ) -> None:

        self.impl = model
        self.model_path = model_path
        self.process: Process | None = None
        self.metrics = metrics
        self.optimizer = optimizer
        self.stopping: list[StoppingCriterion] = []

    def on_before_epochs(self, is_distributed: bool = False):
        """
        Called right before starting the epoch loop
        """
        if is_distributed:
            self.set_as_distributed()
        self.metrics.on_before_epochs()

        for criterion in self.stopping:
            criterion.on_epoch_start()

    def on_epoch_start(self):
        """
        Called at the beginnging of an epoch
        """
        self.metrics.on_epoch_start()

        for criterion in self.stopping:
            criterion.on_epoch_start()

        if not self.impl:
            raise RuntimeError("Attempted to start training without loading a model")
        self.impl.train()

    def on_epoch_end(self) -> tuple[bool, bool]:
        """
        Called at the end of an epoch
        """

        self.metrics.on_epoch_end()

        save_model = []
        finish_loop = []
        for criterion in self.stopping:
            save, finish = criterion.on_epoch_end(self.metrics.cache)
            save_model.append(save)
            finish_loop.append(finish)
        return any(save_model), any(finish_loop)

    def on_validation_start(self):
        """
        Called at the start of the validation stage, before
        any batches are loaded
        """
        self.metrics.on_validation_start()
        if not self.impl:
            raise RuntimeError("Attempted to start validation without loading a model")
        self.impl.eval()

        for criterion in self.stopping:
            criterion.on_validation_start()

    def on_batch_start(self):
        self.metrics.on_batch_start()
        for criterion in self.stopping:
            criterion.on_batch_start()

    def on_batch_end(self, prediction, ground_truth):
        """
        Call at the end of a batch, when the prediction has
        been made
        """
        self.metrics.on_batch_end(prediction, ground_truth)

        finish_loop = []
        for criterion in self.stopping:
            finish_loop.append(criterion.on_batch_end())
        return any(finish_loop)

    def on_before_infer(self):
        """
        Called before doing inference
        """
        self.metrics.on_before_infer()
        for criterion in self.stopping:
            criterion.on_before_infer()

    def load_from_file(self):
        """
        Load the model from the given path
        """
        raise NotImplementedError()

    def load(self, _: int):

        if self.model_path:
            self.load_from_file()
        else:
            raise NotImplementedError()

    def set_as_distributed(self) -> None:
        """
        Indicate that we are running in a distributed setting
        """

    def predict(self, inputs):
        """
        Preduct a result from the model
        """

        if not self.impl:
            raise RuntimeError("Attempted to make a pridiction without loading a model")
        return self.impl(inputs)

    def calculate_loss(self, prediction, ground_truth):
        """
        Evaluate the loss function
        """
        return self.metrics.calculate_loss(prediction, ground_truth)

    def save(self, path: Path):
        """
        Save the model to disk
        """
        raise NotImplementedError()
