import os
from pathlib import Path
import shutil

from iccore.test_utils import get_test_output_dir

from iclearn.data import DataloaderCreate
from iclearn.environment import environment
from iclearn.model import Metrics
from iclearn.output import LoggingOutputHandler
from iclearn.session import Session

from mocks import MockDataloader, MockLossFunc, MockModel
from mocks.images import generate_images


def test_session():

    work_dir = get_test_output_dir()
    dataset = generate_images(work_dir, number=20, splits=[0.5, 0.25])

    # Load the runtime environment for the session
    env = environment.load()

    # Collect anything 'model' related in a single object
    loss_func = MockLossFunc()
    metrics = Metrics(loss_func)
    model = MockModel(metrics)

    result_dir = work_dir / "results"

    # This is a single machine learning 'experiment'
    # when no dataloader provided
    session = Session(
        model,
        env,
        result_dir,
        dataloader=None,
        output_handlers=[LoggingOutputHandler(result_dir)],
    )
    # Check the error message during training
    try:
        session.do_batches("train")
        assert False, "Expected RuntimeError not raised"
    except RuntimeError as error:
        assert str(error) == "Tried to process batch with no dataloader"
    # Check the error message during inference
    try:
        session.infer("infer")
        assert False, "Expected RuntimeError not raised"
    except RuntimeError as error:
        assert str(error) == "Tried to do inference with no input data"

    # Set up the dataloader
    config = DataloaderCreate(dataset=dataset, batch_size=5)
    dataloader = MockDataloader(config)
    dataloader.load()

    # This is a single machine learning 'experiment'
    session = Session(
        model,
        env,
        result_dir,
        dataloader,
        output_handlers=[LoggingOutputHandler(result_dir)],
    )

    num_epochs = 1
    session.train(num_epochs)

    metrics.reset()
    session.infer()

    # Clean up after ourselves
    shutil.rmtree(work_dir)
