import os
from pathlib import Path
import shutil

from iclearn.data import DataloaderCreate
from iclearn.data.split import get_fractional_splits

from iccore.test_utils import get_test_output_dir

from mocks.images import generate_images
from mocks import MockDataloader


# Unit test for Dataloader
def test_dataloader():

    work_dir = get_test_output_dir()

    # Generate 20 samples and splitting them 50% into 'train' and 25% into 'val'
    # train: 10 samples, val: 5 samples, test: 5 samples
    dataset = generate_images(work_dir, number=20, splits=[0.5, 0.25])

    dataloader_config = DataloaderCreate(dataset=dataset, batch_size=5)

    dataloader = MockDataloader(dataloader_config)
    dataloader.load()

    # Test the dataset is split into train, val, test
    assert len(dataloader.datasets) == 3
    assert "train" in dataloader.datasets
    assert "val" in dataloader.datasets
    assert "test" in dataloader.datasets

    # Check the number of train, val and test splits
    train_dataset = dataloader.get_dataset("train")
    val_dataset = dataloader.get_dataset("val")
    test_dataset = dataloader.get_dataset("test")
    assert len(train_dataset) == 10
    assert len(val_dataset) == 5
    assert len(test_dataset) == 5

    # Test getting the train dataset
    train_dataset = dataloader.get_dataset("train")
    assert len(train_dataset) == 10

    # Test getting the train dataloader and get the batch size
    # 10 samples / batch size of 5 = 2
    train_dataloader = dataloader.get_dataloader("train")
    assert len(train_dataloader) == 2
    assert dataloader.num_batches("train") == 2

    # Clean up after ourselves
    shutil.rmtree(work_dir)
