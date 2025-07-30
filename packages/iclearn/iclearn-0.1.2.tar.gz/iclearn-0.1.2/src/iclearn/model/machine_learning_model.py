from pathlib import Path
from typing import Any

from iccore.data import BaseComputationalModel
from icsystemutils.network import remote

from pydantic import BaseModel


class Optimizer(BaseModel, frozen=True):

    name: str
    learning_rate: float
    extra: dict[str, Any] = {}


class StoppingCriterion(BaseModel, frozen=True):

    name: str
    params: dict[str, Any] = {}


class MachineLearningModel(BaseComputationalModel, frozen=True):

    type: str = "MachineLearningModel"
    optimizer: Optimizer
    loss_function: str
    metrics: list[str] = []
    stopping_conditions: list[StoppingCriterion] = []
    batch_size: int = 64
    num_classes: int = 0


def upload(model: MachineLearningModel, host: remote.Host, local_location: Path):

    if not model.location:
        raise RuntimeError("Attempting to upload model without a location")

    remote.upload(local_location, host, model.location, None)


def download(model: MachineLearningModel, host: remote.Host, local_location: Path):

    if not model.location:
        raise RuntimeError("Attempting to download model without a location")
    remote.download(host, model.location, local_location, None)
