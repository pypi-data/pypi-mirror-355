"""
A machine learning session using PyTorch
"""

import logging
from pathlib import Path

import torch.distributed as dist

from iclearn.data import Dataloader
from iclearn.model.torch import TorchModel
from iclearn.output import OutputHandler
from iclearn.session import Session
from iclearn.environment.torch import TorchEnvironment

logger = logging.getLogger(__name__)


class TorchSession(Session):
    """
    This is a Machine Learning workflow session
    """

    def __init__(
        self,
        model: TorchModel,
        env: TorchEnvironment,
        result_dir: Path = Path(),
        dataloader: Dataloader | None = None,
        output_handlers: list[OutputHandler] | None = None,
    ) -> None:

        super().__init__(model, env, result_dir, dataloader, output_handlers)

        self.torch_model = model
        self.torch_env = env

    def on_before_predict(self, batch) -> tuple:
        """
        Called before a prediction during a batch opetation
        """
        x = self.torch_model.to_device(batch[0])
        y = self.torch_model.to_device(batch[1])
        return x, y

    def _init_torch_dist(self):

        logger.info("Starting torch dist process group")
        dist.init_process_group(
            backend=self.torch_env.dist_backend,
            world_size=self.env.world_size,
            rank=self.env.global_rank,
        )

    def on_before_epochs(self, num_epochs: int):
        """
        Called before the epoch loop starts
        """

        if self.env.is_multigpu:
            self._init_torch_dist()

        super().on_before_epochs(num_epochs)

    def on_before_infer(self):
        """
        Called before attempting to do inference
        """

        if self.env.is_multigpu:
            self._init_torch_dist()

        super().on_before_infer()
