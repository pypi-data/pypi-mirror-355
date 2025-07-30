import os
from pathlib import Path
import shutil

from iccore.test_utils import get_test_output_dir

from iclearn.environment import environment
from iclearn.data.split import get_fractional_splits
from iclearn.model import Metrics
from iclearn.output import LoggingOutputHandler
from iclearn.output import TabularMetricsOutputHandler

from mocks.linear import LinearDataloader, LinearLossFunc, LinearModel, LinearSession
from iclearn.data.utils.linear_data import gradient_descent_iter, gradient_descent_batch


def test_regression():

    work_dir = get_test_output_dir()

    # Load the runtime environment for the session
    env = environment.load()

    # Set up the dataloader for the basic test case
    # Testing a single epoch with a single batch
    # Training dataset without validation split
    splits = get_fractional_splits(1.0, 0.0)
    basic_dataloader = LinearDataloader(
        w=0.5, b=0.5, num_points=1, batch_size=1, splits=splits, env=env
    )

    # Collect anything 'model' related in a single object
    loss_func = LinearLossFunc()
    model = LinearModel(metrics=Metrics(loss_func))

    # This is a single machine learning 'experiment'
    result_dir = work_dir / "results"

    # Create the controlled gradient descent for assertion
    # Runs the basic gradient descent algorithm used by LinearOptimizer in the model
    num_epochs = 1

    w, b, _ = gradient_descent_iter(
        w=0.0, b=0.0, x=basic_dataloader.x, y=basic_dataloader.y, lr=0.1
    )

    # Create the iclearn LinearSession to run the test
    session = LinearSession(
        model,
        env=env,
        dataloader=basic_dataloader,
        output_handlers=[LoggingOutputHandler(result_dir)],
    )

    # Run the iclearn training session
    session.train(num_epochs)

    # Basic assert for the parameters of the mock linear model
    assert session.model.impl.w == w
    assert session.model.impl.b == b

    # Set up the dataloader for the advanced test case
    # Reset the model parameters
    model = LinearModel(metrics=Metrics(loss_func))
    splits = get_fractional_splits(0.75, 0.25)

    # Create the dataloader with a training validation split
    # Have three batches of the training data per epoch
    alt_dataloader = LinearDataloader(
        w=0.5, b=0.5, num_points=20, batch_size=5, splits=splits, env=env
    )

    # Access just the training data of the dataloader
    alt_data = alt_dataloader.load_dataset(root=None, name="train", splits=splits)

    # Run the experiment over five epochs
    num_epochs = 5
    w, b = gradient_descent_batch(
        alt_data.x, alt_data.y, num_epochs=num_epochs, batch_size=5
    )

    # Create and run the iclearn LinearSession
    session = LinearSession(
        model,
        env=env,
        dataloader=alt_dataloader,
        output_handlers=[
            LoggingOutputHandler(result_dir),
            TabularMetricsOutputHandler(
                result_dir, filename="test_regression_tabular.csv"
            ),
        ],
    )

    session.train(num_epochs)

    # Assert for the parameters of the mock linear model
    assert session.model.impl.w == w
    assert session.model.impl.b == b

    # Clean up after ourselves
    shutil.rmtree(work_dir)
