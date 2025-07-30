"""
This module has functionality for Machine Learning workflows
"""

import logging
from pathlib import Path

from iccore.system.environment import Environment

from iclearn.data import Dataloader
from iclearn.model import Model
from iclearn.output import OutputHandler

logger = logging.getLogger(__name__)


class Session:
    """
    This is a Machine Learning workflow session. It can be used to train() a model or
    run inference on an existing model (infer()).

    It implements a collection of functions that are called at the standard
    training or inference stages, which can be overriden as needed. The order is:

    on_before_epochs()
    for eachEpoch:
        on_epoch_start()
        do_batches()
            on_batch_start()
            do_batch()
                on_before_predict()
            on_batch_end()
        on_validation_start()
        do_batches()
            ...
        on_epoch_end()
    """

    def __init__(
        self,
        model: Model,
        env: Environment,
        result_dir: Path = Path(),
        dataloader: Dataloader | None = None,
        output_handlers: list[OutputHandler] | None = None,
    ) -> None:

        self.env = env
        self.result_dir = result_dir

        self.model = model
        self.dataloader = dataloader
        if output_handlers:
            self.output_handlers = output_handlers
        else:
            self.output_handlers = []
        self.last_predictions = None

    def on_before_predict(self, batch) -> tuple:
        return batch[0], batch[1]

    def do_batch(self, batch, update_optimizer: bool = False) -> bool:
        """
        Operate on a single batch. The 'update_optimizer'
        flag should be True in the test stage.
        """

        self.on_batch_start()

        if update_optimizer:
            self.model.optimizer.zero_grad()

        x, y = self.on_before_predict(batch)

        prediction = self.model.predict(x)
        loss = self.model.calculate_loss(prediction, y)

        if update_optimizer:
            loss.backward()
            self.on_optimizer_step()
        return self.on_batch_end(prediction, y)

    def on_optimizer_step(self):
        """
        Breaking out the optimizer stepping process.
        For cases where the optimizer has non-standard stepping.
        """

        self.model.optimizer.step()

    def on_before_epochs(self, num_epochs: int):
        """
        Called before the epoch loop starts
        """

        self.model.on_before_epochs(self.env.is_multigpu)
        for handler in self.output_handlers:
            assert self.dataloader
            handler.on_before_epochs(num_epochs, self.dataloader)

    def on_after_epochs(self):
        """
        Called when all epochs are completed
        """
        for handler in self.output_handlers:
            handler.on_after_epochs()

    def on_epoch_start(self, epoch_idx: int):
        """
        Called at the beginning of an epoch
        """
        self.model.on_epoch_start()
        if self.dataloader:
            self.dataloader.on_epoch_start(epoch_idx)

        for handler in self.output_handlers:
            handler.on_epoch_start(self.num_train_batches)

    def on_epoch_end(self):
        """
        Called at the end of an epoch
        """
        should_save, should_finish = self.model.on_epoch_end()
        for handler in self.output_handlers:
            handler.on_epoch_end(self.model.metrics.cache)

        if should_save and self.env.is_master_process():
            logger.info("Saving model with best loss value.")
            self.output_handlers.save_model(self.model)

        if should_finish:
            logger.info("Stopping training due to stop criterion.")
            return True
        return False

    def on_batch_start(self):
        """
        Called at the start of a batch, before any predicionts
        """
        self.model.on_batch_start()
        for handler in self.output_handlers:
            handler.on_batch_start()

    def on_batch_end(self, prediction, ground_truth) -> bool:
        """
        Called at the end of a batch, after predictions
        """
        should_break = self.model.on_batch_end(prediction, ground_truth)
        for handler in self.output_handlers:
            handler.on_batch_end(self.model.metrics.cache)
        return should_break

    @property
    def num_train_batches(self):
        """
        Covenience method to get number of training batches
        """
        return self.dataloader.num_batches("train")

    @property
    def num_val_batches(self):
        """
        Convenience method to get number of validation batches
        """
        return self.dataloader.num_batches("val")

    def on_validation_start(self):
        """
        Called after training epochs, at the start of the
        validation stage.
        """
        self.model.on_validation_start()
        for handler in self.output_handlers:
            handler.on_validation_start(self.num_val_batches)

    def do_batches(self, dl_label: str, update_optimizer: bool = False):
        """
        Loop over all batches in the labelled dataloader
        """

        if not self.dataloader:
            raise RuntimeError("Tried to process batch with no dataloader")

        for batch in self.dataloader.get_dataloader(dl_label):
            should_break = self.do_batch(batch, update_optimizer)
            if should_break:
                logger.info("Breaking from batch loop early")
                break

    def train(
        self,
        num_epochs: int,
        train_dl_label: str = "train",
        val_dl_label: str = "val",
    ):
        """
        Run the training stage
        """

        self.on_before_epochs(num_epochs)
        for epoch in range(1, num_epochs + 1):
            self.on_epoch_start(epoch)
            self.do_batches(train_dl_label, update_optimizer=True)

            if val_dl_label != "":
                self.on_validation_start()
                self.do_batches(val_dl_label)
            else:
                continue

            should_break = self.on_epoch_end()
            if should_break:
                break

        self.on_after_epochs()

    def on_before_infer(self):
        """
        Called before attempting to do inference
        """

        if not self.dataloader:
            raise RuntimeError("Tried to do inference with no input data")
        self.model.on_before_infer()

    def on_after_infer(self, stage):
        """
        Called after doing inference
        """

        for handler in self.output_handlers:
            handler.on_after_infer(
                stage, self.last_predictions, self.model.metrics.cache
            )

    def infer(self, test_dl_label: str = "test"):
        """
        Run the model in inference mode
        """

        self.on_before_infer()
        self.do_batches(test_dl_label)
        self.on_after_infer(test_dl_label)
