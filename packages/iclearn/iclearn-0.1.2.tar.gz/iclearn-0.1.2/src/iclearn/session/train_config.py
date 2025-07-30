from pathlib import Path

from pydantic import BaseModel

from iccore.serialization import write_model

from iclearn.data import DataloaderCreate
from iclearn.model import MachineLearningModel


class TrainConfig(BaseModel, frozen=True):

    dataloader: DataloaderCreate
    model: MachineLearningModel
    num_epochs: int
    num_batches: int
    node_id: int = 0
    num_nodes: int = 1
    num_gpus: int = 1
    local_rank: int = 0
    with_profiling: bool = False
    dataset_dir: Path = Path()
    result_dir: Path = Path()


def write_config(config: TrainConfig, path: Path):
    write_model(config, path / "config.json")
