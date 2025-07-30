from iclearn.model.stopping_criteria import (
    MaxBatchCountStoppingCriterion,
    TrainingStartStoppingCriterion,
    NonDecreasingEarlyStoppingCriterion,
)

from iclearn.model import Metrics

from mocks import MockLossFunc, MockModel


def test_stopping():

    # Collect anything 'model' related in a single object
    loss_func = MockLossFunc()
    metrics = Metrics(loss_func)

    # Create the stopping criteria and the model itself
    model = MockModel(metrics)
    stopping_criterion = [
        TrainingStartStoppingCriterion(),
        MaxBatchCountStoppingCriterion(max_count=0),
        NonDecreasingEarlyStoppingCriterion(threshold=1),
    ]
    model.stopping = stopping_criterion

    # Set up the testing parameters
    mock_data = 0.0
    num_epochs = 1

    # Testing the exit before epoch stopping criteria
    try:
        model.on_before_epochs(num_epochs)
        assert False, "Expected RuntimeError not raised"
    except RuntimeError as error:
        assert str(error) == "Exiting the training before any epoch."

    # Testing the exiting on batch end stopping criteria
    assert model.on_batch_end(mock_data, mock_data) == False

    # Testing the early stopping criteria on batch end
    # Test loss not being in the metric cache -> defaults to outputting false
    assert model.on_epoch_end() == (False, False)

    # Test case where loss is greater than best results
    # i.e end run because no improvement being seen
    model.metrics.cache.stage_results = {"loss": mock_data}
    assert model.on_epoch_end() == (False, True)

    # Test case where loss is less than best result
    # i.e model should be saved given some user defined tolerance
    model.metrics.cache.stage_results = {"loss": -2.0}
    assert model.on_epoch_end() == (True, False)
