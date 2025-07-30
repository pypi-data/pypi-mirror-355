"""
This module has functionaly for loading data from
an iclearn dataset - which is essentially a path to some data.

It differs from a PyTorch dataloader in that it manages 'splits' (test, train, val)
etc - it holds PyTorch-like dataloaders for each split.
"""

from pathlib import Path
import logging

from pydantic import BaseModel

from iccore.data import Dataset
from iccore.system import Environment

from .split import Splits, get_default_splits

logger = logging.getLogger(__name__)


class DataloaderCreate(BaseModel):
    dataset: Dataset
    batch_size: int = 0
    splits: Splits | None = None


class Dataloader:
    """
    This class supports loading data from a provided dataset

    :param Dataset dataset: The dataset (data location) to load from
    :param int batch_size: The size of batches to load at runtime
    :param Splits splits: Description of how to split the dataset
    :param Environment env: The runtime context or environment
    """

    def __init__(self, config: DataloaderCreate, data_dir: Path | None = None):
        self.config = config
        self.data_dir = data_dir
        self.datasets: dict = {}
        self.loaders: dict = {}
        self.samplers: dict = {}

    def load(
        self,
        env: Environment | None = None,
    ) -> None:
        """
        Load the dataset from the supplied path
        """

        data_path = self._get_data_path()
        logger.info("Loading dataset from %s", data_path)

        if not data_path.exists():
            raise RuntimeError(f"Dataset path is empty {data_path}")

        if self.config.splits:
            splits = self.config.splits
        else:
            logger.info("No splits specifed - loading defaults")
            splits = get_default_splits()

        for s in splits.items:
            self._load_dataset(self.config.dataset, s.name, splits)
        self._setup_dataloaders(splits, self.config.batch_size, env)

        logger.info(
            "Finished loading dataset with %d dataloaders", len(self.datasets.keys())
        )

    def _get_data_path(self):

        if not self.config.dataset.original_path:
            if self.data_dir:
                return self.data_dir
            return Path().resolve()

        config_path = Path(self.config.dataset.original_path)
        if not config_path.is_absolute():
            if self.data_dir:
                path = self.data_dir / config_path
            else:
                path = (Path() / config_path).resolve()
        else:
            path = config_path
        return path

    def _load_dataset(self, dataset: Dataset, name: str, splits: Splits):
        self.datasets[name] = self.load_dataset(dataset, name, splits)

    def load_dataset(self, dataset: Dataset, name: str, splits: Splits):
        """
        Override this to provide a PyTorch-like dataset
        """
        raise NotImplementedError()

    def load_sampler(self, data, num_replicas, rank):
        """
        Override to provide a distributed sampler
        """
        return None

    def load_dataloader(self, dataset, batch_size, shuffle, sampler, num_workers):
        """
        Override to provide a PyTorch-like dataloader
        """
        raise NotImplementedError()

    def get_dataset(self, name: str):
        """
        Get the dataset for named split
        """
        return self.datasets[name]

    def get_dataloader(self, name: str):
        """
        Get the dataloader for a named split
        """
        return self.loaders[name]

    def num_batches(self, name: str) -> int:
        return len(self.loaders[name])

    @property
    def num_classes(self) -> int:
        if self.datasets:
            dataset = list(self.datasets.values())[0]
            if hasattr(dataset, "num_classes"):
                return getattr(dataset, "num_classes")
        return 0

    def on_epoch_start(self, epoch_idx: int):
        self._set_sampler_epoch(epoch_idx)

    def _set_sampler_epoch(self, epoch: int):
        for sampler in self.samplers.values():
            sampler.set_epoch(epoch)

    def _setup_dataloaders(
        self,
        splits: Splits,
        batch_size: int,
        env: Environment | None = None,
    ) -> None:
        """
        Set up a dataloader for each split and if supported a
        data sampler
        """
        if env and env.is_multigpu:
            logger.info("Setting up Samplers")
            for split in [s for s in splits.items if s.use_sampler]:
                sampler = self.load_sampler(
                    self.datasets[split.name],
                    env.world_size,
                    env.global_rank,
                )
                if sampler:
                    self.samplers[split.name] = sampler

        logger.info("Setting up Dataloaders")
        for (name, dataset), attrs in zip(self.datasets.items(), splits.items):
            self.loaders[name] = self.load_dataloader(
                dataset,
                batch_size,
                attrs.shuffle,
                sampler=self.samplers[name] if name in self.samplers else None,
                num_workers=env.cpu_info.cores_per_node if env else 1,
            )
