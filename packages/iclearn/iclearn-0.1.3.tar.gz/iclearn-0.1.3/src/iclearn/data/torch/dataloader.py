"""
A dataloader for PyTorch
"""

from pathlib import Path

from torch.utils.data import DataLoader as DataLoaderImpl

from iclearn.data import Dataloader, DataloaderCreate


class TorchDataloader(Dataloader):
    """
    A dataloader for PyTorch
    """

    def __init__(
        self,
        config: DataloaderCreate,
        path: Path | None = None,
    ):

        super().__init__(config, path)

    def load_dataloader(
        self, dataset, batch_size: int, shuffle: bool, sampler, num_workers: int
    ):
        """
        Override base method to return torch dataloader
        """
        return DataLoaderImpl(
            dataset=dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            sampler=sampler,
            num_workers=num_workers,
        )
