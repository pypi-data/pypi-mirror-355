import os
from pathlib import Path
import json
import shutil

from iccore.data import Dataset

from iclearn.data import DataloaderCreate
from iclearn.model import MachineLearningModel, Optimizer
from iclearn.session import TrainConfig
from iclearn.session.train_config import write_config

from iccore.test_utils import get_test_output_dir


# Test write_config() function
def test_write_config():
    work_dir = get_test_output_dir()

    # Create a Config instance
    config = TrainConfig(
        dataloader=DataloaderCreate(dataset=Dataset(), batch_size=5),
        model=MachineLearningModel(
            name="mock_ml_model",
            optimizer=Optimizer(name="mock_optimizer", learning_rate=0.01),
            loss_function="mock_loss_function",
        ),
        num_epochs=10,
        num_batches=2,
        node_id=0,
        num_nodes=1,
        num_gpus=0,
        local_rank=0,
        with_profiling=False,
        dataset_dir=work_dir / "dataset",
        result_dir=work_dir / "results",
    )

    # Write config to the result_dir
    write_config(config, config.result_dir)

    # Check if the config file exists in the result_dir
    config_file = config.result_dir / "config.json"
    assert config_file.exists(), "Expected config.json in the result_dir"

    # Load the config json back
    with open(config_file, "r") as f:
        json_data = json.load(f)

    # Make a new Config instance with the json
    c = TrainConfig(**json_data)

    # Compare new config with the original instance
    assert config == c, f"Config json files don't match: {config} != {c}"

    # Clean up after ourselves
    shutil.rmtree(work_dir)
