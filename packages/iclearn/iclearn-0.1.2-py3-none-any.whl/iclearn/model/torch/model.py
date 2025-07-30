"""
A machine learning model specialized for PyTorch
"""

from pathlib import Path
import typing

import torch

from iclearn.model import Model, Metrics
from iclearn.environment.torch import TorchDevice


class TorchModel(Model):
    """
    A machine learning model with PyTorch additions
    """

    def __init__(
        self,
        metrics: Metrics,
        device: TorchDevice = TorchDevice(),
        model: typing.Any | None = None,
        model_path: Path | None = None,
        optimizer=None,
    ) -> None:

        super().__init__(metrics, model, model_path, optimizer)

        self.device = device
        self.is_sent_to_device: bool = False

    def send_to_device(self) -> None:
        """
        Send the model to the compute device
        """

        if not self.is_sent_to_device:

            if not self.impl:
                raise RuntimeError("Tried to send model to device but no model set")

            self.impl.to(self.device.handle)
            self.is_sent_to_device = True

    def to_device(self, batch):
        """
        Send the data batch to the device
        """

        return batch.to(self.device.handle)

    def load_from_file(self):
        """
        Load the model from the given path
        """

        if self.impl:
            return

        if not self.model_path:
            raise RuntimeError("Tried to load from file but no path set")

        self.impl = torch.load(self.model_path)

    def set_as_distributed(self) -> None:
        """
        If we are running distributed wrap torch model with ddp
        """

        if not self.impl:
            raise RuntimeError("Tried to set model as ddp, but no model set")
        self.impl = torch.nn.parallel.DistributedDataParallel(self.impl)

    def save(self, path: Path):
        if self.impl:
            torch.save(self.impl.state_dict(), path)

    def on_before_epochs(self, is_distributed: bool = False):
        self.send_to_device()
        super().on_before_epochs(is_distributed)

    def on_epoch_start(self):
        torch.set_grad_enabled(True)
        super().on_epoch_start()

    def on_validation_start(self):
        torch.set_grad_enabled(False)
        super().on_validation_start()

    def on_before_infer(self):
        torch.set_grad_enabled(False)
        super().on_before_infer()
        self.send_to_device()
