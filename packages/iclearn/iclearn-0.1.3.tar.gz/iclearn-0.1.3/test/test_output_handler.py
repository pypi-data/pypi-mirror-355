from iclearn.output import OutputHandler


def test_output_handler():
    output_handler = OutputHandler()

    assert output_handler.batch_count == 0
    assert output_handler.epoch_count == 0

    output_handler.on_before_epochs(10, None)
    assert output_handler.num_epochs == 10
    assert output_handler.epoch_count == 0

    output_handler.on_epoch_start(10)
    assert output_handler.epoch_count == 1
    assert output_handler.batch_count == 0
    assert output_handler.num_batches == 10
    assert output_handler.current_stage == "train"

    output_handler.on_batch_start()
    assert output_handler.batch_count == 1

    output_handler.on_batch_end(None)
    assert output_handler.batch_count == 1

    output_handler.on_validation_start(10)
    assert output_handler.batch_count == 0

    output_handler.on_epoch_start(10)
    assert output_handler.epoch_count == 2
    assert output_handler.batch_count == 0
