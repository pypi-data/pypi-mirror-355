import os
from pathlib import Path
import shutil

from iccore.test_utils import get_test_output_dir

from iclearn.data import DataloaderCreate
from iclearn.output import PlottingOutputHandler
from iclearn.model import MetricsCache

from mocks import MockDataloader
from mocks.images import generate_images


def test_on_before_epochs_plotting():

    work_dir = get_test_output_dir()
    dataset = generate_images(work_dir, number=20, splits=[0.5, 0.25])

    config = DataloaderCreate(dataset=dataset, batch_size=5)
    dataloader = MockDataloader(config)
    dataloader.load()

    # Define the output path for saving the plot
    output_path = work_dir / "pre_epochs"
    output_path.mkdir(parents=True, exist_ok=True)

    # Create plot handler for plotting
    plot_handler = PlottingOutputHandler(result_dir=work_dir)
    num_epochs = 10
    plot_handler.on_before_epochs(num_epochs, dataloader)

    # Check that the output file exists
    output_file = output_path / "dataset_sample.svg"
    assert os.path.exists(
        output_file
    ), f"The output file {output_file} was not created."

    # Clean up after ourselves
    shutil.rmtree(work_dir)


def test_on_after_infer_plotting():

    work_dir = get_test_output_dir()
    dataset = generate_images(work_dir, number=20, splits=[0.5, 0.25])

    config = DataloaderCreate(dataset=dataset, batch_size=5)
    dataloader = MockDataloader(config)
    dataloader.load()

    # Define the output path for saving the plot
    output_path = work_dir / "after_infer"
    output_path.mkdir(parents=True, exist_ok=True)

    plot_handler = PlottingOutputHandler(result_dir=work_dir)

    # Access the dataset directly from the dataloader
    train_dataset = dataloader.get_dataset("train")

    predictions = []
    for i in range(min(plot_handler.num_images, len(train_dataset))):
        image, mask = train_dataset[i]
        predictions.append((image, mask, mask))

    # Create MetricsCache instance
    metrics = MetricsCache()
    metrics.stage_results = {
        "iou": 0.75,
        "pa": 0.90,
        "loss": 0.2,
    }

    plot_handler.on_after_infer("test", predictions, metrics)
    # Check the output file for predictions exist
    output_file = output_path / "inference_predictions.svg"
    assert os.path.exists(
        output_file
    ), f"The output file {output_file} was not created."
    # Check the output files for each metric exist
    for metric_key in metrics.stage_results.keys():
        output_file = output_path / f"{metric_key}_metric.svg"
        assert os.path.exists(
            output_file
        ), f"The output file {output_file} was not created."

    # Clean up after ourselves
    shutil.rmtree(work_dir)
